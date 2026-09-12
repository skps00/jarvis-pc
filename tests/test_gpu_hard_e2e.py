"""E2E: GpuHealthHit → AlertWatcher emit → AlertStore (temp queue)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.alert_store import AlertStore
from jarvis.alerts import AlertEvent, AlertWatcher, alert_phrase_for
from jarvis.sensors.backend import GpuSnapshot
from jarvis.sensors.gpu_health import GpuHealthMonitor


def _emit_gpu_hit(watcher: AlertWatcher, hit) -> None:
    """Mirror production ``_sensor_loop`` (hard: alert_phrase_for; never empty)."""
    phrase = (
        alert_phrase_for(hit.kind) if hit.kind == "gpu_hard" else hit.phrase
    )
    if not str(phrase or "").strip():
        phrase = alert_phrase_for(hit.kind)
    watcher._emit(  # noqa: SLF001 — production emit path
        AlertEvent(kind=hit.kind, phrase=phrase, detail=hit.detail),
        force=True,
    )


def test_hard_hit_stores_gpu_hard_critical_phrase(tmp_path: Path) -> None:
    from jarvis.alert_policy import shape
    from jarvis.alert_dispatch import prepare_phrase

    store = AlertStore(tmp_path / "queue.jsonl")
    watcher = AlertWatcher(
        on_event=lambda ev: store.enqueue(
            kind=ev.kind, phrase=ev.phrase, detail=ev.detail or ""
        )
    )
    m = GpuHealthMonitor(
        soft_cooldown_s=0.0,
        hard_cooldown_s=0.0,
        hard_temp_c=90.0,
        soft_temp_c=83.0,
        calibrate_loaded_samples=99,
    )
    hit = m.evaluate(
        GpuSnapshot(ok=True, temp_c=91.0, util_pct=10.0, clock_mhz=500.0)
    )
    assert hit is not None
    assert hit.kind == "gpu_hard"
    _emit_gpu_hit(watcher, hit)
    row = store.peek(lease_s=10)
    assert row is not None
    assert row.kind == "gpu_hard"
    assert row.phrase == "Sir, GPU critical limit reached."
    assert shape("gpu_hard") == "Sir, GPU critical limit reached."
    assert shape("gpu_hard") == alert_phrase_for("gpu_hard")
    assert alert_phrase_for("gpu_hard") == "Sir, GPU critical limit reached."
    text, reason = prepare_phrase(row)
    assert reason is None
    assert text == "Sir, GPU critical limit reached."


def test_soft_hit_stores_gpu_health_soft_phrase(tmp_path: Path) -> None:
    store = AlertStore(tmp_path / "queue.jsonl")
    watcher = AlertWatcher(
        on_event=lambda ev: store.enqueue(
            kind=ev.kind, phrase=ev.phrase, detail=ev.detail or ""
        )
    )
    m = GpuHealthMonitor(
        soft_cooldown_s=0.0,
        hard_cooldown_s=0.0,
        hard_temp_c=90.0,
        soft_temp_c=83.0,
        calibrate_loaded_samples=3,
        util_load_pct=60.0,
    )
    for clk in (2800.0, 2750.0, 2700.0):
        m.evaluate(GpuSnapshot(ok=True, temp_c=70.0, util_pct=90.0, clock_mhz=clk))
    hit = m.evaluate(
        GpuSnapshot(ok=True, temp_c=85.0, util_pct=10.0, clock_mhz=500.0)
    )
    assert hit is not None
    assert hit.kind == "gpu_health"
    _emit_gpu_hit(watcher, hit)
    row = store.peek(lease_s=10)
    assert row is not None
    assert row.kind == "gpu_health"
    assert row.phrase == hit.phrase
    assert "thermal" in row.phrase.lower()


def test_enqueue_rejects_empty_phrase(tmp_path: Path) -> None:
    store = AlertStore(tmp_path / "queue.jsonl")
    with pytest.raises(ValueError):
        store.enqueue(kind="gpu_hard", phrase="")


def test_gpu_hard_producer_phrase_non_empty() -> None:
    captured: list[AlertEvent] = []
    watcher = AlertWatcher(on_event=lambda ev: captured.append(ev))
    m = GpuHealthMonitor(
        soft_cooldown_s=0.0,
        hard_cooldown_s=0.0,
        hard_temp_c=90.0,
        soft_temp_c=83.0,
        calibrate_loaded_samples=99,
    )
    hit = m.evaluate(
        GpuSnapshot(ok=True, temp_c=91.0, util_pct=10.0, clock_mhz=500.0)
    )
    assert hit is not None
    assert hit.kind == "gpu_hard"
    _emit_gpu_hit(watcher, hit)
    assert captured[0].kind == "gpu_hard"
    assert captured[0].phrase.strip() != ""
