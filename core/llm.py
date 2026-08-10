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

def _avisos_de_vigencia():
    """Reemplazos normativos que el corpus todavía cita como vigentes.

    Una circular de 2017 puede seguir vigente y aun así invocar una ley
    derogada: 130 fragmentos citan la Ley 19.537, sustituida en 2022. Esta es
    la primera de tres barreras —aquí, la anotación del contexto y el chequeo
    de la respuesta—, y cubre el caso en que el modelo razona sobre una norma
    que no venía en los fragmentos recuperados. Los datos salen de la tabla de
    vigencia, única fuente, para que sumar un caso sea editar un dato.
    """
    try:
        from core.vigencia import derogadas

        derogaciones = derogadas()
    except Exception:
        return ""
    if not derogaciones:
        return ""

    casos = []
    for d in derogaciones:
        fecha = "-".join(reversed(d["fecha_estado"].split("-")))
        caso = (
            f"La {d['norma']} ({d['nombre']}) fue derogada por la "
            f"{d['reemplazada_por']} el {fecha}, según el {d['base_legal']}"
        )
        if d.get("regla_de_reenvio"):
            caso += f"; {d['regla_de_reenvio']}"
        casos.append(caso + ".")

    return (
        "Vigencia de las referencias: parte del corpus es anterior a reformas "
        "recientes y cita normas ya derogadas. " + " ".join(casos) + " Si un "
        "fragmento del contexto invoca una de esas normas derogadas, no la "
        "presentes como vigente: responde según el cuerpo legal que la "
        "reemplazó, aplica el reenvío y advierte del cambio. "
    )


_PROMPT_BASE = (
    "Eres un asistente experto en normativa chilena de urbanismo y "
    "construcción: la OGUC, la LGUC, la Ley de Copropiedad, el DS 50 de "
    "accesibilidad, las circulares DDU del MINVU y los Formularios Únicos "
    "Nacionales que las Direcciones de Obras Municipales exigen para cada "
    "trámite. Responde usando ÚNICAMENTE el contexto entregado. Cada "
    "fragmento del contexto indica entre corchetes su documento de origen: "
    "cita siempre el documento y el número de artículo cuando sea posible. "
    "Los fragmentos cuya fuente empieza con 'Formulario MINVU' son "
    "procedimiento, no norma: indican qué antecedentes pide la DOM en cada "
    "trámite. Úsalos para responder qué documentos hay que presentar, "
    "atribuyéndolos siempre al formulario, y nunca los cites como si fueran "
    "una exigencia legal ni les asignes rango de ley o de artículo. "
    "El texto vigente de cada artículo de la LGUC es el del fragmento "
    "titulado LGUC. Si el contexto trae fragmentos de la Ley 21.807, no "
    "reproduzcas sus instrucciones de reemplazo ni expliques esta regla en tu "
    "respuesta; menciona esa ley solo si te preguntan qué cambió o desde "
    "cuándo. "
)

_CIERRE = "Si el contexto no contiene la respuesta, dilo claramente y no inventes."

SYSTEM_PROMPT = _PROMPT_BASE + _avisos_de_vigencia() + _CIERRE


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
                # Sin razonamiento extendido: es un respaldo que actúa bajo
                # carga, donde la latencia importa más que la deliberación.
                # thinkingLevel es el parámetro vigente para modelos Gemini 3;
                # el heredado thinkingBudget no es válido en las variantes Lite.
                "thinkingConfig": {"thinkingLevel": "minimal"},
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


def corregir_respuesta(instruccion, respuesta, context):
    """Segunda pasada sobre una respuesta que citó normas derogadas.

    Se reescribe en vez de anexar una advertencia: una nota al pie debajo de
    un párrafo que afirma lo contrario deja al lector eligiendo cuál creer.
    """
    contenido = f"{instruccion}\n\n--- Respuesta a corregir ---\n{respuesta}"
    return generate_answer(contenido, context)


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
