"""New alert-policy settings keys: defaults, clamp, round-trip."""

from __future__ import annotations

import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis import settings as settings_mod
from jarvis.settings import (
    Settings,
    _clamp,
    invalidate_settings_cache,
    load_settings,
    save_settings_patch,
)


@contextmanager
def _isolated_settings(tmp: Path):
    path = tmp / "settings.json"
    with mock.patch.multiple(
        settings_mod,
        SETTINGS_DIR=tmp,
        SETTINGS_PATH=path,
    ):
        # Invalidate any cached lock path so TemporaryDirectory teardown cannot
        # leave a dangling .settings.lockdir for later tests in this process.
        if hasattr(settings_mod, "_PATCH_LOCK"):
            settings_mod._PATCH_LOCK = None
        try:
            yield
        finally:
            if hasattr(settings_mod, "_PATCH_LOCK"):
                settings_mod._PATCH_LOCK = None


_DEFAULTS = {
    "alert_policy_mode": "off",
    "alert_gaming": "hold",
    "alert_hold_ttl_s": 900,
    "alert_held_cap": 64,
    "alert_digest_interval_s": 1800,
    "alert_digest_ttl_s": 86400,
    "alert_dedupe_window_s": 300,
    "alert_llm_polish": "off",
    "alert_llm_timeout_s": 3.0,
}


def test_alert_policy_defaults() -> None:
    s = Settings()
    for k, v in _DEFAULTS.items():
        assert getattr(s, k) == v, k


def test_alert_hold_ttl_clamp() -> None:
    assert _clamp(Settings(alert_hold_ttl_s=1)).alert_hold_ttl_s == 30
    assert _clamp(Settings(alert_hold_ttl_s=999999)).alert_hold_ttl_s == 3600
    assert _clamp(Settings(alert_hold_ttl_s="1200")).alert_hold_ttl_s == 1200


def test_alert_policy_enums_fallback() -> None:
    assert _clamp(Settings(alert_policy_mode="banana")).alert_policy_mode == "off"
    assert _clamp(Settings(alert_gaming="x")).alert_gaming == "hold"
    assert _clamp(Settings(alert_llm_polish="yes")).alert_llm_polish == "off"
    assert _clamp(Settings(alert_policy_mode="shadow")).alert_policy_mode == "shadow"
    assert _clamp(Settings(alert_gaming="drop")).alert_gaming == "drop"
    assert _clamp(Settings(alert_llm_polish="on")).alert_llm_polish == "on"


def test_alert_llm_timeout_clamp() -> None:
    assert _clamp(Settings(alert_llm_timeout_s="abc")).alert_llm_timeout_s == 3.0
    assert _clamp(Settings(alert_llm_timeout_s=0.1)).alert_llm_timeout_s == 1.0
    assert _clamp(Settings(alert_llm_timeout_s=99)).alert_llm_timeout_s == 10.0


def test_alert_dedupe_zero_legal() -> None:
    assert _clamp(Settings(alert_dedupe_window_s=0)).alert_dedupe_window_s == 0


def test_alert_keys_roundtrip_patch() -> None:
    patch = {
        "alert_policy_mode": "enforce",
        "alert_gaming": "drop",
        "alert_hold_ttl_s": 600,
        "alert_held_cap": 32,
        "alert_digest_interval_s": 900,
        "alert_digest_ttl_s": 7200,
        "alert_dedupe_window_s": 0,
        "alert_llm_polish": "on",
        "alert_llm_timeout_s": 5.5,
    }
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        with _isolated_settings(tmp):
            invalidate_settings_cache()
            save_settings_patch(patch)
            invalidate_settings_cache()
            loaded = load_settings(force=True)
            for k, v in patch.items():
                assert getattr(loaded, k) == v, k
