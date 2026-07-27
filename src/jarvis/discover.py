"""Discover candidates for unknown `open xxx` (Start Menu / Steam / Prism)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from jarvis.config import Registry


@dataclass
class Candidate:
    """One discover hit the user can confirm."""

    label: str
    kind: str  # start_menu | steam | prism
    launch_hint: dict
    score: float = 0.0


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s).lower()


def _score_name(query: str, name: str) -> float:
    q, n = _norm(query), _norm(name)
    if not q or not n:
        return 0.0
    if q == n:
        return 100.0
    if q in n or n in q:
        return 80.0 + min(len(q), 10)
    # token overlap
    return 0.0


def discover_candidates(query: str, registry: Registry, *, limit: int = 5) -> list[Candidate]:
    """Search local sources for apps/instances matching query."""
    hits: list[Candidate] = []
    hits.extend(_from_start_menu(query))
    hits.extend(_from_steam(query))
    hits.extend(_from_prism(query, registry))
    hits.sort(key=lambda c: c.score, reverse=True)
    # dedupe by label
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


def _from_start_menu(query: str) -> list[Candidate]:
    roots = [
        Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    ]
    out: list[Candidate] = []
    for root in roots:
        if not root.is_dir():
            continue
        for lnk in root.rglob("*.lnk"):
            score = _score_name(query, lnk.stem)
            if score < 50:
                continue
            out.append(
                Candidate(
                    label=lnk.stem,
                    kind="start_menu",
                    launch_hint={"type": "app_exe", "lnk": str(lnk)},
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
