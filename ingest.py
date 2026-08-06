"""Vectoriza todos los PDF de data/ (incluida data/ddu/) y guarda la base en store/.

Ejecutar cada vez que cambie el corpus:
    python ingest.py

Si se interrumpe (p. ej. por cuota), guarda un checkpoint y al volver a
ejecutarse reanuda desde donde quedó.
"""

import json

from core.chunking import corpus_files, split_document
from core.config import GEMINI_API_KEY, STORE_DIR
from core.embeddings import embed_documents
from core.store import VectorStore

BATCH_SIZE = 10
CHECKPOINT = STORE_DIR / "checkpoint.json"


def main():
    if not GEMINI_API_KEY or "pega_tu_key" in GEMINI_API_KEY:
        print("Falta GEMINI_API_KEY en .env (aistudio.google.com)")
        return

    files = corpus_files()
    print(f"Cargando {len(files)} documentos...")
    chunks = []
    for path in files:
        doc_chunks = split_document(path)
        chunks.extend(doc_chunks)
        print(f"  {path.name}: {len(doc_chunks)} fragmentos")
    print(f"  total: {len(chunks)} fragmentos")

    print("Generando embeddings vía API de Gemini...")
    STORE_DIR.mkdir(exist_ok=True)
    vectors = []
    if CHECKPOINT.exists():
        vectors = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        print(f"  reanudando desde el fragmento {len(vectors)}")

    try:
        for i in range(len(vectors), len(chunks), BATCH_SIZE):
            batch = [c["text"] for c in chunks[i : i + BATCH_SIZE]]
            vectors.extend(embed_documents(batch))
            print(f"  {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)}")
            if (i // BATCH_SIZE) % 20 == 0:  # checkpoint periódico
                CHECKPOINT.write_text(json.dumps(vectors), encoding="utf-8")
    except Exception as e:
        CHECKPOINT.write_text(json.dumps(vectors), encoding="utf-8")
        print(f"\nError: {e}")
        print(f"Progreso guardado ({len(vectors)}/{len(chunks)}): vuelve a correr ingest.py para continuar")
        return

    VectorStore.save(vectors, chunks)
    CHECKPOINT.unlink(missing_ok=True)
    print(f"Listo: {len(chunks)} fragmentos guardados en {STORE_DIR}/")


if __name__ == "__main__":
    main()
