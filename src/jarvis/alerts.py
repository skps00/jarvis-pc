"""Voice alerts via Windows toast + taskbar flash + Discord badge poll.

WhatsApp／Cursor often land in Action Center (Toast). Discord desktop often
does **not** — it only paints a taskbar overlay. We poll the taskbar button
name via UI Automation (``Discord - N …``) so alerts work while focused.

``HSHELL_FLASH`` remains a fallback when the taskbar flashes (unfocused).

English-only phrases — ``mouth.speak`` skips CJK.
"""

from __future__ import annotations

import ctypes
import re
import sys
import threading
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Discord window title fallback: "(N) … Discord"
_DISCORD_UNREAD = re.compile(r"\((\d+)\)")
# Taskbar button: "Discord - 3 個通知尚未讀取" / "Discord - 1 unread"
_DISCORD_TB_NUM = re.compile(
    r"^discord(?:\s*(?:ptb|canary))?\s*[-–—]\s*(\d+)",
    re.I,
)
_DISCORD_TB_MARK = re.compile(
    r"discord.*(?:unread|notification|通知|尚未|未讀|未读)",
    re.I,
)
# Title busy — avoid bare "planning" (Plan Mode chrome / old chat noise).
_CURSOR_BUSY = re.compile(
    r"generating|thinking\b|running agent|agent running|"
    r"applying|working\.\.\.|composer.*run",
    re.I,
)
# Toast attention beyond Done (Done handled by cursor_toast_is_done).
_CURSOR_NEEDS_YOU = re.compile(
    r"waiting\s+for\s+approval|"
    r"switch(?:ing)?\s+mode|"
    r"switch\s+to\s+plan|"
    r"plan\s*mode",
    re.I,
)
_CURSOR_UIA_WAIT_EXACT = "waiting for approval"

_POLL_S = 2.0
_CURSOR_IDLE_HOLD_S = 2.0
# Must stay "busy" this long before idle can mean "agent finished".
_CURSOR_BUSY_HOLD_S = 4.0
# Approval card gone this long before latch clears (click/flicker safe).
_CURSOR_ATTENTION_CLEAR_S = 6.0
HSHELL_FLASH = 0x8006
WM_DESTROY = 0x0002
WM_QUIT = 0x0012


@dataclass
class AlertEvent:
    """One spoken alert."""

    kind: str  # discord | cursor | test
    phrase: str
    detail: str = ""


def discord_unread_count(titles: list[str]) -> int:
    """Max (N) badge across Discord window titles; 0 if none."""
    best = 0
    for t in titles:
        for m in _DISCORD_UNREAD.finditer(t or ""):
            try:
                best = max(best, int(m.group(1)))
            except ValueError:
                continue
    return best


def discord_taskbar_unread(name: str) -> int:
    """Parse unread from Discord taskbar button name.

    Examples: ``Discord - 3 個通知尚未讀取``, ``Discord - 1 unread message``.
    Returns 1 for unread-without-number marks; 0 if idle ``Discord``.
    """
    s = (name or "").strip()
    if not s:
        return 0
    m = _DISCORD_TB_NUM.match(s)
    if m:
        try:
            return max(0, int(m.group(1)))
        except ValueError:
            return 0
    if _DISCORD_TB_MARK.search(s):
        return 1
    return 0


def cursor_titles_busy(titles: list[str]) -> bool:
    """True if any Cursor title looks like an agent is working."""
    return any(_CURSOR_BUSY.search(t or "") for t in titles)


def classify_exe(exe_path: str) -> str | None:
    """Map process image path → alert kind (discord|cursor|whatsapp) or None."""
    name = Path(exe_path or "").name.lower()
    if name in ("discord.exe", "discordptb.exe", "discordcanary.exe"):
        return "discord"
    if name == "cursor.exe":
        return "cursor"
    if name in ("whatsapp.exe", "whatsapp.desktop.exe"):
        return "whatsapp"
    return None


