"""Interfaz web del asistente OGUC.

Uso local:
    uvicorn app:app --reload
Luego abre http://localhost:8000
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from groq import Groq
from pydantic import BaseModel

from query import answer, load_store

load_dotenv()

app = FastAPI(title="Asistente OGUC")

matrix, chunks = load_store()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GEMINI_KEY = os.getenv("GEMINI_API_KEY")


class Question(BaseModel):
    question: str


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/api/ask")
def ask(q: Question):
    question = q.question.strip()
    if not question or len(question) > 500:
        raise HTTPException(400, "La pregunta debe tener entre 1 y 500 caracteres")
    try:
        text, pages = answer(question, matrix, chunks, GEMINI_KEY, client)
    except Exception:
        raise HTTPException(503, "El servicio está saturado, intenta de nuevo en unos segundos")
    return {"answer": text, "pages": pages}
