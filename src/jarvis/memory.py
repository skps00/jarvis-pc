"""Tiny local memory: last Prism instance and last battlefield profile id."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_MEMORY_PATH = Path.home() / "AppData" / "Roaming" / "Jarvis" / "memory.json"


def load_memory(path: Path | None = None) -> dict[str, Any]:
    """Return memory dict; missing file yields empty defaults."""
    mem_path = path or DEFAULT_MEMORY_PATH
    if not mem_path.is_file():
        return {"last_prism_instance": None, "last_battlefield": None}
    try:
        data = json.loads(mem_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"last_prism_instance": None, "last_battlefield": None}
    if not isinstance(data, dict):
        return {"last_prism_instance": None, "last_battlefield": None}
    data.setdefault("last_prism_instance", None)
    data.setdefault("last_battlefield", None)
    return data


def save_memory(data: dict[str, Any], path: Path | None = None) -> None:
    """Persist memory JSON under %APPDATA%\\Jarvis by default."""
    mem_path = path or DEFAULT_MEMORY_PATH
    mem_path.parent.mkdir(parents=True, exist_ok=True)
    mem_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
