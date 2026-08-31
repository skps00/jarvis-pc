"""Tests for jarvis.eval_gate (Self-Evol Task 7, Phase D prerequisite, 2026-08-30).

Covers: deterministic suite hash (immutability check), real execution-based
verification of the golden suite, unknown-suite rejection, failure propagation,
JSON-serializable result.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.eval_gate import (  # noqa: E402
    CheckResult,
    EvalResult,
    GOLDEN_SUITES,
    check_doc_lock,
    doc_test_files,
    mapping_test_files,
    run_suite,
    suite_hash,
)


def test_suite_hash_deterministic():
    assert suite_hash() == suite_hash()
    assert len(suite_hash()) == 16


def test_suite_hash_changes_when_mapping_changes(monkeypatch):
    import jarvis.eval_gate as eg

    before = suite_hash()
    monkeypatch.setattr(eg, "GOLDEN_SUITES", {"golden": {"pytest": ["tests/test_a.py"]}})
    after = suite_hash()
    assert before != after


def test_run_suite_golden_executes_real_checks():
    # Execution-based: this actually runs pytest + py_compile on the golden set.
    res = run_suite("golden")
    assert res.suite == "golden"
    assert res.checks, "expected at least one check"
    assert res.ok, f"golden suite must pass: {[c.name for c in res.checks]}"
    # Every check ran for real: pytest produced a summary.
    pytest_check = next(c for c in res.checks if c.name.startswith("pytest"))
    assert "passed" in pytest_check.detail


def test_run_suite_unknown_raises():
    try:
        run_suite("no_such_suite")
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown suite")


def test_failure_is_propagated(monkeypatch):
    import jarvis.eval_gate as eg

    def fake_fail(*a, **k):
        return CheckResult("pytest fake", False, "1 failed")

    monkeypatch.setattr(eg, "_check_pytest", fake_fail)
    res = run_suite("golden")
    assert res.ok is False


def test_result_to_dict_json_serializable():
    res = EvalResult(
        suite="golden",
        ok=True,
        checks=[CheckResult("py_compile 1 files", True, "ok")],
        started="2026-08-30 09:00:00",
        duration_s=1.25,
    )
    d = res.to_dict()
    assert d["suite"] == "golden"
    assert d["ok"] is True
    assert d["checks"][0]["name"] == "py_compile 1 files"
    json.dumps(d)


def test_all_suites_defined():
    # The three eval categories from the plan must all exist.
    for name in ("golden", "regression", "stress"):
        assert name in GOLDEN_SUITES, f"missing suite {name}"


def test_missing_executable_reports_failure_not_crash(monkeypatch):
    # A missing interpreter/executable must produce a FAILING check, not a
    # traceback out of main() (bug bot finding 2026-08-30).
    import jarvis.eval_gate as eg

    def boom(*a, **k):
        raise FileNotFoundError("no such executable")

    monkeypatch.setattr(eg.subprocess, "run", boom)
    res = run_suite("golden")
    assert res.ok is False
    assert all(not c.ok for c in res.checks)
    assert "executable not found" in res.checks[0].detail


def test_doc_lock_consistent():
    # The golden-set.md doc and GOLDEN_SUITES mapping must name the same test
    # files (pass2 fragility #8: two-source drift). With the real doc this
    # must hold — otherwise --lock fails in CI.
    ok, msgs = check_doc_lock()
    assert ok, msgs


def test_doc_lock_detects_drift(monkeypatch):
    # If the doc and mapping disagree, --lock must report it as failure.
    import jarvis.eval_gate as eg

    monkeypatch.setattr(eg, "_GOLDEN_DOC", Path(eg._GOLDEN_DOC))  # keep type
    monkeypatch.setattr(eg, "doc_test_files", lambda: ["test_a.py", "test_b.py"])
    monkeypatch.setattr(eg, "mapping_test_files", lambda: ["test_a.py"])
    ok, msgs = check_doc_lock()
    assert ok is False
    assert any("doc 有" in m for m in msgs)


def test_mapping_and_doc_use_basenames():
    # Mapping stores paths like tests/test_x.py; doc stores bare test_x.py.
    # Both sides normalize to basenames so the comparison is apples-to-apples.
    assert mapping_test_files() == sorted(Path(f).name for f in mapping_test_files())
    assert all(not f.startswith("tests/") for f in doc_test_files())


def test_doc_full_path_mentions_detected(monkeypatch):
    # Reviewer 2026-08-31: full-path ``tests/test_x.py`` mentions in the doc
    # were silently missed. The regex must accept both forms.
    import jarvis.eval_gate as eg

    monkeypatch.setattr(eg, "doc_test_files", lambda: ["test_a.py", "test_b.py"])
    monkeypatch.setattr(eg, "mapping_test_entries", lambda: ["tests/test_a.py"])
    ok, msgs = check_doc_lock()
    assert ok is False
    assert any("doc 有" in m for m in msgs)


def test_doc_regex_accepts_full_path():
    # The regex itself must capture test_b.py from `tests/test_b.py`.
    import jarvis.eval_gate as eg

    hits = {Path(m.group(1)).name for m in
            eg._DOC_TEST_RE.finditer("`tests/test_b.py` and `test_a.py`")}
    assert hits == {"test_a.py", "test_b.py"}


def test_lock_fails_closed_on_empty_mapping(monkeypatch):
    # Reviewer 2026-08-31: doc AND mapping both empty would have passed as
    # "一致". An empty mapping must fail closed.
    import jarvis.eval_gate as eg

    monkeypatch.setattr(eg, "doc_test_files", lambda: [])
    monkeypatch.setattr(eg, "mapping_test_entries", lambda: [])
    ok, msgs = check_doc_lock()
    assert ok is False
    assert any("fail-closed" in m for m in msgs)


def test_lock_detects_missing_mapping_file(monkeypatch):
    import jarvis.eval_gate as eg

    monkeypatch.setattr(eg, "doc_test_files", lambda: ["test_ghost.py"])
    monkeypatch.setattr(eg, "mapping_test_entries", lambda: ["tests/test_ghost.py"])
    ok, msgs = check_doc_lock()
    assert ok is False
    assert any("唔存在" in m for m in msgs)
