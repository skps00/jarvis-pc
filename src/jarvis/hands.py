"""Whitelist launcher — only registry paths / steam / prism / chrome flag."""

from __future__ import annotations

import ctypes
import re
import subprocess
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from jarvis.config import Profile, Registry
from jarvis import memory as mem

# ponytail: short poll after startfile/steam; slow apps may miss → fall back process_names
_PID_TRACK_SECONDS = 4.0
_PID_TRACK_TYPES = frozenset({"app_exe", "app_lnk", "steam_app", "script_file", "shell_app"})


@dataclass
class LaunchResult:
    """Outcome of a Hands launch attempt."""

    ok: bool
    message: str
    profile_id: str | None = None


def _chrome_running() -> bool:
    """Return True if a chrome.exe process exists (Windows)."""
    if sys.platform != "win32":
        return False
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return "chrome.exe" in out.lower()


def _start_detached(args: list[str], cwd: str | None = None) -> None:
    """Start a process without waiting (Windows-friendly)."""
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        kwargs["close_fds"] = True
    subprocess.Popen(args, cwd=cwd, **kwargs)


def launch_profile(
    registry: Registry,
    profile_id: str,
    *,
    ask_confirm: Callable[[str], bool] | None = None,
    memory_path: Path | None = None,
    force_new: bool = False,
) -> LaunchResult:
    """Launch one enabled profile; updates memory for MC / battlefield."""
    profile = registry.profiles.get(profile_id)
    if profile is None:
        return LaunchResult(False, f"未知 profile id：{profile_id}")
    if not profile.enabled:
        return LaunchResult(False, f"已停用：{profile.display_name}")

    if profile.confirm == "always_yes" or profile.kind == "script":
        prompt = f"確認執行「{profile.display_name}」？[y/N] "
        ok = ask_confirm(prompt) if ask_confirm else False
        if not ok:
            return LaunchResult(False, "已取消（需要確認）", profile_id)

    launch = profile.launch
    ltype = str(launch.get("type") or "")
    track_names = (
        _close_process_names(profile) if ltype in _PID_TRACK_TYPES else []
    )
    before_pids = _pids_for_images(track_names) if track_names else set()
    mon = str(profile.restore.get("monitor") or "") or None
    role = str(profile.restore.get("role") or "") or None
    try:
        if ltype == "steam_app":
            msg = _launch_or_focus_steam(
                launch,
                display_name=profile.display_name,
                ask_confirm=ask_confirm,
                force_new=force_new,
                profile_id=profile_id,
                memory_path=memory_path,
                monitor=mon,
                role=role,
            )
        elif ltype == "prism_instance":
            msg = _launch_prism(
                launch, force_new=force_new, monitor=mon, role=role
            )
            if profile.kind == "launcher_instance":
                data = mem.load_memory(memory_path)
                data["last_prism_instance"] = str(launch.get("instance_id") or profile_id)
                mem.save_memory(data, memory_path)
            _touch_battlefield(registry, profile_id, memory_path)
            return LaunchResult(True, msg, profile_id)
        elif ltype == "app_exe":
            msg = _launch_or_focus_exe(
                launch,
                display_name=profile.display_name,
                force_new=force_new,
                monitor=mon,
                role=role,
            )
        elif ltype == "browser_restore":
            msg = _launch_chrome_restore(
                launch,
                ask_confirm=ask_confirm,
                force_new=force_new,
                monitor=mon,
                role=role,
            )
            _touch_battlefield(registry, profile_id, memory_path)
            return LaunchResult(True, msg, profile_id)
        elif ltype == "app_lnk":
            msg = _launch_or_focus_lnk(
                launch,
                display_name=profile.display_name,
                force_new=force_new,
                monitor=mon,
                role=role,
            )
        elif ltype == "shell_app":
            msg = _launch_or_focus_shell_app(
                launch,
                display_name=profile.display_name,
                force_new=force_new,
                monitor=mon,
                role=role,
            )
        elif ltype == "script_file":
            _launch_script(launch)
            msg = f"已啟動：{profile.display_name}"
        else:
            return LaunchResult(False, f"未支援 launch.type：{ltype}", profile_id)
    except OSError as exc:
        return LaunchResult(False, f"啟動失敗：{exc}", profile_id)

    if track_names:
        _remember_launch_pids(
            profile_id, track_names, before_pids, memory_path=memory_path
        )

    if profile.kind == "launcher_instance":
        data = mem.load_memory(memory_path)
        data["last_prism_instance"] = str(launch.get("instance_id") or profile_id)
        mem.save_memory(data, memory_path)
    if profile.kind in ("game", "launcher_instance", "app", "browser_session"):
        _touch_battlefield(registry, profile_id, memory_path)

    return LaunchResult(True, msg, profile_id)


