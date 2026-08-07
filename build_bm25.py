"""Construye y persiste el índice léxico BM25 desde el corpus vectorizado.

No consume APIs: es cálculo local sobre store/chunks.json. Se ejecuta
después de cada ingesta para que el índice quede alineado con el corpus.

Uso:
    python build_bm25.py
"""

import time

from core.bm25 import INDEX_PATH, Bm25Index
from core.store import VectorStore


def main():
    if not VectorStore.exists():
        print("No hay índice vectorial: ejecuta antes la ingesta.")
        return

    store = VectorStore.load()
    t0 = time.time()
    index = Bm25Index.build(store.chunks)
    build_s = time.time() - t0

    index.save()
    size_mb = INDEX_PATH.stat().st_size / 1024 / 1024
    print(f"Índice BM25: {index.size} fragmentos")
    print(f"  construcción: {build_s:.1f}s")
    print(f"  archivo: {INDEX_PATH.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
