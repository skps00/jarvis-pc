"""Unit tests for brain.translate_to_english_short (mock LLM, no live API)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.brain import translate_to_english_short  # noqa: E402


def test_empty_returns_none():
    assert translate_to_english_short("") is None


def test_pure_english_passthrough():
    assert translate_to_english_short("Open Cursor, sir.") == "Open Cursor, sir."


def test_long_english_trimmed():
    words = " ".join(f"w{i}" for i in range(25))
    out = translate_to_english_short(words)
    assert out is not None
    assert len(out.split()) <= 20


def test_cjk_without_llm_key_returns_none():
    with mock.patch("jarvis.brain.llm_configured", return_value=False):
        assert translate_to_english_short("已開啟 Cursor") is None


def test_cjk_with_mocked_chat():
    with mock.patch("jarvis.brain.llm_configured", return_value=True):
        with mock.patch("jarvis.brain._chat", return_value="Opening Cursor, sir."):
            assert (
                translate_to_english_short("已開啟 Cursor") == "Opening Cursor, sir."
            )


def test_mocked_chat_raising_returns_none():
    with mock.patch("jarvis.brain.llm_configured", return_value=True):
        with mock.patch("jarvis.brain._chat", side_effect=RuntimeError("boom")):
            assert translate_to_english_short("已開啟 Cursor") is None
