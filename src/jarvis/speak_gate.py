"""Pure speak / hold / digest / drop decisions for alerts (no I/O writes)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from jarvis import activity as activity_mod
from jarvis.alert_policy import policy_for, priority_for

FRESH_MAX_AGE_S = 180.0
INPUT_WINDOW_S = 120
_STALE_WARN_INTERVAL_S = 300.0
_last_stale_warn_ts = 0.0


@dataclass(frozen=True)
class SpeakPlan:
    action: str  # "speak" | "hold" | "digest" | "drop"
    reason: str


def is_gaming_v2(activity: dict | None = None) -> bool:
    """True when a game process is live and input was recent (SK 2026-09-12).

    Stale snapshots (missing/unparsable age, or age > FRESH_MAX_AGE_S) → False.
    Launcher/queue/menu (idle ≥ INPUT_WINDOW_S) → False. fg/fullscreen ignored.
    """
    sig = activity_mod.signals(activity)
    age = sig["age_s"]
    if age is None or age > FRESH_MAX_AGE_S:
        return False
    idle = sig["idle_seconds"]
    return bool(
        sig["game_process"] and idle is not None and idle < INPUT_WINDOW_S
    )


def _warn_activity_stale(age: float | None) -> None:
    global _last_stale_warn_ts
    now = time.time()
    if now - _last_stale_warn_ts < _STALE_WARN_INTERVAL_S:
        return
    _last_stale_warn_ts = now
    age_s = "None" if age is None else f"{age:.0f}"
    print(f"[warn] speak_gate activity stale age_s={age_s}", flush=True)


def should_speak(
    row_or_kind: Any,
    *,
    activity: dict | None = None,
    settings: Any | None = None,
    now: Any | None = None,
) -> SpeakPlan:
    """Decide speak/hold/digest/drop for a kind or alert row (first match wins).

    ``now`` accepted for call-site compatibility; age comes from snapshot
    timestamp via ``activity.signals``.
    """
    _ = now  # reserved for future clock injection
    if hasattr(row_or_kind, "kind"):
        kind = getattr(row_or_kind, "kind", None) or ""
    else:
        kind = row_or_kind if isinstance(row_or_kind, str) else ""
    kind = str(kind).strip()

    pri = str(getattr(row_or_kind, "priority", "") or "")
    if pri == "critical":
        return SpeakPlan("speak", "critical")

    if not kind:
        return SpeakPlan("digest", "unknown_kind")

    kind_is_critical = (priority_for(kind) == "critical") or pri == "critical"
    if kind_is_critical:
        return SpeakPlan("speak", "critical")

    sig = activity_mod.signals(activity)
    age = sig["age_s"]
    if age is None or age > FRESH_MAX_AGE_S:
        _warn_activity_stale(age)
        return SpeakPlan("hold", "activity_stale")

    if activity is not None:
        in_call = bool(activity.get("voice_call", False))
    else:
        in_call = activity_mod.voice_call()
    if in_call:
        return SpeakPlan("hold", "voice_call")

    if is_gaming_v2(activity):
        return SpeakPlan("hold", "gaming")

    pol = policy_for(kind, settings)
    if pol == "speak_now":
        return SpeakPlan("speak", "policy")
    if pol == "drop":
        return SpeakPlan("drop", "policy")
    return SpeakPlan("digest", "policy")
