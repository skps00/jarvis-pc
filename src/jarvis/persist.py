"""Persist a confirmed Discover candidate into profiles.yaml."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from jarvis.config import DEFAULT_PROFILES_PATH
from jarvis.discover import Candidate


def _slug(label: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", label.strip()).strip("-").lower()
    return (s or "app")[:40]


def commit_candidate(
    candidate: Candidate,
    path: Path | None = None,
) -> str:
    """
    Append a new enabled profile and return its id.

    Overwrites profiles.yaml (local, gitignored). Raises if id collides hard.
    """
    cfg_path = path or DEFAULT_PROFILES_PATH
    if not cfg_path.is_file():
        raise FileNotFoundError(f"找不到 {cfg_path}（請先有 profiles.yaml）")

    raw: dict[str, Any] = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    profiles = list(raw.get("profiles") or [])
    existing_ids = {str(p.get("id")) for p in profiles}
    base = _slug(candidate.label)
    pid = base
    n = 2
    while pid in existing_ids:
        pid = f"{base}-{n}"
        n += 1

    hint = candidate.launch_hint
    ltype = str(hint.get("type") or "")
    if ltype == "steam_app":
        launch = {"type": "steam_app", "app_id": str(hint.get("app_id"))}
        kind = "game"
        names = [candidate.label]
    elif ltype == "prism_instance":
        launch = {
            "type": "prism_instance",
            "prism_exe": str(hint.get("prism_exe")),
            "instance_id": str(hint.get("instance_id")),
        }
        kind = "launcher_instance"
        names = [candidate.label, str(hint.get("instance_id"))]
    elif ltype == "app_exe" and hint.get("lnk"):
        launch = {"type": "app_lnk", "lnk": str(hint.get("lnk"))}
        kind = "app"
        names = [candidate.label]
    else:
        raise ValueError(f"未支援 discover launch：{hint}")

    profiles.append(
        {
            "id": pid,
            "display_name": candidate.label,
            "kind": kind,
            "enabled": True,
            "match": {"names": names},
            "launch": launch,
            "restore": {"role": "aux", "monitor": "primary"},
        }
    )
    raw["profiles"] = profiles
    cfg_path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return pid
