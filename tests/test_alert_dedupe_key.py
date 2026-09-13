"""self-monitor dedupe_key must use stable sha1, not process-local hash()."""

from __future__ import annotations

import hashlib
from pathlib import Path

from jarvis.alert_store import AlertStore


def _sha1_key(text: str) -> str:
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:16]


def test_different_summary_not_deduped(tmp_path: Path) -> None:
    st = AlertStore(tmp_path / "q.jsonl")
    a = st.enqueue(
        kind="self-monitor",
        phrase="Sir, self monitor found one issue.",
        detail="summary-one",
        dedupe_key=_sha1_key("summary-one"),
    )
    b = st.enqueue(
        kind="self-monitor",
        phrase="Sir, self monitor found another issue.",
        detail="summary-two",
        dedupe_key=_sha1_key("summary-two"),
    )
    assert a.id != b.id
    assert len(st.list_open()) == 2


def test_same_summary_deduped(tmp_path: Path) -> None:
    st = AlertStore(tmp_path / "q.jsonl")
    key = _sha1_key("same-summary")
    a = st.enqueue(
        kind="self-monitor",
        phrase="Sir, self monitor found one issue.",
        detail="same-summary",
        dedupe_key=key,
    )
    b = st.enqueue(
        kind="self-monitor",
        phrase="Sir, self monitor found one issue.",
        detail="same-summary",
        dedupe_key=key,
    )
    assert a.id == b.id
    assert len(st.list_open()) == 1


def test_same_summary_same_key_different_differs() -> None:
    assert _sha1_key("same-summary") == _sha1_key("same-summary")
    assert _sha1_key("summary-one") != _sha1_key("summary-two")
    # Cross-process stable: known vector (not str(hash(...))).
    assert _sha1_key("same-summary") == hashlib.sha1(b"same-summary").hexdigest()[:16]
