"""HTTP MCP (streamable) for alert queue — bind 127.0.0.1 + Bearer token.

Tools: peek_alert, ack_alert, list_alerts, alert_stats.
"""

from __future__ import annotations

import os
import secrets
import threading
from pathlib import Path
from typing import Any

from jarvis.alert_store import AlertStore, default_queue_path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
TOKEN_ENV = "JARVIS_ALERTS_MCP_TOKEN"


def default_token_path() -> Path:
    return default_queue_path().parent / "mcp_token.txt"


def resolve_token(explicit: str | None = None) -> str:
    """Env → explicit → file → generate+persist."""
    env = (os.environ.get(TOKEN_ENV) or "").strip()
    if env:
        return env
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    path = default_token_path()
    if path.is_file():
        t = path.read_text(encoding="utf-8").strip()
        if t:
            return t
    t = secrets.token_urlsafe(24)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(t + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return t


def _require_loopback(host: str) -> str:
    h = (host or DEFAULT_HOST).strip() or DEFAULT_HOST
    if h not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError(f"alerts MCP must bind loopback, got {h!r}")
    return h


def build_mcp(
    *,
    store: AlertStore | None = None,
    token: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
):
    """Create FastMCP app with auth middleware. Requires ``mcp`` package."""
    from mcp.server.fastmcp import FastMCP
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    host = _require_loopback(host)
    st = store or AlertStore()
    expected = token.strip()
    if not expected:
        raise ValueError("alerts MCP token required")

    mcp = FastMCP(
        "jarvis-alerts",
        instructions=(
            "Desktop alert queue. peek_alert → speak phrase with Hermes TTS → "
            "ack_alert. Phrases are short English stubs; never invent message body."
        ),
        host=host,
        port=int(port),
    )

    @mcp.tool()
    def peek_alert(lease_s: float = 30.0) -> dict[str, Any]:
        """Lease next alert. Speak ``phrase`` then call ack_alert."""
        row = st.peek(lease_s=float(lease_s))
        if row is None:
            return {"ok": True, "alert": None}
        return {"ok": True, "alert": row.to_dict()}

    @mcp.tool()
    def ack_alert(alert_id: str) -> dict[str, Any]:
        """Ack after successful speak (or deliberate drop)."""
        ok = st.ack(str(alert_id or ""))
        return {"ok": ok, "alert_id": alert_id}

    @mcp.tool()
    def list_alerts() -> dict[str, Any]:
        """List open (non-acked) alerts."""
        rows = st.list_open()
        return {"ok": True, "alerts": [r.to_dict() for r in rows]}

    @mcp.tool()
    def alert_stats() -> dict[str, Any]:
        """Queue depth / pending / leased."""
        return {"ok": True, **st.stats()}

    class _BearerAuth(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
            auth = request.headers.get("authorization") or ""
            got = ""
            if auth.lower().startswith("bearer "):
                got = auth[7:].strip()
            if not got:
                got = (request.headers.get("x-jarvis-token") or "").strip()
            if got != expected:
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            return await call_next(request)

    app = mcp.streamable_http_app()
    app.add_middleware(_BearerAuth)
    return mcp, app, st


def serve(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    token: str | None = None,
    store_path: Path | None = None,
) -> None:
    """Blocking uvicorn serve (loopback only)."""
    import uvicorn

    host = _require_loopback(host)
    tok = resolve_token(token)
    store = AlertStore(store_path) if store_path else AlertStore()
    _mcp, app, _st = build_mcp(store=store, token=tok, host=host, port=port)
    uvicorn.run(app, host=host, port=int(port), log_level="warning")


_thread: threading.Thread | None = None


def serve_in_thread(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    token: str | None = None,
    store_path: Path | None = None,
) -> threading.Thread:
    """Start HTTP MCP once in a daemon thread."""
    global _thread
    if _thread is not None and _thread.is_alive():
        return _thread

    def _run() -> None:
        serve(host=host, port=port, token=token, store_path=store_path)

    _thread = threading.Thread(target=_run, daemon=True, name="jarvis-alerts-mcp")
    _thread.start()
    return _thread


def main(argv: list[str] | None = None) -> int:
    """CLI: ``jarvis-mcp`` → alerts HTTP MCP."""
    import argparse

    p = argparse.ArgumentParser(description="Jarvis alerts HTTP MCP (127.0.0.1)")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--token", default="", help=f"or env {TOKEN_ENV}")
    p.add_argument("--queue", default="", help="JSONL path override")
    args = p.parse_args(argv)
    try:
        host = _require_loopback(args.host)
    except ValueError as exc:
        print(f"[fail] {exc}", file=__import__("sys").stderr)
        return 2
    tok = resolve_token(args.token or None)
    q = Path(args.queue) if args.queue else None
    print(f"[ok] alerts MCP http://{host}:{int(args.port)}/mcp (Bearer token set)")
    print(f"[ok] token file: {default_token_path()}")
    serve(host=host, port=int(args.port), token=tok, store_path=q)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