def parse_extra_apps(raw: str | list[str] | None) -> list[str]:
    """Comma／newline separated display-name needles (lowercase)."""
    if raw is None:
        return []
    if isinstance(raw, list):
        parts = [str(x) for x in raw]
    else:
        parts = re.split(r"[,;\n]+", str(raw))
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        n = p.strip().lower()
        if len(n) < 2 or n in seen:
            continue
        # built-ins handled separately
        if n in ("discord", "cursor", "whatsapp"):
            continue
        seen.add(n)
        out.append(n)
    return out


def toast_app_kind(
    app_name: str,
    *,
    aumid: str = "",
    extra: list[str] | None = None,
) -> str | None:
    """Map Windows toast app display name／AUMID → alert kind.

    Built-ins: discord | cursor | whatsapp.
    Extra needles → kind ``extra:<AppDisplayName>``.
    """
    a = (app_name or "").strip()
    low = a.lower()
    aid = (aumid or "").strip().lower()
    if "discord" in low or "discord" in aid:
        return "discord"
    if low == "cursor" or low.startswith("cursor ") or "anysphere.cursor" in aid:
        return "cursor"
    if "whatsapp" in low or "whatsapp" in aid:
        return "whatsapp"
    if not a:
        return None
    for needle in extra or []:
        if needle and needle in low:
            return f"extra:{a}"
    return None


def alert_phrase_for(kind: str, *, app_label: str = "") -> str:
    """English TTS phrase for alert kind."""
    if kind == "discord":
        return "Discord has a new message."
    if kind == "cursor":
        return "Cursor finished its work."
    if kind == "cursor_plan":
        return "Cursor wants plan mode."
    if kind == "cursor_approve":
        return "Cursor needs your approval."
    if kind == "whatsapp":
        return "WhatsApp has a new message."
    if kind.startswith("extra:"):
        label = (app_label or kind[6:] or "App").strip()
        # Piper ASCII-only — strip non-ascii from label
        safe = "".join(ch if ord(ch) < 128 else " " for ch in label).strip()
        safe = re.sub(r"\s+", " ", safe) or "App"
        return f"{safe} has a notification."
    return "You have a notification."


def cursor_toast_is_done(texts: list[str]) -> bool:
    """True if Cursor toast looks like agent finished (not every UI toast)."""
    blob = " ".join(texts or []).strip().lower()
    if not blob:
        return False
    if blob.startswith("done"):
        return True
    if "agent's output" in blob or "agents output" in blob:
        return True
    if "finished" in blob and "agent" in blob:
        return True
    return False


def cursor_needs_attention(texts: list[str]) -> bool:
    """True if Cursor toast/UI text needs user (done, plan switch, approval)."""
    blob = " ".join(texts or []).strip()
    if not blob:
        return False
    if cursor_toast_is_done([blob]):
        return True
    return bool(_CURSOR_NEEDS_YOU.search(blob))


def cursor_uia_name_is_wait(name: str) -> bool:
    """True only for the pending-card wait label — not chat that mentions it."""
    return (name or "").strip().casefold() == _CURSOR_UIA_WAIT_EXACT


def cursor_attention_phrase(texts: list[str]) -> str:
    """Pick TTS phrase from Cursor attention blob."""
    blob = " ".join(texts or []).strip().lower()
    if "plan" in blob and (
        "mode" in blob or "switch" in blob or "waiting" in blob
    ):
        return alert_phrase_for("cursor_plan")
    if cursor_toast_is_done(texts):
        return alert_phrase_for("cursor")
    if _CURSOR_NEEDS_YOU.search(blob):
        return alert_phrase_for("cursor_approve")
    return alert_phrase_for("cursor_approve")


