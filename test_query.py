"""Prueba de una consulta de punta a punta (sin interfaz interactiva)."""

import os

from dotenv import load_dotenv
from groq import Groq

from query import answer, load_store

load_dotenv()

matrix, chunks = load_store()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

preguntas = [
    "¿Qué es un permiso de edificación y cuándo se necesita?",
    "¿Puedo construir una ampliación en mi casa sin permiso?",
    "¿Cuántos estacionamientos debe tener un edificio de viviendas?",
]

for pregunta in preguntas:
    texto, paginas = answer(pregunta, matrix, chunks, os.getenv("GEMINI_API_KEY"), client)
    print(f"P: {pregunta}\n\n{texto}\n\n(Fuentes: páginas {paginas})\n{'=' * 70}\n")
