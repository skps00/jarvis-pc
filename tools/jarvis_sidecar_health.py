#!/usr/bin/env python3
"""JARVIS sidecar health watchdog (Hermes cron monitor fingerprint).

Stdout is ALWAYS exactly one line (empty stdout = cron stays silent forever).

Deploy: copy this file to
``%LOCALAPPDATA%\\hermes\\scripts\\jarvis_sidecar_health.py``.

Fingerprints:
  - UP: ``OK wake_on=<True|False>`` (same as v1). Clears state.
    Requires HTTP 200 JSON ``{"ok": true, "service": "jarvis"}``.
  - OFF: HUD gone (no ``JARVIS ONE.exe`` / ``JARVIS-ONE-*.exe``) AND no
    python/pythonw cmdline containing ``jarvis serve``. No time bucket. No wake.
  - DOWN: ``DOWN <reason> t=<bucket>`` — reason names from the HTTP check
    (URLError, HTTPError, BadPayload, Timeout, …).
  - WARN: ``WARN state_io`` if state file read/write fails.

Buckets (from state ``down_since``; string changes only when crossing a bucket):
  ``<5m`` / ``5-30m`` / ``30m-2h`` / ``2-6h`` / ``>6h``. First DOWN → ``<5m``.

State file:
  ``%LOCALAPPDATA%\\hermes\\state\\jarvis_sidecar_health_state.json``
  ``{"down_since": <epoch|null>, "last_reason": "...", "updated_at": <epoch>}``
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# 2026-09-23: FROZEN at 8765 — sidecar alerts MCP + GET/POST /settings; also hardcoded
# in hud/main.js and src/jarvis/settings.py — change all three together or it silently breaks.
HEALTH_URL = "http://127.0.0.1:8765/health"
STATE_PATH = (
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "hermes"
    / "state"
    / "jarvis_sidecar_health_state.json"
)
_HUD_ONE = re.compile(r"(?i)^JARVIS ONE\.exe$")
_HUD_VER = re.compile(r"(?i)^JARVIS-ONE-.*\.exe$")
_PY = re.compile(r"(?i)^pythonw?\.exe$")


class StateIOError(Exception):
    """State file unreadable/unwritable."""


class ProcessEnumError(Exception):
    """Process listing failed (timeout/OS/JSON); not the same as empty list."""


def _bucket(elapsed_s: float) -> str:
    if elapsed_s < 5 * 60:
        return "<5m"
    if elapsed_s < 30 * 60:
        return "5-30m"
    if elapsed_s < 2 * 3600:
        return "30m-2h"
    if elapsed_s < 6 * 3600:
        return "2-6h"
    return ">6h"


def _read_state() -> dict:
    if not STATE_PATH.is_file():
        return {}
    try:
        raw = STATE_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise StateIOError(str(exc)) from exc
    return data if isinstance(data, dict) else {}


def _write_state(down_since: float | None, last_reason: str) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "down_since": down_since,
                "last_reason": last_reason,
                "updated_at": time.time(),
            },
            ensure_ascii=False,
        )
        tmp = STATE_PATH.with_name(STATE_PATH.name + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, STATE_PATH)
    except OSError as exc:
        raise StateIOError(str(exc)) from exc


def _clear_state() -> None:
    if not STATE_PATH.exists():
        return
    try:
        STATE_PATH.unlink()
    except OSError as exc:
        raise StateIOError(str(exc)) from exc


def _process_rows() -> list[dict]:
    ps = (
        "Get-CimInstance Win32_Process | "
        "Select-Object Name, CommandLine | ConvertTo-Json -Compress"
    )
    flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            creationflags=flags,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ProcessEnumError("process enum failed") from exc
    out = (out or "").strip()
    if not out:
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        raise ProcessEnumError("process enum json failed") from exc
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    raise ProcessEnumError("process enum unexpected payload")


def _is_intentional_off() -> bool:
    hud = False
    serve = False
    for row in _process_rows():
        name = str(row.get("Name") or "")
        cmd = str(row.get("CommandLine") or "")
        if _HUD_ONE.match(name) or _HUD_VER.match(name):
            hud = True
        if _PY.match(name) and "jarvis serve" in cmd:
            serve = True
    return (not hud) and (not serve)


def _probe() -> tuple[str, str | None]:
    """Return ('up', wake_on_repr) or ('fail', reason)."""
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=5) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return "fail", "BadPayload"
        if (
            not isinstance(body, dict)
            or body.get("ok") is not True
            or body.get("service") != "jarvis"
        ):
            return "fail", "BadPayload"
        return "up", f"OK wake_on={body.get('wake_on')}"
    except urllib.error.HTTPError:
        return "fail", "HTTPError"
    except TimeoutError:
        return "fail", "Timeout"
    except urllib.error.URLError:
        return "fail", "URLError"
    except Exception as exc:  # noqa: BLE001
        name = type(exc).__name__
        if name in {"timeout", "TimeoutError"}:
            return "fail", "Timeout"
        return "fail", name


def _fingerprint() -> str:
    kind, extra = _probe()
    if kind == "up":
        _clear_state()
        return extra or "OK wake_on=None"
    reason = extra or "unhealthy"
    try:
        intentional_off = _is_intentional_off()
    except ProcessEnumError:
        intentional_off = False
        reason = "enum_failed"
    if intentional_off:
        _clear_state()
        return "OFF"
    now = time.time()
    st = _read_state()
    down_since = st.get("down_since")
    try:
        started = float(down_since) if down_since is not None else None
    except (TypeError, ValueError):
        started = None
    if started is None:
        started = now
        bucket = "<5m"
    else:
        bucket = _bucket(now - started)
    _write_state(started, reason)
    return f"DOWN {reason} t={bucket}"


def main() -> int:
    line = "DOWN internal_error t=<5m"
    try:
        line = _fingerprint()
    except StateIOError:
        line = "WARN state_io"
    except (KeyboardInterrupt, SystemExit):
        line = "DOWN internal_error t=<5m"
        raise
    except Exception:  # noqa: BLE001
        line = "DOWN internal_error t=<5m"
    finally:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