def _toast_texts(notification) -> list[str]:
    """Best-effort plain text lines from a WinRT toast notification."""
    out: list[str] = []
    try:
        for binding in notification.visual.bindings:
            try:
                for el in binding.get_text_elements():
                    t = (el.text or "").strip()
                    if t:
                        out.append(t)
            except Exception:
                continue
    except Exception:
        pass
    return out


def _toast_created_before(notification, floor) -> bool:
    """True if toast creation_time is before *floor* (aware UTC datetime).

    Stale Action Center entries sometimes reappear with a new id — still old.
    """
    if floor is None:
        return False
    try:
        import datetime as _dt

        raw = getattr(notification, "creation_time", None)
        if raw is None:
            return False
        # winrt may give datetime or a tick wrapper
        if isinstance(raw, _dt.datetime):
            created = raw
        else:
            # datetimeoffset-like: .universal_time or convert via timestamp
            ts = getattr(raw, "timestamp", None)
            if callable(ts):
                created = _dt.datetime.fromtimestamp(ts(), tz=_dt.timezone.utc)
            else:
                return False
        if created.tzinfo is None:
            created = created.replace(tzinfo=_dt.timezone.utc)
        return created < floor
    except Exception:
        return False


def _list_windows_for_pids(pids: set[int]) -> list[str]:
    """Visible window titles owned by *pids* (Windows)."""
    if sys.platform != "win32" or not pids:
        return []
    user32 = ctypes.windll.user32
    titles: list[str] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _lparam):  # noqa: ANN001
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd) + 1
        if length <= 1:
            return True
        buf = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buf, length)
        title = buf.value
        if not title:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) in pids:
            titles.append(title)
        return True

    user32.EnumWindows(_enum, 0)
    return titles


def _exe_for_hwnd(hwnd: int) -> str:
    """Best-effort full path of process owning *hwnd*."""
    if not hwnd:
        return ""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        # QueryFullProcessImageNameW
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return ""
        return buf.value
    finally:
        kernel32.CloseHandle(handle)


def _discord_taskbar_names_uia() -> list[str] | None:
    """Discord taskbar button names via UI Automation; None if unavailable."""
    if sys.platform != "win32":
        return None
    try:
        import comtypes  # type: ignore
        import comtypes.client  # type: ignore
    except ImportError:
        return None
    try:
        comtypes.CoInitialize()
    except OSError:
        pass
    try:
        try:
            from comtypes.gen.UIAutomationClient import (  # type: ignore
                CUIAutomation,
                TreeScope_Children,
                TreeScope_Descendants,
                UIA_AutomationIdPropertyId,
                UIA_ClassNamePropertyId,
            )
        except (ImportError, OSError, AttributeError):
            comtypes.client.GetModule("UIAutomationCore.dll")
            from comtypes.gen.UIAutomationClient import (  # type: ignore
                CUIAutomation,
                TreeScope_Children,
                TreeScope_Descendants,
                UIA_AutomationIdPropertyId,
                UIA_ClassNamePropertyId,
            )
        uia = comtypes.client.CreateObject(CUIAutomation)
        root = uia.GetRootElement()
        aumids = (
            "com.squirrel.Discord.Discord",
            "com.squirrel.DiscordPTB.DiscordPTB",
            "com.squirrel.DiscordCanary.DiscordCanary",
        )
        id_conds = [
            uia.CreatePropertyCondition(UIA_AutomationIdPropertyId, aid)
            for aid in aumids
        ]
        discord_cond = id_conds[0]
        for c in id_conds[1:]:
            discord_cond = uia.CreateOrCondition(discord_cond, c)
        names: list[str] = []
        for cls in ("Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
            try:
                tb_cond = uia.CreatePropertyCondition(UIA_ClassNamePropertyId, cls)
                trays = root.FindAll(TreeScope_Children, tb_cond)
            except Exception:
                continue
            if trays is None:
                continue
            for i in range(int(trays.Length)):
                tray = trays.GetElement(i)
                try:
                    hits = tray.FindAll(TreeScope_Descendants, discord_cond)
                except Exception:
                    continue
                if hits is None:
                    continue
                for j in range(int(hits.Length)):
                    try:
                        nm = hits.GetElement(j).CurrentName or ""
                    except Exception:
                        continue
                    if nm:
                        names.append(nm)
        return names
    except Exception:
        return None


def _discord_unread_best(*, title_n: int, tb_names: list[str] | None) -> int:
    """Max of title (N) badge and taskbar overlay parse."""
    best = max(0, int(title_n))
    if not tb_names:
        return best
    for nm in tb_names:
        best = max(best, discord_taskbar_unread(nm))
    return best


def _cursor_hwnds_for_pids(pids: set[int]) -> list[int]:
    """Visible top-level HWND owned by *pids*."""
    if sys.platform != "win32" or not pids:
        return []
    user32 = ctypes.windll.user32
    out: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _lparam):  # noqa: ANN001
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) in pids:
            out.append(int(hwnd))
        return True

    user32.EnumWindows(_enum, 0)
    return out


