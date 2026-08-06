"""Cliente de embeddings (API REST de Gemini).

Único módulo que conoce el proveedor de embeddings: para cambiar de
proveedor, basta con reemplazar este archivo manteniendo las firmas.
"""

import time

import numpy as np
import requests

from core.config import EMBED_DIM, EMBED_MODEL, GEMINI_API_KEY

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _headers():
    # La key va en el header y no en la URL: las URLs quedan registradas en
    # logs de errores y proxies; los headers no.
    return {"x-goog-api-key": GEMINI_API_KEY}


def _embed(text, task_type):
    url = f"{_BASE}/{EMBED_MODEL}:embedContent"
    body = {
        "model": f"models/{EMBED_MODEL}",
        "content": {"parts": [{"text": text}]},
        "taskType": task_type,
        "outputDimensionality": EMBED_DIM,
    }
    last_error = "sin detalle"
    for attempt in range(8):
        try:
            r = requests.post(url, json=body, headers=_headers(), timeout=60)
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            wait = min(5 * (attempt + 1), 30)
            print(f"  error de conexión, reintentando en {wait}s...")
            time.sleep(wait)
            continue
        if r.status_code == 429:
            last_error = r.text[:1500]
            wait = min(15 * (attempt + 1), 60)
            print(f"  límite de tasa, esperando {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()["embedding"]["values"]
    raise RuntimeError(f"Demasiados reintentos contra la API de Gemini: {last_error}")


def embed_query(text):
    """Vector normalizado para una pregunta de usuario."""
    v = np.array(_embed(text, "RETRIEVAL_QUERY"), dtype=np.float32)
    return v / np.linalg.norm(v)


def embed_documents(texts):
    """Vectores (sin normalizar) para una lista de fragmentos de documento.

    Intenta el endpoint batch; si el tier lo rechaza, cae a peticiones
    de a una con pausa entre ellas.
    """
    url = f"{_BASE}/{EMBED_MODEL}:batchEmbedContents"
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
    try:
        r = requests.post(url, json=body, headers=_headers(), timeout=120)
        if r.status_code == 200:
            return [e["values"] for e in r.json()["embeddings"]]
    except requests.exceptions.RequestException:
        pass  # cae al modo de a uno, que tiene reintentos

    vectors = []
    for t in texts:
        vectors.append(_embed(t, "RETRIEVAL_DOCUMENT"))
        time.sleep(0.5)
    return vectors
