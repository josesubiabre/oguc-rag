"""Registro de las fuentes del corpus: qué es cada archivo, de qué versión y
de dónde salió.

Deliberadamente el manifiesto **no gobierna la ingesta**. Si `corpus_files()`
dependiera de él, una entrada mal escrita dejaría un documento fuera del
índice sin que nadie se entere. En cambio se contrasta contra tres cosas —el
disco, el índice y las fuentes oficiales— de modo que una discrepancia se
denuncia en vez de propagarse en silencio.
"""

import hashlib
import json
from datetime import date, datetime
from pathlib import Path

from core.config import DATA_DIR

MANIFEST_PATH = DATA_DIR / "manifest.json"
MESES = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}


def cargar(path=MANIFEST_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def guardar(datos, path=MANIFEST_PATH):
    """Escritura atómica: un fallo a medias dejaría el registro ilegible."""
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp.replace(path)


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def ruta_absoluta(entrada, data_dir=DATA_DIR):
    return Path(data_dir) / entrada["ruta"]


def fecha_leychile(texto):
    """Convierte '24-JUN-2026' a date. Devuelve None si no es esa forma."""
    partes = texto.strip().upper().split("-")
    if len(partes) != 3 or partes[1] not in MESES:
        return None
    try:
        return date(int(partes[2]), MESES[partes[1]], int(partes[0]))
    except ValueError:
        return None


def dias_restantes(fecha_iso, hoy=None):
    """Días hasta la fecha dada. Negativo si ya pasó, None si no hay fecha."""
    if not fecha_iso:
        return None
    hoy = hoy or date.today()
    objetivo = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
    return (objetivo - hoy).days


def entradas(datos):
    """Documentos y colecciones juntos, para recorrerlos de una sola forma."""
    return [*datos.get("documentos", []), *datos.get("colecciones", [])]
