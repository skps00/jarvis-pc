"""gpu_health + NVML/smi parse + speak timeout helpers (no live GPU required)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from jarvis.sensors.backend import (
    GpuSnapshot,
    NvidiaSmiBackend,
    _parse_num,
    parse_smi_csv_line,
)
from jarvis.sensors.gpu_health import GpuHealthMonitor, gpu_health_phrase

_SPEAK = Path(__file__).resolve().parents[1] / "scripts" / "hermes_alert_speak_once.py"


def _load_speak_mod():
    spec = importlib.util.spec_from_file_location("hermes_alert_speak_once", _SPEAK)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_num_filters_255() -> None:
    assert _parse_num("255", is_temp=True) is None
    assert _parse_num("N/A") is None
    assert _parse_num("83.5", is_temp=True) == 83.5
    assert _parse_num("2797") == 2797.0


def test_gpu_health_phrases() -> None:
    assert "Clocks" in gpu_health_phrase("clock_drop")
    assert "thermal" in gpu_health_phrase("hot").lower()


def test_hard_temp_always_triggers() -> None:
    """Hard ceiling fires before calibration."""
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
    assert "thermal" in hit.phrase.lower()


def test_soft_temp_waits_for_calibration() -> None:
    m = GpuHealthMonitor(
        soft_cooldown_s=0.0,
        hard_temp_c=99.0,
        soft_temp_c=80.0,
        calibrate_loaded_samples=99,
    )
    assert (
        m.evaluate(
            GpuSnapshot(ok=True, temp_c=84.0, util_pct=10.0, clock_mhz=500.0)
        )
        is None
    )


def test_clock_drop_after_calibration() -> None:
    m = GpuHealthMonitor(
        soft_cooldown_s=0.0,
        util_load_pct=60.0,
        clock_drop_ratio=0.85,
        clock_drop_hits=2,
        hard_temp_c=99.0,
        soft_temp_c=99.0,
        calibrate_loaded_samples=3,
    )
    for clk in (2800.0, 2750.0, 2700.0):
        assert (
            m.evaluate(
                GpuSnapshot(ok=True, temp_c=70.0, util_pct=90.0, clock_mhz=clk)
            )
            is None
        )
    assert m._calibrated  # noqa: SLF001
    assert (
        m.evaluate(
            GpuSnapshot(ok=True, temp_c=72.0, util_pct=95.0, clock_mhz=2200.0)
        )
        is None
    )  # streak 1
    hit = m.evaluate(
        GpuSnapshot(ok=True, temp_c=73.0, util_pct=95.0, clock_mhz=2100.0)
    )
    assert hit is not None
    assert "Clocks" in hit.phrase


def test_per_reason_cooldown_independent() -> None:
    m = GpuHealthMonitor(
        soft_cooldown_s=999.0,
        hard_cooldown_s=0.0,
        hard_temp_c=90.0,
        soft_temp_c=99.0,
        calibrate_loaded_samples=3,
        clock_drop_hits=1,
        util_load_pct=60.0,
        clock_drop_ratio=0.85,
    )
    # Calibrate + soft clock emit (starts soft cooldown for clock_drop)
    for clk in (2800.0, 2750.0, 2700.0):
        m.evaluate(GpuSnapshot(ok=True, temp_c=70.0, util_pct=90.0, clock_mhz=clk))
    hit_clk = m.evaluate(
        GpuSnapshot(ok=True, temp_c=70.0, util_pct=95.0, clock_mhz=2000.0)
    )
    assert hit_clk is not None
    # Soft cooldown would block another clock_drop; hard temp must still fire
    hit_hot = m.evaluate(
        GpuSnapshot(ok=True, temp_c=95.0, util_pct=95.0, clock_mhz=2000.0)
    )
    assert hit_hot is not None
    assert "thermal" in hit_hot.phrase.lower()


def test_gap_clears_hist(monkeypatch) -> None:
    logs: list[str] = []
    m = GpuHealthMonitor(
        soft_cooldown_s=0.0,
        hard_temp_c=99.0,
        soft_temp_c=99.0,
        calibrate_loaded_samples=3,
    )
    m.set_log(logs.append)
    for clk in (2800.0, 2750.0, 2700.0):
        m.evaluate(GpuSnapshot(ok=True, temp_c=70.0, util_pct=90.0, clock_mhz=clk))
    assert m._calibrated  # noqa: SLF001
    assert m.evaluate(GpuSnapshot(ok=False, error="driver")) is None
    assert any("gap" in x for x in logs)
    assert not m._calibrated  # noqa: SLF001
    assert len(m._hist) == 0  # noqa: SLF001


def test_parse_smi_csv_comma_in_name() -> None:
    snap = parse_smi_csv_line(
        '"NVIDIA GeForce RTX 5090, Limited", 43, N/A, 20, 2797, 109.11'
    )
    assert snap.ok
    assert "5090" in snap.name
    assert "," in snap.name
    assert snap.temp_c == 43.0
    assert snap.clock_mhz == 2797.0


def test_nvidia_smi_parse_line(monkeypatch) -> None:
    class _P:
        returncode = 0
        stdout = "NVIDIA GeForce RTX 5090, 43, N/A, 20, 2797, 109.11\n"
        stderr = ""

    monkeypatch.setattr(
        "jarvis.sensors.backend.subprocess.run", lambda *a, **k: _P()
    )
    snap = NvidiaSmiBackend(smi_path="nvidia-smi").read()
    assert snap.ok
    assert "5090" in snap.name
    assert snap.temp_c == 43.0
    assert snap.mem_temp_c is None
    assert snap.util_pct == 20.0
    assert snap.clock_mhz == 2797.0
    assert snap.source == "smi"


def test_speak_hermes_only_when_mode_hermes(monkeypatch) -> None:
    mod = _load_speak_mod()
    calls = {"mouth": 0, "hermes": 0}

    monkeypatch.setattr(mod, "_alert_tts_mode", lambda: "hermes")
    monkeypatch.setattr(
        mod, "_speak_jarvis_mouth", lambda p: calls.__setitem__("mouth", calls["mouth"] + 1) or True
    )
    monkeypatch.setattr(
        mod,
        "_speak_hermes_subprocess",
        lambda p: calls.__setitem__("hermes", calls["hermes"] + 1) or True,
    )
    assert mod._speak_hermes("hi") is True
    assert calls["hermes"] == 1
    assert calls["mouth"] == 0


def test_speak_piper_mode(monkeypatch) -> None:
    mod = _load_speak_mod()
    monkeypatch.setattr(mod, "_alert_tts_mode", lambda: "piper")
    monkeypatch.setattr(mod, "_speak_jarvis_mouth", lambda p: True)
    monkeypatch.setattr(
        mod, "_speak_hermes_subprocess", lambda p: (_ for _ in ()).throw(AssertionError("no"))
    )
    assert mod._speak_hermes("hi") is True


def test_run_hidden_timeout_kills(monkeypatch) -> None:
    """Hang child → returncode 124; kill tree invoked."""
    mod = _load_speak_mod()
    killed: list[int] = []
    real_kill = mod._kill_process_tree

    def fake_kill(pid: int) -> None:
        killed.append(pid)
        real_kill(pid)

    monkeypatch.setattr(mod, "_kill_process_tree", fake_kill)
    r = mod._run_hidden(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        timeout_s=0.5,
        capture=True,
    )
    assert r.returncode == 124
    assert killed, "expected taskkill/kill on timeout"


if __name__ == "__main__":
    test_parse_num_filters_255()
    test_gpu_health_phrases()
    test_hard_temp_always_triggers()
    test_soft_temp_waits_for_calibration()
    test_clock_drop_after_calibration()
    test_parse_smi_csv_comma_in_name()
    print("ok")
