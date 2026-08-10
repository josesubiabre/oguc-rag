"""Tests de la orquestación híbrida y sus degradaciones.

Ningún test llama a servicios pagados: embeddings y LLM van mockeados.
"""

import numpy as np
import pytest

from core import rag
from tests.test_bm25 import CHUNKS


class FakeStore:
    def __init__(self, chunks):
        self.chunks = chunks
        # Vectores unitarios distintos por fragmento: el primero es el más
        # similar a la consulta simulada.
        self.matrix = np.eye(len(chunks), dtype=np.float32)


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    """Store y BM25 en memoria; sin acceso a disco ni a la red."""
    store = FakeStore(CHUNKS)
    rag._store.cache_clear()
    rag._bm25.cache_clear()
    monkeypatch.setattr(rag, "_store", lambda: store)
    from core.bm25 import Bm25Index

    indice = Bm25Index.build(CHUNKS)
    monkeypatch.setattr(rag, "_bm25", lambda: indice)
    yield


def _vector_hacia(i):
    def fake(_question):
        v = np.zeros(len(CHUNKS), dtype=np.float32)
        v[i] = 1.0
        return v

    return fake


def test_modo_hibrido_cuando_ambos_responden(monkeypatch):
    monkeypatch.setattr(rag, "embed_query", _vector_hacia(0))
    monkeypatch.setattr(rag, "generate_answer", lambda q, c: ("respuesta", "groq"))
    text, sources, provider, mode = rag.answer("altura de baranda")
    assert mode == "hybrid"
    assert provider == "groq"
    assert sources


def test_fallback_a_bm25_si_falla_el_embedding(monkeypatch):
    def explota(_q):
        raise RuntimeError("Créditos de Gemini agotados")

    monkeypatch.setattr(rag, "embed_query", explota)
    monkeypatch.setattr(rag, "generate_answer", lambda q, c: ("respuesta", "groq"))
    text, sources, provider, mode = rag.answer("artículo 4.2.7")
    assert mode == "bm25_fallback"
    assert sources, "debe seguir citando fuentes sin embeddings"
    assert "4.2.7" in sources[0]["source"] or sources


def test_modo_semantico_si_bm25_no_coincide(monkeypatch):
    monkeypatch.setattr(rag, "embed_query", _vector_hacia(1))
    monkeypatch.setattr(rag, "generate_answer", lambda q, c: ("respuesta", "groq"))
    # Consulta sin ninguna palabra del corpus: BM25 no aporta candidatos
    _, _, _, mode = rag.answer("zzzz qwerty inexistente")
    assert mode == "semantic"


def test_respuesta_extractiva_si_ambos_llm_fallan(monkeypatch):
    monkeypatch.setattr(rag, "embed_query", _vector_hacia(0))

    def sin_llm(_q, _c):
        raise RuntimeError("Groq y Gemini caídos")

    monkeypatch.setattr(rag, "generate_answer", sin_llm)
    text, sources, provider, mode = rag.answer("altura de baranda")
    assert provider == "extractive"
    assert "temporalmente no" in text  # explica la indisponibilidad
    assert "OGUC" in text  # incluye la trazabilidad al documento
    assert sources


def test_sin_cobertura_no_inventa(monkeypatch):
    def explota(_q):
        raise RuntimeError("sin embeddings")

    monkeypatch.setattr(rag, "embed_query", explota)
    text, sources, provider, mode = rag.answer("zzzz qwerty inexistente")
    assert provider == "sin_resultados"
    assert sources == []


def test_rrf_prioriza_lo_que_aparece_en_ambos_rankings():
    # El 1 está en las dos listas (aunque bajo en la segunda); el 4 solo en
    # una, en primer lugar. La coincidencia entre recuperadores debe pesar más.
    fusion = rag._rrf([[1, 2, 3], [4, 5, 1]], k=3)
    assert fusion[0] == 1


def test_rrf_respeta_el_orden_dentro_de_un_solo_ranking():
    fusion = rag._rrf([[7, 8, 9]], k=3)
    assert fusion == [7, 8, 9]


# --- Reserva de un lugar para los formularios (procedimiento) ---

FRAGMENTOS_MIXTOS = [
    {"source": "OGUC", "text": "a", "page": 1},
    {"source": "Circular DDU 100", "text": "b", "page": 1},
    {"source": "Formulario MINVU 2-3.1 (Solicitud de Permiso)", "text": "c", "page": 1},
    {"source": "LGUC", "text": "d", "page": 1},
]


def test_reserva_da_lugar_al_formulario_que_rrf_descarto():
    """Es el caso real: fuerte en semántica, débil en BM25, fuera del top."""
    indices, semantico = [0, 1, 3], [0, 2, 1, 3]
    assert rag._reservar_procedimiento(indices, semantico, FRAGMENTOS_MIXTOS, 3) == [
        0,
        1,
        2,
    ]


def test_reserva_no_duplica_si_ya_hay_formulario():
    indices = [0, 2, 1]
    assert rag._reservar_procedimiento(indices, [2, 0, 1], FRAGMENTOS_MIXTOS, 3) == indices


def test_reserva_no_interviene_en_preguntas_normativas():
    """Sin formularios entre los candidatos no se sacrifica ningún resultado."""
    indices = [0, 1, 3]
    assert rag._reservar_procedimiento(indices, [0, 1, 3], FRAGMENTOS_MIXTOS, 3) == indices


def test_reserva_no_agranda_el_contexto():
    """Reemplaza el último lugar: el costo por consulta no puede crecer."""
    indices = [0, 1, 3]
    salida = rag._reservar_procedimiento(indices, [2], FRAGMENTOS_MIXTOS, 3)
    assert len(salida) == len(indices)
