"""Regression: sidecar health monitor payload + fingerprint buckets."""

from __future__ import annotations

import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1] / "tools" / "jarvis_sidecar_health.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("jarvis_sidecar_health", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Handler(BaseHTTPRequestHandler):
    status = 200
    body: bytes = b"{}"
    content_type = "application/json"

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(self.status)
        self.send_header("Content-Type", self.content_type)
        self.send_header("Content-Length", str(len(self.body)))
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def _run(handler_cls: type[BaseHTTPRequestHandler]) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _stop(server: ThreadingHTTPServer) -> None:
    server.shutdown()
    server.server_close()


def test_bucket_boundaries() -> None:
    mod = _load()
    assert mod._bucket(0) == "<5m"
    assert mod._bucket(4 * 60) == "<5m"
    assert mod._bucket(5 * 60) == "5-30m"
    assert mod._bucket(29 * 60 + 59) == "5-30m"
    assert mod._bucket(30 * 60) == "30m-2h"
    assert mod._bucket(2 * 3600) == "2-6h"
    assert mod._bucket(6 * 3600) == ">6h"


def _probe_against(mod, handler_cls: type[BaseHTTPRequestHandler]):
    server = _run(handler_cls)
    try:
        port = int(server.server_address[1])
        mod.HEALTH_URL = f"http://127.0.0.1:{port}/health"
        return mod._probe()
    finally:
        _stop(server)


def test_probe_accepts_jarvis_payload() -> None:
    mod = _load()

    class H(_Handler):
        body = json.dumps({"ok": True, "service": "jarvis", "wake_on": False}).encode()

    kind, extra = _probe_against(mod, H)
    assert kind == "up"
    assert extra == "OK wake_on=False"


def test_probe_rejects_wrong_service() -> None:
    mod = _load()

    class H(_Handler):
        body = json.dumps({"ok": True, "service": "not-jarvis"}).encode()

    assert _probe_against(mod, H) == ("fail", "BadPayload")


def test_probe_rejects_ok_false() -> None:
    mod = _load()

    class H(_Handler):
        body = json.dumps({"ok": False, "service": "jarvis"}).encode()

    assert _probe_against(mod, H) == ("fail", "BadPayload")


def test_probe_rejects_plain_text() -> None:
    mod = _load()

    class H(_Handler):
        content_type = "text/plain"
        body = b"not json"

    assert _probe_against(mod, H) == ("fail", "BadPayload")


def test_fingerprint_off_no_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "STATE_PATH", tmp_path / "jarvis_sidecar_health_state.json")
    monkeypatch.setattr(mod, "_process_rows", lambda: [])
    monkeypatch.setattr(mod, "_probe", lambda: ("fail", "BadPayload"))
    assert mod._fingerprint() == "OFF"


def test_fingerprint_enum_failed_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    mod = _load()
    monkeypatch.setattr(mod, "STATE_PATH", tmp_path / "jarvis_sidecar_health_state.json")
    monkeypatch.setattr(mod, "_probe", lambda: ("fail", "URLError"))

    def _boom(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd="powershell", timeout=20)

    monkeypatch.setattr(subprocess, "check_output", _boom)
    fp = mod._fingerprint()
    assert fp.startswith("DOWN")
    assert "enum_failed" in fp
    assert fp != "OFF"


def test_fingerprint_off_empty_enum_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative control: successful enum with no matches stays OFF."""
    mod = _load()
    monkeypatch.setattr(mod, "STATE_PATH", tmp_path / "jarvis_sidecar_health_state.json")
    monkeypatch.setattr(mod, "_process_rows", lambda: [])
    monkeypatch.setattr(mod, "_probe", lambda: ("fail", "URLError"))
    assert mod._fingerprint() == "OFF"


def test_fingerprint_down_hud_and_stable_bucket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load()
    state = tmp_path / "jarvis_sidecar_health_state.json"
    monkeypatch.setattr(mod, "STATE_PATH", state)
    monkeypatch.setattr(
        mod,
        "_process_rows",
        lambda: [{"Name": "JARVIS ONE.exe", "CommandLine": ""}],
    )
    monkeypatch.setattr(mod, "_probe", lambda: ("fail", "BadPayload"))
    first = mod._fingerprint()
    assert first == "DOWN BadPayload t=<5m"
    second = mod._fingerprint()
    assert second == first
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


def test_fingerprint_bucket_after_six_minutes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import time

    mod = _load()
    state = tmp_path / "jarvis_sidecar_health_state.json"
    monkeypatch.setattr(mod, "STATE_PATH", state)
    monkeypatch.setattr(
        mod,
        "_process_rows",
        lambda: [{"Name": "JARVIS ONE.exe", "CommandLine": ""}],
    )
    monkeypatch.setattr(mod, "_probe", lambda: ("fail", "BadPayload"))
    started = time.time() - 6 * 60
    state.write_text(
        json.dumps({"down_since": started, "last_reason": "BadPayload", "updated_at": started}),
        encoding="utf-8",
    )
    assert mod._fingerprint() == "DOWN BadPayload t=5-30m"


def test_fingerprint_up_clears_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load()
    state = tmp_path / "jarvis_sidecar_health_state.json"
    monkeypatch.setattr(mod, "STATE_PATH", state)
    state.write_text(
        json.dumps({"down_since": 1, "last_reason": "x", "updated_at": 1}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "_process_rows", lambda: [])
    monkeypatch.setattr(mod, "_probe", lambda: ("up", "OK wake_on=False"))
    assert mod._fingerprint() == "OK wake_on=False"
    assert not state.exists()
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []
