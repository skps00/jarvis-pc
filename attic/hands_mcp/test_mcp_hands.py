"""Unit tests for Jarvis Hands MCP (no live stdio Hermes)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.engine import RunResult
from jarvis.mcp_hands import (
    TOOL_DEFS,
    _utterance_for,
    call_tool,
    result_to_text,
)


def test_tool_defs_cover_required_names():
    names = {t["name"] for t in TOOL_DEFS}
    assert names == {
        "open_app",
        "close_app",
        "restart_app",
        "power",
        "discover",
    }


def test_utterance_mapping():
    assert _utterance_for("open_app", {"target": "Cursor"}) == "開 Cursor"
    assert _utterance_for("close_app", {"target": "Discord"}) == "關 Discord"
    assert _utterance_for("restart_app", {"target": "Chrome"}) == "重開 Chrome"
    assert _utterance_for("power", {"action": "shutdown"}) == "關機"
    assert _utterance_for("power", {"action": "sleep"}) == "睡眠"
    assert _utterance_for("discover", {"query": "notepad"}) == "開 notepad"
    assert _utterance_for("open_app", {"target": "  "}) is None
    assert _utterance_for("power", {"action": "reboot"}) is None


def test_result_to_text():
    assert "ok" in result_to_text(RunResult(True, ["[ok] hi"]))
    assert "fail" in result_to_text(RunResult(False, ["nope"]))


def test_call_tool_dry_run_open():
    fake = RunResult(True, ["[dry-run] open cursor"])
    with mock.patch(
        "jarvis.mcp_hands.execute_utterance", return_value=fake
    ) as ex:
        out = call_tool(
            "open_app",
            {"target": "Cursor", "dry_run": True},
            ask_confirm=lambda _p: False,
        )
    assert out["isError"] is False
    assert "dry-run" in out["content"][0]["text"]
    ex.assert_called_once()
    kwargs = ex.call_args
    assert kwargs[0][0] == "開 Cursor"
    assert kwargs[1]["dry_run"] is True
    assert kwargs[1]["repair_asr"] is False


def test_call_tool_unknown():
    out = call_tool("yolo_shell", {}, ask_confirm=lambda _p: True)
    assert out["isError"] is True
    assert "unknown" in out["content"][0]["text"].lower()


def test_call_tool_confirm_denied_propagates():
    fake = RunResult(False, ["[fail] 已取消（需要確認）"])
    with mock.patch(
        "jarvis.mcp_hands.execute_utterance", return_value=fake
    ) as ex:
        out = call_tool(
            "close_app",
            {"target": "Discord"},
            ask_confirm=lambda _p: False,
        )
    assert out["isError"] is True
    assert ex.call_args[1]["ask_confirm"]("x") is False


def test_no_yolo_in_tool_names():
    blob = " ".join(t["name"] + t.get("description", "") for t in TOOL_DEFS)
    assert "yolo" not in blob.lower()


if __name__ == "__main__":
    for fn in (
        test_tool_defs_cover_required_names,
        test_utterance_mapping,
        test_result_to_text,
        test_call_tool_dry_run_open,
        test_call_tool_unknown,
        test_call_tool_confirm_denied_propagates,
        test_no_yolo_in_tool_names,
    ):
        fn()
        print("ok", fn.__name__)
    print("all passed")
