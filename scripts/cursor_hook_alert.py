#!/usr/bin/env python3
"""Cursor hooks → Jarvis alert queue.

Handles:
  - ``stop`` (status=completed|error) → finished / error phrase
  - ``preToolUse`` for SwitchMode / Ask* → needs approval phrase

AskQuestion often skips hooks in Cursor (upstream bug) — companion still
uses exact UIA ``Waiting for approval`` when Cursor alerts are on.

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


def _phrase_for_payload(data: dict) -> tuple[str, str] | None:
    """Return (phrase, detail) or None to skip."""
    tool = str(data.get("tool_name") or "")
    if tool:
        if not _is_approval_tool(tool):
            return None
        if "switch" in _norm_tool(tool) or "mode" in _norm_tool(tool):
            phrase = "Cursor wants plan mode."
        else:
            phrase = "Cursor needs your approval."
        return phrase, f"hook preToolUse tool={tool}"[:200]

    status = str(data.get("status") or "").strip().lower()
    if status == "aborted":
        return None
    if status == "error":
        return "Cursor stopped with an error.", f"hook stop status={status}"
    # completed, or empty stdin smoke / stop without status
    if status in ("completed", ""):
        return (
            "Cursor finished its work.",
            f"hook stop status={status or 'completed'} loop={data.get('loop_count', 0)}",
        )
    return None


def main() -> int:
    raw = sys.stdin.read()
    data: dict = {}
    if raw.strip():
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

    pair = _phrase_for_payload(data)
    # Never block tools / agent loop
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
