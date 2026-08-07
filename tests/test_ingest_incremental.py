"""Tests de idempotencia e integridad de la ingesta incremental.

No llaman a la API: los embeddings van mockeados.
"""

import numpy as np

import ingest_incremental as inc
from core.store import VectorStore

CHUNKS = [
    {"text": "fragmento uno", "page": 1, "source": "OGUC"},
    {"text": "fragmento dos", "page": 2, "source": "OGUC"},
    {"text": "fragmento tres", "page": 3, "source": "LGUC"},
]


def _fake_embeddings(textos):
    """Vector determinista por texto: permite verificar correspondencia."""
    return [[float(len(t)), 1.0, 0.0] for t in textos]


def test_clave_depende_solo_del_texto():
    a = {"text": "igual", "page": 1, "source": "OGUC"}
    b = {"text": "igual", "page": 99, "source": "OTRO"}
    assert inc.text_key(a) == inc.text_key(b)


def test_ingesta_dos_veces_no_duplica_ni_rellama(tmp_path, monkeypatch):
    monkeypatch.setattr(inc, "STORE_DIR", tmp_path)
    monkeypatch.setattr(inc, "CHECKPOINT", tmp_path / "incremental_checkpoint.json")
    monkeypatch.setattr(inc, "build_corpus", lambda: list(CHUNKS))
    monkeypatch.setattr(inc, "GEMINI_API_KEY", "clave-de-prueba")

    llamadas = []

    def contar(textos):
        llamadas.append(len(textos))
        return _fake_embeddings(textos)

    monkeypatch.setattr(inc, "embed_documents", contar)

    # Se capturan los originales antes de parchar para evitar recursión:
    # los reemplazos solo fijan el directorio temporal.
    orig_save, orig_load, orig_exists = (
        VectorStore.save,
        VectorStore.load,
        VectorStore.exists,
    )
    monkeypatch.setattr(
        VectorStore, "save",
        staticmethod(lambda v, c, store_dir=None: orig_save(v, c, tmp_path)),
    )
    monkeypatch.setattr(
        VectorStore, "load",
        staticmethod(lambda store_dir=None: orig_load(tmp_path)),
    )
    monkeypatch.setattr(
        VectorStore, "exists",
        staticmethod(lambda store_dir=None: orig_exists(tmp_path)),
    )

    inc.main()
    assert sum(llamadas) == len(CHUNKS), "primera corrida embebe todo"
    matriz = np.load(tmp_path / "embeddings.npy")
    assert matriz.shape[0] == len(CHUNKS)

    llamadas.clear()
    inc.main()
    assert llamadas == [], "segunda corrida no debe llamar a la API"
    matriz2 = np.load(tmp_path / "embeddings.npy")
    assert matriz2.shape[0] == len(CHUNKS), "no debe duplicar fragmentos"


def test_save_rechaza_desalineacion(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="desalineación"):
        VectorStore.save([[1.0, 0.0]], CHUNKS, store_dir=tmp_path)


def test_save_es_atomico_y_conserva_correspondencia(tmp_path):
    vectores = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    VectorStore.save(vectores, CHUNKS, store_dir=tmp_path)
    store = VectorStore.load(store_dir=tmp_path)
    assert len(store.chunks) == store.matrix.shape[0] == 3
    assert not list(tmp_path.glob("*.tmp*")), "no deben quedar temporales"
