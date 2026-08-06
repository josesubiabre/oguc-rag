"""Tests del nombrado de fuentes del corpus — no requieren APIs."""

from pathlib import Path

from core.chunking import source_name


def test_documentos_conocidos():
    assert source_name(Path("data/oguc.pdf")) == "OGUC"
    assert source_name(Path("data/LGUC-Ley-General-Septiembre-2025.pdf")) == "LGUC"
    assert (
        source_name(Path("data/Ley-de-copropiedad-Inmobiliaria-Ley-21442.pdf"))
        == "Ley de Copropiedad (21.442)"
    )
    assert (
        source_name(Path("data/Normativa-de-accesibilidad-unioversal-DS-N-50.pdf"))
        == "DS 50 Accesibilidad Universal"
    )


def test_circulares_ddu():
    assert source_name(Path("data/ddu/DDU-118.pdf")) == "Circular DDU 118"
    assert (
        source_name(Path("data/ddu/DDU-165-Modificada-por-DDU-446.pdf"))
        == "Circular DDU 165"
    )
    assert source_name(Path("data/ddu/Circular-DDU-513-para-publicar.pdf")) == "Circular DDU 513"


def test_desconocido_usa_nombre_de_archivo():
    assert source_name(Path("data/otro-documento.pdf")) == "otro-documento"
