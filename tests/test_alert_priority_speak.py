"""should_speak honors row.priority=critical (even unknown kinds)."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from jarvis.alert_store import AlertStore
from jarvis.speak_gate import should_speak


def _gaming_snap() -> dict:
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "state": "using",
        "idle_seconds": 0,
        "voice_call": False,
        "apps": [{"name": "counter-strike 2", "category": "game"}],
        "foreground": {
            "title": "Discord",
            "process": "Discord.exe",
            "pid": 1,
            "hwnd": 1,
        },
    }


def test_row_priority_critical_penetrates_gaming(tmp_path) -> None:
    st = AlertStore(tmp_path / "q.jsonl")
    row = st.enqueue(
        kind="weird",
        phrase="Sir, something critical.",
        priority="critical",
    )
    plan = should_speak(row, activity=_gaming_snap())
    assert (plan.action, plan.reason) == ("speak", "critical")


def test_gpu_hard_still_critical_via_priority_for() -> None:
    plan = should_speak("gpu_hard", activity=_gaming_snap())
    assert (plan.action, plan.reason) == ("speak", "critical")
    row = SimpleNamespace(kind="gpu_hard", priority="normal")
    # kind still critical via priority_for even if stored priority wrong
    plan2 = should_speak(row, activity=_gaming_snap())
    assert (plan2.action, plan2.reason) == ("speak", "critical")
