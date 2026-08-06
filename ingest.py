"""Carga la OGUC, la divide en fragmentos, genera embeddings con la API de
Gemini y guarda todo en store/ (matriz numpy + textos en JSON).

Ejecutar una sola vez (o cada vez que cambie el PDF):
    python ingest.py
"""

import json
import os
import re
import time

import numpy as np
import requests
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

PDF_PATH = "data/oguc.pdf"
STORE_DIR = "store"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768
BATCH_SIZE = 10
MAX_CHUNK_CHARS = 2000


def extract_pages(path):
    reader = PdfReader(path)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


def split_chunks(pages):
    """Une el texto y lo corta priorizando los límites de 'Artículo N°'."""
    full = ""
    page_marks = []  # (posición en el texto, número de página)
    for num, text in pages:
        page_marks.append((len(full), num))
        full += text + "\n"

    def page_of(pos):
        current = page_marks[0][1]
        for offset, num in page_marks:
            if offset > pos:
                break
            current = num
        return current

    # Corta en cada "Artículo X" que aparezca al inicio de línea
    starts = [m.start() for m in re.finditer(r"\n\s*Artículo\s+\d", full)] or [0]
    if starts[0] != 0:
        starts.insert(0, 0)
    sections = [(s, full[s:e]) for s, e in zip(starts, starts[1:] + [len(full)])]

    chunks = []
    for pos, text in sections:
        text = text.strip()
        if len(text) < 50:
            continue
        # Si un artículo es muy largo, se subdivide por párrafos con solapamiento
        if len(text) <= MAX_CHUNK_CHARS:
            chunks.append({"text": text, "page": page_of(pos)})
        else:
            header = text[:120].splitlines()[0]
            step = MAX_CHUNK_CHARS - 300
            for i in range(0, len(text), step):
                part = text[i : i + MAX_CHUNK_CHARS]
                if i > 0:
                    part = f"[{header}...]\n{part}"
                chunks.append({"text": part, "page": page_of(pos + i)})
    return chunks


def embed_one(text, api_key):
    """Embebe un solo texto, con reintentos pacientes ante límites de tasa."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{EMBED_MODEL}:embedContent?key={api_key}"
    )
    body = {
        "model": f"models/{EMBED_MODEL}",
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_DOCUMENT",
        "outputDimensionality": EMBED_DIM,
    }
    for attempt in range(8):
        r = requests.post(url, json=body, timeout=60)
        if r.status_code == 429:
            wait = min(15 * (attempt + 1), 60)
            print(f"  límite de tasa, esperando {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()["embedding"]["values"]
    raise RuntimeError(f"Demasiados reintentos contra la API de Gemini: {r.text[:1500]}")


def embed_batch(texts, api_key):
    """Intenta el endpoint batch; si el tier gratuito lo rechaza (429),
    cae a peticiones de a una con pausa entre ellas."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{EMBED_MODEL}:batchEmbedContents?key={api_key}"
    )
    body = {
        "requests": [
            {
                "model": f"models/{EMBED_MODEL}",
                "content": {"parts": [{"text": t}]},
                "taskType": "RETRIEVAL_DOCUMENT",
                "outputDimensionality": EMBED_DIM,
            }
            for t in texts
        ]
    }
    r = requests.post(url, json=body, timeout=120)
    if r.status_code == 200:
        return [e["values"] for e in r.json()["embeddings"]]

    vectors = []
    for t in texts:
        vectors.append(embed_one(t, api_key))
        time.sleep(0.5)  # ~2 por segundo para respetar el límite por minuto
    return vectors


def main():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or "pega_tu_key" in api_key:
        print("Falta tu API key: edita .env y pega tu GEMINI_API_KEY (aistudio.google.com)")
        return

    print("Cargando PDF...")
    pages = extract_pages(PDF_PATH)
    print(f"  {len(pages)} páginas")

    chunks = split_chunks(pages)
    print(f"  {len(chunks)} fragmentos")

    print("Generando embeddings vía API de Gemini...")
    os.makedirs(STORE_DIR, exist_ok=True)
    checkpoint = os.path.join(STORE_DIR, "checkpoint.json")
    vectors = []
    if os.path.exists(checkpoint):
        with open(checkpoint, encoding="utf-8") as f:
            vectors = json.load(f)
        print(f"  reanudando desde el fragmento {len(vectors)}")

    try:
        for i in range(len(vectors), len(chunks), BATCH_SIZE):
            batch = [c["text"] for c in chunks[i : i + BATCH_SIZE]]
            vectors.extend(embed_batch(batch, api_key))
            print(f"  {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)}")
    except Exception as e:
        with open(checkpoint, "w", encoding="utf-8") as f:
            json.dump(vectors, f)
        print(f"\nError: {e}")
        print(f"Progreso guardado ({len(vectors)}/{len(chunks)}): vuelve a correr ingest.py para continuar")
        return

    matrix = np.array(vectors, dtype=np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)  # normaliza para coseno

    np.save(os.path.join(STORE_DIR, "embeddings.npy"), matrix)
    if os.path.exists(checkpoint):
        os.remove(checkpoint)
    with open(os.path.join(STORE_DIR, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    print(f"Listo: {len(chunks)} fragmentos guardados en {STORE_DIR}/")


if __name__ == "__main__":
    main()
