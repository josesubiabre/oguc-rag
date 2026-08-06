"""Cliente de embeddings (API REST de Gemini).

Único módulo que conoce el proveedor de embeddings: para cambiar de
proveedor, basta con reemplazar este archivo manteniendo las firmas.
"""

import time

import numpy as np
import requests

from core.config import EMBED_DIM, EMBED_MODEL, GEMINI_API_KEY

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _embed(text, task_type):
    url = f"{_BASE}/{EMBED_MODEL}:embedContent?key={GEMINI_API_KEY}"
    body = {
        "model": f"models/{EMBED_MODEL}",
        "content": {"parts": [{"text": text}]},
        "taskType": task_type,
        "outputDimensionality": EMBED_DIM,
    }
    for attempt in range(8):
        r = requests.post(url, json=body, timeout=60)
        if r.status_code == 429:
            wait = min(15 * (attempt + 1), 60)
            print(f"  límite de tasa, esperando {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()["embedding"]["values"]
    raise RuntimeError(f"Demasiados reintentos contra la API de Gemini: {r.text[:1500]}")


def embed_query(text):
    """Vector normalizado para una pregunta de usuario."""
    v = np.array(_embed(text, "RETRIEVAL_QUERY"), dtype=np.float32)
    return v / np.linalg.norm(v)


def embed_documents(texts):
    """Vectores (sin normalizar) para una lista de fragmentos de documento.

    Intenta el endpoint batch; si el tier lo rechaza, cae a peticiones
    de a una con pausa entre ellas.
    """
    url = f"{_BASE}/{EMBED_MODEL}:batchEmbedContents?key={GEMINI_API_KEY}"
    body = {
        "requests": [
            {
                "model": f"models/{EMBED_MODEL}",
                "content": {"parts": [{"text": t}]},
                "taskType": "RETRIEVAL_DOCUMENT",
                "outputDimensionality": EMBED_DIM,
            }
            for t in texts
        ]
    }
    r = requests.post(url, json=body, timeout=120)
    if r.status_code == 200:
        return [e["values"] for e in r.json()["embeddings"]]

    vectors = []
    for t in texts:
        vectors.append(_embed(t, "RETRIEVAL_DOCUMENT"))
        time.sleep(0.5)
    return vectors
