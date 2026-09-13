"""STT accuracy consumer (Self-Evol E2, 2026-08-31).

Primary source: ``%APPDATA%\\Jarvis\\repair_log.jsonl`` (structured JSONL
written by ``engine._log_repair_event``). serve.log text parsing
(``asr_repair=`` lines) is only the fallback when the structured log is
empty/missing. wake_debug.log supplies ``oww_fire`` counts for the repair
ratio denominator.

Design:
- Deterministic, stdlib-only (no LLM) so it is unit-testable.
- ``--fingerprint`` emits a stable monitor summary (R6 zero-idle-cost pattern):
  * NO_DATA when there are no wake fires,
  * REPAIR_RATIO <ratio>|<repair>|<total> once there is data.
- Suggestions are printed, never auto-applied: promoting a wrong alias into
  memory/stt_aliases would corrupt routing, so the human (or a future gated
  pipeline) decides. A pair repeated >= SUGGEST_MIN times is worth it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

# serve.log 行: [engine] asr_repair=ASR 修正：'raw' → 'fixed'；app 補開（78%）：'c' → 'd'
_RE_ASR_REPAIR = re.compile(r"asr_repair=")
_RE_CONFUSION = re.compile(r"'([^']+)'\s*→\s*'([^']+)'")
_RE_OWW_FIRE = re.compile(r"oww_fire")

SUGGEST_MIN = 3  # 同一 raw→fixed 出現 >=3 次先值得建議
TOP_N = 5
_REPAIR_WINDOW = 2000  # matches _tail_lines on wake_debug.log


def default_serve_log() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "serve.log"


def default_wake_log() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "wake_debug.log"


def default_repair_log() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "repair_log.jsonl"


def _tail_lines(path: Path, n: int = 2000) -> list[str]:
    if not path.is_file():
        return []
    try:
        # deque with maxlen keeps only the last n lines — no full-file read
        from collections import deque

        with path.open(encoding="utf-8", errors="replace") as f:
            return list(deque(f, maxlen=n))
    except OSError:
        return []


def count_fires(wake_lines: list[str]) -> int:
    """Number of ``oww_fire`` lines (wake trips) in the window."""
    return sum(1 for line in wake_lines if _RE_OWW_FIRE.search(line))


def load_repair_events(repair_log: Path) -> list[tuple[str, str]]:
    """Read structured repair_log.jsonl (written by engine._log_repair_event).

    Malformed lines are skipped; a missing file returns [] (caller falls back
    to serve.log text parsing).
    """
    if not repair_log.is_file():
        return []
    pairs: list[tuple[str, str]] = []
    lines = _tail_lines(repair_log, _REPAIR_WINDOW)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        raw = str(obj.get("raw") or "").strip()
        fixed = str(obj.get("fixed") or "").strip()
        if raw and fixed and raw != fixed:
            pairs.append((raw, fixed))
    return pairs


def parse_repair_pairs(serve_lines: list[str]) -> list[tuple[str, str]]:
    """Extract (raw, fixed) confusion pairs from ``asr_repair=`` notes.

    Takes the FIRST arrow pair in each note — that is the original STT
    mis-hearing; later arrows (e.g. an app-name rewrite in the same note)
    are derived from it and would double-count.
    """
    pairs: list[tuple[str, str]] = []
    for line in serve_lines:
        if not _RE_ASR_REPAIR.search(line):
            continue
        m = _RE_CONFUSION.search(line)
        if m:
            raw = m.group(1).strip()
            fixed = m.group(2).strip()
            if raw and fixed and raw != fixed:
                pairs.append((raw, fixed))
    return pairs


def extract_alias_target(fixed: str) -> str | None:
    """``開 Cursor`` / ``閂 whatsapp`` → ``Cursor`` / ``whatsapp`` (learn_stt_alias target).

    Only clear verb+target shapes qualify; anything else (query/unknown)
    cannot be turned into an app alias.
    """
    t = (fixed or "").strip()
    m = re.match(r"^(開|再開|另開|多開|閂|關|關閉|關掉|open|launch|close|quit)\s+(.+)$", t, re.I)
    if not m:
        return None
    target = m.group(2).strip()
    if not target or len(target) > 40:
        return None
    return target


def compute_stats(
    repair_pairs: list[tuple[str, str]], fires: int
) -> dict[str, object]:
    """Repair-ratio stats over the log window."""
    hits = len(repair_pairs)
    counter: Counter[tuple[str, str]] = Counter(repair_pairs)
    top = counter.most_common(TOP_N)
    suggestions = [
        {"raw": raw, "fixed": fixed, "count": count}
        for (raw, fixed), count in top
        if count >= SUGGEST_MIN
    ]
    for s in suggestions:
        s["alias_target"] = extract_alias_target(str(s["fixed"]))
    ratio = round(hits / fires, 4) if fires else None
    return {
        "fires": fires,
        "repair_hits": hits,
        "repair_ratio": ratio,
        "top_confusions": [
            {"raw": raw, "fixed": fixed, "count": count} for (raw, fixed), count in top
        ],
        "suggestions": suggestions,
    }


def fingerprint(stats: dict[str, object]) -> str:
    """Deterministic monitor fingerprint: NO_DATA or REPAIR_RATIO <r>|<h>|<n>."""
    if not int(stats.get("fires") or 0):
        return "NO_DATA"
    r = stats.get("repair_ratio")
    r_str = "NA" if r is None else f"{float(r):.4f}"
    return f"REPAIR_RATIO {r_str}|{stats['repair_hits']}|{stats['fires']}"


def _append_summary(path: Path, line: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def run_once(
    serve_log: Path | None = None,
    wake_log: Path | None = None,
    *,
    repair_log: Path | None = None,
    write_log: bool = True,
) -> tuple[dict[str, object], str]:
    """One stats pass. Returns (stats, summary_line).

    Repair pairs come from the structured repair_log.jsonl when present
    (⑬ format-coupling fix); otherwise falls back to serve.log text.
    """
    serve = serve_log or default_serve_log()
    wake = wake_log or default_wake_log()
    rlog = repair_log or default_repair_log()
    fires = count_fires(_tail_lines(wake))
    pairs = load_repair_events(rlog)
    if not pairs:
        pairs = parse_repair_pairs(_tail_lines(serve))
    stats = compute_stats(pairs, fires)
    ratio = stats["repair_ratio"]
    ratio_str = "n/a" if ratio is None else f"{float(ratio):.2%}"
    summary = (
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"fires={stats['fires']} repair={stats['repair_hits']} "
        f"repair_ratio={ratio_str} suggestions={len(stats['suggestions'])}"
    )
    if write_log:
        _append_summary(Path(os.environ.get("APPDATA", "")) / "Jarvis" / "stt_stats.log", summary)
    return stats, summary


def main() -> int:
    ap = argparse.ArgumentParser(description="JARVIS STT accuracy consumer (E2)")
    ap.add_argument("--serve-log", default="", help="path to serve.log (default APPDATA)")
    ap.add_argument("--wake-log", default="", help="path to wake_debug.log (default APPDATA)")
    ap.add_argument("--repair-log", default="", help="path to repair_log.jsonl (default APPDATA)")
    ap.add_argument("--fingerprint", action="store_true", help="print monitor fingerprint only")
    ap.add_argument("--no-write", action="store_true", help="don't append stt_stats.log")
    args = ap.parse_args()

    stats, _summary = run_once(
        Path(args.serve_log) if args.serve_log else None,
        Path(args.wake_log) if args.wake_log else None,
        repair_log=Path(args.repair_log) if args.repair_log else None,
        write_log=not args.no_write,
    )
    if args.fingerprint:
        print(fingerprint(stats))
        return 0
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
