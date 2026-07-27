"""Windows Startup folder toggle for `jarvis serve`."""

from __future__ import annotations

import sys
from pathlib import Path


STARTUP_NAME = "JARVIS.cmd"


def startup_dir() -> Path:
    """Return the current user's Windows Startup folder."""
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def startup_path() -> Path:
    """Path to the JARVIS startup script."""
    return startup_dir() / STARTUP_NAME


def is_enabled() -> bool:
    """True if Startup script exists."""
    return startup_path().is_file()


def enable() -> str:
    """
    Write a Startup .cmd that launches `python -m jarvis serve`.

    Uses the same Python interpreter currently running Jarvis.
    """
    if sys.platform != "win32":
        return "僅支援 Windows 開機自啟"
    folder = startup_dir()
    folder.mkdir(parents=True, exist_ok=True)
    py = Path(sys.executable).resolve()
    # /B keeps a console briefly so early errors are visible; user can hide later
    body = (
        "@echo off\r\n"
        f'start "" "{py}" -m jarvis serve\r\n'
    )
    path = startup_path()
    path.write_text(body, encoding="utf-8")
    return f"已啟用開機自啟：{path}"


def disable() -> str:
    """Remove Startup script if present."""
    path = startup_path()
    if path.is_file():
        path.unlink()
        return f"已關閉開機自啟（已刪：{path}）"
    return "開機自啟本來就未開啟"
