"""Tests for jarvis.clarify (Self-Evol Task 6, Phase E v2, 2026-08-30).

Covers the plan's acceptance criteria:
- EVPI gate: ask only when unknowns are non-empty AND change the action;
  confidence is a secondary signal, not the sole gate (R12).
- Question selection: <=5 in round 1, <=2 in round 2, impactful first.
- 2-round cap: after round 2 the session forces proceed.
- Conservative fallback per task type (delete -> don't delete, send -> don't
  send, generate -> most generic reading).
- Precision log appends valid JSONL.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.clarify import (  # noqa: E402
    MAX_QUESTIONS_ROUND1,
    MAX_QUESTIONS_ROUND2,
    ClarifySession,
    Understanding,
    Unknown,
    conservative_assumption,
    log_clarify_event,
    select_questions,
    should_ask,
)


def _u(
    task: str = "test task",
    unknowns: list[Unknown] | None = None,
    assumptions: list[str] | None = None,
    confidence: float = 70.0,
    task_type: str = "other",
) -> Understanding:
    return Understanding(
        task=task,
        unknowns=unknowns or [],
        assumptions=assumptions or [],
        confidence=confidence,
        task_type=task_type,
    )


def _uk(
    qid: str,
    impact: bool = True,
    category: str = "範圍",
    options: list[str] | None = None,
    gain: float = 1.0,
) -> Unknown:
    return Unknown(
        id=qid,
        question=f"Q {qid}",
        category=category,
        impact=impact,
        options=options or [],
        gain=gain,
    )


# ---------------------------------------------------------------------------
# EVPI gate (E1 / R12)
# ---------------------------------------------------------------------------

def test_should_ask_false_when_no_unknowns():
    assert should_ask(_u()) is False


def test_should_ask_false_when_unknowns_do_not_change_action():
    # Unknowns exist but both answers lead to the same action -> don't ask.
    u = _u(unknowns=[_uk("U1", impact=False), _uk("U2", impact=False)])
    assert should_ask(u) is False


def test_should_ask_true_when_unknown_changes_action():
    u = _u(unknowns=[_uk("U1", impact=True)])
    assert should_ask(u) is True


def test_should_ask_true_when_mixed_unknowns():
    # One impactful unknown among harmless ones is enough (EVPI).
    u = _u(unknowns=[_uk("U1", impact=False), _uk("U2", impact=True)])
    assert should_ask(u) is True


def test_confidence_is_not_the_sole_gate():
    # High confidence with impactful unknowns still asks (R12: raw
    # confidence is overconfident; the unknown itself is the trigger).
    u = _u(unknowns=[_uk("U1", impact=True)], confidence=95.0)
    assert should_ask(u) is True
    # Low confidence with zero impactful unknowns does NOT ask.
    u2 = _u(unknowns=[_uk("U1", impact=False)], confidence=30.0)
    assert should_ask(u2) is False


# ---------------------------------------------------------------------------
# Question selection (E2)
# ---------------------------------------------------------------------------

def test_select_questions_caps_at_five():
    unknowns = [_uk(f"U{i}") for i in range(8)]
    picked = select_questions(unknowns)
    assert len(picked) <= MAX_QUESTIONS_ROUND1


def test_select_questions_prioritizes_impactful():
    unknowns = [
        _uk("U1", impact=False, gain=5.0),
        _uk("U2", impact=True, gain=1.0),
        _uk("U3", impact=True, gain=2.0),
    ]
    picked = select_questions(unknowns, max_q=2)
    assert [u.id for u in picked] == ["U3", "U2"]


def test_select_questions_respects_round2_cap():
    unknowns = [_uk(f"U{i}") for i in range(5)]
    picked = select_questions(unknowns, max_q=MAX_QUESTIONS_ROUND2)
    assert len(picked) <= MAX_QUESTIONS_ROUND2


def test_select_questions_deterministic_order():
    unknowns = [_uk("U1", impact=True, gain=1.0), _uk("U2", impact=True, gain=1.0)]
    a = [u.id for u in select_questions(unknowns)]
    b = [u.id for u in select_questions(unknowns)]
    assert a == b


# ---------------------------------------------------------------------------
# Session / 2-round cap (E2 / E3)
# ---------------------------------------------------------------------------

def test_round1_returns_questions_round2_followups_then_none():
    u = _u(unknowns=[_uk(f"U{i}") for i in range(6)])
    s = ClarifySession(u)
    q1 = s.next_round()
    assert q1 is not None
    assert len(q1) <= MAX_QUESTIONS_ROUND1
    assert s.rounds_used == 1

    q2 = s.next_round()
    assert q2 is not None
    assert len(q2) <= MAX_QUESTIONS_ROUND2
    assert s.rounds_used == 2
    # No repeated questions across rounds.
    asked = {x.id for x in q1} | {x.id for x in q2}
    assert len(asked) == len(q1) + len(q2)

    assert s.next_round() is None  # force proceed after round 2
    assert s.done is True


def test_round2_questions_are_unasked_only():
    u = _u(unknowns=[_uk("U1"), _uk("U2"), _uk("U3")])
    s = ClarifySession(u)
    q1 = s.next_round()
    q2 = s.next_round()
    q1_ids = {x.id for x in q1 or []}
    q2_ids = {x.id for x in q2 or []}
    assert q1_ids.isdisjoint(q2_ids)


def test_next_round_never_asks_non_impactful():
    # EVPI (R12): questions that cannot change the action are never posed,
    # even if the round cap has room (cursor review HIGH-3).
    u = _u(unknowns=[_uk("U1", impact=False), _uk("U2", impact=False)])
    s = ClarifySession(u)
    assert s.next_round() is None  # nothing impactful -> force proceed
    assert s.proceed()["rounds_used"] == 1


def test_proceed_covers_asked_but_unanswered(tmp_path):
    # Asked-but-unanswered unknowns still get a conservative assumption
    # (cursor review HIGH-2) — `_asked_ids` is not the same as answered.
    u = _u(
        task="delete temp files",
        unknowns=[_uk("U1", impact=True, options=["只刪 temp", "刪埋 cache"])],
        task_type="delete",
    )
    s = ClarifySession(u, log_path=tmp_path / "clarify.jsonl")
    q1 = s.next_round()
    assert q1 is not None and [x.id for x in q1] == ["U1"]
    # User never answers; proceed must still assume conservatively for U1.
    plan = s.proceed()
    assert any("唔刪除" in a for a in plan["assumptions"])


def test_record_answers_excludes_from_fallback(tmp_path):
    u = _u(
        task="delete temp files",
        unknowns=[_uk("U1", impact=True, options=["只刪 temp", "刪埋 cache"])],
        task_type="delete",
    )
    s = ClarifySession(u, log_path=tmp_path / "clarify.jsonl")
    s.next_round()
    s.record_answers(["U1"])  # user answered
    plan = s.proceed()
    assert all("唔刪除" not in a for a in plan["assumptions"])


def test_proceed_returns_conservative_assumptions():
    # 6 unknowns: round 1 asks 5 (cap), the lowest-gain one stays unresolved
    # -> proceed() falls back to a conservative assumption for it.
    unknowns = [_uk(f"U{i}", impact=True) for i in range(1, 7)]
    unknowns[-1].gain = 0.01
    u = _u(
        task="remove temp files",
        unknowns=unknowns,
        task_type="delete",
    )
    s = ClarifySession(u)
    q1 = s.next_round()
    assert q1 is not None and len(q1) == 5
    plan = s.proceed()
    assert plan["rounds_used"] == 1
    assert len(plan["assumptions"]) >= 1
    assert "唔刪除任何嘢" in plan["assumptions"][0]


# ---------------------------------------------------------------------------
# Conservative fallback (E3)
# ---------------------------------------------------------------------------

def test_conservative_delete_does_not_delete():
    assert "唔刪除" in conservative_assumption("delete")


def test_conservative_send_does_not_send():
    assert "唔發送" in conservative_assumption("send")


def test_conservative_generate_most_generic():
    assert "最通用" in conservative_assumption("generate")


def test_conservative_unknown_task_type_defaults_to_other():
    assert "唔改變現狀" in conservative_assumption("unknown_type")


def test_conservative_with_unknown_includes_safe_option():
    uk = _uk("U1", options=["立即執行", "先計劃再執行"])
    out = conservative_assumption("send", uk)
    assert "先計劃再執行" in out


# ---------------------------------------------------------------------------
# Precision log (E4)
# ---------------------------------------------------------------------------

def test_log_appends_jsonl(tmp_path):
    log_path = tmp_path / "clarify_log.jsonl"
    log_clarify_event(log_path, {"event": "ask", "rounds_used": 1, "changed_plan": None})
    log_clarify_event(log_path, {"event": "proceed", "rounds_used": 2, "changed_plan": False})
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["event"] == "ask"
    assert "ts" in first  # timestamp auto-added
    assert first["rounds_used"] == 1
    assert first["changed_plan"] is None


def test_log_best_effort_on_oserror(tmp_path, monkeypatch):
    # A write failure must not raise (gate never breaks over logging).
    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", boom)
    log_clarify_event(tmp_path / "x.jsonl", {"event": "ask"})  # must not raise


def test_understanding_to_dict_is_json_serializable():
    u = _u(
        unknowns=[_uk("U1", impact=True, options=["a", "b"])],
        confidence=72.5,
    )
    d = u.to_dict()
    assert isinstance(d, dict)
    assert d["confidence"] == 72.5
    assert d["unknowns"][0]["impact"] is True
    json.dumps(d, ensure_ascii=False)  # must not raise
