#!/usr/bin/env python3
"""One-shot: peek alert queue → TTS → ack.

For Hermes cron ``--no-agent --script`` (gateway ticks ~60s; min schedule 1m).
Prefer ``hermes_alert_poll_loop.py`` for ~1s latency.

``alert_tts=hermes`` → Hermes TTS subprocess only (never Piper mouth).
``alert_tts=piper`` → in-process Jarvis mouth.
``alert_tts=off`` → ack without speaking.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# jarvis-pc src on path when run from repo; Hermes cron copies under ~/.hermes/scripts
_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_TTS_TIMEOUT_S = 60.0


def _no_window_flags() -> int:
    """Hide console for child processes on Windows."""
    if sys.platform != "win32":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))


def _alert_tts_mode() -> str:
    try:
        from jarvis.settings import load_settings

        return str(getattr(load_settings(), "alert_tts", "hermes") or "hermes").lower()
    except Exception:
        return "hermes"


def _kill_process_tree(pid: int) -> None:
    """Windows: taskkill /F /T. Else: terminate then kill."""
    if pid <= 0:
        return
    flags = _no_window_flags()
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            creationflags=flags,
            check=False,
        )
        return
    try:
        os.kill(pid, 15)
    except OSError:
        return
    time.sleep(0.2)
    try:
        os.kill(pid, 9)
    except OSError:
        pass


def _run_hidden(
    argv: list[str],
    *,
    timeout_s: float = _TTS_TIMEOUT_S,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Popen + wait; on timeout ``taskkill /F /T`` the whole tree (ffplay grandchildren)."""
    flags = _no_window_flags()
    proc = subprocess.Popen(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=flags,
    )
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _kill_process_tree(proc.pid)
        try:
            out, err = proc.communicate(timeout=5)
        except Exception:
            out, err = "", ""
        return subprocess.CompletedProcess(
            argv, returncode=124, stdout=out or "", stderr=err or "timeout"
        )
    return subprocess.CompletedProcess(
        argv, returncode=int(proc.returncode or 0), stdout=out or "", stderr=err or ""
    )


def _speak_jarvis_mouth(phrase: str) -> bool:
    """Jarvis Piper in-process (alert_tts=piper only)."""
    try:
        from jarvis.mouth import available, speak
    except Exception:
        return False
    if not available():
        return False
    return bool(speak(phrase, blocking=True, force=True))


def _hermes_pythonw() -> Path | None:
    hermes_home = Path(
        os.environ.get("HERMES_HOME")
        or (Path(os.environ["LOCALAPPDATA"]) / "hermes")
    )
    agent = hermes_home / "hermes-agent"
    # pythonw only — never python.exe (flash risk even with CREATE_NO_WINDOW)
    py = agent / "venv" / "Scripts" / "pythonw.exe"
    if py.is_file():
        return py
    return None


def _speak_hermes_subprocess(phrase: str) -> bool:
    """Hermes TTS synth + hidden ffplay / sounddevice (60s hard timeout)."""
    hermes_home = Path(
        os.environ.get("HERMES_HOME")
        or (Path(os.environ["LOCALAPPDATA"]) / "hermes")
    )
    agent = hermes_home / "hermes-agent"
    py = _hermes_pythonw()
    if py is None:
        print(f"[fail] no Hermes pythonw under {agent}", file=sys.stderr)
        return False
    os.environ["HERMES_HOME"] = str(hermes_home)
    code = (
        "import json,os,sys\n"
        f"os.chdir({str(agent)!r})\n"
        "sys.path.insert(0, os.getcwd())\n"
        "from tools.tts_tool import text_to_speech_tool\n"
        f"raw=text_to_speech_tool(text={phrase!r}, provider='piper')\n"
        "print(raw)\n"
    )
    r = _run_hidden([str(py), "-c", code], timeout_s=_TTS_TIMEOUT_S, capture=True)
    if r.returncode != 0:
        print(r.stderr or r.stdout or f"exit {r.returncode}", file=sys.stderr)
        return False
    line = (r.stdout or "").strip().splitlines()[-1] if r.stdout else ""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        print(r.stdout, file=sys.stderr)
        return False
    path = data.get("file_path")
    if not data.get("success") or not path:
        print(line, file=sys.stderr)
        return False
    # Prefer sounddevice for wav — no ffplay console
    if str(path).lower().endswith(".wav"):
        try:
            import wave

            import numpy as np
            import sounddevice as sd

            with wave.open(str(path), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                sr = wf.getframerate()
            sd.play(audio, samplerate=sr)
            sd.wait()
            return True
        except Exception:
            pass
    ffplay = shutil.which("ffplay")
    if not ffplay:
        cand = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "WinGet" / "Packages"
        hits = (
            list(cand.glob("Gyan.FFmpeg*/ffmpeg-*/bin/ffplay.exe"))
            if cand.is_dir()
            else []
        )
        ffplay = str(hits[0]) if hits else ""
    if not ffplay:
        print("[fail] ffplay not on PATH", file=sys.stderr)
        return False
    p = _run_hidden(
        [
            ffplay,
            "-nodisp",
            "-autoexit",
            "-nostats",
            "-hide_banner",
            "-loglevel",
            "error",
            path,
        ],
        timeout_s=_TTS_TIMEOUT_S,
        capture=False,
    )
    return p.returncode == 0


def _speak_hermes(phrase: str) -> bool:
    """Dispatch by ``alert_tts`` setting (hermes | piper | off)."""
    mode = _alert_tts_mode()
    if mode == "off":
        return True
    if mode == "piper":
        return _speak_jarvis_mouth(phrase)
    # hermes (default): Hermes TTS only — never Piper first
    return _speak_hermes_subprocess(phrase)


def main() -> int:
    from jarvis.alert_store import AlertStore

    st = AlertStore()
    row = st.peek(lease_s=60.0)
    if row is None:
        return 0  # silent tick
    ok = _speak_hermes(row.phrase)
    if ok:
        st.ack(row.id)
        return 0
    print(f"[fail] speak {row.id[:8]}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
