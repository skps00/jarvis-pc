"""Autonomy Ladder framework (Self-Evol Task 9, Phase D v2, R10/R18).

Earned autonomy with per-operation grading (NOT whole-agent levels):

- L0   = today: suggest -> SK approves -> execute (human gate).
- L1a  = fully automatic INSIDE a sandbox (filesystem + network isolation).
- L1b  = automatic low-risk apply (full lineage, revertible, over-threshold
         escalates to human).
- L1c  = high-risk, always human (irreversible / destructive / exfiltration /
         evaluator / policy changes).

Transition rules (R18, AWS pattern):
- Promotion requires a rolling-window of sustained performance (not a single
  good run), a recorded human authorization event (H_auth log), and evidence.
- Demotion is immediate, automatic and asymmetric (quality degrade -> down,
  no approval needed); granularity is per-permission, and SK keeps a one-key
  full rollback (kill switch).
- Hysteresis: the promotion threshold sits ABOVE the demotion threshold to
  prevent flapping.
- Safety score and capability score are computed separately — safety is an
  independent floor, never averaged away.

Hard red lines (METR / DGM / Anthropic): no persistent self-replication,
evaluator/golden-set/approval rules physically outside agent write access,
subagents cannot spawn subagents, no agent may change its own permissions.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

_logger = logging.getLogger("jarvis.autonomy")

L0 = "L0"
L1A = "L1a"
L1B = "L1b"
L1C = "L1c"
LEVELS = (L0, L1A, L1B, L1C)

# Per-operation classification (R10). Higher number = more autonomy.
_OPERATION_LEVELS = {
    "sandbox_explore": L1A,   # inside sandbox, fully isolated
    "apply_low_risk": L1B,    # reversible, small blast radius, low risk
    "apply_medium_risk": L1B, # reversible, medium risk
    "irreversible": L1C,      # deletes, destructive
    "exfiltration_touch": L1C,  # anything touching credentials/secrets outbound
    "evaluator_change": L1C,  # evaluator / golden set / approval rules / policy
    "spawn_agent": L1C,       # spawning agents is human-gated (R9)
    "config_change": L1C,     # control-plane config
}

# Hysteresis (R18): promotion needs MORE evidence than staying demoted.
PROMOTE_THRESHOLD = 0.90
DEMOTE_THRESHOLD = 0.85

_RATE_LIMIT = 5  # auto-applies per week above which the rate alarm fires


@dataclass
class Operation:
    kind: str
    blast_radius: int = 1  # files touched
    reversible: bool = True
    risk: str = "low"  # low | medium | high

    def level(self) -> str:
        """Per-operation autonomy level (R10)."""
        if self.kind in _OPERATION_LEVELS:
            return _OPERATION_LEVELS[self.kind]
        if not self.reversible or self.risk == "high" or self.blast_radius > 5:
            return L1C
        return L1B  # reversible low/medium risk outside sandbox -> L1b


@dataclass
class EvalEvidence:
    """Composite promotion evidence (R18: rolling window, not one run)."""
    golden_regression_free: bool = False
    auto_apply_pass_rate: float = 0.0  # execution-verified, not LLM self-score
    override_rate: float = 1.0  # % of auto-apply SK overrode (lower is better)
    weeks_stable: int = 0
    redline_violations: int = 0

    def composite(self) -> float:
        """Capability score — safety is NOT averaged in (R18)."""
        if not self.golden_regression_free:
            return 0.0
        if self.redline_violations:
            return 0.0
        score = 0.0
        score += min(self.auto_apply_pass_rate, 1.0) * 0.5
        score += max(0.0, 1.0 - self.override_rate) * 0.3
        score += min(self.weeks_stable / 2.0, 1.0) * 0.2
        return round(score, 3)


@dataclass
class AuthEvent:
    who: str
    action: str
    level: str
    evidence_ref: str = ""
    ts: str = ""

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["ts"] = self.ts or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return d


def _auth_log_path() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "h_auth.log.jsonl"


def _state_path() -> Path:
    """Persisted autonomy level — MCP/status tools read this; without it the
    level would live only in memory and reset to L0 on every restart."""
    return Path(os.environ.get("APPDATA", "")) / "Jarvis" / "autonomy_state.json"


class AutonomyState:
    """Tracks the current level, safety floor, and promotion/demotion rules.

    Level is persisted to ``autonomy_state.json`` (APPDATA\\Jarvis) so the
    gate survives restarts and can be queried by Hermes via MCP.
    """

    def __init__(
        self,
        level: str = L0,
        log_path: Path | None = None,
        sandbox_ready: bool = False,
        state_path: Path | None = None,
    ) -> None:
        self.log_path = log_path or _auth_log_path()
        self.state_path = state_path or _state_path()
        # L1a prerequisite: sandbox (filesystem + network isolation) must
        # physically exist before ANY sandbox-only autonomy is granted.
        # Open Q5 (Docker vs WSL2) not decided -> stays False (cursor review
        # 2026-08-30 HIGH-4).
        self.sandbox_ready = sandbox_ready
        self.level = level
        self._load()

    def _load(self) -> None:
        """Restore persisted level/sandbox flag (best-effort, never crash)."""
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        lvl = str(data.get("level") or L0)
        if lvl in LEVELS:
            self.level = lvl
        if isinstance(data.get("sandbox_ready"), bool):
            self.sandbox_ready = data["sandbox_ready"]
        # Consistency red line: L1a (sandbox-internal autonomy) must NEVER be
        # restored without a physical sandbox — an agent must not inherit
        # sandbox autonomy on paper (hand-edited/old-schema file). Fail-closed
        # to L0; L1b/L1c are sandbox-external levels and don't require it.
        if self.level == L1A and not self.sandbox_ready:
            _logger.warning("state file claims L1a without sandbox_ready — "
                            "failing closed to L0")
            self.level = L0

    def _save(self) -> bool:
        """Persist level + sandbox flag atomically. Returns success so callers
        can treat a failed write as a real error (silent failure would let a
        stale HIGHER level file come back after restart — fail-open)."""
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_path.with_name(self.state_path.name + ".tmp")
            tmp.write_text(
                json.dumps(
                    {"level": self.level, "sandbox_ready": self.sandbox_ready},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            os.replace(tmp, self.state_path)
            return True
        except OSError as exc:
            _logger.warning("autonomy state save failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    def _next_level(self) -> str | None:
        """Next rung UP the ladder — never skip a rung (R10)."""
        return {L0: L1A, L1A: L1B, L1B: L1C}.get(self.level)

    def can_promote(self, evidence: EvalEvidence) -> tuple[bool, list[str]]:
        """Composite gate + hysteresis. All requirements must hold (R18)."""
        if self.level == L0:
            reqs = [
                ("golden 0 regression", evidence.golden_regression_free),
                ("apply 通過率 ≥80%", evidence.auto_apply_pass_rate >= 0.80),
                ("override rate <3%", evidence.override_rate < 0.03),
                ("生產-like 穩定 ≥2 週", evidence.weeks_stable >= 2),
                ("0 紅線違反", evidence.redline_violations == 0),
                ("複合分數 ≥0.90（hysteresis）", evidence.composite() >= PROMOTE_THRESHOLD),
            ]
        elif self.level == L1A or self.level == L1B:
            reqs = [
                ("golden+regression 連續 2 週無 regression", evidence.golden_regression_free and evidence.weeks_stable >= 2),
                ("0 紅線違反", evidence.redline_violations == 0),
                ("複合分數 ≥0.90", evidence.composite() >= PROMOTE_THRESHOLD),
            ]
        else:  # L1c -> higher levels need long-horizon tasks; not implemented yet
            reqs = [("更高級需要長任務集 eval（未建）", False)]
        failed = [name for name, ok in reqs if not ok]
        return (not failed), failed

    def promote(self, evidence: EvalEvidence, who: str = "SK") -> bool:
        """Promote ONE step after an explicit human authorization event (R18:
        an agent can never promote itself; every step is auditable)."""
        ok, _ = self.can_promote(evidence)
        if not ok:
            return False
        nxt = self._next_level()
        if nxt is None:
            return False
        if nxt == L1A and not self.sandbox_ready:
            # Sandbox must exist first — never grant sandbox autonomy on paper.
            return False
        # R18: a promotion without a durable H_auth audit record must not
        # happen — refuse rather than promote silently.
        if not self._log(AuthEvent(who=who, action="promote", level=nxt,
                                   evidence_ref=f"composite={evidence.composite()}")):
            _logger.error("promote to %s refused: H_auth audit log write failed", nxt)
            return False
        old = self.level
        self.level = nxt
        if not self._save():
            # Keep memory consistent with disk (fail-closed: revert the step).
            self.level = old
            return False
        return True

    def demote(self, reason: str, target: str = L0) -> str:
        """Immediate automatic asymmetric demotion — no approval needed."""
        if LEVELS.index(target) >= LEVELS.index(self.level):
            return self.level  # demotion must go DOWN
        old = self.level
        self._log(AuthEvent(who="auto", action=f"demote:{reason}", level=target))
        self.level = target
        if not self._save():
            # Demotion is a SAFETY action; a failed persist means the old
            # HIGHER level file survives and will return after restart
            # (fail-open). Memory is already demoted for this process — log
            # loudly so the caller can surface the problem.
            _logger.error(
                "demote %s -> %s failed to persist; old level %s will return "
                "on restart", old, target, old,
            )
        return self.level

    def demote_if_needed(self, evidence: EvalEvidence) -> str | None:
        """Score-driven automatic demotion (R18 hysteresis floor).

        When the composite capability score drops below DEMOTE_THRESHOLD the
        state demotes to L0 immediately — asymmetric with promotion (promote
        needs 0.90, demote fires at <0.85). Returns the new level or None.
        """
        if self.level == L0:
            return None
        if evidence.composite() < DEMOTE_THRESHOLD:
            return self.demote("composite_below_floor")
        return None

    def kill_switch(self, who: str = "SK") -> str:
        """One-key full rollback to L0 (human-triggered)."""
        self._log(AuthEvent(who=who, action="kill_switch", level=L0))
        self.level = L0
        if not self._save():
            # Same fail-open risk as demote: the stale higher-level file would
            # silently restore autonomy after restart. Memory is L0 now.
            _logger.error("kill_switch failed to persist; old autonomy level "
                          "will return on restart")
        return self.level

    def _log(self, ev: AuthEvent) -> bool:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(ev.to_dict(), ensure_ascii=False) + "\n")
            return True
        except OSError as exc:
            _logger.warning("h_auth log write failed: %s", exc)
            return False


def rate_alarm(weekly_auto_applies: list[int]) -> bool:
    """Self-improvement rate monitor (R18): abnormal acceleration -> demote."""
    if len(weekly_auto_applies) < 2:
        return False
    latest = weekly_auto_applies[-1]
    prev = max(weekly_auto_applies[:-1])
    return latest > _RATE_LIMIT and latest > prev * 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _demo() -> int:
    import tempfile

    # Demo must NEVER touch the real APPDATA state/log (it would clobber the
    # live autonomy level — reviewer 2026-08-31 HIGH).
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        state = AutonomyState(level=L0, log_path=base / "_demo_h_auth.jsonl",
                              state_path=base / "_demo_state.json")
        for op_kind in ("sandbox_explore", "apply_low_risk", "irreversible", "evaluator_change"):
            op = Operation(kind=op_kind)
            print(f"{op_kind:18} -> {op.level()}")
        ev = EvalEvidence(golden_regression_free=True, auto_apply_pass_rate=0.95,
                          override_rate=0.01, weeks_stable=3, redline_violations=0)
        print(f"composite={ev.composite()} can_promote={state.can_promote(ev)}")
        print(f"promote -> {state.promote(ev)} level={state.level}")
        print(f"rate_alarm([1,2,3,12]) -> {rate_alarm([1, 2, 3, 12])}")
        print(f"kill_switch -> {state.kill_switch()}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="JARVIS Autonomy Ladder (Phase D)")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return _demo()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
