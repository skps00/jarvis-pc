#!/usr/bin/env python3
"""Read-only shadow ledger / heartbeat summary CLI (P1 gate metrics).

Usage::

    python scripts/alert_shadow_report.py [--hours 24] [--json] [--path DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from jarvis.alert_shadow import HB_INTERVAL_S  # noqa: E402


def _parse_ts(raw: Any) -> float | None:
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str) and raw.strip():
        try:
            s = raw.strip().replace("Z", "+00:00")
            return datetime.fromisoformat(s).timestamp()
        except ValueError:
            return None
    return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    out.append(obj)
    except OSError:
        return []
    return out


def _ledger_paths(alerts_dir: Path | None) -> tuple[Path, Path]:
    if alerts_dir is not None:
        return alerts_dir / "shadow_ledger.jsonl", alerts_dir / "shadow_heartbeat.jsonl"
    from jarvis.alert_shadow import heartbeat_path, shadow_ledger_path

    return shadow_ledger_path(), heartbeat_path()


def build_report(
    *,
    hours: float = 24.0,
    alerts_dir: Path | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Aggregate shadow ledger + heartbeat. Never raises; missing → zeros."""
    t_now = time_now(now)
    cutoff = t_now - float(hours) * 3600.0
    ledger_path, hb_path = _ledger_paths(alerts_dir)

    decisions: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    for row in _read_jsonl(ledger_path):
        ts = _parse_ts(row.get("ts"))
        if ts is None or ts < cutoff:
            continue
        dec = str(row.get("decision") or "").strip() or "unknown"
        decisions[dec] += 1
        reason = str(row.get("reason") or "").strip()
        if reason:
            reasons[reason] += 1
        kind = str(row.get("kind") or "").strip()
        if kind:
            kinds[kind] += 1

    hb_lines = 0
    gaming_v1 = 0
    gaming_v2 = 0
    v1_only = 0
    v2_only = 0
    for row in _read_jsonl(hb_path):
        ts = _parse_ts(row.get("ts"))
        if ts is None or ts < cutoff:
            continue
        hb_lines += 1
        v1 = bool(row.get("v1_gaming"))
        v2 = bool(row.get("is_gaming_v2"))
        if v1:
            gaming_v1 += 1
        if v2:
            gaming_v2 += 1
        if v1 and not v2:
            v1_only += 1
        if v2 and not v1:
            v2_only += 1

    game_active_hours = round(gaming_v2 * HB_INTERVAL_S / 3600.0, 4)

    return {
        "hours": float(hours),
        "decisions": {
            "speak": int(decisions.get("speak", 0)),
            "hold": int(decisions.get("hold", 0)),
            "digest": int(decisions.get("digest", 0)),
            "drop": int(decisions.get("drop", 0)),
        },
        "reasons": {k: int(v) for k, v in sorted(reasons.items())},
        "kinds": {k: int(v) for k, v in sorted(kinds.items())},
        "heartbeat": {
            "lines": hb_lines,
            "game_active_hours": game_active_hours,
            "gaming_v1_true": gaming_v1,
            "gaming_v2_true": gaming_v2,
        },
        "fp_hint": {"v1_only": v1_only, "v2_only": v2_only},
    }


def time_now(now: float | None) -> float:
    if now is not None:
        return float(now)
    return datetime.now(timezone.utc).timestamp()


def _print_human(report: dict[str, Any]) -> None:
    """Human-readable key: value summary (default CLI output)."""
    print(f"hours: {report['hours']}")
    dec = report.get("decisions") or {}
    for k in ("speak", "hold", "digest", "drop"):
        print(f"decisions.{k}: {dec.get(k, 0)}")
    for k, v in (report.get("reasons") or {}).items():
        print(f"reasons.{k}: {v}")
    for k, v in (report.get("kinds") or {}).items():
        print(f"kinds.{k}: {v}")
    hb = report.get("heartbeat") or {}
    for k in ("lines", "game_active_hours", "gaming_v1_true", "gaming_v2_true"):
        print(f"heartbeat.{k}: {hb.get(k, 0)}")
    fp = report.get("fp_hint") or {}
    print(f"fp_hint.v1_only: {fp.get('v1_only', 0)}")
    print(f"fp_hint.v2_only: {fp.get('v2_only', 0)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Shadow ledger / heartbeat summary")
    ap.add_argument("--hours", type=float, default=24.0, help="lookback window")
    ap.add_argument("--json", action="store_true", help="stdout pure JSON only")
    ap.add_argument(
        "--path",
        type=Path,
        default=None,
        help="alerts dir (shadow_ledger.jsonl + shadow_heartbeat.jsonl)",
    )
    args = ap.parse_args(argv)
    report = build_report(hours=args.hours, alerts_dir=args.path)
    if args.json:
        print(json.dumps(report, ensure_ascii=True, sort_keys=False))
    else:
        _print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
