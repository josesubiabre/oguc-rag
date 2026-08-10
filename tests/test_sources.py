"""Tests del nombrado de fuentes y del alcance del corpus — sin APIs."""

from pathlib import Path

from core.chunking import corpus_files, source_name

SRC = Path("data/01_sources")
DDU = SRC / "interpretacion_oficial" / "ddu_generales"
FORM = SRC / "tramites" / "formularios_minvu"


def test_documentos_conocidos():
    assert source_name(SRC / "normativa_base/oguc/ds-47-oguc-version-2026-03.pdf") == "OGUC"
    assert (
        source_name(SRC / "normativa_base/lguc/dfl-458-lguc-version-2026-06-24.pdf")
        == "LGUC"
    )
    assert (
        source_name(
            SRC / "leyes_especiales/copropiedad/ley-21442-copropiedad-version-2026-02-16.pdf"
        )
        == "Ley de Copropiedad (21.442)"
    )
    assert (
        source_name(
            SRC
            / "leyes_especiales/planificacion_territorial"
            / "ley-21807-planificacion-territorial-2026-02-16.pdf"
        )
        == "Ley 21.807 (Planificación Territorial)"
    )
    assert (
        source_name(
            SRC / "decretos_y_reglamentos/accesibilidad/ds-50-accesibilidad-universal-2015.pdf"
        )
        == "DS 50 Accesibilidad Universal"
    )


def test_reglamento_no_se_confunde_con_la_ley():
    """El reglamento y la ley que reglamenta son documentos distintos."""
    assert (
        source_name(
            SRC / "decretos_y_reglamentos/copropiedad/reglamento-ley-21442-2025-01-09.pdf"
        )
        == "Reglamento de la Ley de Copropiedad"
    )


def test_tomos_de_la_oguc_ilustrada_se_distinguen():
    ilus = SRC / "material_explicativo" / "oguc_ilustrada"
    assert source_name(ilus / "OGUC-Ilustrada-I-del-Urbanismo.pdf") == "OGUC Ilustrada I"
    assert source_name(ilus / "OGUC-Ilustrada-II-del-Urbanismo.pdf") == "OGUC Ilustrada II"


def test_circulares_ddu():
    assert source_name(DDU / "DDU-118.pdf") == "Circular DDU 118"
    assert source_name(DDU / "DDU-165-Modificada-por-DDU-446.pdf") == "Circular DDU 165"
    assert source_name(DDU / "Circular-DDU-513-para-publicar.pdf") == "Circular DDU 513"
    # El MINVU publica algunas con prefijo CIR en vez de DDU: es la misma serie
    assert source_name(DDU / "CIR-182.pdf") == "Circular DDU 182"
    assert source_name(DDU / "Cir-231.pdf") == "Circular DDU 231"


def test_formularios_solicitudes_y_resoluciones():
    """El código lleva actuación y tipo de obra, pese al ruido del archivo."""
    assert (
        source_name(FORM / "FORMULARIO-2-3.1.f.pdf")
        == "Formulario MINVU 2-3.1 (Solicitud de Permiso de Edificación - Obra Nueva)"
    )
    # Sufijos de versión y guiones sueltos no deben entrar en el código
    assert (
        source_name(FORM / "FORMULARIO-2-1.2.-version-2026.pdf")
        == "Formulario MINVU 2-1.2 (Solicitud de Aprobación de Anteproyecto - Ampliación)"
    )
    assert (
        source_name(FORM / "FORMULARIO-2-7.4.-1.pdf")
        == "Formulario MINVU 2-7.4 (Solicitud de Recepción Definitiva - Reconstrucción)"
    )
    assert (
        source_name(FORM / "FORMULARIO-2-8.5..pdf")
        == "Formulario MINVU 2-8.5 (Certificado de Recepción Definitiva - Reparación)"
    )


def test_formularios_declaraciones_juradas():
    """Aquí el código va al inicio del nombre, no tras 'FORMULARIO'."""
    assert (
        source_name(FORM / "2.1.2.1.1-DJ-de-Inicio-de-Obra_Obra-Nueva_FORMULARIO.pdf")
        == "Formulario MINVU 2.1.2.1.1 (Declaración Jurada de Inicio de Obra - Obra Nueva)"
    )


def test_formularios_comprobantes_no_usan_tipo_de_obra():
    """En los comprobantes el último dígito es el momento del trámite."""
    assert (
        source_name(FORM / "2.2.2.1.0-Comprobante-Ingreso-DJ-Inicio-Edificacion.pdf")
        == "Formulario MINVU 2.2.2.1.0 (Comprobante de Ingreso, Declaración de Inicio)"
    )
    assert (
        source_name(FORM / "2.2.2.1.1-Comprobante-Archivo-DJ-Inicio-Edificacion.pdf")
        == "Formulario MINVU 2.2.2.1.1 (Comprobante de Archivo, Declaración de Inicio)"
    )


def test_mapa_de_formularios():
    assert (
        source_name(FORM / "MAPA-FORMULARIOS-OBRAS-DE-EDIFICACION.pdf")
        == "Mapa de Formularios MINVU"
    )


def test_regla_de_formularios_solo_aplica_en_su_carpeta():
    """Fuera de formularios_minvu el mismo nombre no debe citarse como formulario."""
    assert source_name(SRC / "FORMULARIO-2-3.1.pdf") == "FORMULARIO-2-3.1"


def test_desconocido_usa_nombre_de_archivo():
    assert source_name(Path("data/otro-documento.pdf")) == "otro-documento"


# --- Alcance del corpus ---


def test_corpus_solo_toma_lo_que_esta_en_sources(tmp_path):
    """Separar carpetas en disco no basta: la exclusión vive en el código.

    Sin esto, una versión superada en 90_archive/ —o un PDF dejado suelto en
    la raíz— volvería al índice y el buscador entregaría dos redacciones del
    mismo artículo sin forma de saber cuál rige.
    """
    for ruta in [
        "01_sources/normativa_base/lguc/vigente.pdf",
        "00_inbox/recien-bajado.pdf",
        "90_archive/version-superada.pdf",
        "02_processed/text/derivado.pdf",
        "suelto-en-la-raiz.pdf",
    ]:
        destino = tmp_path / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"%PDF-1.7")

    encontrados = [p.name for p in corpus_files(tmp_path)]
    assert encontrados == ["vigente.pdf"]
