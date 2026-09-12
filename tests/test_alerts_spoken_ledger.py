"""Spoken ledger must record real TTS success (mode=off / claim / digest)."""

from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from types import SimpleNamespace

from jarvis.alert_dispatch import enforce
from jarvis.alert_policy import is_speakable
from jarvis.alert_store import (
    AlertStore,
    format_missed_sentence,
    label_for,
    read_miss_ledger,
)
from jarvis.speak_gate import SpeakPlan

_POLL = Path(__file__).resolve().parents[1] / "scripts" / "hermes_alert_poll_loop.py"


def _load_poll():
    spec = importlib.util.spec_from_file_location("hermes_alert_poll_loop", _POLL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ledger_events(store: AlertStore, alert_id: str) -> list[dict]:
    path = store._ledger_path
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("id") == alert_id:
            out.append(d)
    return out


def test_enforce_claim_false_writes_spoken(tmp_path: Path) -> None:
    store = AlertStore(tmp_path / "q.jsonl")
    row = store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    cfg = SimpleNamespace(alert_gaming="hold")
    assert (
        enforce(
            store,
            row,
            SpeakPlan("speak", "off"),
            cfg=cfg,
            speak=lambda _t: True,
            claim=False,
        )
        == "speak"
    )
    events = [e["event"] for e in _ledger_events(store, row.id)]
    assert "spoken" in events
    assert "speak_claim" not in events
    entries = read_miss_ledger(store.path, hours=24.0)
    assert format_missed_sentence(entries) == "Sir, nothing missed."


def test_enforce_claim_true_speak_fail_no_spoken(tmp_path: Path) -> None:
    store = AlertStore(tmp_path / "q.jsonl")
    row = store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    cfg = SimpleNamespace(alert_gaming="hold")
    assert (
        enforce(
            store,
            row,
            SpeakPlan("speak", "policy"),
            cfg=cfg,
            speak=lambda _t: False,
            claim=True,
        )
        == "none"
    )
    events = [e["event"] for e in _ledger_events(store, row.id)]
    assert "spoken" not in events
    assert "speak_claim" in events
    assert "speak_fail" in events
    entries = read_miss_ledger(store.path, hours=24.0)
    sentence = format_missed_sentence(entries)
    assert "went unanswered" in sentence


def test_digest_flush_spoken_or_restore(tmp_path: Path) -> None:
    poll = _load_poll()
    store = AlertStore(tmp_path / "q.jsonl")
    row = store.enqueue(kind="whatsapp", phrase="WhatsApp has a new message.")
    t0 = 1_700_000_000.0
    store.mark_digest([row.id], now=t0)
    assert (
        poll._flush_digest_common(
            store, speak=lambda _p: True, now=t0 + 1.0
        )
        is not None
    )
    events_ok = [e["event"] for e in _ledger_events(store, row.id)]
    reasons_ok = [e.get("reason") for e in _ledger_events(store, row.id)]
    assert "spoken" in events_ok
    assert "digest_flush" in reasons_ok

    row2 = store.enqueue(kind="discord", phrase="Sir, Discord ping.")
    store.mark_digest([row2.id], now=t0)
    assert (
        poll._flush_digest_common(
            store, speak=lambda _p: False, now=t0 + 2.0
        )
        is None
    )
    events_fail = [e["event"] for e in _ledger_events(store, row2.id)]
    assert "spoken" not in events_fail or events_fail.count("spoken") == 0
    # No spoken after failed flush (speak_claim is not "spoken").
    assert not any(
        e["event"] == "spoken" for e in _ledger_events(store, row2.id)
    )
    assert any(
        e["event"] == "digest_restore" for e in _ledger_events(store, row2.id)
    )


def test_digest_sentence_speakable_after_digit_strip() -> None:
    poll = _load_poll()
    # Unknown kind with 4+ digits must not poison the digest sentence.
    assert "1234" not in label_for("extra:app1234")
    sentence = poll.format_digest_sentence({"extra:app1234": 1})
    assert sentence is not None
    assert is_speakable(sentence)


def test_flush_fallback_when_mouth_would_refuse(tmp_path: Path) -> None:
    poll = _load_poll()
    store = AlertStore(tmp_path / "q.jsonl")
    row = store.enqueue(kind="whatsapp", phrase="WhatsApp has a new message.")
    t0 = time.time()
    store.mark_digest([row.id], now=t0)
    spoken: list[str] = []

    def capture(p: str) -> bool:
        spoken.append(p)
        return True

    # Force format_digest_sentence to return an unspeakable string.
    orig = poll.format_digest_sentence
    poll.format_digest_sentence = lambda _c: "Sir, app1234 noise while you were away."
    try:
        out = poll._flush_digest_common(store, speak=capture, now=t0 + 1.0)
    finally:
        poll.format_digest_sentence = orig
    assert out == "Sir, you have new alerts while you were away."
    assert spoken == ["Sir, you have new alerts while you were away."]
    assert is_speakable(spoken[0])


def test_clear_digest_by_id_any_state(tmp_path: Path) -> None:
    store = AlertStore(tmp_path / "q.jsonl")
    a = store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    store.mark_digest([a.id])
    store.mark_spoken([a.id])
    assert store.clear_digest([a.id]) == 1
    assert store.path.read_text(encoding="utf-8").strip() == ""

    b = store.enqueue(kind="test", phrase="Sir, another test alert.")
    store.mark_digest([b.id])
    assert store.clear_digest([b.id]) == 1
    assert not any(
        line.strip() for line in store.path.read_text(encoding="utf-8").splitlines()
    )


def test_release_held_noop_skips_write(tmp_path: Path) -> None:
    store = AlertStore(tmp_path / "q.jsonl")
    store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    before = store.path.read_text(encoding="utf-8")
    mtime = store.path.stat().st_mtime_ns
    time.sleep(0.02)
    assert store.release_held() == 0
    assert store.path.read_text(encoding="utf-8") == before
    assert store.path.stat().st_mtime_ns == mtime


def test_digest_cap_drops_oldest(tmp_path: Path) -> None:
    store = AlertStore(tmp_path / "q.jsonl", held_cap=2, digest_cap=4)
    now = time.time()
    for i in range(9):
        r = store.enqueue(kind="whatsapp", phrase=f"WhatsApp has a new message {i}.")
        store.mark_digest([r.id], now=now - float(9 - i))   # 由最舊到最新，全部喺 TTL 內
    digests = [r for r in store.digest_rows(now=now)]
    assert len(digests) == 4
    # 最舊 5 條應該已被 digest_cap 掉；最新 4 條仍在
    assert "WhatsApp has a new message 8." in {r.phrase for r in digests}
    ledger = store._ledger_path.read_text(encoding="utf-8")
    assert "digest_cap" in ledger
    assert any(
        json.loads(ln).get("reason") == "digest_cap"
        for ln in ledger.splitlines()
        if ln.strip()
    )
