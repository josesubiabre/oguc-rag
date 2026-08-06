"""Generación de respuestas (Groq). Único módulo que conoce el LLM y el prompt."""

from functools import lru_cache

from groq import Groq

from core.config import GROQ_API_KEY, LLM_MODEL

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
    return Groq(api_key=GROQ_API_KEY)


def generate_answer(question, context):
    resp = _client().chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Contexto:\n{context}\n\nPregunta: {question}"},
        ],
    )
    return resp.choices[0].message.content
