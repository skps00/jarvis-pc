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

import json
import os
from pathlib import Path
from unittest import mock

import pytest

_LIVE_SETTINGS_JSON = Path.home() / "AppData" / "Roaming" / "Jarvis" / "settings.json"

_PRISTINE_SETTINGS = {
    "hermes_enabled": False,
    "wake_threshold": 0.50,
    "alert_voice": False,
}


def live_settings_mtime_ns() -> int | None:
    """st_mtime_ns of the real (non-isolated) settings.json, or None if missing."""
    try:
        return _LIVE_SETTINGS_JSON.stat().st_mtime_ns
    except OSError:
        return None


# Snapshot at conftest import — before any test writes.
LIVE_SETTINGS_MTIME_AT_IMPORT = live_settings_mtime_ns()


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


def _no_real_hermes(*_a, **_k):
    raise AssertionError("test 唔准打真 Hermes")


@pytest.fixture(scope="session", autouse=True)
def _isolate_settings(tmp_path_factory: pytest.TempPathFactory):
    """Isolate settings.json via JARVIS_SETTINGS_DIR + fail-loud Hermes sentinels."""
    from jarvis.settings import Settings

    prev = os.environ.get("JARVIS_SETTINGS_DIR")
    root = tmp_path_factory.mktemp("settings_appdata")
    jdir = root / "Jarvis"
    jdir.mkdir(parents=True, exist_ok=True)
    os.environ["JARVIS_SETTINGS_DIR"] = str(jdir)
    (jdir / "settings.json").write_text(
        json.dumps(_PRISTINE_SETTINGS, indent=2) + "\n",
        encoding="utf-8",
    )

    p_engine_chat = mock.patch("jarvis.engine.hermes_chat", side_effect=_no_real_hermes)
    p_bridge = mock.patch("jarvis.hermes_bridge.chat", side_effect=_no_real_hermes)
    p_load = mock.patch(
        "jarvis.engine.load_settings",
        lambda *_a, **_k: Settings(hermes_enabled=False, alert_voice=False),
    )
    p_engine_chat.start()
    p_bridge.start()
    p_load.start()
    try:
        yield jdir
    finally:
        p_load.stop()
        p_bridge.stop()
        p_engine_chat.stop()
        if prev is None:
            os.environ.pop("JARVIS_SETTINGS_DIR", None)
        else:
            os.environ["JARVIS_SETTINGS_DIR"] = prev


@pytest.fixture(autouse=True)
def _reset_isolated_settings(_isolate_settings):
    """Rewrite session-tmp settings.json to pristine before every test."""
    path = Path(_isolate_settings) / "settings.json"
    path.write_text(
        json.dumps(_PRISTINE_SETTINGS, indent=2) + "\n",
        encoding="utf-8",
    )
    from jarvis.settings import invalidate_settings_cache

    invalidate_settings_cache()
    yield
