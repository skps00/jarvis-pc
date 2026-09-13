"""JARVIS self-review: trend analysis over self_monitor.log + findings store.

Reads the last N daily summary lines from ``%APPDATA%\\Jarvis\\self_monitor.log``,
aggregates per-day, detects sustained (>=3 consecutive day) degradations, and
writes ``%APPDATA%\\Jarvis\\self_review.json``.

Design notes (Self-Evol plan R15/R16, 2026-08-30):
- Every finding carries provenance (scope / source / trust) so untrusted input
  can never be promoted to verified — the voice channel is an untrusted input.
- Trend rule: a metric must degrade on 3 CONSECUTIVE days to be flagged; a
  single-day spike is noise (self_monitor's own tuning already reacts to
  single-day fp >= 3).
- This module is read-only w.r.t. the logs; the writeback pipeline
  (maker/skeptic -> approval -> append-only) is a later task.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

_TAIL_LINES = 2000
_TREND_WINDOW = 3  # consecutive days of degradation before flagging
_EXPIRES_DAYS = 7

# self_monitor.log summary line, e.g.:
#   2026-08-30 09:00:00 | fires=5 fp=1 stt_miss=0 avg_best=0.42 avg_peak=0.55
#   agc=2.1x agc_boost_pct=60% aec=on stt_rtf=0.31 repair=0 tts_ok=3 err=0
#   vram=9.5 thr=0.50->0.50
_RE_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} \| ")
_RE_KV = re.compile(r"(\w+)=([\d.]+|n/a|on|off)")
_RE_THR = re.compile(r"thr=([\d.]+)->([\d.]+)")

# Metrics whose LOWER is better (fp, stt_rtf, err) vs HIGHER is better.
_LOWER_IS_BETTER = {"fp", "stt_miss", "stt_rtf", "err"}


def _jarvis_dir() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis"


def _tail_lines(path: Path, n: int) -> list[str]:
    if not path.is_file():
        return []
    try:
        # deque with maxlen keeps only the last n lines — no full-file read
        # (cursor review 2026-08-30 MEDIUM-4: log can grow for years).
        from collections import deque

        with path.open(encoding="utf-8", errors="replace") as f:
            return list(deque(f, maxlen=n))
    except OSError:
        return []


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_log(lines: list[str]) -> list[dict[str, object]]:
    """Parse self_monitor.log summary lines into per-entry dicts (one per run)."""
    entries: list[dict[str, object]] = []
    for line in lines:
        m = _RE_DATE.match(line)
        if not m:
            continue
        entry: dict[str, object] = {"date": m.group(1)}
        for key, val in _RE_KV.findall(line):
            if val in ("n/a", "on", "off"):
                entry[key] = val
            else:
                entry[key] = float(val)
        tm = _RE_THR.search(line)
        if tm:
            entry["thr_old"] = float(tm.group(1))
            entry["thr_new"] = float(tm.group(2))
        entries.append(entry)
    return entries


def aggregate_by_day(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    """Combine multiple runs per calendar day into one daily snapshot (last run wins for scalars)."""
    by_day: dict[str, dict[str, object]] = {}
    for e in entries:
        day = str(e["date"])
        if day not in by_day:
            by_day[day] = dict(e)
            by_day[day]["runs"] = 1
        else:
            agg = by_day[day]
            for k, v in e.items():
                if k in ("date", "runs"):
                    continue
                if k == "fires" and isinstance(v, (int, float)) and isinstance(agg.get(k), (int, float)):
                    agg[k] = int(agg[k]) + int(v)  # type: ignore[operator]
                elif k in ("thr_old", "thr_new"):
                    agg[k] = v  # last run's threshold
                else:
                    agg[k] = v  # last run wins for rates/averages
            agg["runs"] = int(agg["runs"]) + 1  # type: ignore[operator]
    return [by_day[d] for d in sorted(by_day)]


# ---------------------------------------------------------------------------
# Trend detection
# ---------------------------------------------------------------------------

def _metric_value(day: dict[str, object], metric: str) -> float | None:
    v = day.get(metric)
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _consecutive_days(days: list[dict[str, object]], window: int = _TREND_WINDOW) -> bool:
    """②: 最近 window 內嘅日 entries 必須係連續曆日，缺日唔可以當「連續退化」。"""
    dates = [str(d.get("date") or "") for d in days[-window:]]
    if len(dates) < 2:
        return True
    try:
        prev = datetime.strptime(dates[0], "%Y-%m-%d")
        for ds in dates[1:]:
            cur = datetime.strptime(ds, "%Y-%m-%d")
            if (cur - prev).days != 1:
                return False
            prev = cur
        return True
    except ValueError:
        return False


def detect_trend(
    days: list[dict[str, object]], metric: str, window: int = _TREND_WINDOW
) -> bool:
    """True if metric degraded on `window` consecutive days (last `window` days)."""
    if len(days) < window:
        return False
    if not _consecutive_days(days, window):
        return False
    lower_better = metric in _LOWER_IS_BETTER
    recent = days[-window:]
    vals = [_metric_value(d, metric) for d in recent]
    if any(v is None for v in vals):
        return False
    degraded = 0
    prev: float | None = None
    for v in vals:  # type: ignore[arg-type]
        if prev is not None:
            worsened = (v > prev) if lower_better else (v < prev)
            if worsened:
                degraded += 1
            else:
                degraded = 0
        prev = v
    return degraded >= window - 1


# ---------------------------------------------------------------------------
# Findings / review building
# ---------------------------------------------------------------------------

# 加新 metric 到 self_monitor.log summary 時，如果要 trend 監控，記得同步加落
# 呢度 + _LOWER_IS_BETTER（方向定義）。硬編碼係有意：明確列出要監控嘅 metric，
# 唔會因為 log 多咗 key 而自動出 finding（③）。
_TREND_METRICS = ["fp", "stt_rtf", "stt_miss", "err"]


def build_findings(
    days: list[dict[str, object]], generated_at: str
) -> list[dict[str, object]]:
    """Detect sustained trends and emit schema-compliant findings (R15/R16)."""
    findings: list[dict[str, object]] = []
    created = generated_at[:10]
    expires = (datetime.strptime(created, "%Y-%m-%d") + timedelta(days=_EXPIRES_DAYS)).strftime(
        "%Y-%m-%d"
    )
    for metric in _TREND_METRICS:
        if detect_trend(days, metric):
            recent = days[-_TREND_WINDOW:]
            vals = [_metric_value(d, metric) for d in recent]
            findings.append(
                {
                    "id": f"TREND-{metric}-{created}",
                    "type": "trend_issue",
                    "metric": metric,
                    "severity": "medium",
                    "confidence": 0.8,  # log-derived, verified source
                    "source": f"self_monitor.log (last {_TREND_WINDOW} days: {vals})",
                    "contradicts": [],
                    "created": created,
                    "updated": created,
                    "expires": expires,
                    "summary": f"{metric} degraded on {_TREND_WINDOW} consecutive days ({vals})",
                    "provenance": {
                        "trust": "verified",
                        "scope": "log-derived",
                        "source": "self_monitor.log",
                    },
                }
            )
    return findings


def build_review(
    days: list[dict[str, object]], generated_at: str, fragility: list[dict[str, object]] | None = None
) -> dict[str, object]:
    """Assemble the full self_review.json document."""
    return {
        "date": generated_at[:10],
        "generated_at": generated_at,
        "days_analyzed": len(days),
        "trends": {m: detect_trend(days, m) for m in _TREND_METRICS},
        "findings": build_findings(days, generated_at),
        "suggestions": [],
        "fragility": fragility or [],
        "schema_version": 1,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def fingerprint(review: dict[str, object]) -> str:
    """Deterministic one-line fingerprint for the cron monitor (R3: agent can't touch)."""
    findings = review.get("findings", [])
    if not findings:
        return "NONE"
    parts = [f"{f.get('metric')}:{f.get('summary')}" for f in findings]  # type: ignore[union-attr]
    return "FINDING " + " | ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="JARVIS self-review trend analysis")
    ap.add_argument("--fingerprint", action="store_true", help="print deterministic fingerprint only")
    ap.add_argument("--days", type=int, default=7, help="days of log history to analyze")
    args = ap.parse_args()

    base = _jarvis_dir()
    lines = _tail_lines(base / "self_monitor.log", _TAIL_LINES)
    entries = parse_log(lines)
    if not entries and lines:
        # ① fail-visible：log 有內容但一條 summary 都 parse 唔到 → self_monitor.log
        # 格式改咗。唔好 silent 當 NONE（monitor 唔會醒）；出固定 ERROR marker（⑫ 已
        # 保證持續 ERROR 唔 spam）。
        print("ERROR", flush=True)
        return 2
    days = aggregate_by_day(entries)
    if args.days > 0:
        days = days[-args.days:]  # honor --days: analyze the last N calendar days

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    review = build_review(days, generated_at)

    try:
        base.mkdir(parents=True, exist_ok=True)
        with (base / "self_review.json").open("w", encoding="utf-8") as f:
            json.dump(review, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        print(f"ERROR: cannot write self_review.json: {exc}", file=sys.stderr)
        return 1

    if args.fingerprint:
        print(fingerprint(review), flush=True)
        return 0

    print(json.dumps(review, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
