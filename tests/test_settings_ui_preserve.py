"""Regression: settings UI save must not revert unbound keys to defaults.

Tests the pure save-merge helper ``apply_ui_settings`` (no Tk required).
Full SettingsWindow covered by test_settings_ui_smoke.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.settings import Settings  # noqa: E402
from jarvis.settings_ui import apply_ui_settings  # noqa: E402


def test_apply_ui_settings_preserves_unbound() -> None:
    """stt_preload / alerts_mcp_port / alert_policy_mode survive a no-op UI merge."""
    base = Settings(
        stt_preload=True,
        alerts_mcp_port=8765,
        alert_policy_mode="shadow",
        tts_ack=True,
        vc_fail_closed=True,
    )
    # Simulate _save() overwriting only UI-bound fields (same values = no change).
    merged = apply_ui_settings(
        base,
        alert_voice=base.alert_voice,
        alert_discord=base.alert_discord,
        alert_policy_mode=base.alert_policy_mode,
    )
    assert merged.stt_preload is True
    assert merged.alerts_mcp_port == 8765
    assert merged.alert_policy_mode == "shadow"
    assert merged.tts_ack is True
    assert merged.vc_fail_closed is True


def test_apply_ui_settings_overwrites_bound_only() -> None:
    base = Settings(stt_preload=True, alert_policy_mode="off")
    merged = apply_ui_settings(base, alert_policy_mode="enforce")
    assert merged.alert_policy_mode == "enforce"
    assert merged.stt_preload is True
