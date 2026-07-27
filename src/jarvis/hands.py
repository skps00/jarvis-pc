"""Whitelist launcher — only registry paths / steam / prism / chrome flag."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from jarvis.config import Profile, Registry
from jarvis import memory as mem


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
    try:
        if ltype == "steam_app":
            _launch_steam(launch)
            msg = f"{'已新開' if force_new else '已啟動'}：{profile.display_name}"
        elif ltype == "prism_instance":
            msg = _launch_prism(launch, force_new=force_new)
            if profile.kind == "launcher_instance":
                data = mem.load_memory(memory_path)
                data["last_prism_instance"] = str(launch.get("instance_id") or profile_id)
                mem.save_memory(data, memory_path)
            _touch_battlefield(registry, profile_id, memory_path)
            return LaunchResult(True, msg, profile_id)
        elif ltype == "app_exe":
            _launch_exe(launch)
            msg = f"{'已新開' if force_new else '已啟動'}：{profile.display_name}"
        elif ltype == "browser_restore":
            msg = _launch_chrome_restore(launch, ask_confirm=ask_confirm, force_new=force_new)
            _touch_battlefield(registry, profile_id, memory_path)
            return LaunchResult(True, msg, profile_id)
        elif ltype == "app_lnk":
            _launch_lnk(launch)
            msg = f"{'已新開' if force_new else '已啟動'}：{profile.display_name}"
        elif ltype == "script_file":
            _launch_script(launch)
            msg = f"已啟動：{profile.display_name}"
        else:
            return LaunchResult(False, f"未支援 launch.type：{ltype}", profile_id)
    except OSError as exc:
        return LaunchResult(False, f"啟動失敗：{exc}", profile_id)

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
                "| ForEach-Object { $_.CommandLine }",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _minecraft_instance_running(instance_id: str) -> bool:
    """Best-effort: Java process cmdline mentions this Prism instance id."""
    return any(_cmdline_matches_instance(line, instance_id) for line in _java_command_lines())


def _focus_window_title_contains(*needles: str) -> bool:
    """Bring first visible window whose title contains any needle (Windows)."""
    if sys.platform != "win32" or not needles:
        return False
    user32 = ctypes.windll.user32
    hits = [n.lower() for n in needles if n]
    found = False

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _lparam):  # noqa: ANN001
        nonlocal found
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buf, length)
        title = buf.value.lower()
        if any(n in title for n in hits):
            # ponytail: 只最小化先 SW_RESTORE；否則會把全螢幕／最大化拆成細窗
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            found = True
            return False
        return True

    user32.EnumWindows(_enum, 0)
    return found


def _launch_prism(launch: dict, *, force_new: bool = False) -> str:
    exe = Path(str(launch.get("prism_exe") or ""))
    instance_id = str(launch.get("instance_id") or "").strip()
    instance_name = str(launch.get("instance_name") or instance_id).strip()
    if not exe.is_file():
        raise OSError(f"找不到 Prism：{exe}")
    if not instance_id:
        raise OSError("prism_instance 缺少 instance_id")

    if not force_new and _minecraft_instance_running(instance_id):
        needles = [instance_name, "Minecraft", instance_id.replace("_", " ")]
        if _focus_window_title_contains(*needles):
            return f"Minecraft（{instance_name}）已在執行；已切換至遊戲視窗"
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


def _launch_lnk(launch: dict) -> None:
    """Open a Windows .lnk via Shell (os.startfile)."""
    import os

    lnk = Path(str(launch.get("lnk") or ""))
    if not lnk.is_file():
        raise OSError(f"找不到捷徑：{lnk}")
    if sys.platform != "win32":
        raise OSError("app_lnk 僅支援 Windows")
    os.startfile(str(lnk))  # noqa: S606


def _launch_chrome_restore(
    launch: dict,
    ask_confirm: Callable[[str], bool] | None = None,
    *,
    force_new: bool = False,
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
        # ponytail: 唔問殺 process；設計＝已開只 focus。多窗唔問邊個，focus Z-order 最上
        if _focus_window_title_contains("google chrome", "- chrome"):
            return (
                "Chrome 已在執行；已切換至現有視窗"
                "（多窗時唔問邊個，focus 最上層嗰個）"
            )
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
        elif ltype == "app_lnk":
            _launch_lnk(launch_hint)
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
    """Open last_battlefield profile if set (role layout is soft / later)."""
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


def system_power(
    action: str,
    *,
    ask_confirm: Callable[[str], bool] | None = None,
) -> LaunchResult:
    """Shutdown or sleep after Always Yes. No confirm → refuse (唔靜默關機)."""
    if action not in ("shutdown", "sleep"):
        return LaunchResult(False, f"未知電源動作：{action}")
    if sys.platform != "win32":
        return LaunchResult(False, "電源指令僅支援 Windows")

    label = "關機" if action == "shutdown" else "睡眠"
    ok = ask_confirm(f"確認要{label}？（危險動作）") if ask_confirm else False
    if not ok:
        return LaunchResult(False, f"已取消{label}")

    try:
        if action == "shutdown":
            # /t 0 即時；仍可喺確認窗取消
            subprocess.Popen(
                ["shutdown", "/s", "/t", "0"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return LaunchResult(True, "已下關機指令")
        # SetSuspendState(Hibernate=False, ForceCritical=False, DisableWakeEvent=False)
        ctypes.windll.powrprof.SetSuspendState(0, 0, 0)  # type: ignore[attr-defined]
        return LaunchResult(True, "已進入睡眠")
    except OSError as exc:
        return LaunchResult(False, f"{label}失敗：{exc}")
