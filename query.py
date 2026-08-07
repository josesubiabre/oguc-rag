"""Consulta la OGUC en lenguaje natural desde la terminal.

Requiere haber ejecutado antes ingest.py. Uso:
    python query.py
"""

from core.config import GEMINI_API_KEY, GROQ_API_KEY
from core.rag import answer
from core.store import VectorStore


def main():
    if not GEMINI_API_KEY or "pega_tu_key" in GEMINI_API_KEY:
        print("Falta GEMINI_API_KEY en .env (aistudio.google.com)")
        return
    if not GROQ_API_KEY or "pega_tu_key" in GROQ_API_KEY:
        print("Falta GROQ_API_KEY en .env (console.groq.com)")
        return
    if not VectorStore.exists():
        print("No existe la base vectorial: ejecuta primero  python ingest.py")
        return

    print("Pregúntale a la OGUC (escribe 'salir' para terminar)\n")
    while True:
        question = input("Pregunta: ").strip()
        if not question or question.lower() in ("salir", "exit", "quit"):
            break
        text, sources, _, _ = answer(question)
        print(f"\n{text}\n")
        cites = "; ".join(
            f"{s['source']} págs. {', '.join(map(str, s['pages']))}" for s in sources
        )
        print(f"(Fuentes: {cites})\n")


if __name__ == "__main__":
    main()
