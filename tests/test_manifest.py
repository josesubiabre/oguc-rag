"""Tests del registro de fuentes y de la comprobación de vigencia.

Ninguno consulta la red ni servicios pagados.
"""

import json
from datetime import date

import pytest

import check_vigencia as cv
from core import manifest


def _documento(tmp_path, **kw):
    archivo = tmp_path / "doc.pdf"
    archivo.write_bytes(b"%PDF-1.7 contenido")
    base = {
        "id": "doc",
        "ruta": "doc.pdf",
        "categoria": "normativa_vigente",
        "cita": "OGUC",
        "sha256": manifest.sha256(archivo),
        "fin_vigencia": None,
        "url_oficial": "https://ejemplo.cl",
        "fecha_publicacion": "2020-01-01",
        "en_indice": True,
    }
    base.update(kw)
    return base


# --- Utilidades de fechas ---


def test_fecha_leychile_reconoce_el_formato_del_bcn():
    assert manifest.fecha_leychile("24-JUN-2026") == date(2026, 6, 24)
    assert manifest.fecha_leychile("13-ABR-1976") == date(1976, 4, 13)


def test_fecha_leychile_devuelve_none_ante_algo_distinto():
    assert manifest.fecha_leychile("2026-06-24") is None
    assert manifest.fecha_leychile("32-XXX-2026") is None


def test_dias_restantes():
    hoy = date(2026, 8, 10)
    assert manifest.dias_restantes("2026-08-11", hoy) == 1
    assert manifest.dias_restantes("2026-08-01", hoy) == -9
    assert manifest.dias_restantes(None, hoy) is None


def test_guardar_y_cargar_conservan_acentos(tmp_path):
    """Los acentos importan: la cita del manifiesto se compara con la del índice."""
    ruta = tmp_path / "manifest.json"
    datos = {"documentos": [{"cita": "Ley 21.807 (Planificación Territorial)"}]}
    manifest.guardar(datos, ruta)
    assert manifest.cargar(ruta) == datos
    assert not list(tmp_path.glob("*.tmp")), "no deben quedar temporales"


# --- Comprobaciones ---


def test_integridad_detecta_archivo_reemplazado(tmp_path, monkeypatch):
    monkeypatch.setattr(cv, "DATA_DIR", tmp_path)
    datos = {"documentos": [_documento(tmp_path)]}
    hallazgos = []
    cv.revisar_integridad(datos, hallazgos)
    assert hallazgos == []

    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.7 otro contenido")
    cv.revisar_integridad(datos, hallazgos)
    assert hallazgos and hallazgos[0][0] == "ERROR"


def test_integridad_detecta_archivo_ausente(tmp_path, monkeypatch):
    monkeypatch.setattr(cv, "DATA_DIR", tmp_path)
    datos = {"documentos": [_documento(tmp_path)]}
    (tmp_path / "doc.pdf").unlink()
    hallazgos = []
    cv.revisar_integridad(datos, hallazgos)
    assert hallazgos[0][0] == "ERROR"


@pytest.mark.parametrize(
    "fin,nivel",
    [("2026-08-01", "ERROR"), ("2026-08-11", "AVISO"), ("2027-01-01", None)],
)
def test_vigencia_segun_cuanto_falte(tmp_path, fin, nivel):
    """Caducada es error; por caducar es aviso; lejana no se reporta."""
    datos = {"documentos": [_documento(tmp_path, fin_vigencia=fin)]}
    hallazgos = []
    cv.revisar_vigencia(datos, date(2026, 8, 10), hallazgos)
    assert (hallazgos[0][0] if hallazgos else None) == nivel


def test_coherencia_detecta_cita_declarada_que_no_esta_indexada(tmp_path, monkeypatch):
    """El manifiesto no puede afirmar que algo está en el índice si no está."""
    monkeypatch.setattr(cv, "STORE_DIR", tmp_path)
    (tmp_path / "chunks.json").write_text(
        json.dumps([{"source": "OGUC", "text": "x", "page": 1}]), encoding="utf-8"
    )
    datos = {"documentos": [_documento(tmp_path, cita="LGUC")], "colecciones": []}
    hallazgos = []
    cv.revisar_coherencia(datos, hallazgos)
    assert hallazgos[0][0] == "ERROR"


def test_coherencia_acepta_las_colecciones_por_prefijo(tmp_path, monkeypatch):
    """Una colección cita con marcador variable: «Circular DDU <número>»."""
    monkeypatch.setattr(cv, "STORE_DIR", tmp_path)
    (tmp_path / "chunks.json").write_text(
        json.dumps([{"source": "Circular DDU 548", "text": "x", "page": 1}]),
        encoding="utf-8",
    )
    datos = {
        "documentos": [],
        "colecciones": [
            {"id": "ddu", "cita": "Circular DDU <número>", "en_indice": True}
        ],
    }
    hallazgos = []
    cv.revisar_coherencia(datos, hallazgos)
    assert hallazgos == []


def test_manifiesto_real_es_coherente_con_el_indice():
    """Guardia sobre los datos de verdad: manifiesto e índice no deben divergir."""
    datos = manifest.cargar()
    hallazgos = []
    cv.revisar_coherencia(datos, hallazgos)
    cv.revisar_integridad(datos, hallazgos)
    assert [h for h in hallazgos if h[0] == "ERROR"] == []
