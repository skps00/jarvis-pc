"""Parity tests for shared alert_dispatch.enforce (poll_loop + speak_once)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.alert_dispatch import effective_action, enforce
from jarvis.alert_store import AlertStore, StoredAlert
from jarvis.speak_gate import SpeakPlan


@pytest.fixture()
def store(tmp_path: Path) -> AlertStore:
    return AlertStore(tmp_path / "queue.jsonl")


def _all(st: AlertStore) -> list[StoredAlert]:
    if not st.path.is_file():
        return []
    return [
        StoredAlert.from_dict(json.loads(line))
        for line in st.path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _ledger(st: AlertStore) -> list[dict]:
    path = st._ledger_path
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def test_enforce_hold_then_release_roundtrip(store: AlertStore) -> None:
    row = store.enqueue(kind="whatsapp", phrase="Sir, WhatsApp has a new message.")
    cfg = SimpleNamespace(alert_gaming="hold", alert_hold_ttl_s=900)
    result = enforce(
        store,
        row,
        SpeakPlan("hold", "gaming"),
        cfg=cfg,
        speak=lambda _t: True,
        claim=True,
    )
    assert result == "hold"
    rows = _all(store)
    assert len(rows) == 1
    assert rows[0].state == "held"
    events = [(e["event"], e["reason"]) for e in _ledger(store)]
    assert ("hold", "ok") in events
    assert store.release_held() == 1
    assert store.list_open()[0].id == row.id


def test_enforce_digest_and_drop(store: AlertStore) -> None:
    dig = store.enqueue(kind="discord", phrase="Sir, Discord has a new message.")
    cfg = SimpleNamespace(alert_gaming="hold", alert_hold_ttl_s=900)
    assert (
        enforce(
            store,
            dig,
            SpeakPlan("digest", "policy"),
            cfg=cfg,
            speak=lambda _t: True,
        )
        == "digest"
    )
    assert any(e.get("event") == "digest" for e in _ledger(store))
    assert _all(store)[0].state == "digest"

    drop_row = store.enqueue(kind="cursor", phrase="Sir, Cursor needs attention.")
    assert (
        enforce(
            store,
            drop_row,
            SpeakPlan("drop", "voice_off"),
            cfg=cfg,
            speak=lambda _t: True,
        )
        == "drop"
    )
    assert not any(r.id == drop_row.id for r in _all(store))
    assert any(
        e.get("event") == "drop" and e.get("reason") == "voice_off"
        for e in _ledger(store)
    )


def test_effective_action_gaming_drop_override() -> None:
    cfg_drop = SimpleNamespace(alert_gaming="drop")
    cfg_hold = SimpleNamespace(alert_gaming="hold")
    plan = SpeakPlan("hold", "gaming")
    assert effective_action(plan, cfg=cfg_drop) == "drop"
    assert effective_action(plan, cfg=cfg_hold) == "hold"
    assert effective_action(SpeakPlan("digest", "policy"), cfg=cfg_drop) == "digest"


def test_speak_claim_and_restore(store: AlertStore) -> None:
    cfg = SimpleNamespace(alert_gaming="hold", alert_hold_ttl_s=900)
    fail_row = store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    assert (
        enforce(
            store,
            fail_row,
            SpeakPlan("speak", "policy"),
            cfg=cfg,
            speak=lambda _t: False,
            claim=True,
        )
        == "none"
    )
    rows = _all(store)
    assert len(rows) == 1
    assert rows[0].id == fail_row.id
    assert rows[0].state == "pending"

    ok_row = store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    assert (
        enforce(
            store,
            ok_row,
            SpeakPlan("speak", "policy"),
            cfg=cfg,
            speak=lambda _t: True,
            claim=True,
        )
        == "speak"
    )
    open_ids = {r.id for r in store.list_open()}
    assert ok_row.id not in open_ids
    assert fail_row.id in open_ids


def test_choke_drop_reason_parity_poll_and_once(
    store: AlertStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """poll_loop _speak_choked and speak_once enforce path share drop reason."""
    import importlib.util

    import jarvis.alert_dispatch as alert_dispatch

    monkeypatch.setattr(
        alert_dispatch, "prepare_phrase", lambda _row: (None, "metric")
    )
    cfg = SimpleNamespace(alert_gaming="hold", alert_hold_ttl_s=900)

    row_a = store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    poll_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "hermes_alert_poll_loop.py"
    )
    spec = importlib.util.spec_from_file_location("hermes_alert_poll_loop", poll_path)
    assert spec and spec.loader
    poll = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(poll)
    assert poll._speak_choked(store, row_a, speak=lambda _p: True, claim=False) is False

    row_b = store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    enforce(
        store,
        row_b,
        SpeakPlan("speak", "off"),
        cfg=cfg,
        speak=lambda _p: True,
        claim=False,
    )

    def _drop_reasons(rid: str) -> list[str]:
        return [
            e["reason"]
            for e in _ledger(store)
            if e.get("id") == rid and e.get("event") == "drop"
        ]

    ra, rb = _drop_reasons(row_a.id), _drop_reasons(row_b.id)
    assert ra and rb
    assert ra[0] == rb[0] == "metric"
