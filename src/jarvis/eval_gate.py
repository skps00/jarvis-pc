"""Eval Gate runner (Self-Evol Task 7, Phase D prerequisite, R11).

Execution-based verification for JARVIS changes — NOT LLM self-judgement.
Each suite runs real checks (pytest / py_compile / node --check) and reports
pass/fail plus a suite hash so the golden set can be verified immutable.

Design notes (R11 / R15):
- Golden set is frozen + hand-labelled; it lives in
  ``.hermes/plans/self-evol-golden-set.md`` (human) and the runnable mapping
  here (machine). The eval suite must stay outside what an autonomous agent
  can write — at L0 that is guaranteed by the human gate; before opening any
  auto-apply (L1) the suite location must be moved to agent-read-only storage.
- Run multiple times and take the statistical result (METR: same prompt has
  high variance across runs) — ``--repeat N``.
- Never refresh the golden set from model output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

_PY = r"C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe"
_REPO = Path(r"C:\Users\skps9\Documents\Code_Project\jarvis-pc")
_HUD = Path(r"C:\Users\skps9\Documents\Code_Project\jarvis-hud")
# Human-readable golden-set doc. `--lock` verifies this doc and GOLDEN_SUITES
# have not drifted (pass2 fragility #8): every test file the doc lists must
# exist in the machine mapping and vice versa.
_GOLDEN_DOC = _REPO / ".hermes" / "plans" / "self-evol-golden-set.md"

# Suite -> checks. Add/remove only with SK approval; keep in sync with
# self-evol-golden-set.md (hand-labelled golden tasks).
GOLDEN_SUITES: dict[str, dict[str, list[str]]] = {
    "golden": {
        # Core capabilities that must never regress (frozen). Covers every
        # module under src/jarvis plus the self-evol foundations.
        "pytest": [
            "tests/test_alert_store.py",
            "tests/test_alert_tts_sink.py",
            "tests/test_alerts.py",
            "tests/test_app_index.py",
            "tests/test_autonomy.py",
            "tests/test_autostart.py",
            "tests/test_brain.py",
            "tests/test_clarify.py",
            "tests/test_clarify_stats.py",
            "tests/test_cursor_hooks.py",
            "tests/test_discover.py",
            # NOTE: test_eval_gate.py intentionally NOT in golden — its
            # test_run_suite_golden_executes_real_checks re-runs this suite,
            # which would recurse into itself.
            "tests/test_gpu_health.py",
            "tests/test_hands_mc.py",
            "tests/test_hermes_bridge.py",
            "tests/test_hermes_trusted.py",
            "tests/test_prompt_pipeline.py",
            "tests/test_router.py",
            "tests/test_self_review.py",
            "tests/test_settings.py",
            "tests/test_shell_wake_restart.py",
            "tests/test_speaker_gate.py",
            "tests/test_wake.py",
        ],
        "py_compile": [
            "src/jarvis/activity.py",
            "src/jarvis/aec.py",
            "src/jarvis/alert_store.py",
            "src/jarvis/alerts.py",
            "src/jarvis/app_index.py",
            "src/jarvis/asr_repair.py",
            "src/jarvis/autonomy.py",
            "src/jarvis/brain.py",
            "src/jarvis/clarify.py",
            "src/jarvis/clarify_stats.py",
            "src/jarvis/config.py",
            "src/jarvis/discover.py",
            "src/jarvis/engine.py",
            "src/jarvis/eval_gate.py",
            "src/jarvis/gpu_policy.py",
            "src/jarvis/hands.py",
            "src/jarvis/hermes_bridge.py",
            "src/jarvis/mage_engine.py",
            "src/jarvis/mcp_alerts_http.py",
            "src/jarvis/memory.py",
            "src/jarvis/mouth.py",
            "src/jarvis/persist.py",
            "src/jarvis/prompt_pipeline.py",
            "src/jarvis/router.py",
            "src/jarvis/self_monitor.py",
            "src/jarvis/self_review.py",
            "src/jarvis/settings.py",
            "src/jarvis/shell_app.py",
            "src/jarvis/speaker_gate.py",
            "src/jarvis/wake.py",
        ],
    },
    "regression": {
        # Already-fixed problems must not recur.
        "pytest": [
            "tests/test_settings_ui_smoke.py",
            "tests/test_mcp_alerts_http.py",
        ],
    },
    "stress": {
        # Heavy / adversarial cases (definitions in golden-set.md).
        "pytest": [
            "tests/test_self_review.py",
            "tests/test_autonomy.py",
            "tests/test_clarify.py",
        ],
    },
}

@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class EvalResult:
    suite: str
    ok: bool = False  # filled after checks run
    checks: list[CheckResult] = field(default_factory=list)
    started: str = ""
    duration_s: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "suite": self.suite,
            "ok": self.ok,
            "checks": [{"name": c.name, "ok": c.ok, "detail": c.detail[:300]} for c in self.checks],
            "started": self.started,
            "duration_s": round(self.duration_s, 2),
        }


def suite_hash() -> str:
    """Deterministic hash of the suite mapping (immutability check)."""
    payload = json.dumps(GOLDEN_SUITES, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _run(cmd: list[str], cwd: Path, timeout: int = 180) -> tuple[int, str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
    except FileNotFoundError:
        # Missing interpreter/executable must be a FAILING check, not a crash.
        return 127, f"executable not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except OSError as exc:
        return 126, f"cannot execute {cmd[0]}: {exc}"
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out.strip()[-400:]


def _check_pytest(files: list[str]) -> CheckResult:
    cmd = [_PY, "-m", "pytest", "-q", *files]
    code, out = _run(cmd, _REPO)
    ok = code == 0
    tail = [l for l in out.splitlines() if "passed" in l or "failed" in l or "error" in l.lower()]
    return CheckResult(f"pytest {len(files)} files", ok, "; ".join(tail[-3:]) or out[-200:])


def _check_py_compile(files: list[str]) -> CheckResult:
    cmd = [_PY, "-m", "py_compile", *files]
    code, out = _run(cmd, _REPO)
    return CheckResult(f"py_compile {len(files)} files", code == 0, out or "ok")


def _check_node_check(files: list[str]) -> CheckResult:
    results: list[str] = []
    ok = True
    for f in files:
        code, out = _run(["node", "--check", str(_HUD / f)], _HUD)
        ok = ok and code == 0
        results.append(f"{f}:{'ok' if code == 0 else 'FAIL'}")
    return CheckResult(f"node --check {len(files)} files", ok, "; ".join(results))


def run_suite(name: str) -> EvalResult:
    """Execute one suite's checks for real (execution-based verification)."""
    cfg = GOLDEN_SUITES.get(name)
    if cfg is None:
        raise KeyError(f"unknown suite: {name}")
    started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    t0 = time.time()
    res = EvalResult(suite=name, started=started)
    for check, files in cfg.items():
        if not files:
            continue
        if check == "pytest":
            res.checks.append(_check_pytest(files))
        elif check == "py_compile":
            res.checks.append(_check_py_compile(files))
        elif check == "node_check":
            res.checks.append(_check_node_check(files))
        else:
            res.checks.append(CheckResult(check, False, "unknown check type"))
    res.duration_s = time.time() - t0
    res.ok = bool(res.checks) and all(c.ok for c in res.checks)
    return res


