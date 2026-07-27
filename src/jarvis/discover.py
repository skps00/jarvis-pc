"""Discover candidates for unknown `open xxx` (Start Menu / Desktop / installed / Steam / Prism)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from jarvis.config import Registry

# Get-StartApps is ~1s; cache across voice turns
_START_APPS_CACHE: list[tuple[str, str]] | None = None
_START_APPS_TS = 0.0
_START_APPS_TTL = 300.0
_LNK_STEMS_CACHE: list[str] | None = None
_LNK_STEMS_TS = 0.0

_SOURCE_RANK = {
    "start_menu": 0,
    "desktop": 1,
    "local_programs": 2,
    "start_apps": 3,
    "steam": 4,
    "prism": 5,
}

_SKIP_EXE = re.compile(
    r"(uninstall|unins\d*|setup|update|updater|crash|helper|elevate|install)",
    re.I,
)


@dataclass
class Candidate:
    """One discover hit the user can confirm."""

    label: str
    kind: str  # start_menu | desktop | local_programs | start_apps | steam | prism
    launch_hint: dict
    score: float = 0.0


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s).lower()


def _score_name(query: str, name: str) -> float:
    from jarvis.app_index import pair_score

    return pair_score(query, name)


def discover_candidates(query: str, registry: Registry, *, limit: int = 5) -> list[Candidate]:
    """Search local sources for apps/instances matching query."""
    hits: list[Candidate] = []
    hits.extend(_from_start_menu(query))
    hits.extend(_from_desktop(query))
    hits.extend(_from_local_programs(query))
    hits.extend(_from_start_apps(query))
    hits.extend(_from_steam(query))
    hits.extend(_from_prism(query, registry))
    hits.sort(
        key=lambda c: (-c.score, _SOURCE_RANK.get(c.kind, 99)),
    )
    # dedupe by label — keep best score / preferred source
    seen: set[str] = set()
    out: list[Candidate] = []
    for c in hits:
        key = _norm(c.label)
        if key in seen or c.score < 50:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= limit:
            break
    return out


def _lnk_candidates(query: str, roots: list[Path], kind: str) -> list[Candidate]:
    out: list[Candidate] = []
    for root in roots:
        if not root.is_dir():
            continue
        try:
            lnks = root.rglob("*.lnk")
        except OSError:
            continue
        for lnk in lnks:
            score = _score_name(query, lnk.stem)
            if score < 50:
                continue
            out.append(
                Candidate(
                    label=lnk.stem,
                    kind=kind,
                    launch_hint={"type": "app_exe", "lnk": str(lnk)},
                    score=score,
                )
            )
    return out


def _from_start_menu(query: str) -> list[Candidate]:
    roots = [
        Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    ]
    return _lnk_candidates(query, roots, "start_menu")


def _from_desktop(query: str) -> list[Candidate]:
    roots = [
        Path.home() / "Desktop",
        Path.home() / "OneDrive" / "Desktop",
        Path(r"C:\Users\Public\Desktop"),
    ]
    return _lnk_candidates(query, roots, "desktop")


def _from_local_programs(query: str) -> list[Candidate]:
    """Shallow scan %LOCALAPPDATA%\\Programs for matching .exe."""
    root = Path.home() / "AppData" / "Local" / "Programs"
    if not root.is_dir():
        return []
    out: list[Candidate] = []
    try:
        for exe in root.rglob("*.exe"):
            try:
                rel = exe.relative_to(root)
            except ValueError:
                continue
            if len(rel.parts) > 4:
                continue
            if _SKIP_EXE.search(exe.stem):
                continue
            stem_score = _score_name(query, exe.stem)
            folder = rel.parts[0] if rel.parts else ""
            folder_score = _score_name(query, folder) if folder else 0.0
            score = max(stem_score, folder_score)
            if score < 50:
                continue
            label = exe.stem if stem_score >= folder_score else folder
            out.append(
                Candidate(
                    label=label,
                    kind="local_programs",
                    launch_hint={"type": "app_exe", "exe": str(exe)},
                    score=score,
                )
            )
    except OSError:
        return out
    return out


def _load_start_apps() -> list[tuple[str, str]]:
    """Return [(Name, AppID), ...] via Get-StartApps (cached)."""
    global _START_APPS_CACHE, _START_APPS_TS
    now = time.time()
    if _START_APPS_CACHE is not None and (now - _START_APPS_TS) < _START_APPS_TTL:
        return _START_APPS_CACHE
    if sys.platform != "win32":
        _START_APPS_CACHE = []
        _START_APPS_TS = now
        return _START_APPS_CACHE
    try:
        raw = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json -Compress",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        _START_APPS_CACHE = []
        _START_APPS_TS = now
        return _START_APPS_CACHE
    raw = (raw or "").strip()
    if not raw:
        rows: list = []
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = []
        if isinstance(data, dict):
            rows = [data]
        elif isinstance(data, list):
            rows = data
        else:
            rows = []
    parsed: list[tuple[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        name = str(item.get("Name") or "").strip()
        app_id = str(item.get("AppID") or "").strip()
        if name and app_id:
            parsed.append((name, app_id))
    _START_APPS_CACHE = parsed
    _START_APPS_TS = now
    return parsed


def clear_start_apps_cache() -> None:
    """Test helper: drop Get-StartApps + lnk stem caches."""
    global _START_APPS_CACHE, _START_APPS_TS, _LNK_STEMS_CACHE, _LNK_STEMS_TS
    _START_APPS_CACHE = None
    _START_APPS_TS = 0.0
    _LNK_STEMS_CACHE = None
    _LNK_STEMS_TS = 0.0


def _lnk_stem_roots() -> list[Path]:
    return [
        Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
        Path.home() / "Desktop",
        Path.home() / "OneDrive" / "Desktop",
        Path(r"C:\Users\Public\Desktop"),
    ]


def _cached_lnk_stems() -> list[str]:
    """Start Menu + Desktop shortcut names (cached)."""
    global _LNK_STEMS_CACHE, _LNK_STEMS_TS
    now = time.time()
    if _LNK_STEMS_CACHE is not None and (now - _LNK_STEMS_TS) < _START_APPS_TTL:
        return _LNK_STEMS_CACHE
    stems: list[str] = []
    for root in _lnk_stem_roots():
        if not root.is_dir():
            continue
        try:
            for lnk in root.rglob("*.lnk"):
                if lnk.stem:
                    stems.append(lnk.stem)
        except OSError:
            continue
    _LNK_STEMS_CACHE = stems
    _LNK_STEMS_TS = now
    return stems


def iter_installed_labels() -> list[str]:
    """All discoverable app display names for fuzzy／粵拼 index."""
    labels: list[str] = []
    for name, _app_id in _load_start_apps():
        labels.append(name)
    labels.extend(_cached_lnk_stems())
    root = Path.home() / "AppData" / "Local" / "Programs"
    if root.is_dir():
        try:
            for child in root.iterdir():
                if child.is_dir():
                    labels.append(child.name)
        except OSError:
            pass
    return labels


def _from_start_apps(query: str) -> list[Candidate]:
    """Windows Start apps list (classic + Store/UWP)."""
    out: list[Candidate] = []
    for name, app_id in _load_start_apps():
        score = _score_name(query, name)
        if score < 50:
            continue
        out.append(
            Candidate(
                label=name,
                kind="start_apps",
                launch_hint={"type": "shell_app", "app_id": app_id},
                score=score,
            )
        )
    return out


def _from_steam(query: str) -> list[Candidate]:
    """Parse steam appmanifest_*.acf for app names (best-effort)."""
    libraries = [
        Path(r"C:\Program Files (x86)\Steam\steamapps"),
        Path(r"C:\Program Files\Steam\steamapps"),
        Path.home() / "Steam" / "steamapps",
    ]
    out: list[Candidate] = []
    for lib in libraries:
        if not lib.is_dir():
            continue
        for acf in lib.glob("appmanifest_*.acf"):
            try:
                text = acf.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            m_name = re.search(r'"name"\s+"([^"]+)"', text)
            m_id = re.search(r'"appid"\s+"(\d+)"', text)
            if not m_name or not m_id:
                continue
            name, app_id = m_name.group(1), m_id.group(1)
            score = _score_name(query, name)
            if score < 50:
                continue
            out.append(
                Candidate(
                    label=name,
                    kind="steam",
                    launch_hint={"type": "steam_app", "app_id": app_id},
                    score=score,
                )
            )
    return out


def _from_prism(query: str, registry: Registry) -> list[Candidate]:
    """List sibling instances next to a known prism_exe."""
    out: list[Candidate] = []
    prism_exe: Path | None = None
    for p in registry.profiles.values():
        if p.launch.get("type") == "prism_instance":
            exe = Path(str(p.launch.get("prism_exe") or ""))
            if exe.is_file():
                prism_exe = exe
                break
    if prism_exe is None:
        return out
    # Prism portable: .../instances/<id>/
    root = prism_exe.parent
    instances = root / "instances"
    if not instances.is_dir():
        # some builds keep instances under %appdata%
        alt = Path.home() / "AppData" / "Roaming" / "PrismLauncher" / "instances"
        instances = alt if alt.is_dir() else instances
    if not instances.is_dir():
        return out
    for folder in instances.iterdir():
        if not folder.is_dir():
            continue
        name = folder.name
        score = _score_name(query, name)
        # also check instance.cfg name=
        cfg = folder / "instance.cfg"
        display = name
        if cfg.is_file():
            try:
                cfg_text = cfg.read_text(encoding="utf-8", errors="ignore")
                m = re.search(r"^name=(.+)$", cfg_text, re.M)
                if m:
                    display = m.group(1).strip()
                    score = max(score, _score_name(query, display))
            except OSError:
                pass
        if score < 50:
            continue
        out.append(
            Candidate(
                label=display,
                kind="prism",
                launch_hint={
                    "type": "prism_instance",
                    "prism_exe": str(prism_exe),
                    "instance_id": name,
                },
                score=score,
            )
        )
    return out
