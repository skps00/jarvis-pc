#!/usr/bin/env python3
"""Cursor hooks → Jarvis alert queue.

``stop`` means the agent *loop ended for this turn* — NOT always “job done”.
When Cursor pauses for SwitchMode / Ask, it often still fires ``stop`` with
``status=completed``. We suppress that false “finished” for a short window
after an approval-tool ``preToolUse`` (or companion UIA wait).

AskQuestion often skips hooks (upstream Cursor bug) — companion UIA
``Waiting for approval`` remains the fallback.

Install: ``python -m jarvis cursor-hooks install``
Docs: https://cursor.com/docs/agent/hooks
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from jarvis.cursor_hooks import (  # noqa: E402
    clear_waiting,
    mark_waiting,
    waiting_active,
)

_APPROVAL_TOOLS = {
    "switchmode",
    "switch_mode",
    "askquestion",
    "ask_question",
    "askuserquestion",
    "ask_user_question",
}


def _norm_tool(name: str) -> str:
    return "".join(ch for ch in (name or "").lower() if ch.isalnum() or ch == "_")


def _is_approval_tool(tool_name: str) -> bool:
    nt = _norm_tool(tool_name)
    if not nt:
        return False
    if nt in _APPROVAL_TOOLS:
        return True
    compact = nt.replace("_", "")
    if "switchmode" in compact:
        return True
    if compact.startswith("ask") and "question" in compact:
        return True
    return False


def _is_tool_hook(data: dict) -> bool:
    return bool(
        data.get("tool_name")
        or data.get("tool_input") is not None
        or data.get("tool_use_id")
        or str(data.get("hook_event_name") or "").lower()
        in ("pretooluse", "posttooluse", "posttoolusefailure")
    )


def _phrase_for_payload(data: dict) -> tuple[str, str] | None:
    """Return (phrase, detail) or None to skip."""
    if _is_tool_hook(data):
        tool = str(data.get("tool_name") or "")
        if not _is_approval_tool(tool):
            return None
        mark_waiting()
        if "switch" in _norm_tool(tool) or "mode" in _norm_tool(tool):
            phrase = "Cursor wants plan mode."
        else:
            phrase = "Cursor needs your approval."
        return phrase, f"hook preToolUse tool={tool}"[:200]

    status = str(data.get("status") or "").strip().lower()
    if status == "aborted":
        return None
    if status == "error":
        clear_waiting()
        return "Cursor stopped with an error.", f"hook stop status={status}"
    if status != "completed":
        return None
    # Loop ended — often also when pausing for user approval.
    if waiting_active():
        return None
    clear_waiting()
    return (
        "Cursor finished its work.",
        f"hook stop status=completed loop={data.get('loop_count', 0)}",
    )


def main() -> int:
    raw = sys.stdin.read()
    data: dict = {}
    if raw.strip():
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

    if not data:
        sys.stdout.write("{}")
        return 0

    pair = _phrase_for_payload(data)
    out: dict = {}
    if pair is None:
        sys.stdout.write(json.dumps(out))
        return 0
    phrase, detail = pair
    try:
        from jarvis.alert_store import AlertStore

        conv = str(data.get("conversation_id") or "")[:12]
        if conv:
            detail = f"{detail} conv={conv}"
        AlertStore().enqueue(
            kind="cursor",
            phrase=phrase,
            app="Cursor",
            detail=detail[:200],
        )
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[jarvis-hook] enqueue fail: {exc}\n")
    sys.stdout.write(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
