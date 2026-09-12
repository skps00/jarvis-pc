"""Shadow-mode ledger + heartbeat writers (fail-open; no delivery changes)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.alert_store import default_queue_path

_MAX_BYTES = 2 * 1024 * 1024
_WARN_INTERVAL_S = 60.0
HB_INTERVAL_S = 45.0
_last_warn_ts = 0.0


def shadow_ledger_path() -> Path:
    """``<alerts dir>/shadow_ledger.jsonl`` beside the alert queue."""
    return default_queue_path().parent / "shadow_ledger.jsonl"


def heartbeat_path() -> Path:
    """``<alerts dir>/shadow_heartbeat.jsonl`` beside the alert queue."""
    return default_queue_path().parent / "shadow_heartbeat.jsonl"


def _marker_path() -> Path:
    return default_queue_path().parent / "shadow_heartbeat.marker"


def _warn(msg: str) -> None:
    global _last_warn_ts
    now = time.time()
    if now - _last_warn_ts < _WARN_INTERVAL_S:
        return
    _last_warn_ts = now
    print(f"[warn] alert_shadow: {msg}", flush=True)


def _iso_ts(now: float | None) -> str:
    if now is None:
        return datetime.now(timezone.utc).astimezone().isoformat()
    return datetime.fromtimestamp(now).isoformat()


def _maybe_rotate(path: Path) -> None:
    if not path.is_file():
        return
    if path.stat().st_size <= _MAX_BYTES:
        return
    bak = Path(str(path) + ".1")
    if bak.exists():
        bak.unlink()
    path.rename(bak)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _maybe_rotate(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def record_decision(
    kind: str,
    row_id: str,
    plan: Any,
    *,
    mode: str,
    now: float | None = None,
) -> None:
    """Append one shadow decision line. Never raises."""
    try:
        row = {
            "ts": _iso_ts(now),
            "mode": mode,
            "id": row_id,
            "kind": kind,
            "decision": getattr(plan, "action", None),
            "reason": getattr(plan, "reason", None),
        }
        _append_jsonl(shadow_ledger_path(), row)
    except Exception as exc:  # noqa: BLE001
        _warn(f"record_decision failed: {exc}")


def _last_heartbeat_ts() -> float | None:
    """Youngest prior heartbeat ts from marker or last jsonl line."""
    marker = _marker_path()
    try:
        if marker.is_file():
            raw = marker.read_text(encoding="utf-8").strip()
            if raw:
                return float(raw)
    except Exception:  # noqa: BLE001
        pass
    path = heartbeat_path()
    try:
        if not path.is_file():
            return None
        last = ""
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = line
        if not last:
            return None
        obj = json.loads(last)
        ts = obj.get("ts")
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, str) and ts:
            return datetime.fromisoformat(ts).timestamp()
    except Exception:  # noqa: BLE001
        return None
    return None


def record_heartbeat(
    *, interval_s: float | None = None, now: float | None = None
) -> bool:
    """Append one heartbeat sample; self-throttled. Never raises.

    Returns False when skipped by throttle or on write failure (fail-open).
    """
    try:
        gap = float(HB_INTERVAL_S if interval_s is None else interval_s)
        t = time.time() if now is None else float(now)
        prev = _last_heartbeat_ts()
        if prev is not None and (t - prev) < gap:
            return False

        from jarvis import activity
        from jarvis.settings import load_settings
        from jarvis.speak_gate import is_gaming_v2

        mode = str(
            getattr(load_settings(), "alert_policy_mode", "off") or "off"
        ).strip().lower()
        row = {
            "ts": _iso_ts(t),
            "signals": activity.signals(),
            "is_gaming_v2": bool(is_gaming_v2()),
            "v1_gaming": bool(activity.gaming()),
            "mode": mode,
        }
        _append_jsonl(heartbeat_path(), row)
        try:
            _marker_path().write_text(str(t), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        return True
    except Exception as exc:  # noqa: BLE001
        _warn(f"record_heartbeat failed: {exc}")
        return False
