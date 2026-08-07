"""API web de NormaObra.

Uso local:
    uvicorn app:app --reload
El frontend vive en web/ (Next.js) y reenvía /api/* a este servidor.
"""

import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.analytics import log_query
from core.rag import answer

# Sin documentación interactiva pública: el API tiene un solo endpoint y
# exponer /docs solo facilita el reconocimiento a terceros.
app = FastAPI(title="NormaObra API", docs_url=None, redoc_url=None, openapi_url=None)


class Question(BaseModel):
    question: str


@app.get("/")
def home():
    return {"status": "ok", "service": "NormaObra API"}


@app.post("/api/ask")
def ask(q: Question):
    question = q.question.strip()
    if not question or len(question) > 500:
        raise HTTPException(400, "La pregunta debe tener entre 1 y 500 caracteres")

    started = time.time()
    try:
        text, sources, provider = answer(question)
    except Exception as e:
        log_query(question, int((time.time() - started) * 1000), error=e)
        raise HTTPException(503, "El servicio está saturado, intenta de nuevo en unos segundos")

    log_query(
        question,
        int((time.time() - started) * 1000),
        sources=sources,
        answer_text=text,
        provider=provider,
    )
    return {"answer": text, "sources": sources}
