"""Tests for gpu_policy failover chain (2026-08-31 #11, D3).

nvidia-smi → HWiNFO SHM → empty. GPU-Z excluded (no public API).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.gpu_policy import gpu_metrics, gpu_metrics_with_fallback  # noqa: E402


class _P:
    def __init__(self, rc=0, out=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = ""


def test_gpu_metrics_parses_nvidia_smi():
    with mock.patch(
        "jarvis.gpu_policy.subprocess.run",
        return_value=_P(0, "21, 4439, 32607, 52\n"),
    ):
        m = gpu_metrics()
    assert m["gpu_util"] == 21.0
    assert m["vram_used_mb"] == 4439.0
    assert m["vram_total_mb"] == 32607.0
    assert m["gpu_temp_c"] == 52.0


def test_gpu_metrics_handles_n_a():
    with mock.patch(
        "jarvis.gpu_policy.subprocess.run",
        return_value=_P(0, "N/A, N/A, N/A, N/A\n"),
    ):
        m = gpu_metrics()
    assert m["gpu_util"] is None
    assert m["gpu_temp_c"] is None


def test_gpu_metrics_failure_returns_empty():
    with mock.patch(
        "jarvis.gpu_policy.subprocess.run", return_value=_P(1, "")
    ):
        m = gpu_metrics()
    assert m["gpu_util"] is None
    assert m["gpu_temp_c"] is None


def test_fallback_uses_nvidia_smi_when_healthy():
    with mock.patch(
        "jarvis.gpu_policy.subprocess.run",
        return_value=_P(0, "30, 5000, 32607, 60\n"),
    ):
        m = gpu_metrics_with_fallback()
    assert m["gpu_util"] == 30.0
    assert "source" not in m  # native path, no source tag


def test_fallback_to_hwinfo_when_smi_down():
    sensors = [
        {"name": "GPU Temperature", "value": 61.0, "unit": "°C"},
        {"name": "GPU Memory Used", "value": 4096.0, "unit": "MB"},
        {"name": "GPU Memory Total", "value": 32607.0, "unit": "MB"},
        {"name": "GPU Load", "value": 42.0, "unit": "%"},
        {"name": "CPU Temperature", "value": 55.0, "unit": "°C"},  # ignored
    ]
    with mock.patch(
        "jarvis.gpu_policy.subprocess.run", return_value=_P(1, "")
    ), mock.patch(
        "jarvis.hwinfo_shm.read_sensors",
        return_value={"sensors": sensors},
    ):
        m = gpu_metrics_with_fallback()
    assert m["source"] == "hwinfo"
    assert m["gpu_temp_c"] == 61.0
    assert m["vram_used_mb"] == 4096.0
    assert m["gpu_util"] == 42.0


def test_fallback_empty_when_hwinfo_unavailable():
    with mock.patch(
        "jarvis.gpu_policy.subprocess.run", return_value=_P(1, "")
    ), mock.patch(
        "jarvis.hwinfo_shm.read_sensors", return_value={}
    ):
        m = gpu_metrics_with_fallback()
    assert m["gpu_util"] is None
    assert m["gpu_temp_c"] is None
    assert "source" not in m


def test_fallback_gb_unit_converted_to_mb():
    sensors = [
        {"name": "GPU Memory Used", "value": 4.0, "unit": "GB"},
    ]
    with mock.patch(
        "jarvis.gpu_policy.subprocess.run", return_value=_P(1, "")
    ), mock.patch(
        "jarvis.hwinfo_shm.read_sensors",
        return_value={"sensors": sensors},
    ):
        m = gpu_metrics_with_fallback()
    assert m["vram_used_mb"] == 4096.0
