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
    """Devuelve (texto de respuesta, páginas fuente ordenadas)."""
    qvec = embed_query(question)
    hits = _store().search(qvec, k)
    context = "\n\n---\n\n".join(h["text"] for h in hits)
    text = generate_answer(question, context)
    pages = sorted({h["page"] for h in hits})
    return text, pages