def _cursor_uia_waiting_approval(pids: set[int]) -> tuple[bool, str]:
    """True if Cursor shows approval card (Switch mode / Ask / MCP auth).

    Matches workbench waitText ``Waiting for approval`` (not chat 'plan' noise).
    Returns (hit, detail).
    """
    if sys.platform != "win32" or not pids:
        return False, ""
    try:
        import comtypes  # type: ignore
        import comtypes.client  # type: ignore
    except ImportError:
        return False, ""
    try:
        comtypes.CoInitialize()
    except OSError:
        pass
    try:
        try:
            from comtypes.gen.UIAutomationClient import (  # type: ignore
                CUIAutomation,
                TreeScope_Descendants,
                UIA_ButtonControlTypeId,
                UIA_ControlTypePropertyId,
                UIA_TextControlTypeId,
            )
        except (ImportError, OSError, AttributeError):
            comtypes.client.GetModule("UIAutomationCore.dll")
            from comtypes.gen.UIAutomationClient import (  # type: ignore
                CUIAutomation,
                TreeScope_Descendants,
                UIA_ButtonControlTypeId,
                UIA_ControlTypePropertyId,
                UIA_TextControlTypeId,
            )
        uia = comtypes.client.CreateObject(CUIAutomation)
        names: list[str] = []
        for hwnd in _cursor_hwnds_for_pids(pids)[:3]:
            try:
                el = uia.ElementFromHandle(hwnd)
            except Exception:
                continue
            for ctid in (UIA_ButtonControlTypeId, UIA_TextControlTypeId):
                try:
                    cond = uia.CreatePropertyCondition(
                        UIA_ControlTypePropertyId, ctid
                    )
                    found = el.FindAll(TreeScope_Descendants, cond)
                except Exception:
                    continue
                if found is None:
                    continue
                n = min(int(found.Length), 300)
                for i in range(n):
                    try:
                        nm = (found.GetElement(i).CurrentName or "").strip()
                    except Exception:
                        continue
                    if nm and len(nm) <= 80:
                        names.append(nm)
        if not names:
            return False, ""
        # Exact wait label only. Substring matches chat bubbles that quote
        # "Waiting for approval" (clicking that chat → false alert).
        planish = any(n.strip().casefold() == "plan mode" for n in names)
        for nm in names:
            if cursor_uia_name_is_wait(nm):
                tag = "plan:" if planish else ""
                return True, f"uia:{tag}{nm}"
        return False, ""
    except Exception:
        return False, ""


