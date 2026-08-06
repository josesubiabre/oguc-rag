# RAG OGUC 🇨🇱

Asistente de preguntas y respuestas sobre la **Ordenanza General de Urbanismo y Construcciones (OGUC)** de Chile, usando RAG (Retrieval-Augmented Generation).

## Arquitectura

- **PDF → fragmentos**: `pypdf` + corte por límites de "Artículo N°"
- **Embeddings**: API de Google Gemini (`gemini-embedding-001`)
- **Base vectorial**: matriz numpy + búsqueda por similitud coseno (sin dependencias nativas — funciona incluso en Windows ARM64)
- **LLM**: Llama 3.3 70B vía Groq (gratis)

### Estructura

```
core/               # lógica del RAG, un módulo por responsabilidad
├── config.py       # toda la configuración
├── chunking.py     # PDF → fragmentos
├── embeddings.py   # cliente Gemini (cambiar de proveedor = tocar solo esto)
├── store.py        # base vectorial (búsqueda híbrida futura = tocar solo esto)
├── llm.py          # prompt + Groq
└── rag.py          # orquestación pregunta → respuesta
ingest.py           # script de ingesta (usa core/)
query.py            # CLI de consultas (usa core/)
app.py              # API FastAPI (usa core/)
tests/              # pytest, sin consumo de APIs
web/                # frontend Next.js + Tailwind + shadcn
```

Tests: `python -m pytest tests/`

## Uso

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Crea un archivo `.env` con:

```
GROQ_API_KEY=...     # console.groq.com
GEMINI_API_KEY=...   # aistudio.google.com
```

Luego:

```bash
python ingest.py    # vectoriza la OGUC (una sola vez)
python query.py     # pregunta en lenguaje natural (terminal)
```

### Interfaz web

Backend (API):

```bash
uvicorn app:app --reload
```

Frontend (Next.js + Tailwind + shadcn, en `web/`):

```bash
cd web
npm install
npm run dev
```

Abre http://localhost:3000 (el frontend reenvía `/api/*` al backend del puerto 8000).

## Roadmap

- [x] RAG funcionando (ingesta + consultas con citas de artículos)
- [x] Interfaz web local (Next.js + Tailwind + shadcn, diseño estilo v0)
- [ ] Despliegue público (hosting gratuito)
- [ ] Analítica de uso
