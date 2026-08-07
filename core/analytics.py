"""Registro de uso: qué se pregunta, cuánto tarda y cuándo falla.

Dos capas, ambas opcionales y nunca bloqueantes:

1. stdout en formato JSON — visible siempre en los logs de Vercel, sin
   configuración ni costo, pero con retención corta.
2. Upstash Redis (REST) — persistencia real para análisis histórico. Se
   activa solo si existen UPSTASH_REDIS_REST_URL y UPSTASH_REDIS_REST_TOKEN.

No se registra IP, user agent ni identificador de usuario: solo el texto de
la consulta y métricas de servicio.
"""

import json
import os
import time

import requests

REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
LIST_KEY = "normaobra:queries"
MAX_EVENTS = 5000

# Frases con que el modelo declara que la normativa indexada no cubre la
# consulta. Detectarlas revela vacíos del corpus, no fallas del servicio.
_SIN_COBERTURA = (
    "no contiene la respuesta",
    "no se especifica",
    "no hay información",
    "no se menciona",
    "no puedo responder",
    "no se encuentra",
)


def _persist(event):
    if not REDIS_URL or not REDIS_TOKEN:
        return
    # LPUSH + LTRIM en un pipeline: mantiene solo los últimos MAX_EVENTS
    requests.post(
        f"{REDIS_URL}/pipeline",
        headers={"Authorization": f"Bearer {REDIS_TOKEN}"},
        json=[
            ["LPUSH", LIST_KEY, json.dumps(event, ensure_ascii=False)],
            ["LTRIM", LIST_KEY, "0", str(MAX_EVENTS - 1)],
        ],
        timeout=5,
    )


def log_query(
    question,
    latency_ms,
    sources=None,
    answer_text=None,
    error=None,
    provider=None,
    mode=None,
):
    """Registra una consulta. Nunca lanza: la analítica no puede romper la app."""
    try:
        event = {
            "ts": int(time.time()),
            "question": question[:500],
            "latency_ms": latency_ms,
            "ok": error is None,
        }
        if provider:
            event["provider"] = provider
        if mode:
            event["mode"] = mode  # hybrid | semantic | bm25_fallback
        if error:
            event["error"] = str(error)[:200]
        if sources:
            event["sources"] = [s["source"] for s in sources]
        if answer_text:
            lowered = answer_text.lower()
            event["sin_cobertura"] = any(f in lowered for f in _SIN_COBERTURA)
        print(json.dumps({"analytics": event}, ensure_ascii=False), flush=True)
        _persist(event)
    except Exception:
        pass
