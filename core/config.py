"""Configuración única del proyecto. Todo valor ajustable vive aquí."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

# Rutas
DATA_DIR = ROOT / "data"
STORE_DIR = ROOT / "store"

# Embeddings (Gemini)
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768

# LLM: Groq como primera opción, Gemini como respaldo ante saturación
LLM_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "gemini-3.5-flash"

# Recuperación y chunking
TOP_K = 5
MAX_CHUNK_CHARS = 2000

# Credenciales
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
