"""Wake helpers (no mic / model download in CI)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.wake import wake_available


def test_wake_available_bool():
    assert isinstance(wake_available(), bool)


def test_text_is_wake_jarvis():
    from jarvis.wake import text_is_wake

    assert text_is_wake("Jarvis")
    assert text_is_wake("hey jarvis")
    assert text_is_wake("賈維斯")
    assert text_is_wake("draaws .")
    assert text_is_wake("daws .")
    assert text_is_wake("do you driverss .")
    assert text_is_wake("he drivefus .")
    assert text_is_wake("jarvus")
    assert not text_is_wake("開 WhatsApp")
    assert not text_is_wake("please ask jarvis to open chrome now")
    assert not text_is_wake("well.")
    assert not text_is_wake("office .")


def test_custom_wake_helpers():
    from jarvis.wake import CUSTOM_WAKE_DIR, has_custom_jarvis_model, _jarvis_score

    assert CUSTOM_WAKE_DIR.name == "wake"
    assert isinstance(has_custom_jarvis_model(), bool)
    assert _jarvis_score({"hey_jarvis": 0.9, "alexa": 0.99}) == 0.9
    assert _jarvis_score({"alexa": 0.99}) == 0.0


def test_default_threshold():
    from jarvis.wake import (
        CUSTOM_DEFAULT_THRESHOLD,
        DEFAULT_THRESHOLD,
        _REARM_BELOW,
        recommended_threshold,
    )

    assert 0.5 <= DEFAULT_THRESHOLD <= 0.6
    assert 0.25 <= CUSTOM_DEFAULT_THRESHOLD <= 0.45
    assert _REARM_BELOW < CUSTOM_DEFAULT_THRESHOLD
    assert recommended_threshold() in (DEFAULT_THRESHOLD, CUSTOM_DEFAULT_THRESHOLD)


def test_wake_model_paths_includes_bundled_and_custom():
    """Custom jarvis.onnx must not drop hey_jarvis (Hey Jarvis still required)."""
    from jarvis import wake as wake_mod

    fake = Path("C:/fake/Jarvis/wake/jarvis.onnx")
    with (
        mock.patch.object(wake_mod, "has_custom_jarvis_model", return_value=True),
        mock.patch.object(wake_mod, "custom_wake_models", return_value=[fake]),
        mock.patch.object(
            wake_mod,
            "_hey_jarvis_model_paths",
            return_value=["C:/fake/hey_jarvis_v0.1.onnx"],
        ),
    ):
        paths = wake_mod._wake_model_paths()
    assert paths[0].endswith("hey_jarvis_v0.1.onnx")
    assert str(fake) in paths


def test_wake_model_paths_bundled_without_custom():
    from jarvis import wake as wake_mod

    with (
        mock.patch.object(wake_mod, "has_custom_jarvis_model", return_value=False),
        mock.patch.object(wake_mod, "custom_wake_models", return_value=[]),
        mock.patch.object(
            wake_mod,
            "_hey_jarvis_model_paths",
            return_value=["C:/fake/hey_jarvis_v0.1.onnx"],
        ),
    ):
        paths = wake_mod._wake_model_paths()
    assert paths == ["C:/fake/hey_jarvis_v0.1.onnx"]


if __name__ == "__main__":
    test_wake_available_bool()
    test_text_is_wake_jarvis()
    test_custom_wake_helpers()
    test_default_threshold()
    test_wake_model_paths_includes_bundled_and_custom()
    test_wake_model_paths_bundled_without_custom()
    print("all passed")
