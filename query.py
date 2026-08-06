"""Consulta la OGUC en lenguaje natural desde la terminal.

Requiere haber ejecutado antes ingest.py. Uso:
    python query.py
"""

import json
import os

import numpy as np
import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

STORE_DIR = "store"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768
LLM_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

SYSTEM_PROMPT = (
    "Eres un asistente experto en la Ordenanza General de Urbanismo y "
    "Construcciones (OGUC) de Chile. Responde usando ÚNICAMENTE el contexto "
    "entregado. Cita siempre el número de artículo cuando sea posible. Si el "
    "contexto no contiene la respuesta, dilo claramente y no inventes."
)


def embed_query(text, api_key):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{EMBED_MODEL}:embedContent?key={api_key}"
    )
    body = {
        "model": f"models/{EMBED_MODEL}",
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_QUERY",
        "outputDimensionality": EMBED_DIM,
    }
    r = requests.post(url, json=body, timeout=60)
    r.raise_for_status()
    v = np.array(r.json()["embedding"]["values"], dtype=np.float32)
    return v / np.linalg.norm(v)


def load_store():
    matrix = np.load(os.path.join(STORE_DIR, "embeddings.npy"))
    with open(os.path.join(STORE_DIR, "chunks.json"), encoding="utf-8") as f:
        chunks = json.load(f)
    return matrix, chunks


def answer(question, matrix, chunks, gemini_key, client):
    """Devuelve (respuesta, páginas fuente) para una pregunta."""
    qvec = embed_query(question, gemini_key)
    scores = matrix @ qvec
    top = np.argsort(scores)[::-1][:TOP_K]
    context = "\n\n---\n\n".join(chunks[i]["text"] for i in top)

    resp = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Contexto:\n{context}\n\nPregunta: {question}"},
        ],
    )
    pages = sorted({chunks[i]["page"] for i in top})
    return resp.choices[0].message.content, pages


def main():
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not gemini_key or "pega_tu_key" in gemini_key:
        print("Falta GEMINI_API_KEY en .env (aistudio.google.com)")
        return
    if not groq_key or "pega_tu_key" in groq_key:
        print("Falta GROQ_API_KEY en .env (console.groq.com)")
        return
    if not os.path.exists(os.path.join(STORE_DIR, "embeddings.npy")):
        print("No existe la base vectorial: ejecuta primero  python ingest.py")
        return

    matrix, chunks = load_store()
    client = Groq(api_key=groq_key)

    print("Pregúntale a la OGUC (escribe 'salir' para terminar)\n")
    while True:
        question = input("Pregunta: ").strip()
        if not question or question.lower() in ("salir", "exit", "quit"):
            break
        text, pages = answer(question, matrix, chunks, gemini_key, client)
        print(f"\n{text}\n")
        print(f"(Fuentes: páginas {', '.join(map(str, pages))} del PDF)\n")


if __name__ == "__main__":
    main()
