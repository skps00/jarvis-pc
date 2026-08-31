"""JARVIS Clarification Gate (Self-Evol Task 6, Phase E v2).

A structured "do I understand the user's goal well enough to start?"
layer for agents, per the Self-Evol plan (R12/R17, 2026-08-30):

- Structural self-assessment: unknowns -> assumptions -> per-item review
  -> confidence (P(True)-style; raw verbalized confidence is overconfident).
- EVPI trigger: ask ONLY when unknowns are non-empty AND at least one
  unknown would change the action. If both answers lead to the same action,
  do not ask (Alexa: top-1 is right ~77% of the time; users fatigue after
  ~11 questions).
- One round primary, two rounds max: round 1 picks 3-5 structured questions
  (category + concrete options, no free text); round 2 allows only 1-2
  follow-ups; after 2 rounds force proceed.
- Fallback: proceed-with-assumptions. The most conservative assumption is
  task-type dependent (delete -> don't delete, send -> don't send,
  generate -> most generic reading, ...). Listed to the user up front.
- Precision log (feedback loop): every ask is appended to
  %APPDATA%\\Jarvis\\clarify_log.jsonl with "did this change the plan?"
  so the threshold and question quality can be calibrated later.
- Security (R17): user answers are untrusted input — this module never
  executes anything from an answer; it only updates the understanding.

The core logic is deterministic (no LLM dependency) so it is unit-testable.
An LLM may fill in `Unknown`s, but the gate decisions live here.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

MAX_QUESTIONS_ROUND1 = 5
MAX_QUESTIONS_ROUND2 = 2
MAX_ROUNDS = 2

CATEGORIES = ("目標含糊", "範圍", "優先次序", "驗收標準", "約束")

TASK_TYPES = ("delete", "send", "generate", "modify", "other")


@dataclass
class Unknown:
    """One open point that could change how the task is executed."""

    id: str
    question: str
    category: str
    impact: bool  # True = answering this changes the action (EVPI)
    options: list[str] = field(default_factory=list)  # 2-5 concrete readings
    gain: float = 1.0  # information-gain priority hint, higher asked first


@dataclass
class Understanding:
    """Structured self-assessment result (E1)."""

    task: str
    unknowns: list[Unknown]
    assumptions: list[str]
    confidence: float  # 0-100, derived structurally (P(True)-style)
    task_type: str = "other"

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["confidence"] = round(float(d["confidence"]), 1)
        return d


# ---------------------------------------------------------------------------
# EVPI trigger (E1 / R12)
# ---------------------------------------------------------------------------

def should_ask(u: Understanding) -> bool:
    """True when unknowns are non-empty AND at least one changes the action.

    Confidence is deliberately NOT the primary gate (R12): verbalized
    confidence is systematically overconfident; the EVPI principle is.
    """
    if not u.unknowns:
        return False
    return any(uk.impact for uk in u.unknowns)


def select_questions(
    unknowns: list[Unknown], max_q: int = MAX_QUESTIONS_ROUND1
) -> list[Unknown]:
    """Pick the highest-information-gain questions, capped at `max_q`.

    Impactful unknowns first, then by gain, then stable by id (deterministic).
    """
    ranked = sorted(
        unknowns,
        key=lambda u: (u.impact, u.gain, u.id),
        reverse=True,
    )
    return ranked[:max_q]


# ---------------------------------------------------------------------------
# Conservative fallback assumptions (E3)
# ---------------------------------------------------------------------------

_DEFAULT_ASSUMPTIONS: dict[str, str] = {
    "delete": "唔刪除任何嘢（假設對象未確認）",
    "send": "唔發送任何嘢（假設內容/收件人未確認）",
    "generate": "用最通用、最直接嘅詮釋生成",
    "modify": "只做可逆、可回滾嘅修改",
    "other": "唔改變現狀，等確認",
}


def conservative_assumption(task_type: str, unknown: Unknown | None = None) -> str:
    """Most-conservative reading for an unresolved unknown, by task type."""
    if task_type not in _DEFAULT_ASSUMPTIONS:
        task_type = "other"
    base = _DEFAULT_ASSUMPTIONS[task_type]
    if unknown is not None and unknown.options:
        # Prefer the safest listed option when available; fall back to base.
        safe = _safest_option(unknown.options, task_type)
        return f"{base}（{unknown.question} → {safe}）"
    return base


def _safest_option(options: list[str], task_type: str) -> str:
    """Pick the conservative option. Naive but deterministic: for destructive
    task types the LAST option is treated as the escape hatch; otherwise keep
    the first (most literal) reading."""
    if task_type in ("delete", "send"):
        return options[-1] if options else "(無選項)"
    return options[0] if options else "(無選項)"


# ---------------------------------------------------------------------------
# Session state machine (E2 / E3): one round primary, two rounds max
# ---------------------------------------------------------------------------

class ClarifySession:
    """Tracks rounds, enforces the 2-round cap, produces the fallback plan.

    Usage:
        s = ClarifySession(understanding, log_path=...)
        q1 = s.next_round()        # <=5 questions
        # ... user answers -> update understanding ...
        q2 = s.next_round()        # <=2 follow-ups
        # ... answers ...
        assert s.next_round() is None   # force proceed
        plan = s.proceed(changed_plan=False)
    """

    def __init__(
        self,
        understanding: Understanding,
        log_path: Path | None = None,
    ) -> None:
        self.u = understanding
        self.log_path = log_path
        self._rounds = 0
        self._asked_ids: set[str] = set()
        self._answered_ids: set[str] = set()

    def record_answers(self, ids: list[str]) -> None:
        """Mark unknowns as answered by the user (call after each round).

        `proceed()` applies conservative assumptions to everything NOT in this
        set — asked-but-unanswered unknowns still get a safe fallback.
        """
        self._answered_ids.update(ids)

    @property
    def rounds_used(self) -> int:
        return self._rounds

    @property
    def done(self) -> bool:
        return self._rounds >= MAX_ROUNDS

    def next_round(self) -> list[Unknown] | None:
        """Return questions for the next round, or None to force proceed.

        Only IMPACTFUL unknowns are asked (EVPI, R12): a question whose answer
        cannot change the action must never burn the user's fatigue budget.
        """
        if self.done:
            return None
        self._rounds += 1
        max_q = MAX_QUESTIONS_ROUND1 if self._rounds == 1 else MAX_QUESTIONS_ROUND2
        fresh = [
            u for u in self.u.unknowns
            if u.id not in self._asked_ids and u.impact
        ]
        chosen = select_questions(fresh, max_q=max_q)
        if not chosen:
            # Nothing worth asking left -> skip to proceed even within cap.
            return None
        self._asked_ids.update(u.id for u in chosen)
        return chosen

    def proceed(
        self,
        changed_plan: bool | None = None,
        note: str = "",
    ) -> dict[str, object]:
        """Force-proceed with conservative assumptions; log the outcome.

        Every still-UNANSWERED unknown gets a conservative assumption —
        including ones that were asked but never answered (cursor review
        2026-08-30 HIGH-2).
        """
        unresolved = [u for u in self.u.unknowns if u.id not in self._answered_ids]
        assumptions = list(self.u.assumptions)
        for u in unresolved:
            assumptions.append(conservative_assumption(self.u.task_type, u))
        # De-duplicate, keep order.
        assumptions = list(dict.fromkeys(assumptions))

        plan = {
            "task": self.u.task,
            "rounds_used": self._rounds,
            "assumptions": assumptions,
            "confidence": self.u.confidence,
            "note": note,
        }
        self._log(
            {
                "event": "proceed",
                "rounds_used": self._rounds,
                "n_questions_asked": len(self._asked_ids),
                "changed_plan": changed_plan,
                "note": note,
                "n_assumptions": len(assumptions),
            }
        )
        return plan

    # ------------------------------------------------------------------
    def _log(self, entry: dict[str, object]) -> None:
        if self.log_path is None:
            return
        log_clarify_event(self.log_path, entry)


# ---------------------------------------------------------------------------
# Precision log (E4 / R12 feedback loop)
# ---------------------------------------------------------------------------

def log_clarify_event(log_path: Path, entry: dict[str, object]) -> None:
    """Append one JSONL record to the calibration log (best-effort)."""
    record = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **entry,
    }
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        # Calibration log is best-effort; never break the gate over it.
        return


def default_log_path() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "clarify_log.jsonl"


# ---------------------------------------------------------------------------
# CLI (demo / manual verification)
# ---------------------------------------------------------------------------

def _demo(task: str, task_type: str) -> int:
    u = Understanding(
        task=task,
        task_type=task_type,
        unknowns=[
            Unknown("U1", "目標係咪要修改現有檔案？", "範圍", True,
                    ["改現有檔", "新開一個檔"], gain=2.0),
            Unknown("U2", "優先次序：即刻做定係等確認？", "優先次序", False,
                    ["即刻做", "等確認"], gain=1.0),
        ],
        assumptions=["跟現有 code style"],
        confidence=70.0,
    )
    print(json.dumps(u.to_dict(), ensure_ascii=False, indent=2))
    print(f"should_ask: {should_ask(u)}")
    s = ClarifySession(u, log_path=default_log_path())
    q1 = s.next_round()
    print(f"round1: {[x.id for x in q1] if q1 else None}")
    q2 = s.next_round()
    print(f"round2: {[x.id for x in q2] if q2 else None}")
    print(f"round3: {s.next_round()}")
    print(json.dumps(s.proceed(), ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="JARVIS Clarification Gate")
    ap.add_argument("--demo", action="store_true", help="run the demo flow")
    ap.add_argument("--task", default="demo task", help="task description")
    ap.add_argument("--task-type", choices=TASK_TYPES, default="other")
    args = ap.parse_args()
    if args.demo:
        return _demo(args.task, args.task_type)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
