"""Wake helpers (no mic / model download in CI)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.wake import wake_available


def test_wake_available_bool():
    assert isinstance(wake_available(), bool)


def test_text_is_wake_jarvis():
    from jarvis.wake import text_is_wake

    assert text_is_wake("Jarvis")
    assert text_is_wake("hey jarvis")
    assert not text_is_wake("賈維斯")
    assert not text_is_wake("加維斯")
    assert not text_is_wake("開 WhatsApp")
    assert not text_is_wake("")
