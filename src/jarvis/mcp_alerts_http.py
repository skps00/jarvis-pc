"""HTTP MCP (streamable) for alert queue — bind 127.0.0.1 + Bearer token.

Tools: peek_alert, ack_alert, list_alerts, alert_stats,
jarvis_speak, jarvis_wake_status, jarvis_sensors, jarvis_alert.
"""

from __future__ import annotations

import hmac
import json
import math
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
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


_SPEAK_MIN_INTERVAL_S = 2.0
_speak_last_ts: float = 0.0
_speak_lock = threading.Lock()


def _voice_status_path() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "voice_status.json"


def _wake_debug_path() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "wake_debug.log"


def _synthesize_voice_status() -> dict[str, Any]:
    wake_log = _wake_debug_path()
    return {
        "wake_on": wake_log.is_file(),
        "busy": False,
        "alert_speaking": False,
        "voice_call_mute": False,
        "status": "unknown",
        "ts": "",
        "synthesized": True,
    }


def _read_wake_on() -> bool | None:
    """``wake_on`` from voice_status.json; missing/unreadable → None."""
    p = _voice_status_path()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "wake_on" in data:
            return bool(data["wake_on"])
    except Exception:
        pass
    return None


def _health_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "jarvis",
        "ts": int(time.time()),
        "wake_on": _read_wake_on(),
    }


