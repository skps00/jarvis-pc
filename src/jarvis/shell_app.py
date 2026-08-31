"""System tray + companion panel + hotkey + settings.

Hermes owns chat/voice. This shell = desktop alerts eyes + Approve companion.
"""

from __future__ import annotations

import queue
import re
import sys
import threading
import time
import tkinter as tk
from typing import Any
from tkinter import messagebox, scrolledtext, ttk

from jarvis.engine import RunResult, execute_utterance
from jarvis.settings import Settings, hotkey_display, load_settings
# NOTE: jarvis.settings_ui (tkinter SettingsWindow) FROZEN 2026-08-31 (#12):
# settings live in Electron settings.html. File kept for tests/rollback.

# Windows single-instance (ctypes — no extra dep)
_MUTEX_NAME = "Local\\JarvisPcServe.v1"
_SHOW_EVENT_NAME = "Local\\JarvisPcServe.Show.v1"
_ERROR_ALREADY_EXISTS = 183
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 258


def _win_kernel32():
    import ctypes

    return ctypes.windll.kernel32


def _stop_alert_poller_processes(*, keep_pid: int | None = None) -> int:
    """Kill orphan ``hermes_alert_poll_loop`` processes. Returns count stopped."""
    if sys.platform != "win32":
        return 0
    import os
    import subprocess

    me = os.getpid()
    keep = {me}
    if keep_pid is not None:
        keep.add(int(keep_pid))
    flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    # CIM is more reliable than wmic on current Windows.
    ps = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.CommandLine -match 'hermes_alert_poll_loop' } | "
        "Select-Object -ExpandProperty ProcessId"
    )
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
        )
    except (OSError, subprocess.CalledProcessError):
        return 0
    killed = 0
    for line in out.splitlines():
        line = line.strip()
        if not line.isdigit():
            continue
        pid = int(line)
        if pid in keep:
            continue
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
                creationflags=flags,
            )
            killed += 1
        except OSError:
            continue
    return killed


def _signal_existing_show() -> bool:
    """Pulse show-event so the running instance deiconifies. True if signaled."""
    import sys

    if sys.platform != "win32":
        return False
    k32 = _win_kernel32()
    # EVENT_MODIFY_STATE
    h = k32.OpenEventW(0x0002, False, _SHOW_EVENT_NAME)
    if not h:
        return False
    try:
        k32.SetEvent(h)
        return True
    finally:
        k32.CloseHandle(h)


def acquire_serve_lock(*, wait_sec: float = 0.0) -> list | None:
    """
    Acquire single-instance mutex (+ create show event).

    Returns mutable ``[mutex_handle, show_event_handle]`` or None if another
    instance owns it after waiting ``wait_sec`` (used by restart child).
    """
    import sys
    import time

    if sys.platform != "win32":
        return [None, None]  # no lock on non-Windows

    k32 = _win_kernel32()
    deadline = time.monotonic() + max(0.0, wait_sec)
    while True:
        mutex = k32.CreateMutexW(None, False, _MUTEX_NAME)
        if not mutex:
            return None
        already = k32.GetLastError() == _ERROR_ALREADY_EXISTS
        if not already:
            show_ev = k32.CreateEventW(None, False, False, _SHOW_EVENT_NAME)
            return [mutex, show_ev]
        k32.CloseHandle(mutex)
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.2)


def release_serve_lock(lock: list | None) -> None:
    """Close mutex / show-event handles (idempotent)."""
    import sys

    if not lock or sys.platform != "win32":
        return
    k32 = _win_kernel32()
    for i, h in enumerate(lock):
        if h:
            try:
                k32.CloseHandle(h)
            except Exception:
                pass
            lock[i] = None


def _pick_spoken_line(lines: list[str]) -> str | None:
    """Pick the line worth speaking aloud (speak/ok/fail), tag stripped.

    Prefer ``[speak]`` (Hermes short English). Do **not** use ``[caption]``
    (often CJK — mouth would skip). Debug lines stay in the log only.
    """
    import re

    speak: str | None = None
    ok_fail: str | None = None
    for line in lines:
        m = re.match(r"^\[speak\]\s*(.*)$", line)
        if m and m.group(1).strip():
            speak = m.group(1).strip()
            continue
        m = re.match(r"^\[(?:ok|fail)\]\s*(.*)$", line)
        if m and m.group(1).strip():
            ok_fail = m.group(1).strip()
    return speak or ok_fail


