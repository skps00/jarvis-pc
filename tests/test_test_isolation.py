"""Guards: pytest must not touch live %APPDATA%\\Jarvis or the real Hermes API."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from jarvis import engine as engine_mod
from jarvis.settings import (
    invalidate_settings_cache,
    load_settings,
    settings_path,
)


def test_hermes_chat_sentinel_raises():
    with pytest.raises(AssertionError, match="Hermes"):
        engine_mod.hermes_chat("ping")


def test_settings_path_is_tmp_not_live():
    live = Path.home() / "AppData" / "Roaming" / "Jarvis" / "settings.json"
    got = settings_path()
    assert got != live
    assert "pytest" in str(got).lower() or "tmp" in str(got).lower() or "settings_appdata" in str(got)


def test_unmocked_query_path_raises_assertion():
    with pytest.raises(AssertionError, match="Hermes"):
        engine_mod.hermes_chat("怎樣開 Chrome？")


def test_live_settings_mtime_unchanged():
    import conftest as iso_conftest

    before = iso_conftest.LIVE_SETTINGS_MTIME_AT_IMPORT
    if before is None:
        return
    now = iso_conftest.live_settings_mtime_ns()
    assert now == before


def test_settings_cache_is_path_keyed(tmp_path, monkeypatch):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "settings.json").write_text(
        json.dumps({"wake_threshold": 0.31}, indent=2) + "\n",
        encoding="utf-8",
    )
    (b / "settings.json").write_text(
        json.dumps({"wake_threshold": 0.42}, indent=2) + "\n",
        encoding="utf-8",
    )
    s = 1700000000
    os.utime(a / "settings.json", (s, s))
    os.utime(b / "settings.json", (s, s))

    invalidate_settings_cache()
    monkeypatch.setenv("JARVIS_SETTINGS_DIR", str(a))
    assert load_settings(force=True).wake_threshold == 0.31
    monkeypatch.setenv("JARVIS_SETTINGS_DIR", str(b))
    assert load_settings().wake_threshold == 0.42
