"""Procesa PDF escaneados (sin capa de texto) con lectura visual.

Los manuales ilustrados son escaneos: pypdf no extrae nada de ellos. Este
script describe cada página con un modelo de visión, incluyendo lo que
muestran los diagramas, y deja el resultado listo para `python ingest.py`.

Uso:
    python ingest_vision.py                 # procesa los escaneos de 01_sources
    python ingest_vision.py ruta/al.pdf     # procesa un archivo puntual

Es reanudable: si se interrumpe, al repetir continúa donde quedó.
"""

import sys
from pathlib import Path

from core.config import GEMINI_API_KEY, ILUSTRADA_DIR
from core.vision import extract_document, extracted_path

DEFAULT_DIR = ILUSTRADA_DIR


def main():
    if not GEMINI_API_KEY or "pega_tu_key" in GEMINI_API_KEY:
        print("Falta GEMINI_API_KEY en .env")
        return

    if len(sys.argv) > 1:
        pdfs = [Path(sys.argv[1])]
    else:
        DEFAULT_DIR.mkdir(parents=True, exist_ok=True)
        pdfs = sorted(DEFAULT_DIR.glob("*.pdf"))

    if not pdfs:
        print(f"No hay PDF en {DEFAULT_DIR}/")
        print("Copia ahí los manuales escaneados y vuelve a ejecutar.")
        return

    for pdf in pdfs:
        print(f"\n=== {pdf.name}")

        def progreso(actual, total, detalle):
            fin = "\n" if actual == total else "\r"
            print(f"  página {actual}/{total} · {detalle}      ", end=fin, flush=True)

        paginas = extract_document(pdf, on_progress=progreso)
        utiles = sum(1 for t in paginas.values() if t and t != "SIN_CONTENIDO")
        print(f"  listo: {utiles} páginas con contenido -> {extracted_path(pdf).name}")

    print("\nAhora ejecuta:  python ingest.py")


if __name__ == "__main__":
    main()
