"""GPU resource policy: when SK is gaming (sk_activity.json state=playing) and
GPU VRAM pressure is high, heavy models (STT SenseVoice, future Mage-VL) should
yield VRAM to the game. Small models keep GPU when VRAM is free."""

from __future__ import annotations

import re
import subprocess
import sys

from jarvis.activity import gaming


def gaming_now() -> bool:
    """True when sk_activity.json reports state == 'playing'."""
    return gaming()


def gpu_metrics() -> dict:
    """nvidia-smi GPU util / VRAM / temperature; None values on failure."""
    empty: dict = {
        "gpu_util": None,
        "vram_used_mb": None,
        "vram_total_mb": None,
        "gpu_temp_c": None,
    }
    try:
        kwargs: dict = {
            "capture_output": True,
            "text": True,
            "timeout": 3,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = 0x08000000
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            **kwargs,
        )
        if proc.returncode != 0:
            return empty
        lines = (proc.stdout or "").strip().splitlines()
        if not lines:
            return empty
        parts = [p.strip() for p in lines[0].split(",")]
        if len(parts) < 4:
            return empty
        return {
            "gpu_util": _float_or_none(parts[0]),
            "vram_used_mb": _float_or_none(parts[1]),
            "vram_total_mb": _float_or_none(parts[2]),
            "gpu_temp_c": _float_or_none(parts[3]),
        }
    except Exception:
        return empty


def _float_or_none(v: object) -> float | None:
    try:
        f = float(str(v))
        return f if f == f else None  # NaN -> None
    except (TypeError, ValueError):
        return None


def gpu_metrics_with_fallback() -> dict:
    """GPU metrics with failover chain (2026-08-31 #11, D3):

    nvidia-smi → HWiNFO64 shared memory (GPU temp / VRAM / util sensors) → {}.

    GPU-Z is NOT in the chain: it has no public shared-memory API, so a
    GPU-Z failover is not implementable (recorded, not done).
    """
    m = gpu_metrics()
    if m.get("gpu_util") is not None or m.get("gpu_temp_c") is not None:
        return m
    # Fallback: HWiNFO SHM — find GPU-ish sensors by name.
    try:
        from jarvis import hwinfo_shm

        data = hwinfo_shm.read_sensors()
    except Exception:
        return m
    sensors = data.get("sensors") if isinstance(data, dict) else None
    if not sensors:
        return m

    gpu_temp: float | None = None
    vram_used: float | None = None
    vram_total: float | None = None
    gpu_util: float | None = None
    for item in sensors:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").lower()
        unit = str(item.get("unit") or "").lower()
        try:
            value = float(item.get("value"))
        except (TypeError, ValueError):
            continue
        if "gpu" not in name:
            continue
        if gpu_temp is None and re.search(r"temp|hotspot|core", name) and re.search(r"°?c|celsius", unit):
            gpu_temp = value
        elif vram_used is None and re.search(r"memory|vram", name) and re.search(r"mb|gb", unit):
            vram_used = value if "mb" in unit else value * 1024.0
        elif vram_total is None and re.search(r"memory.*total|total.*memory", name):
            vram_total = value if "mb" in unit else value * 1024.0
        elif gpu_util is None and re.search(r"util|load|usage", name) and re.search(r"%", unit):
            gpu_util = value
    if any(v is not None for v in (gpu_temp, vram_used, gpu_util)):
        return {
            "gpu_util": gpu_util,
            "vram_used_mb": vram_used,
            "vram_total_mb": vram_total,
            "gpu_temp_c": gpu_temp,
            "source": "hwinfo",
        }
    return m


def vram_pressure(threshold_pct: float = 85.0) -> bool:
    """True when nvidia-smi memory.used / memory.total exceeds threshold_pct."""
    m = gpu_metrics()
    used = m.get("vram_used_mb")
    total = m.get("vram_total_mb")
    if used is None or total is None or total <= 0:
        return False
    return (used / total) * 100.0 > threshold_pct


def should_stt_use_gpu() -> bool:
    """False if playing AND vram_pressure(); else True. Fail-open on errors."""
    try:
        if not gaming_now():
            return True
        return not vram_pressure()
    except Exception:
        return True