# ---------------------------------------------------------------------------
# `--lock`: prevent doc <-> mapping drift (pass2 fragility #8)
# ---------------------------------------------------------------------------

_DOC_TEST_RE = re.compile(r"`([^`]*test_[a-zA-Z0-9_]+\.py)`")


def doc_test_files() -> list[str]:
    """Test files referenced in self-evol-golden-set.md (basenames, sorted).

    Accepts bare ``test_x.py`` AND full-path ``tests/test_x.py`` mentions
    inside backticks (reviewer 2026-08-31: full-path mentions were silently
    missed before).
    """
    if not _GOLDEN_DOC.is_file():
        return []
    try:
        text = _GOLDEN_DOC.read_text(encoding="utf-8")
    except OSError:
        return []
    return sorted({Path(m.group(1)).name for m in _DOC_TEST_RE.finditer(text)})


def mapping_test_entries() -> list[str]:
    """All pytest files in GOLDEN_SUITES (sorted, de-duped, relative paths)."""
    out: set[str] = set()
    for cfg in GOLDEN_SUITES.values():
        out.update(cfg.get("pytest", []))
    return sorted(out)


def mapping_test_files() -> list[str]:
    """Test files referenced by GOLDEN_SUITES (basenames, sorted)."""
    return sorted({Path(f).name for f in mapping_test_entries()})


