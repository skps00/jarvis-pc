"""Read HWiNFO64 sensor shared memory (Windows file mapping).

Requires HWiNFO64 running with Settings → General → Shared Memory Support enabled.
Layout follows HWiNFO SDK ``HWiNFO_SENSORS_SHARED_MEM`` / ``HWiNFO_SENSOR``.
"""

from __future__ import annotations

import ctypes
import re
from ctypes import wintypes
from typing import Any

# HWiNFO SDK reading types (eHWiNFO_READING_TYPE)
_RT_TEMP = 1
_RT_VOLT = 2
_RT_FAN = 3

_MAP_NAMES = ("Global\\HWiNFO_SENSORSMAP2", "HWiNFO_SENSORSMAP2")
_SIGNATURE = b"HWiNFO"
_MAX_ENTRIES = 40

_FILE_MAP_READ = 0x0004

_kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

_OpenFileMappingW = _kernel32.OpenFileMappingW
_OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
_OpenFileMappingW.restype = wintypes.HANDLE

_MapViewOfFile = _kernel32.MapViewOfFile
_MapViewOfFile.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_size_t,
]
_MapViewOfFile.restype = wintypes.LPVOID

_UnmapViewOfFile = _kernel32.UnmapViewOfFile
_UnmapViewOfFile.argtypes = [wintypes.LPVOID]
_UnmapViewOfFile.restype = wintypes.BOOL

_CloseHandle = _kernel32.CloseHandle
_CloseHandle.argtypes = [wintypes.HANDLE]
_CloseHandle.restype = wintypes.BOOL


class _SharedMemHeader(ctypes.Structure):
    _fields_ = [
        ("signature", ctypes.c_char * 8),
        ("version", wintypes.DWORD),
        ("revision", wintypes.DWORD),
        ("poll_time", ctypes.c_int64),
        ("offset_of_sensor_section", wintypes.DWORD),
        ("size_of_sensor_section", wintypes.DWORD),
        ("sensor_section_elements", wintypes.DWORD),
    ]


class _SensorEntry(ctypes.Structure):
    _fields_ = [
        ("name_original", ctypes.c_char * 128),
        ("name_user", ctypes.c_char * 128),
        ("unit", ctypes.c_char * 16),
        ("value", ctypes.c_double),
        ("value_min", ctypes.c_double),
        ("value_max", ctypes.c_double),
        ("value_avg", ctypes.c_double),
        ("reading_type", wintypes.DWORD),
        ("sensor_index", wintypes.DWORD),
        ("sensor_inst", wintypes.DWORD),
        ("sensor_id", wintypes.DWORD),
    ]


_SENSOR_SIZE = ctypes.sizeof(_SensorEntry)


def _decode_cstr(raw: bytes) -> str:
    nul = raw.find(b"\x00")
    if nul >= 0:
        raw = raw[:nul]
    return raw.decode("utf-8", errors="replace").strip()


def _open_mapping() -> tuple[wintypes.HANDLE, int] | None:
    for name in _MAP_NAMES:
        try:
            handle = _OpenFileMappingW(_FILE_MAP_READ, False, name)
        except Exception:
            continue
        if not handle:
            continue
        try:
            view = _MapViewOfFile(handle, _FILE_MAP_READ, 0, 0, 0)
        except Exception:
            _CloseHandle(handle)
            continue
        if not view:
            _CloseHandle(handle)
            continue
        return handle, int(view)
    return None


def _close_mapping(handle: wintypes.HANDLE, view_addr: int) -> None:
    try:
        if view_addr:
            _UnmapViewOfFile(view_addr)
    except Exception:
        pass
    try:
        if handle:
            _CloseHandle(handle)
    except Exception:
        pass


def shm_available() -> bool:
    """Return True if HWiNFO sensor shared memory can be opened and mapped."""
    opened = _open_mapping()
    if opened is None:
        return False
    handle, view_addr = opened
    _close_mapping(handle, view_addr)
    return True


def _is_meaningful(entry: _SensorEntry, name: str, unit: str) -> bool:
    if entry.reading_type in (_RT_TEMP, _RT_VOLT, _RT_FAN):
        return True
    blob = f"{name} {unit}".lower()
    return bool(re.search(r"\b(temp|rpm|fan|volt|voltage|°c|celsius)\b", blob))


def _pick_name(entry: _SensorEntry) -> str:
    user = _decode_cstr(bytes(entry.name_user))
    if user:
        return user
    return _decode_cstr(bytes(entry.name_original))


def read_sensors() -> dict[str, Any]:
    """Read sensor entries from HWiNFO shared memory.

    Returns ``{"sensors": [{"name", "value", "unit"}, ...]}`` (up to ~40 entries),
    or ``{}`` when shared memory is unavailable or unreadable.
    """
    opened = _open_mapping()
    if opened is None:
        return {}

    handle, view_addr = opened
    out: list[dict[str, Any]] = []
    try:
        header = _SharedMemHeader.from_address(view_addr)
        if not bytes(header.signature).startswith(_SIGNATURE):
            return {}

        count = int(header.sensor_section_elements)
        offset = int(header.offset_of_sensor_section)
        if count <= 0 or count > 4096 or offset <= 0:
            return {}

        base = view_addr + offset
        for i in range(count):
            if len(out) >= _MAX_ENTRIES:
                break
            try:
                entry = _SensorEntry.from_address(base + i * _SENSOR_SIZE)
            except Exception:
                continue

            name = _pick_name(entry)
            if not name:
                continue
            unit = _decode_cstr(bytes(entry.unit))
            try:
                value = float(entry.value)
            except (TypeError, ValueError):
                continue
            if not _is_meaningful(entry, name, unit):
                continue
            if value != value:  # NaN
                continue

            out.append({"name": name, "value": value, "unit": unit})

        return {"sensors": out}
    except Exception:
        return {}
    finally:
        _close_mapping(handle, view_addr)


def summary() -> str:
    """One-line best-effort summary, e.g. ``CPU 51°C | GPU 45°C | FAN1 1200rpm``."""
    data = read_sensors()
    sensors = data.get("sensors") if isinstance(data, dict) else None
    if not sensors:
        return ""

    cpu_val: str | None = None
    gpu_val: str | None = None
    fan_parts: list[str] = []

    for item in sensors:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        unit = str(item.get("unit") or "")
        try:
            value = float(item.get("value"))
        except (TypeError, ValueError):
            continue
        nl = name.lower()
        ul = unit.lower()

        if cpu_val is None and "cpu" in nl and re.search(r"temp|package|tctl|tdie", nl):
            cpu_val = _fmt_reading("CPU", value, unit, default_unit="°C")
        elif gpu_val is None and "gpu" in nl and re.search(r"temp|hotspot|core", nl):
            gpu_val = _fmt_reading("GPU", value, unit, default_unit="°C")
        elif re.search(r"fan|rpm", nl) or "rpm" in ul or re.search(r"fan", nl):
            label = re.sub(r"\s+", " ", name.split()[0] if name else "FAN").upper()
            fan_parts.append(_fmt_reading(label, value, unit, default_unit="rpm"))

    parts: list[str] = []
    if cpu_val:
        parts.append(cpu_val)
    if gpu_val:
        parts.append(gpu_val)
    parts.extend(fan_parts[:3])
    return " | ".join(parts)


def _fmt_reading(label: str, value: float, unit: str, *, default_unit: str) -> str:
    u = unit.strip() or default_unit
    if u.lower() in ("c", "°c", "celsius"):
        u = "°C"
    if value == int(value):
        return f"{label} {int(value)}{u}"
    return f"{label} {value:.1f}{u}"
