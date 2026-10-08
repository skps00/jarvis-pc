"""Regression: control HTTP self-probe requires our /health payload."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from jarvis.shell_app import probe_control_http


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


def _run(handler_cls: type[BaseHTTPRequestHandler]) -> tuple[ThreadingHTTPServer, int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, int(server.server_address[1])


def _stop(server: ThreadingHTTPServer) -> None:
    server.shutdown()
    server.server_close()


def test_probe_accepts_own_health_payload() -> None:
    class H(_Handler):
        body = json.dumps({"ok": True, "service": "jarvis"}).encode("utf-8")

    server, port = _run(H)
    try:
        assert probe_control_http(port, 2.0) is True
    finally:
        _stop(server)


def test_probe_rejects_wrong_service() -> None:
    class H(_Handler):
        body = json.dumps({"ok": True, "service": "not-jarvis"}).encode("utf-8")

    server, port = _run(H)
    try:
        assert probe_control_http(port, 1.0) is False
    finally:
        _stop(server)


def test_probe_rejects_http_503() -> None:
    class H(_Handler):
        status = 503
        body = json.dumps({"ok": True, "service": "jarvis"}).encode("utf-8")

    server, port = _run(H)
    try:
        assert probe_control_http(port, 1.0) is False
    finally:
        _stop(server)


def test_probe_rejects_closed_port() -> None:
    class H(_Handler):
        body = json.dumps({"ok": True, "service": "jarvis"}).encode("utf-8")

    server, port = _run(H)
    _stop(server)
    assert probe_control_http(port, 1.0) is False


def test_probe_rejects_non_json_body() -> None:
    class H(_Handler):
        content_type = "text/plain"
        body = b"ok"

    server, port = _run(H)
    try:
        assert probe_control_http(port, 1.0) is False
    finally:
        _stop(server)
