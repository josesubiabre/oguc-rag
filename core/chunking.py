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
    "reglamento-de-la-ley-21442": "Reglamento de la Ley de Copropiedad",
    "normativa-de-accesibilidad": "DS 50 Accesibilidad Universal",
    "oguc-ilustrada": "OGUC Ilustrada",
}

# Formulario Único Nacional del MINVU: el prefijo del código identifica la
# actuación ante la DOM y el último dígito el tipo de obra. Se citan con su
# nombre y no solo con el número, que por sí solo no le dice nada al usuario.
_FORM_ACTUACION = {
    "2-1": "Solicitud de Aprobación de Anteproyecto",
    "2-2": "Resolución de Aprobación de Anteproyecto",
    "2-3": "Solicitud de Permiso de Edificación",
    "2-4": "Permiso de Edificación",
    "2-5": "Solicitud de Modificación de Proyecto",
    "2-6": "Resolución de Modificación de Proyecto",
    "2-7": "Solicitud de Recepción Definitiva",
    "2-8": "Certificado de Recepción Definitiva",
    "2.1.2.1": "Declaración Jurada de Inicio de Obra",
    "2.1.2.2": "Declaración Jurada de Modificación de Proyecto",
    "2.1.2.3": "Declaración Jurada de Término de Ejecución",
}
_FORM_OBRA = {
    "1": "Obra Nueva",
    "2": "Ampliación",
    "3": "Alteración",
    "4": "Reconstrucción",
    "5": "Reparación",
}
# En los comprobantes de la DOM el último dígito no es tipo de obra sino
# el momento del trámite (0 ingreso, 1 archivo), así que van mapeados enteros.
_FORM_COMPROBANTE = {
    "2.2.2.1.0": "Comprobante de Ingreso, Declaración de Inicio",
    "2.2.2.1.1": "Comprobante de Archivo, Declaración de Inicio",
    "2.2.2.2.0": "Comprobante de Ingreso, Declaración de Modificación",
    "2.2.2.2.1": "Comprobante de Archivo, Declaración de Modificación",
    "2.2.2.3.0": "Comprobante de Ingreso, Declaración de Término",
    "2.2.2.3.1": "Comprobante de Archivo, Declaración de Término",
}


def _formulario_name(stem):
    """Cita legible de un Formulario Único Nacional a partir de su archivo."""
    if stem.upper().startswith("MAPA"):
        return "Mapa de Formularios MINVU"

    m = re.match(r"(?:FORMULARIO[-_])?(\d+(?:[-.]\d+)+)", stem, re.IGNORECASE)
    if not m:
        return "Formulario MINVU"

    codigo = m.group(1)
    if codigo in _FORM_COMPROBANTE:
        return f"Formulario MINVU {codigo} ({_FORM_COMPROBANTE[codigo]})"

    familia, _, obra = codigo.rpartition(".")
    actuacion = _FORM_ACTUACION.get(familia)
    if not actuacion:
        return f"Formulario MINVU {codigo}"
    tipo = _FORM_OBRA.get(obra)
    detalle = f"{actuacion} - {tipo}" if tipo else actuacion
    return f"Formulario MINVU {codigo} ({detalle})"


def source_name(path):
    """Nombre legible del documento a partir de su archivo."""
    path = Path(path)
    m = re.search(r"DDU[-_ ]?(\d+)", path.name, re.IGNORECASE)
    if m and path.parent.name == "ddu":
        return f"Circular DDU {m.group(1)}"

    if path.parent.name == "formularios":
        return _formulario_name(path.stem)

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


def es_procedimiento(chunk):
    """True si el fragmento es un formulario y no una norma.

    Los formularios describen qué antecedentes exige la DOM en cada trámite.
    Se distinguen para citarlos y recuperarlos con reglas propias, sin
    mezclarlos con textos que sí tienen rango legal.
    """
    fuente = chunk.get("source", "")
    return fuente.startswith(("Formulario MINVU", "Mapa de Formularios"))


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
