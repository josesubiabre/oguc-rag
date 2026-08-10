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


def test_reglamento_no_se_confunde_con_la_ley():
    """El reglamento y la ley que reglamenta son documentos distintos."""
    assert (
        source_name(Path("data/Reglamento-de-la-ley-21442-Reglamento-de-copropiedad.pdf"))
        == "Reglamento de la Ley de Copropiedad"
    )


def test_formularios_solicitudes_y_resoluciones():
    """El código lleva actuación y tipo de obra, pese al ruido del archivo."""
    f = Path("data/formularios")
    assert (
        source_name(f / "FORMULARIO-2-3.1.f.pdf")
        == "Formulario MINVU 2-3.1 (Solicitud de Permiso de Edificación - Obra Nueva)"
    )
    # Sufijos de versión y guiones sueltos no deben entrar en el código
    assert (
        source_name(f / "FORMULARIO-2-1.2.-version-2026.pdf")
        == "Formulario MINVU 2-1.2 (Solicitud de Aprobación de Anteproyecto - Ampliación)"
    )
    assert (
        source_name(f / "FORMULARIO-2-7.4.-1.pdf")
        == "Formulario MINVU 2-7.4 (Solicitud de Recepción Definitiva - Reconstrucción)"
    )
    assert (
        source_name(f / "FORMULARIO-2-8.5..pdf")
        == "Formulario MINVU 2-8.5 (Certificado de Recepción Definitiva - Reparación)"
    )


def test_formularios_declaraciones_juradas():
    """Aquí el código va al inicio del nombre, no tras 'FORMULARIO'."""
    assert (
        source_name(
            Path("data/formularios/2.1.2.1.1-DJ-de-Inicio-de-Obra_Obra-Nueva_FORMULARIO.pdf")
        )
        == "Formulario MINVU 2.1.2.1.1 (Declaración Jurada de Inicio de Obra - Obra Nueva)"
    )


def test_formularios_comprobantes_no_usan_tipo_de_obra():
    """En los comprobantes el último dígito es el momento del trámite."""
    f = Path("data/formularios")
    assert (
        source_name(f / "2.2.2.1.0-Comprobante-Ingreso-DJ-Inicio-Edificacion.pdf")
        == "Formulario MINVU 2.2.2.1.0 (Comprobante de Ingreso, Declaración de Inicio)"
    )
    assert (
        source_name(f / "2.2.2.1.1-Comprobante-Archivo-DJ-Inicio-Edificacion.pdf")
        == "Formulario MINVU 2.2.2.1.1 (Comprobante de Archivo, Declaración de Inicio)"
    )


def test_mapa_de_formularios():
    assert (
        source_name(Path("data/formularios/MAPA-FORMULARIOS-OBRAS-DE-EDIFICACION.pdf"))
        == "Mapa de Formularios MINVU"
    )


def test_regla_de_formularios_solo_aplica_en_su_carpeta():
    """Fuera de data/formularios el mismo nombre no debe citarse como formulario."""
    assert source_name(Path("data/FORMULARIO-2-3.1.pdf")) == "FORMULARIO-2-3.1"


def test_desconocido_usa_nombre_de_archivo():
    assert source_name(Path("data/otro-documento.pdf")) == "otro-documento"
