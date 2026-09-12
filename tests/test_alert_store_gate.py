"""AlertStore state-machine / gate-neutrality tests (temp dir only)."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path

import pytest

from jarvis import alert_policy
from jarvis.alert_store import (
    DEDUPE_WINDOW_S,
    HELD_CAP,
    AlertStore,
    StoredAlert,
    miss_ledger_path,
)


@pytest.fixture()
def qpath(tmp_path: Path) -> Path:
    return tmp_path / "queue.jsonl"


def _read_ledger(store: AlertStore) -> list[dict]:
    path = store._ledger_path
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def test_old_row_compatibility(qpath: Path) -> None:
    """Queue JSONL without new fields → pending/normal, empty dedupe_key."""
    old = {
        "id": "abc123",
        "kind": "discord",
        "phrase": "Sir, Discord needs attention.",
        "app": "",
        "detail": "",
        "ts": time.time(),
        "ttl_s": 120.0,
        "status": "pending",
        "lease_until": 0.0,
    }
    qpath.write_text(json.dumps(old) + "\n", encoding="utf-8")
    st = AlertStore(qpath)
    rows = st.list_open()
    assert len(rows) == 1
    r = rows[0]
    assert r.state == "pending"
    assert r.priority == "normal"
    assert r.dedupe_key == ""
    assert r.hold_until == 0.0


def test_peek_ignores_held_and_digest(qpath: Path) -> None:
    """Regression: store stays neutral — held/digest neither returned nor mutated."""
    st = AlertStore(qpath)
    a = st.enqueue(kind="discord", phrase="Pending one.")
    b = st.enqueue(kind="discord", phrase="Will hold.")
    c = st.enqueue(kind="discord", phrase="Will digest.")
    st.hold([b.id], ttl_s=60.0)
    st.mark_digest([c.id])
    # mutate fingerprints before peek
    before = {r.id: (r.state, r.lease_until, r.status) for r in _all(st)}
    got = st.peek(lease_s=10)
    assert got is not None
    assert got.id == a.id
    after = {r.id: (r.state, r.lease_until, r.status) for r in _all(st)}
    assert after[b.id] == before[b.id]
    assert after[c.id] == before[c.id]


def _all(st: AlertStore) -> list[StoredAlert]:
    with st.path.open(encoding="utf-8") as f:  # type: ignore[arg-type]
        return [
            StoredAlert.from_dict(json.loads(line))
            for line in f
            if line.strip()
        ]


def test_hold_release_roundtrip(qpath: Path) -> None:
    st = AlertStore(qpath)
    a = st.enqueue(kind="discord", phrase="Hold me.")
    assert st.hold([a.id], ttl_s=30.0) == 1
    assert st.peek(lease_s=10) is None
    assert st.release_held() == 1
    got = st.peek(lease_s=10)
    assert got is not None
    assert got.id == a.id


def test_expired_held_becomes_digest(qpath: Path) -> None:
    st = AlertStore(qpath)
    a = st.enqueue(kind="discord", phrase="Hold briefly.")
    past = time.time() - 100.0
    st.hold([a.id], ttl_s=1.0, now=past)  # hold_until already in the past
    row = StoredAlert.from_dict(
        json.loads(qpath.read_text(encoding="utf-8").strip())
    )
    assert row.expired(now=time.time()) is False
    # read path must not mutate; write op triggers held → digest
    st.list_open()
    assert _all(st)[0].state == "held"
    st.enqueue(kind="discord", phrase="Trigger GC.")
    rows = [r for r in _all(st) if r.id == a.id]
    assert len(rows) == 1
    assert rows[0].state == "digest"
    assert rows[0].expired(now=time.time()) is False
    reasons = [e["reason"] for e in _read_ledger(st) if e.get("event") == "digest"]
    assert "hold_timeout" in reasons


def test_mark_spoken_gc_and_digest_expiry(qpath: Path) -> None:
    st = AlertStore(qpath, default_ttl_s=60.0)
    a = st.enqueue(kind="discord", phrase="Spoken soon.")
    assert st.mark_spoken([a.id]) == 1
    rows = _all(st)
    assert len(rows) == 1
    assert rows[0].state == "spoken"
    # GC keeps spoken until default_ttl_s (read path does not drop)
    young = time.time()
    st.list_open()
    assert any(r.id == a.id for r in _all(st))
    # age the row past default_ttl_s; write op persists drop
    raw = json.loads(qpath.read_text(encoding="utf-8").strip())
    raw["ts"] = young - 60.0 - 1.0
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    st.enqueue(kind="discord", phrase="GC trigger spoken.")
    assert not any(r.id == a.id for r in _all(st))

    # digest survives until 24h from digest_at (not raw ts)
    b = st.enqueue(kind="discord", phrase="Digest me.")
    st.mark_digest([b.id])
    raw = json.loads(qpath.read_text(encoding="utf-8").strip().splitlines()[-1])
    # keep only the digest row for ageing
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    raw["ts"] = time.time() - (23 * 3600)
    raw["digest_at"] = time.time() - (23 * 3600)
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    st.enqueue(kind="discord", phrase="GC trigger digest young.")
    assert any(r.id == b.id for r in _all(st))
    raw = json.loads(
        next(line for line in qpath.read_text(encoding="utf-8").splitlines() if b.id in line)
    )
    raw["ts"] = time.time() - (25 * 3600)
    raw["digest_at"] = time.time() - (25 * 3600)
    # rewrite file with aged digest + drop the trigger row for a clean assert
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    st.enqueue(kind="discord", phrase="GC trigger digest old.")
    assert not any(r.id == b.id for r in _all(st))
    assert any(e.get("reason") == "digest_expired" for e in _read_ledger(st))


def test_eviction_protects_held_and_critical(qpath: Path) -> None:
    def policy(kind: str) -> str:
        return "critical" if kind == "crit" else "normal"

    st = AlertStore(qpath, max_depth=3, policy=policy)
    held = st.enqueue(kind="normal", phrase="Hold this.")
    st.hold([held.id], ttl_s=60.0)
    crit = st.enqueue(kind="crit", phrase="Critical alert.")
    # flood with normal pending past max_depth
    for i in range(6):
        st.enqueue(kind="normal", phrase=f"Ping {i}.")
    ids = {r.id: r for r in _all(st)}
    assert held.id in ids
    assert ids[held.id].state == "held"
    assert crit.id in ids
    assert ids[crit.id].priority == "critical"
    # only pending normals may be evicted; held+critical survive
    pending_normals = [
        r for r in ids.values() if r.state == "pending" and r.priority == "normal"
    ]
    assert len(pending_normals) <= 3


def test_held_cap_collapse(qpath: Path) -> None:
    st = AlertStore(qpath, max_depth=200)
    ids = []
    for i in range(70):
        r = st.enqueue(kind="discord", phrase=f"Hold {i}.", app="Discord")
        ids.append(r.id)
    n = st.hold(ids, ttl_s=60.0)
    assert n == 70
    held = [r for r in _all(st) if r.state == "held"]
    assert len(held) <= HELD_CAP
    # newest kept among collapsed group
    newest_id = ids[-1]
    assert any(r.id == newest_id and r.state == "held" for r in _all(st))
    reasons = {e.get("reason") for e in _read_ledger(st)}
    assert "held_cap" in reasons or "collapse" in reasons


def test_no_spin_when_all_held(qpath: Path) -> None:
    st = AlertStore(qpath, max_depth=4)
    ids = []
    for i in range(4):
        r = st.enqueue(kind="discord", phrase=f"H{i}.")
        ids.append(r.id)
    st.hold(ids, ttl_s=3600.0)
    t0 = time.perf_counter()
    # hold again (no eligible pending) + enforce cap with all held — must return fast
    n = st.hold(ids, ttl_s=3600.0)
    elapsed = time.perf_counter() - t0
    assert n == 0
    assert elapsed < 2.0


def test_dedupe_window(qpath: Path) -> None:
    st = AlertStore(qpath)
    st.enqueue(kind="discord", phrase="One.", dedupe_key="msg:1")
    st.enqueue(kind="discord", phrase="Two.", dedupe_key="msg:1")
    assert len(_all(st)) == 1
    assert any(e.get("reason") == "dedupe" for e in _read_ledger(st))
    # after window → two rows (inflate ttl so GC does not collect the aged row before dedupe)
    raw = json.loads(qpath.read_text(encoding="utf-8").strip())
    raw["ts"] = time.time() - DEDUPE_WINDOW_S - 1.0
    raw["ttl_s"] = DEDUPE_WINDOW_S * 10
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    ledger_n = len(_read_ledger(st))
    st.enqueue(kind="discord", phrase="Three.", dedupe_key="msg:1")
    assert len(_all(st)) == 2
    assert not any(e.get("reason") == "dedupe" for e in _read_ledger(st)[ledger_n:])

    # Contrast: original short ttl_s + same aged ts → GC drops the row first, so enqueue is not a dedupe.
    raw = json.loads(qpath.read_text(encoding="utf-8").splitlines()[0])
    raw["ts"] = time.time() - DEDUPE_WINDOW_S - 1.0
    raw["ttl_s"] = 120.0
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    ledger_n = len(_read_ledger(st))
    st.enqueue(kind="discord", phrase="Four.", dedupe_key="msg:1")
    assert len(_all(st)) == 1
    assert not any(e.get("reason") == "dedupe" for e in _read_ledger(st)[ledger_n:])


def test_ledger_fail_open(qpath: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    st = AlertStore(qpath)
    real_open = Path.open

    def bad_open(self: Path, *a: object, **k: object):  # noqa: ANN001
        if "miss_ledger" in str(self):
            raise OSError("disk full")
        return real_open(self, *a, **k)  # type: ignore[misc]

    monkeypatch.setattr(Path, "open", bad_open)
    a = st.enqueue(kind="discord", phrase="Still ok.")
    assert a.id
    assert st.hold([a.id], ttl_s=10.0) == 1
    assert st.release_held() == 1
    got = st.peek(lease_s=5)
    assert got and got.id == a.id
    assert st.mark_spoken([a.id]) == 1


def test_concurrency_enqueue_hold(qpath: Path) -> None:
    st1 = AlertStore(qpath, max_depth=100)
    st2 = AlertStore(qpath, max_depth=100)
    errors: list[BaseException] = []

    def enq() -> None:
        try:
            for i in range(20):
                st1.enqueue(kind="discord", phrase=f"E{i}.")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def hold_loop() -> None:
        try:
            for _ in range(20):
                open_ids = [r.id for r in st2.list_open()]
                if open_ids:
                    st2.hold(open_ids[:3], ttl_s=30.0)
                time.sleep(0.001)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    t1 = threading.Thread(target=enq)
    t2 = threading.Thread(target=hold_loop)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)
    assert not errors
    text = qpath.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        if line.strip():
            rows.append(json.loads(line))
    assert rows  # valid JSON, non-empty
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids))  # no duplicate id corruption


# --- F1–F10 regression (task 2-R2) ---


def test_f1_eviction_never_kills_new_row(qpath: Path) -> None:
    st = AlertStore(qpath, max_depth=4)
    # fill with 4 digest rows (protected from eviction)
    for i in range(4):
        r = st.enqueue(kind="discord", phrase=f"Dig {i}.")
        st.mark_digest([r.id])
    neu = st.enqueue(kind="discord", phrase="New normal.")
    ids = {r.id for r in _all(st)}
    assert neu.id in ids
    assert any(r.id == neu.id and r.state == "pending" for r in _all(st))
    # peek must be able to see it (digest ignored)
    got = st.peek(lease_s=5)
    assert got is not None and got.id == neu.id
    # second case: older normal present → old evicted, new kept
    qpath.write_text("", encoding="utf-8")
    st = AlertStore(qpath, max_depth=2)
    old = st.enqueue(kind="discord", phrase="Old.")
    time.sleep(0.02)
    mid = st.enqueue(kind="discord", phrase="Mid.")
    time.sleep(0.02)
    new = st.enqueue(kind="discord", phrase="New.")
    ids = {r.id for r in _all(st)}
    assert new.id in ids
    assert mid.id in ids
    assert old.id not in ids
    assert any(
        e.get("reason") == "evict" and e.get("id") == old.id for e in _read_ledger(st)
    )


def test_f2_collapse_spares_critical(qpath: Path) -> None:
    st = AlertStore(qpath, max_depth=200)
    crit_ids: list[str] = []
    norm_ids: list[str] = []
    # 10 critical + 70 normal → non-critical count exceeds HELD_CAP
    for i in range(10):
        r = st.enqueue(
            kind="discord",
            phrase=f"C{i}.",
            app="Discord",
            priority="critical",
        )
        crit_ids.append(r.id)
    for i in range(70):
        r = st.enqueue(
            kind="discord",
            phrase=f"N{i}.",
            app="Discord",
            priority="normal",
        )
        norm_ids.append(r.id)
    st.hold(crit_ids + norm_ids, ttl_s=60.0)
    rows = {r.id: r for r in _all(st)}
    for cid in crit_ids:
        assert rows[cid].state == "held"
        assert rows[cid].priority == "critical"
    demoted = [
        e
        for e in _read_ledger(st)
        if e.get("event") == "digest" and e.get("reason") in ("collapse", "held_cap")
    ]
    assert demoted  # cap enforcement ran
    demoted_ids = {e["id"] for e in demoted}
    assert demoted_ids.isdisjoint(set(crit_ids))
    assert demoted_ids <= set(norm_ids)
    held_normals = [
        r for r in rows.values() if r.state == "held" and r.priority == "normal"
    ]
    assert len(held_normals) <= HELD_CAP


def test_f3_policy_vocabulary_fail_safe(qpath: Path, caplog: pytest.LogCaptureFixture) -> None:
    st = AlertStore(qpath, max_depth=2, policy=alert_policy.policy_for)
    with caplog.at_level(logging.WARNING, logger="jarvis.alert_store"):
        hard = st.enqueue(kind="gpu_hard", phrase="Sir, GPU critical limit reached.")
    assert hard.priority == "critical"
    # fill with normals — critical survives eviction
    st.enqueue(kind="extra", phrase="N1.")
    st.enqueue(kind="extra", phrase="N2.")
    st.enqueue(kind="extra", phrase="N3.")
    assert any(r.id == hard.id and r.priority == "critical" for r in _all(st))

    caplog.clear()
    st2 = AlertStore(qpath.parent / "q2.jsonl", policy=lambda k: "speak_now")
    with caplog.at_level(logging.WARNING, logger="jarvis.alert_store"):
        r = st2.enqueue(kind="extra", phrase="Illegal vocab.")
    assert r.priority == "critical"
    assert any("illegal policy result" in rec.message for rec in caplog.records)

    caplog.clear()

    def boom(_k: str) -> str:
        raise RuntimeError("policy down")

    st3 = AlertStore(qpath.parent / "q3.jsonl", policy=boom)
    with caplog.at_level(logging.WARNING, logger="jarvis.alert_store"):
        r3 = st3.enqueue(kind="extra", phrase="Raises.")
    assert r3.priority == "critical"
    assert any("illegal policy result" in rec.message for rec in caplog.records)

    # adapter maps CRITICAL kinds without warning
    st4 = AlertStore(qpath.parent / "q4.jsonl", policy=alert_policy.priority_for)
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="jarvis.alert_store"):
        r4 = st4.enqueue(kind="gpu_hard", phrase="Via adapter.")
    assert r4.priority == "critical"
    assert not any("illegal policy result" in rec.message for rec in caplog.records)


def test_f4_peek_does_not_mutate_held(qpath: Path) -> None:
    st = AlertStore(qpath)
    a = st.enqueue(kind="discord", phrase="Hold briefly.")
    st.hold([a.id], ttl_s=0.5)
    time.sleep(0.6)
    before_ledger = len(_read_ledger(st))
    assert st.peek(lease_s=5) is None
    row = _all(st)[0]
    assert row.state == "held"
    assert not any(
        e.get("reason") == "hold_timeout" for e in _read_ledger(st)[before_ledger:]
    )
    st.enqueue(kind="discord", phrase="Write GC.")
    row = next(r for r in _all(st) if r.id == a.id)
    assert row.state == "digest"
    assert any(e.get("reason") == "hold_timeout" for e in _read_ledger(st))


def test_f5_dirlock_timeout_stale_and_atomic(qpath: Path) -> None:
    st = AlertStore(qpath, max_depth=50)
    # (a) lock path is a regular file → TimeoutError, no infinite spin
    lock = st._lock_path
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("not a dir", encoding="utf-8")
    t0 = time.perf_counter()
    with pytest.raises(TimeoutError):
        st.enqueue(kind="discord", phrase="Blocked.")
    # default lock timeout is 5s; allow small scheduling slack
    assert time.perf_counter() - t0 < 8.0
    lock.unlink(missing_ok=True)

    # (b) stale lock dir reclaimed
    lock.mkdir()
    old = time.time() - 120.0
    os.utime(lock, (old, old))
    r = st.enqueue(kind="discord", phrase="After stale.")
    assert r.id
    assert not lock.exists()

    # (c) two threads → valid JSON, no lost rows
    errors: list[BaseException] = []

    def writer(n: int) -> None:
        try:
            s = AlertStore(qpath, max_depth=200)
            for i in range(15):
                s.enqueue(kind="discord", phrase=f"T{n}-{i}.")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)
    assert not errors
    rows = [
        json.loads(line)
        for line in qpath.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) >= 30
    assert len({r["id"] for r in rows}) == len(rows)

    # (d) peek returns None (not exception) when lock times out
    lock.write_text("block", encoding="utf-8")
    assert st.peek(lease_s=1) is None
    lock.unlink(missing_ok=True)


def test_f6_ttl_expiry_ledger(qpath: Path) -> None:
    st = AlertStore(qpath, default_ttl_s=0.05)
    st.enqueue(kind="test", phrase="Expire me.")
    time.sleep(0.08)
    st.enqueue(kind="test", phrase="Trigger GC.")
    reasons = {(e.get("event"), e.get("reason")) for e in _read_ledger(st)}
    assert ("drop", "ttl_expired") in reasons


def test_f7_dedupe_returns_existing(qpath: Path) -> None:
    st = AlertStore(qpath)
    first = st.enqueue(kind="discord", phrase="One.", dedupe_key="msg:1")
    second = st.enqueue(kind="discord", phrase="Two.", dedupe_key="msg:1")
    assert second.id == first.id
    assert any(r.id == first.id for r in _all(st))
    # lease then ack by returned id
    got = st.peek(lease_s=5)
    assert got and got.id == first.id
    assert st.ack(second.id) is True
    assert _all(st) == []


def test_f8_digest_age_from_digest_at(qpath: Path) -> None:
    st = AlertStore(qpath)
    a = st.enqueue(kind="discord", phrase="Old ts.", ttl_s=3600.0)
    # age ts to 25h ago while still pending
    raw = json.loads(qpath.read_text(encoding="utf-8").strip())
    raw["ts"] = time.time() - (25 * 3600)
    raw["ttl_s"] = 3600.0 * 48  # still within ttl from... wait expired() uses ts
    # expired uses ts — inflate ttl so pending survives until hold
    raw["ttl_s"] = 25 * 3600 + 3600
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    st.hold([a.id], ttl_s=0.05)
    time.sleep(0.08)
    st.enqueue(kind="discord", phrase="GC to digest.")
    row = next(r for r in _all(st) if r.id == a.id)
    assert row.state == "digest"
    assert float(row.digest_at) > 0.0
    # not dropped in first GC pass despite ancient ts
    assert not any(
        e.get("id") == a.id and e.get("reason") == "digest_expired"
        for e in _read_ledger(st)
    )


def test_f9_spoken_gc_uses_default_ttl(qpath: Path) -> None:
    st = AlertStore(qpath, default_ttl_s=0.05)
    a = st.enqueue(kind="discord", phrase="Speak.")
    st.mark_spoken([a.id])
    time.sleep(0.2)
    st.enqueue(kind="discord", phrase="GC spoken.")
    assert not any(r.id == a.id for r in _all(st))
    assert any(e.get("reason") == "spoken_expired" for e in _read_ledger(st))


def test_f10_miss_ledger_follows_queue_path(qpath: Path, tmp_path: Path) -> None:
    custom = tmp_path / "custom_dir" / "q.jsonl"
    st = AlertStore(custom)
    assert st._ledger_path == miss_ledger_path(custom)
    assert st._ledger_path == custom.parent / "miss_ledger.jsonl"
    st.enqueue(kind="discord", phrase="Ledger here.")
    assert st._ledger_path.is_file()
    from jarvis.alert_store import default_queue_path

    default_ledger = miss_ledger_path(default_queue_path())
    assert st._ledger_path.resolve() != default_ledger.resolve() or (
        custom.parent.resolve() == default_ledger.parent.resolve()
    )


def test_read_path_lock_timeout_fast(qpath: Path) -> None:
    """Read paths return None/[] within ~2s when lock is held (READ_TIMEOUT_S)."""
    from jarvis.alert_store import READ_TIMEOUT_S

    st = AlertStore(qpath)
    lock = st._lock_path
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.mkdir()
    try:
        t0 = time.perf_counter()
        assert st.peek(lease_s=1) is None
        elapsed = time.perf_counter() - t0
        assert elapsed < 2.0
        assert elapsed >= READ_TIMEOUT_S * 0.5
        t1 = time.perf_counter()
        assert st.list_open() == []
        assert time.perf_counter() - t1 < 2.0
        t2 = time.perf_counter()
        assert st.digest_rows() == []
        assert time.perf_counter() - t2 < 2.0
        t3 = time.perf_counter()
        stats = st.stats()
        assert stats["open"] == 0
        assert time.perf_counter() - t3 < 2.0
    finally:
        try:
            lock.rmdir()
        except OSError:
            pass


def test_peek_never_deletes_expired_rows(qpath: Path) -> None:
    """peek must not silently drop rows; write op collects with ledger."""
    from jarvis.alert_store import DIGEST_MAX_AGE_S

    st = AlertStore(qpath)
    pending = st.enqueue(kind="discord", phrase="Expire pending.", ttl_s=0.05)
    digest = st.enqueue(kind="whatsapp", phrase="Expire digest.")
    st.mark_digest([digest.id])
    time.sleep(0.15)
    # Age digest past DIGEST_MAX_AGE_S
    lines = []
    for line in qpath.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d["id"] == digest.id:
            d["digest_at"] = time.time() - DIGEST_MAX_AGE_S - 10.0
            d["ts"] = d["digest_at"]
        lines.append(json.dumps(d))
    qpath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    for _ in range(3):
        assert st.peek(lease_s=5) is None

    ids = {r.id for r in _all(st)}
    assert pending.id in ids
    assert digest.id in ids
    expire_reasons = {
        e.get("reason")
        for e in _read_ledger(st)
        if e.get("reason") in ("ttl_expired", "digest_expired", "spoken_expired")
    }
    assert expire_reasons == set()

    # Read paths stay honest without writing
    q_mtime = qpath.stat().st_mtime
    led_path = st._ledger_path
    led_mtime = led_path.stat().st_mtime if led_path.is_file() else None
    assert st.list_open() == []
    assert st.digest_rows() == []
    states = st.stats()["states"]
    assert states.get("pending", 0) == 0
    assert states.get("digest", 0) == 0
    assert states.get("held", 0) == 0
    assert states.get("spoken", 0) == 0
    assert qpath.stat().st_mtime == q_mtime
    if led_mtime is not None:
        assert led_path.stat().st_mtime == led_mtime

    # Next write op collects with ledger reasons
    st.gc()
    ids_after = {r.id for r in _all(st)}
    assert pending.id not in ids_after
    assert digest.id not in ids_after
    reasons = {e.get("reason") for e in _read_ledger(st)}
    assert "ttl_expired" in reasons
    assert "digest_expired" in reasons


def test_expired_held_not_visible_on_read(qpath: Path) -> None:
    """Held past hold_until excluded from list_open/digest_rows (no write)."""
    st = AlertStore(qpath)
    a = st.enqueue(kind="discord", phrase="Hold briefly.")
    past = time.time() - 100.0
    st.hold([a.id], ttl_s=1.0, now=past)
    q_mtime = qpath.stat().st_mtime
    assert st.list_open() == []
    assert st.digest_rows() == []
    assert st.stats()["states"].get("held", 0) == 0
    assert qpath.stat().st_mtime == q_mtime
    # Still held on disk until write op
    assert _all(st)[0].state == "held"


def test_release_refreshes_lifetime(qpath: Path) -> None:
    """release_held refreshes ts so aged held rows do not evaporate."""
    st = AlertStore(qpath)
    a = st.enqueue(kind="discord", phrase="Hold then release.", ttl_s=1)
    assert st.hold([a.id], ttl_s=900) == 1
    raw = json.loads(qpath.read_text(encoding="utf-8").strip())
    raw["ts"] = time.time() - 2.0
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    assert st.release_held() == 1
    open_rows = st.list_open()
    assert len(open_rows) == 1
    assert open_rows[0].id == a.id
    assert not any(
        e.get("event") == "drop" and e.get("reason") == "ttl_expired"
        for e in _read_ledger(st)
    )
    got = st.peek(lease_s=10)
    assert got is not None
    assert got.id == a.id


def test_stats_has_dropped_24h(qpath: Path) -> None:
    st = AlertStore(qpath)
    assert st.stats()["dropped_24h"] == 0
    a = st.enqueue(kind="discord", phrase="Drop me.")
    st.drop([a.id], "test")
    assert st.stats()["dropped_24h"] == 1


def test_gc_noop_does_not_rewrite(qpath: Path) -> None:
    """gc() with no deadline transitions must not rewrite queue bytes."""
    st = AlertStore(qpath)
    st.enqueue(kind="discord", phrase="Young pending.")
    before = qpath.read_bytes()
    st.gc()
    assert qpath.read_bytes() == before

    # Aged pending past ttl → gc writes (bytes change)
    raw = json.loads(qpath.read_text(encoding="utf-8").strip())
    raw["ts"] = time.time() - 10_000.0
    raw["ttl_s"] = 60.0
    qpath.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    aged = qpath.read_bytes()
    st.gc()
    assert qpath.read_bytes() != aged
    assert qpath.read_text(encoding="utf-8").strip() == ""
