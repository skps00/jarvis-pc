#!/usr/bin/env python3
"""Tight poll (~1s): peek → Hermes TTS → ack. Meets <3s better than cron.

Hermes cron min interval is 1 minute and gateway ticks ~60s — too slow for alerts.
Run this alongside ``jarvis-mcp`` / ``jarvis serve``.
Override: ``JARVIS_ALERT_POLL_S`` (default 1).
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_once = _HERE / "hermes_alert_speak_once.py"
_spec = importlib.util.spec_from_file_location("hermes_alert_speak_once", _once)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
_speak_hermes = _mod._speak_hermes

from jarvis.alert_dispatch import enforce  # noqa: E402
from jarvis.alert_store import label_for  # noqa: E402

RELEASE_QUIET_S = 180.0
_DIGEST_FAIL_LOG_TS = 0.0


def _log_digest_fail(msg: str = "[fail] digest flush speak") -> None:
    """Rate-limit digest speak-fail logs to once per 60s."""
    global _DIGEST_FAIL_LOG_TS
    wall = time.time()
    if wall - _DIGEST_FAIL_LOG_TS >= 60.0:
        _DIGEST_FAIL_LOG_TS = wall
        print(msg, flush=True)


def plan_for(
    row: Any,
    mode: str,
    *,
    activity: dict | None = None,
    settings: Any | None = None,
):
    """Compute SpeakPlan for a peeked row (enforce/shadow only; off returns early)."""
    from jarvis.speak_gate import should_speak

    return should_speak(row, activity=activity, settings=settings)


def _digest_label(kind: str) -> str:
    """Map kind → speakable label (single source: alert_store.label_for)."""
    return label_for(kind)


def _digest_clause(kind: str, n: int) -> str:
    """One count+label clause with singular/plural + ≤3-digit count."""
    from jarvis.alert_policy import _fmt_count, _plural

    label = _digest_label(kind)
    count_s = _fmt_count(n)
    # Bare proper-name labels get "notification(s)"; multi-word / "notification"
    # labels already carry the noun — pluralize the final word only.
    if " " not in label and label != "notification":
        noun = _plural(n, "notification", "notifications")
        return f"{count_s} {label} {noun}"
    if " " in label:
        head, last = label.rsplit(" ", 1)
        return f"{count_s} {head} {_plural(n, last, last + 's')}"
    return f"{count_s} {_plural(n, label, label + 's')}"


def format_digest_sentence(counts: dict[str, int]) -> str | None:
    """Deterministic digest TTS from kind→count map. Pure ASCII; no LLM."""
    ranked = sorted(
        ((str(k), int(n)) for k, n in (counts or {}).items() if int(n) > 0),
        key=lambda kv: (-kv[1], kv[0]),
    )
    if not ranked:
        return None
    # Select top 3: count desc, kind asc. Emit: count desc, label asc
    # (golden lists Discord, GPU health warning, notification — label order).
    top = sorted(ranked[:3], key=lambda kv: (-kv[1], _digest_label(kv[0])))
    clauses = [_digest_clause(kind, n) for kind, n in top]
    extra = len(ranked) > 3
    if len(clauses) == 1:
        body = clauses[0]
    elif len(clauses) == 2:
        body = f"{clauses[0]} and {clauses[1]}"
    else:
        # no Oxford comma
        body = f"{clauses[0]}, {clauses[1]} and {clauses[2]}"
    if extra:
        body = f"{body} and other notifications"
    return f"Sir, {body} while you were away."


def _busy(*, activity: dict | None = None) -> tuple[bool, bool, bool]:
    """Return ``(busy, gaming, in_call)``."""
    from jarvis import activity as activity_mod
    from jarvis.speak_gate import is_gaming_v2

    gaming = bool(is_gaming_v2(activity))
    if activity is not None:
        in_call = bool(activity.get("voice_call", False))
    else:
        in_call = bool(activity_mod.voice_call())
    return (gaming or in_call), gaming, in_call


def maybe_release_held(
    store: Any,
    state: dict[str, Any],
    *,
    activity: dict | None = None,
    now: float | None = None,
) -> int:
    """Release held rows after quiet (non-gaming, non-call) flap window.

    Convergence: all held ``priority==critical`` plus the single newest
    non-critical held row. Remainder stay held until hold_until → digest.
    """
    t = time.time() if now is None else float(now)
    busy, _g, _c = _busy(activity=activity)
    if busy:
        state["quiet_since"] = None
        return 0
    if state.get("quiet_since") is None:
        state["quiet_since"] = t
    quiet_ok = (t - float(state["quiet_since"])) >= RELEASE_QUIET_S
    if not quiet_ok:
        return 0
    held_fn = getattr(store, "held_rows", None)
    if callable(held_fn):
        held = list(held_fn(now=t) or [])
    else:
        held = []
    crit = [
        r
        for r in held
        if str(getattr(r, "priority", "") or "") == "critical"
    ]
    normals = [
        r
        for r in held
        if str(getattr(r, "priority", "") or "") != "critical"
    ]
    newest = (
        max(normals, key=lambda r: float(getattr(r, "ts", 0) or 0))
        if normals
        else None
    )
    candidates: list[str] = [str(r.id) for r in crit]
    nn = 0
    if newest is not None:
        candidates.append(str(newest.id))
        nn = 1
    nc = len(crit)
    if not candidates:
        if (t - float(state.get("last_release_warn", 0.0) or 0.0)) >= 60.0:
            print("[warn] release_held noop", flush=True)
            state["last_release_warn"] = t
        return 0
    n = int(store.release_held(ids=candidates, now=t) or 0)
    if n == 0:
        if (t - float(state.get("last_release_warn", 0.0) or 0.0)) >= 60.0:
            print("[warn] release_held noop", flush=True)
            state["last_release_warn"] = t
        return 0
    # Reset quiet window so next release waits a full quiet period again.
    state["quiet_since"] = t
    print(f"[ok] release_held n={n} (critical={nc}, newest={nn})", flush=True)
    return n


def _flush_digest_common(
    store: Any,
    *,
    speak=None,
    now: float | None = None,
) -> str | None:
    """Claim + speak all current digest rows once (shared by gated / immediate flush)."""
    from jarvis.alert_policy import is_speakable

    speak_fn = _speak_hermes if speak is None else speak
    t = time.time() if now is None else float(now)
    rows = list(store.digest_rows(now=t) or [])
    if not rows:
        return None
    counts: Counter[str] = Counter()
    for r in rows:
        k = str(getattr(r, "kind", "") or "alert").strip() or "alert"
        counts[k] += 1
    sentence = format_digest_sentence(dict(counts))
    if not sentence:
        return None
    if not is_speakable(sentence):
        sentence = "Sir, you have new alerts while you were away."
    ids = [str(r.id) for r in rows]
    # Claim first so a clear_digest lock failure cannot leave rows in digest
    # (would re-speak the same sentence next interval/transition).
    taken = int(store.mark_spoken(ids, now=t) or 0)
    if taken == 0:
        return None
    fail_reason = "tts"
    try:
        ok = bool(speak_fn(sentence))
    except Exception as exc:  # noqa: BLE001
        ok = False
        fail_reason = str(exc)[:80] or "tts"
    if not ok:
        try:
            store._set_state(
                ids, "digest", "digest_restore", reason=fail_reason, now=t
            )
        except Exception:  # noqa: BLE001
            store.mark_digest(ids, now=t)
        _log_digest_fail()
        return None
    for r in rows:
        try:
            store._ledger(str(r.id), str(r.kind), "spoken", "digest_flush", now=t)
        except Exception:  # noqa: BLE001
            pass
    try:
        store.clear_digest(ids, now=t)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] digest flush clear failed: {exc}", flush=True)
    print(f"[ok] digest flush: {sentence}", flush=True)
    return sentence


def maybe_flush_digest(
    store: Any,
    state: dict[str, Any],
    settings: Any,
    *,
    speak=None,
    activity: dict | None = None,
    now: float | None = None,
) -> str | None:
    """Speak one digest sentence when interval elapsed or gaming→idle."""
    t = time.time() if now is None else float(now)
    busy, _gaming, _in_call = _busy(activity=activity)
    was_busy = bool(state.get("was_busy", False))
    transition = was_busy and not busy
    state["was_busy"] = busy
    if busy:
        return None
    rows = list(store.digest_rows(now=t) or [])
    if not rows:
        return None
    interval = float(getattr(settings, "alert_digest_interval_s", 1800) or 1800)
    oldest = min(
        float(getattr(r, "digest_at", 0) or 0) or float(getattr(r, "ts", 0) or 0)
        for r in rows
    )
    aged = (t - oldest) >= interval
    if not (aged or transition):
        return None
    return _flush_digest_common(store, speak=speak, now=t)


def _speak_choked(
    store: Any,
    row: Any,
    *,
    speak=None,
    claim: bool = False,
    cfg: Any | None = None,
    now: float | None = None,
) -> bool:
    """Shape+choke → optional mark_spoken claim → speak → ack. False = no ack."""
    from types import SimpleNamespace

    from jarvis.speak_gate import SpeakPlan

    speak_fn = _speak_hermes if speak is None else speak
    result = enforce(
        store,
        row,
        SpeakPlan("speak", "speak"),
        cfg=cfg if cfg is not None else SimpleNamespace(),
        now=now,
        speak=speak_fn,
        claim=claim,
    )
    return result == "speak"


def _flush_digest_now(
    store: Any,
    *,
    speak=None,
    now: float | None = None,
) -> str | None:
    """Claim + speak all current digest rows once (no interval gate)."""
    return _flush_digest_common(store, speak=speak, now=now)


def tick(
    store: Any,
    state: dict[str, Any],
    *,
    settings: Any | None = None,
    speak=None,
    activity: dict | None = None,
    now: float | None = None,
    interval: float = 1.0,
) -> Any | None:
    """One poll iteration (release → digest → peek → act). Returns peeked row or None."""
    from jarvis import alert_shadow
    from jarvis.settings import load_settings

    cfg = settings if settings is not None else load_settings()
    mode = str(getattr(cfg, "alert_policy_mode", "off") or "off").strip().lower()
    t = time.time() if now is None else float(now)

    if mode == "off":
        # Converge zombies without shadow / without changing speak path.
        busy, _, _ = _busy(activity=activity)
        state["was_busy"] = busy
        gc = getattr(store, "gc", None)
        if callable(gc):
            gc(now=t)
        _flush_digest_now(store, speak=speak, now=t)
        store.release_held(now=t)
    else:
        alert_shadow.record_heartbeat()
        # Unconditional write-path GC each tick (~1s). Instructions asked
        # unconditional release_held; that skips quiet flap + thrash-holds under
        # gaming — call gc() instead (persist=True only). held→pending stays
        # quiet-gated via maybe_release_held → release_held.
        gc = getattr(store, "gc", None)
        if callable(gc):
            gc(now=t)
        maybe_release_held(store, state, activity=activity, now=t)
        maybe_flush_digest(
            store, state, cfg, speak=speak, activity=activity, now=t
        )

    lease_s = max(300.0, float(interval) * 10.0)
    row = store.peek(lease_s=lease_s)
    if row is None:
        return None

    if mode == "off":
        _speak_choked(store, row, speak=speak, claim=False, cfg=cfg, now=t)
        return row

    plan = plan_for(row, mode, activity=activity, settings=cfg)
    alert_shadow.record_decision(
        str(getattr(row, "kind", "") or ""),
        str(getattr(row, "id", "") or ""),
        plan,
        mode=mode,
    )

    if mode == "shadow":
        _speak_choked(store, row, speak=speak, claim=False, cfg=cfg, now=t)
        return row

    # enforce
    enforce(store, row, plan, cfg=cfg, now=t, speak=speak or _speak_hermes, claim=True)
    return row


def main() -> int:
    from jarvis.alert_store import default_store
    from jarvis.settings import load_settings

    interval = float(os.environ.get("JARVIS_ALERT_POLL_S", "1") or "1")
    st = default_store()
    state: dict[str, Any] = {
        "quiet_since": None,
        "was_busy": False,
    }
    print(f"[ok] alert poll loop every {interval}s → {st.path}", flush=True)
    while True:
        try:
            tick(st, state, settings=load_settings(), interval=interval)
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] poll: {exc}", flush=True)
        time.sleep(max(0.5, interval))


if __name__ == "__main__":
    raise SystemExit(main())
