"""Tests de la capa de vigencia normativa. Ningún test llama a la API."""

import json

import pytest

from core import rag, vigencia
from core.chunking import split_chunks

TABLA = {
    "derogadas": [
        {
            "id": "ley-19537",
            "norma": "Ley 19.537",
            "nombre": "Sobre copropiedad inmobiliaria",
            "patron": "19[.,]?537",
            "estado": "derogada",
            "fecha_estado": "2022-04-13",
            "reemplazada_por": "Ley 21.442",
            "base_legal": "artículo 100 de la Ley 21.442",
            "regla_de_reenvio": "las referencias se entienden hechas a la nueva ley",
            "concordancias": [
                {
                    "articulo": "13",
                    "equivalente": "artículos 29 y 15 N° 3 de la Ley 21.442",
                    "materia": "alteraciones en bienes comunes",
                    "fundamento": "el artículo 29 remite al cuadro del artículo 15",
                }
            ],
        }
    ]
}


@pytest.fixture(autouse=True)
def tabla_de_prueba(tmp_path, monkeypatch):
    ruta = tmp_path / "vigencia.json"
    ruta.write_text(json.dumps(TABLA), encoding="utf-8")
    monkeypatch.setattr(vigencia, "VIGENCIA_PATH", ruta)
    vigencia._tabla.cache_clear()
    yield
    vigencia._tabla.cache_clear()


# --- Detección ---


def test_detecta_la_norma_derogada_con_y_sin_punto():
    assert [d["id"] for d in vigencia.citadas_en("según la ley 19.537")] == ["ley-19537"]
    assert [d["id"] for d in vigencia.citadas_en("la ley 19537 dispone")] == ["ley-19537"]


def test_no_marca_un_texto_sin_referencias():
    assert vigencia.citadas_en("el artículo 4.2.7 de la OGUC") == []
    assert vigencia.citadas_en("") == []


def test_sin_tabla_el_sistema_sigue_funcionando(tmp_path, monkeypatch):
    """Si falta el archivo se responde sin la capa, en vez de caer."""
    monkeypatch.setattr(vigencia, "VIGENCIA_PATH", tmp_path / "no-existe.json")
    vigencia._tabla.cache_clear()
    assert vigencia.citadas_en("ley 19.537") == []
    assert vigencia.derogadas() == []


# --- Criterio de corrección ---


def test_obliga_a_corregir_si_cita_la_derogada_sin_la_vigente():
    pendientes = vigencia.referencias_sin_mapear(
        "El artículo 17 de la Ley N° 19.537 exige acuerdo de la asamblea."
    )
    assert [d["id"] for d in pendientes] == ["ley-19537"]


def test_no_corrige_si_ya_menciona_la_norma_vigente():
    """Nombrar la ley derogada no es el error; presentarla como vigente sí.

    Citar la doctrina antigua y advertir el reemplazo es la salida correcta.
    """
    assert (
        vigencia.referencias_sin_mapear(
            "La Circular DDU 375 invoca el artículo 17 de la Ley 19.537, hoy "
            "reemplazada por la Ley 21.442."
        )
        == []
    )


def test_la_instruccion_lleva_las_concordancias_verificadas():
    texto = vigencia.instruccion_de_correccion(TABLA["derogadas"])
    assert "artículos 29 y 15 N° 3 de la Ley 21.442" in texto
    assert "artículo 100 de la Ley 21.442" in texto
    # El encargo debe preservar la doctrina, no descartar el documento
    assert "No descartes ese documento" in texto


# --- Indexación y contexto ---


def test_la_indexacion_marca_los_fragmentos_que_citan_normas_derogadas():
    from core import chunking

    paginas = [(1, "Artículo 1\nSegún la ley 19.537 los bienes comunes..." + "x" * 60)]
    chunks = split_chunks(paginas)
    for c in chunks:
        c["source"] = "Circular DDU 375"
        citas = [d["id"] for d in vigencia.citadas_en(c["text"])]
        if citas:
            c["derogadas"] = citas
    assert chunks[0]["derogadas"] == ["ley-19537"]
    assert chunking.es_norma({"source": "Circular DDU 375"}) is False


def test_el_contexto_anota_la_cita_derogada_sin_tocar_el_texto():
    """El aviso va en el encabezado: la doctrina se entrega intacta."""
    hits = [
        {
            "source": "Circular DDU 375",
            "page": 1,
            "text": "el artículo 17 de la ley 19.537",
            "derogadas": ["ley-19537"],
        }
    ]
    contexto = rag._contexto(hits)
    assert "[Circular DDU 375, página 1]" in contexto
    assert "derogada el 2022-04-13 por la Ley 21.442" in contexto
    # La concordancia verificada viaja en el aviso, no solo en la corrección
    assert "corresponde a artículos 29 y 15 N° 3 de la Ley 21.442" in contexto
    assert "el artículo 17 de la ley 19.537" in contexto  # texto intacto


def test_el_contexto_no_anota_fragmentos_limpios():
    hits = [{"source": "OGUC", "page": 287, "text": "las barandas..."}]
    assert "ATENCIÓN" not in rag._contexto(hits)
