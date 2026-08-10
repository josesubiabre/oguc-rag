"""Comprueba que el corpus siga siendo el que el manifiesto declara.

Una respuesta puede ser perfecta y aun así estar equivocada, si el texto de
origen dejó de regir. Este script no lee normativa: audita metadatos. Revisa
cuatro cosas, en orden de gravedad:

1. Integridad   — el archivo existe y su hash es el registrado.
2. Vigencia     — ninguna versión declarada ha caducado.
3. Colecciones  — las circulares y formularios siguen coincidiendo con el
                  índice publicado por el MINVU.
4. Coherencia   — lo que el manifiesto declara está realmente en el índice.

Termina con código 1 si algo necesita atención, para poder automatizarlo.

Uso:
    python check_vigencia.py              # comprueba todo
    python check_vigencia.py --offline    # omite las consultas al MINVU
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import requests

from core.config import DATA_DIR, STORE_DIR
from core.manifest import cargar, dias_restantes, entradas, guardar, sha256

HEADERS = {"User-Agent": "Mozilla/5.0 (proyecto educativo RAG normativa urbanismo Chile)"}
AVISO_DIAS = 30  # margen para reaccionar antes de que una versión caduque


def _indice_pdf(url, patron):
    html = requests.get(url, headers=HEADERS, timeout=60).text
    enlaces = set(re.findall(r'href="(https?://[^"]+\.pdf)"', html, re.IGNORECASE))
    if patron:
        enlaces = {u for u in enlaces if re.search(patron, u, re.IGNORECASE)}
    return enlaces


def revisar_integridad(datos, hallazgos):
    for d in datos["documentos"]:
        ruta = DATA_DIR / d["ruta"]
        if not ruta.exists():
            hallazgos.append(("ERROR", d["id"], f"falta el archivo: {d['ruta']}"))
            continue
        if sha256(ruta) != d["sha256"]:
            hallazgos.append(
                ("ERROR", d["id"], "el archivo cambió sin actualizar el manifiesto")
            )


def revisar_vigencia(datos, hoy, hallazgos):
    for d in datos["documentos"]:
        dias = dias_restantes(d.get("fin_vigencia"), hoy)
        if dias is None:
            continue
        if dias < 0:
            hallazgos.append(
                ("ERROR", d["id"], f"versión caducada hace {-dias} días "
                 f"(fin de vigencia {d['fin_vigencia']}); descargar la nueva desde "
                 f"{d.get('url_oficial') or 'la fuente oficial'}")
            )
        elif dias <= AVISO_DIAS:
            hallazgos.append(
                ("AVISO", d["id"], f"la versión vigente caduca en {dias} días "
                 f"({d['fin_vigencia']})")
            )


def revisar_colecciones(datos, offline, hallazgos):
    for c in datos["colecciones"]:
        carpeta = DATA_DIR / c["directorio"]
        locales = {p.name for p in carpeta.glob("*.pdf")}
        if len(locales) != c["documentos"]:
            hallazgos.append(
                ("AVISO", c["id"], f"el manifiesto declara {c['documentos']} archivos "
                 f"y en disco hay {len(locales)}")
            )
        if offline:
            continue
        try:
            remotos = {u.split("/")[-1] for u in _indice_pdf(c["url_indice"], c.get("patron"))}
            if c.get("url_derogadas"):
                derogadas = {
                    u.split("/")[-1]
                    for u in _indice_pdf(c["url_derogadas"], c.get("patron"))
                }
                remotos -= derogadas
        except Exception as e:
            hallazgos.append(("AVISO", c["id"], f"no se pudo consultar el índice: {e}"))
            continue
        nuevos, retirados = sorted(remotos - locales), sorted(locales - remotos)
        if nuevos:
            hallazgos.append(
                ("ACCION", c["id"], f"{len(nuevos)} publicaciones nuevas en el MINVU: "
                 f"{', '.join(nuevos[:5])}{' ...' if len(nuevos) > 5 else ''}")
            )
        if retirados:
            hallazgos.append(
                ("ACCION", c["id"], f"{len(retirados)} ya no figuran vigentes: "
                 f"{', '.join(retirados[:5])}{' ...' if len(retirados) > 5 else ''}")
            )


def revisar_coherencia(datos, hallazgos):
    """Lo declarado debe estar en el índice: si no, el manifiesto miente."""
    chunks_path = STORE_DIR / "chunks.json"
    if not chunks_path.exists():
        hallazgos.append(("AVISO", "indice", "no hay chunks.json que contrastar"))
        return
    fuentes = {c["source"] for c in json.loads(chunks_path.read_text(encoding="utf-8"))}
    for e in entradas(datos):
        if not e.get("en_indice"):
            continue
        cita = e["cita"]
        presente = (
            any(f.startswith(cita.split("<")[0].strip()) for f in fuentes)
            if "<" in cita
            else cita in fuentes
        )
        if not presente:
            hallazgos.append(
                ("ERROR", e["id"], f"declarado en el índice pero no hay fragmentos "
                 f"citados como «{cita}»")
            )


def revisar_datos_faltantes(datos, hallazgos):
    for d in datos["documentos"]:
        faltan = [
            campo
            for campo in ("url_oficial", "fecha_publicacion")
            if not d.get(campo) and d["categoria"] == "normativa_vigente"
        ]
        if faltan:
            hallazgos.append(
                ("PENDIENTE", d["id"], f"sin {' ni '.join(faltan)} en el manifiesto")
            )


def main():
    offline = "--offline" in sys.argv
    hoy = date.today()
    datos = cargar()
    hallazgos = []

    revisar_integridad(datos, hallazgos)
    revisar_vigencia(datos, hoy, hallazgos)
    revisar_colecciones(datos, offline, hallazgos)
    revisar_coherencia(datos, hallazgos)
    revisar_datos_faltantes(datos, hallazgos)

    print(f"Comprobacion de vigencia - {hoy.isoformat()}"
          f"{' (sin consultar el MINVU)' if offline else ''}")
    print(f"  {len(datos['documentos'])} documentos, "
          f"{len(datos['colecciones'])} colecciones\n")

    orden = {"ERROR": 0, "ACCION": 1, "AVISO": 2, "PENDIENTE": 3}
    for nivel, ident, mensaje in sorted(hallazgos, key=lambda h: orden[h[0]]):
        print(f"  [{nivel:<9}] {ident:<20} {mensaje}")
    if not hallazgos:
        print("  todo en orden")

    # Solo se sella la fecha de lo que se pudo comprobar de verdad.
    if not offline:
        for e in entradas(datos):
            e["ultima_verificacion"] = hoy.isoformat()
        datos["actualizado_al"] = hoy.isoformat()
        guardar(datos)
        print("\n  manifiesto sellado con la fecha de hoy")

    graves = [h for h in hallazgos if h[0] in ("ERROR", "ACCION")]
    print(f"\n{len(graves)} hallazgo(s) requieren accion.")
    return 1 if graves else 0


if __name__ == "__main__":
    raise SystemExit(main())