def _make_icon_image(*, recording: bool = False):
    """Tiny circle icon for the tray (blue=idle; recording unused after ASR removal)."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fill = (200, 40, 40, 255) if recording else (30, 90, 180, 255)
    inner = (255, 200, 200, 255) if recording else (200, 230, 255, 255)
    draw.ellipse((4, 4, 60, 60), fill=fill)
    draw.ellipse((22, 22, 42, 42), fill=inner)
    return img



_MAGE_VISION_RE = re.compile(
    r"(睇圖|看圖)[\s:：]*(.+\.(?:png|jpg|jpeg|webp))",
    re.IGNORECASE,
)


def _try_mage_vision_command(text: str) -> RunResult | None:
    """Handle 睇圖/看圖 <path> when mage_enabled; else None."""
    cfg = load_settings()
    if not getattr(cfg, "mage_enabled", False):
        return None
    m = _MAGE_VISION_RE.search((text or "").strip())
    if not m:
        return None
    path = m.group(2).strip().strip("\"'")
    prompt = (
        getattr(cfg, "mage_prompt_default", None)
        or "Describe this image in detail."
    )
    try:
        from jarvis.mage_engine import get_mage_engine

        answer = get_mage_engine().understand_image(path, prompt=prompt)
        return RunResult(True, [f"[mage] {path}", answer])
    except Exception as exc:  # noqa: BLE001
        return RunResult(False, [f"Mage vision error: {exc}"])


def _strip_wake_word(text: str) -> str:
    """Remove leading wake phrase from STT output."""
    import re

    t0 = text.strip()
    patterns = [
        r"^(hey\s+)?jarvis[\s,.!？?，、。]*",
        r"^(hey\s+)?javis[\s,.!？?，、。]*",
        r"^(hey\s+)?jarvi[\s,.!？?，、。]*",
        r"^(hey\s+)?drivers[\s,.!？?，、。]*",
        r"^(hey\s+)?draaws[\s,.!？?，、。]*",
        r"^賈維斯[\s,.!？?，、。]*",
        r"^贾维斯[\s,.!？?，、。]*",
    ]
    for pat in patterns:
        m = re.match(pat, t0, re.IGNORECASE)
        if m:
            return t0[m.end() :].strip()
    return t0


def _resolve_input_device(dev: int | str | None) -> int | None:
    """wake_mic_device 可以係 int（舊格式）或 str（裝置名）。str → 而家嘅 index。

    Windows sounddevice 同一個 mic 有多個變體（44.1k/48k），48k 開唔到 16k
    stream —— resolve_mic_name 會揀 44.1kHz entry。
    """
    if isinstance(dev, str) and dev:
        try:
            from jarvis.wake import resolve_mic_name

            return resolve_mic_name(dev)
        except Exception:
            return None
    return dev


class JarvisShell:
    """Companion panel + tray; hotkey shows the panel."""

    def __init__(self, *, instance_lock: list | None = None) -> None:
        import os

        # Phase 8.2: Electron Companion replaces tkinter panel — headless serve only.
        self._headless = os.environ.get("JARVIS_ELECTRON_HOST") == "1"
        self._headless_stop = threading.Event()

        self._instance_lock = instance_lock
        self._ui_queue: queue.Queue = queue.Queue()
        self._tray = None
        self._hotkey_listener = None
        self._busy = False
        self._hermes_trusted_until = 0.0  # monotonic; 0 = Safe
        self._settings_win = None  # tkinter SettingsWindow FROZEN (#12)
        self._show_watch_stop = threading.Event()
        self._pending_image: str | None = None
        self._wake_stop = threading.Event()
        self._wake_pause = threading.Event()
        self._wake_thread: threading.Thread | None = None
        self._wake_on = False
        self._last_wake_ts = 0.0
        self._tts_holding_pause = False
        # Voice call gate（sk_activity.json `voice_call` → mute 被動出聲 + pause wake）
        self._voice_call_mute = False
        self._aec_active = False
        self._vc_gate_stop = threading.Event()
        self._game_watch_stop = threading.Event()
        self._game_watch_thread: threading.Thread | None = None
        self._settings_apply_thread: threading.Thread | None = None
        cfg = load_settings()
        self._wake_cd = float(cfg.wake_cd_seconds)
        self._wake_threshold = float(cfg.wake_threshold)
        self._wake_mic_device: int | None = cfg.wake_mic_device
        self._text_wake = bool(getattr(cfg, "text_wake", False))
        self._hotkey = cfg.hotkey
        self._alert_watcher = None
        self._alert_speaking = False
        self._alert_poller = None
        self._self_monitor_thread: threading.Thread | None = None
        self._status_text = "就緒"

        if self._headless:
            self.root = None
            self.status = None
            self.hint = None
            self.strip = None
            self.entry = None
            self.btn_send = None
            self.btn_wake = None
            self.img_status = None
            self.log = None
            return

        self.root = tk.Tk()
        self.root.title("JARVIS · companion")
        self.root.geometry("480x420+80+80")
        self.root.attributes("-topmost", True)
        # ponytail: withdraw until hotkey — reduces focus steal when idle
        self.root.withdraw()

        frm = tk.Frame(self.root, padx=10, pady=10)
        frm.pack(fill=tk.BOTH, expand=True)

        self.status = tk.Label(
            frm,
            text="● 就緒",
            anchor="w",
            fg="#1a5fb4",
            font=("Segoe UI", 11, "bold"),
        )
        self.status.pack(fill=tk.X, pady=(0, 2))

        self.hint = tk.Label(
            frm,
            text=(
                "companion — Hermes 對話；呢度只係桌面提醒眼睛 · "
                f"{hotkey_display(self._hotkey)} 顯示／隱藏"
            ),
            anchor="w",
            fg="#555",
            font=("Segoe UI", 9),
            wraplength=440,
            justify="left",
        )
        self.hint.pack(fill=tk.X, pady=(0, 4))

        self.strip = tk.Label(
            frm,
            text="MCP · · ·  |  poller · · ·  |  tts · · ·",
            anchor="w",
            fg="#333",
            font=("Consolas", 9),
        )
        self.strip.pack(fill=tk.X, pady=(0, 6))

        # Legacy hooks kept for wake/submit code paths (not packed).
        self.entry = None
        self.btn_send = None
        self.btn_wake = None
        self.img_status = None

        self.log = scrolledtext.ScrolledText(
            frm, height=12, state=tk.DISABLED, font=("Segoe UI", 9)
        )
        self.log.pack(fill=tk.BOTH, expand=True)

        btn_row = tk.Frame(frm)
        btn_row.pack(fill=tk.X, pady=(8, 0))
        tk.Button(btn_row, text="試語音提醒", command=self.test_alert).pack(
            side=tk.LEFT
        )
        tk.Button(btn_row, text="Hermes 網頁", command=self.open_hermes_dashboard).pack(
            side=tk.LEFT, padx=6
        )
        tk.Button(btn_row, text="設定", command=self.open_settings).pack(
            side=tk.LEFT, padx=6
        )
        tk.Button(btn_row, text="隱藏", command=self.hide).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_row, text="重啟", command=self.restart_app).pack(
            side=tk.RIGHT, padx=6
        )
        tk.Button(btn_row, text="結束", command=self.quit_app).pack(side=tk.RIGHT)

        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.after(100, self._drain_queue)
        self.root.after(800, self._refresh_status_strip)

    def apply_settings(self, s: Settings, *, restart_wake: bool = False) -> None:
        """Apply runtime knobs from Settings (after save)."""
        from jarvis.settings import uses_hermes_voice_frontend

        if not s.hermes_enabled:
            # only tears down if currently Trusted（免每次儲存打 WSL）
            self.clear_hermes_trusted()
        was_wake = bool(self._wake_on)
        self._wake_cd = float(s.wake_cd_seconds)
        self._wake_threshold = float(s.wake_threshold)
        self._wake_mic_device = s.wake_mic_device
        self._text_wake = bool(getattr(s, "text_wake", False))
        hermes_note = "Hermes=on" if s.hermes_enabled else "Hermes=off"
        vf = getattr(s, "voice_frontend", "hermes")
        att = getattr(s, "alert_tts", "hermes")
        self.append_log(
            f"[ok] 已套用：{hermes_note} voice={vf} alert_tts={att} "
            f"熱鍵={hotkey_display(s.hotkey)}"
        )
        if s.hotkey != self._hotkey:
            self._hotkey = s.hotkey
            if not self._headless and self.hint is not None:
                self.hint.configure(
                    text=(
                        "companion — Hermes 對話；呢度只係桌面提醒眼睛 · "
                        f"{hotkey_display(self._hotkey)} 顯示／隱藏"
                    )
                )
            self.restart_hotkey()
        self._refresh_status_strip()
        # Hermes voice frontend → never keep Jarvis OWW (mic fight)
        if uses_hermes_voice_frontend(s):
            if was_wake:
                self.stop_wake()
                self.append_log(
                    "[ok] 語音前端=Hermes → 已關 Jarvis 聽候（避免搶咪）"
                )
        elif restart_wake and was_wake:
            self.stop_wake()
            if self._wake_thread is not None and self._wake_thread.is_alive():
                self.append_log("[warn] 聽候線程未停清；請稍後再開")
            else:
                self.start_wake()
                if self._busy or getattr(self, "_tts_holding_pause", False):
                    self._wake_pause.set()

        self._apply_alert_settings(s)

    def _apply_alert_settings(self, s: Settings | None = None) -> None:
        """Start/update Discord／Cursor voice alert watcher from settings."""
        from jarvis.alerts import AlertWatcher

        cfg = s if s is not None else load_settings()
        if self._alert_watcher is None:
            self._alert_watcher = AlertWatcher(
                on_event=self._on_alert_event,
                on_log=lambda m: self._ui_queue.put(("log", m)),
            )
            self._alert_watcher.start()
        self._alert_watcher.configure(
            enabled=bool(getattr(cfg, "alert_voice", True)),
            discord=bool(getattr(cfg, "alert_discord", True)),
            cursor=bool(getattr(cfg, "alert_cursor", True)),
            cursor_hooks=bool(getattr(cfg, "alert_cursor_hooks", True)),
            cursor_toast=bool(getattr(cfg, "alert_cursor_toast", True)),
            cursor_uia=bool(getattr(cfg, "alert_cursor_uia", True)),
            cursor_watch=bool(getattr(cfg, "alert_cursor_watch", False)),
            whatsapp=bool(getattr(cfg, "alert_whatsapp", True)),
            always=bool(getattr(cfg, "alert_always", True)),
            extra=str(getattr(cfg, "alert_extra", "") or ""),
            cd_seconds=float(getattr(cfg, "alert_cd_seconds", 0.0)),
            gpu_health=bool(getattr(cfg, "alert_gpu_health", True)),
            gpu_poll_s=float(getattr(cfg, "alert_gpu_poll_s", 5.0)),
        )
        try:
            from jarvis.cursor_hooks import is_installed as _hooks_on

            if (
                getattr(cfg, "alert_cursor", True)
                and getattr(cfg, "alert_cursor_hooks", True)
                and not _hooks_on()
            ):
                self._ui_queue.put(
                    (
                        "log",
                        "[warn] Cursor hooks 已勾但未裝 → python -m jarvis cursor-hooks install",
                    )
                )
        except Exception:
            pass
        self._ensure_alerts_mcp(cfg)

    def _on_alert_event(self, ev) -> None:
        """Background alert → UI queue (speak on Tk drain)."""
        self._ui_queue.put(("alert", ev))

    def _ensure_alerts_mcp(self, cfg: Settings) -> None:
        """Start loopback HTTP alerts MCP + ~2s Hermes TTS poller when hermes sink on."""
        if not bool(getattr(cfg, "alert_voice", True)):
            return
        if str(getattr(cfg, "alert_tts", "hermes") or "").lower() != "hermes":
            return
        try:
            from jarvis.mcp_alerts_http import resolve_token, serve_in_thread

            port = int(getattr(cfg, "alerts_mcp_port", 8765) or 8765)
            tok = resolve_token(str(getattr(cfg, "alerts_mcp_token", "") or "") or None)
            serve_in_thread(host="127.0.0.1", port=port, token=tok)
            self._ui_queue.put(
                (
                    "log",
                    f"[ok] alerts MCP http://127.0.0.1:{port}/mcp（Hermes peek）",
                )
            )
        except Exception as exc:  # noqa: BLE001
            self._ui_queue.put(("log", f"[fail] alerts MCP：{exc}"))
        self._ensure_alert_poller()

    def _ensure_alert_poller(self) -> None:
        """Background ~2s peek→TTS→ack (cron alone is ≥1m)."""
        if getattr(self, "_alert_poller", None) is not None:
            return
        import os
        import subprocess
        from pathlib import Path

        from jarvis.autostart import _pythonw

        script = Path(__file__).resolve().parents[2] / "scripts" / "hermes_alert_poll_loop.py"
        if not script.is_file():
            self._ui_queue.put(("log", f"[warn] 無 poller：{script}"))
            return
        # Orphan pollers (restart / Cursor) each flash console on speak.
        killed = _stop_alert_poller_processes()
        if killed:
            self._ui_queue.put(("log", f"[ok] 清舊 alert poller ×{killed}"))
        try:
            # pythonw + CREATE_NO_WINDOW: hidden console for any console child
            flags = 0
            if sys.platform == "win32":
                flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self._alert_poller = subprocess.Popen(
                [str(_pythonw()), str(script)],
                cwd=str(script.parent.parent),
                env={
                    **dict(os.environ),
                    "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
                    "JARVIS_ALERT_POLL_S": "1",
                },
                creationflags=flags,
            )
            self._ui_queue.put(("log", "[ok] alert poller ~2s（Jarvis Piper）"))
        except Exception as exc:  # noqa: BLE001
            self._ui_queue.put(("log", f"[fail] alert poller：{exc}"))

    def _enqueue_alert(self, kind: str, phrase: str, *, app: str = "", log_prefix: str = "alert") -> None:
        """Enqueue an alert phrase into the store (poller will speak it)."""
        try:
            from jarvis.alert_store import AlertStore
            AlertStore().enqueue(kind=kind, phrase=phrase, app=app)
            self._ui_queue.put(("log", f"[ok] {log_prefix}: {phrase[:80]}"))
        except Exception as exc:  # noqa: BLE001
            self._ui_queue.put(("log", f"[fail] {log_prefix}: {exc}"))

    def _ensure_self_monitor(self) -> None:
        """Daily self-monitor (wake/serve stats + threshold auto-tune) in-app.

        Replaces the old Hermes cron ``jarvis-self-monitor`` (2026-08-29):
        run once ~10min after serve start (catch-up), then daily at 09:00.
        Notable findings → alert store → alert poller speaks them.
        """
        if getattr(self, "_self_monitor_thread", None) is not None:
            return

        def _run() -> None:
            def _one_pass() -> None:
                try:
                    from jarvis.self_monitor import run_once

                    summary, notable = run_once()
                    if not notable:
                        return
                    self._enqueue_alert(
                        "self-monitor", summary, log_prefix="self-monitor notable"
                    )
                except Exception as exc:  # noqa: BLE001
                    self._ui_queue.put(("log", f"[fail] self-monitor: {exc}"))

            # Catch-up shortly after serve start (log tail has data by then).
            time.sleep(600)
            _one_pass()
            while True:
                now = time.localtime()
                nxt = time.mktime(
                    (now.tm_year, now.tm_mon, now.tm_mday, 9, 0, 0, 0, 0, -1)
                )
                if nxt <= time.time():
                    nxt += 86400
                time.sleep(max(60.0, nxt - time.time()))
                _one_pass()

        try:
            t = threading.Thread(target=_run, daemon=True, name="jarvis-self-monitor")
            t.start()
            self._self_monitor_thread = t
            self._ui_queue.put(("log", "[ok] self-monitor daily 09:00（in-app）"))
        except Exception as exc:  # noqa: BLE001
            self._ui_queue.put(("log", f"[fail] self-monitor 啟動失敗：{exc}"))

    def arm_hermes_trusted(self, *, minutes: float = 30.0) -> None:
        """G3: Trusted window → enable docker terminal; expires → Safe."""
        import time as _time

        mins = max(1.0, float(minutes))
        self.append_log(f"[ok] 開 Trusted（docker terminal，{mins:g} 分鐘）…")

        def work() -> None:
            from jarvis.hermes_bridge import (
                apply_hermes_trusted_toolsets,
                recycle_api_server,
            )

            ok, msg = apply_hermes_trusted_toolsets()
            if not ok:
                self._ui_queue.put(("log", f"[fail] Trusted 開唔到：{msg}"))
                return
            self._ui_queue.put(("log", f"[ok] {msg}"))
            ok2, msg2 = recycle_api_server()
            if not ok2:
                self._ui_queue.put(("log", f"[warn] API 重載：{msg2}"))
            else:
                self._ui_queue.put(("log", "[ok] API 已重載（Trusted toolsets）"))
            self._hermes_trusted_until = _time.monotonic() + mins * 60.0
            self._ui_queue.put(
                ("log", f"[ok] Hermes Trusted {mins:g} 分鐘（之後回 Safe）")
            )

        threading.Thread(target=work, daemon=True).start()

    def clear_hermes_trusted(self) -> None:
        """Force Safe if currently Trusted；no-op when already Safe."""
        was = self._hermes_trusted_until > 0
        if not was:
            return
        self._hermes_trusted_until = 0.0
        self.append_log("[ok] 回 Safe（關 docker terminal）…")

        def work() -> None:
            from jarvis.hermes_bridge import (
                apply_hermes_safe_toolsets,
                recycle_api_server,
            )

            ok, msg = apply_hermes_safe_toolsets()
            if not ok:
                self._ui_queue.put(("log", f"[warn] Safe toolsets：{msg}"))
            else:
                self._ui_queue.put(("log", f"[ok] 已回 Safe（{msg}）"))
            ok2, msg2 = recycle_api_server()
            if not ok2:
                self._ui_queue.put(("log", f"[warn] API 重載：{msg2}"))

        threading.Thread(target=work, daemon=True).start()

    def hermes_is_trusted(self) -> bool:
        """True while within Trusted window; auto-expire → Safe toolsets."""
        import time as _time

        if self._hermes_trusted_until <= 0:
            return False
        if _time.monotonic() >= self._hermes_trusted_until:
            self.append_log("[ok] Trusted 到期 → Safe")
            self.clear_hermes_trusted()
            return False
        return True


    def _toggle_wake(self) -> None:
        """UI toggle for Jarvis listen (OWW → VAD → STT)."""
        if self._wake_on:
            self.stop_wake()
        else:
            self.start_wake()

    def start_wake(self) -> None:
        """Background OWW wake loop."""
        from jarvis.settings import load_settings, uses_hermes_voice_frontend
        from jarvis.wake import (
            has_custom_jarvis_model,
            run_wake_loop,
            wake_available,
        )

        if uses_hermes_voice_frontend(load_settings()):
            self.append_log(
                "[warn] 語音前端=Hermes — Jarvis 聽候已禁；改用 Hermes wake／"
                "docs/hermes_voice_smoke.md；要本機 OWW 請設定改「Jarvis」"
            )
            self._set_wake_btn("聽候：關")
            self._write_voice_status()
            return
        if self._wake_thread and self._wake_thread.is_alive():
            return
        if not wake_available():
            self.append_log('[warn] 聽候依賴未裝：pip install "jarvis-pc[wake]"')
            self._set_wake_btn("聽候：關")
            self._write_voice_status()
            return
        self._wake_stop.clear()
        self._wake_pause.clear()
        self._wake_on = True
        self._set_wake_btn("聽候：開")
        self._write_voice_status()
        thr = max(0.25, min(0.99, float(self._wake_threshold)))
        cd = float(self._wake_cd)
        mode = "hey+custom" if has_custom_jarvis_model() else "hey_jarvis"
        text_wake = bool(self._text_wake)

        def on_detect() -> None:
            # Hold mic until UI handles / rejects（唔等 drain 先 pause）
            self._wake_pause.set()
            self._ui_queue.put(("wake", None))

        def on_command(pcm_array: Any) -> None:
            self._wake_pause.set()
            self._ui_queue.put(("wake_cmd", pcm_array))

        def work() -> None:
            aec_proc = None
            loopback = None
            aec_chain = None
            try:
                from jarvis.settings import load_settings as _ls2

                _s = _ls2()
                if getattr(_s, "aec_enabled", False):
                    from jarvis import aec as aec_mod

                    if aec_mod.available():
                        ref_names: list[str] = []
                        _cfg_ref = getattr(_s, "aec_reference_device", "") or ""
                        if _cfg_ref:
                            ref_names.append(_cfg_ref)
                        _tout = getattr(_s, "tts_output_device", None) or ""
                        if _tout:
                            if isinstance(_tout, int):
                                try:
                                    import sounddevice as sd

                                    _tout = sd.query_devices(_tout)["name"]
                                except Exception:
                                    _tout = ""
                            if _tout and str(_tout) not in ref_names:
                                ref_names.append(str(_tout))
                        # Arctis loopback excluded: sidetone/leakage puts the
                        # user's own voice into the reference → AEC cancels wake
                        # word (~0.33→~0.24). TTS echo already handled by Phase 2.
                        for _extra in ("SteelSeries Sonar - Chat",):
                            if _extra not in ref_names:
                                ref_names.append(_extra)
                        pairs: list[tuple[Any, Any]] = []
                        active_names: list[str] = []
                        for name in ref_names:
                            dev = aec_mod.find_loopback_for_output(name)
                            if dev is None:
                                continue
                            lb = aec_mod.LoopbackCapture(dev[0])
                            if not lb.start():
                                continue
                            frame = lb.get_chunk(1280, timeout=0.5)
                            if frame is None:
                                try:
                                    lb.stop()
                                except Exception:
                                    pass
                                continue
                            pairs.append((lb, aec_mod.AecProcessor()))
                            active_names.append(name)
                        if pairs:
                            aec_chain = aec_mod.AecChain(pairs)
                            self._aec_active = True
                            self._ui_queue.put(
                                (
                                    "log",
                                    f"[ok] AEC on: refs=[{', '.join(active_names)}]",
                                )
                            )
                    else:
                        self._ui_queue.put(
                            ("log", "[warn] aec_enabled 但 pyaec 未裝")
                        )
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[warn] AEC init fail：{exc}"))
                aec_proc = None
                loopback = None
                aec_chain = None
            try:
                self._ui_queue.put(
                    (
                        "log",
                        f"[ok] 聽候 Jarvis（{mode}）thr={thr} CD={cd}s "
                        f"text_wake={text_wake} aec={'on' if aec_chain else 'off'}",
                    )
                )
                run_wake_loop(
                    on_detect,
                    on_command=on_command,
                    threshold=thr,
                    post_resume_s=cd,
                    stop_event=self._wake_stop,
                    pause_event=self._wake_pause,
                    text_wake=text_wake,
                    input_device=_resolve_input_device(self._wake_mic_device),
                    aec_processor=None,
                    loopback=None,
                    aec_chain=aec_chain,
                )
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] 聽候：{exc}"))
                self._ui_queue.put(("wake_off", None))
            finally:
                if aec_chain is not None:
                    try:
                        aec_chain.stop()
                    except Exception:
                        pass

        self._wake_thread = threading.Thread(
            target=work, daemon=True, name="jarvis-wake"
        )
        self._wake_thread.start()
        self._write_voice_status()

    def stop_wake(self, *, join_timeout: float = 2.5) -> None:
        """Stop wake loop, join thread, release mic."""
        self._wake_on = False
        self._wake_stop.set()
        self._wake_pause.set()
        th = self._wake_thread
        if th is not None and th.is_alive() and th is not threading.current_thread():
            th.join(timeout=join_timeout)
        if th is not None and th.is_alive():
            self.append_log("[warn] 聽候線程未完全停下")
        elif th is not None:
            self._wake_thread = None
        self._set_wake_btn("聽候：關")
        self.append_log("[ok] 聽候已關")
        self._write_voice_status()

    def _on_listen_cmd(self, pcm_array: Any) -> None:
        """Transcribe pre-captured PCM from wake → execute."""
        if self._busy:
            return
        # Guard empty capture (SenseVoice window-size-0 crash path)
        try:
            n = int(getattr(pcm_array, "size", 0) or 0)
        except Exception:
            n = 0
        if n < 1600:  # <0.1s @ 16kHz
            self.append_log("[fail] 指令音頻太短／空白")
            self.set_status("● 識別失敗", kind="fail")
            self._wake_pause.clear()
            return
        self._set_busy(True)
        # D2: capture 完成即刻唸「Yes, Sir.」——俾 SK 即時知道「聽到喇、講完喇」開始處理
        # （唔等 STT，因為 STT 首次 load 要幾秒；Yes Sir 先唸 = 即時回饋）
        try:
            from jarvis.settings import load_settings as _ls

            _cfg = _ls()
            if (
                _cfg.tts_enabled
                and getattr(_cfg, "tts_ack", True)
                and not self._voice_call_mute
            ):
                from jarvis.mouth import available as _tts_avail
                from jarvis.mouth import speak as _tts_speak

                if _tts_avail():
                    threading.Thread(
                        target=lambda: _tts_speak("Yes, Sir."),
                        daemon=True,
                    ).start()
        except Exception:
            pass
        self.set_status("● 語音識別中…", kind="busy")

        def work() -> None:
            path = None
            try:
                from jarvis.config import load_registry
                from jarvis.ear import pcm_to_wav, transcribe_path
                from jarvis.settings import load_settings, uses_cloud_asr

                cfg = load_settings()
                path = pcm_to_wav(pcm_array)
                dur = (
                    float(pcm_array.size) / 16000.0
                    if hasattr(pcm_array, "size")
                    else 0.0
                )
                self._ui_queue.put(("log", f"[ear] 指令音頻 {dur:.1f}s"))
                status_msg = (
                    f"● 雲端 ASR（{cfg.asr_model}）…"
                    if uses_cloud_asr(cfg)
                    else f"● 本機 ASR（{cfg.asr_provider}）…"
                )
                self._ui_queue.put(("status", (status_msg, "busy")))
                self._ui_queue.put(
                    ("log", f"[ear] 開始 ASR（{cfg.asr_provider}）…")
                )
                if cfg.asr_provider == "fun_asr":
                    self._ui_queue.put(
                        (
                            "log",
                            "[ear] Fun-ASR 首次下載／載入可能要幾分鐘；"
                            "卡住請改設定→SenseVoice 後重啟",
                        )
                    )
                registry = load_registry()
                hot: list[str] = []
                for pr in registry.profiles.values():
                    hot.extend(pr.names)
                    hot.extend(pr.locale_hints)
                text = transcribe_path(path, language="yue", hotwords=hot)
                self._ui_queue.put(
                    ("log", f"[ear] raw={text!r} ({cfg.asr_provider})")
                )
                if not text.strip():
                    self._ui_queue.put(("log", "[fail] 聽唔到指令"))
                    self._ui_queue.put(("status", ("● 識別失敗", "fail")))
                    return
                clean = _strip_wake_word(text.strip())
                if clean != text.strip():
                    self._ui_queue.put(("log", f"[ear] stripped → {clean!r}"))
                if not clean.strip():
                    self._ui_queue.put(("log", "[fail] 淨係 wake 詞"))
                    self._ui_queue.put(("status", ("● 無指令", "fail")))
                    return
                self._ui_queue.put(("log", f"> {clean}"))
                self._ui_queue.put(("status", ("● 執行指令中…", "busy")))
                result = _try_mage_vision_command(clean.strip())
                if result is None:
                    result = execute_utterance(
                        clean.strip(),
                        ask_confirm=self._ask_confirm_threadsafe,
                        repair_asr=True,
                    )
                self._ui_queue.put(("result", result.lines))
                self._ui_queue.put(
                    (
                        "status",
                        (
                            "● 就緒" if result.ok else "● 失敗（見日誌）",
                            "ok" if result.ok else "fail",
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] 語音指令：{exc}"))
                self._ui_queue.put(("status", ("● 失敗（見日誌）", "fail")))
            finally:
                if path is not None:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
                self._ui_queue.put(("busy", False))

        threading.Thread(target=work, daemon=True).start()

    def open_settings(self) -> None:
        """Open settings. tkinter SettingsWindow is FROZEN (2026-08-31 #12):
        settings now live in Electron settings.html (JARVIS ONE tray → 設定).
        Keep the entry point as a no-op log so old callers don't crash."""
        self.append_log("[ok] 設定由 Electron HUD 管（JARVIS ONE tray → 設定）")

    def open_hermes_dashboard(self) -> None:
        """Start/open Hermes web UI in browser (background; no WSL flash)."""
        self.append_log("[ok] 開 Hermes 網頁…")
        self.set_status("● 開 Hermes 網頁…", kind="busy")

        def work() -> None:
            from jarvis.hermes_bridge import open_dashboard

            try:
                ok, msg = open_dashboard()
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] Hermes 網頁：{exc}"))
                self._ui_queue.put(("status", ("● 網頁失敗", "fail")))
                return
            self._ui_queue.put(("log", f"[ok] {msg}" if ok else f"[fail] {msg}"))
            self._ui_queue.put(
                ("status", ("● 就緒" if ok else "● 網頁失敗", "ok" if ok else "fail"))
            )

        threading.Thread(target=work, daemon=True).start()

    def attach_clipboard_image(self, *, silent_fail: bool = False) -> bool:
        """Grab clipboard image into HermesSandbox inbox; attach to next send."""
        from jarvis.hermes_bridge import save_clipboard_image

        try:
            path = save_clipboard_image()
        except Exception as exc:  # noqa: BLE001
            self.append_log(f"[fail] 貼圖：{exc}")
            return False
        if path is None:
            if not silent_fail:
                self.append_log("[warn] 剪貼簿無圖（先截圖／複製圖片）")
            return False
        self._pending_image = str(path)
        if self.img_status is not None:
            self.img_status.configure(
                text=f"已附圖：{path.name}（下一句送 Hermes）", fg="#1a5fb4"
            )
        self.append_log(f"[ok] 已附圖 {path}")
        return True

    def _on_paste_image(self, _event=None):
        """Legacy: clipboard image attach (no Entry in companion UI)."""
        if self.attach_clipboard_image(silent_fail=True):
            return "break"
        return None

    def _clear_pending_image(self) -> None:
        self._pending_image = None
        if self.img_status is not None:
            self.img_status.configure(text="")

    def _write_voice_status(self) -> None:
        """Write %APPDATA%/Jarvis/voice_status.json so Electron can show voice state."""
        import json as _json
        import os as _os
        from pathlib import Path as _Path

        try:
            st = {
                "wake_on": bool(getattr(self, "_wake_on", False)),
                "busy": bool(getattr(self, "_busy", False)),
                "alert_speaking": bool(getattr(self, "_alert_speaking", False)),
                "voice_call_mute": bool(getattr(self, "_voice_call_mute", False)),
                "status": getattr(self, "_status_text", "就緒"),
                "ts": time.strftime("%H:%M:%S"),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),  # ISO → HUD can detect stale
            }
            p = _Path(_os.environ.get("APPDATA", "")) / "Jarvis" / "voice_status.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(_json.dumps(st, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def set_status(self, text: str, *, kind: str = "idle") -> None:
        """Update status bar + window title (UI thread)."""
        short = text.replace("● ", "").replace("…", "")
        self._status_text = short
        if self._headless:
            self._write_voice_status()
            return
        colors = {
            "idle": "#1a5fb4",
            "busy": "#e5a50a",
            "ok": "#26a269",
            "fail": "#c01c28",
        }
        self.status.configure(text=text, fg=colors.get(kind, "#1a5fb4"))
        self.root.title(f"JARVIS · {short[:40]}")
        if self._tray is not None:
            try:
                self._tray.icon = _make_icon_image(recording=False)
                self._tray.title = f"JARVIS · {short[:48]}"
            except Exception:
                pass
        self._write_voice_status()

    def append_log(self, text: str) -> None:
        """Append a line to the caption log (UI thread)."""
        if self._headless:
            print(text, flush=True)
            return
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def show(self) -> None:
        """Show and focus the panel without forcing forever-on-top after focus."""
        if self._headless:
            return
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        if self.entry is not None:
            self.entry.focus_set()
            self.entry.selection_range(0, tk.END)

    def hide(self) -> None:
        """Hide to tray; do not quit."""
        if self._headless:
            return
        self.root.withdraw()

    def quit_app(self) -> None:
        """Stop tray + hotkey and exit the process."""
        self._show_watch_stop.set()
        self._vc_gate_stop.set()
        try:
            self.stop_wake(join_timeout=1.5)
        except Exception:
            pass
        try:
            if self._alert_watcher is not None:
                self._alert_watcher.stop(join_timeout=1.0)
                self._alert_watcher = None
        except Exception:
            pass
        tray = self._tray
        if tray is not None:
            try:
                tray.stop()
            except Exception:
                pass
            self._tray = None
        self.stop_hotkey()
        release_serve_lock(self._instance_lock)
        self._instance_lock = None
        if self._headless:
            self._headless_stop.set()
            return
        try:
            self.root.destroy()
        except tk.TclError:
            pass
    def restart_app(self) -> None:
        """Spawn a new serve process (no console), then quit this one."""
        import os
        import subprocess
        import sys

        from jarvis.autostart import _pythonw, _workdir

        self.append_log("[ok] 重啟 JARVIS…")
        py = _pythonw()
        cwd = _workdir()
        env = os.environ.copy()
        # Child waits for our mutex release after quit
        env["JARVIS_SERVE_WAIT"] = "20"
        src = cwd / "src"
        if src.is_dir():
            prev = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = str(src) if not prev else f"{src}{os.pathsep}{prev}"

        # CREATE_NO_WINDOW only — DETACHED_PROCESS makes CREATE_NO_WINDOW a
        # no-op and every console child (ffplay/python) flashes a CMD.
        flags = 0
        if sys.platform == "win32":
            flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) | int(
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )

        try:
            subprocess.Popen(
                [str(py), "-m", "jarvis", "serve"],
                cwd=str(cwd),
                env=env,
                creationflags=flags,
                close_fds=True,
            )
        except OSError as exc:
            self.append_log(f"[fail] 重啟失敗：{exc}")
            if not self._headless:
                messagebox.showerror("JARVIS", f"重啟失敗：{exc}", parent=self.root)
            return
        # release lock then exit so child can acquire
        if self._headless:
            threading.Timer(0.2, self.quit_app).start()
        else:
            self.root.after(200, self.quit_app)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        if self.btn_send is not None:
            self.btn_send.configure(state=state)
        if self.entry is not None:
            self.entry.configure(state=state)
        if busy:
            self._wake_pause.set()
        elif not self._tts_holding_pause:
            self._wake_pause.clear()
        self._write_voice_status()

    def _set_wake_btn(self, text: str) -> None:
        if self.btn_wake is not None:
            try:
                self.btn_wake.configure(text=text)
            except Exception:
                pass

    def test_alert(self) -> None:
        """Enqueue / emit one test alert phrase."""
        w = self._alert_watcher
        if w is None:
            self.append_log("[warn] alert watcher 未開")
            return
        w.emit_test()
        self.append_log("[ok] 已送試語音提醒")

    def _refresh_status_strip(self) -> None:
        """Update MCP / poller / alert_tts line (UI thread)."""
        try:
            cfg = load_settings()
            att = str(getattr(cfg, "alert_tts", "hermes") or "hermes")
            port = int(getattr(cfg, "alerts_mcp_port", 8765) or 8765)
            mcp = "up" if self._mcp_port_up(port) else "down"
            poller = "up" if self._poller_alive() else "down"
            voice = "on" if getattr(cfg, "alert_voice", True) else "off"
            if not self._headless:
                self.strip.configure(
                    text=(
                        f"MCP {mcp}:{port}  |  poller {poller}  |  "
                        f"alert_tts={att}  |  alerts={voice}"
                    )
                )
        except Exception:
            pass
        try:
            if self._headless:
                threading.Timer(3.0, self._refresh_status_strip).start()
            else:
                self.root.after(3000, self._refresh_status_strip)
        except Exception:
            pass

    @staticmethod
    def _mcp_port_up(port: int) -> bool:
        import socket

        try:
            with socket.create_connection(("127.0.0.1", int(port)), timeout=0.25):
                return True
        except OSError:
            return False

    def _poller_alive(self) -> bool:
        p = getattr(self, "_alert_poller", None)
        try:
            return p is not None and p.poll() is None
        except Exception:
            return False

    def _ask_confirm(self, prompt: str) -> bool:
        if self._headless:
            self.append_log(f"[warn] headless 無 UI 確認：{prompt[:120]}")
            return False
        return bool(messagebox.askyesno("JARVIS 確認", prompt, parent=self.root))

    def _on_submit(self, _event=None) -> None:
        if self._busy:
            return
        if self.entry is None:
            self.append_log("[warn] companion 模式無指令欄（用 Hermes）")
            return
        text = self.entry.get().strip()
        img = self._pending_image
        if not text and not img:
            return
        if not text:
            text = "請描述呢張圖。"
        self.entry.delete(0, tk.END)
        self._clear_pending_image()
        self.append_log(f"> {text}" + (f" [圖]" if img else ""))
        self._set_busy(True)
        self.set_status("● 執行指令中…", kind="busy")

        def work() -> None:
            try:
                result = _try_mage_vision_command(text)
                if result is None:
                    result = execute_utterance(
                        text,
                        ask_confirm=self._ask_confirm_threadsafe,
                        image_path=img,
                        repair_asr=False,  # UI 打字；唔跑 STT 修正／爛 alias
                    )
                self._ui_queue.put(("result", result.lines))
                self._ui_queue.put(
                    ("status", ("● 就緒" if result.ok else "● 失敗（見日誌）", "ok" if result.ok else "fail"))
                )
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] {exc}"))
                self._ui_queue.put(("status", ("● 失敗（見日誌）", "fail")))
            finally:
                self._ui_queue.put(("busy", False))

        threading.Thread(target=work, daemon=True).start()

    def _push_hud_reply(self, payload: list[str]) -> None:
        """Push the reply text to the JARVIS HUD overlay (127.0.0.1:8770)."""
        import json
        import re
        import urllib.request

        caption: str | None = None
        spoken: str | None = None
        for line in payload:
            m = re.match(r"^\[caption\]\s*(.*)$", line)
            if m and m.group(1).strip() and caption is None:
                caption = m.group(1).strip()
            m = re.match(r"^\[speak\]\s*(.*)$", line)
            if m and m.group(1).strip() and spoken is None:
                spoken = m.group(1).strip()
        text = caption or spoken
        if not text:
            return
        data = json.dumps({"text": text, "spoken": spoken or ""}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8770/reply",
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)

    def _ask_confirm_threadsafe(self, prompt: str) -> bool:
        """Ask Yes/No on the Tk thread from a worker."""
        if self._headless:
            return self._ask_confirm(prompt)
        box: queue.Queue = queue.Queue()

        def ask() -> None:
            box.put(self._ask_confirm(prompt))

        self.root.after(0, ask)
        try:
            return bool(box.get(timeout=120))
        except queue.Empty:
            return False

    def _handle_result(self, payload) -> None:
        for line in payload:
            self.append_log(line)
        # Push reply to JARVIS HUD overlay (best effort, silent).
        try:
            self._push_hud_reply(payload)
        except Exception:
            pass
        from jarvis.mouth import available, interrupt, speak

        if available():
            reply = _pick_spoken_line(payload)
            if reply:
                self._tts_holding_pause = True
                self._wake_pause.set()
                # 中斷「Yes, Sir.」ack，避免同正式 reply 疊聲
                try:
                    interrupt()
                except Exception:
                    pass

                def _speak(text: str = reply) -> None:
                    try:
                        speak(text, blocking=True)
                    finally:
                        self._tts_holding_pause = False
                        if (
                            self._wake_on
                            and not self._busy
                            and not self._voice_call_mute
                        ):
                            self._wake_pause.clear()

                threading.Thread(target=_speak, daemon=True).start()

    def _handle_alert(self, payload) -> None:
        try:
            from jarvis.alerts import alert_phrase_for
            from jarvis.settings import load_settings as _load_s

            akind = str(getattr(payload, "kind", "") or "")
            detail = getattr(payload, "detail", "") or ""
            # Prefer watcher phrase (cursor plan/approve/done differ).
            # Never speak toast body (often CJK).
            raw_phrase = (
                getattr(payload, "phrase", "") or ""
            ).strip()
            if akind == "test":
                phrase = "Alert system ready."
            elif (
                akind == "cursor"
                and raw_phrase
                and not any(
                    "\u4e00" <= ch <= "\u9fff" for ch in raw_phrase
                )
            ):
                phrase = raw_phrase
            elif akind in ("discord", "whatsapp", "cursor", "test"):
                phrase = alert_phrase_for(
                    "cursor" if akind == "cursor" else akind
                )
                if akind == "cursor" and "flash" in detail:
                    phrase = "Cursor needs your attention."
            else:
                phrase = raw_phrase
                if not phrase or any(
                    "\u4e00" <= ch <= "\u9fff" for ch in phrase
                ):
                    phrase = alert_phrase_for(
                        akind or "extra", app_label=akind
                    )

            self.append_log(
                f"[alert] {akind or '?'}"
                f"{(': ' + detail) if detail else ''}"
            )
            if not phrase:
                self.append_log("[warn] alert 無英文句，略過朗讀")
                return
            sink = str(
                getattr(_load_s(), "alert_tts", "hermes") or "hermes"
            ).lower()
            if self._voice_call_mute:
                # Voice call 中：唔出聲（防洩漏俾對方）
                self.append_log(
                    "[alert] voice_call 中，略過朗讀（防洩漏）"
                )
            elif sink == "off":
                self.append_log("[alert] alert_tts=off，略過")
            elif sink == "hermes":
                # CRITICAL: no mouth.speak — Hermes polls MCP
                self._enqueue_alert(akind or "extra", phrase)
            else:
                from jarvis.mouth import available, speak

                if not available():
                    self.append_log(
                        "[warn] alert 無 Piper 模型，唔得朗讀"
                    )
                elif self._alert_speaking:
                    self.append_log(
                        "[warn] alert TTS 忙，略過重複（只朗讀英文提醒句）"
                    )
                else:
                    self._alert_speaking = True
                    self._write_voice_status()
                    self._tts_holding_pause = True
                    self._wake_pause.set()
                    self.append_log(f"[alert] 朗讀: {phrase}")

                    def _alert_speak(text: str = phrase) -> None:
                        try:
                            from jarvis.mouth import last_speak_error

                            ok = speak(
                                text, blocking=True, force=True
                            )
                            if not ok:
                                err = last_speak_error() or "unknown"
                                self._ui_queue.put(
                                    (
                                        "log",
                                        f"[fail] alert TTS：{err}",
                                    )
                                )
                        finally:
                            self._alert_speaking = False
                            self._write_voice_status()
                            self._tts_holding_pause = False
                            if (
                                self._wake_on
                                and not self._busy
                                and not self._voice_call_mute
                            ):
                                self._wake_pause.clear()

                    threading.Thread(
                        target=_alert_speak, daemon=True
                    ).start()
        except Exception as exc:  # noqa: BLE001
            self.append_log(f"[fail] alert handler: {exc}")

    def _handle_wake(self, payload) -> None:
        self.request_show()
        now = time.time()
        if self._busy or self._tts_holding_pause:
            self._wake_pause.set()
            self.append_log("[warn] 忙碌中，略過聽候")
        elif now - self._last_wake_ts < float(self._wake_cd):
            self._wake_pause.clear()
            self.append_log("[warn] 聽候 CD 中")
        else:
            self._last_wake_ts = now
            self.append_log("[ok] 聽到 Jarvis（無 PCM；略過）")
            self._wake_pause.clear()

    def _handle_wake_cmd(self, payload) -> None:
        self.request_show()
        now = time.time()
        if self._busy or self._tts_holding_pause:
            self._wake_pause.set()
            self.append_log("[warn] 忙碌中，略過聽候")
        elif now - self._last_wake_ts < float(self._wake_cd):
            self._wake_pause.clear()
            self.append_log("[warn] 聽候 CD 中")
        else:
            self._last_wake_ts = now
            self.append_log("[ok] 聽到 Jarvis → 識別指令")
            self._on_listen_cmd(payload)

    def _drain_queue(self) -> None:
        # G3: Trusted 到期要關 docker terminal（唔靠人記得）
        try:
            self.hermes_is_trusted()
        except Exception:
            pass
        try:
            while True:
                kind, payload = self._ui_queue.get_nowait()
                if kind == "result":
                    self._handle_result(payload)
                    continue
                if kind == "alert":
                    self._handle_alert(payload)
                    continue
                if kind == "wake":
                    self._handle_wake(payload)
                    continue
                if kind == "wake_cmd":
                    self._handle_wake_cmd(payload)
                    continue
                elif kind == "wake_off":
                    self._wake_on = False
                    self._set_wake_btn("聽候：關")
                elif kind == "show":
                    self.show()
                elif kind == "toggle":
                    self.toggle()
                elif kind == "settings":
                    self.open_settings()
                elif kind == "log":
                    self.append_log(str(payload))
                elif kind == "status":
                    text, st = payload
                    self.set_status(text, kind=st)
                elif kind == "busy":
                    self._set_busy(bool(payload))
        except queue.Empty:
            pass
        if self._headless:
            threading.Timer(0.1, self._drain_queue).start()
        else:
            self.root.after(100, self._drain_queue)

    def toggle(self) -> None:
        """Show if withdrawn; hide if visible."""
        if self._headless:
            return
        try:
            withdrawn = self.root.state() == "withdrawn"
        except tk.TclError:
            withdrawn = True
        if withdrawn:
            self.show()
        else:
            self.hide()

    def request_show(self) -> None:
        """Called from hotkey / tray thread."""
        self._ui_queue.put(("show", None))

    def request_toggle(self) -> None:
        """Called from hotkey thread to toggle visibility."""
        self._ui_queue.put(("toggle", None))

    def request_settings(self) -> None:
        """Open settings from tray thread."""
        self._ui_queue.put(("settings", None))

    def stop_hotkey(self) -> None:
        """Unregister global hotkey listener."""
        if self._hotkey_listener is not None:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
            self._hotkey_listener = None

    def restart_hotkey(self) -> None:
        """Stop then start with current ``self._hotkey``."""
        self.stop_hotkey()
        self.start_hotkey()

    def start_hotkey(self) -> None:
        """Listen for configured hotkey in a background thread."""
        try:
            from pynput import keyboard
        except ImportError:
            self._ui_queue.put(("log", "[warn] 未安裝 pynput，熱鍵不可用"))
            return

        hk = self._hotkey or "<ctrl>+<alt>+j"

        def on_activate() -> None:
            self.request_toggle()

        try:
            hotkeys = keyboard.GlobalHotKeys({hk: on_activate})
            hotkeys.start()
        except Exception as exc:  # noqa: BLE001
            self._ui_queue.put(
                ("log", f"[fail] 熱鍵註冊失敗 {hotkey_display(hk)}：{exc}")
            )
            return
        self._hotkey_listener = hotkeys
        self._ui_queue.put(
            ("log", f"[ok] 熱鍵 {hotkey_display(hk)} 已註冊（再開隱藏／顯示）")
        )

    def start_tray(self) -> None:
        """Start pystray icon in a daemon thread."""
        import os

        if os.environ.get("JARVIS_ELECTRON_HOST") == "1":
            self._ui_queue.put(("log", "[ok] tray 由 Electron 管（JARVIS ONE）"))
            return
        try:
            import pystray
        except ImportError:
            self._ui_queue.put(("log", "[warn] 未安裝 pystray，無系統匣"))
            return

        def on_show(icon, item) -> None:  # noqa: ARG001
            self.request_show()

        def on_settings(icon, item) -> None:  # noqa: ARG001
            self.request_settings()

        def on_quit(icon, item) -> None:  # noqa: ARG001
            icon.stop()
            self.root.after(0, self.quit_app)

        def on_restart(icon, item) -> None:  # noqa: ARG001
            self.root.after(0, self.restart_app)

        def on_test_alert(icon, item) -> None:  # noqa: ARG001
            self.root.after(0, self.test_alert)

        menu = pystray.Menu(
            pystray.MenuItem("開啟 companion", on_show, default=True),
            pystray.MenuItem("試語音提醒", on_test_alert),
            pystray.MenuItem("設定", on_settings),
            pystray.MenuItem("重啟", on_restart),
            pystray.MenuItem("結束", on_quit),
        )
        icon = pystray.Icon("jarvis", _make_icon_image(), "JARVIS · companion", menu)
        self._tray = icon
        threading.Thread(target=icon.run, daemon=True).start()
        self._ui_queue.put(("log", "[ok] 系統匣已啟動"))

    def _start_voice_call_gate(self) -> None:
        """Voice call (pycaw via sk_activity.json) → mute passive TTS + pause wake.

        被動出聲（ack/alerts）mute；SK 主動 wake 嘅 reply 照出（SK 明知 voice call 中
        叫 JARVIS，自己承受洩漏）。wake 暫停防對方聲誤觸——AEC 開咗之後可放寬。
        """
        from jarvis.activity import load_activity

        def _loop() -> None:
            while not self._vc_gate_stop.is_set():
                try:
                    st = load_activity()
                    vc = bool(st.get("voice_call", False))
                    self._voice_call_mute = vc
                    if vc:
                        if not self._aec_active:
                            self._wake_pause.set()
                    else:
                        # 唔係 command 處理中先 clear（fire 處理中 pause 由 _on_listen_cmd 管）
                        if (
                            self._wake_on
                            and not self._busy
                            and not self._tts_holding_pause
                            and not self._voice_call_mute
                        ):
                            self._wake_pause.clear()
                except Exception:
                    pass
                time.sleep(5.0)

        threading.Thread(target=_loop, daemon=True, name="jarvis-vc-gate").start()

    def _start_game_alert_watch(self) -> None:
        """Watch sk_activity.json game_started → enqueue one "Game is ready" alert per game session."""
        # Idempotent-start guard (mirror _ensure_alert_poller).
        if getattr(self, "_game_watch_thread", None) is not None:
            return

        def _watch() -> None:
            from jarvis.activity import load_activity

            last_seen = None  # (game, started) tuple we already alerted
            while not self._game_watch_stop.is_set():
                try:
                    data = load_activity() or {}
                    game = data.get("game")
                    started = bool(data.get("game_started", False))
                    key = (game, started)
                    if started and game and key != last_seen:
                        last_seen = key
                        self._enqueue_alert(
                            "game",
                            f"{game} is ready, sir.",
                            app="game",
                            log_prefix="game alert",
                        )
                    elif not started:
                        last_seen = None
                except Exception:  # noqa: BLE001
                    pass
                self._game_watch_stop.wait(timeout=5.0)

        self._game_watch_thread = threading.Thread(
            target=_watch, daemon=True, name="jarvis-game-alert"
        )
        self._game_watch_thread.start()

    def _start_settings_apply_watch(self) -> None:
        """H2: apply settings patches (HTTP / self-monitor) to live values without restart."""
        if getattr(self, "_settings_apply_thread", None) is not None:
            return

        def _watch() -> None:
            while not self._game_watch_stop.is_set():
                try:
                    from jarvis.settings import consume_pending_apply

                    patch = consume_pending_apply()
                    if patch:
                        if "wake_threshold" in patch:
                            try:
                                self._wake_threshold = float(patch["wake_threshold"])
                                self._ui_queue.put(
                                    ("log", f"[ok] settings applied: wake_threshold={self._wake_threshold}")
                                )
                            except (TypeError, ValueError):
                                pass
                except Exception:  # noqa: BLE001
                    pass
                self._game_watch_stop.wait(timeout=5.0)

        t = threading.Thread(target=_watch, daemon=True, name="jarvis-settings-apply")
        t.start()
        self._settings_apply_thread = t

    def _safe_start(self, label: str, fn) -> None:
        """Run a background-service starter, logging failures without crashing boot."""
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            self.append_log(f"[warn] {label} 啟動失敗：{exc}")

    def run(self) -> None:
        """Block on Tk mainloop, or headless wait when JARVIS_ELECTRON_HOST=1."""
        self.start_hotkey()
        self.start_tray()
        self._start_show_watch()
        # Warm Piper/ORT on UI thread before alerts (avoids DLL init races)
        try:
            from jarvis.mouth import available, warmup

            if available():
                ok, note = warmup()
                if ok:
                    self.append_log("[ok] TTS Piper 已預載")
                else:
                    self.append_log(
                        f"[warn] TTS 預載失敗，改用子行程播：{note}"
                    )
        except Exception as exc:  # noqa: BLE001
            self.append_log(f"[warn] TTS 預載：{exc}")
        # STT warmup：預載 SenseVoice（CPU 載入實測 ~3.5GB RAM）——跟 stt_preload
        # 設定（default False = lazy load，第一次喚醒先載，慳 RAM；True = 啟動預載
        # 令首次喚醒快 5-8s）。background 唔 block UI。
        try:
            from jarvis.ear import _get_sensevoice
            from jarvis.settings import load_settings

            if load_settings().stt_preload:
                def _warm_stt() -> None:
                    try:
                        _get_sensevoice()
                        self.append_log("[ok] STT SenseVoice 已預載")
                    except Exception as exc2:  # noqa: BLE001
                        self.append_log(f"[warn] STT 預載：{exc2}")

                threading.Thread(target=_warm_stt, daemon=True).start()
            else:
                self.append_log("[ok] STT SenseVoice lazy（stt_preload=off，慳 ~3.5GB RAM）")
        except Exception as exc:  # noqa: BLE001
            self.append_log(f"[warn] STT 預載：{exc}")
        self._apply_alert_settings()
        # Voice call gate：sk_activity.json `voice_call` → mute 被動 TTS + pause wake
        self._safe_start("voice_call gate", self._start_voice_call_gate)
        # Game-ready alert：sk_activity.json game_started → 「<Game> is ready, sir.」
        self._safe_start("game alert watch", self._start_game_alert_watch)
        # H2: settings patch apply（HTTP/self-monitor → live wake_threshold）
        self._safe_start("settings apply", self._start_settings_apply_watch)
        # Daily self-monitor（in-app；取代舊 Hermes cron jarvis-self-monitor）
        self._safe_start("self-monitor", self._ensure_self_monitor)
        # Always-on voice: auto-start OWW wake on serve (respects voice_frontend).
        self._safe_start("自動聽候", self.start_wake)
        cfg = load_settings()
        att = getattr(cfg, "alert_tts", "hermes")
        self.set_status("● 就緒", kind="idle")
        self.append_log("JARVIS companion 就緒 — 桌面提醒眼睛（對話用 Hermes）")
        self.append_log(
            f"[ok] alert_tts={att} Hermes="
            f"{'on' if cfg.hermes_enabled else 'off'} · docs/hermes_alerts_mcp.md"
        )
        if self._headless:
            self.append_log("[ok] headless serve（Electron Companion；無 tkinter 視窗）")
        self._refresh_status_strip()
        if self._headless:
            threading.Timer(0.1, self._drain_queue).start()
            try:
                while not self._headless_stop.is_set():
                    self._headless_stop.wait(timeout=1.0)
            finally:
                self._show_watch_stop.set()
                if self._hotkey_listener is not None:
                    try:
                        self._hotkey_listener.stop()
                    except Exception:
                        pass
                release_serve_lock(self._instance_lock)
                self._instance_lock = None
            return
        self.request_show()
        self.root.mainloop()
        self._show_watch_stop.set()
        # mainloop ended (quit_app may already have stopped these)
        if self._hotkey_listener is not None:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
        release_serve_lock(self._instance_lock)
        self._instance_lock = None

    def _start_show_watch(self) -> None:
        """Background: second serve instance pulses show-event → deiconify."""
        import sys

        if sys.platform != "win32" or not self._instance_lock:
            return
        show_ev = self._instance_lock[1]
        if not show_ev:
            return
        k32 = _win_kernel32()

        def watch() -> None:
            while not self._show_watch_stop.is_set():
                r = k32.WaitForSingleObject(show_ev, 500)
                if r == _WAIT_OBJECT_0:
                    self.request_show()

        threading.Thread(target=watch, daemon=True, name="jarvis-show").start()


def run_shell() -> None:
    """Entry for `jarvis serve` — single instance on Windows."""
    import os
    import sys

    wait = float(os.environ.pop("JARVIS_SERVE_WAIT", "0") or "0")
    lock = acquire_serve_lock(wait_sec=wait)
    if lock is None:
        shown = _signal_existing_show()
        from jarvis.settings import hotkey_display, load_settings

        try:
            tip = hotkey_display(load_settings().hotkey)
        except Exception:
            tip = "熱鍵"
        msg = (
            "JARVIS 已在運行"
            + (" — 已叫現有視窗顯示" if shown else f"（{tip} 顯示）")
        )
        print(msg, file=sys.stderr)
        raise SystemExit(0)
    shell = JarvisShell(instance_lock=lock)
    try:
        shell.run()
    finally:
        # quit_app may already have released (idempotent)
        release_serve_lock(lock)
