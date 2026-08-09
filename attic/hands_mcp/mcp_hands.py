"""Jarvis Hands MCP server — stdio JSON-RPC, whitelist via engine only.

No YOLO. Confirm-required Hands still need Yes (MessageBox). Never bypass
profiles.yaml whitelist. Hermes should call these tools instead of raw shell.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable

from jarvis.engine import RunResult, execute_utterance

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "jarvis-hands"
SERVER_VERSION = "0.1.0"

AskConfirmFn = Callable[[str], bool]

TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "open_app",
        "description": (
            "Open a whitelisted Windows app/game via Jarvis Hands "
            "(profiles.yaml). Pass display name or short alias, e.g. Cursor, CS2."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "App name / alias to open",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Parse only; do not launch",
                    "default": False,
                },
            },
            "required": ["target"],
        },
    },
    {
        "name": "close_app",
        "description": (
            "Close a whitelisted app (confirm dialog). Uses Hands process list／PIDs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "App name / alias"},
                "dry_run": {"type": "boolean", "default": False},
            },
            "required": ["target"],
        },
    },
    {
        "name": "restart_app",
        "description": "Restart a whitelisted app (confirm, then close+open).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "App name / alias"},
                "dry_run": {"type": "boolean", "default": False},
            },
            "required": ["target"],
        },
    },
    {
        "name": "power",
        "description": (
            "System power via Hands whitelist: shutdown or sleep. Always confirms."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["shutdown", "sleep"],
                    "description": "shutdown | sleep",
                },
                "dry_run": {"type": "boolean", "default": False},
            },
            "required": ["action"],
        },
    },
    {
        "name": "discover",
        "description": (
            "Find an unregistered Start Menu／Desktop app and offer to open＋save "
            "profile (confirm). Same Discover path as typed「開 xxx」."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "App search text"},
                "dry_run": {"type": "boolean", "default": False},
            },
            "required": ["query"],
        },
    },
]


def ask_confirm_messagebox(prompt: str) -> bool:
    """Windows Yes/No; fail-closed elsewhere."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        # MB_YESNO | MB_ICONQUESTION | MB_TOPMOST | MB_SETFOREGROUND
        flags = 0x00000004 | 0x00000020 | 0x00040000 | 0x00010000
        r = ctypes.windll.user32.MessageBoxW(None, str(prompt), "JARVIS Hands", flags)
        return int(r) == 6  # IDYES
    except Exception:
        return False


def _utterance_for(tool: str, args: dict[str, Any]) -> str | None:
    """Map MCP tool args → Chinese/EN utterance for execute_utterance."""
    if tool == "open_app":
        t = str(args.get("target") or "").strip()
        return f"開 {t}" if t else None
    if tool == "close_app":
        t = str(args.get("target") or "").strip()
        return f"關 {t}" if t else None
    if tool == "restart_app":
        t = str(args.get("target") or "").strip()
        return f"重開 {t}" if t else None
    if tool == "power":
        action = str(args.get("action") or "").strip().lower()
        if action == "shutdown":
            return "關機"
        if action == "sleep":
            return "睡眠"
        return None
    if tool == "discover":
        q = str(args.get("query") or "").strip()
        return f"開 {q}" if q else None
    return None


def result_to_text(result: RunResult) -> str:
    """Flatten RunResult for MCP tool content."""
    body = "\n".join(result.lines)
    tag = "ok" if result.ok else "fail"
    return f"[{tag}]\n{body}" if body else f"[{tag}]"


def call_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    ask_confirm: AskConfirmFn | None = None,
) -> dict[str, Any]:
    """Execute one Hands tool; returns MCP tools/call result payload."""
    args = dict(arguments or {})
    dry_run = bool(args.pop("dry_run", False))
    confirm = ask_confirm if ask_confirm is not None else ask_confirm_messagebox

    if name not in {t["name"] for t in TOOL_DEFS}:
        return {
            "content": [{"type": "text", "text": f"[fail] unknown tool: {name}"}],
            "isError": True,
        }

    utterance = _utterance_for(name, args)
    if not utterance:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"[fail] missing／invalid args for {name}",
                }
            ],
            "isError": True,
        }

    try:
        result = execute_utterance(
            utterance,
            dry_run=dry_run,
            ask_confirm=confirm,
            repair_asr=False,
        )
    except Exception as exc:  # noqa: BLE001 — MCP must not die on tool errors
        return {
            "content": [{"type": "text", "text": f"[fail] {type(exc).__name__}: {exc}"}],
            "isError": True,
        }

    text = result_to_text(result)
    return {"content": [{"type": "text", "text": text}], "isError": not result.ok}


def _read_message() -> dict[str, Any] | None:
    """Read one MCP stdio message (Content-Length or single JSON line)."""
    header = b""
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            return None
        header += ch
        if header.endswith(b"\r\n\r\n"):
            break
        # Newline-delimited JSON (tests / simple clients)
        if b"\n" in header and b"Content-Length" not in header.upper():
            line = header.strip()
            if not line:
                header = b""
                continue
            return json.loads(line.decode("utf-8"))

    headers = header.decode("utf-8", errors="replace")
    length = 0
    for line in headers.split("\r\n"):
        if line.lower().startswith("content-length:"):
            length = int(line.split(":", 1)[1].strip())
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    if len(body) < length:
        return None
    return json.loads(body.decode("utf-8"))


def _write_message(msg: dict[str, Any]) -> None:
    raw = json.dumps(msg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(
        f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw
    )
    sys.stdout.buffer.flush()


def _handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    """Dispatch one JSON-RPC request; None = notification (no response)."""
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }

    if method == "notifications/initialized" or method == "initialized":
        return None

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOL_DEFS},
        }

    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            arguments = {}
        result = call_tool(name, arguments)
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    if msg_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def run_stdio() -> None:
    """Block on stdin; serve MCP until EOF."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    while True:
        try:
            msg = _read_message()
        except (json.JSONDecodeError, ValueError) as exc:
            _write_message(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {exc}"},
                }
            )
            continue
        if msg is None:
            break
        resp = _handle(msg)
        if resp is not None:
            _write_message(resp)


def main() -> None:
    """CLI entry: ``python -m jarvis.mcp_hands``."""
    run_stdio()


if __name__ == "__main__":
    main()
