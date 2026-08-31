#!/usr/bin/env python3
"""stdio MCP trampoline: no console window on Windows.

IMPORTANT: Do **not** launch this via ``.venv\\Scripts\\pythonw.exe`` on uv/venv
Windows installs — that file is often a *console* (CUI) shim (~45KB) and will
show a black CMD for the whole MCP lifetime. Use a real GUI ``pythonw.exe``
(e.g. ``pythoncore-*-64\\pythonw.exe`` or uv's ``...\\pythonw.exe`` with PE
subsystem=2).

Cursor spawns this via real *pythonw.exe*. We re-exec the MCP server with
``CREATE_NO_WINDOW`` while inheriting stdin/stdout/stderr.

Usage (mcp.json):
  command: .../pythoncore-.../pythonw.exe   # real GUI binary
  args: [this_script, --, real.exe, arg1, arg2, ...]
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("usage: mcp_stdio_no_console.py -- <command> [args...]", file=sys.stderr)
        return 2
    flags = 0
    if sys.platform == "win32":
        flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        proc = subprocess.Popen(
            argv,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            creationflags=flags,
        )
    except OSError as exc:
        print(f"mcp_stdio_no_console: {exc}", file=sys.stderr)
        return 1
    return int(proc.wait())


if __name__ == "__main__":
    raise SystemExit(main())
