"""Extracción del PDF y división en fragmentos por límites de 'Artículo N°'."""

import re
from pathlib import Path

from pypdf import PdfReader

from core.config import DATA_DIR, MAX_CHUNK_CHARS

# Nombres legibles para los documentos conocidos (por prefijo de archivo)
_KNOWN_SOURCES = {
    "oguc": "OGUC",
    "lguc": "LGUC",
    "ley-de-copropiedad": "Ley de Copropiedad (21.442)",
    "normativa-de-accesibilidad": "DS 50 Accesibilidad Universal",
    "oguc-ilustrada": "OGUC Ilustrada",
}


def source_name(path):
    """Nombre legible del documento a partir de su archivo."""
    path = Path(path)
    m = re.search(r"DDU[-_ ]?(\d+)", path.name, re.IGNORECASE)
    if m and path.parent.name == "ddu":
        return f"Circular DDU {m.group(1)}"

    stem_lower = path.stem.lower()

    # Los tomos de la OGUC Ilustrada se distinguen entre sí para poder
    # rastrear cada cita hasta su tomo y página.
    if stem_lower.startswith("oguc-ilustrada"):
        tomo = re.match(r"oguc-ilustrada-(i+)\b", stem_lower)
        return f"OGUC Ilustrada {tomo.group(1).upper()}" if tomo else "OGUC Ilustrada"

    # Prefijo más largo primero: "oguc-ilustrada" debe ganarle a "oguc".
    for prefix in sorted(_KNOWN_SOURCES, key=len, reverse=True):
        if stem_lower.startswith(prefix):
            return _KNOWN_SOURCES[prefix]
    return path.stem


def corpus_files(data_dir=DATA_DIR):
    """Todos los PDF del corpus, ordenados de forma estable."""
    return sorted(Path(data_dir).rglob("*.pdf"))


def extract_pages(path):
    """Devuelve [(número de página, texto), ...]."""
    reader = PdfReader(path)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


def split_document(path, max_chars=MAX_CHUNK_CHARS):
    """Extrae y fragmenta un PDF, etiquetando cada fragmento con su fuente.

    Si el documento fue procesado con lectura visual (escaneos), usa esa
    extracción en lugar de la capa de texto, que en esos PDF está vacía.
    """
    from core.vision import load_extracted

    source = source_name(path)
    visual = load_extracted(path)
    if visual is not None:
        # Una página descrita = un fragmento: la descripción ya es una
        # unidad temática coherente y cabe holgadamente en el límite.
        chunks = [
            {"text": texto[:max_chars], "page": num, "source": source}
            for num, texto in visual
            if len(texto) >= 50
        ]
        return chunks

    chunks = split_chunks(extract_pages(path), max_chars=max_chars)
    for c in chunks:
        c["source"] = source
    return chunks


def split_chunks(pages, max_chars=MAX_CHUNK_CHARS):
    """Une el texto y lo corta priorizando los límites de 'Artículo N°'.

    Devuelve [{"text": ..., "page": ...}, ...].
    """
    full = ""
    page_marks = []  # (posición en el texto, número de página)
    for num, text in pages:
        page_marks.append((len(full), num))
        full += text + "\n"

    def page_of(pos):
        current = page_marks[0][1]
        for offset, num in page_marks:
            if offset > pos:
                break
            current = num
        return current

    # Corta en cada "Artículo X" que aparezca al inicio de línea,
    # exactamente donde empieza la palabra (no en el salto de línea previo,
    # que pertenece a la página anterior)
    starts = [m.start(1) for m in re.finditer(r"\n\s*(Artículo\s+\d)", full)] or [0]
    if starts[0] != 0:
        starts.insert(0, 0)
    sections = [(s, full[s:e]) for s, e in zip(starts, starts[1:] + [len(full)])]

    chunks = []
    for pos, text in sections:
        text = text.strip()
        if len(text) < 50:
            continue
        # Si un artículo es muy largo, se subdivide con solapamiento
        if len(text) <= max_chars:
            chunks.append({"text": text, "page": page_of(pos)})
        else:
            header = text[:120].splitlines()[0]
            step = max_chars - 300
            for i in range(0, len(text), step):
                part = text[i : i + max_chars]
                if i > 0:
                    part = f"[{header}...]\n{part}"
                chunks.append({"text": part, "page": page_of(pos + i)})
    return chunks
