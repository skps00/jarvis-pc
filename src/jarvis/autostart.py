"""Windows Startup folder toggle for `jarvis serve`."""

from __future__ import annotations

import sys
from pathlib import Path


STARTUP_NAME = "JARVIS.vbs"
_LEGACY_CMD = "JARVIS.cmd"


def startup_dir() -> Path:
    """Return the current user's Windows Startup folder."""
    return (
        Path.home()
        / "AppData"
        / "Roaming"
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
    )


def startup_path() -> Path:
    """Path to the JARVIS startup script (silent VBS)."""
    return startup_dir() / STARTUP_NAME


def legacy_cmd_path() -> Path:
    """Old console Startup script (shows CMD) — remove on enable/disable."""
    return startup_dir() / _LEGACY_CMD


def is_enabled() -> bool:
    """True if silent VBS or legacy .cmd is present."""
    return startup_path().is_file() or legacy_cmd_path().is_file()


def has_legacy_cmd() -> bool:
    """True if old JARVIS.cmd still in Startup (will flash console)."""
    return legacy_cmd_path().is_file()


def _pythonw() -> Path:
    """Prefer pythonw.exe beside current interpreter (no console)."""
    py = Path(sys.executable).resolve()
    if py.name.lower() == "python.exe":
        pyw = py.with_name("pythonw.exe")
        if pyw.is_file():
            return pyw
    return py


def _workdir() -> Path:
    """Repo root when editable (src/jarvis/…); else cwd."""
    here = Path(__file__).resolve()
    # …/jarvis-pc/src/jarvis/autostart.py → parents[2] = repo
    if len(here.parents) >= 3 and (here.parents[2] / "pyproject.toml").is_file():
        return here.parents[2]
    return Path.cwd()


def _remove_legacy_cmd() -> None:
    legacy = legacy_cmd_path()
    if legacy.is_file():
        legacy.unlink()


def enable() -> str:
    """
    Write a Startup .vbs that launches `pythonw -m jarvis serve` with no window.

    Removes legacy JARVIS.cmd if present (that one flashed a console).
    """
    if sys.platform != "win32":
        return "僅支援 Windows 開機自啟"
    folder = startup_dir()
    folder.mkdir(parents=True, exist_ok=True)
    had_legacy = has_legacy_cmd()
    _remove_legacy_cmd()
    py = _pythonw()
    cwd = _workdir()
    # VBS: double any " inside paths
    py_q = str(py).replace('"', '""')
    cwd_q = str(cwd).replace('"', '""')
    body = (
        'Set sh = CreateObject("WScript.Shell")\n'
        f'sh.CurrentDirectory = "{cwd_q}"\n'
        f'sh.Run """{py_q}"" -m jarvis serve", 0, False\n'
    )
    path = startup_path()
    # ASCII-only VBS; newline=\r\n for WScript
    path.write_text(body, encoding="utf-8", newline="\r\n")
    note = "（已清舊 .cmd）" if had_legacy else ""
    return f"已啟用開機自啟（無黑窗）{note}：{path}"


def disable() -> str:
    """Remove Startup VBS and legacy .cmd if present."""
    path = startup_path()
    had_vbs = path.is_file()
    had_cmd = has_legacy_cmd()
    _remove_legacy_cmd()
    if path.is_file():
        path.unlink()
    if had_vbs or had_cmd:
        return f"已關閉開機自啟（已清 Startup 腳本）"
    return "開機自啟本來就未開啟"
