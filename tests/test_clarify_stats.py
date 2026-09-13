"""Tests for jarvis.clarify_stats (Self-Evol E4 consumer, 2026-08-31).

Covers: empty log, precision over recorded outcomes, unrecorded tracking,
malformed-line tolerance, deterministic fingerprint.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.clarify_stats import (  # noqa: E402
    compute_stats,
    default_log_path,
    fingerprint,
    load_events,
)


def _proceed(changed_plan, n_questions=1, rounds=1, assumptions=1) -> dict:
    return {
        "ts": "2026-08-31 09:00:00",
        "event": "proceed",
        "rounds_used": rounds,
        "n_questions_asked": n_questions,
        "changed_plan": changed_plan,
        "note": "",
        "n_assumptions": assumptions,
    }


def test_empty_log(tmp_path):
    stats = compute_stats([])
    assert stats["total_proceeds"] == 0
    assert stats["precision"] is None
    assert fingerprint(stats) == "NO_DATA"


def test_missing_log_file(tmp_path):
    assert load_events(tmp_path / "nope.jsonl") == []
    stats = compute_stats(load_events(tmp_path / "nope.jsonl"))
    assert fingerprint(stats) == "NO_DATA"


def test_precision_calculation():
    events = [
        _proceed(True),
        _proceed(False),
        _proceed(True),
        _proceed(True),
    ]
    stats = compute_stats(events)
    assert stats["total_proceeds"] == 4
    assert stats["changed_plan_true"] == 3
    assert stats["changed_plan_false"] == 1
    assert stats["changed_plan_unrecorded"] == 0
    assert stats["precision"] == 0.75
    assert fingerprint(stats) == "PRECISION 0.750|4|4"


def test_unrecorded_outcomes_tracked_separately():
    events = [_proceed(True), _proceed(None), _proceed(False)]
    stats = compute_stats(events)
    assert stats["changed_plan_unrecorded"] == 1
    # precision counts only recorded outcomes
    assert stats["precision"] == 0.5


def test_all_unrecorded_precision_none():
    events = [_proceed(None), _proceed(None)]
    stats = compute_stats(events)
    assert stats["precision"] is None
    assert fingerprint(stats) == "PRECISION NA|2|2"


def test_malformed_lines_skipped(tmp_path):
    p = tmp_path / "clarify_log.jsonl"
    p.write_text(
        '{"event": "proceed", "changed_plan": true}\n'
        "{ not json\n"
        '"plain string"\n'
        '{"event": "proceed", "changed_plan": false}\n',
        encoding="utf-8",
    )
    events = load_events(p)
    assert len(events) == 2  # true + false; 2 malformed lines skipped
    stats = compute_stats(events)
    assert stats["precision"] == 0.5  # true=1, false=1


def test_questions_and_rounds_averages():
    events = [_proceed(True, n_questions=3, rounds=2, assumptions=2),
              _proceed(False, n_questions=5, rounds=1, assumptions=0)]
    stats = compute_stats(events)
    assert stats["questions_asked"] == 8
    assert stats["avg_rounds"] == 1.5
    assert stats["avg_assumptions"] == 1.0


def test_non_proceed_events_ignored():
    events = [
        {"event": "ask", "changed_plan": None},
        _proceed(True),
    ]
    stats = compute_stats(events)
    assert stats["total_proceeds"] == 1


def test_default_log_path_uses_appdata(monkeypatch):
    monkeypatch.setenv("APPDATA", "C:/fake/appdata")
    assert default_log_path() == Path("C:/fake/appdata") / "Jarvis" / "clarify_log.jsonl"
