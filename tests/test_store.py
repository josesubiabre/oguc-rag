"""Tests de la base vectorial — no requieren APIs."""

import numpy as np

from core.store import VectorStore

CHUNKS = [
    {"text": "fragmento a", "page": 1},
    {"text": "fragmento b", "page": 2},
    {"text": "fragmento c", "page": 3},
]
VECTORS = [[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]]


def test_roundtrip_guardar_cargar(tmp_path):
    VectorStore.save(VECTORS, CHUNKS, store_dir=tmp_path)
    store = VectorStore.load(store_dir=tmp_path)
    assert store.matrix.shape == (3, 2)
    assert store.chunks == CHUNKS
    # Las filas quedan normalizadas
    norms = np.linalg.norm(store.matrix, axis=1)
    assert np.allclose(norms, 1.0)


def test_search_devuelve_los_mas_similares(tmp_path):
    VectorStore.save(VECTORS, CHUNKS, store_dir=tmp_path)
    store = VectorStore.load(store_dir=tmp_path)
    q = np.array([1.0, 0.0], dtype=np.float32)
    hits = store.search(q, k=2)
    assert hits[0]["text"] == "fragmento a"      # coseno 1.0
    assert hits[1]["text"] == "fragmento c"      # coseno ~0.71


def test_exists(tmp_path):
    assert not VectorStore.exists(store_dir=tmp_path)
    VectorStore.save(VECTORS, CHUNKS, store_dir=tmp_path)
    assert VectorStore.exists(store_dir=tmp_path)
