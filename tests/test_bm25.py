"""Tests del recuperador léxico. Sin llamadas a servicios pagados."""

from core.bm25 import Bm25Index, tokenize

CHUNKS = [
    {
        "text": "Artículo 4.2.7. Las barandas de balcones deberán tener una "
                "altura mínima de 0,95 m medida desde el piso terminado.",
        "page": 287,
        "source": "OGUC",
    },
    {
        "text": "Circular DDU 514 imparte instrucciones sobre la aplicación "
                "de las normas de accesibilidad universal en edificaciones.",
        "page": 1,
        "source": "Circular DDU 514",
    },
    {
        "text": "El DS 50 de 2015 modifica la Ordenanza en materia de "
                "accesibilidad universal para personas con discapacidad.",
        "page": 10,
        "source": "DS 50 Accesibilidad Universal",
    },
    {
        "text": "La Ley 21.442 sobre copropiedad inmobiliaria regula los "
                "bienes comunes y la administración de condominios.",
        "page": 3,
        "source": "Ley de Copropiedad (21.442)",
    },
    {
        "text": "Artículo 5.1.4. Las obras menores requieren un permiso "
                "otorgado por el Director de Obras Municipales.",
        "page": 388,
        "source": "OGUC",
    },
]


def test_tokenize_conserva_referencias_normativas():
    tokens = tokenize("Artículo 4.2.7 y la Ley 21.442")
    assert "4.2.7" in tokens
    assert "21.442" in tokens
    # Las partes también se indexan para tolerar consultas parciales
    assert "4" in tokens and "2" in tokens and "7" in tokens


def test_tokenize_normaliza_tildes_y_mayusculas():
    assert tokenize("ARTÍCULO Ámbito") == tokenize("articulo ambito")


def test_tokenize_conserva_siglas_y_numeros():
    tokens = tokenize("La circular DDU 514 y el DS 50")
    assert "ddu" in tokens and "514" in tokens
    assert "ds" in tokens and "50" in tokens


def test_referencia_exacta_a_articulo():
    idx = Bm25Index.build(CHUNKS)
    top = idx.rank("artículo 4.2.7", 3)
    assert top, "debe encontrar algo"
    assert "4.2.7" in CHUNKS[top[0]]["text"]


def test_numero_de_circular_ddu():
    idx = Bm25Index.build(CHUNKS)
    top = idx.rank("circular DDU 514", 3)
    assert CHUNKS[top[0]]["source"] == "Circular DDU 514"


def test_referencia_a_ley_con_punto():
    idx = Bm25Index.build(CHUNKS)
    top = idx.rank("ley 21.442", 3)
    assert "21.442" in CHUNKS[top[0]]["text"]


def test_consulta_cotidiana_encuentra_permiso():
    idx = Bm25Index.build(CHUNKS)
    top = idx.rank("necesito un permiso de obras menores", 3)
    assert any("5.1.4" in CHUNKS[i]["text"] for i in top)


def test_sin_coincidencias_devuelve_vacio():
    idx = Bm25Index.build(CHUNKS)
    assert idx.rank("zzzz qwerty inexistente", 3) == []


def test_persistencia_del_indice(tmp_path):
    ruta = tmp_path / "bm25.pkl"
    Bm25Index.build(CHUNKS).save(ruta)
    assert ruta.exists()
    cargado = Bm25Index.load(ruta)
    assert cargado.size == len(CHUNKS)
    assert cargado.rank("artículo 4.2.7", 1)