def _touch_battlefield(registry: Registry, profile_id: str, memory_path: Path | None) -> None:
    data = mem.load_memory(memory_path)
    data["last_battlefield"] = profile_id
    mem.save_memory(data, memory_path)


def _launch_steam(launch: dict) -> None:
    app_id = str(launch.get("app_id") or "").strip()
    if not app_id:
        raise OSError("steam_app 缺少 app_id")
    # ponytail: steam protocol is enough on a normal Steam install
    if sys.platform == "win32":
        import os

        os.startfile(f"steam://rungameid/{app_id}")  # noqa: S606
        return
    subprocess.Popen(["xdg-open", f"steam://rungameid/{app_id}"])


def _process_names(launch: dict) -> list[str]:
    raw = launch.get("process_names") or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(x).strip() for x in raw if str(x).strip()]


def _image_running(image: str) -> bool:
    """True if tasklist finds image name (Windows)."""
    if sys.platform != "win32":
        return False
    name = image if image.lower().endswith(".exe") else f"{image}.exe"
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return name.lower() in out.lower()


def _any_process_running(names: list[str]) -> bool:
    return any(_image_running(n) for n in names)


def _kill_images(names: list[str]) -> None:
    """taskkill /F listed images. Raises OSError if all fail."""
    if sys.platform != "win32":
        raise OSError("關閉程序僅支援 Windows")
    errors: list[str] = []
    killed = False
    for image in names:
        name = image if image.lower().endswith(".exe") else f"{image}.exe"
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", name],
                check=False,
                capture_output=True,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            killed = True
        except OSError as exc:
            errors.append(f"{name}: {exc}")
    if not killed and errors:
        raise OSError("; ".join(errors))


def _pids_for_images(names: list[str]) -> set[int]:
    """PIDs currently running for given image names (Windows tasklist)."""
    found: set[int] = set()
    if sys.platform != "win32" or not names:
        return found
    for image in names:
        name = image if image.lower().endswith(".exe") else f"{image}.exe"
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                text=True,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.CalledProcessError):
            continue
        for line in out.splitlines():
            line = line.strip()
            if not line or line.upper().startswith("INFO:"):
                continue
            # "Discord.exe","12345","Console","1","12,345 K"
            parts = line.strip('"').split('","')
            if len(parts) < 2:
                continue
            try:
                found.add(int(parts[1]))
            except ValueError:
                continue
    return found


def _pid_alive(pid: int) -> bool:
    if sys.platform != "win32" or pid <= 0:
        return False
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return str(pid) in out and "INFO:" not in out.upper()


def _wait_new_pids(
    names: list[str],
    before: set[int],
    *,
    timeout: float = _PID_TRACK_SECONDS,
) -> list[int]:
    """Poll until new image PIDs appear after launch."""
    if not names:
        return []
    deadline = time.time() + timeout
    while time.time() < deadline:
        now = _pids_for_images(names)
        fresh = now - before
        if fresh:
            time.sleep(0.4)  # sibling processes (updater → main)
            return sorted(_pids_for_images(names) - before)
        time.sleep(0.25)
    return []


def _alive_remembered_pids(
    profile_id: str, memory_path: Path | None = None
) -> list[int]:
    """Live PIDs from memory; prune dead ones."""
    remembered = mem.get_profile_pids(profile_id, memory_path)
    alive = [p for p in remembered if _pid_alive(p)]
    if alive != remembered:
        mem.set_profile_pids(profile_id, alive, memory_path)
    return alive


def _remember_launch_pids(
    profile_id: str,
    names: list[str],
    before: set[int],
    *,
    memory_path: Path | None = None,
) -> list[int]:
    """After launch: keep prior live PIDs + newly appeared ones."""
    prior = _alive_remembered_pids(profile_id, memory_path)
    fresh = _wait_new_pids(names, before)
    merged = sorted(set(prior) | set(fresh))
    mem.set_profile_pids(profile_id, merged, memory_path)
    return merged


def _steam_focus_needles(display_name: str) -> tuple[str, ...]:
    """Window-title needles for Steam games (CS2 etc.)."""
    name = (display_name or "").strip()
    out: list[str] = []
    if name:
        out.append(name)
    low = name.lower()
    if "counter-strike" in low or name.upper() == "CS2" or "cs2" in low:
        out.extend(["Counter-Strike 2", "Counter-Strike"])
    # unique keep order
    seen: set[str] = set()
    uniq: list[str] = []
    for n in out:
        k = n.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(n)
    return tuple(uniq)


