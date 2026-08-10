"""Descarga las circulares DDU generales vigentes del MINVU.

Destino: data/01_sources/interpretacion_oficial/ddu_generales/. Se conservan
los nombres de archivo del MINVU: son la clave con que este script decide qué
ya está descargado, así que renombrarlos obligaría a bajar las 250 de nuevo.

Fuente: página oficial "circulares generales por número". Se excluyen las
que aparecen en la página de derogadas o cuyo nombre indica derogación.

Idempotente: los archivos ya descargados se saltan; se puede reanudar.
Uso:
    python download_ddu.py
"""

import re
import time

import requests

from core.config import DDU_DIR
BASE = "https://www.minvu.gob.cl/elementos-tecnicos/circulares-division-de-desarrollo-urbano-ddu"
VIGENTES_URL = f"{BASE}/circulares-generales-por-numero/"
DEROGADAS_URL = f"{BASE}/circulares-derogadas/"
HEADERS = {"User-Agent": "Mozilla/5.0 (proyecto educativo RAG normativa urbanismo Chile)"}


def pdf_links(page_url):
    html = requests.get(page_url, headers=HEADERS, timeout=60).text
    links = set(re.findall(r'href="(https?://[^"]+\.pdf)"', html))
    return {u for u in links if re.search(r"DDU|CIR-", u, re.IGNORECASE)}


def main():
    print("Leyendo índices del MINVU...")
    vigentes = pdf_links(VIGENTES_URL)
    derogadas = pdf_links(DEROGADAS_URL)

    targets = sorted(
        u for u in vigentes - derogadas
        if not re.search(r"derogad|deja-sin-efecto", u, re.IGNORECASE)
    )
    print(f"  {len(vigentes)} en el índice, {len(targets)} vigentes a descargar")

    DDU_DIR.mkdir(parents=True, exist_ok=True)
    ok = skipped = failed = 0
    for i, url in enumerate(targets, 1):
        dest = DDU_DIR / url.split("/")[-1]
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
        if i % 25 == 0:
            print(f"  {i}/{len(targets)}")
        time.sleep(0.3)  # cortesía con el servidor del MINVU

    print(f"Listo: {ok} descargadas, {skipped} ya existían, {failed} fallidas")


if __name__ == "__main__":
    main()
