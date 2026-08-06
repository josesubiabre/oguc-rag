"""Orquestación RAG: pregunta → recuperación → respuesta con fuentes."""

from functools import lru_cache

from core.config import TOP_K
from core.embeddings import embed_query
from core.llm import generate_answer
from core.store import VectorStore


@lru_cache(maxsize=1)
def _store():
    return VectorStore.load()


def answer(question, k=TOP_K):
    """Devuelve (texto, fuentes), con fuentes = [{"source", "pages"}, ...]."""
    qvec = embed_query(question)
    hits = _store().search(qvec, k)
    context = "\n\n---\n\n".join(
        f"[{h.get('source', 'OGUC')}, página {h['page']}]\n{h['text']}" for h in hits
    )
    text = generate_answer(question, context)

    by_source = {}
    for h in hits:
        by_source.setdefault(h.get("source", "OGUC"), set()).add(h["page"])
    sources = [
        {"source": s, "pages": sorted(p)} for s, p in sorted(by_source.items())
    ]
    return text, sources
