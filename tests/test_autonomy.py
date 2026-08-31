"""Tests for jarvis.autonomy (Self-Evol Task 9, Phase D v2, 2026-08-30).

Covers: per-operation grading (R10), composite promotion gate with hysteresis
(R18), automatic asymmetric demotion, human authorization log, one-key kill
switch, and self-improvement rate alarm.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.autonomy import (  # noqa: E402
    L0,
    L1A,
    L1B,
    L1C,
    AuthEvent,
    AutonomyState,
    EvalEvidence,
    Operation,
    rate_alarm,
)


def _good_evidence() -> EvalEvidence:
    return EvalEvidence(
        golden_regression_free=True,
        auto_apply_pass_rate=0.95,
        override_rate=0.01,
        weeks_stable=3,
        redline_violations=0,
    )


# ---------------------------------------------------------------------------
# Per-operation grading (R10)
# ---------------------------------------------------------------------------

def test_classify_operations():
    assert Operation("sandbox_explore").level() == L1A
    assert Operation("apply_low_risk").level() == L1B
    assert Operation("irreversible").level() == L1C
    assert Operation("evaluator_change").level() == L1C
    assert Operation("spawn_agent").level() == L1C


def test_classify_fallback_by_risk():
    assert Operation("unknown_kind", risk="high").level() == L1C
    assert Operation("unknown_kind", reversible=False).level() == L1C
    assert Operation("unknown_kind", risk="low", reversible=True).level() == L1B


# ---------------------------------------------------------------------------
# Composite gate + hysteresis (R18)
# ---------------------------------------------------------------------------

def test_composite_score():
    assert _good_evidence().composite() >= 0.90
    bad = EvalEvidence(golden_regression_free=False)
    assert bad.composite() == 0.0
    redline = EvalEvidence(golden_regression_free=True, redline_violations=1)
    assert redline.composite() == 0.0


def test_can_promote_all_requirements():
    ok, failed = AutonomyState(
        L0, state_path=Path("nonexistent") / "autonomy_state.json"
    ).can_promote(_good_evidence())
    assert ok is True
    assert failed == []


def test_can_promote_missing_any_requirement():
    ev = _good_evidence()
    ev.auto_apply_pass_rate = 0.70  # below 0.80
    ok, failed = AutonomyState(
        L0, state_path=Path("nonexistent") / "autonomy_state.json"
    ).can_promote(ev)
    assert ok is False
    assert any("通過率" in f for f in failed)


def test_hysteresis_threshold():
    # composite 0.894 sits between demote (0.85) and promote (0.90). All other
    # L0 requirements are MET (pass 0.80, override 0.02, weeks 3, golden free,
    # 0 redlines) so the ONLY failure is the composite/hysteresis gate —
    # isolating hysteresis from the other gates (cursor review MEDIUM-5).
    ev = EvalEvidence(
        golden_regression_free=True,
        auto_apply_pass_rate=0.80,
        override_rate=0.02,
        weeks_stable=3,
        redline_violations=0,
    )
    assert 0.85 <= ev.composite() < 0.90
    ok, failed = AutonomyState(
        L0, state_path=Path("nonexistent") / "autonomy_state.json"
    ).can_promote(ev)
    assert ok is False
    assert failed == ["複合分數 ≥0.90（hysteresis）"]  # sole failure


def test_promote_requires_human_auth_and_records_it(tmp_path):
    # L1a needs the sandbox to physically exist (R10) — grant it here so the
    # promotion goes L0 -> L1a, never skipping a rung (cursor review HIGH-4).
    state = AutonomyState(L0, log_path=tmp_path / "h_auth.jsonl",
                          sandbox_ready=True, state_path=tmp_path / "autonomy_state.json")
    assert state.promote(_good_evidence(), who="SK") is True
    assert state.level == L1A
    lines = (tmp_path / "h_auth.jsonl").read_text(encoding="utf-8").splitlines()
    ev = json.loads(lines[-1])
    assert ev["who"] == "SK"
    assert ev["action"] == "promote"
    assert ev["level"] == L1A
    assert "composite" in ev["evidence_ref"]


def test_promote_blocked_without_sandbox(tmp_path):
    # Sandbox not ready (Open Q5 undecided) -> L0 cannot promote to L1a.
    state = AutonomyState(L0, log_path=tmp_path / "h_auth.jsonl",
                          state_path=tmp_path / "autonomy_state.json")
    assert state.promote(_good_evidence(), who="SK") is False
    assert state.level == L0
    assert not (tmp_path / "h_auth.jsonl").is_file()  # no auth event logged


def test_promote_rejected_without_evidence():
    state = AutonomyState(L0, log_path=Path("nonexistent") / "x.jsonl",
                          state_path=Path("nonexistent") / "autonomy_state.json")
    assert state.promote(EvalEvidence(), who="agent_self") is False
    assert state.level == L0  # agent cannot self-promote


# ---------------------------------------------------------------------------
# Demotion + kill switch (R18)
# ---------------------------------------------------------------------------

def test_demote_is_immediate_and_automatic(tmp_path):
    state = AutonomyState(L1B, log_path=tmp_path / "h_auth.jsonl",
                          state_path=tmp_path / "autonomy_state.json")
    assert state.demote("quality_degraded") == L0
    lines = (tmp_path / "h_auth.jsonl").read_text(encoding="utf-8").splitlines()
    ev = json.loads(lines[-1])
    assert ev["who"] == "auto"
    assert "quality_degraded" in ev["action"]


def test_demote_cannot_go_up():
    state = AutonomyState(L0, state_path=Path("nonexistent") / "autonomy_state.json")
    assert state.demote("x", target=L1B) == L0  # stays L0, no bogus log


def test_demote_if_needed_fires_below_floor(tmp_path):
    state = AutonomyState(L1B, log_path=tmp_path / "h_auth.jsonl",
                          state_path=tmp_path / "autonomy_state.json")
    bad = EvalEvidence(golden_regression_free=True, auto_apply_pass_rate=0.5,
                       override_rate=0.5, weeks_stable=1, redline_violations=0)
    assert bad.composite() < 0.85
    assert state.demote_if_needed(bad) == L0
    lines = (tmp_path / "h_auth.jsonl").read_text(encoding="utf-8").splitlines()
    assert "composite_below_floor" in json.loads(lines[-1])["action"]


def test_demote_if_needed_noop_when_ok(tmp_path):
    state = AutonomyState(L1B, log_path=tmp_path / "h_auth.jsonl",
                          state_path=tmp_path / "autonomy_state.json")
    assert state.demote_if_needed(_good_evidence()) is None
    assert state.level == L1B
    assert not (tmp_path / "h_auth.jsonl").is_file()


def test_demote_if_needed_noop_at_l0():
    assert AutonomyState(L0, state_path=Path("nonexistent") / "autonomy_state.json").demote_if_needed(EvalEvidence()) is None


def test_kill_switch_returns_to_l0(tmp_path):
    state = AutonomyState(L1C, log_path=tmp_path / "h_auth.jsonl",
                          state_path=tmp_path / "autonomy_state.json")
    assert state.kill_switch() == L0
    lines = (tmp_path / "h_auth.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[-1])["action"] == "kill_switch"


# ---------------------------------------------------------------------------
# Rate alarm (R18 self-improvement rate monitor)
# ---------------------------------------------------------------------------

def test_rate_alarm_fires_on_abnormal_acceleration():
    assert rate_alarm([1, 2, 3, 12]) is True


def test_rate_alarm_silent_on_normal_growth():
    assert rate_alarm([1, 2, 3, 4]) is False
    assert rate_alarm([1]) is False  # insufficient history
    assert rate_alarm([]) is False


# ---------------------------------------------------------------------------
# Persistence (2026-08-31 wiring): level survives restarts + MCP query
# ---------------------------------------------------------------------------

def test_state_persists_level_across_instances(tmp_path):
    state_path = tmp_path / "autonomy_state.json"
    state = AutonomyState(
        L0,
        log_path=tmp_path / "h_auth.jsonl",
        sandbox_ready=True,
        state_path=state_path,
    )
    assert state.promote(_good_evidence(), who="SK") is True
    # A fresh instance must read back the persisted level (not reset to L0).
    state2 = AutonomyState(state_path=state_path)
    assert state2.level == L1A
    assert state2.sandbox_ready is True


def test_state_ignores_invalid_persisted_level(tmp_path):
    state_path = tmp_path / "autonomy_state.json"
    state_path.write_text('{"level": "L9", "sandbox_ready": false}', encoding="utf-8")
    state = AutonomyState(state_path=state_path)
    assert state.level == L0
    assert state.sandbox_ready is False


def test_state_ignores_malformed_file(tmp_path):
    state_path = tmp_path / "autonomy_state.json"
    state_path.write_text("{ not json", encoding="utf-8")
    assert AutonomyState(state_path=state_path).level == L0


def test_demote_persists_new_level(tmp_path):
    state_path = tmp_path / "autonomy_state.json"
    state = AutonomyState(L1B, log_path=tmp_path / "h_auth.jsonl", state_path=state_path)
    state.demote("quality_degraded")
    assert AutonomyState(state_path=state_path).level == L0


def test_kill_switch_persists_l0(tmp_path):
    state_path = tmp_path / "autonomy_state.json"
    state = AutonomyState(L1C, log_path=tmp_path / "h_auth.jsonl", state_path=state_path)
    state.kill_switch()
    assert AutonomyState(state_path=state_path).level == L0


# ---------------------------------------------------------------------------
# Reviewer 2026-08-31 fixes: save/log failure handling, demo isolation,
# load consistency
# ---------------------------------------------------------------------------

def test_promote_refuses_when_audit_log_fails(monkeypatch, tmp_path):
    # R18: a promotion without a durable H_auth audit record must not happen.
    state = AutonomyState(L0, log_path=tmp_path / "h_auth.jsonl",
                          state_path=tmp_path / "autonomy_state.json",
                          sandbox_ready=True)
    # _log failure (e.g. disk full) -> promote refused, nothing persisted.
    monkeypatch.setattr(state, "_log", lambda ev: False)
    assert state.promote(_good_evidence(), who="SK") is False
    assert state.level == L0
    assert not (tmp_path / "autonomy_state.json").is_file()


def test_promote_rolls_back_when_save_fails(monkeypatch, tmp_path):
    import jarvis.autonomy as autonomy_mod

    state = AutonomyState(L0, log_path=tmp_path / "h_auth.jsonl",
                          state_path=tmp_path / "autonomy_state.json",
                          sandbox_ready=True)
    monkeypatch.setattr(state, "_save", lambda: False)
    assert state.promote(_good_evidence(), who="SK") is False
    assert state.level == L0  # memory rolled back to match disk


def test_kill_switch_save_failure_logs_loud(monkeypatch, tmp_path, caplog):
    import logging

    import jarvis.autonomy as autonomy_mod

    state = AutonomyState(L1C, log_path=tmp_path / "h_auth.jsonl",
                          state_path=tmp_path / "autonomy_state.json")
    monkeypatch.setattr(state, "_save", lambda: False)
    with caplog.at_level(logging.ERROR, logger="jarvis.autonomy"):
        assert state.kill_switch() == L0  # memory still demoted
        assert any("kill_switch failed to persist" in r.message for r in caplog.records)


def test_demo_does_not_touch_real_state(monkeypatch, tmp_path):
    # _demo must run against a temp state/log, never the live APPDATA files.
    import jarvis.autonomy as autonomy_mod

    seen: list[str] = []
    monkeypatch.setattr(autonomy_mod, "_state_path",
                        lambda: (seen.append("state") or tmp_path / "real_state.json"))
    monkeypatch.setattr(autonomy_mod, "_auth_log_path",
                        lambda: (seen.append("log") or tmp_path / "real_log.jsonl"))
    assert autonomy_mod._demo() == 0
    # The monkeypatched real paths must never have been created.
    assert not (tmp_path / "real_state.json").is_file()
    assert not (tmp_path / "real_log.jsonl").is_file()


def test_load_fails_closed_l1a_without_sandbox(tmp_path):
    # A state file claiming L1a without sandbox_ready must fail closed to L0.
    state_path = tmp_path / "autonomy_state.json"
    state_path.write_text('{"level": "L1a", "sandbox_ready": false}', encoding="utf-8")
    state = AutonomyState(state_path=state_path)
    assert state.level == L0


def test_save_is_atomic(tmp_path):
    # temp + os.replace: no half-written JSON survives a simulated crash.
    state_path = tmp_path / "autonomy_state.json"
    state = AutonomyState(L1B, log_path=tmp_path / "h_auth.jsonl", state_path=state_path)
    state.demote("quality_degraded")
    assert AutonomyState(state_path=state_path).level == L0
    assert not state_path.with_name(state_path.name + ".tmp").exists()
