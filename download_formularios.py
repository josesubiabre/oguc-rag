"""Descarga los Formularios Únicos Nacionales del MINVU a data/formularios/.

Fuente: página oficial de formularios de permisos de edificación. Son los
formularios que las Direcciones de Obras Municipales exigen para cada
actuación (anteproyecto, permiso, modificación, recepción definitiva), más
las declaraciones juradas y los documentos que emite la propia DOM.

A diferencia de la OGUC o las circulares DDU, no son normas: son el
procedimiento. Se indexan como categoría aparte para que las respuestas no
los citen con el mismo rango que una ley.

Idempotente: los archivos ya descargados se saltan; se puede reanudar.
Uso:
    python download_formularios.py
"""

import re
import time

import requests

from core.config import ROOT

FORM_DIR = ROOT / "data" / "formularios"
INDICE_URL = (
    "https://www.minvu.gob.cl/elementos-tecnicos/formularios/"
    "formularios-de-permisos-de-edificacion/"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (proyecto educativo RAG normativa urbanismo Chile)"}


def pdf_links(page_url):
    html = requests.get(page_url, headers=HEADERS, timeout=60).text
    return sorted(set(re.findall(r'href="(https?://[^"]+\.pdf)"', html, re.IGNORECASE)))


def main():
    print("Leyendo el índice de formularios del MINVU...")
    targets = pdf_links(INDICE_URL)
    print(f"  {len(targets)} formularios en el índice")

    FORM_DIR.mkdir(parents=True, exist_ok=True)
    ok = skipped = failed = 0
    for i, url in enumerate(targets, 1):
        dest = FORM_DIR / url.split("/")[-1]
        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=120)
            r.raise_for_status()
            dest.write_bytes(r.content)
            ok += 1
        except Exception as e:
            failed += 1
            print(f"  fallo {url.split('/')[-1]}: {e}")
        if i % 10 == 0:
            print(f"  {i}/{len(targets)}")
        time.sleep(0.3)  # cortesía con el servidor del MINVU

    peso = sum(f.stat().st_size for f in FORM_DIR.glob("*.pdf")) / 1024 / 1024
    print(f"Listo: {ok} descargados, {skipped} ya existían, {failed} fallidos")
    print(f"  {len(list(FORM_DIR.glob('*.pdf')))} archivos, {peso:.1f} MB en total")


if __name__ == "__main__":
    main()
