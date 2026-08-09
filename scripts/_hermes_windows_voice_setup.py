#!/usr/bin/env python3
"""After Windows native Hermes install: voice/wake extras + mic-stable config."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

LOCAL = Path(os.environ["LOCALAPPDATA"]) / "hermes"
AGENT = LOCAL / "hermes-agent"
CFG = LOCAL / "config.yaml"
ENV = LOCAL / ".env"


def main() -> int:
    if not AGENT.is_dir():
        print(f"MISSING {AGENT} — wait for install.ps1 to finish")
        return 2
    py = AGENT / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        # uv venv layout variants
        for cand in (
            AGENT / "venv" / "Scripts" / "python.exe",
            LOCAL / "bin" / "python.exe",
        ):
            if cand.is_file():
                py = cand
                break
        else:
            print("NO venv python yet")
            return 3
    print("python", py)
    uv = LOCAL / "bin" / "uv.exe"
    # voice + wake via uv (Hermes Windows installer; pip may be missing)
    if uv.is_file():
        subprocess.check_call(
            [
                str(uv),
                "pip",
                "install",
                "--python",
                str(py),
                "-e",
                f"{AGENT}[voice]",
                "-e",
                f"{AGENT}[wake]",
            ],
            cwd=str(AGENT),
        )
    else:
        subprocess.check_call(
            [str(py), "-m", "ensurepip", "--upgrade"],
            cwd=str(AGENT),
        )
        subprocess.check_call(
            [str(py), "-m", "pip", "install", "-e", ".[voice]", "-e", ".[wake]"],
            cwd=str(AGENT),
        )
    # audio check
    subprocess.check_call(
        [
            str(py),
            "-c",
            "import sounddevice as sd; ds=sd.query_devices(); "
            "print('devices', len(ds)); "
            "print('default', sd.default.device); "
            "[print(i, d['name'], 'in', d['max_input_channels'], 'out', d['max_output_channels']) "
            "for i,d in enumerate(ds) if d['max_input_channels'] or d['max_output_channels']]",
        ]
    )
    block = """
# --- jarvis-pc: Windows native mic (stable) ---
wake_word:
  enabled: true
  provider: openwakeword
  phrase: "hey jarvis"
  capture: local
  surface: auto
  openwakeword:
    model: hey_jarvis

voice:
  barge_in: true
  auto_tts: true

stt:
  provider: local
  local:
    model: base

tts:
  provider: edge
  edge:
    voice: "en-US-AriaNeural"
"""
    if CFG.is_file():
        text = CFG.read_text(encoding="utf-8")
        bak = CFG.with_suffix(".yaml.bak-jarvis-win")
        if not bak.exists():
            bak.write_text(text, encoding="utf-8")
        if "barge_in:" not in text or "hey_jarvis" not in text:
            if not text.endswith("\n"):
                text += "\n"
            CFG.write_text(text + block, encoding="utf-8")
            print("appended voice/wake to", CFG)
        else:
            # force capture local
            if "capture: client" in text:
                text = text.replace("capture: client", "capture: local")
                CFG.write_text(text, encoding="utf-8")
                print("set capture: local")
            else:
                print("config already has voice/wake")
    else:
        CFG.write_text(block.lstrip(), encoding="utf-8")
        print("wrote new", CFG)

    # copy .env from WSL if Windows missing keys
    wsl_env = Path(r"\\wsl$\Ubuntu\home\skps9\.hermes\.env")
    # try common distro names via wslpath through subprocess
    if not ENV.is_file():
        try:
            out = subprocess.check_output(
                ["wsl", "-e", "bash", "-lc", "cat ~/.hermes/.env"],
                text=True,
            )
            ENV.write_text(out, encoding="utf-8")
            print("copied .env from WSL")
        except Exception as exc:
            print("could not copy .env:", exc)
    else:
        print(".env already exists")
    print("OK — use NEW PowerShell: hermes chat  then /voice on /wake on")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
