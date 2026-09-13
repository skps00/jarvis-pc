#!/usr/bin/env python3
"""Watch cmd/conhost/powershell spawns for 30 minutes. Classify Jarvis vs Cursor."""
from __future__ import annotations

import ctypes
import datetime as dt
import sys
import time
from ctypes import wintypes

DURATION_S = 30 * 60
OUT = r"C:\Users\skps9\AppData\Local\Temp\jarvis_cmd_watch_30m.txt"

JARVIS_MARKERS = (
    "jarvis",
    "hermes_alert",
    "nvidia-smi",
    "mcp_stdio_no_console",
    "cursor_hook_alert",
    r"\pythoncore-3.14-64\pythonw.exe",
    r"jarvis-pc\.venv",
)
CURSOR_MARKERS = (
    "cursor.exe",
    "ps-script-",
    "cursor-hook-payload",
    r"\programs\cursor",
    "codegraph",
    "context7",
)

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
advapi = ctypes.WinDLL("advapi32", use_last_error=True)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
CreateToolhelp32Snapshot.restype = wintypes.HANDLE
Process32FirstW = kernel32.Process32FirstW
Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
Process32FirstW.restype = wintypes.BOOL
Process32NextW = kernel32.Process32NextW
Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
Process32NextW.restype = wintypes.BOOL
CloseHandle = kernel32.CloseHandle
OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE
QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
QueryFullProcessImageNameW.restype = wintypes.BOOL

TH32CS_SNAPPROCESS = 0x00000002


def snapshot_pids() -> dict[int, tuple[int, str]]:
    h = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if h in (0, wintypes.HANDLE(-1).value):
        return {}
    out: dict[int, tuple[int, str]] = {}
    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    ok = Process32FirstW(h, ctypes.byref(pe))
    while ok:
        out[int(pe.th32ProcessID)] = (int(pe.th32ParentProcessID), pe.szExeFile)
        ok = Process32NextW(h, ctypes.byref(pe))
    CloseHandle(h)
    return out


def image_path(pid: int) -> str:
    h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        h = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(32768)
        if QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        CloseHandle(h)


def classify(blob: str) -> str:
    s = blob.lower()
    if any(m.lower() in s for m in JARVIS_MARKERS):
        return "JARVIS"
    if any(m.lower() in s for m in CURSOR_MARKERS):
        return "CURSOR"
    if "amdrsserv" in s or r"\amd\cnext" in s:
        return "AMD"
    if "gradlew" in s or "minecraft" in s:
        return "MC"
    return "OTHER"


def chain(pid: int, snap: dict[int, tuple[int, str]], depth: int = 6) -> list[str]:
    rows = []
    seen: set[int] = set()
    cur = pid
    for _ in range(depth):
        if cur in seen or cur <= 0:
            break
        seen.add(cur)
        parent, name = snap.get(cur, (0, "?"))
        path = image_path(cur)
        rows.append(f"{name} pid={cur} parent={parent} exe={path}")
        cur = parent
    return rows


def log(line: str) -> None:
    ts = dt.datetime.now().strftime("%H:%M:%S")
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(f"{ts}\t{line}\n")


def main() -> int:
    open(OUT, "w", encoding="utf-8").write(
        f"# start {dt.datetime.now().isoformat()} duration={DURATION_S}s\n"
    )
    prev = set(snapshot_pids())
    end = time.monotonic() + DURATION_S
    ticks = 0
    while time.monotonic() < end:
        time.sleep(0.5)
        ticks += 1
        snap = snapshot_pids()
        now = set(snap)
        born = now - prev
        prev = now
        for pid in born:
            parent, name = snap.get(pid, (0, "?"))
            n = (name or "").lower()
            if n not in ("cmd.exe", "conhost.exe", "powershell.exe", "pwsh.exe"):
                continue
            anc = chain(pid, snap)
            blob = " | ".join(anc)
            tag = classify(blob)
            log(f"{tag}\t{name}\tpid={pid}\tppid={parent}\tchain={blob}")
        if ticks % 120 == 0:
            left = int(end - time.monotonic())
            log(f"HEARTBEAT\tleft={left}s")
    log(f"# end {dt.datetime.now().isoformat()}")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
