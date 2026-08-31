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


# ---------------------------------------------------------------------------
# Self-Evol wiring: clarify gate + autonomy state (2026-08-31)
# ---------------------------------------------------------------------------

from jarvis.mcp_alerts_http import (  # noqa: E402
    autonomy_state_impl,
    clarify_gate_impl,
)


def test_clarify_gate_asks_only_for_impactful_unknowns() -> None:
    r = clarify_gate_impl(
        "刪除舊 log",
        task_type="delete",
        unknowns=[
            {"id": "U1", "question": "刪邊個 log？", "category": "範圍",
             "impact": True, "options": ["wake_debug", "全部"]},
            {"id": "U2", "question": "幾時刪？", "category": "優先次序",
             "impact": False, "options": ["即刻", "等確認"]},
        ],
        assumptions=[],
        confidence=60.0,
    )
    assert r["ok"] is True
    assert r["should_ask"] is True
    assert [q["id"] for q in r["questions"]] == ["U1"]  # impactful only
    assert r["confidence"] == 60.0


def test_clarify_gate_silent_when_no_unknowns() -> None:
    r = clarify_gate_impl("開 Minecraft", task_type="other", unknowns=[],
                          assumptions=["跟 default profile"], confidence=95.0)
    assert r["should_ask"] is False
    assert r["questions"] == []


def test_clarify_gate_conservative_fallback_by_task_type() -> None:
    # send task + unresolved unknown -> conservative "唔發送" assumption
    r = clarify_gate_impl(
        "發送報告",
        task_type="send",
        unknowns=[{"id": "U1", "question": "俾邊個？", "category": "範圍",
                   "impact": False, "options": ["SK", "全部"]}],
    )
    assert r["should_ask"] is False
    assert any("唔發送" in a for a in r["conservative_assumptions"])


def test_clarify_gate_normalizes_bad_task_type() -> None:
    r = clarify_gate_impl("whatever", task_type="not-a-type", unknowns=[])
    assert r["task_type"] == "other"


def test_autonomy_state_impl_reads_log_and_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import jarvis.autonomy as autonomy_mod

    monkeypatch.setattr(autonomy_mod, "_auth_log_path", lambda: tmp_path / "h_auth.jsonl")
    monkeypatch.setattr(autonomy_mod, "_state_path", lambda: tmp_path / "autonomy_state.json")
    (tmp_path / "h_auth.jsonl").write_text(
        '{"who": "SK", "action": "promote", "level": "L1a"}\n',
        encoding="utf-8",
    )
    r = autonomy_state_impl()
    assert r["ok"] is True
    assert r["level"] == "L0"  # no state file -> default L0
    assert len(r["recent_h_auth_events"]) == 1
    assert r["recent_h_auth_events"][0]["action"] == "promote"


# ---------------------------------------------------------------------------
# Adversarial parsing (independent reviewer findings, 2026-08-31)
# ---------------------------------------------------------------------------

def test_impact_string_false_is_not_truthy() -> None:
    # bool("false") == True would ask questions the caller did not want.
    r = clarify_gate_impl(
        "刪除舊 log", task_type="delete",
        unknowns=[{"id": "U1", "question": "刪邊個？", "category": "範圍",
                   "impact": "false", "options": ["wake_debug", "全部"]}],
    )
    assert r["should_ask"] is False  # "false" literal -> no ask
    assert r["questions"] == []
    # literal "true" still asks
    r2 = clarify_gate_impl(
        "刪除舊 log", task_type="delete",
        unknowns=[{"id": "U1", "question": "刪邊個？", "category": "範圍",
                   "impact": "true", "options": ["wake_debug", "全部"]}],
    )
    assert r2["should_ask"] is True


def test_malformed_gain_keeps_unknown() -> None:
    # A bad gain must degrade to default, NOT drop the unknown (dropping it
    # would also drop its conservative fallback assumption).
    for bad in (None, "", "high", {"x": 1}, "abc"):
        r = clarify_gate_impl(
            "刪除舊 log", task_type="delete",
            unknowns=[{"id": "U1", "question": "刪邊個？", "category": "範圍",
                       "impact": True, "gain": bad}],
        )
        assert r["n_unknowns"] == 1, f"gain={bad!r} must not drop the unknown"
        assert r["should_ask"] is True
        assert any("唔刪除" in a for a in r["conservative_assumptions"])


def test_options_string_not_char_splitted() -> None:
    r = clarify_gate_impl(
        "刪除舊 log", task_type="delete",
        unknowns=[{"id": "U1", "question": "刪邊個？", "category": "範圍",
                   "impact": True, "options": "delete everything"}],
    )
    q = r["questions"][0]
    assert q["options"] == []  # string options ignored, not per-char split


def test_confidence_clamped_and_tolerant() -> None:
    for bad in ("abc", float("nan"), float("inf"), -5, 1000):
        r = clarify_gate_impl("test", task_type="other", unknowns=[], confidence=bad)
        assert 0.0 <= r["confidence"] <= 100.0, f"confidence={bad!r} must clamp"


def test_assumptions_string_not_char_iterated() -> None:
    r = clarify_gate_impl("test", task_type="other", unknowns=[],
                          assumptions="foo", confidence=90)
    # string assumptions ignored (not ['f','o','o']), fallback still present
    assert all(len(a) > 1 for a in r["force_proceed_assumptions"])


def test_force_proceed_merges_caller_assumptions() -> None:
    r = clarify_gate_impl(
        "刪除舊 log", task_type="delete",
        unknowns=[{"id": "U1", "question": "刪邊個？", "category": "範圍",
                   "impact": True}],
        assumptions=["跟現有 code style"],
    )
    assert "跟現有 code style" in r["force_proceed_assumptions"]
    assert any("唔刪除" in a for a in r["force_proceed_assumptions"])


def test_autonomy_state_impl_skips_non_dict_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import jarvis.autonomy as autonomy_mod

    monkeypatch.setattr(autonomy_mod, "_auth_log_path", lambda: tmp_path / "h_auth.jsonl")
    monkeypatch.setattr(autonomy_mod, "_state_path", lambda: tmp_path / "autonomy_state.json")
    (tmp_path / "h_auth.jsonl").write_text(
        '"just a string"\n'
        '42\n'
        '{"who": "SK", "action": "demote", "level": "L0"}\n'
        + "x" * 5000 + "\n",  # oversized line must be skipped too
        encoding="utf-8",
    )
    r = autonomy_state_impl()
    assert len(r["recent_h_auth_events"]) == 1
    assert r["recent_h_auth_events"][0]["action"] == "demote"
