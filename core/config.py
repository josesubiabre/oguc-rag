"""Configuración única del proyecto. Todo valor ajustable vive aquí."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

# Rutas
DATA_DIR = ROOT / "data"
STORE_DIR = ROOT / "store"

# El corpus se ordena por tipo jurídico bajo 01_sources/, separado de lo que
# se genera a partir de él. Un documento nuevo sin validar va a 00_inbox/ y
# una versión superada a 90_archive/: ninguna de las dos se indexa.
SOURCES_DIR = DATA_DIR / "01_sources"
DDU_DIR = SOURCES_DIR / "interpretacion_oficial" / "ddu_generales"
FORMULARIOS_DIR = SOURCES_DIR / "tramites" / "formularios_minvu"
ILUSTRADA_DIR = SOURCES_DIR / "material_explicativo" / "oguc_ilustrada"
VISION_DIR = DATA_DIR / "02_processed" / "vision"

# Embeddings (Gemini)
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768

# LLM: Groq como primera opción, Gemini como respaldo ante saturación
LLM_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

# Recuperación y chunking
TOP_K = 5
MAX_CHUNK_CHARS = 2000

# Credenciales
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
