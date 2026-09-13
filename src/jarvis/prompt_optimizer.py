"""Prompt Optimizer (Self-Evol Phase F, Task 8 completion, R13).

The plan's L2 Optimizer: offline, GEPA-style reflection evolution for
high-frequency task types, driven by ACCEPTANCE-CRITERIA SCORING (never LLM
self-praise). Winning prompts enter the PatternStore only with score evidence.

Security (R13, the most severe risk):
- The optimizer itself is pure text->text: it has NO tools and NO network
  access. `mutate_llm` and `scorer` are injected by the caller (the scorer is
  execution-based verification).
- The INVARIANT safety block is injected by the system; the optimizer cannot
  rewrite it (mutations that drop it are rejected).
- Every optimized output is diffed against the original and scanned for
  sensitive patterns; on hit -> original is used and the attempt logged.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from jarvis.prompt_pipeline import (
    INVARIANT_BLOCK,
    Pattern,
    PatternStore,
    apply_optimized,
    scan_sensitive,
)

_logger = logging.getLogger("jarvis.prompt_optimizer")

# Callables injected by the caller — the optimizer never calls LLMs directly.
#   mutate_llm: (prompt: str, feedback: str) -> str   (text -> text)
#   scorer:     (prompt: str) -> float                 (execution-based, 0..1)
MutateFn = Callable[[str, str], str]
ScoreFn = Callable[[str], float]


@dataclass
class OptimizeResult:
    task_type: str
    generations: int
    population: int
    best_score: float
    baseline_score: float
    applied: bool  # a winning pattern was stored
    pattern_id: str = ""
    rejected: list[str] = field(default_factory=list)  # injection/score rejects


def _reject(reason: str, detail: str) -> None:
    _logger.warning("optimizer rejected: %s (%s)", reason, detail[:120])


class PromptOptimizer:
    """GEPA-style offline prompt evolution.

    Loop (Kilo): mutate -> score -> keep top -> repeat. Only a score-backed
    winner above the store's min_score is stored (R13: patterns driven by
    measured improvement, never by self-praise).
    """

    def __init__(
        self,
        store: PatternStore,
        mutate_llm: MutateFn,
        scorer: ScoreFn,
        *,
        min_score: float = 0.8,
        improvement_gap: float = 0.02,
    ) -> None:
        self.store = store
        self.mutate = mutate_llm
        self.score = scorer
        self.min_score = min_score
        self.improvement_gap = improvement_gap  # winner must beat baseline by this

    def optimize(
        self,
        task_type: str,
        base_prompt: str,
        *,
        generations: int = 3,
        population: int = 4,
    ) -> OptimizeResult:
        """Evolve `base_prompt` for `generations` rounds. Population size N
        candidates per round (baseline + N-1 mutations)."""
        if INVARIANT_BLOCK not in base_prompt:
            # The system safety block must be present before we evolve anything.
            _reject("missing_invariant_block", "base prompt")
            return OptimizeResult(task_type, generations, population, 0.0, 0.0,
                                  False, rejected=["missing_invariant_block"])

        baseline_score = self._safe_score(base_prompt)
        if baseline_score is None:
            return OptimizeResult(task_type, generations, population, 0.0, 0.0,
                                  False, rejected=["scorer_failed"])

        # population[0] is always the current best (elitism).
        population_list: list[str] = [base_prompt]
        best = base_prompt
        best_score = baseline_score
        rejected: list[str] = []

        for gen in range(1, generations + 1):
            # Produce offspring from the current best.
            offspring: list[str] = []
            for _ in range(max(1, population - 1)):
                kid, reject_reason = self._mutate_safe(
                    best, _feedback(gen, best_score)
                )
                if kid is None:
                    rejected.append(reject_reason or "mutation_rejected")
                    continue
                offspring.append(kid)

            scored: list[tuple[float, str]] = []
            for kid in offspring:
                sc = self._safe_score(kid)
                if sc is None:
                    rejected.append("scorer_failed")
                    continue
                scored.append((sc, kid))

            if not scored:
                continue  # no valid offspring this round

            scored.sort(key=lambda t: t[0], reverse=True)
            new_score, new_best = scored[0]  # (score, prompt)
            if new_score > best_score:
                best, best_score = new_best, new_score
                # Keep the new best in the population (elitism).
                population_list = [best] + [p for _, p in scored[1:]]
            # else: keep previous best; no flapping.

        # Apply only when the winner is a REAL measured improvement.
        applied = False
        pattern_id = ""
        if best_score >= self.min_score and best_score - baseline_score >= self.improvement_gap:
            effective, applied_ok, hits = apply_optimized(base_prompt, best)
            if not applied_ok:
                rejected.append(f"injection:{','.join(hits)}")
            else:
                pattern = Pattern(
                    id=f"opt-{task_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    task_type=task_type,
                    prompt_template=effective,
                    score=round(best_score, 3),
                    won_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    fail_conditions=[f"score drops below {self.min_score}"],
                )
                if self.store.add(pattern, min_score=self.min_score):
                    applied = True
                    pattern_id = pattern.id

        return OptimizeResult(
            task_type=task_type,
            generations=generations,
            population=population,
            best_score=round(best_score, 3),
            baseline_score=round(baseline_score, 3),
            applied=applied,
            pattern_id=pattern_id,
            rejected=rejected,
        )

    # ------------------------------------------------------------------
    def _mutate_safe(self, prompt: str, feedback: str) -> tuple[str | None, str]:
        """Mutation that can never drop the invariant block or INTRODUCE new
        sensitive content. Only NEW patterns (vs the parent) count — the
        invariant block itself legitimately mentions token/key/secret/approval
        as prohibitions. Returns (prompt|None, reject_reason)."""
        candidate = self.mutate(prompt, feedback)
        if not candidate or not isinstance(candidate, str):
            return None, "mutation_invalid"
        if INVARIANT_BLOCK not in candidate:
            _reject("mutation_dropped_invariant", candidate[:80])
            return None, "mutation_dropped_invariant"
        new_hits = sorted(
            set(scan_sensitive(candidate)) - set(scan_sensitive(prompt))
        )
        if new_hits:
            reason = "injection:" + ",".join(new_hits)
            _reject(reason, candidate[:80])
            return None, reason
        return candidate, ""

    def _safe_score(self, prompt: str) -> float | None:
        try:
            sc = float(self.score(prompt))
        except Exception as exc:  # noqa: BLE001 — scorer failure is not fatal
            _reject("scorer_exception", str(exc)[:120])
            return None
        if sc < 0.0 or sc > 1.0 or sc != sc:  # NaN guard
            _reject("scorer_out_of_range", str(sc))
            return None
        return sc


def _feedback(gen: int, score: float) -> str:
    """Short reflection seed — the mutate_llm turns this into a variant."""
    return f"generation {gen}; previous best score {score:.3f}; keep the goal, "
    "tighten acceptance criteria, avoid ambiguity; never touch the system block."


# ---------------------------------------------------------------------------
# CLI (dry-run against a dummy scorer — real scorers are caller-injected)
# ---------------------------------------------------------------------------

def _demo() -> int:
    import tempfile

    from jarvis.prompt_pipeline import TaskSpec, format_task

    with tempfile.TemporaryDirectory() as d:
        store = PatternStore(Path(d) / "patterns.json")
        base = format_task(TaskSpec(
            goal="研究 X", background="context", constraints=["唔好改測試"],
            acceptance=["200 passed"], output_format="一句總結",
        ))
        # Deterministic fake: "better" prompt = contains '明確' marker.
        opt = PromptOptimizer(
            store,
            mutate_llm=lambda p, fb: p + "\n（明確）",
            scorer=lambda p: 0.95 if "（明確）" in p else 0.50,
        )
        res = opt.optimize("research", base, generations=2, population=2)
        print(json.dumps({
            "baseline": res.baseline_score,
            "best": res.best_score,
            "applied": res.applied,
            "pattern_id": res.pattern_id,
            "rejected": res.rejected,
        }, ensure_ascii=False))
    return 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="JARVIS Prompt Optimizer (Phase F, offline)")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return _demo()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
