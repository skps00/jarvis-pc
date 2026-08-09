#!/usr/bin/env python3

"""One-shot: peek alert queue → TTS → ack.



For Hermes cron ``--no-agent --script`` (gateway ticks ~60s; min schedule 1m).

Prefer ``hermes_alert_poll_loop.py`` for ~2s latency.



Playback prefers in-process Jarvis Piper (``mouth.speak``) so Windows does not

flash a console for ``python.exe`` / ``ffplay``. Hermes subprocess is fallback.

"""



from __future__ import annotations



import json

import os

import shutil

import subprocess

import sys

from pathlib import Path



# jarvis-pc src on path when run from repo; Hermes cron copies under ~/.hermes/scripts

_REPO = Path(__file__).resolve().parents[1]

_SRC = _REPO / "src"

if _SRC.is_dir() and str(_SRC) not in sys.path:

    sys.path.insert(0, str(_SRC))





def _no_window_flags() -> int:

    """Hide console for child processes on Windows."""

    if sys.platform != "win32":

        return 0

    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))





def _speak_jarvis_mouth(phrase: str) -> bool:

    """Same jarvis-high.onnx voice; no console child."""

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

    for name in ("pythonw.exe", "python.exe"):

        py = agent / "venv" / "Scripts" / name

        if py.is_file():

            return py

    return None





def _speak_hermes_subprocess(phrase: str) -> bool:

    """Fallback: Hermes TTS synth + hidden ffplay."""

    hermes_home = Path(

        os.environ.get("HERMES_HOME")

        or (Path(os.environ["LOCALAPPDATA"]) / "hermes")

    )

    agent = hermes_home / "hermes-agent"

    py = _hermes_pythonw()

    if py is None:

        print(f"[fail] no Hermes python under {agent}", file=sys.stderr)

        return False

    os.environ["HERMES_HOME"] = str(hermes_home)

    flags = _no_window_flags()

    code = (

        "import json,os,sys\n"

        f"os.chdir({str(agent)!r})\n"

        "sys.path.insert(0, os.getcwd())\n"

        "from tools.tts_tool import text_to_speech_tool\n"

        f"raw=text_to_speech_tool(text={phrase!r}, provider='piper')\n"

        "print(raw)\n"

    )

    r = subprocess.run(

        [str(py), "-c", code],

        capture_output=True,

        text=True,

        encoding="utf-8",

        errors="replace",

        creationflags=flags,

    )

    if r.returncode != 0:

        print(r.stderr or r.stdout, file=sys.stderr)

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

    p = subprocess.run(

        [ffplay, "-nodisp", "-autoexit", "-loglevel", "error", path],

        check=False,

        creationflags=flags,

    )

    return p.returncode == 0





def _speak_hermes(phrase: str) -> bool:

    """Speak alert phrase (Jarvis Piper in-process, else Hermes subprocess)."""

    if _speak_jarvis_mouth(phrase):

        return True

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


