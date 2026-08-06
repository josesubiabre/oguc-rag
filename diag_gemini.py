"""Diagnóstico de la API key de Gemini: prueba embeddings y chat."""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("GEMINI_API_KEY", "")
print("key:", KEY[:6] + "...", "largo:", len(KEY))

BASE = "https://generativelanguage.googleapis.com/v1beta"

tests = {
    "embeddings (1 texto)": (
        f"{BASE}/models/gemini-embedding-001:embedContent",
        {"model": "models/gemini-embedding-001", "content": {"parts": [{"text": "hola"}]}},
    ),
    "chat (gemini-2.5-flash-lite)": (
        f"{BASE}/models/gemini-2.5-flash-lite:generateContent",
        {"contents": [{"parts": [{"text": "di hola"}]}]},
    ),
}

for name, (url, body) in tests.items():
    r = requests.post(f"{url}?key={KEY}", json=body, timeout=30)
    print(f"\n=== {name}: HTTP {r.status_code}")
    try:
        data = r.json()
        if "error" in data:
            print(json.dumps(data["error"], indent=2)[:2500])
        else:
            print("OK:", str(data)[:200])
    except Exception:
        print(r.text[:500])
