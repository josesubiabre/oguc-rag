"""Extracción de documentos escaneados mediante lectura visual (Gemini).

Los PDF escaneados no tienen capa de texto: pypdf no extrae nada de ellos.
Aquí cada página se renderiza como imagen y un modelo con visión describe su
contenido, incluyendo lo que muestran los diagramas y esquemas — que es
justamente el valor de un manual ilustrado.

El resultado se guarda junto al PDF como `<nombre>.extracted.json`, así el
proceso es reanudable y la ingesta normal lo reutiliza sin volver a pagar.
"""

import base64
import json
import time
from pathlib import Path

import pymupdf
import requests

from core.config import FALLBACK_MODEL, GEMINI_API_KEY

DPI = 150
MAX_OUTPUT_TOKENS = 4000

# Pedir transcripción literal hace que Gemini bloquee la respuesta por
# recitación de material con copyright. Parafrasear evita el bloqueo y,
# además, produce texto más útil para búsqueda semántica.
PROMPT = (
    "Esta es una página de un manual ilustrado de normativa chilena de "
    "urbanismo y construcción. Explica con tus propias palabras, de forma "
    "técnica y precisa, qué regla o concepto normativo se aborda. Indica el "
    "número de artículo si aparece. Si hay diagramas, esquemas, cortes, "
    "plantas o tablas, describe qué muestra cada uno: qué elementos "
    "aparecen, qué dimensiones o distancias se acotan y qué condición "
    "normativa ilustran. No copies el texto literal: parafrasea y "
    "sintetiza. Si la página no tiene contenido normativo (portada, índice, "
    "página en blanco), responde solamente: SIN_CONTENIDO"
)


def _describe_page(image_bytes):
    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{FALLBACK_MODEL}:generateContent",
        headers={"x-goog-api-key": GEMINI_API_KEY},
        json={
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": PROMPT},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64.b64encode(image_bytes).decode(),
                        }
                    },
                ],
            }],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": MAX_OUTPUT_TOKENS,
            },
        },
        timeout=180,
    )
    r.raise_for_status()
    candidate = r.json()["candidates"][0]
    # RECITATION u otros filtros dejan la respuesta sin partes: se omite
    parts = candidate.get("content", {}).get("parts", [])
    return "".join(p["text"] for p in parts if "text" in p).strip()


def extracted_path(pdf_path):
    return Path(pdf_path).with_suffix(".extracted.json")


def extract_document(pdf_path, on_progress=None):
    """Describe cada página del PDF. Reanudable: reutiliza lo ya extraído."""
    pdf_path = Path(pdf_path)
    destino = extracted_path(pdf_path)
    paginas = json.loads(destino.read_text(encoding="utf-8")) if destino.exists() else {}

    doc = pymupdf.open(pdf_path)
    try:
        for i in range(doc.page_count):
            clave = str(i + 1)
            if clave in paginas:
                continue
            pix = doc[i].get_pixmap(dpi=DPI)
            try:
                texto = _describe_page(pix.tobytes("png"))
            except Exception as e:
                # Una página problemática no debe abortar el documento
                texto = ""
                if on_progress:
                    on_progress(i + 1, doc.page_count, f"error: {str(e)[:80]}")
            paginas[clave] = texto
            if on_progress:
                on_progress(i + 1, doc.page_count, f"{len(texto)} chars")
            destino.write_text(
                json.dumps(paginas, ensure_ascii=False), encoding="utf-8"
            )
            time.sleep(0.2)
    finally:
        doc.close()
    return paginas


def load_extracted(pdf_path):
    """Devuelve [(página, texto)] si existe extracción visual; si no, None."""
    destino = extracted_path(pdf_path)
    if not destino.exists():
        return None
    paginas = json.loads(destino.read_text(encoding="utf-8"))
    return [
        (int(n), t)
        for n, t in sorted(paginas.items(), key=lambda kv: int(kv[0]))
        if t and t != "SIN_CONTENIDO"
    ]
