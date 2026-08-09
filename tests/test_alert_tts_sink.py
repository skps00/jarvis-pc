"""Regression: hermes sink must not call mouth.speak."""

from __future__ import annotations

from pathlib import Path

import jarvis.mouth as mouth
from jarvis.alert_store import AlertStore
from jarvis.settings import Settings, _clamp


def test_hermes_enqueue_does_not_need_mouth(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []

    def boom(*_a, **_k):
        calls.append("speak")
        raise AssertionError("mouth.speak must not run for hermes sink")

    monkeypatch.setattr(mouth, "speak", boom)
    st = AlertStore(tmp_path / "q.jsonl")
    row = st.enqueue(kind="discord", phrase="Sir, Discord needs attention.")
    assert row.phrase.startswith("Sir")
    assert calls == []
    assert st.peek() is not None


def test_settings_alert_tts_clamp() -> None:
    assert _clamp(Settings(alert_tts="NOPE")).alert_tts == "hermes"
    assert _clamp(Settings(alert_tts="piper")).alert_tts == "piper"
    assert _clamp(Settings(alert_tts="OFF")).alert_tts == "off"
    assert Settings().alert_tts == "hermes"
