"""speak_gate: is_gaming_v2 + should_speak (pure decision; no file writes)."""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis import activity
from jarvis.speak_gate import is_gaming_v2, should_speak

_POLICY_ON = SimpleNamespace(
    alert_voice=True,
    alert_discord=True,
    alert_whatsapp=True,
    alert_cursor=True,
)


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _real_cs2_bg(**overrides) -> dict:
    # Real measured fixture shape (CS2+MC running, Discord foreground).
    base = {
        "timestamp": _now_iso(),
        "state": "using",
        "game": "counter-strike 2",
        "game_started": False,
        "fullscreen": False,
        "idle_seconds": 0,
        "foreground": {
            "hwnd": 67746,
            "title": "@JARVIS - Discord",
            "pid": 23084,
            "process": "Discord.exe",
        },
        "voice_call": False,
        "apps": [
            {"name": "counter-strike 2", "category": "game"},
            {"name": "minecraft", "category": "game"},
        ],
    }
    base.update(overrides)
    return base


REAL_CS2_BG = _real_cs2_bg()


def test_is_gaming_v2_true_while_v1_false() -> None:
    snap = _real_cs2_bg()
    assert is_gaming_v2(snap) is True
    # v1 gaming() semantics: state == "playing" only
    assert (snap.get("state") == "playing") is False


def test_launcher_idle_and_no_game() -> None:
    assert is_gaming_v2(_real_cs2_bg(idle_seconds=300)) is False
    assert is_gaming_v2(_real_cs2_bg(apps=[])) is False


def test_stale_snapshot() -> None:
    old = (datetime.now() - timedelta(seconds=400)).strftime("%Y-%m-%dT%H:%M:%S")
    assert is_gaming_v2(_real_cs2_bg(timestamp=old, idle_seconds=0)) is False


def test_activity_stale_holds_non_critical() -> None:
    old = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    stale = _real_cs2_bg(timestamp=old, apps=[], idle_seconds=300)
    plan = should_speak("whatsapp", activity=stale, settings=_POLICY_ON)
    assert (plan.action, plan.reason) == ("hold", "activity_stale")
    plan_c = should_speak("gpu_hard", activity=stale)
    assert (plan_c.action, plan_c.reason) == ("speak", "critical")
    no_ts = dict(stale)
    no_ts.pop("timestamp", None)
    plan2 = should_speak("whatsapp", activity=no_ts, settings=_POLICY_ON)
    assert (plan2.action, plan2.reason) == ("hold", "activity_stale")


def test_critical_ignores_alert_voice_off() -> None:
    off = SimpleNamespace(
        alert_voice=False,
        alert_discord=False,
        alert_whatsapp=False,
        alert_cursor=False,
    )
    plan = should_speak("gpu_hard", activity=_real_cs2_bg(apps=[]), settings=off)
    assert (plan.action, plan.reason) == ("speak", "critical")
    # FIX5: alert_voice=False alone must not mute CRITICAL (parity with policy_for).
    plan2 = should_speak(
        "gpu_hard",
        settings=SimpleNamespace(alert_voice=False),
    )
    assert (plan2.action, plan2.reason) == ("speak", "critical")


def test_critical_penetrates_gaming() -> None:
    snap = _real_cs2_bg()
    plan = should_speak("gpu_hard", activity=snap)
    assert (plan.action, plan.reason) == ("speak", "critical")
    plan2 = should_speak("cursor_approve", activity=snap)
    assert (plan2.action, plan2.reason) == ("speak", "critical")


def test_whatsapp_hold_gaming_or_digest() -> None:
    snap = _real_cs2_bg()
    plan = should_speak("whatsapp", activity=snap, settings=_POLICY_ON)
    assert (plan.action, plan.reason) == ("hold", "gaming")
    quiet = _real_cs2_bg(apps=[])
    plan2 = should_speak("whatsapp", activity=quiet, settings=_POLICY_ON)
    assert (plan2.action, plan2.reason) == ("digest", "policy")


def test_voice_call_hold() -> None:
    snap = _real_cs2_bg(voice_call=True)
    plan = should_speak("whatsapp", activity=snap, settings=_POLICY_ON)
    assert (plan.action, plan.reason) == ("hold", "voice_call")


def test_gaming_v1_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(activity, "load_activity", lambda: {"state": "using"})
    assert activity.gaming() is False
    src = inspect.getsource(activity.gaming)
    assert '== "playing"' in src or "== 'playing'" in src


def test_purity_no_file_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a, **_k):
        raise AssertionError("Path.write_text must not be called")

    monkeypatch.setattr(Path, "write_text", boom)
    snap = _real_cs2_bg()
    assert is_gaming_v2(snap) is True
    plan = should_speak("whatsapp", activity=snap, settings=_POLICY_ON)
    assert plan.action == "hold"
    plan2 = should_speak(SimpleNamespace(kind="gpu_hard"), activity=snap)
    assert (plan2.action, plan2.reason) == ("speak", "critical")
