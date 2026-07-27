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
    assert not text_is_wake("開 WhatsApp")
    assert not text_is_wake("please ask jarvis to open chrome now")


def test_custom_wake_helpers():
    from jarvis.wake import CUSTOM_WAKE_DIR, has_custom_jarvis_model, _jarvis_score

    assert CUSTOM_WAKE_DIR.name == "wake"
    assert isinstance(has_custom_jarvis_model(), bool)
    assert _jarvis_score({"hey_jarvis": 0.9, "alexa": 0.99}) == 0.9
    assert _jarvis_score({"alexa": 0.99}) == 0.0


def test_default_threshold():
    from jarvis.wake import DEFAULT_THRESHOLD, _REARM_BELOW

    assert 0.5 <= DEFAULT_THRESHOLD <= 0.6
    assert _REARM_BELOW < DEFAULT_THRESHOLD


if __name__ == "__main__":
    test_wake_available_bool()
    test_text_is_wake_jarvis()
    test_custom_wake_helpers()
    test_default_threshold()
    print("all passed")
