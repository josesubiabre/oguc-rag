"""Consulta la OGUC en lenguaje natural desde la terminal.

Uso:
    python query.py
"""

import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

DB_DIR = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

PROMPT = ChatPromptTemplate.from_template(
    """Eres un asistente experto en la Ordenanza General de Urbanismo y \
Construcciones (OGUC) de Chile. Responde la pregunta usando ÚNICAMENTE el \
contexto entregado. Cita siempre el número de artículo cuando sea posible. \
Si el contexto no contiene la respuesta, dilo claramente y no inventes.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""
)


def main():
    if not os.getenv("GROQ_API_KEY") or "pega_tu_key" in os.getenv("GROQ_API_KEY", ""):
        print("Falta tu API key: edita el archivo .env y pega tu key de console.groq.com")
        return

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 5})
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    print("Pregúntale a la OGUC (escribe 'salir' para terminar)\n")
    while True:
        question = input("Pregunta: ").strip()
        if not question or question.lower() in ("salir", "exit", "quit"):
            break

        docs = retriever.invoke(question)
        context = "\n\n---\n\n".join(d.page_content for d in docs)
        answer = llm.invoke(PROMPT.format(context=context, question=question))

        print(f"\n{answer.content}\n")
        pages = sorted({d.metadata.get("page", "?") + 1 for d in docs if isinstance(d.metadata.get("page"), int)})
        print(f"(Fuentes: páginas {', '.join(map(str, pages))} del PDF)\n")


if __name__ == "__main__":
    main()
