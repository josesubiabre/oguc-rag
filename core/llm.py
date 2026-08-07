"""Generación de respuestas. Único módulo que conoce los LLM y el prompt.

Estrategia de dos proveedores: Groq responde rápido y gratis, pero su tier
gratuito tope en 12.000 tokens por minuto (~4 consultas). Cuando se satura,
Gemini toma el relevo automáticamente: tiene límites mucho más altos y un
costo marginal bajo, así que el usuario nunca ve un error por demanda.
"""

from functools import lru_cache

import requests
from groq import Groq

from core.config import (
    FALLBACK_MODEL,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    LLM_MODEL,
)

SYSTEM_PROMPT = (
    "Eres un asistente experto en normativa chilena de urbanismo y "
    "construcción: la OGUC, la LGUC, la Ley de Copropiedad, el DS 50 de "
    "accesibilidad y las circulares DDU del MINVU. Responde usando "
    "ÚNICAMENTE el contexto entregado. Cada fragmento del contexto indica "
    "entre corchetes su documento de origen: cita siempre el documento y el "
    "número de artículo cuando sea posible. Si el contexto no contiene la "
    "respuesta, dilo claramente y no inventes."
)


@lru_cache(maxsize=1)
def _client():
    # Sin reintentos internos: ante saturación queremos pasar a Gemini de
    # inmediato, no esperar los ~28s que el SDK reintenta por su cuenta.
    return Groq(api_key=GROQ_API_KEY, max_retries=0, timeout=20.0)


def _ask_groq(user_content):
    resp = _client().chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    return resp.choices[0].message.content


def _ask_gemini(user_content):
    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{FALLBACK_MODEL}:generateContent",
        headers={"x-goog-api-key": GEMINI_API_KEY},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
            "generationConfig": {
                "temperature": 0,
                # Sin razonamiento extendido: con él la respuesta tarda ~30s;
                # sin él, ~1,5s con la misma calidad para este caso de uso.
                "thinkingConfig": {"thinkingBudget": 0},
            },
        },
        timeout=60,
    )
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p["text"] for p in parts if "text" in p)


def generate_answer(question, context):
    """Devuelve (respuesta, proveedor usado)."""
    user_content = f"Contexto:\n{context}\n\nPregunta: {question}"
    try:
        return _ask_groq(user_content), "groq"
    except Exception:
        # Saturación o caída de Groq: seguimos con Gemini en vez de fallar
        return _ask_gemini(user_content), "gemini"


def extractive_answer(hits):
    """Respuesta sin modelo: los fragmentos recuperados, con su origen.

    Se usa cuando ningún proveedor de generación responde. La búsqueda ya
    encontró material relevante, así que entregarlo es más útil que un error.
    """
    partes = [
        "⚠️ La redacción automática de respuestas está temporalmente no "
        "disponible. Estos son los fragmentos de la normativa que mejor "
        "coinciden con tu consulta, para que los revises directamente:\n"
    ]
    for h in hits:
        texto = h["text"].strip()
        if len(texto) > 900:
            texto = texto[:900].rsplit(" ", 1)[0] + "…"
        partes.append(f"— {h.get('source', 'OGUC')}, página {h['page']}:\n{texto}")
    return "\n\n".join(partes)
