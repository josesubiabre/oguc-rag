"""Carga la OGUC, la divide en fragmentos y los guarda vectorizados en Chroma.

Ejecutar una sola vez (o cada vez que cambie el PDF):
    python ingest.py
"""

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF_PATH = "data/oguc.pdf"
DB_DIR = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    print("Cargando PDF...")
    docs = PyPDFLoader(PDF_PATH).load()
    print(f"  {len(docs)} páginas cargadas")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\nArtículo", "\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(docs)
    print(f"  {len(chunks)} fragmentos generados")

    print("Generando embeddings (la primera vez descarga el modelo, ~500MB)...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    Chroma.from_documents(chunks, embeddings, persist_directory=DB_DIR)
    print(f"Listo: base vectorial guardada en {DB_DIR}/")


if __name__ == "__main__":
    main()
