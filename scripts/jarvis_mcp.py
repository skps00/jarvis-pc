#!/usr/bin/env python3
"""Launch Jarvis alerts HTTP MCP (loopback + Bearer token).

Usage::

    python scripts/jarvis_mcp.py
    # or: jarvis-mcp

Hermes config: see docs/hermes_alerts_mcp.md
Hands MCP archived under attic/hands_mcp/
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from jarvis.mcp_alerts_http import main

if __name__ == "__main__":
    raise SystemExit(main())
