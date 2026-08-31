"""Pluggable GPU metric backends. P0: NVML primary, nvidia-smi CSV fallback."""

from __future__ import annotations

import csv
import io
import shutil
import subprocess
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GpuSnapshot:
    """One poll of official NVIDIA metrics (no unofficial hotspot)."""

    name: str = ""
    temp_c: float | None = None
    mem_temp_c: float | None = None
    util_pct: float | None = None
    clock_mhz: float | None = None
    power_w: float | None = None
    ok: bool = False
    error: str = ""
    source: str = ""  # "nvml" | "smi" | ""


class SensorBackend(Protocol):
    """Hardware reader interface (architecture solid line)."""

    def read(self) -> GpuSnapshot:
        """Return latest snapshot; never raise for missing GPU."""


def _parse_num(raw: str, *, is_temp: bool = False) -> float | None:
    s = (raw or "").strip()
    if not s or s.upper() in ("N/A", "[N/A]", "NA"):
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    # Locked Blackwell hotspot signature often decoded as 255
    if is_temp and v >= 250.0:
        return None
    return v


def parse_smi_csv_line(line: str) -> GpuSnapshot:
    """Parse one nvidia-smi CSV row (handles commas inside quoted GPU names)."""
    row = next(csv.reader(io.StringIO(line.strip())), None)
    if not row:
        return GpuSnapshot(ok=False, error="empty csv row", source="smi")
    parts = list(row)
    while len(parts) < 6:
        parts.append("")
    return GpuSnapshot(
        name=(parts[0] or "").strip(),
        temp_c=_parse_num(parts[1], is_temp=True),
        mem_temp_c=_parse_num(parts[2], is_temp=True),
        util_pct=_parse_num(parts[3]),
        clock_mhz=_parse_num(parts[4]),
        power_w=_parse_num(parts[5]),
        ok=True,
        source="smi",
    )


class NvmlBackend:
    """Read GPU via NVML (``nvidia-ml-py`` / ``pynvml``). No console child."""

    def __init__(self, *, index: int = 0) -> None:
        self._index = int(index)
        self._ok: bool | None = None
        self._err = ""

    def available(self) -> bool:
        if self._ok is not None:
            return self._ok
        try:
            import pynvml  # type: ignore[import-untyped]
        except ImportError:
            self._ok = False
            self._err = "pynvml not installed (pip install nvidia-ml-py)"
            return False
        try:
            pynvml.nvmlInit()
            pynvml.nvmlDeviceGetHandleByIndex(self._index)
            self._ok = True
            self._err = ""
            return True
        except Exception as exc:  # noqa: BLE001
            self._ok = False
            self._err = f"nvmlInit: {exc}"
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
            return False

    def read(self) -> GpuSnapshot:
        if not self.available():
            return GpuSnapshot(ok=False, error=self._err or "nvml unavailable", source="nvml")
        import pynvml  # type: ignore[import-untyped]

        try:
            # nvmlInit is idempotent after available(); re-init if shutdown elsewhere
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(self._index)
            except Exception:
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(self._index)
            name_raw = pynvml.nvmlDeviceGetName(handle)
            name = (
                name_raw.decode("utf-8", errors="replace")
                if isinstance(name_raw, (bytes, bytearray))
                else str(name_raw)
            )
            temp = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
            if temp >= 250.0:
                temp_c: float | None = None
            else:
                temp_c = temp
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                util_pct = float(util.gpu)
            except Exception:
                util_pct = None
            try:
                clock_mhz = float(
                    pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                )
            except Exception:
                clock_mhz = None
            try:
                power_w = float(pynvml.nvmlDeviceGetPowerUsage(handle)) / 1000.0
            except Exception:
                power_w = None
            mem_temp_c: float | None = None
            return GpuSnapshot(
                name=name,
                temp_c=temp_c,
                mem_temp_c=mem_temp_c,
                util_pct=util_pct,
                clock_mhz=clock_mhz,
                power_w=power_w,
                ok=True,
                source="nvml",
            )
        except Exception as exc:  # noqa: BLE001
            self._ok = False
            self._err = str(exc)
            return GpuSnapshot(ok=False, error=str(exc)[:200], source="nvml")


class NvidiaSmiBackend:
    """Read GPU via ``nvidia-smi`` CSV (driver ships with card). Fallback path."""

    QUERY = (
        "name,temperature.gpu,temperature.memory,"
        "utilization.gpu,clocks.current.graphics,power.draw"
    )

    def __init__(self, *, smi_path: str | None = None, timeout_s: float = 5.0) -> None:
        self._smi = smi_path or shutil.which("nvidia-smi") or "nvidia-smi"
        self._timeout = float(timeout_s)

    def read(self) -> GpuSnapshot:
        try:
            flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
            proc = subprocess.run(
                [
                    self._smi,
                    f"--query-gpu={self.QUERY}",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                # nvidia-smi on some locales may emit non-UTF-8 — decode errors
                # would kill the reader thread (2026-08-31).
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout,
                check=False,
                stdin=subprocess.DEVNULL,
                creationflags=flags,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return GpuSnapshot(ok=False, error=str(exc), source="smi")
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "nvidia-smi failed").strip()
            return GpuSnapshot(ok=False, error=err[:200], source="smi")
        lines = (proc.stdout or "").strip().splitlines()
        if not lines:
            return GpuSnapshot(ok=False, error="empty nvidia-smi output", source="smi")
        # First GPU only (ponytail: multi-GPU later)
        return parse_smi_csv_line(lines[0])


class PreferNvmlBackend:
    """NVML first; fall back to nvidia-smi when NVML missing/fails."""

    def __init__(self) -> None:
        self._nvml = NvmlBackend()
        self._smi = NvidiaSmiBackend()
        self._use_smi = not self._nvml.available()

    def read(self) -> GpuSnapshot:
        if not self._use_smi:
            snap = self._nvml.read()
            if snap.ok:
                return snap
            # Transient NVML failure → try smi once; keep preferring NVML next time
            # unless package/driver permanently missing (available() already False).
            if not self._nvml.available():
                self._use_smi = True
            else:
                fb = self._smi.read()
                if fb.ok:
                    return fb
                return snap
        return self._smi.read()


def default_gpu_backend() -> SensorBackend:
    """Production reader: NVML primary, smi fallback."""
    return PreferNvmlBackend()
