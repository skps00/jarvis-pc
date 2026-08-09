"""Unit tests for alert JSONL store."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from jarvis.alert_store import AlertStore


@pytest.fixture()
def store(tmp_path: Path) -> AlertStore:
    return AlertStore(tmp_path / "queue.jsonl", max_depth=4, default_ttl_s=60.0)


def test_enqueue_peek_ack(store: AlertStore) -> None:
    a = store.enqueue(kind="discord", phrase="Sir, Discord needs attention.")
    assert a.id
    got = store.peek(lease_s=10)
    assert got is not None
    assert got.id == a.id
    assert got.status == "leased"
    # second peek while leased → none
    assert store.peek(lease_s=10) is None
    assert store.ack(a.id) is True
    assert store.peek(lease_s=10) is None


def test_lease_expiry_redelivers(store: AlertStore) -> None:
    a = store.enqueue(kind="whatsapp", phrase="WhatsApp message, sir.")
    got = store.peek(lease_s=0.05)
    assert got and got.id == a.id
    time.sleep(0.08)
    again = store.peek(lease_s=10)
    assert again is not None
    assert again.id == a.id


def test_ttl_drops(tmp_path: Path) -> None:
    st = AlertStore(tmp_path / "q.jsonl", default_ttl_s=0.05)
    st.enqueue(kind="test", phrase="Alert system ready.")
    time.sleep(0.08)
    assert st.peek() is None
    assert st.stats()["open"] == 0


def test_max_depth_drops_oldest(store: AlertStore) -> None:
    ids = []
    for i in range(6):
        r = store.enqueue(kind="extra", phrase=f"Ping {i}.")
        ids.append(r.id)
    open_ids = {r.id for r in store.list_open()}
    assert len(open_ids) == 4
    assert ids[0] not in open_ids
    assert ids[1] not in open_ids
    assert ids[-1] in open_ids


def test_stats(store: AlertStore) -> None:
    store.enqueue(kind="discord", phrase="Sir, Discord needs attention.")
    store.peek(lease_s=30)
    s = store.stats()
    assert s["open"] == 1
    assert s["leased"] == 1
    assert s["pending"] == 0
