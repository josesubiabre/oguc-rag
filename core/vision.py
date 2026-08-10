"""Extracción de documentos escaneados mediante lectura visual (Gemini).

Los PDF escaneados no tienen capa de texto: pypdf no extrae nada de ellos.
Aquí cada página se renderiza como imagen y un modelo con visión describe su
contenido, incluyendo lo que muestran los diagramas y esquemas — que es
justamente el valor de un manual ilustrado.

El resultado se guarda en `data/02_processed/vision/<nombre>.extracted.json`,
separado de los PDF originales, así el proceso es reanudable y la ingesta
normal lo reutiliza sin volver a pagar.
"""

import base64
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf
import requests

# Las extracciones no son fuente oficial: viven separadas de los PDF para que
# nadie las confunda con un documento descargado del MINVU o de Ley Chile.
from core.config import FALLBACK_MODEL, GEMINI_API_KEY, VISION_DIR

DPI = 150
MAX_OUTPUT_TOKENS = 4000
WORKERS = 6  # páginas simultáneas; el tier pagado de Gemini lo tolera holgado

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
    return VISION_DIR / f"{Path(pdf_path).stem}.extracted.json"


def extract_document(pdf_path, on_progress=None):
    """Describe cada página del PDF. Reanudable: reutiliza lo ya extraído.

    Las páginas se procesan en paralelo porque cada una es independiente y
    la latencia es de red, no de CPU.
    """
    pdf_path = Path(pdf_path)
    destino = extracted_path(pdf_path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    paginas = json.loads(destino.read_text(encoding="utf-8")) if destino.exists() else {}

    doc = pymupdf.open(pdf_path)
    total = doc.page_count
    # Una página guardada como cadena vacía falló: se reintenta en la
    # siguiente pasada. SIN_CONTENIDO sí es un resultado válido y definitivo.
    pendientes = [i for i in range(total) if not paginas.get(str(i + 1))]

    # PyMuPDF no garantiza acceso concurrente al documento: el renderizado
    # se serializa y solo la llamada de red va en paralelo.
    doc_lock = threading.Lock()
    state_lock = threading.Lock()
    hechas = [0]

    def procesar(i):
        with doc_lock:
            img = doc[i].get_pixmap(dpi=DPI).tobytes("png")
        texto, detalle = "", ""
        for intento in range(3):
            try:
                texto = _describe_page(img)
                detalle = f"{len(texto)} chars"
                break
            except Exception as e:
                detalle = f"error: {str(e)[:60]}"
                if intento < 2:
                    time.sleep(5 * (intento + 1))
        with state_lock:
            paginas[str(i + 1)] = texto
            hechas[0] += 1
            if hechas[0] % 10 == 0 or hechas[0] == len(pendientes):
                destino.write_text(
                    json.dumps(paginas, ensure_ascii=False), encoding="utf-8"
                )
            if on_progress:
                on_progress(hechas[0], len(pendientes), detalle)

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            list(pool.map(procesar, pendientes))
    finally:
        with state_lock:
            destino.write_text(
                json.dumps(paginas, ensure_ascii=False), encoding="utf-8"
            )
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
