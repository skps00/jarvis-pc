"""Clarify precision-log consumer (Self-Evol E4, 2026-08-31).

Reads %APPDATA%\\Jarvis\\clarify_log.jsonl (written by jarvis.clarify) and
computes calibration stats: how often a clarification question CHANGED the
plan (precision). This is the feedback loop for the Phase E gate — the
threshold and question quality are meant to be calibrated from these numbers,
not from LLM self-assessment (R12).

Design:
- Deterministic, no LLM dependency (pure stdlib) so it is unit-testable.
- `--fingerprint` emits a stable summary for the monitor/cron pattern:
  * NO_DATA when there are no proceed events,
  * PRECISION <rate>|<asked>|<n> once there is data.
  A changed fingerprint wakes the daily-review agent; an unchanged one costs
  nothing (monitor pattern, R6 zero-idle-cost).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def default_log_path() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "clarify_log.jsonl"


def load_events(log_path: Path) -> list[dict[str, object]]:
    """All JSONL records; malformed lines are skipped (never crash)."""
    if not log_path.is_file():
        return []
    events: list[dict[str, object]] = []
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events


def compute_stats(events: list[dict[str, object]]) -> dict[str, object]:
    """Calibration stats over proceed events.

    precision = changed_plan True / (True + False) — the fraction of
    clarification rounds that actually changed the plan. Null/absent
    changed_plan (caller never recorded the outcome) is tracked separately so
    we can see when the feedback loop is not being used.
    """
    proceeds = [e for e in events if str(e.get("event") or "") == "proceed"]
    total = len(proceeds)
    if total == 0:
        return {
            "total_proceeds": 0,
            "questions_asked": 0,
            "changed_plan_true": 0,
            "changed_plan_false": 0,
            "changed_plan_unrecorded": 0,
            "precision": None,
            "avg_rounds": 0.0,
            "avg_assumptions": 0.0,
        }
    asked = 0
    cp_true = cp_false = cp_null = 0
    rounds_sum = 0.0
    assum_sum = 0.0
    for e in proceeds:
        asked += int(e.get("n_questions_asked") or 0)
        cp = e.get("changed_plan")
        if cp is True:
            cp_true += 1
        elif cp is False:
            cp_false += 1
        else:
            cp_null += 1
        rounds_sum += float(e.get("rounds_used") or 0)
        assum_sum += float(e.get("n_assumptions") or 0)
    recorded = cp_true + cp_false
    precision = round(cp_true / recorded, 3) if recorded else None
    return {
        "total_proceeds": total,
        "questions_asked": asked,
        "changed_plan_true": cp_true,
        "changed_plan_false": cp_false,
        "changed_plan_unrecorded": cp_null,
        "precision": precision,
        "avg_rounds": round(rounds_sum / total, 2),
        "avg_assumptions": round(assum_sum / total, 2),
    }


def fingerprint(stats: dict[str, object]) -> str:
    """Deterministic monitor fingerprint: NO_DATA or PRECISION <p>|<asked>|<n>."""
    if not stats.get("total_proceeds"):
        return "NO_DATA"
    p = stats.get("precision")
    p_str = "NA" if p is None else f"{float(p):.3f}"
    return f"PRECISION {p_str}|{stats['questions_asked']}|{stats['total_proceeds']}"


def main() -> int:
    ap = argparse.ArgumentParser(description="JARVIS clarify precision-log consumer (E4)")
    ap.add_argument("--log", default="", help="path to clarify_log.jsonl (default APPDATA)")
    ap.add_argument("--fingerprint", action="store_true",
                    help="print monitor fingerprint only")
    args = ap.parse_args()

    path = Path(args.log) if args.log else default_log_path()
    stats = compute_stats(load_events(path))
    if args.fingerprint:
        print(fingerprint(stats))
        return 0
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
