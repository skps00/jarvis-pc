"""Hands MC already-running helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.hands import _cmdline_matches_instance


def test_cmdline_matches_instance():
    iid = "No_Flesh_Within_Chest-1.0.2-DIM"
    assert _cmdline_matches_instance(
        r'javaw -Djava.library.path=C:\instances\No_Flesh_Within_Chest-1.0.2-DIM\natives',
        iid,
    )
    assert not _cmdline_matches_instance("javaw -jar other.jar", iid)


if __name__ == "__main__":
    test_cmdline_matches_instance()
    print("ok")
