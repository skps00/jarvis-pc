"""Tests for jarvis.engine repair_log helpers."""

from __future__ import annotations

import json
from pathlib import Path

from jarvis.engine import _log_repair_event, _maybe_rotate_repair_log


def test_log_repair_event_writes_row(tmp_path: Path) -> None:
    path = tmp_path / "repair_log.jsonl"
    _log_repair_event("ASR 修正：'cura' → 'Cursor'", repair_log=path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["raw"] == "cura"
    assert rows[0]["fixed"] == "Cursor"


def test_log_repair_event_first_arrow_only(tmp_path: Path) -> None:
    path = tmp_path / "repair_log.jsonl"
    _log_repair_event(
        "ASR 修正：'cura' → '開 Cursor'；app 補開（80%）：'x' → 'Cursor'",
        repair_log=path,
    )
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["raw"] == "cura"
    assert rows[0]["fixed"] == "開 Cursor"


def test_log_repair_event_no_arrow_writes_nothing(tmp_path: Path) -> None:
    path = tmp_path / "repair_log.jsonl"
    _log_repair_event("ASR 修正（冇箭頭）", repair_log=path)
    assert not path.exists()


def test_maybe_rotate_repair_log(tmp_path: Path) -> None:
    path = tmp_path / "repair_log.jsonl"
    lines = [json.dumps({"ts": i, "raw": f"r{i}", "fixed": f"f{i}"}) for i in range(20005)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    last = lines[-1]
    _maybe_rotate_repair_log(path)
    kept = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(kept) <= 10000
    assert kept[-1] == last


def test_log_repair_event_unwritable_dir_no_raise(tmp_path: Path) -> None:
    bad = tmp_path / "no" / "such" / "deep" / "missing" / "repair_log.jsonl"
    _log_repair_event("ASR 修正：'a' → 'b'", repair_log=bad)  # must not raise
