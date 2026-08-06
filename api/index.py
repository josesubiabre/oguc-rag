"""Punto de entrada para Vercel: expone la app FastAPI como función serverless.

Vercel detecta la variable `app` (ASGI) y enruta las peticiones aquí según
vercel.json. La app real vive en app.py, en la raíz del repositorio.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402, F401
