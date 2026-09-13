"""alert_shadow writers + poll-loop shadow helpers (mode=off = zero files)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis import alert_shadow
from jarvis.alert_store import AlertStore
from jarvis.speak_gate import SpeakPlan

_POLL = Path(__file__).resolve().parents[1] / "scripts" / "hermes_alert_poll_loop.py"


def _load_poll():
    spec = importlib.util.spec_from_file_location("hermes_alert_poll_loop", _POLL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _idle_activity() -> dict:
    return {
        "timestamp": "2026-01-01T00:00:00",
        "state": "idle",
        "idle_seconds": 300,
        "voice_call": False,
        "apps": [],
        "foreground": {"title": "", "process": "", "pid": 0, "hwnd": 0},
    }


@pytest.fixture()
def alerts_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    q = tmp_path / "queue.jsonl"
    monkeypatch.setattr(alert_shadow, "shadow_ledger_path", lambda: tmp_path / "shadow_ledger.jsonl")
    monkeypatch.setattr(alert_shadow, "heartbeat_path", lambda: tmp_path / "shadow_heartbeat.jsonl")
    monkeypatch.setattr(alert_shadow, "_marker_path", lambda: tmp_path / "shadow_heartbeat.marker")
    monkeypatch.setattr(
        "jarvis.alert_store.default_queue_path",
        lambda: q,
    )
    return tmp_path


def test_record_decision_one_json_line(alerts_dir: Path) -> None:
    plan = SpeakPlan("hold", "gaming")
    alert_shadow.record_decision("whatsapp", "abc-1", plan, mode="shadow", now=1_700_000_000.0)
    ledger = alerts_dir / "shadow_ledger.jsonl"
    assert ledger.is_file()
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["id"] == "abc-1"
    assert obj["kind"] == "whatsapp"
    assert obj["mode"] == "shadow"
    assert obj["decision"] == "hold"
    assert obj["reason"] == "gaming"
    assert "ts" in obj


def test_mode_off_creates_no_shadow_file(alerts_dir: Path) -> None:
    poll = _load_poll()
    store = AlertStore(alerts_dir / "queue.jsonl")
    store.enqueue(kind="discord", phrase="Sir, ping.")
    spoken: list[str] = []
    state: dict = {"quiet_since": None, "was_busy": False}
    poll.tick(
        store,
        state,
        settings=SimpleNamespace(alert_policy_mode="off"),
        speak=lambda p: spoken.append(p) or True,
        activity=_idle_activity(),
    )
    assert spoken == ["Sir, ping."]
    assert not (alerts_dir / "shadow_ledger.jsonl").exists()
    assert not (alerts_dir / "shadow_heartbeat.jsonl").exists()
    assert list(alerts_dir.glob("shadow*")) == []


def test_heartbeat_throttle(alerts_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jarvis.activity.signals", lambda: {"idle_seconds": 0})
    monkeypatch.setattr("jarvis.activity.gaming", lambda: False)
    monkeypatch.setattr("jarvis.speak_gate.is_gaming_v2", lambda activity=None: False)
    monkeypatch.setattr(
        "jarvis.settings.load_settings",
        lambda: SimpleNamespace(alert_policy_mode="shadow"),
    )
    t0 = 1_700_000_000.0
    assert alert_shadow.record_heartbeat(interval_s=45, now=t0) is True
    hb = alerts_dir / "shadow_heartbeat.jsonl"
    n1 = len([ln for ln in hb.read_text(encoding="utf-8").splitlines() if ln.strip()])
    assert n1 == 1
    assert alert_shadow.record_heartbeat(interval_s=45, now=t0 + 10) is False
    n2 = len([ln for ln in hb.read_text(encoding="utf-8").splitlines() if ln.strip()])
    assert n2 == 1
    assert alert_shadow.record_heartbeat(interval_s=45, now=t0 + 60) is True
    n3 = len([ln for ln in hb.read_text(encoding="utf-8").splitlines() if ln.strip()])
    assert n3 == 2


def test_rotation_at_2mb(alerts_dir: Path) -> None:
    ledger = alerts_dir / "shadow_ledger.jsonl"
    ledger.write_bytes(b"x" * int(2.1 * 1024 * 1024))
    plan = SpeakPlan("speak", "critical")
    alert_shadow.record_decision("gpu_hard", "id-2", plan, mode="shadow")
    bak = Path(str(ledger) + ".1")
    assert bak.is_file()
    assert bak.stat().st_size >= int(2.1 * 1024 * 1024)
    assert ledger.is_file()
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["id"] == "id-2"


def test_fail_open_no_raise(alerts_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(alert_shadow, "_append_jsonl", boom)
    plan = SpeakPlan("drop", "policy")
    alert_shadow.record_decision("x", "y", plan, mode="shadow")  # must not raise
    assert alert_shadow.record_heartbeat(now=1.0) is False

    poll = _load_poll()
    store = AlertStore(alerts_dir / "queue.jsonl")
    store.enqueue(kind="discord", phrase="Sir, ok.")
    spoken: list[str] = []
    state: dict = {"quiet_since": None, "was_busy": False}
    row = poll.tick(
        store,
        state,
        settings=SimpleNamespace(
            alert_policy_mode="shadow",
            alert_digest_interval_s=1800,
        ),
        speak=lambda p: spoken.append(p) or True,
        activity=_idle_activity(),
    )
    assert row is not None
    assert spoken == ["Sir, ok."]


def test_shadow_still_speaks(alerts_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    poll = _load_poll()
    monkeypatch.setattr(
        poll,
        "plan_for",
        lambda row, mode, activity=None, settings=None: SpeakPlan("hold", "gaming"),
    )
    monkeypatch.setattr("jarvis.activity.signals", lambda: {"idle_seconds": 300})
    monkeypatch.setattr("jarvis.activity.gaming", lambda: False)
    monkeypatch.setattr("jarvis.speak_gate.is_gaming_v2", lambda activity=None: False)
    store = AlertStore(alerts_dir / "queue.jsonl")
    store.enqueue(kind="whatsapp", phrase="Sir, message.")
    spoken: list[str] = []
    state: dict = {"quiet_since": None, "was_busy": False}
    poll.tick(
        store,
        state,
        settings=SimpleNamespace(
            alert_policy_mode="shadow",
            alert_digest_interval_s=1800,
        ),
        speak=lambda p: spoken.append(p) or True,
        activity=_idle_activity(),
    )
    assert spoken == ["Sir, message."]
    ledger = alerts_dir / "shadow_ledger.jsonl"
    assert ledger.is_file()
    obj = json.loads(ledger.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert obj["decision"] == "hold"
    assert obj["mode"] == "shadow"
