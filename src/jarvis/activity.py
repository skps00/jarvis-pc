"""Shared helpers for reading SK activity state (sk_activity.json)."""

from __future__ import annotations

import json
import os


def state_path() -> str:
    """LOCALAPPDATA/hermes/state/sk_activity.json"""
    return os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "hermes",
        "state",
        "sk_activity.json",
    )


def load_activity() -> dict:
    """Read sk_activity.json; return {} on any error."""
    try:
        with open(state_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def gaming() -> bool:
    """True when state == 'playing'."""
    return load_activity().get("state") == "playing"


def voice_call() -> bool:
    """True when voice_call flag is set."""
    return bool(load_activity().get("voice_call", False))
