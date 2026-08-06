"""Tests del chunking — no requieren PDF ni APIs."""

from core.chunking import split_chunks

PAGES = [
    (1, "PREÁMBULO\nEste es el texto introductorio de la ordenanza de prueba.\n"),
    (2, "Artículo 1.1.1. Las definiciones de esta ordenanza son obligatorias.\n"
        "Artículo 1.1.2. " + "Contenido largo del segundo artículo. " * 100),
    (3, "Artículo 1.1.3. Artículo corto en otra página.\nCon una segunda línea de contenido."),
]


def test_corta_por_articulos():
    chunks = split_chunks(PAGES)
    starts = [c["text"][:30] for c in chunks]
    assert any(s.startswith("Artículo 1.1.1") for s in starts)
    assert any(s.startswith("Artículo 1.1.3") for s in starts)


def test_articulo_largo_se_subdivide_con_encabezado():
    chunks = split_chunks(PAGES, max_chars=500)
    parts = [c for c in chunks if "1.1.2" in c["text"][:60]]
    assert len(parts) > 1
    # Las continuaciones llevan el encabezado del artículo entre corchetes
    assert parts[1]["text"].startswith("[Artículo 1.1.2")


def test_ningun_chunk_supera_el_maximo():
    chunks = split_chunks(PAGES, max_chars=500)
    # margen por el encabezado agregado a las continuaciones
    assert all(len(c["text"]) <= 650 for c in chunks)


def test_paginas_correctas():
    chunks = split_chunks(PAGES)
    ultimo = [c for c in chunks if c["text"].startswith("Artículo 1.1.3")][0]
    assert ultimo["page"] == 3


def test_descarta_fragmentos_triviales():
    chunks = split_chunks([(1, "hola\n")])
    assert chunks == []
