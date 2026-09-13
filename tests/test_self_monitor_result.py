"""MonitorResult return type + shaped speakable alert from run_once summary."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.alert_policy import is_speakable, shape
from jarvis.self_monitor import MonitorResult, run_once


def test_run_once_returns_monitor_result_and_unpacks() -> None:
    # Avoid APPDATA I/O / nvidia-smi; keep summary/notable logic exercised.
    with (
        patch("jarvis.self_monitor._tail_lines", return_value=[]),
        patch("jarvis.self_monitor._read_wake_threshold", return_value=0.5),
        patch("jarvis.self_monitor._write_wake_threshold", return_value=False),
        patch("jarvis.self_monitor._query_vram_gb", return_value="n/a"),
    ):
        result = run_once()
    assert isinstance(result, MonitorResult)
    assert hasattr(result, "summary")
    assert hasattr(result, "notable")
    assert isinstance(result.summary, str)
    assert isinstance(result.notable, bool)
    summary, notable = result
    assert summary == result.summary
    assert notable == result.notable
    # tuple-compat unpack from run_once() itself
    with (
        patch("jarvis.self_monitor._tail_lines", return_value=[]),
        patch("jarvis.self_monitor._read_wake_threshold", return_value=0.5),
        patch("jarvis.self_monitor._write_wake_threshold", return_value=False),
        patch("jarvis.self_monitor._query_vram_gb", return_value="n/a"),
    ):
        summary2, notable2 = run_once()
    assert isinstance(summary2, str)
    assert isinstance(notable2, bool)


def test_shape_self_monitor_from_run_once_summary() -> None:
    with (
        patch("jarvis.self_monitor._tail_lines", return_value=[]),
        patch("jarvis.self_monitor._read_wake_threshold", return_value=0.5),
        patch("jarvis.self_monitor._write_wake_threshold", return_value=False),
        patch("jarvis.self_monitor._query_vram_gb", return_value="n/a"),
    ):
        result = run_once()
    spoken = shape("self-monitor", detail=result.summary)
    assert spoken.isascii()
    assert "=" not in spoken
    assert is_speakable(spoken) is True
