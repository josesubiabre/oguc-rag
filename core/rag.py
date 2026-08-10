"""Orquestación RAG: pregunta → recuperación híbrida → respuesta con fuentes.

La recuperación combina dos señales complementarias:

- semántica (embeddings): entiende paráfrasis, depende de una API externa;
- léxica (BM25): exacta con artículos y circulares, local y sin costo.

Los rankings se fusionan con Reciprocal Rank Fusion, que combina posiciones
en vez de puntajes — necesario porque la similitud coseno y el puntaje BM25
no comparten escala y promediarlos no tendría sentido.

Si la vía semántica falla, la búsqueda continúa solo con BM25 en lugar de
caer: es preferible una respuesta de calidad algo menor que ninguna.
"""

from functools import lru_cache

from core.bm25 import Bm25Index
from core.chunking import es_norma, es_procedimiento
from core.config import TOP_K
from core.embeddings import embed_query
from core.llm import extractive_answer, generate_answer
from core.store import VectorStore

RRF_K = 60  # constante estándar: amortigua el peso de los primeros puestos
CANDIDATES = 20  # profundidad de cada ranking antes de fusionar
CANDIDATOS_NORMA = 10  # ver _reservar_fuentes: medido sobre el corpus real


@lru_cache(maxsize=1)
def _store():
    return VectorStore.load()


@lru_cache(maxsize=1)
def _bm25():
    """Índice léxico: precompilado si existe, construido al vuelo si no."""
    if Bm25Index.exists():
        index = Bm25Index.load()
        if index.size == len(_store().chunks):
            return index
    return Bm25Index.build(_store().chunks)


def _rrf(rankings, k):
    """Fusiona listas de índices por Reciprocal Rank Fusion."""
    puntajes = {}
    for ranking in rankings:
        for posicion, idx in enumerate(ranking):
            puntajes[idx] = puntajes.get(idx, 0.0) + 1.0 / (RRF_K + posicion + 1)
    orden = sorted(puntajes, key=lambda i: puntajes[i], reverse=True)
    return orden[:k]


def _reservar(indices, candidatos, chunks, predicado, ranura):
    """Sustituye una ranura por el mejor candidato semántico que cumpla.

    RRF premia que un documento aparezca en ambos rankings, así que un
    fragmento fuerte en una sola vía pierde contra otros peor posicionados en
    las dos. Eso deja fuera material que la búsqueda semántica sí había
    identificado, y hay dos casos donde importa lo suficiente como para
    reservarle un lugar. Se reemplaza, nunca se agrega: el contexto no crece
    y el costo por consulta no cambia.
    """
    if len(indices) < abs(ranura) or any(predicado(chunks[i]) for i in indices):
        return indices
    mejor = next((i for i in candidatos if predicado(chunks[i])), None)
    if mejor is None or mejor in indices:
        return indices
    nuevos = list(indices)
    nuevos[ranura] = mejor
    return nuevos


def _reservar_fuentes(indices, semantico, chunks):
    """Garantiza que la respuesta tenga un formulario y una norma si procede.

    Los formularios son fuertes en semántica y débiles en BM25 —su texto son
    rótulos de campos, no prosa—, así que las circulares les ganan siempre.
    Con las normas pasa algo parecido pero peor: en una consulta de
    copropiedad, media docena de circulares antiguas desplazaban a la ley
    vigente, y el modelo terminaba citando la ley derogada que esas circulares
    invocan.

    Los umbrales salen de medir el corpus real. Un formulario pertinente
    aparece entre los puestos 4 y 10 de la vía semántica y en preguntas
    normativas nunca antes del 25, así que basta exigir que esté dentro de
    CANDIDATES. Una norma pertinente aparece entre el 1 y el 5, mientras que
    las que conviene descartar caen del 13 en adelante; CANDIDATOS_NORMA = 10
    deja margen por ambos lados. Sin ese tope se cuela una norma cualquiera
    por el solo hecho de ser la mejor de un mal lote.
    """
    indices = _reservar(indices, semantico, chunks, es_procedimiento, -1)
    return _reservar(
        indices, semantico[:CANDIDATOS_NORMA], chunks, es_norma, -2
    )


def retrieve(question, k=TOP_K):
    """Devuelve (fragmentos, modo). Modo: hybrid | semantic | bm25_fallback."""
    store = _store()

    lexico = _bm25().rank(question, CANDIDATES)

    semantico = []
    try:
        qvec = embed_query(question)
        semantico = [
            int(i) for i in (store.matrix @ qvec).argsort()[::-1][:CANDIDATES]
        ]
    except Exception:
        semantico = []  # sin señal semántica: seguimos con la léxica

    if semantico and lexico:
        modo, indices = "hybrid", _rrf([semantico, lexico], k)
        indices = _reservar_fuentes(indices, semantico, store.chunks)
    elif semantico:
        modo, indices = "semantic", semantico[:k]
    elif lexico:
        modo, indices = "bm25_fallback", lexico[:k]
    else:
        return [], "bm25_fallback"

    return [store.chunks[i] for i in indices], modo


def answer(question, k=TOP_K):
    """Devuelve (texto, fuentes, proveedor, modo de recuperación)."""
    hits, modo = retrieve(question, k)
    if not hits:
        return (
            "No encontré nada en la normativa indexada que responda esa "
            "consulta. Intenta reformularla con otros términos.",
            [],
            "sin_resultados",
            modo,
        )

    context = "\n\n---\n\n".join(
        f"[{h.get('source', 'OGUC')}, página {h['page']}]\n{h['text']}" for h in hits
    )
    try:
        text, provider = generate_answer(question, context)
    except Exception:
        # Ambos LLM caídos: entregamos los fragmentos recuperados en crudo
        # en vez de un error, porque la búsqueda sí encontró material útil.
        text, provider = extractive_answer(hits), "extractive"

    by_source = {}
    for h in hits:
        by_source.setdefault(h.get("source", "OGUC"), set()).add(h["page"])
    sources = [
        {"source": s, "pages": sorted(p)} for s, p in sorted(by_source.items())
    ]
    return text, sources, provider, modo
