"""Recuperador léxico BM25: búsqueda por palabras, local y sin costo.

Complementa la búsqueda semántica (que entiende paráfrasis pero depende de
una API externa) y la sustituye cuando esa API falla. Es Python puro, sin
extensiones nativas, por lo que funciona igual en Windows ARM64 y en Vercel.

La normalización preserva las referencias normativas, que son justamente
donde este recuperador aporta más: 4.2.7, DDU 514, DS 50, 21.442.
"""

import pickle
import re
import unicodedata
from pathlib import Path

from rank_bm25 import BM25Okapi

from core.config import STORE_DIR

INDEX_PATH = STORE_DIR / "bm25.pkl"

# Token: palabras y números, permitiendo puntos internos (4.2.7, 21.442)
_TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)*")


def tokenize(text):
    """Minúsculas y sin tildes, conservando dígitos y referencias con punto."""
    lowered = unicodedata.normalize("NFD", text.lower())
    sin_tildes = "".join(c for c in lowered if unicodedata.category(c) != "Mn")
    tokens = _TOKEN.findall(sin_tildes)

    # "4.2.7" también se indexa como 4, 2 y 7 para que una consulta parcial
    # ("artículo 4.2") siga encontrando el fragmento.
    extra = []
    for t in tokens:
        if "." in t:
            extra.extend(p for p in t.split(".") if p)
    return tokens + extra


class Bm25Index:
    def __init__(self, bm25):
        self._bm25 = bm25

    @classmethod
    def build(cls, chunks):
        return cls(BM25Okapi([tokenize(c["text"]) for c in chunks]))

    @classmethod
    def load(cls, path=INDEX_PATH):
        with open(path, "rb") as f:
            return cls(pickle.load(f))

    @classmethod
    def exists(cls, path=INDEX_PATH):
        return Path(path).exists()

    def save(self, path=INDEX_PATH):
        path = Path(path)
        path.parent.mkdir(exist_ok=True)
        tmp = path.with_suffix(".pkl.tmp")
        with open(tmp, "wb") as f:
            pickle.dump(self._bm25, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(path)

    @property
    def size(self):
        return len(self._bm25.doc_len)

    def rank(self, query, k):
        """Índices de los k fragmentos más relevantes, de mayor a menor.

        Descarta puntajes nulos: sin coincidencia léxica no hay resultado
        que aportar, y devolverlo solo ensuciaría la fusión.
        """
        scores = self._bm25.get_scores(tokenize(query))
        orden = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [i for i in orden[:k] if scores[i] > 0]
