"""Prueba de una consulta de punta a punta (sin interfaz interactiva)."""

import os

from dotenv import load_dotenv
from groq import Groq

from query import answer, load_store

load_dotenv()

matrix, chunks = load_store()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

pregunta = "¿Cuál es la altura mínima de una baranda en un balcón?"
texto, paginas = answer(pregunta, matrix, chunks, os.getenv("GEMINI_API_KEY"), client)
print(f"P: {pregunta}\n\n{texto}\n\n(Fuentes: páginas {paginas})")
