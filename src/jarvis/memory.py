"""Tiny local memory: last Prism / battlefield / launched PIDs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_MEMORY_PATH = Path.home() / "AppData" / "Roaming" / "Jarvis" / "memory.json"

_DEFAULTS: dict[str, Any] = {
    "last_prism_instance": None,
    "last_battlefield": None,
    "profile_pids": {},
}


def load_memory(path: Path | None = None) -> dict[str, Any]:
    """Return memory dict; missing file yields empty defaults."""
    mem_path = path or DEFAULT_MEMORY_PATH
    if not mem_path.is_file():
        return dict(_DEFAULTS)
    try:
        data = json.loads(mem_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(_DEFAULTS)
    if not isinstance(data, dict):
        return dict(_DEFAULTS)
    for key, val in _DEFAULTS.items():
        data.setdefault(key, dict(val) if isinstance(val, dict) else val)
    if not isinstance(data.get("profile_pids"), dict):
        data["profile_pids"] = {}
    return data


def save_memory(data: dict[str, Any], path: Path | None = None) -> None:
    """Persist memory JSON under %APPDATA%\\Jarvis by default."""
    mem_path = path or DEFAULT_MEMORY_PATH
    mem_path.parent.mkdir(parents=True, exist_ok=True)
    mem_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_profile_pids(profile_id: str, path: Path | None = None) -> list[int]:
    """Return remembered PIDs for a profile (may be stale)."""
    raw = load_memory(path).get("profile_pids") or {}
    vals = raw.get(profile_id) or []
    out: list[int] = []
    for x in vals:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            continue
    return out


def set_profile_pids(
    profile_id: str, pids: list[int], path: Path | None = None
) -> None:
    """Replace remembered PIDs for profile; empty list deletes entry."""
    data = load_memory(path)
    store = data.setdefault("profile_pids", {})
    clean = [int(p) for p in pids if int(p) > 0]
    if clean:
        store[profile_id] = clean
    else:
        store.pop(profile_id, None)
    save_memory(data, path)


def clear_profile_pids(profile_id: str, path: Path | None = None) -> None:
    """Drop remembered PIDs for one profile."""
    set_profile_pids(profile_id, [], path)
