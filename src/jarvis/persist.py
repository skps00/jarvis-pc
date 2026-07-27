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


def _guess_process_names(label: str, extra: list[str] | None = None) -> list[str]:
    names: list[str] = []
    if extra:
        names.extend(extra)
    label = (label or "").strip()
    if label and re.match(r"^[A-Za-z0-9][\w .-]*$", label):
        exe = label if label.lower().endswith(".exe") else f"{label}.exe"
        if exe not in names:
            names.append(exe)
    return names


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
    elif ltype == "shell_app" and hint.get("app_id"):
        launch = {
            "type": "shell_app",
            "app_id": str(hint.get("app_id")),
            "process_names": _guess_process_names(candidate.label),
        }
        kind = "app"
        names = [candidate.label]
    elif ltype in ("app_exe", "app_lnk") and hint.get("lnk"):
        lnk = str(hint.get("lnk"))
        launch = {"type": "app_lnk", "lnk": lnk}
        kind = "app"
        names = [candidate.label]
        try:
            from jarvis.hands import _resolve_lnk_target

            target = _resolve_lnk_target(lnk)
            if target and target.name:
                launch["process_names"] = [target.name]
            else:
                launch["process_names"] = _guess_process_names(candidate.label)
        except Exception:
            launch["process_names"] = _guess_process_names(candidate.label)
    elif ltype == "app_exe" and hint.get("exe"):
        exe = Path(str(hint.get("exe")))
        launch = {
            "type": "app_exe",
            "exe": str(exe),
            "process_names": [exe.name],
        }
        kind = "app"
        names = [candidate.label, exe.stem]
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
