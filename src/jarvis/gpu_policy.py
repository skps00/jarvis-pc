"""GPU resource policy: when SK is gaming (sk_activity.json state=playing) and
GPU VRAM pressure is high, heavy models (STT SenseVoice, future Mage-VL) should
yield VRAM to the game. Small models keep GPU when VRAM is free."""

from __future__ import annotations

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
            "gpu_util": int(parts[0]),
            "vram_used_mb": int(parts[1]),
            "vram_total_mb": int(parts[2]),
            "gpu_temp_c": int(parts[3]),
        }
    except Exception:
        return empty


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