def _launch_or_focus_steam(
    launch: dict,
    *,
    display_name: str,
    ask_confirm: Callable[[str], bool] | None = None,
    force_new: bool = False,
    profile_id: str | None = None,
    memory_path: Path | None = None,
    monitor: str | None = None,
    role: str | None = None,
) -> str:
    """Launch via steam://; if already running (and not force_new) → focus window."""
    _ = ask_confirm, profile_id, memory_path
    names = _process_names(launch)
    if not force_new and names and _any_process_running(names):
        needles = _steam_focus_needles(display_name)
        if needles:
            ok, note = _focus_window_title_contains(
                *needles, monitor=monitor, role=role
            )
            if ok:
                return f"{display_name} 已在執行；已切換至視窗{note}"
        return f"{display_name} 已在執行；未搶到 focus（請 Alt+Tab）"
    _launch_steam(launch)
    return f"{'已新開' if force_new else '已啟動'}：{display_name}"


# backward alias for tests / imports
_launch_or_close_steam = _launch_or_focus_steam


def _cmdline_matches_instance(cmdline: str, instance_id: str) -> bool:
    """True if a Java cmdline looks like this Prism instance."""
    if not cmdline or not instance_id:
        return False
    low = cmdline.lower()
    iid = instance_id.lower()
    if iid in low:
        return True
    # instances\Foo_Bar or instances/Foo_Bar
    for sep in ("\\", "/"):
        if f"instances{sep}{iid}" in low:
            return True
    return False


def _java_command_lines() -> list[str]:
    """Collect javaw/java command lines on Windows."""
    return [cmdline for _pid, cmdline in _java_processes()]


def _java_processes() -> list[tuple[int, str]]:
    """Return (pid, cmdline) for java/javaw on Windows."""
    if sys.platform != "win32":
        return []
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter "
                "\"Name='javaw.exe' OR Name='java.exe'\" "
                "| Select-Object ProcessId, CommandLine "
                "| ConvertTo-Json -Compress",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    out = (out or "").strip()
    if not out:
        return []
    import json

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    rows: list[tuple[int, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            pid = int(item.get("ProcessId"))
        except (TypeError, ValueError):
            continue
        cmdline = str(item.get("CommandLine") or "").strip()
        if cmdline:
            rows.append((pid, cmdline))
    return rows


def _minecraft_instance_running(instance_id: str) -> bool:
    """Best-effort: Java process cmdline mentions this Prism instance id."""
    return any(_cmdline_matches_instance(line, instance_id) for line in _java_command_lines())


def _list_windows_title_contains(*needles: str) -> list[tuple[int, str, int]]:
    """
    Visible windows matching title needles, Z-order top→bottom.

    Each item: (hwnd, title, pid).
    """
    if sys.platform != "win32" or not needles:
        return []
    user32 = ctypes.windll.user32
    hits = [n.lower() for n in needles if n]
    out: list[tuple[int, str, int]] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _lparam):  # noqa: ANN001
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buf, length)
        title = buf.value
        if not title or not any(n in title.lower() for n in hits):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) > 0:
            out.append((int(hwnd), title, int(pid.value)))
        return True

    user32.EnumWindows(_enum, 0)
    return out


def _focus_hwnd(hwnd: int) -> bool:
    """Bring one hwnd to foreground (Windows)."""
    if sys.platform != "win32" or not hwnd:
        return False
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    # ponytail: 只最小化先 SW_RESTORE；否則會把全螢幕／最大化拆成細窗
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    else:
        user32.ShowWindow(hwnd, 5)  # SW_SHOW
    user32.BringWindowToTop(hwnd)
    fg = user32.GetForegroundWindow()
    if fg:
        tid_fg = user32.GetWindowThreadProcessId(fg, None)
        tid_self = kernel32.GetCurrentThreadId()
        if tid_fg and tid_self and tid_fg != tid_self:
            user32.AttachThreadInput(tid_self, tid_fg, True)
            user32.SetForegroundWindow(hwnd)
            user32.AttachThreadInput(tid_self, tid_fg, False)
        else:
            user32.SetForegroundWindow(hwnd)
    else:
        user32.SetForegroundWindow(hwnd)
    return True


