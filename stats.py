"""Reporte de uso de NormaObra a partir de los eventos guardados en Upstash.

Requiere UPSTASH_REDIS_REST_URL y UPSTASH_REDIS_REST_TOKEN en .env
(las mismas variables configuradas en Vercel).

Uso:
    python stats.py            # reporte en consola
    python stats.py --csv      # exporta consultas.csv para analizar aparte
"""

import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
LIST_KEY = "normaobra:queries"


def fetch_events():
    r = requests.post(
        f"{REDIS_URL}/pipeline",
        headers={"Authorization": f"Bearer {REDIS_TOKEN}"},
        json=[["LRANGE", LIST_KEY, "0", "-1"]],
        timeout=30,
    )
    r.raise_for_status()
    return [json.loads(x) for x in r.json()[0]["result"]]


def percentil(valores, p):
    if not valores:
        return 0
    ordenados = sorted(valores)
    return ordenados[min(int(len(ordenados) * p / 100), len(ordenados) - 1)]


def main():
    if not REDIS_URL or not REDIS_TOKEN:
        print("Falta configurar Upstash: agrega UPSTASH_REDIS_REST_URL y")
        print("UPSTASH_REDIS_REST_TOKEN en .env (cópialas desde Vercel).")
        return

    eventos = fetch_events()
    if not eventos:
        print("Aún no hay consultas registradas.")
        return

    if "--csv" in sys.argv:
        with open("consultas.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["fecha", "pregunta", "ms", "ok", "sin_cobertura", "fuentes"])
            for e in reversed(eventos):
                w.writerow([
                    datetime.fromtimestamp(e["ts"], timezone.utc).isoformat(),
                    e["question"],
                    e["latency_ms"],
                    e["ok"],
                    e.get("sin_cobertura", ""),
                    " | ".join(e.get("sources", [])),
                ])
        print(f"Exportado consultas.csv con {len(eventos)} consultas")
        return

    total = len(eventos)
    fallidas = [e for e in eventos if not e["ok"]]
    sin_cobertura = [e for e in eventos if e.get("sin_cobertura")]
    latencias = [e["latency_ms"] for e in eventos if e["ok"]]
    desde = datetime.fromtimestamp(min(e["ts"] for e in eventos), timezone.utc)

    print(f"\n=== NormaObra · {total} consultas desde {desde:%d-%m-%Y %H:%M} UTC ===\n")
    print(f"  Errores          {len(fallidas):>4}  ({len(fallidas) / total:.0%})")
    print(f"  Sin cobertura    {len(sin_cobertura):>4}  ({len(sin_cobertura) / total:.0%})")
    print(f"  Latencia mediana {percentil(latencias, 50) / 1000:>4.1f}s")
    print(f"  Latencia p95     {percentil(latencias, 95) / 1000:>4.1f}s")

    print("\n--- Consultas más frecuentes")
    for pregunta, n in Counter(e["question"].lower() for e in eventos).most_common(10):
        print(f"  {n:>3}x  {pregunta[:70]}")

    print("\n--- Documentos más citados")
    fuentes = Counter(s for e in eventos for s in e.get("sources", []))
    for fuente, n in fuentes.most_common(10):
        print(f"  {n:>3}x  {fuente}")

    if sin_cobertura:
        print("\n--- Preguntas que el corpus no cubrió (oportunidades)")
        for e in sin_cobertura[:10]:
            print(f"  · {e['question'][:70]}")

    print()


if __name__ == "__main__":
    main()
