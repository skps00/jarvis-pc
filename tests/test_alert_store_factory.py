"""default_store factory: policy inject + settings caps + fail-open."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.alert_store import AlertStore, default_store


def test_default_store_injects_policy(tmp_path: Path) -> None:
    st = default_store(tmp_path / "q.jsonl")
    assert st.enqueue(kind="gpu_hard", phrase="x").priority == "critical"
    # FIX7 AA: sidecar_down no longer critical (reserved, no producer)
    assert st.enqueue(kind="sidecar_down", phrase="y").priority == "normal"
    assert st.enqueue(kind="cursor_approve", phrase="z").priority == "critical"
    assert st.enqueue(kind="whatsapp", phrase="w").priority == "normal"


def test_default_store_reads_settings_caps(tmp_path: Path) -> None:
    cfg = SimpleNamespace(
        alert_held_cap=3,
        alert_dedupe_window_s=0.0,
        alert_digest_ttl_s=60.0,
    )
    st = default_store(tmp_path / "q.jsonl", settings=cfg)
    assert st.held_cap == 3
    assert st.dedupe_window_s == 0.0
    assert st.digest_max_age_s == 60.0


def test_default_store_fail_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom() -> None:
        raise RuntimeError("settings unavailable")

    monkeypatch.setattr("jarvis.settings.load_settings", _boom)
    st = default_store(tmp_path / "q.jsonl", settings=object())
    assert isinstance(st, AlertStore)
    row = st.enqueue(kind="test", phrase="Sir, still works.")
    assert row.phrase == "Sir, still works."


def test_default_store_load_settings_fail_keeps_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom() -> None:
        raise RuntimeError("settings unavailable")

    monkeypatch.setattr("jarvis.settings.load_settings", _boom)
    st = default_store(tmp_path / "q.jsonl")
    assert st.enqueue(kind="gpu_hard", phrase="x").priority == "critical"


def test_default_store_except_branch_injects_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Outer factory except must still pass policy (FIX7 AD)."""

    def _boom() -> None:
        raise RuntimeError("settings unavailable")

    monkeypatch.setattr("jarvis.settings.load_settings", _boom)
    # Force AlertStore(**kwargs) to raise via bad held_cap → except branch.
    bad = SimpleNamespace(
        alert_held_cap=object(),  # int(object()) TypeError
        alert_dedupe_window_s=300.0,
        alert_digest_ttl_s=86400.0,
    )
    st = default_store(tmp_path / "q.jsonl", settings=bad)
    assert st.enqueue(kind="gpu_hard", phrase="x").priority == "critical"
