"""Shared helpers for reading SK activity state (sk_activity.json)."""

from __future__ import annotations

import json
import os
from datetime import datetime


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


def activity_age_s(activity: dict | None = None) -> float | None:
    """Seconds since the JSON ``timestamp``; None when missing/unparsable."""
    act = load_activity() if activity is None else activity
    raw = act.get("timestamp") if isinstance(act, dict) else None
    if not raw:
        return None
    try:
        s = str(raw).strip().replace("Z", "+00:00")
        ts = datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None
    now = datetime.now(ts.tzinfo) if ts.tzinfo is not None else datetime.now()
    return (now - ts).total_seconds()


def signals(activity: dict | None = None) -> dict:
    """Raw decision fields from an activity snapshot (or live load)."""
    act = load_activity() if activity is None else activity
    if not isinstance(act, dict):
        act = {}

    game_names: list[str] = []
    for app in act.get("apps") or []:
        if isinstance(app, dict) and app.get("category") == "game":
            name = app.get("name")
            if name:
                game_names.append(str(name))

    fg = act.get("foreground") if isinstance(act.get("foreground"), dict) else {}
    hay = f"{fg.get('process') or ''} {fg.get('title') or ''}".lower()
    fg_is_game = any(n.lower() in hay for n in game_names)

    idle_raw = act.get("idle_seconds")
    idle: int | None
    try:
        idle = int(idle_raw) if idle_raw is not None else None
    except (TypeError, ValueError):
        idle = None

    return {
        "game_process": bool(game_names),
        "game_names": game_names,
        "idle_seconds": idle,
        "fg_is_game": fg_is_game,
        "fullscreen": bool(act.get("fullscreen", False)),
        "voice_call": bool(act.get("voice_call", False)),
        "state": str(act.get("state") or ""),
        "age_s": activity_age_s(act),
        "v1_gaming": act.get("state") == "playing",
    }
