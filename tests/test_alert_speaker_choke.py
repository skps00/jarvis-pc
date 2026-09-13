"""TTS choke point: metric/URL/CJK/empty text must not reach synthesis."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from jarvis.alert_policy import guard_for_speech, shape, speech_guard


def test_guard_for_speech_reasons() -> None:
    assert guard_for_speech("GPU=95C mem=88") == "metric"
    assert guard_for_speech("see http://x.com") == "url"
    assert guard_for_speech("Sir, all systems nominal.") is None
    assert guard_for_speech("測試") == "cjk"
    assert guard_for_speech("   ") == "empty"


def test_guard_short_digits_ok_long_run_metric() -> None:
    assert guard_for_speech("Sir, 3 messages while you were away.") is None
    assert guard_for_speech("Sir, 12345 events.") == "metric"


def test_shaped_alert_phrase_passes_guard() -> None:
    phrase = shape("gpu_health", phrase="hot")
    assert guard_for_speech(phrase) is None


def test_mouth_skips_synthesis_on_guard_reject(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis import mouth

    called: list[str] = []
    guards: list[str] = []

    def fake_sub(text: str, *, force: bool = False, guard: str = "strict") -> bool:
        called.append(text)
        guards.append(guard)
        return True

    monkeypatch.setattr(mouth, "_prefer_subprocess", True)
    monkeypatch.setattr(mouth, "_tts_params", lambda: (True, 1.0, 1.0, None))
    monkeypatch.setattr(mouth, "_speak_subprocess", fake_sub)

    assert mouth.speak("GPU=95C mem=88", blocking=True, force=True) is False
    assert called == []

    ok = mouth.speak("Sir, all systems nominal.", blocking=True, force=True)
    assert ok is True
    assert called == ["Sir, all systems nominal."]
    assert guards == ["strict"]


def test_jarvis_speak_fails_closed_on_metric(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    pytest.importorskip("starlette")

    from jarvis.alert_store import AlertStore
    from jarvis import mcp_alerts_http as mah

    monkeypatch.setattr("jarvis.activity.gaming", lambda: False)
    monkeypatch.setattr("jarvis.activity.voice_call", lambda: False)
    monkeypatch.setattr(mah, "_speak_last_ts", 0.0)

    spoken: list[str] = []
    monkeypatch.setattr(
        "jarvis.mouth.speak",
        lambda text, **kwargs: spoken.append(text) or True,
    )

    st = AlertStore(tmp_path / "q.jsonl")
    mcp, _app, _ = mah.build_mcp(store=st, token="t" * 16, host="127.0.0.1")
    speak_fn = mcp._tool_manager.get_tool("jarvis_speak").fn

    bad = speak_fn("GPU=95C mem=88")
    assert bad["ok"] is False
    assert bad["reason"] == "metric"
    assert spoken == []

    # Clear rate-limit window between calls.
    mah._speak_last_ts = time.monotonic() - 10.0
    good = speak_fn("Sir, all systems nominal.")
    assert good.get("reason") not in {"metric", "url", "cjk", "empty"}
    assert good["ok"] is True

    mah._speak_last_ts = time.monotonic() - 10.0
    # Missing trailing period → strict_ok False (same as mouth).
    no_period = speak_fn("Sir, GPU critical limit reached")
    assert no_period["ok"] is False
    assert no_period.get("reason")
    assert "Sir, GPU critical limit reached" not in spoken


def test_speech_guard_modes() -> None:
    assert speech_guard("Sir, the year is 2026.") == "metric"
    assert speech_guard("Sir, the year is 2026.", mode="lenient") is None


def test_mouth_lenient_speaks_metric_like_text(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis import mouth

    called: list[str] = []
    guards: list[str] = []

    def fake_sub(text: str, *, force: bool = False, guard: str = "strict") -> bool:
        called.append(text)
        guards.append(guard)
        return True

    monkeypatch.setattr(mouth, "_prefer_subprocess", True)
    monkeypatch.setattr(mouth, "_tts_params", lambda: (True, 1.0, 1.0, None))
    monkeypatch.setattr(mouth, "_speak_subprocess", fake_sub)

    phrase = "Sir, the year is 2026."
    assert mouth.speak(phrase, guard="lenient", blocking=True, force=True) is True
    assert called == [phrase]
    assert guards == ["lenient"]
    called.clear()
    guards.clear()
    assert mouth.speak(phrase, guard="strict", blocking=True, force=True) is False
    assert called == []
    assert guards == []