class AlertWatcher:
    """Shell-hook flash + title poller → English TTS alerts."""

    def __init__(
        self,
        *,
        on_event: Callable[[AlertEvent], None] | None = None,
        on_log: Callable[[str], None] | None = None,
    ) -> None:
        self._on_event = on_event
        self._on_log = on_log
        self._stop = threading.Event()
        self._poll_thread: threading.Thread | None = None
        self._hook_thread: threading.Thread | None = None
        self._hwnd = None
        self._enabled = True
        self._discord = True
        self._cursor = True
        # When False, Cursor alerts come from stop hook → queue only.
        self._cursor_watch = False
        self._whatsapp = True
        self._extra: list[str] = []
        self._always = True  # toast poll (works while focused)
        self._cd = 0.0  # 0 = no cooldown
        self._last_speak = 0.0
        self._discord_prev: int | None = None
        self._cursor_was_busy = False
        self._cursor_busy_since = 0.0
        self._cursor_idle_since = 0.0
        self._cursor_alerted_for_cycle = False
        self._cursor_attention_latched = False
        self._cursor_attention_gone_since = 0.0
        self._toast_epoch = 0.0  # monotonic; skip toasts created before start
        self._lock = threading.Lock()
        self._toast_thread: threading.Thread | None = None

    def configure(
        self,
        *,
        enabled: bool | None = None,
        discord: bool | None = None,
        cursor: bool | None = None,
        cursor_watch: bool | None = None,
        whatsapp: bool | None = None,
        always: bool | None = None,
        extra: str | list[str] | None = None,
        cd_seconds: float | None = None,
    ) -> None:
        if enabled is not None:
            self._enabled = bool(enabled)
        if discord is not None:
            self._discord = bool(discord)
        if cursor is not None:
            self._cursor = bool(cursor)
        if cursor_watch is not None:
            self._cursor_watch = bool(cursor_watch)
        if whatsapp is not None:
            self._whatsapp = bool(whatsapp)
        if always is not None:
            self._always = bool(always)
        if extra is not None:
            self._extra = parse_extra_apps(extra)
        if cd_seconds is not None:
            self._cd = max(0.0, float(cd_seconds))

    def start(self) -> None:
        if sys.platform != "win32":
            return
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._stop.clear()
        self._hook_thread = threading.Thread(
            target=self._hook_loop, daemon=True, name="jarvis-alert-hook"
        )
        self._poll_thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="jarvis-alert-poll"
        )
        self._toast_thread = threading.Thread(
            target=self._toast_loop, daemon=True, name="jarvis-alert-toast"
        )
        self._hook_thread.start()
        self._poll_thread.start()
        self._toast_thread.start()
        self._log(
            "[ok] 語音提醒已開（Toast／Flash；Cursor 預設靠 stop hook）"
        )

    def stop(self, *, join_timeout: float = 1.5) -> None:
        self._stop.set()
        hwnd = self._hwnd
        if hwnd:
            try:
                ctypes.windll.user32.PostMessageW(hwnd, WM_DESTROY, 0, 0)
            except Exception:
                pass
        for th in (self._hook_thread, self._poll_thread, self._toast_thread):
            if th is not None and th.is_alive() and th is not threading.current_thread():
                th.join(timeout=join_timeout)
        self._hook_thread = None
        self._poll_thread = None
        self._toast_thread = None
        self._hwnd = None

    def emit_test(self) -> None:
        """Force one test phrase (settings button)."""
        self._emit(
            AlertEvent(kind="test", phrase="Alert system ready.", detail="manual test"),
            force=True,
        )

    def _log(self, msg: str) -> None:
        if self._on_log:
            try:
                self._on_log(msg)
            except Exception:
                pass

    def _emit(self, ev: AlertEvent, *, force: bool = False) -> None:
        now = time.monotonic()
        with self._lock:
            if (
                not force
                and self._cd > 0
                and now - self._last_speak < self._cd
            ):
                return
            self._last_speak = now
        self._log(f"[alert] {ev.kind}: {ev.detail or ev.phrase}")
        if self._on_event:
            try:
                self._on_event(ev)
            except Exception:
                pass

    def _on_flash(self, hwnd: int) -> None:
        if not self._enabled or not hwnd:
            return
        kind = classify_exe(_exe_for_hwnd(int(hwnd)))
        if kind == "discord" and self._discord:
            self._emit(
                AlertEvent(
                    kind="discord",
                    phrase=alert_phrase_for("discord"),
                    detail="taskbar flash",
                )
            )
        elif kind == "cursor" and self._cursor and self._cursor_watch:
            self._emit(
                AlertEvent(
                    kind="cursor",
                    phrase="Cursor needs your attention.",
                    detail="taskbar flash",
                )
            )
        elif kind == "whatsapp" and self._whatsapp:
            self._emit(
                AlertEvent(
                    kind="whatsapp",
                    phrase=alert_phrase_for("whatsapp"),
                    detail="taskbar flash",
                )
            )

    def _toast_loop(self) -> None:
        """Poll Windows notification center for watched app toasts."""
        try:
            import asyncio

            from winrt.windows.ui.notifications import NotificationKinds
            from winrt.windows.ui.notifications.management import (
                UserNotificationListener,
                UserNotificationListenerAccessStatus,
            )
        except ImportError:
            self._log(
                '[warn] Toast 提醒未裝：pip install "jarvis-pc[alerts]"'
            )
            return

        async def run() -> None:
            listener = UserNotificationListener.current
            access = await listener.request_access_async()
            if access != UserNotificationListenerAccessStatus.ALLOWED:
                self._log(
                    "[warn] Windows 拒絕對通知存取；設定→私隱→通知"
                )
                return
            seen: set[int] = set()
            # Wall-clock floor: ignore Action Center leftovers / recycled IDs
            # whose creation_time is before this loop started.
            import datetime as _dt

            toast_started = _dt.datetime.now(_dt.timezone.utc)
            self._toast_epoch = time.monotonic()
            try:
                existing = await listener.get_notifications_async(
                    NotificationKinds.TOAST
                )
                for n in existing:
                    seen.add(int(n.id))
            except Exception as exc:  # noqa: BLE001
                self._log(f"[warn] toast seed: {exc}")
            self._log("[ok] Toast 監聽中（前景亦提醒）")
            while not self._stop.is_set():
                if self._enabled and self._always:
                    try:
                        notes = await listener.get_notifications_async(
                            NotificationKinds.TOAST
                        )
                        for n in notes:
                            nid = int(n.id)
                            if nid in seen:
                                continue
                            seen.add(nid)
                            if _toast_created_before(n, toast_started):
                                continue
                            try:
                                app = n.app_info.display_info.display_name or ""
                            except Exception:
                                app = ""
                            try:
                                aumid = str(
                                    getattr(n.app_info, "app_user_model_id", "")
                                    or ""
                                )
                            except Exception:
                                aumid = ""
                            kind = toast_app_kind(
                                app, aumid=aumid, extra=self._extra
                            )
                            if not kind:
                                continue
                            texts = _toast_texts(n.notification)
                            detail = "toast " + (
                                " | ".join(texts)[:80] or app
                            )
                            if kind == "discord" and self._discord:
                                self._emit(
                                    AlertEvent(
                                        kind="discord",
                                        phrase=alert_phrase_for("discord"),
                                        detail=detail,
                                    )
                                )
                            elif (
                                kind == "cursor"
                                and self._cursor
                                and self._cursor_watch
                            ):
                                if cursor_needs_attention(texts):
                                    self._emit(
                                        AlertEvent(
                                            kind="cursor",
                                            phrase=cursor_attention_phrase(
                                                texts
                                            ),
                                            detail=detail,
                                        )
                                    )
                            elif kind == "whatsapp" and self._whatsapp:
                                self._emit(
                                    AlertEvent(
                                        kind="whatsapp",
                                        phrase=alert_phrase_for("whatsapp"),
                                        detail=detail,
                                    )
                                )
                            elif kind.startswith("extra:"):
                                self._emit(
                                    AlertEvent(
                                        kind="extra",
                                        phrase=alert_phrase_for(
                                            kind, app_label=app
                                        ),
                                        detail=detail,
                                    )
                                )
                        if len(seen) > 4000:
                            # ponytail: drop oldest half of id set
                            seen = set(sorted(seen)[-2000:])
                    except Exception as exc:  # noqa: BLE001
                        self._log(f"[warn] toast poll: {exc}")
                        await asyncio.sleep(3.0)
                await asyncio.sleep(1.2)

        try:
            asyncio.run(run())
        except Exception as exc:  # noqa: BLE001
            self._log(f"[warn] toast loop: {exc}")

    def _hook_loop(self) -> None:
        """Hidden message window + RegisterShellHookWindow for HSHELL_FLASH."""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        LRESULT = ctypes.c_ssize_t
        WPARAM = ctypes.c_size_t
        LPARAM = ctypes.c_ssize_t
        WNDPROC = ctypes.WINFUNCTYPE(
            LRESULT, wintypes.HWND, wintypes.UINT, WPARAM, LPARAM
        )
        shell_msg = user32.RegisterWindowMessageW("SHELLHOOK")
        user32.DefWindowProcW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            WPARAM,
            LPARAM,
        ]
        user32.DefWindowProcW.restype = LRESULT

        @WNDPROC
        def wndproc(hwnd, msg, wparam, lparam):  # noqa: ANN001
            if msg == shell_msg and int(wparam) == HSHELL_FLASH:
                try:
                    self._on_flash(int(lparam))
                except Exception as exc:  # noqa: BLE001
                    self._log(f"[warn] alert flash: {exc}")
                return 0
            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        # Keep callback alive for window lifetime
        self._wndproc_ref = wndproc

        class WNDCLASS(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        hinst = kernel32.GetModuleHandleW(None)
        class_name = "JarvisAlertShellHook"
        wc = WNDCLASS()
        wc.style = 0
        wc.lpfnWndProc = wndproc
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = hinst
        wc.hIcon = None
        wc.hCursor = None
        wc.hbrBackground = None
        wc.lpszMenuName = None
        wc.lpszClassName = class_name
        atom = user32.RegisterClassW(ctypes.byref(wc))
        if not atom:
            err = kernel32.GetLastError()
            if err not in (0, 1410):  # ERROR_CLASS_ALREADY_EXISTS
                self._log(f"[warn] alert RegisterClass: {err}")

        # Hidden top-level window (message-only HWND_MESSAGE is flaky via ctypes)
        hwnd = user32.CreateWindowExW(
            0,
            class_name,
            "JarvisAlertHook",
            0x80000000,  # WS_POPUP
            0,
            0,
            0,
            0,
            None,
            None,
            hinst,
            None,
        )
        if not hwnd:
            self._log(f"[fail] alert CreateWindow: {kernel32.GetLastError()}")
            return
        self._hwnd = int(hwnd)
        if not user32.RegisterShellHookWindow(hwnd):
            self._log(f"[fail] RegisterShellHookWindow: {kernel32.GetLastError()}")
            user32.DestroyWindow(hwnd)
            self._hwnd = None
            return
        self._log("[ok] ShellHook FLASH 監聽中")

        msg = wintypes.MSG()
        while not self._stop.is_set():
            ret = user32.MsgWaitForMultipleObjects(0, None, False, 200, 0x4FF)
            while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
                if msg.message == WM_QUIT:
                    self._stop.set()
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            if ret == 0xFFFFFFFF:
                break

        try:
            user32.DeregisterShellHookWindow(hwnd)
        except Exception:
            pass
        try:
            user32.DestroyWindow(hwnd)
        except Exception:
            pass
        self._hwnd = None

    def _poll_loop(self) -> None:
        from jarvis.hands import _pids_for_images

        while not self._stop.is_set():
            try:
                if self._enabled:
                    if self._discord:
                        self._tick_discord(_pids_for_images)
                    if self._cursor:
                        self._tick_cursor(_pids_for_images)
            except Exception as exc:  # noqa: BLE001
                self._log(f"[warn] alert poll: {exc}")
            self._stop.wait(_POLL_S)

    def _tick_discord(self, pids_fn) -> None:
        pids = set()
        for name in ("Discord.exe", "DiscordPTB.exe", "DiscordCanary.exe"):
            pids |= pids_fn([name])
        titles = _list_windows_for_pids(pids) if pids else []
        title_n = discord_unread_count(titles)
        tb_names = _discord_taskbar_names_uia()
        n = _discord_unread_best(title_n=title_n, tb_names=tb_names)
        if self._discord_prev is None:
            self._discord_prev = n
            return
        if n > self._discord_prev:
            detail = f"unread {self._discord_prev}→{n}"
            if tb_names:
                detail += " taskbar " + (tb_names[0][:60])
            else:
                detail = f"title {detail}"
            self._emit(
                AlertEvent(
                    kind="discord",
                    phrase=alert_phrase_for("discord"),
                    detail=detail,
                )
            )
        self._discord_prev = n

    def _tick_cursor(self, pids_fn) -> None:
        pids = pids_fn(["Cursor.exe"])
        if not pids:
            self._cursor_was_busy = False
            self._cursor_busy_since = 0.0
            self._cursor_idle_since = 0.0
            self._cursor_alerted_for_cycle = False
            self._cursor_attention_latched = False
            self._cursor_attention_gone_since = 0.0
            return
        # Exact UIA wait card (plan / ask) — always when Cursor on.
        # Full toast/title/flash only when alert_cursor_watch.
        now = time.monotonic()
        if self._cursor:
            hit, detail = _cursor_uia_waiting_approval(pids)
            if hit:
                self._cursor_attention_gone_since = 0.0
                if not self._cursor_attention_latched:
                    self._cursor_attention_latched = True
                    try:
                        from jarvis.cursor_hooks import mark_waiting

                        mark_waiting()
                    except Exception:
                        pass
                    phrase = (
                        alert_phrase_for("cursor_plan")
                        if "plan" in (detail or "").lower()
                        else alert_phrase_for("cursor_approve")
                    )
                    self._emit(
                        AlertEvent(
                            kind="cursor",
                            phrase=phrase,
                            detail=detail or "uia approval",
                        )
                    )
            elif self._cursor_attention_latched:
                if self._cursor_attention_gone_since <= 0:
                    self._cursor_attention_gone_since = now
                elif now - self._cursor_attention_gone_since >= _CURSOR_ATTENTION_CLEAR_S:
                    self._cursor_attention_latched = False
                    self._cursor_attention_gone_since = 0.0
            else:
                self._cursor_attention_gone_since = 0.0
        if not (self._cursor and self._cursor_watch):
            return
        titles = _list_windows_for_pids(pids)
        busy = cursor_titles_busy(titles)
        if busy:
            if self._cursor_busy_since <= 0:
                self._cursor_busy_since = now
            elif now - self._cursor_busy_since >= _CURSOR_BUSY_HOLD_S:
                # Sustained busy only — one-poll flicker must not arm "done".
                self._cursor_was_busy = True
            self._cursor_idle_since = 0.0
            self._cursor_alerted_for_cycle = False
            return
        self._cursor_busy_since = 0.0
        if not self._cursor_was_busy:
            return
        if self._cursor_idle_since <= 0:
            self._cursor_idle_since = now
            return
        if now - self._cursor_idle_since < _CURSOR_IDLE_HOLD_S:
            return
        if self._cursor_alerted_for_cycle:
            return
        self._cursor_alerted_for_cycle = True
        self._cursor_was_busy = False
        self._emit(
            AlertEvent(
                kind="cursor",
                phrase="Cursor finished its work.",
                detail="title busy→idle",
            )
        )
