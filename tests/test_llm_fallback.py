"""Tests del encadenamiento de proveedores de generación. Sin llamadas reales."""

import pytest

from core import llm
from tests.test_bm25 import CHUNKS


def test_usa_groq_cuando_responde(monkeypatch):
    monkeypatch.setattr(llm, "_ask_groq", lambda c: "desde groq")
    monkeypatch.setattr(llm, "_ask_gemini", lambda c: pytest.fail("no debe llamarse"))
    texto, proveedor = llm.generate_answer("pregunta", "contexto")
    assert (texto, proveedor) == ("desde groq", "groq")


def test_cae_a_gemini_si_groq_falla(monkeypatch):
    def satura(_c):
        raise RuntimeError("429 rate limit")

    monkeypatch.setattr(llm, "_ask_groq", satura)
    monkeypatch.setattr(llm, "_ask_gemini", lambda c: "desde gemini")
    texto, proveedor = llm.generate_answer("pregunta", "contexto")
    assert (texto, proveedor) == ("desde gemini", "gemini")


def test_propaga_error_si_ambos_fallan(monkeypatch):
    monkeypatch.setattr(llm, "_ask_groq", lambda c: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(llm, "_ask_gemini", lambda c: (_ for _ in ()).throw(RuntimeError("y")))
    with pytest.raises(Exception):
        llm.generate_answer("pregunta", "contexto")


def test_respuesta_extractiva_conserva_trazabilidad():
    texto = llm.extractive_answer(CHUNKS[:2])
    assert "OGUC" in texto and "página 287" in texto
    assert "Circular DDU 514" in texto
    assert "temporalmente no" in texto


def test_respuesta_extractiva_trunca_fragmentos_largos():
    largo = [{"text": "palabra " * 500, "page": 1, "source": "OGUC"}]
    texto = llm.extractive_answer(largo)
    assert "…" in texto
    assert len(texto) < 1500
