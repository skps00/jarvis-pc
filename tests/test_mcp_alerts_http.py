"""Alerts HTTP MCP auth + tool smoke (requires mcp extra)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("mcp")
pytest.importorskip("starlette")

from jarvis.alert_store import AlertStore
from jarvis.mcp_alerts_http import build_mcp, resolve_token


def test_resolve_token_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JARVIS_ALERTS_MCP_TOKEN", raising=False)
    token_file = tmp_path / "mcp_token.txt"
    monkeypatch.setattr(
        "jarvis.mcp_alerts_http.default_token_path", lambda: token_file
    )
    t1 = resolve_token(None)
    assert len(t1) >= 16
    assert token_file.read_text(encoding="utf-8").strip() == t1
    t2 = resolve_token(None)
    assert t2 == t1


def test_build_mcp_rejects_non_loopback(tmp_path: Path) -> None:
    st = AlertStore(tmp_path / "q.jsonl")
    with pytest.raises(ValueError, match="loopback"):
        build_mcp(store=st, token="secret", host="0.0.0.0")


def test_bearer_middleware_401(tmp_path: Path) -> None:
    from starlette.testclient import TestClient

    st = AlertStore(tmp_path / "q.jsonl")
    st.enqueue(kind="test", phrase="Alert system ready.")
    _mcp, app, _ = build_mcp(store=st, token="good-token", host="127.0.0.1")
    client = TestClient(app)
    r = client.get("/mcp")
    assert r.status_code == 401
    r2 = client.get("/mcp", headers={"Authorization": "Bearer bad"})
    assert r2.status_code == 401
