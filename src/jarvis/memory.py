"""Tiny local memory: last Prism / battlefield / launched PIDs / STT aliases."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEFAULT_MEMORY_PATH = Path.home() / "AppData" / "Roaming" / "Jarvis" / "memory.json"

_DEFAULTS: dict[str, Any] = {
    "last_prism_instance": None,
    "last_battlefield": None,
    "profile_pids": {},
    "stt_aliases": {},
}
_MAX_STT_ALIASES = 300


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
    if not isinstance(data.get("stt_aliases"), dict):
        data["stt_aliases"] = {}
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


def _alias_key(raw: str) -> str:
    return re.sub(r"\s+", "", (raw or "").strip().lower())


# Shell／Hermes 句唔好當 STT alias（否則 rm 路徑會被學成「執行」）
_SHELLISH = re.compile(
    r"(/tmp/|/mnt/|\\|-\s*rf\b|\brm\s|curl\s|wget\s|https?://|`|\|)",
    re.I,
)


def _looks_shellish(raw: str) -> bool:
    t = raw or ""
    if _SHELLISH.search(t):
        return True
    # long paste with path-ish punctuation
    if len(t) >= 36 and ("/" in t or "：" in t or ":" in t):
        return True
    return False


def get_stt_alias(
    raw: str,
    path: Path | None = None,
    *,
    static: dict[str, str] | None = None,
) -> str | None:
    """Look up STT alias: memory first, then static (profiles.yaml)."""
    if _looks_shellish(raw):
        return None
    key = _alias_key(raw)
    if len(key) < 2:
        return None
    store = load_memory(path).get("stt_aliases") or {}
    val = store.get(key)
    if val:
        return str(val).strip()
    if static:
        # keys may already be normalized, or raw yaml keys
        hit = static.get(key) or static.get(raw.strip().lower())
        if hit:
            return str(hit).strip()
        for sk, sv in static.items():
            if _alias_key(sk) == key:
                return str(sv).strip()
    return None


def list_stt_aliases(path: Path | None = None) -> dict[str, str]:
    """Return copy of learned stt_aliases (insertion order)."""
    store = load_memory(path).get("stt_aliases") or {}
    if not isinstance(store, dict):
        return {}
    return {str(k): str(v) for k, v in store.items()}


def learn_stt_alias(
    raw: str,
    canonical: str,
    path: Path | None = None,
) -> bool:
    """
    Remember garbled → canonical app label.

    Returns True if stored. Skips no-ops / too-short / identical keys.
    """
    if _looks_shellish(raw) or _looks_shellish(canonical):
        return False
    key = _alias_key(raw)
    label = (canonical or "").strip()
    if len(key) < 2 or len(label) < 2:
        return False
    if len(key) > 48:
        return False
    # bare verbs / Hermes filler — not app labels
    if _alias_key(label) in {
        "執行",
        "运行",
        "運行",
        "run",
        "execute",
        "ok",
        "yes",
        "no",
    }:
        return False
    if key == _alias_key(label):
        return False
    data = load_memory(path)
    store = data.setdefault("stt_aliases", {})
    if not isinstance(store, dict):
        store = {}
        data["stt_aliases"] = store
    # refresh insertion order (move to end)
    store.pop(key, None)
    store[key] = label
    while len(store) > _MAX_STT_ALIASES:
        oldest = next(iter(store))
        store.pop(oldest, None)
    save_memory(data, path)
    return True


def clear_stt_aliases(path: Path | None = None) -> None:
    """Test helper: wipe learned aliases."""
    data = load_memory(path)
    data["stt_aliases"] = {}
    save_memory(data, path)