def _role_layout_rect(
    work: tuple[int, int, int, int],
    role: str | None,
    *,
    keep_w: int,
    keep_h: int,
) -> tuple[int, int, int, int, str]:
    """
    Map restore.role → (x, y, w, h, note_suffix) inside work area.

    primary_game fills; chat/ide/browser split; else keep size at top-left.
    """
    left, top, right, bottom = work
    max_w = max(100, right - left)
    max_h = max(100, bottom - top)
    r = (role or "").strip().lower()
    if r in ("primary_game", "game"):
        return left, top, max_w, max_h, "鋪滿"
    if r in ("chat_or_map", "chat"):
        w = max(100, max_w // 2)
        return left + max_w - w, top, w, max_h, "右半"
    if r == "ide":
        w = max(100, (max_w * 2) // 3)
        return left, top, w, max_h, "左2/3"
    if r in ("browser", "browser_session"):
        w = max(100, (max_w * 2) // 3)
        return left + max_w - w, top, w, max_h, "右2/3"
    w = min(max(100, keep_w), max_w)
    h = min(max(100, keep_h), max_h)
    return left, top, w, h, "角"


def _monitor_work_areas() -> list[tuple[int, int, int, int]]:
    """
    Return work-area rects (left, top, right, bottom), primary first.

    Multi-monitor support for restore.monitor + restore.role.
    """
    if sys.platform != "win32":
        return []
    user32 = ctypes.windll.user32
    areas: list[tuple[int, int, int, int]] = []

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    MonitorEnumProc = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
    )

    primary: list[tuple[int, int, int, int]] = []
    others: list[tuple[int, int, int, int]] = []

    def _cb(hmon, _hdc, _lprc, _lp):  # noqa: ANN001
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            r = info.rcWork
            box = (int(r.left), int(r.top), int(r.right), int(r.bottom))
            if info.dwFlags & 1:  # MONITORINFOF_PRIMARY
                primary.append(box)
            else:
                others.append(box)
        return True

    user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_cb), 0)
    return primary + others


def _place_hwnd_on_monitor(
    hwnd: int,
    monitor: str,
    role: str | None = None,
) -> str:
    """
    Place window onto primary/secondary by restore.role layout.

    Returns short note or empty.
    """
    if sys.platform != "win32" or not hwnd or not monitor:
        return ""
    which = monitor.strip().lower()
    areas = _monitor_work_areas()
    if not areas:
        return ""
    if which in ("primary", "main", "1"):
        box = areas[0]
        label = "主螢幕"
    elif which in ("secondary", "second", "2", "aux"):
        if len(areas) < 2:
            return ""
        box = areas[1]
        label = "副螢幕"
    else:
        return ""
    user32 = ctypes.windll.user32
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return ""
    keep_w = int(rect.right - rect.left)
    keep_h = int(rect.bottom - rect.top)
    x, y, w, h, how = _role_layout_rect(box, role, keep_w=keep_w, keep_h=keep_h)
    user32.MoveWindow(hwnd, x, y, w, h, True)
    return f"；已移去{label}（{how}）"


def _focus_window_title_contains(
    *needles: str,
    monitor: str | None = None,
    role: str | None = None,
) -> tuple[bool, str]:
    """
    Focus Z-order topmost matching window; optional move to monitor+role.

    Returns (ok, note). note explains multi-window pick / monitor move.
    """
    wins = _list_windows_title_contains(*needles)
    if not wins:
        return False, ""
    hwnd, title, _pid = wins[0]
    note = ""
    if len(wins) > 1:
        short = title[:40] + ("…" if len(title) > 40 else "")
        note = f"；多窗×{len(wins)}揀最上「{short}」"
    ok = _focus_hwnd(hwnd)
    if ok and monitor:
        note += _place_hwnd_on_monitor(hwnd, monitor, role=role)
    return ok, note


def _window_pids_title_contains(*needles: str) -> list[int]:
    """Collect visible window owner PIDs whose title contains any needle."""
    seen: set[int] = set()
    out: list[int] = []
    for _hwnd, _title, pid in _list_windows_title_contains(*needles):
        if pid not in seen:
            seen.add(pid)
            out.append(pid)
    return out


def _launch_prism(
    launch: dict,
    *,
    force_new: bool = False,
    monitor: str | None = None,
    role: str | None = None,
) -> str:
    exe = Path(str(launch.get("prism_exe") or ""))
    instance_id = str(launch.get("instance_id") or "").strip()
    instance_name = str(launch.get("instance_name") or instance_id).strip()
    if not exe.is_file():
        raise OSError(f"找不到 Prism：{exe}")
    if not instance_id:
        raise OSError("prism_instance 缺少 instance_id")

    if not force_new and _minecraft_instance_running(instance_id):
        needles = [instance_name, "Minecraft", instance_id.replace("_", " ")]
        ok, note = _focus_window_title_contains(
            *needles, monitor=monitor, role=role
        )
        if ok:
            return f"Minecraft（{instance_name}）已在執行；已切換至遊戲視窗{note}"
        return f"Minecraft（{instance_name}）已在執行；未搶到 focus（請 Alt+Tab）"

    _start_detached([str(exe), "--launch", instance_id], cwd=str(exe.parent))
    if force_new:
        return f"已新開：{instance_name}"
    return f"已啟動：{instance_name}"