def check_doc_lock() -> tuple[bool, list[str]]:
    """Return (consistent, messages). Doc and mapping must list the same
    test files — a change to one side alone is drift. Fail-closed on an empty
    mapping or a missing file."""
    doc = doc_test_files()
    entries = mapping_test_entries()
    mapping = [Path(f).name for f in entries]
    msgs: list[str] = []
    if not entries:
        msgs.append("GOLDEN_SUITES 冇任何 pytest 檔案（fail-closed）")
        return False, msgs
    dup = sorted({b for b in mapping if mapping.count(b) > 1})
    if dup:
        msgs.append(f"mapping 內重複 basename（對比會失去分辨力）：{', '.join(dup)}")
    only_doc = sorted(set(doc) - set(mapping))
    only_map = sorted(set(mapping) - set(doc))
    if only_doc:
        msgs.append(f"doc 有、mapping 冇：{', '.join(only_doc)}")
    if only_map:
        msgs.append(f"mapping 有、doc 冇：{', '.join(only_map)}")
    missing = sorted(f for f in entries if not (_REPO / f).is_file())
    if missing:
        msgs.append(f"mapping 檔案唔存在：{', '.join(missing)}")
    if not only_doc and not only_map and not dup and not missing:
        msgs.append(f"一致（{len(doc)} 個 test files）")
        return True, msgs
    return False, msgs


def uncovered_test_files() -> list[str]:
    """tests/ files not referenced by any suite (informational)."""
    mapped = set(mapping_test_files())
    existing = sorted(p.name for p in (_REPO / "tests").glob("test_*.py"))
    return sorted(set(existing) - mapped)


def main() -> int:
    ap = argparse.ArgumentParser(description="JARVIS Eval Gate (execution-based)")
    ap.add_argument("--suite", choices=list(GOLDEN_SUITES), help="run one suite")
    ap.add_argument("--all", action="store_true", help="run every suite")
    ap.add_argument("--repeat", type=int, default=1, help="run N times (statistical, R11)")
    ap.add_argument("--hash", action="store_true", help="print suite mapping hash only")
    ap.add_argument("--lock", action="store_true",
                    help="verify golden-set.md doc and GOLDEN_SUITES mapping agree")
    args = ap.parse_args()

    if args.hash:
        print(suite_hash())
        return 0

    if args.lock:
        ok, msgs = check_doc_lock()
        for m in msgs:
            print(m)
        unc = uncovered_test_files()
        if unc:
            print(f"(warn) tests/ 有檔案未覆蓋任何 suite：{', '.join(unc)}")
        return 0 if ok else 1

    suites = list(GOLDEN_SUITES) if args.all else ([args.suite] if args.suite else ["golden"])
    all_ok = True
    for suite in suites:
        for i in range(args.repeat):
            res = run_suite(suite)
            all_ok = all_ok and res.ok
            print(json.dumps(res.to_dict(), ensure_ascii=False))
            print(f"suite={suite} run={i + 1}/{args.repeat} ok={res.ok} "
                  f"({res.duration_s:.1f}s)")
    print(f"HASH {suite_hash()}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
