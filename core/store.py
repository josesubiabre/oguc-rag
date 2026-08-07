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
        """Normaliza y persiste de forma atómica.

        Escribe primero a archivos temporales y recién al final los mueve
        sobre los definitivos: un fallo a mitad de camino deja el índice
        anterior intacto en vez de corromperlo.
        """
        store_dir = Path(store_dir)
        store_dir.mkdir(exist_ok=True)

        matrix = np.array(vectors, dtype=np.float32)
        if matrix.shape[0] != len(chunks):
            raise ValueError(
                f"desalineación: {matrix.shape[0]} vectores vs {len(chunks)} fragmentos"
            )
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)

        tmp_emb = store_dir / "embeddings.npy.tmp"
        tmp_chunks = store_dir / "chunks.json.tmp"
        np.save(tmp_emb, matrix)
        # np.save agrega .npy si el nombre no termina en .npy
        tmp_emb_real = tmp_emb.with_suffix(".tmp.npy")
        with open(tmp_chunks, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False)

        tmp_emb_real.replace(store_dir / "embeddings.npy")
        tmp_chunks.replace(store_dir / "chunks.json")

    def search(self, query_vector, k):
        """Devuelve los k fragmentos más similares: [{"text", "page"}, ...]."""
        scores = self.matrix @ query_vector
        top = np.argsort(scores)[::-1][:k]
        return [self.chunks[i] for i in top]