def _launch_exe(launch: dict) -> None:
    exe = Path(str(launch.get("exe") or ""))
    if not exe.is_file():
        raise OSError(f"找不到程式：{exe}")
    args = [str(exe)] + [str(a) for a in (launch.get("args") or [])]
    cwd = launch.get("working_dir")
    _start_detached(args, cwd=str(cwd) if cwd else str(exe.parent))


def _launch_or_focus_exe(
    launch: dict,
    *,
    display_name: str,
    force_new: bool = False,
    monitor: str | None = None,
    role: str | None = None,
) -> str:
    """Launch exe; if process_names already running → focus (not second copy)."""
    names = _process_names(launch)
    if not force_new and names and _any_process_running(names):
        needles = (display_name,) if display_name.strip() else ()
        if needles:
            ok, note = _focus_window_title_contains(
                *needles, monitor=monitor, role=role
            )
            if ok:
                return f"{display_name} 已在執行；已切換至視窗{note}"
        return f"{display_name} 已在執行；未搶到 focus（請 Alt+Tab）"
    _launch_exe(launch)
    return f"{'已新開' if force_new else '已啟動'}：{display_name}"


def _launch_script(launch: dict) -> None:
    path = Path(str(launch.get("path") or ""))
    if not path.is_file():
        raise OSError(f"找不到腳本：{path}")
    cwd = launch.get("working_dir")
    shell = str(launch.get("shell") or "bat").lower()
    if shell == "ps1":
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(path)]
    else:
        cmd = ["cmd", "/c", str(path)]
    extra = [str(a) for a in (launch.get("args") or [])]
    _start_detached(cmd + extra, cwd=str(cwd) if cwd else str(path.parent))