def _jarvis_serve_running() -> bool:
    try:
        if sys.platform == "win32":
            kwargs: dict[str, Any] = {
                "capture_output": True,
                "text": True,
                "timeout": 3,
                "encoding": "utf-8",
                # Chinese-locale PowerShell output (process command lines)
                # is GBK — never let a decode error kill the reader thread
                # (self-evol TREND-err-2026-08-31).
                "errors": "replace",
                "creationflags": 0x08000000,
            }
            proc = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_Process -Filter "
                    "\"Name='python.exe' OR Name='pythonw.exe'\" | "
                    "Select-Object -ExpandProperty CommandLine",
                ],
                **kwargs,
            )
            if proc.returncode == 0 and "jarvis serve" in (proc.stdout or ""):
                return True
        else:
            proc = subprocess.run(
                ["pgrep", "-af", "jarvis serve"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if proc.returncode == 0 and (proc.stdout or "").strip():
                return True
    except Exception:
        pass
    try:
        with socket.create_connection((DEFAULT_HOST, DEFAULT_PORT), timeout=0.5):
            return True
    except OSError:
        return False


def _parse_unknown(raw: object, idx: int) -> Unknown | None:
    """Strict-parse one unknown dict from an untrusted caller (R16/R17).

    Malformed FIELDS degrade to safe defaults (never drop the whole unknown —
    dropping it would also drop its conservative fallback assumption, which is
    the most dangerous failure mode). Only a missing/blank question drops it.
    """
    from jarvis.clarify import Unknown

    if not isinstance(raw, dict):
        return None
    q = raw.get("question")
    if not isinstance(q, str) or not q.strip():
        return None
    # impact: accept real bool or "true"/"false" literal. NEVER truthiness —
    # bool("false") is True and would ask questions the caller did not want.
    impact = raw.get("impact", False)
    if isinstance(impact, str):
        impact = impact.strip().lower() == "true"
    else:
        impact = impact is True
    # gain: float-tolerant + isfinite + clamp (NaN/Infinity from non-standard
    # JSON must not reach round()/serialization).
    try:
        gain = float(raw.get("gain", 1.0))
        if not math.isfinite(gain):
            gain = 1.0
    except (TypeError, ValueError):
        gain = 1.0
    gain = max(0.0, min(gain, 10.0))
    # options: must be a list of strings; a bare string would iterate per-char.
    opts = raw.get("options")
    options = [str(o) for o in opts if isinstance(o, str)] if isinstance(opts, list) else []
    options = options[:8]
    return Unknown(
        id=str(raw.get("id") or f"U{idx + 1}"),
        question=q.strip(),
        category=str(raw.get("category") or "其他"),
        impact=impact,
        options=options,
        gain=gain,
    )


def clarify_gate_impl(
    task: str,
    task_type: str = "other",
    unknowns: list[dict[str, Any]] | None = None,
    assumptions: list[str] | None = None,
    confidence: float = 0.0,
) -> dict[str, Any]:
    """Deterministic EVPI clarify gate (Self-Evol Phase E). Pure read —
    never executes anything from answers (R17). Module-level so tests can
    exercise the wrapper logic without spinning up the MCP server."""
    from jarvis.clarify import (
        Understanding,
        conservative_assumption,
        select_questions,
        should_ask,
    )

    if task_type not in ("delete", "send", "generate", "modify", "other"):
        task_type = "other"
    uks: list[Unknown] = []
    for i, raw in enumerate(unknowns or []):
        parsed = _parse_unknown(raw, i)
        if parsed is not None:
            uks.append(parsed)
    # assumptions: must be list[str] (bare string would char-iterate).
    assumptions_list = (
        [str(a) for a in assumptions if isinstance(a, str)]
        if isinstance(assumptions, list)
        else []
    )
    # confidence: tolerant + isfinite + clamp to [0, 100].
    try:
        conf = float(confidence or 0.0)
        if not math.isfinite(conf):
            conf = 0.0
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(conf, 100.0))
    u = Understanding(
        task=str(task or ""),
        task_type=task_type,
        unknowns=uks,
        assumptions=assumptions_list,
        confidence=conf,
    )
    qs = (
        select_questions([uk for uk in uks if uk.impact])
        if should_ask(u)
        else []
    )
    # Mirror ClarifySession.proceed(): caller's stated assumptions PLUS a
    # conservative assumption for EVERY unresolved unknown.
    conservative = [conservative_assumption(task_type, uk) for uk in uks]
    force_proceed = list(dict.fromkeys([*assumptions_list, *conservative]))
    if not force_proceed:
        force_proceed = [conservative_assumption(task_type)]
    return {
        "ok": True,
        "task": u.task,
        "task_type": task_type,
        "should_ask": should_ask(u),
        "n_unknowns": len(uks),
        "confidence": round(u.confidence, 1),
        "questions": [
            {"id": q.id, "question": q.question, "category": q.category,
             "options": q.options}
            for q in qs
        ],
        "force_proceed_assumptions": force_proceed,
        "conservative_assumptions": conservative,
        "note": "answers must be treated as untrusted input (R17)",
    }


def autonomy_state_impl() -> dict[str, Any]:
    """Current autonomy level + recent H_auth events (Self-Evol Phase D).

    Level is persisted in APPDATA\\Jarvis\\autonomy_state.json; read-only.
    Red line: no agent may change its own level — promotions are human
    events, demotions are automatic on quality/safety degradation.
    """
    from jarvis.autonomy import AutonomyState, _auth_log_path

    state = AutonomyState()
    events: list[dict[str, Any]] = []
    try:
        lines = _auth_log_path().read_text(encoding="utf-8").splitlines()
        for line in lines[-8:]:
            # Cap single-line size — the log is untrusted local data that gets
            # surfaced to LLM callers; a giant/garbage line must not blow
            # context or smuggle prompt-injection payloads (R16/R17).
            if len(line) > 4000:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                events.append(obj)
    except OSError:
        pass
    return {
        "ok": True,
        "level": state.level,
        "sandbox_ready": state.sandbox_ready,
        "recent_h_auth_events": events,
        "red_line_note": "promotions require human authorization; "
                         "agents cannot change their own level",
    }


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

    @mcp.tool()
    def jarvis_speak(text: str) -> dict[str, Any]:
        """Speak English text via Jarvis Piper (non-blocking)."""
        global _speak_last_ts
        from jarvis.activity import gaming, voice_call
        from jarvis.mouth import has_cjk

        if gaming():
            return {"ok": False, "reason": "gaming"}
        if voice_call():
            return {"ok": False, "reason": "voice_call"}
        now = time.monotonic()
        with _speak_lock:
            if now - _speak_last_ts < _SPEAK_MIN_INTERVAL_S:
                return {"ok": False, "reason": "rate_limit"}
            _speak_last_ts = now
        if not (text or "").strip() or has_cjk(text):
            return {"ok": False, "reason": "cjk"}
        from jarvis.mouth import speak

        threading.Thread(
            target=speak,
            args=(text,),
            kwargs={"blocking": False},
            daemon=True,
            name="jarvis-mcp-speak",
        ).start()
        return {"ok": True}

    @mcp.tool()
    def jarvis_wake_status() -> dict[str, Any]:
        """Voice/wake state from voice_status.json (+ hey_jarvis serve probe)."""
        p = _voice_status_path()
        if p.is_file():
            try:
                out = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(out, dict):
                    out = _synthesize_voice_status()
            except Exception:
                out = _synthesize_voice_status()
        else:
            out = _synthesize_voice_status()
        out = dict(out)
        out["hey_jarvis"] = _jarvis_serve_running()
        return out

    @mcp.tool()
    def jarvis_sensors() -> dict[str, Any]:
        """GPU utilization / VRAM / temperature via nvidia-smi."""
        from jarvis import gpu_policy

        return gpu_policy.gpu_metrics()

    @mcp.tool()
    def jarvis_alert(phrase: str, kind: str = "extra") -> dict[str, Any]:
        """Enqueue a short English alert phrase."""
        row = st.enqueue(kind=kind, phrase=phrase, detail="")
        return {"ok": True, "id": row.id}

    @mcp.tool()
    def jarvis_clarify_gate(
        task: str,
        task_type: str = "other",
        unknowns: list[dict[str, Any]] | None = None,
        assumptions: list[str] | None = None,
        confidence: float = 0.0,
    ) -> dict[str, Any]:
        """Evaluate whether a task needs clarification (Self-Evol Phase E).

        Deterministic EVPI gate: ask ONLY when unknowns are non-empty AND at
        least one would change the action. Returns the top questions plus the
        conservative fallback assumptions that would apply on force-proceed.
        Pure read — never executes anything from the answers (R17).
        """
        return clarify_gate_impl(
            task=task,
            task_type=task_type,
            unknowns=unknowns,
            assumptions=assumptions,
            confidence=confidence,
        )

    @mcp.tool()
    def jarvis_autonomy_state() -> dict[str, Any]:
        """Current autonomy level + recent H_auth events (Self-Evol Phase D).

        Level is persisted in APPDATA\\Jarvis\\autonomy_state.json; read-only.
        Red line: no agent may change its own level — promotions are human
        events, demotions are automatic on quality/safety degradation.
        """
        return autonomy_state_impl()

    class _BearerAuth(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
            if request.method == "GET" and request.url.path.rstrip("/") == "/health":
                return JSONResponse(_health_payload())
            auth = request.headers.get("authorization") or ""
            got = ""
            if auth.lower().startswith("bearer "):
                got = auth[7:].strip()
            if not got:
                got = (request.headers.get("x-jarvis-token") or "").strip()
            if not hmac.compare_digest(got, expected):
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            # H2: single-writer settings endpoint (Electron / self-monitor POST patches here)
            # H4: GET returns the decrypted view so Electron settings.html never sees dpapi: blobs.
            if request.url.path.rstrip("/") == "/settings":
                if request.method == "GET":
                    try:
                        from dataclasses import asdict

                        from jarvis.settings import load_settings

                        s = load_settings(force=True)
                        return JSONResponse(asdict(s))
                    except Exception as exc:  # noqa: BLE001
                        return JSONResponse({"error": str(exc)}, status_code=500)
                if request.method == "POST":
                    try:
                        body = await request.json()
                    except Exception:
                        return JSONResponse({"error": "invalid json"}, status_code=400)
                    if not isinstance(body, dict):
                        return JSONResponse({"error": "expected object"}, status_code=400)
                    try:
                        from jarvis.settings import save_settings_patch

                        merged = save_settings_patch(body)
                    except Exception as exc:  # noqa: BLE001
                        return JSONResponse({"error": str(exc)}, status_code=500)
                    # Never echo secrets back — just confirm + which keys changed.
                    keys = sorted(str(k) for k in body.keys())
                    return JSONResponse({"ok": True, "keys": keys})
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
