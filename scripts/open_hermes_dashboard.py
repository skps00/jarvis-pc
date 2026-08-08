"""Start Hermes dashboard in WSL without a console flash; open browser on Windows."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.hermes_bridge import open_dashboard  # noqa: E402


def main() -> int:
    ok, msg = open_dashboard()
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
