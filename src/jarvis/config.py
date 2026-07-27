"""Load and validate Jarvis profile registry from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILES_PATH = REPO_ROOT / "config" / "profiles.yaml"
EXAMPLE_PROFILES_PATH = REPO_ROOT / "config" / "profiles.example.yaml"


@dataclass
class Profile:
    """One launchable target in the whitelist registry."""

    id: str
    display_name: str
    kind: str
    enabled: bool
    names: list[str]
    locale_hints: list[str]
    launch: dict[str, Any]
    restore: dict[str, Any] = field(default_factory=dict)
    confirm: str = "auto"
    use_as_default_mc: bool = False


@dataclass
class Registry:
    """Parsed profiles.yaml plus matching policy tables."""

    profiles: dict[str, Profile]
    open_verbs: list[str]
    name_aliases: dict[str, str]
    restore_phrases: list[str]
    target_modifiers: list[str]
    verb_kind_limits: dict[str, list[str]]
    match_policy: dict[str, Any]
    allow_bare_name: bool
    defaults: dict[str, Any]
    path: Path


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def load_registry(path: Path | None = None) -> Registry:
    """Load profiles YAML. Prefers profiles.yaml, falls back to example."""
    cfg_path = path or DEFAULT_PROFILES_PATH
    if not cfg_path.is_file():
        cfg_path = EXAMPLE_PROFILES_PATH
    if not cfg_path.is_file():
        raise FileNotFoundError(f"No profiles file at {DEFAULT_PROFILES_PATH}")

    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    profiles: dict[str, Profile] = {}
    for item in raw.get("profiles") or []:
        launch = dict(item.get("launch") or {})
        match = item.get("match") or {}
        pid = str(item["id"])
        profiles[pid] = Profile(
            id=pid,
            display_name=str(item.get("display_name") or pid),
            kind=str(item.get("kind") or "app"),
            enabled=bool(item.get("enabled", True)),
            names=_as_str_list(match.get("names")),
            locale_hints=_as_str_list(match.get("locale_hints")),
            launch=launch,
            restore=dict(item.get("restore") or {}),
            confirm=str(item.get("confirm") or "auto"),
            use_as_default_mc=bool(launch.get("use_as_default_mc", False)),
        )

    aliases = {str(k).lower(): str(v) for k, v in (raw.get("name_aliases") or {}).items()}
    return Registry(
        profiles=profiles,
        open_verbs=_as_str_list(raw.get("open_verbs")),
        name_aliases=aliases,
        restore_phrases=_as_str_list(raw.get("restore_phrases")),
        target_modifiers=_as_str_list(raw.get("target_modifiers")),
        verb_kind_limits={
            str(k).lower(): _as_str_list(v) for k, v in (raw.get("verb_kind_limits") or {}).items()
        },
        match_policy=dict(raw.get("match_policy") or {}),
        allow_bare_name=bool(raw.get("allow_bare_name", False)),
        defaults=dict(raw.get("defaults") or {}),
        path=cfg_path,
    )
