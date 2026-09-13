"""Shared pytest fixtures.

Guard: `pytest tests/` must never write into the LIVE JARVIS state directory
(`%APPDATA%/Jarvis`). Every module that owns state (shell_app._write_voice_status,
alert_store, autonomy, cursor_hooks, engine, eval_gate, mcp_alerts_http) resolves
its path lazily from `os.environ["APPDATA"]` at call time, so redirecting APPDATA
for the whole session is enough.

Regression: 2026-09-13 - tests/test_alert_piper_gate.py -> JarvisShell._handle_alert
-> shell_app._write_voice_status() overwrote the live voice_status.json
(wake_on=false), so the HUD showed "listening = off" until the sidecar rewrote it,
and the sidecar-health cron reported a false fingerprint change.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolate_appdata(tmp_path_factory: pytest.TempPathFactory):
    """Point APPDATA at a throwaway dir for the whole test session."""
    real = os.environ.get("APPDATA")
    sandbox = tmp_path_factory.mktemp("appdata")
    (sandbox / "Jarvis").mkdir(parents=True, exist_ok=True)
    os.environ["APPDATA"] = str(sandbox)
    try:
        yield sandbox
    finally:
        if real is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = real