def _launch_shell_app(launch: dict) -> None:
    """Launch via shell:AppsFolder\\AppID (Start menu / Store apps)."""
    app_id = str(launch.get("app_id") or "").strip()
    if not app_id:
        raise OSError("shell_app 缺少 app_id")
    if sys.platform != "win32":
        raise OSError("shell_app 僅支援 Windows")
    # explorer handles both classic and UWP AppIDs from Get-StartApps
    subprocess.Popen(
        ["explorer.exe", f"shell:AppsFolder\\{app_id}"],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _shell_app_focus_needles(display_name: str) -> tuple[str, ...]:
    """Window-title needles for focus; prefer profile display_name only."""
    name = (display_name or "").strip()
    return (name,) if name else ()


def _launch_or_focus_shell_app(
    launch: dict,
    *,
    display_name: str,
    force_new: bool = False,
    monitor: str | None = None,
    role: str | None = None,
) -> str:
    """Launch shell_app; if already open (and not force_new) just focus window."""
    needles = _shell_app_focus_needles(display_name)
    if not force_new and needles and _window_pids_title_contains(*needles):
        ok, note = _focus_window_title_contains(
            *needles, monitor=monitor, role=role
        )
        if ok:
            return f"{display_name} 已在執行；已切換至視窗{note}"
        return f"{display_name} 已在執行；未搶到 focus（請 Alt+Tab）"

    _launch_shell_app(launch)
    if not needles:
        return f"{'已新開' if force_new else '已啟動'}：{display_name}"

    # Wait for window then focus (Store apps start slow)
    deadline = time.time() + 4.0
    while time.time() < deadline:
        ok, note = _focus_window_title_contains(
            *needles, monitor=monitor, role=role
        )
        if ok:
            return f"{'已新開' if force_new else '已啟動'}：{display_name}{note}"
        time.sleep(0.25)
    return f"{'已新開' if force_new else '已啟動'}：{display_name}（未搶到 focus）"


def _launch_lnk(launch: dict) -> None:
    """Open a Windows .lnk via Shell (os.startfile)."""
    import os

    lnk = Path(str(launch.get("lnk") or ""))
    if not lnk.is_file():
        raise OSError(f"找不到捷徑：{lnk}")
    if sys.platform != "win32":
        raise OSError("app_lnk 僅支援 Windows")
    os.startfile(str(lnk))  # noqa: S606


def _launch_or_focus_lnk(
    launch: dict,
    *,
    display_name: str,
    force_new: bool = False,
    monitor: str | None = None,
    role: str | None = None,
) -> str:
    """Open .lnk; if process_names running → focus."""
    names = _process_names(launch)
    if not force_new and names and _any_process_running(names):
        needles = (display_name,) if display_name.strip() else ()
        if needles:
            ok, note = _focus_window_title_contains(
                *needles, monitor=monitor, role=role
            )
            if ok:
                return f"{display_name} 已在執行；已切換至視窗{note}"
        return f"{display_name} 已在執行；未搶到 focus（請 Alt+Tab）"
    _launch_lnk(launch)
    return f"{'已新開' if force_new else '已啟動'}：{display_name}"


def _launch_chrome_restore(
    launch: dict,
    ask_confirm: Callable[[str], bool] | None = None,
    *,
    force_new: bool = False,
    monitor: str | None = None,
    role: str | None = None,
) -> str:
    """Cold-start restore, focus if running, or --new-window when force_new."""
    _ = ask_confirm
    exe = launch.get("exe")
    chrome = Path(str(exe)) if exe else Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not chrome.is_file():
        raise OSError(f"找不到 Chrome：{chrome}")

    if force_new:
        _start_detached([str(chrome), "--new-window"])
        return "已開新 Chrome 視窗（--new-window）"

    if _chrome_running():
        # ponytail: 唔問殺 process；設計＝已開只 focus。多窗揀 Z-order 最上
        ok, note = _focus_window_title_contains(
            "google chrome", "- chrome", monitor=monitor, role=role
        )
        if ok:
            return f"Chrome 已在執行；已切換至現有視窗{note or '（多窗揀最上）'}"
        return "Chrome 已在執行；未搶到 focus（請 Alt+Tab）"

    _start_detached([str(chrome), "--restore-last-session"])
    return (
        "已用 --restore-last-session 啟動 Chrome。"
        "若要多窗一齊返：下次用 Chrome 選單「結束 Google Chrome」關晒再開。"
    )


def launch_discovered(
    launch_hint: dict,
    *,
    ask_confirm: Callable[[str], bool] | None = None,
) -> LaunchResult:
    """
    One-shot launch from Discover without a Registry Profile.

    Used right after user confirms a candidate (before/after yaml write).
    """
    _ = ask_confirm  # reserved for future always_yes scripts
    ltype = str(launch_hint.get("type") or "")
    try:
        if ltype == "steam_app":
            _launch_steam(launch_hint)
        elif ltype == "prism_instance":
            msg = _launch_prism(launch_hint, force_new=False)
            return LaunchResult(True, msg, None)
        elif ltype == "app_exe" and launch_hint.get("lnk"):
            _launch_lnk({"lnk": launch_hint["lnk"]})
        elif ltype == "app_exe" and launch_hint.get("exe"):
            _launch_exe(launch_hint)
        elif ltype == "app_lnk":
            _launch_lnk(launch_hint)
        elif ltype == "shell_app":
            _launch_shell_app(launch_hint)
        else:
            return LaunchResult(False, f"未支援 discover launch：{ltype}")
    except OSError as exc:
        return LaunchResult(False, f"啟動失敗：{exc}")
    return LaunchResult(True, f"已啟動（Discover）：{ltype}")


def restore_battlefield(
    registry: Registry,
    *,
    ask_confirm: Callable[[str], bool] | None = None,
    memory_path: Path | None = None,
) -> LaunchResult:
    """Open last_battlefield profile if set (role layout via restore.role)."""
    data = mem.load_memory(memory_path)
    pid = data.get("last_battlefield")
    if not pid:
        return LaunchResult(False, "未有戰場紀錄（先開過 CS／MC／Cursor／Chrome）")
    return launch_profile(registry, str(pid), ask_confirm=ask_confirm, memory_path=memory_path)


def resolve_default_mc(
    registry: Registry,
    *,
    force_last: bool,
    memory_path: Path | None = None,
) -> tuple[str | None, str]:
    """
    Resolve _default_mc to a profile id.

    force_last:「開上次 MC」——必須有 Memory，否則失敗說明。
    """
    data = mem.load_memory(memory_path)
    last = data.get("last_prism_instance")
    by_instance = {
        str(p.launch.get("instance_id")): p.id
        for p in registry.profiles.values()
        if p.kind == "launcher_instance" and p.enabled
    }
    defaults = [p for p in registry.profiles.values() if p.enabled and p.use_as_default_mc]

    if force_last:
        if last and last in by_instance:
            return by_instance[last], "使用 Memory 上次實例"
        if last:
            # instance id stored directly as key match
            for p in registry.profiles.values():
                if p.launch.get("instance_id") == last:
                    return p.id, "使用 Memory 上次實例"
            return None, f"Memory 有實例「{last}」但 profiles 未登錄"
        return None, "未有上次 MC 紀錄（先開過具名 pack，或用「開 MC」）"

    if last:
        for p in registry.profiles.values():
            if p.enabled and p.launch.get("instance_id") == last:
                return p.id, "使用 Memory 上次實例"
    if len(defaults) == 1:
        return defaults[0].id, "使用 use_as_default_mc"
    if len(defaults) > 1:
        return None, "多個預設 MC，請講具名 pack 或先開一次以寫入 Memory"
    if defaults:
        return defaults[0].id, "使用預設 MC"
    return None, "未設定 use_as_default_mc 的 Prism 實例"


def _java_pids_for_instance(instance_id: str) -> list[int]:
    """PIDs of java/javaw whose cmdline matches Prism instance_id."""
    if not instance_id:
        return []
    return [
        pid
        for pid, cmdline in _java_processes()
        if _cmdline_matches_instance(cmdline, instance_id)
    ]


def _kill_pids(pids: list[int]) -> None:
    if sys.platform != "win32":
        raise OSError("關閉程序僅支援 Windows")
    if not pids:
        raise OSError("無對應 process 可關")
    for pid in pids:
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            check=False,
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )


def close_profile(
    registry: Registry,
    profile_id: str,
    *,
    ask_confirm: Callable[[str], bool] | None = None,
    memory_path: Path | None = None,
) -> LaunchResult:
    """Always Yes then kill remembered PIDs / process_names / Prism java."""
    if profile_id == "_pending_default_mc":
        resolved, note = resolve_default_mc(
            registry, force_last=False, memory_path=memory_path
        )
        if not resolved:
            return LaunchResult(False, note or "未有可關嘅 MC")
        profile_id = resolved

    profile = registry.profiles.get(profile_id)
    if profile is None:
        return LaunchResult(False, f"未知 profile id：{profile_id}")
    if not profile.enabled:
        return LaunchResult(False, f"已停用：{profile.display_name}")

    # check running before confirm（唔好問完先話未開）
    ltype = str(profile.launch.get("type") or "")
    if ltype == "prism_instance":
        iid = str(profile.launch.get("instance_id") or "")
        pids = _java_pids_for_instance(iid)
        if not pids:
            return LaunchResult(
                False, f"「{profile.display_name}」未在運行", profile_id
            )
        ok = (
            ask_confirm(f"確認關閉「{profile.display_name}」？")
            if ask_confirm
            else False
        )
        if not ok:
            return LaunchResult(False, f"已取消關閉：{profile.display_name}", profile_id)
        try:
            _kill_pids(pids)
        except OSError as exc:
            return LaunchResult(False, f"關閉失敗：{exc}", profile_id)
        mem.clear_profile_pids(profile_id, memory_path)
        return LaunchResult(
            True,
            f"已關閉：{profile.display_name}（Prism java ×{len(pids)}）",
            profile_id,
        )

    remembered = _alive_remembered_pids(profile_id, memory_path)
    names = _close_process_names(profile)
    if remembered:
        ok = (
            ask_confirm(f"確認關閉「{profile.display_name}」？")
            if ask_confirm
            else False
        )
        if not ok:
            return LaunchResult(False, f"已取消關閉：{profile.display_name}", profile_id)
        try:
            _kill_pids(remembered)
        except OSError as exc:
            return LaunchResult(False, f"關閉失敗：{exc}", profile_id)
        mem.clear_profile_pids(profile_id, memory_path)
        return LaunchResult(
            True,
            f"已關閉：{profile.display_name}（記住 PID ×{len(remembered)}）",
            profile_id,
        )

    # shell_app fallback: process name may differ (Store/UWP wrapper)
    if ltype == "shell_app":
        pids = _window_pids_title_contains(profile.display_name, profile.id)
        if pids:
            ok = (
                ask_confirm(f"確認關閉「{profile.display_name}」？")
                if ask_confirm
                else False
            )
            if not ok:
                return LaunchResult(False, f"已取消關閉：{profile.display_name}", profile_id)
            try:
                _kill_pids(pids)
            except OSError as exc:
                return LaunchResult(False, f"關閉失敗：{exc}", profile_id)
            mem.clear_profile_pids(profile_id, memory_path)
            return LaunchResult(
                True,
                f"已關閉：{profile.display_name}（視窗標題 ×{len(pids)}）",
                profile_id,
            )

    if not names:
        return LaunchResult(
            False,
            f"「{profile.display_name}」未設 process_names，唔知關邊個 process",
            profile_id,
        )
    if not _any_process_running(names):
        return LaunchResult(False, f"「{profile.display_name}」未在運行", profile_id)

    ok = (
        ask_confirm(f"確認關閉「{profile.display_name}」？") if ask_confirm else False
    )
    if not ok:
        return LaunchResult(False, f"已取消關閉：{profile.display_name}", profile_id)
    try:
        _kill_images(names)
    except OSError as exc:
        return LaunchResult(False, f"關閉失敗：{exc}", profile_id)
    mem.clear_profile_pids(profile_id, memory_path)
    return LaunchResult(
        True,
        f"已關閉：{profile.display_name}（process_names：{', '.join(names)}）",
        profile_id,
    )


