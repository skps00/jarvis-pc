"""Miss ledger reader + alert_miss local intent (tmp paths only)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.alert_store import (
    AlertStore,
    _label_for,
    format_missed_sentence,
    miss_ledger_path,
    read_miss_ledger,
)
from jarvis.config import load_registry
from jarvis.engine import execute_utterance
from jarvis.router import route

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def store(tmp_path: Path) -> AlertStore:
    return AlertStore(tmp_path / "queue.jsonl", max_depth=8, default_ttl_s=600.0)


def _reg():
    return load_registry(ROOT / "config" / "profiles.example.yaml")


def test_every_transition_writes_ledger(store: AlertStore) -> None:
    a = store.enqueue(kind="discord", phrase="Sir, Discord needs attention.")
    store.peek(lease_s=10)
    store.hold([a.id], ttl_s=60)
    store.mark_digest([a.id])
    store.drop([a.id], reason="test_drop")
    ledger = miss_ledger_path(store.path)
    assert ledger.is_file()
    events = set()
    for line in ledger.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        events.add(d["event"])
    # peek is neutral (no ledger); claim writes speak_claim; hold → event "hold"
    assert "enqueue" in events
    assert "hold" in events
    assert "digest" in events
    assert "drop" in events


def test_ledger_rotate(store: AlertStore, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jarvis.alert_store.LEDGER_ROTATE_BYTES", 40)
    store.enqueue(kind="a", phrase="Sir, first alert.")
    store.enqueue(kind="b", phrase="Sir, second alert forces rotate.")
    rotated = Path(str(miss_ledger_path(store.path)) + ".1")
    assert rotated.is_file()


def test_read_miss_ledger_window_and_sort(tmp_path: Path) -> None:
    q = tmp_path / "queue.jsonl"
    ledger = miss_ledger_path(q)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    old_ts = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(now - 25 * 3600)
    )
    mid_ts = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(now - 3600)
    )
    new_ts = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(now - 60)
    )
    # deliberate out-of-order write + bad JSON line
    lines = [
        json.dumps(
            {"ts": new_ts, "id": "n", "kind": "new", "event": "enqueue", "reason": "ok"}
        ),
        json.dumps(
            {"ts": old_ts, "id": "o", "kind": "old", "event": "enqueue", "reason": "ok"}
        ),
        "NOT-JSON{{{",
        json.dumps(
            {"ts": mid_ts, "id": "m", "kind": "mid", "event": "enqueue", "reason": "ok"}
        ),
    ]
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    got = read_miss_ledger(q, hours=24.0, now=now)
    assert [e["id"] for e in got] == ["m", "n"]
    assert [e["ts"] for e in got] == [mid_ts, new_ts]


def test_read_miss_ledger_missing_file(tmp_path: Path) -> None:
    assert read_miss_ledger(tmp_path / "no_queue.jsonl") == []


def test_read_reads_rotated_file(tmp_path: Path) -> None:
    q = tmp_path / "queue.jsonl"
    ledger = miss_ledger_path(q)
    rotated = Path(str(ledger) + ".1")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    old_ts = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(now - 7200)
    )
    new_ts = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(now - 60)
    )
    rotated.write_text(
        json.dumps(
            {
                "ts": old_ts,
                "id": "old",
                "kind": "discord",
                "event": "enqueue",
                "reason": "ok",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    ledger.write_text(
        json.dumps(
            {
                "ts": new_ts,
                "id": "new",
                "kind": "whatsapp",
                "event": "hold",
                "reason": "ok",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    got = read_miss_ledger(q, hours=24.0, now=now)
    assert [e["id"] for e in got] == ["old", "new"]
    assert [e["ts"] for e in got] == [old_ts, new_ts]


def test_read_rejects_future_ts(tmp_path: Path) -> None:
    q = tmp_path / "queue.jsonl"
    ledger = miss_ledger_path(q)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    future_ts = time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.localtime(now + 3600)
    )
    ledger.write_text(
        json.dumps(
            {
                "ts": future_ts,
                "id": "f",
                "kind": "discord",
                "event": "enqueue",
                "reason": "ok",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert read_miss_ledger(q, hours=24.0, now=now) == []


def test_format_missed_sentence_empty() -> None:
    assert format_missed_sentence([]) == "Sir, nothing missed."


def test_format_missed_sentence_ascii_and_counts() -> None:
    entries = [
        {"id": "a", "kind": "self-monitor", "event": "enqueue"},
        {"id": "b", "kind": "self-monitor", "event": "hold"},
        {"id": "c", "kind": "警報", "event": "enqueue"},
        {"id": "d", "kind": "whatsapp", "event": "enqueue"},
        {"id": "e", "kind": "discord", "event": "enqueue"},
        {"id": "f", "kind": "cursor", "event": "enqueue"},
    ]
    sentence = format_missed_sentence(entries)
    assert sentence.isascii()
    assert "self monitor x2" in sentence
    assert "and others" in sentence
    assert sentence.startswith("Sir, 6 alerts went unanswered")


def test_sentence_counts_unanswered_ids_only() -> None:
    entries = [
        {"id": "spoken1", "kind": "discord", "event": "enqueue"},
        {"id": "spoken1", "kind": "discord", "event": "spoken"},
        {"id": "held1", "kind": "whatsapp", "event": "hold"},
        {"id": "drop1", "kind": "cursor", "event": "drop"},
    ]
    sentence = format_missed_sentence(entries)
    assert sentence.startswith("Sir, 2 alerts went unanswered")
    assert "5 alerts" not in sentence


def test_sentence_nothing_missed_when_all_spoken() -> None:
    entries = [
        {"id": "a", "kind": "discord", "event": "enqueue"},
        {"id": "a", "kind": "discord", "event": "spoken"},
        {"id": "b", "kind": "whatsapp", "event": "hold"},
        {"id": "b", "kind": "whatsapp", "event": "spoken"},
    ]
    assert format_missed_sentence(entries) == "Sir, nothing missed."


def test_sentence_labels_dedupe_after_sanitize() -> None:
    entries = [
        {"id": "1", "kind": "警報", "event": "enqueue"},
        {"id": "2", "kind": "警號", "event": "hold"},
    ]
    sentence = format_missed_sentence(entries)
    assert "alert x2" in sentence
    assert "alert x1, alert x1" not in sentence


def test_sentence_large_total_over_999() -> None:
    entries = [
        {"id": f"id{i}", "kind": "discord", "event": "enqueue"}
        for i in range(1000)
    ]
    sentence = format_missed_sentence(entries)
    assert "over 999" in sentence
    assert sentence.isascii()
    assert not re.search(r"\d{4}", sentence)


def test_label_strips_symbols() -> None:
    label = _label_for("a=b|c->d")
    for ch in "=|<>":
        assert ch not in label
    assert _label_for("警報") == "alert"
    assert _label_for("") == "alert"


def test_count_clause_over_999() -> None:
    entries = [
        {"id": f"id{i}", "kind": "whatsapp", "event": "enqueue"}
        for i in range(1000)
    ]
    sentence = format_missed_sentence(entries)
    assert "WhatsApp over 999" in sentence
    assert "xover 999" not in sentence
    assert sentence.isascii()


def test_route_what_did_i_miss() -> None:
    i = route("what did i miss", _reg())
    assert i.kind == "alert_miss"
    assert i.caption == "missed alerts"


def test_route_variants() -> None:
    hit = [
        "what did i miss",
        "What did I miss?",
        "did i miss anything",
        "did i miss any alerts",
        "what did i miss sir",
        "what did i miss today",
        "what have i missed",
        "jarvis what did i miss",
        "miss咗啲咩",
        "miss咗啲咩呀",
        "我miss左啲咩",
        "miss左乜",
    ]
    for phrase in hit:
        i = route(phrase, _reg())
        assert i.kind == "alert_miss", phrase
        assert i.caption == "missed alerts", phrase

    miss = [
        ("open minecraft", "open_profile"),
        ("what is a pickaxe", "query"),
        ("tell me a joke", None),  # unknown or query — just not alert_miss
        ("開 minecraft", "open_profile"),
    ]
    for phrase, expect in miss:
        i = route(phrase, _reg())
        assert i.kind != "alert_miss", phrase
        if expect is not None:
            assert i.kind == expect, (phrase, i.kind)


def test_engine_never_calls_hermes_on_miss(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _boom(*_a, **_k):
        raise AssertionError("hermes must not be called for alert_miss")

    monkeypatch.setattr("jarvis.engine._dispatch_hermes", _boom)
    monkeypatch.setattr(
        "jarvis.engine.load_settings",
        lambda: SimpleNamespace(hermes_enabled=True),
    )
    monkeypatch.setattr(
        "jarvis.alert_store.default_queue_path",
        lambda: tmp_path / "queue.jsonl",
    )
    result = execute_utterance("what did i miss", repair_asr=False)
    assert result.ok is True
    speak = [ln for ln in result.lines if ln.startswith("[speak] ")]
    assert speak
    spoken = speak[0][len("[speak] ") :]
    assert spoken.isascii()


def test_engine_caption_line_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "jarvis.engine.load_settings",
        lambda: SimpleNamespace(hermes_enabled=False),
    )
    monkeypatch.setattr(
        "jarvis.alert_store.default_queue_path",
        lambda: tmp_path / "queue.jsonl",
    )
    result = execute_utterance("what did i miss", repair_asr=False)
    assert result.ok is True
    caption = [ln for ln in result.lines if ln.startswith("[caption] ")]
    assert caption
    assert caption[0][len("[caption] ") :].isascii()


def test_engine_fail_open_neutral_sentence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise(*_a, **_k):
        raise RuntimeError("ledger boom")

    monkeypatch.setattr("jarvis.alert_store.read_miss_ledger", _raise)
    monkeypatch.setattr(
        "jarvis.engine.load_settings",
        lambda: SimpleNamespace(hermes_enabled=False),
    )
    result = execute_utterance("what did i miss", repair_asr=False)
    assert result.ok is True
    assert (
        "[speak] Sir, the alert ledger is unavailable." in result.lines
    )
