"""Daily JARVIS self-monitor: wake/serve stats + safe wake_threshold auto-tune.

Moved into the sidecar package (2026-08-29) so JARVIS is self-contained —
no more external Hermes cron for this. ``shell_app`` spawns a daemon thread
that runs this daily at 09:00 (plus a catch-up run shortly after serve start);
notable findings are pushed to the alert store → spoken by the alert poller.

CLI usage (diagnostics) still works: ``python -m jarvis.self_monitor``.
Silent stdout unless threshold changed, errors, or fp>=3.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

_TAIL_LINES = 2000
_THR_MIN = 0.25
_THR_MAX = 0.75
_FP_DUR_S = 0.6
_FP_TUNE_MIN = 3
_PEAK_LOW = 0.28

_RE_OWW_CMD_DUR = re.compile(r"oww_cmd_pcm\s+dur=([\d.]+)s")
_RE_HEARTBEAT_BEST = re.compile(r"\bbest=([\d.]+)")
_RE_HEARTBEAT_PEAK = re.compile(r"\bpeak_best=([\d.]+)")
_RE_AGC_GAIN = re.compile(r"agc_gain=([\d.]+)")
_RE_RTF = re.compile(r"rtf_avg:\s*([\d.]+)")


def _jarvis_dir() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis"


def _tail_lines(path: Path, n: int) -> list[str]:
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    return lines[-n:] if len(lines) > n else lines


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _parse_wake_debug(lines: list[str]) -> dict[str, object]:
    fires = 0
    fp = 0
    stt_miss = 0
    best_vals: list[float] = []
    peak_vals: list[float] = []
    agc_vals: list[float] = []
    aec = False
    for line in lines:
        if "oww_fire" in line:
            fires += 1
        if "oww_cmd_pcm" in line:
            m = _RE_OWW_CMD_DUR.search(line)
            if m and float(m.group(1)) < _FP_DUR_S:
                fp += 1
        if "stt_wake" in line and "ok=False" in line:
            stt_miss += 1
        if "wake_heartbeat" in line:
            mb = _RE_HEARTBEAT_BEST.search(line)
            mp = _RE_HEARTBEAT_PEAK.search(line)
            if mb:
                best_vals.append(float(mb.group(1)))
            if mp:
                peak_vals.append(float(mp.group(1)))
        if "agc_gain=" in line:
            mg = _RE_AGC_GAIN.search(line)
            if mg:
                agc_vals.append(float(mg.group(1)))
        if "aec_first_apply" in line:
            aec = True
    return {
        "fires": fires,
        "fp": fp,
        "stt_miss": stt_miss,
        "avg_best": _avg(best_vals),
        "avg_peak": _avg(peak_vals),
        "agc_vals": agc_vals,
        "aec": aec,
    }


def _parse_serve_log(lines: list[str]) -> dict[str, object]:
    rtf_vals: list[float] = []
    err = 0
    repair_hits = 0
    tts_ok = 0
    for line in lines:
        mr = _RE_RTF.search(line)
        if mr:
            rtf_vals.append(float(mr.group(1)))
        if "Traceback" in line:
            err += 1
        if "UnicodeDecodeError" in line:
            err += 1
        if "stream_err" in line:
            err += 1
        if "asr_repair=" in line:
            repair_hits += 1
        if "tts_ok" in line:
            tts_ok += 1
    return {"rtf_avg": _avg(rtf_vals), "err": err, "repair_hits": repair_hits, "tts_ok": tts_ok}


def _read_wake_threshold(settings_path: Path) -> float | None:
    if not settings_path.is_file():
        return None
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    try:
        return float(data.get("wake_threshold", 0.50))
    except (TypeError, ValueError):
        return 0.50


def _tune_threshold(current: float, fires: int, fp: int, avg_peak: float | None) -> float:
    if fp >= _FP_TUNE_MIN:
        return min(_THR_MAX, current + 0.05)
    if avg_peak is not None and avg_peak < _PEAK_LOW and fires == 0:
        return max(_THR_MIN, current - 0.05)
    return current


def _write_wake_threshold(settings_path: Path, new_thr: float) -> bool:
    """Single-writer patch via settings.save_settings_patch (dir-lock + atomic + pending-apply)."""
    try:
        from jarvis.settings import save_settings_patch

        save_settings_patch({"wake_threshold": round(new_thr, 2)})
        return True
    except Exception:  # noqa: BLE001
        return False


def _fmt_f(value: float | None, places: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{places}f}"


def _agc_boost_pct(agc_vals: list[float]) -> float | None:
    if not agc_vals:
        return None
    boosted = sum(1 for v in agc_vals if v > 1.5)
    return 100.0 * boosted / len(agc_vals)


def _query_vram_gb() -> str:
    try:
        from jarvis.gpu_policy import gpu_metrics

        mib = gpu_metrics().get("vram_used_mb")
        if mib is None:
            return "?"
        return f"{mib / 1024:.1f}"
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return "?"


def run_once() -> tuple[str, bool]:
    """Run one self-monitor pass. Returns (summary_line, notable).

    notable = threshold changed / serve errors / fp >= 3 (things SK should hear).
    Writes the summary to ``%APPDATA%\\Jarvis\\self_monitor.log`` regardless.
    """
    base = _jarvis_dir()
    wake_lines = _tail_lines(base / "wake_debug.log", _TAIL_LINES)
    serve_lines = _tail_lines(base / "serve.log", _TAIL_LINES)

    wake = _parse_wake_debug(wake_lines)
    serve = _parse_serve_log(serve_lines)

    settings_path = base / "settings.json"
    old_thr = _read_wake_threshold(settings_path)
    new_thr = old_thr
    if old_thr is not None:
        tuned = _tune_threshold(
            old_thr,
            int(wake["fires"]),
            int(wake["fp"]),
            wake["avg_peak"],  # type: ignore[arg-type]
        )
        if tuned != old_thr:
            if _write_wake_threshold(settings_path, tuned):
                new_thr = tuned

    agc_vals: list[float] = wake["agc_vals"]  # type: ignore[assignment]
    agc_avg = _avg(agc_vals)
    agc_str = f"{agc_avg:.1f}x" if agc_avg is not None else "n/a"
    boost_pct = _agc_boost_pct(agc_vals)
    boost_str = f"{boost_pct:.0f}%" if boost_pct is not None else "n/a"
    vram_str = _query_vram_gb()

    thr_old = _fmt_f(old_thr) if old_thr is not None else "n/a"
    thr_new = _fmt_f(new_thr) if new_thr is not None else "n/a"

    summary = (
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"fires={wake['fires']} fp={wake['fp']} stt_miss={wake['stt_miss']} "
        f"avg_best={_fmt_f(wake['avg_best'])} avg_peak={_fmt_f(wake['avg_peak'])} "
        f"agc={agc_str} agc_boost_pct={boost_str} aec={'on' if wake['aec'] else 'off'} "
        f"stt_rtf={_fmt_f(serve['rtf_avg'])} repair={serve['repair_hits']} tts_ok={serve['tts_ok']} "
        f"err={serve['err']} "
        f"vram={vram_str} thr={thr_old}->{thr_new}"
    )

    try:
        base.mkdir(parents=True, exist_ok=True)
        with (base / "self_monitor.log").open("a", encoding="utf-8") as f:
            f.write(summary + "\n")
    except OSError:
        pass

    notable = (
        (old_thr is not None and new_thr is not None and new_thr != old_thr)
        or int(serve["err"]) > 0
        or int(wake["fp"]) >= _FP_TUNE_MIN
    )
    return summary, notable


def main() -> int:
    summary, notable = run_once()
    if notable:
        print(summary, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
