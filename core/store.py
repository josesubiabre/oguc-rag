"""Base vectorial: matriz numpy normalizada + fragmentos en JSON.

Único módulo que conoce el formato de almacenamiento: para pasar a una
búsqueda híbrida (BM25 + embeddings) o a otra base, se cambia solo aquí.
"""

import json
from pathlib import Path

import numpy as np

from core.config import STORE_DIR


class VectorStore:
    def __init__(self, matrix, chunks):
        self.matrix = matrix
        self.chunks = chunks

    @classmethod
    def load(cls, store_dir=STORE_DIR):
        store_dir = Path(store_dir)
        matrix = np.load(store_dir / "embeddings.npy")
        with open(store_dir / "chunks.json", encoding="utf-8") as f:
            chunks = json.load(f)
        return cls(matrix, chunks)

    @classmethod
    def exists(cls, store_dir=STORE_DIR):
        return (Path(store_dir) / "embeddings.npy").exists()

    @staticmethod
    def save(vectors, chunks, store_dir=STORE_DIR):
        """Normaliza y persiste. `vectors` es una lista de listas de floats."""
        store_dir = Path(store_dir)
        store_dir.mkdir(exist_ok=True)
        matrix = np.array(vectors, dtype=np.float32)
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
        np.save(store_dir / "embeddings.npy", matrix)
        with open(store_dir / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False)

    def search(self, query_vector, k):
        """Devuelve los k fragmentos más similares: [{"text", "page"}, ...]."""
        scores = self.matrix @ query_vector
        top = np.argsort(scores)[::-1][:k]
        return [self.chunks[i] for i in top]
