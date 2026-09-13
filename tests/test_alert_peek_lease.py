"""MCP peek_alert default lease covers TTS window."""

from __future__ import annotations

import inspect

from jarvis import mcp_alerts_http


def test_peek_alert_default_lease_300() -> None:
    src = inspect.getsource(mcp_alerts_http.build_mcp)
    assert "def peek_alert(lease_s: float = 300.0)" in src
    assert "TTS" in src
