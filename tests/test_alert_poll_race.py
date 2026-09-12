"""Poll-loop enforce gate + lease race (temp dirs only; never live queue)."""

from __future__ import annotations

import importlib.util
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis import alert_dispatch
from jarvis.alert_store import AlertStore, StoredAlert

_POLL = Path(__file__).resolve().parents[1] / "scripts" / "hermes_alert_poll_loop.py"


def _load_poll():
    spec = importlib.util.spec_from_file_location("hermes_alert_poll_loop", _POLL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _gaming_snap(**overrides) -> dict:
    base = {
        "timestamp": _now_iso(),
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
    base.update(overrides)
    return base


def _idle_snap(**overrides) -> dict:
    return _gaming_snap(apps=[], idle_seconds=300, **overrides)


_SETTINGS = SimpleNamespace(
    alert_policy_mode="enforce",
    alert_gaming="hold",
    alert_hold_ttl_s=900,
    alert_digest_interval_s=1800,
    alert_voice=True,
    alert_discord=True,
    alert_whatsapp=True,
    alert_cursor=True,
)


@pytest.fixture()
def poll_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    q = tmp_path / "queue.jsonl"
    store = AlertStore(q)
    poll = _load_poll()
    monkeypatch.setattr(
        "jarvis.alert_store.default_queue_path",
        lambda: q,
    )
    monkeypatch.setattr(
        "jarvis.alert_shadow.shadow_ledger_path",
        lambda: tmp_path / "shadow_ledger.jsonl",
    )
    monkeypatch.setattr(
        "jarvis.alert_shadow.heartbeat_path",
        lambda: tmp_path / "shadow_heartbeat.jsonl",
    )
    monkeypatch.setattr(
        "jarvis.alert_shadow._marker_path",
        lambda: tmp_path / "shadow_heartbeat.marker",
    )
    state = {"quiet_since": None, "was_busy": False}
    return SimpleNamespace(
        path=tmp_path,
        queue=q,
        store=store,
        poll=poll,
        state=state,
    )


def _all(store: AlertStore) -> list[StoredAlert]:
    if not store.path.is_file():
        return []
    return [
        StoredAlert.from_dict(json.loads(line))
        for line in store.path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _settings(**overrides) -> SimpleNamespace:
    d = dict(_SETTINGS.__dict__)
    d.update(overrides)
    return SimpleNamespace(**d)


def test_enforce_critical_penetrates_gaming(poll_env) -> None:
    env = poll_env
    spoken: list[str] = []
    row = env.store.enqueue(
        kind="gpu_hard",
        phrase="Sir, GPU critical limit reached.",
        priority="critical",
    )
    env.poll.tick(
        env.store,
        settings=_settings(),
        speak=lambda p: spoken.append(p) or True,
        activity=_gaming_snap(),
        state=env.state,
        now=time.time(),
    )
    assert spoken
    assert "=" not in spoken[0]
    rows = _all(env.store)
    # acked → removed; or spoken state if claim kept then acked
    assert not any(r.id == row.id and r.state == "pending" for r in rows)
    assert not any(r.id == row.id and r.state == "held" for r in rows)


def test_enforce_whatsapp_held_then_release(poll_env) -> None:
    env = poll_env
    spoken: list[str] = []
    row = env.store.enqueue(kind="whatsapp", phrase="WhatsApp has a new message.")
    t0 = 1_700_000_000.0
    env.poll.tick(
        env.store,
        settings=_settings(),
        speak=lambda p: spoken.append(p) or True,
        activity=_gaming_snap(),
        state=env.state,
        now=t0,
    )
    assert spoken == []
    assert any(r.id == row.id and r.state == "held" for r in _all(env.store))

    # Quiet window: tick-by-tick (interval=1s); 3 ticks still held; ≥180s releases.
    interval = 1.0
    now = t0 + 1.0
    for _ in range(3):
        n = env.poll.maybe_release_held(
            env.store, env.state, activity=_idle_snap(), now=now
        )
        assert n == 0
        assert any(r.id == row.id and r.state == "held" for r in _all(env.store))
        now += interval
    n = env.poll.maybe_release_held(
        env.store, env.state, activity=_idle_snap(), now=t0 + 1.0 + 180.0
    )
    assert n >= 1
    assert any(r.id == row.id and r.state == "pending" for r in _all(env.store))


def test_format_digest_sentence_kinds() -> None:
    poll = _load_poll()
    fmt = poll.format_digest_sentence
    assert (
        fmt({"whatsapp": 3, "discord": 2})
        == "Sir, 3 WhatsApp notifications and 2 Discord notifications while you were away."
    )
    assert fmt({"whatsapp": 1}) == "Sir, 1 WhatsApp notification while you were away."
    assert fmt({"discord": 1}) == "Sir, 1 Discord notification while you were away."
    assert (
        fmt({"discord": 1, "extra": 1, "gpu_health": 1, "whatsapp": 1})
        == "Sir, 1 Discord notification, 1 GPU health warning and 1 notification and other notifications while you were away."
    )
    assert (
        fmt({"whatsapp": 1200})
        == "Sir, over 999 WhatsApp notifications while you were away."
    )
    assert fmt({}) is None


def test_enforce_digest_flush_sentence(poll_env) -> None:
    env = poll_env
    spoken: list[str] = []
    env.store.enqueue(kind="whatsapp", phrase="WhatsApp has a new message.")
    env.store.enqueue(kind="discord", phrase="Sir, Discord ping.")
    t0 = 1_700_000_000.0
    # Not gaming → digest (one row per tick)
    for i in range(2):
        env.poll.tick(
            env.store,
            settings=_settings(alert_digest_interval_s=60),
            speak=lambda p: spoken.append(p) or True,
            activity=_idle_snap(),
            state=env.state,
            now=t0 + i,
        )
    assert spoken == []
    digest = [r for r in _all(env.store) if r.state == "digest"]
    assert len(digest) >= 2

    # Age digest_at so flush triggers
    lines = []
    for line in env.queue.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("state") == "digest":
            d["digest_at"] = t0 - 120.0
        lines.append(json.dumps(d))
    env.queue.write_text("\n".join(lines) + "\n", encoding="utf-8")

    env.poll.tick(
        env.store,
        settings=_settings(alert_digest_interval_s=60),
        speak=lambda p: spoken.append(p) or True,
        activity=_idle_snap(),
        state=env.state,
        now=t0 + 1.0,
    )
    assert len(spoken) == 1
    assert (
        spoken[0]
        == "Sir, 1 Discord notification and 1 WhatsApp notification while you were away."
    )
    assert spoken[0].isascii()
    assert "=" not in spoken[0]
    assert not any(r.state == "digest" for r in _all(env.store))
    ledger = env.store._ledger_path
    assert ledger.is_file()
    assert any(
        json.loads(ln).get("reason") == "digest_flush"
        for ln in ledger.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    )


def test_digest_dedupe_merges_identical_whatsapp(poll_env) -> None:
    """Same kind+dedupe_key → one row (intended); digest count stays 1."""
    env = poll_env
    spoken: list[str] = []
    a = env.store.enqueue(
        kind="whatsapp",
        phrase="WhatsApp has a new message.",
        dedupe_key="wa-same",
    )
    b = env.store.enqueue(
        kind="whatsapp",
        phrase="WhatsApp has a new message.",
        dedupe_key="wa-same",
    )
    assert a.id == b.id
    t0 = 1_700_000_000.0
    env.poll.tick(
        env.store,
        settings=_settings(alert_digest_interval_s=60),
        speak=lambda p: spoken.append(p) or True,
        activity=_idle_snap(),
        state=env.state,
        now=t0,
    )
    assert spoken == []
    digest = [r for r in _all(env.store) if r.state == "digest"]
    assert len(digest) == 1
    assert digest[0].kind == "whatsapp"

    lines = []
    for line in env.queue.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("state") == "digest":
            d["digest_at"] = t0 - 120.0
        lines.append(json.dumps(d))
    env.queue.write_text("\n".join(lines) + "\n", encoding="utf-8")

    env.poll.tick(
        env.store,
        settings=_settings(alert_digest_interval_s=60),
        speak=lambda p: spoken.append(p) or True,
        activity=_idle_snap(),
        state=env.state,
        now=t0 + 1.0,
    )
    assert len(spoken) == 1
    assert spoken[0] == "Sir, 1 WhatsApp notification while you were away."
    assert not any(r.state == "digest" for r in _all(env.store))


def test_poisoned_metrics_shaped_or_dropped(poll_env) -> None:
    env = poll_env
    spoken: list[str] = []
    row = env.store.enqueue(
        kind="self-monitor",
        phrase="thr=0.65->0.70",
        detail="fires=1|fp=0|err=0|thr=0.65->0.70",
    )
    env.poll.tick(
        env.store,
        settings=_settings(),
        speak=lambda p: spoken.append(p) or True,
        activity=_idle_snap(),
        state=env.state,
        now=time.time(),
    )
    if spoken:
        assert "=" not in spoken[0]
        assert "->" not in spoken[0]
        assert spoken[0].isascii()
    else:
        assert not any(r.id == row.id for r in _all(env.store))
        reasons = [
            json.loads(ln).get("reason")
            for ln in env.store._ledger_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert any(r in {"metric", "cjk", "url", "empty", "not_speakable"} for r in reasons)


def test_choke_drop_uses_real_reason(poll_env, monkeypatch: pytest.MonkeyPatch) -> None:
    """patched on the shared dispatch module (FIX5 moved prepare_phrase there)"""
    env = poll_env
    monkeypatch.setattr(alert_dispatch, "prepare_phrase", lambda _row: (None, "metric"))
    row = env.store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    ok = env.poll._speak_choked(
        env.store,
        row,
        speak=lambda _p: True,
        claim=False,
    )
    assert ok is False
    assert not any(r.id == row.id for r in _all(env.store))
    reasons = [
        json.loads(ln).get("reason")
        for ln in env.store._ledger_path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and json.loads(ln).get("id") == row.id
    ]
    assert "metric" in reasons
    assert "not_speakable" not in reasons


def test_lease_blocks_double_speak(poll_env) -> None:
    env = poll_env
    env.store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    barrier = threading.Barrier(2)
    results: list[object] = []

    def slow_speak(p: str) -> bool:
        barrier.wait(timeout=5)
        time.sleep(1.5)
        return True

    def worker() -> None:
        env.poll.tick(
            env.store,
            settings=_settings(alert_policy_mode="off"),
            speak=slow_speak,
            activity=_idle_snap(),
            state={"quiet_since": None, "was_busy": False},
            interval=1.0,
        )

    t1 = threading.Thread(target=worker)
    t1.start()
    barrier.wait(timeout=5)
    # During speech, second peek must see lease
    got = env.store.peek(lease_s=300.0)
    results.append(got)
    t1.join(timeout=10)
    assert results[0] is None


def test_mode_off_no_shadow_no_transitions(poll_env) -> None:
    env = poll_env
    spoken: list[str] = []
    row = env.store.enqueue(kind="discord", phrase="Sir, ping.")
    env.poll.tick(
        env.store,
        settings=_settings(alert_policy_mode="off"),
        speak=lambda p: spoken.append(p) or True,
        activity=_gaming_snap(),
        state=env.state,
        now=time.time(),
    )
    assert spoken == ["Sir, ping."]
    assert not (env.path / "shadow_ledger.jsonl").exists()
    assert not (env.path / "shadow_heartbeat.jsonl").exists()
    # acked → gone; no held/digest
    assert not any(r.id == row.id for r in _all(env.store))


def test_tts_failure_keeps_pending(poll_env) -> None:
    env = poll_env
    row = env.store.enqueue(kind="test", phrase="Sir, this is a test alert.")

    def boom(_p: str) -> bool:
        raise RuntimeError("tts down")

    env.poll.tick(
        env.store,
        settings=_settings(),
        speak=boom,
        activity=_idle_snap(),
        state=env.state,
        now=time.time(),
    )
    rows = _all(env.store)
    assert any(r.id == row.id and r.state == "pending" for r in rows)


def test_tick_injected_clock_keeps_digest(poll_env) -> None:
    """Full tick(now=injected) must not wall-clock-GC a young digest row."""
    from jarvis.alert_store import DIGEST_MAX_AGE_S

    env = poll_env
    spoken: list[str] = []
    row = env.store.enqueue(kind="discord", phrase="Sir, Discord ping.")
    env.store.mark_digest([row.id])
    t0 = 1_700_000_000.0
    # digest_at near injected clock (young); wall clock is years later
    raw = json.loads(env.queue.read_text(encoding="utf-8").strip())
    raw["digest_at"] = t0 - 60.0
    raw["ts"] = t0 - 60.0
    # Ensure wall-clock age would look ancient if GC mixed clocks wrongly
    assert (time.time() - raw["digest_at"]) > DIGEST_MAX_AGE_S
    env.queue.write_text(json.dumps(raw) + "\n", encoding="utf-8")

    env.poll.tick(
        env.store,
        settings=_settings(alert_digest_interval_s=3600),
        speak=lambda p: spoken.append(p) or True,
        activity=_idle_snap(),
        state=env.state,
        now=t0,
    )
    assert spoken == []
    digests = [r for r in _all(env.store) if r.id == row.id]
    assert len(digests) == 1
    assert digests[0].state == "digest"


def _age_digest(queue: Path, t0: float, age_s: float = 120.0) -> None:
    lines = []
    for line in queue.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("state") == "digest":
            d["digest_at"] = t0 - age_s
        lines.append(json.dumps(d))
    queue.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_digest_flush_speak_failure_keeps_digest(poll_env) -> None:
    """speak_fn False → rows stay digest so next interval can retry."""
    env = poll_env
    row = env.store.enqueue(kind="whatsapp", phrase="WhatsApp has a new message.")
    env.store.mark_digest([row.id])
    t0 = 1_700_000_000.0
    _age_digest(env.queue, t0)
    spoken: list[str] = []

    out = env.poll.maybe_flush_digest(
        env.store,
        env.state,
        _settings(alert_digest_interval_s=60),
        speak=lambda p: spoken.append(p) or False,
        activity=_idle_snap(),
        now=t0,
    )
    assert out is None
    assert spoken  # attempted once
    assert any(r.id == row.id for r in env.store.digest_rows(now=t0))


def test_digest_flush_clear_failure_no_respeak(
    poll_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """clear_digest TimeoutError → still only one speak across two ticks."""
    env = poll_env
    env.store.enqueue(kind="whatsapp", phrase="WhatsApp has a new message.")
    env.store.enqueue(kind="discord", phrase="Sir, Discord ping.")
    t0 = 1_700_000_000.0
    for i, r in enumerate(_all(env.store)):
        env.store.mark_digest([r.id], now=t0 + i)
    _age_digest(env.queue, t0)

    def boom(*_a, **_k):
        raise TimeoutError("lock busy")

    monkeypatch.setattr(env.store, "clear_digest", boom)
    spoken: list[str] = []

    def speak_ok(p: str) -> bool:
        spoken.append(p)
        return True

    cfg = _settings(alert_digest_interval_s=60)
    env.poll.maybe_flush_digest(
        env.store,
        env.state,
        cfg,
        speak=speak_ok,
        activity=_idle_snap(),
        now=t0,
    )
    env.poll.maybe_flush_digest(
        env.store,
        env.state,
        cfg,
        speak=speak_ok,
        activity=_idle_snap(),
        now=t0 + 1.0,
    )
    assert len(spoken) == 1
    assert env.store.digest_rows(now=t0 + 1.0) == []


def test_mark_spoken_refreshes_ts_survives_gc(poll_env) -> None:
    """Near-ttl row → mark_spoken refreshes ts; gc past old age keeps spoken."""
    env = poll_env
    ttl = 60.0
    store = AlertStore(env.queue, default_ttl_s=ttl)
    row = store.enqueue(kind="test", phrase="Sir, this is a test alert.")
    now = time.time()
    raw = json.loads(env.queue.read_text(encoding="utf-8").strip())
    # Age near ttl but still pending-valid so GC inside mark_spoken keeps it.
    old_ts = now - (ttl - 5.0)
    raw["ts"] = old_ts
    env.queue.write_text(json.dumps(raw) + "\n", encoding="utf-8")

    n = store.mark_spoken([row.id])
    assert n == 1
    assert store.stats()["states"]["spoken"] >= 1
    spoken_rows = [r for r in _all(store) if r.id == row.id and r.state == "spoken"]
    assert len(spoken_rows) == 1
    assert spoken_rows[0].ts >= now - 1.0
    # Old ts + 15s would be spoken_expired; refreshed ts survives.
    store.gc(now=now + 15.0)
    assert any(r.id == row.id and r.state == "spoken" for r in _all(store))
    assert (now + 15.0 - old_ts) > ttl


def test_release_convergence_one_normal_plus_critical(poll_env) -> None:
    """Quiet release: all critical + newest normal only; rest stay held."""
    env = poll_env
    t0 = 1_700_000_000.0
    normals = []
    for i in range(6):
        r = env.store.enqueue(
            kind="whatsapp",
            phrase=f"WhatsApp has a new message {i}.",
            priority="normal",
        )
        normals.append(r)
    crits = []
    for i in range(2):
        r = env.store.enqueue(
            kind="gpu_hard",
            phrase=f"Sir, GPU critical {i}.",
            priority="critical",
        )
        crits.append(r)
    # Stamp distinct ts (newest normal = last of the 6).
    lines = []
    by_id = {r.id: r for r in normals + crits}
    for idx, line in enumerate(env.queue.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        d = json.loads(line)
        if d["id"] in {r.id for r in normals}:
            d["ts"] = t0 + float(normals.index(by_id[d["id"]]))
        else:
            d["ts"] = t0 + 100.0 + float(crits.index(by_id[d["id"]]))
        lines.append(json.dumps(d))
    env.queue.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ids = [r.id for r in normals + crits]
    assert env.store.hold(ids, ttl_s=900, now=t0) == 8
    env.state["quiet_since"] = t0
    n = env.poll.maybe_release_held(
        env.store, env.state, activity=_idle_snap(), now=t0 + 180.0
    )
    assert n == 3
    rows = _all(env.store)
    pending = [r for r in rows if r.state == "pending"]
    held = [r for r in rows if r.state == "held"]
    assert len(pending) == 3
    assert len(held) == 5
    pending_ids = {r.id for r in pending}
    assert {r.id for r in crits} <= pending_ids
    newest_normal = normals[-1]
    assert newest_normal.id in pending_ids
    assert {r.id for r in normals[:-1]} == {r.id for r in held}


def test_release_quiet_window_resets_after_success(poll_env) -> None:
    """After a successful release, quiet_since resets — no wash on every tick."""
    env = poll_env
    t0 = 1_700_000_000.0
    normals = []
    for i in range(5):
        normals.append(
            env.store.enqueue(
                kind="whatsapp",
                phrase=f"WhatsApp has a new message {i}.",
                priority="normal",
            )
        )
    crits = []
    for i in range(2):
        crits.append(
            env.store.enqueue(
                kind="gpu_hard",
                phrase=f"Sir, GPU critical {i}.",
                priority="critical",
            )
        )
    lines = []
    by_id = {r.id: r for r in normals + crits}
    for line in env.queue.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d["id"] in {r.id for r in normals}:
            d["ts"] = t0 + float(normals.index(by_id[d["id"]]))
        else:
            d["ts"] = t0 + 100.0 + float(crits.index(by_id[d["id"]]))
        lines.append(json.dumps(d))
    env.queue.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert env.store.hold([r.id for r in normals + crits], ttl_s=900, now=t0) == 7
    env.state["quiet_since"] = t0
    released_ns = []
    now = t0 + 180.0
    for _ in range(5):
        n = env.poll.maybe_release_held(
            env.store, env.state, activity=_idle_snap(), now=now
        )
        released_ns.append(n)
        now += 5.0
    assert released_ns[0] != 0
    assert all(n == 0 for n in released_ns[1:])
    assert sum(released_ns) == 3
    held = [r for r in _all(env.store) if r.state == "held"]
    assert len(held) == 4


def test_release_noop_warn_rate_limited(
    poll_env, capsys: pytest.CaptureFixture[str]
) -> None:
    """Five quiet ticks with no held → at most one noop warn."""
    env = poll_env
    t0 = 1_700_000_000.0
    env.state["quiet_since"] = t0
    for i in range(5):
        env.poll.maybe_release_held(
            env.store,
            env.state,
            activity=_idle_snap(),
            now=t0 + 180.0 + i * 10.0,
        )
    out = capsys.readouterr().out
    assert out.count("[warn] release_held noop") <= 1


def test_mode_off_clears_held_and_digest(poll_env) -> None:
    """mode=off converges zombie held/digest without shadow writes."""
    env = poll_env
    spoken: list[str] = []
    held_row = env.store.enqueue(kind="whatsapp", phrase="WhatsApp has a new message.")
    dig_row = env.store.enqueue(kind="discord", phrase="Sir, Discord ping.")
    t0 = time.time()
    env.store.hold([held_row.id], ttl_s=900, now=t0)
    env.store.mark_digest([dig_row.id], now=t0)
    assert env.store.stats()["states"]["held"] >= 1
    assert env.store.stats()["states"]["digest"] >= 1
    for i in range(2):
        env.poll.tick(
            env.store,
            settings=_settings(alert_policy_mode="off"),
            speak=lambda p: spoken.append(p) or True,
            activity=_idle_snap(),
            state=env.state,
            now=t0 + i,
        )
    st = env.store.stats()["states"]
    assert st.get("held", 0) == 0
    assert st.get("digest", 0) == 0
    assert not (env.path / "shadow_ledger.jsonl").exists()
    assert spoken  # digest and/or released pending spoken

