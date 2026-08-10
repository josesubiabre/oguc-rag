"""Ingesta incremental: vectoriza solo los fragmentos que aún no existen.

Compara el corpus recalculado contra el índice actual usando el hash del
texto de cada fragmento, así reutiliza todos los embeddings ya pagados y
llama a la API únicamente por lo nuevo. Es idempotente: ejecutarlo dos
veces seguidas no genera llamadas ni duplica fragmentos.

Uso:
    python ingest_incremental.py --dry-run   # informe sin costo
    python ingest_incremental.py             # vectoriza lo pendiente
"""

import hashlib
import json
import sys

import numpy as np

from core.chunking import corpus_files, split_document
from core.config import GEMINI_API_KEY, STORE_DIR
from core.embeddings import embed_documents
from core.store import VectorStore

BATCH_SIZE = 10
CHECKPOINT = STORE_DIR / "incremental_checkpoint.json"


def text_key(chunk):
    return hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()


def build_corpus():
    """Recalcula el corpus completo desde data/ (sin costo)."""
    chunks = []
    for ruta in corpus_files():
        chunks.extend(split_document(ruta))
    return chunks


def load_existing():
    """Devuelve ({hash del texto: vector}, fragmentos guardados)."""
    if not VectorStore.exists():
        return {}, []
    store = VectorStore.load()
    if len(store.chunks) != store.matrix.shape[0]:
        raise SystemExit(
            f"Índice inconsistente: {len(store.chunks)} fragmentos vs "
            f"{store.matrix.shape[0]} vectores. Revisar antes de continuar."
        )
    mapa = {}
    for chunk, vector in zip(store.chunks, store.matrix):
        mapa.setdefault(text_key(chunk), vector)
    return mapa, store.chunks


def main():
    dry_run = "--dry-run" in sys.argv

    print("Recalculando corpus desde data/ ...")
    corpus = build_corpus()
    conocidos, previos_chunks = load_existing()
    previos = len(previos_chunks)

    pendientes = [c for c in corpus if text_key(c) not in conocidos]
    chars = sum(len(c["text"]) for c in pendientes)

    print(f"  fragmentos en el corpus     : {len(corpus)}")
    print(f"  ya vectorizados (reutilizar): {len(corpus) - len(pendientes)}")
    print(f"  pendientes (requieren API)  : {len(pendientes)}")
    print(f"  caracteres pendientes       : {chars:,}")
    print(f"  llamadas previstas          : ~{-(-len(pendientes) // BATCH_SIZE)} lotes de {BATCH_SIZE}")

    if dry_run:
        print("\n--dry-run: no se realizó ninguna llamada pagada.")
        return

    # Los metadatos también cuentan: cambiar una regla de citación no genera
    # embeddings pendientes, pero sí debe llegar al índice. Sin comparar los
    # fragmentos guardados contra el corpus, el script cortaba aquí y una
    # circular seguía citándose "CIR-182" en vez de "Circular DDU 182".
    if not pendientes and previos_chunks == corpus:
        print("\nNada pendiente: el índice ya está al día.")
        return
    if not pendientes:
        print("  sin embeddings nuevos; se reescribe el índice por metadatos")

    if pendientes and (not GEMINI_API_KEY or "pega_tu_key" in GEMINI_API_KEY):
        print("Falta GEMINI_API_KEY en .env")
        return

    # Checkpoint: {hash: vector} de lo ya embebido en esta corrida
    nuevos = {}
    if CHECKPOINT.exists():
        nuevos = {k: np.array(v, dtype=np.float32) for k, v in
                  json.loads(CHECKPOINT.read_text(encoding="utf-8")).items()}
        print(f"  reanudando: {len(nuevos)} ya embebidos en una corrida previa")

    faltan = [c for c in pendientes if text_key(c) not in nuevos]
    llamadas = 0
    try:
        for i in range(0, len(faltan), BATCH_SIZE):
            lote = faltan[i : i + BATCH_SIZE]
            vectores = embed_documents([c["text"] for c in lote])
            llamadas += 1
            for chunk, vec in zip(lote, vectores):
                nuevos[text_key(chunk)] = np.array(vec, dtype=np.float32)
            print(f"  {min(i + BATCH_SIZE, len(faltan))}/{len(faltan)}")
            CHECKPOINT.write_text(
                json.dumps({k: v.tolist() for k, v in nuevos.items()}),
                encoding="utf-8",
            )
    except Exception as e:
        CHECKPOINT.write_text(
            json.dumps({k: v.tolist() for k, v in nuevos.items()}), encoding="utf-8"
        )
        print(f"\nError: {e}")
        print(f"Progreso guardado ({len(nuevos)}/{len(pendientes)}). "
              "Vuelve a ejecutar para continuar sin repetir llamadas.")
        return

    # Ensamble final: un vector por fragmento, en el orden del corpus
    disponibles = {**conocidos, **nuevos}
    vectores, chunks_final = [], []
    for c in corpus:
        k = text_key(c)
        if k in disponibles:
            vectores.append(disponibles[k])
            chunks_final.append(c)

    if len(vectores) != len(corpus):
        raise SystemExit(
            f"Faltan vectores para {len(corpus) - len(vectores)} fragmentos; no se escribe."
        )

    VectorStore.save(vectores, chunks_final)
    CHECKPOINT.unlink(missing_ok=True)

    # El índice léxico se reconstruye para no quedar desalineado del corpus
    from core.bm25 import Bm25Index

    Bm25Index.build(chunks_final).save()

    # Sin caracteres fuera de cp1252: la consola de Windows no los codifica y
    # una flecha en un mensaje de estado bastaba para abortar el script entero
    # después de haber pagado y guardado todo el trabajo.
    print(f"\nIndice actualizado: {previos} -> {len(chunks_final)} fragmentos")
    print(f"Llamadas pagadas realizadas en esta corrida: {llamadas}")


if __name__ == "__main__":
    main()
