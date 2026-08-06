"""Extracción del PDF y división en fragmentos por límites de 'Artículo N°'."""

import re

from pypdf import PdfReader

from core.config import MAX_CHUNK_CHARS


def extract_pages(path):
    """Devuelve [(número de página, texto), ...]."""
    reader = PdfReader(path)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


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
