"""Construye una base vectorial parcial desde el checkpoint de ingest.py,
para poder probar query.py mientras se renueva la cuota diaria de Gemini.
Al completar la ingesta real, ingest.py sobreescribe estos archivos."""

import json
import os

import numpy as np

from ingest import PDF_PATH, STORE_DIR, extract_pages, split_chunks

with open(os.path.join(STORE_DIR, "checkpoint.json"), encoding="utf-8") as f:
    vectors = json.load(f)

chunks = split_chunks(extract_pages(PDF_PATH))[: len(vectors)]

matrix = np.array(vectors, dtype=np.float32)
matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)

np.save(os.path.join(STORE_DIR, "embeddings.npy"), matrix)
with open(os.path.join(STORE_DIR, "chunks.json"), "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False)

print(f"Base parcial lista: {len(chunks)} fragmentos (el checkpoint sigue intacto)")
