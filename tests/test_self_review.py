"""Tests for jarvis.self_review (Self-Evol Task 2, 2026-08-30).

Covers: log parsing, per-day aggregation, sustained-trend detection
(3 consecutive days, single-day noise ignored), findings schema
(confidence/source/contradicts/expires/provenance), fingerprint output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.self_review import (  # noqa: E402
    _TREND_WINDOW,
    aggregate_by_day,
    build_findings,
    build_review,
    detect_trend,
    fingerprint,
    parse_log,
)


def _line(date: str, fp: float, rtf: float, err: float = 0.0) -> str:
    """Synthesize one self_monitor.log summary line."""
    return (
        f"{date} 09:00:00 | fires=10 fp={fp} stt_miss=0 avg_best=0.40 avg_peak=0.55 "
        f"agc=2.0x agc_boost_pct=50% aec=on stt_rtf={rtf} repair=0 tts_ok=3 err={err} "
        f"vram=9.5 thr=0.50->0.50"
    )


# ---------------------------------------------------------------------------
# parse_log
# ---------------------------------------------------------------------------

def test_parse_log_extracts_fields():
    lines = [_line("2026-08-24", 1, 0.30), _line("2026-08-25", 2, 0.40)]
    entries = parse_log(lines)
    assert len(entries) == 2
    e = entries[0]
    assert e["date"] == "2026-08-24"
    assert e["fp"] == 1.0
    assert e["stt_rtf"] == 0.30
    assert e["aec"] == "on"
    assert e["thr_old"] == 0.50
    assert e["thr_new"] == 0.50


def test_parse_log_ignores_garbage_lines():
    lines = ["not a summary", "2026-08-24 garbage without pipe", _line("2026-08-24", 1, 0.3)]
    entries = parse_log(lines)
    assert len(entries) == 1


# ---------------------------------------------------------------------------
# aggregate_by_day
# ---------------------------------------------------------------------------

def test_aggregate_sums_fires_keeps_last_rate():
    entries = [
        {"date": "2026-08-24", "fires": 5, "fp": 1, "stt_rtf": 0.30},
        {"date": "2026-08-24", "fires": 7, "fp": 2, "stt_rtf": 0.35},
        {"date": "2026-08-25", "fires": 3, "fp": 0, "stt_rtf": 0.28},
    ]
    days = aggregate_by_day(entries)
    assert len(days) == 2
    day1 = days[0]
    assert day1["date"] == "2026-08-24"
    assert day1["fires"] == 12  # summed
    assert day1["runs"] == 2
    assert day1["stt_rtf"] == 0.35  # last run wins


# ---------------------------------------------------------------------------
# detect_trend
# ---------------------------------------------------------------------------

def _days(fp_values: list[float]) -> list[dict]:
    return [{"date": f"2026-08-{20 + i:02d}", "fp": v, "stt_rtf": 0.3} for i, v in enumerate(fp_values)]


def test_trend_flag_on_3_consecutive_degradation():
    # fp rising 3 days straight (lower is better => rising = worse)
    days = _days([1, 2, 3])
    assert detect_trend(days, "fp") is True


def test_trend_not_flagged_on_single_day_noise():
    # one bad day then recovery — not a sustained trend
    days = _days([1, 5, 1, 1])
    assert detect_trend(days, "fp") is False


def test_trend_not_flagged_with_insufficient_data():
    assert detect_trend(_days([1, 2]), "fp") is False


def test_trend_not_flagged_on_improvement():
    # fp falling (improving) — no flag
    days = _days([3, 2, 1])
    assert detect_trend(days, "fp") is False


def test_trend_requires_window_not_just_any_3():
    # degradation on days 1-2 then stable: only 2 consecutive degraded at the tail
    days = _days([1, 2, 2, 2])
    assert detect_trend(days, "fp") is False


# ---------------------------------------------------------------------------
# build_findings / schema
# ---------------------------------------------------------------------------

def test_finding_schema_fields_present():
    days = _days([1, 2, 3])
    findings = build_findings(days, "2026-08-30 09:00:00")
    assert len(findings) == 1
    f = findings[0]
    for key in ("id", "type", "metric", "severity", "confidence", "source",
                "contradicts", "created", "updated", "expires", "summary", "provenance"):
        assert key in f, f"missing schema field: {key}"
    assert isinstance(f["confidence"], float) and 0 <= f["confidence"] <= 1
    assert f["contradicts"] == []
    assert f["provenance"]["trust"] == "verified"
    assert f["expires"] > f["created"]  # expires is a later date string


def test_no_findings_when_healthy():
    days = _days([1, 1, 1])
    assert build_findings(days, "2026-08-30 09:00:00") == []


def test_build_review_structure():
    days = _days([1, 2, 3])
    review = build_review(days, "2026-08-30 09:00:00", fragility=[{"id": "F1"}])
    assert review["date"] == "2026-08-30"
    assert review["days_analyzed"] == 3
    assert "trends" in review
    assert "suggestions" in review
    assert review["fragility"] == [{"id": "F1"}]
    assert review["schema_version"] == 1
    # JSON-serializable
    json.dumps(review)


# ---------------------------------------------------------------------------
# fingerprint
# ---------------------------------------------------------------------------

def test_fingerprint_none_when_no_findings():
    review = build_review(_days([1, 1, 1]), "2026-08-30 09:00:00")
    assert fingerprint(review) == "NONE"


def test_fingerprint_finding_when_trend():
    review = build_review(_days([1, 2, 3]), "2026-08-30 09:00:00")
    fp = fingerprint(review)
    assert fp.startswith("FINDING ")
    assert "fp" in fp


def test_fingerprint_deterministic():
    review1 = build_review(_days([1, 2, 3]), "2026-08-30 09:00:00")
    review2 = build_review(_days([1, 2, 3]), "2026-08-30 09:00:00")
    assert fingerprint(review1) == fingerprint(review2)