def _resolve_lnk_target(lnk: str | Path) -> Path | None:
    """Resolve Windows .lnk TargetPath via WScript.Shell."""
    if sys.platform != "win32":
        return None
    path = Path(lnk)
    if not path.is_file():
        return None
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
                f"'{str(path).replace(chr(39), chr(39)+chr(39))}'); "
                "$s.TargetPath",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    target = (out or "").strip().strip('"')
    if not target:
        return None
    return Path(target)


def _close_process_names(profile: Profile) -> list[str]:
    names = _process_names(profile.launch)
    if names:
        return names
    ltype = str(profile.launch.get("type") or "")
    if ltype == "browser_restore":
        return ["chrome.exe"]
    if ltype == "app_exe" and profile.launch.get("exe"):
        return [Path(str(profile.launch["exe"])).name]
    if ltype in ("app_lnk", "app_exe") and profile.launch.get("lnk"):
        target = _resolve_lnk_target(str(profile.launch["lnk"]))
        if target and target.name:
            return [target.name]
    # last resort: display_name.exe（Discord／WhatsApp）
    label = (profile.display_name or profile.id or "").strip()
    if label and re.match(r"^[A-Za-z0-9][\w .-]*$", label):
        return [f"{label}.exe" if not label.lower().endswith(".exe") else label]
    return []


def restart_profile(
    registry: Registry,
    profile_id: str,
    *,
    ask_confirm: Callable[[str], bool] | None = None,
    memory_path: Path | None = None,
) -> LaunchResult:
    """Always Yes once: kill if running, then launch."""
    import time

    if profile_id == "_pending_default_mc":
        resolved, note = resolve_default_mc(
            registry, force_last=False, memory_path=memory_path
        )
        if not resolved:
            return LaunchResult(False, note or "未有可重開嘅 MC")
        profile_id = resolved

    profile = registry.profiles.get(profile_id)
    if profile is None:
        return LaunchResult(False, f"未知 profile id：{profile_id}")
    if not profile.enabled:
        return LaunchResult(False, f"已停用：{profile.display_name}")

    ok = ask_confirm(f"確認重開「{profile.display_name}」？") if ask_confirm else False
    if not ok:
        return LaunchResult(False, f"已取消重開：{profile.display_name}", profile_id)

    ltype = str(profile.launch.get("type") or "")
    try:
        if ltype == "prism_instance":
            iid = str(profile.launch.get("instance_id") or "")
            pids = _java_pids_for_instance(iid)
            if pids:
                _kill_pids(pids)
                time.sleep(1.5)
        else:
            remembered = _alive_remembered_pids(profile_id, memory_path)
            if remembered:
                _kill_pids(remembered)
                mem.clear_profile_pids(profile_id, memory_path)
                time.sleep(1.5)
            else:
                names = _close_process_names(profile)
                if names and _any_process_running(names):
                    _kill_images(names)
                    mem.clear_profile_pids(profile_id, memory_path)
                    time.sleep(1.5)
    except OSError as exc:
        return LaunchResult(False, f"重開時關閉失敗：{exc}", profile_id)

    launched = launch_profile(
        registry,
        profile_id,
        ask_confirm=None,
        memory_path=memory_path,
        force_new=False,
    )
    if not launched.ok:
        return LaunchResult(False, f"已關但啟動失敗：{launched.message}", profile_id)
    return LaunchResult(True, f"已重開：{profile.display_name}", profile_id)


def system_power(
    action: str,
    *,
    ask_confirm: Callable[[str], bool] | None = None,
) -> LaunchResult:
    """Shutdown / reboot / sleep after Always Yes. No confirm → refuse."""
    if action not in ("shutdown", "sleep", "reboot"):
        return LaunchResult(False, f"未知電源動作：{action}")
    if sys.platform != "win32":
        return LaunchResult(False, "電源指令僅支援 Windows")

    label = {"shutdown": "關機", "sleep": "睡眠", "reboot": "重新開機"}[action]
    ok = ask_confirm(f"確認要{label}？（危險動作）") if ask_confirm else False
    if not ok:
        return LaunchResult(False, f"已取消{label}")

    try:
        if action == "shutdown":
            subprocess.Popen(
                ["shutdown", "/s", "/t", "0"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return LaunchResult(True, "已下關機指令")
        if action == "reboot":
            subprocess.Popen(
                ["shutdown", "/r", "/t", "0"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return LaunchResult(True, "已下重新開機指令")
        ctypes.windll.powrprof.SetSuspendState(0, 0, 0)  # type: ignore[attr-defined]
        return LaunchResult(True, "已進入睡眠")
    except OSError as exc:
        return LaunchResult(False, f"{label}失敗：{exc}")
