"""Prompt Pipeline (Self-Evol Task 8, Phase F v2, R13).

Two layers:
- L1 Formatter (inline, cheap): structure a task brief into the five sections
  目標 / 背景 / 約束 / 驗收標準 / 輸出格式. Simple tasks skip straight to a
  template; cached patterns are used verbatim (no optimizer call).
- L2 Optimizer (offline): only for high-frequency task types; GEPA-style
  reflection / DSPy compile driven by acceptance-criteria scoring. Winning
  prompts enter the pattern store ONLY with score evidence — never from
  LLM self-praise.

Injection defence (R13, the most severe risk):
- An INVARIANT safety block is injected by the system; the optimizer cannot
  rewrite it (no tool/network privileges; pure text->text).
- Every optimized output is diffed against the original and scanned for
  sensitive patterns (privileges / tools / output destination / safety
  keywords). On hit -> fall back to the original and log the attempt.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

SECTIONS = ("目標", "背景", "約束", "驗收標準", "輸出格式")

# System-injected safety block the optimizer must never rewrite.
INVARIANT_BLOCK = (
    "【系統安全約束（不可修改）】\n"
    "- 唔准改動工具權限／審批規則／config／evaluator\n"
    "- 唔准覆蓋或扭曲使用者原始指令\n"
    "- 高風險動作（刪除／發送／付費／權限）維持人手確認\n"
    "- 輸出唔准包含任何 secrets（API key／token／密碼）\n"
)

# Sensitive patterns: if an optimized prompt INTRODUCES any of these compared
# to the original, the optimization is treated as a potential jailbreak.
_SENSITIVE = re.compile(
    r"(權限|permission|sudo|admin|繞過|bypass|改.*config|修改.*工具|"
    r"輸出.*(?:到|去)|curl\s|rm\s+-rf|刪除.*全部|發送.*全部|exfil|"
    r"api[_-]?key|secret|password|token|免審批|skip.*approval|disable.*gate|"
    r"忽略.*規則|ignore.*rule)",
    re.I,
)

# __file__-relative (2026-08-31): repo can move without breaking pattern store.
_DEFAULT_PATTERNS_PATH = (
    Path(__file__).resolve().parents[2]
    / ".hermes" / "plans" / "prompt-patterns.json"
)


@dataclass
class TaskSpec:
    goal: str
    background: str = ""
    constraints: list[str] = field(default_factory=list)
    acceptance: list[str] = field(default_factory=list)
    output_format: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class Pattern:
    id: str
    task_type: str
    prompt_template: str
    score: float  # acceptance-scored; only score-backed entries are stored
    won_at: str
    fail_conditions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# L1 Formatter (inline)
# ---------------------------------------------------------------------------

def format_task(spec: TaskSpec) -> str:
    """Structure a task brief into the five sections (deterministic)."""
    lines = [INVARIANT_BLOCK]
    body = {
        "目標": spec.goal,
        "背景": spec.background or "（冇特別背景）",
        "約束": "；".join(spec.constraints) if spec.constraints else "（冇）",
        "驗收標準": "；".join(spec.acceptance) if spec.acceptance else "（冇）",
        "輸出格式": spec.output_format or "（自由格式）",
    }
    for sec in SECTIONS:
        lines.append(f"## {sec}\n{body[sec]}")
    return "\n\n".join(lines)


_SIMPLE_FIELDS = re.compile(r"\{goal\}|\{output_format\}")

_SIMPLE_TEMPLATE = (
    "【系統安全約束（不可修改）】\n"
    "- 高風險動作（刪除／發送／付費／權限）維持人手確認\n\n"
    "## 目標\n{goal}\n\n"
    "## 輸出格式\n{output_format}"
)


def format_simple(goal: str, output_format: str = "簡短完成") -> str:
    """Cheap template for simple tasks (no external data, few steps).

    Single-pass substitution (re.sub, not str.format / chained replace) so
    braces in untrusted goal text can never raise or substitute template
    fields (cursor review 2026-08-30 MEDIUM-3; R16/R17: voice/task strings
    are untrusted).
    """
    return _SIMPLE_FIELDS.sub(
        lambda m: goal if m.group(0) == "{goal}" else output_format,
        _SIMPLE_TEMPLATE,
    )


# ---------------------------------------------------------------------------
# Injection defence (R13)
# ---------------------------------------------------------------------------

def scan_sensitive(text: str) -> list[str]:
    """Return sensitive-pattern matches found in `text`."""
    return sorted({m.group(0) for m in _SENSITIVE.finditer(text)})


def apply_optimized(original: str, optimized: str) -> tuple[str, bool, list[str]]:
    """Apply an optimized prompt unless it INTRODUCES sensitive patterns.

    Returns (effective_prompt, applied, hits). On hit the ORIGINAL is used and
    the attempt is reported — the caller should log it for replay audit.
    Only patterns NEW in the optimized body (vs the original body) count:
    legitimate goal/acceptance text mentioning token/key is not a jailbreak
    (cursor review 2026-08-30 MEDIUM-2).
    """
    if INVARIANT_BLOCK not in optimized:
        # Optimizer must never drop/rewrite the invariant block.
        return original, False, ["missing_invariant_block"]
    # Scan only the optimizer-controlled body — the system block is trusted
    # (it legitimately mentions token/key/secret as prohibitions).
    body = optimized.replace(INVARIANT_BLOCK, "")
    orig_body = original.replace(INVARIANT_BLOCK, "")
    hits = sorted(set(scan_sensitive(body)) - set(scan_sensitive(orig_body)))
    if hits:
        return original, False, hits
    return optimized, True, []


# ---------------------------------------------------------------------------
# L2 Optimizer + pattern store (offline, score-backed only)
# ---------------------------------------------------------------------------

class PatternStore:
    """Persistent pattern library. Only score-backed entries are stored (R13:
    patterns are driven by measured score improvements, not LLM self-praise)."""

    def __init__(self, path: Path = _DEFAULT_PATTERNS_PATH) -> None:
        self.path = path
        self.patterns: list[Pattern] = self._load()

    def _load(self) -> list[Pattern]:
        if not self.path.is_file():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        if not isinstance(data, list):
            return []  # malformed store -> degrade to empty, never crash
        out: list[Pattern] = []
        for d in data:
            if not isinstance(d, dict):
                continue
            try:
                out.append(Pattern(**{k: v for k, v in d.items() if k in Pattern.__dataclass_fields__}))
            except TypeError:
                continue
        return out

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps([asdict(p) for p in self.patterns], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            return  # best-effort

    def hit(self, task_type: str) -> Pattern | None:
        """Cached pattern for a task type, if any."""
        for p in self.patterns:
            if p.task_type == task_type:
                return p
        return None

    def add(self, pattern: Pattern, min_score: float = 0.8) -> bool:
        """Store only when the pattern has a real score above `min_score` and
        beats the incumbent for the same task type (highest score wins)."""
        if pattern.score < min_score:
            return False
        incumbent = self.hit(pattern.task_type)
        if incumbent is not None and pattern.score <= incumbent.score:
            return False
        self.patterns = [p for p in self.patterns if p.task_type != pattern.task_type]
        self.patterns.append(pattern)
        self.save()
        return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _demo() -> int:
    import tempfile

    spec = TaskSpec(
        goal="將 jarvis-pc 測試全部跑綠",
        background="pytest 喺 jarvis-pc repo",
        constraints=["唔好改測試"],
        acceptance=["201 passed"],
        output_format="一句總結",
    )
    print(format_task(spec))
    print("---")
    print(format_simple("確認 server 喺 8643 聽緊"))
    print("---")
    with tempfile.TemporaryDirectory() as d:
        store = PatternStore(Path(d) / "patterns.json")
        ok = store.add(Pattern("P1", "research", "template...", score=0.9, won_at="2026-08-30"))
        print(f"add score 0.9 -> {ok}")
        ok2 = store.add(Pattern("P2", "research", "template2...", score=0.5, won_at="2026-08-30"))
        print(f"add score 0.5 -> {ok2} (should be False)")
        print(f"hit research -> {store.hit('research') is not None}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="JARVIS Prompt Pipeline (Phase F)")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return _demo()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
