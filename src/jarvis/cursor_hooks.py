"""Install / remove Cursor hooks → Jarvis alert queue."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HOOK_MARKER = "cursor_hook_alert.py"
HOOKS_VERSION = 1
# After SwitchMode/Ask / UIA wait, ignore stop→finished this long.
WAIT_SUPPRESS_S = 180.0


def cursor_dir() -> Path:
    """``~/.cursor`` (Windows: ``%USERPROFILE%\\.cursor``)."""
    return Path.home() / ".cursor"


def hooks_json_path() -> Path:
    return cursor_dir() / "hooks.json"


def hook_script_src() -> Path:
    """Repo script path."""
    return Path(__file__).resolve().parents[2] / "scripts" / "cursor_hook_alert.py"


def alerts_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".jarvis")
    return Path(base) / "Jarvis" / "alerts"


def wait_flag_path() -> Path:
    return alerts_dir() / "hook_wait_until.txt"


def hook_last_fire_path() -> Path:
    return alerts_dir() / "hook_last_fire.txt"


def mark_hook_fired() -> None:
    """Record that a Cursor hook actually ran (for toast Done dedupe)."""
    path = hook_last_fire_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(time.time()), encoding="utf-8")


def hook_fired_recently(*, within_s: float = 30.0) -> bool:
    path = hook_last_fire_path()
    if not path.is_file():
        return False
    try:
        ts = float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    return (time.time() - ts) <= float(within_s)


def mark_waiting(*, seconds: float = WAIT_SUPPRESS_S) -> None:
    """Suppress stop→finished until *seconds* elapse (approval / plan card)."""
    path = wait_flag_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(time.time() + float(seconds)), encoding="utf-8")


def waiting_active() -> bool:
    path = wait_flag_path()
    if not path.is_file():
        return False
    try:
        until = float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    if time.time() < until:
        return True
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
    return False


def clear_waiting() -> None:
    try:
        wait_flag_path().unlink(missing_ok=True)
    except OSError:
        pass


def _python_for_hook() -> Path:
    """Prefer console ``python.exe`` (stdin reliable on Windows hooks).

    ``pythonw`` can break Cursor's Windows hook launcher / stdin pipe.
    Console flash is avoided via ``cmd /c start /b``-style? No — Cursor
    hides hook windows; use ``python.exe -u`` under ``cmd /c``.
    """
    py = Path(sys.executable).resolve()
    if py.name.lower() == "pythonw.exe":
        console = py.with_name("python.exe")
        if console.is_file():
            return console
    return py


def hook_command() -> str:
    """Command string Cursor will spawn for hooks.

    On Windows, wrap with ``cmd /c`` — community-confirmed fix when bare
    quoted exe paths never run (forum: hooks not working on Windows).
    """
    script = hook_script_src()
    py = _python_for_hook()
    if sys.platform == "win32":
        # cmd /c "exe" "script" — paths quoted for spaces.
        return f'cmd /c ""{py}" -u "{script}""'
    return f'"{py}" -u "{script}"'


def _is_ours(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    cmd = str(entry.get("command") or "")
    return HOOK_MARKER in cmd.replace("\\", "/")


def load_hooks() -> dict:
    path = hooks_json_path()
    if not path.is_file():
        return {"version": HOOKS_VERSION, "hooks": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": HOOKS_VERSION, "hooks": {}}
    if not isinstance(data, dict):
        return {"version": HOOKS_VERSION, "hooks": {}}
    data.setdefault("version", HOOKS_VERSION)
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        data["hooks"] = {}
    return data


def save_hooks(data: dict) -> Path:
    path = hooks_json_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def install() -> str:
    """Merge Jarvis stop + preToolUse hooks into ``~/.cursor/hooks.json``."""
    script = hook_script_src()
    if not script.is_file():
        return f"[fail] missing hook script: {script}"
    data = load_hooks()
    hooks = data.setdefault("hooks", {})
    cmd = hook_command()
    entry = {"command": cmd, "loop_limit": None, "timeout": 15}

    for key in ("stop", "preToolUse"):
        items = hooks.get(key)
        if not isinstance(items, list):
            items = []
        items = [e for e in items if not _is_ours(e)]
        # One shared script; Cursor passes hook_event_name / tool_name in JSON.
        items.append(dict(entry))
        hooks[key] = items

    data["hooks"] = hooks
    data["version"] = HOOKS_VERSION
    path = save_hooks(data)
    return (
        f"[ok] Cursor hooks (stop + preToolUse) → {path}\n"
        f"     cmd: {cmd}\n"
        f"     Enable Hooks in Cursor Settings; reload window.\n"
        f"     Windows: uses cmd /c (required for reliable spawn).\n"
        f"     Debug: View → Output → Hooks. AskQuestion may still skip hooks."
    )


def uninstall() -> str:
    """Remove our hook entries (leave other hooks alone)."""
    data = load_hooks()
    hooks = data.get("hooks") or {}
    removed = 0
    for key in ("stop", "preToolUse"):
        items = hooks.get(key)
        if not isinstance(items, list):
            continue
        new_items = [e for e in items if not _is_ours(e)]
        removed += len(items) - len(new_items)
        if new_items:
            hooks[key] = new_items
        else:
            hooks.pop(key, None)
    if removed == 0:
        return "[ok] Jarvis hooks were not installed"
    data["hooks"] = hooks
    path = save_hooks(data)
    return f"[ok] removed {removed} Jarvis hook entr(y/ies) from {path}"


def is_installed() -> bool:
    data = load_hooks()
    hooks = data.get("hooks") or {}
    for key in ("stop", "preToolUse"):
        items = hooks.get(key) or []
        if isinstance(items, list) and any(_is_ours(e) for e in items):
            return True
    return False


def status() -> str:
    data = load_hooks()
    hooks = data.get("hooks") or {}
    bits = []
    for key in ("stop", "preToolUse"):
        items = hooks.get(key) or []
        ours = (
            any(_is_ours(e) for e in items) if isinstance(items, list) else False
        )
        bits.append(f"{key}={'yes' if ours else 'no'}")
    path = hooks_json_path()
    return (
        f"cursor-hooks: {'installed' if is_installed() else 'not installed'}"
        f" ({', '.join(bits)})\n"
        f"hooks.json: {path} ({'exists' if path.is_file() else 'missing'})\n"
        f"script: {hook_script_src()}"
    )
