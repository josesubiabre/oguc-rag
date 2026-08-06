"""Vectoriza la OGUC y guarda la base en store/.

Ejecutar una sola vez (o cada vez que cambie el PDF):
    python ingest.py

Si se interrumpe (p. ej. por cuota), guarda un checkpoint y al volver a
ejecutarse reanuda desde donde quedó.
"""

import json

from core.chunking import extract_pages, split_chunks
from core.config import GEMINI_API_KEY, PDF_PATH, STORE_DIR
from core.embeddings import embed_documents
from core.store import VectorStore

BATCH_SIZE = 10
CHECKPOINT = STORE_DIR / "checkpoint.json"


def main():
    if not GEMINI_API_KEY or "pega_tu_key" in GEMINI_API_KEY:
        print("Falta GEMINI_API_KEY en .env (aistudio.google.com)")
        return

    print("Cargando PDF...")
    pages = extract_pages(PDF_PATH)
    print(f"  {len(pages)} páginas")

    chunks = split_chunks(pages)
    print(f"  {len(chunks)} fragmentos")

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
