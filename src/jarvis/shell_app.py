"""System tray + small command window + configurable hotkey + settings.

ASR / wake listening removed — text input only (+ optional TTS).
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from jarvis.engine import execute_utterance
from jarvis.settings import Settings, hotkey_display, load_settings
from jarvis.settings_ui import SettingsWindow

# Windows single-instance (ctypes — no extra dep)
_MUTEX_NAME = "Local\\JarvisPcServe.v1"
_SHOW_EVENT_NAME = "Local\\JarvisPcServe.Show.v1"
_ERROR_ALREADY_EXISTS = 183
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 258


def _win_kernel32():
    import ctypes

    return ctypes.windll.kernel32


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


class JarvisShell:
    """Tk command panel + optional tray; hotkey shows the panel."""

    def __init__(self, *, instance_lock: list | None = None) -> None:
        self.root = tk.Tk()
        self.root.title("JARVIS · 就緒")
        self.root.geometry("440x400+80+80")
        self.root.attributes("-topmost", True)
        # ponytail: withdraw until hotkey — reduces focus steal when idle
        self.root.withdraw()

        self._instance_lock = instance_lock
        self._ui_queue: queue.Queue = queue.Queue()
        self._tray = None
        self._hotkey_listener = None
        self._busy = False
        self._hermes_trusted_until = 0.0  # monotonic; 0 = Safe
        self._settings_win: SettingsWindow | None = None
        self._show_watch_stop = threading.Event()
        self._pending_image: str | None = None
        cfg = load_settings()
        self._hotkey = cfg.hotkey

        frm = tk.Frame(self.root, padx=8, pady=8)
        frm.pack(fill=tk.BOTH, expand=True)

        self.status = tk.Label(
            frm,
            text="● 就緒（背景運行中）",
            anchor="w",
            fg="#1a5fb4",
            font=("Segoe UI", 11, "bold"),
        )
        self.status.pack(fill=tk.X, pady=(0, 4))

        self.hint = tk.Label(
            frm,
            text=f"指令（Enter 送出）· {hotkey_display(self._hotkey)} 顯示／隱藏",
            anchor="w",
        )
        self.hint.pack(anchor="w")
        self.entry = tk.Entry(frm)
        self.entry.pack(fill=tk.X, pady=(0, 6))
        self.entry.bind("<Return>", self._on_submit)
        self.entry.bind("<Control-v>", self._on_paste_image)
        self.entry.bind("<Control-V>", self._on_paste_image)

        self.img_status = tk.Label(
            frm, text="", anchor="w", fg="#666", font=("Segoe UI", 8)
        )
        self.img_status.pack(fill=tk.X)

        self.log = scrolledtext.ScrolledText(frm, height=10, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)

        btn_row = tk.Frame(frm)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        self.btn_send = tk.Button(btn_row, text="送出", command=self._on_submit)
        self.btn_send.pack(side=tk.LEFT)
        tk.Button(btn_row, text="貼圖", command=self.attach_clipboard_image).pack(
            side=tk.LEFT, padx=6
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

    def apply_settings(self, s: Settings) -> None:
        """Apply runtime knobs from Settings (after save)."""
        if not s.hermes_enabled:
            # only tears down if currently Trusted（免每次儲存打 WSL）
            self.clear_hermes_trusted()
        hermes_note = "Hermes=on" if s.hermes_enabled else "Hermes=off"
        self.append_log(
            f"[ok] 已套用：{hermes_note} LLM={s.llm_model} 熱鍵={hotkey_display(s.hotkey)}"
        )
        if s.hotkey != self._hotkey:
            self._hotkey = s.hotkey
            self.hint.configure(
                text=f"指令（Enter 送出）· {hotkey_display(self._hotkey)} 顯示／隱藏"
            )
            self.restart_hotkey()

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

    def open_settings(self) -> None:
        """Open settings Toplevel (one at a time)."""
        if self._settings_win is not None:
            try:
                if self._settings_win.win.winfo_exists():
                    self._settings_win.win.lift()
                    self._settings_win.win.focus_force()
                    return
            except tk.TclError:
                pass
        self.request_show()
        self._settings_win = SettingsWindow(self)

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
        self.img_status.configure(text=f"已附圖：{path.name}（下一句送 Hermes）", fg="#1a5fb4")
        self.append_log(f"[ok] 已附圖 {path}")
        return True

    def _on_paste_image(self, _event=None):
        """Ctrl+V: if clipboard is image, attach; else let Entry paste text."""
        if self.attach_clipboard_image(silent_fail=True):
            return "break"
        return None

    def _clear_pending_image(self) -> None:
        self._pending_image = None
        self.img_status.configure(text="")

    def set_status(self, text: str, *, kind: str = "idle") -> None:
        """Update status bar + window title (UI thread)."""
        colors = {
            "idle": "#1a5fb4",
            "busy": "#e5a50a",
            "ok": "#26a269",
            "fail": "#c01c28",
        }
        self.status.configure(text=text, fg=colors.get(kind, "#1a5fb4"))
        short = text.replace("● ", "").replace("…", "")
        self.root.title(f"JARVIS · {short[:40]}")
        if self._tray is not None:
            try:
                self._tray.icon = _make_icon_image(recording=False)
                self._tray.title = f"JARVIS · {short[:48]}"
            except Exception:
                pass

    def append_log(self, text: str) -> None:
        """Append a line to the caption log (UI thread)."""
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def show(self) -> None:
        """Show and focus the panel without forcing forever-on-top after focus."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.entry.focus_set()
        self.entry.selection_range(0, tk.END)

    def hide(self) -> None:
        """Hide to tray; do not quit."""
        self.root.withdraw()

    def quit_app(self) -> None:
        """Stop tray + hotkey and exit the process."""
        self._show_watch_stop.set()
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

        flags = 0
        if sys.platform == "win32":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0
            )
            flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)

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
            messagebox.showerror("JARVIS", f"重啟失敗：{exc}", parent=self.root)
            return
        # release lock then exit so child can acquire
        self.root.after(200, self.quit_app)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_send.configure(state=state)
        self.entry.configure(state=state)

    def _ask_confirm(self, prompt: str) -> bool:
        return bool(messagebox.askyesno("JARVIS 確認", prompt, parent=self.root))

    def _on_submit(self, _event=None) -> None:
        if self._busy:
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

    def _ask_confirm_threadsafe(self, prompt: str) -> bool:
        """Ask Yes/No on the Tk thread from a worker."""
        box: queue.Queue = queue.Queue()

        def ask() -> None:
            box.put(self._ask_confirm(prompt))

        self.root.after(0, ask)
        try:
            return bool(box.get(timeout=120))
        except queue.Empty:
            return False

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
                    for line in payload:
                        self.append_log(line)
                    from jarvis.mouth import available, speak

                    if available():
                        reply = _pick_spoken_line(payload)
                        if reply:

                            def _speak(text: str = reply) -> None:
                                speak(text, blocking=True)

                            threading.Thread(target=_speak, daemon=True).start()
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
        self.root.after(100, self._drain_queue)

    def toggle(self) -> None:
        """Show if withdrawn; hide if visible."""
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

        menu = pystray.Menu(
            pystray.MenuItem("開啟 JARVIS", on_show, default=True),
            pystray.MenuItem("設定", on_settings),
            pystray.MenuItem("重啟", on_restart),
            pystray.MenuItem("結束", on_quit),
        )
        icon = pystray.Icon("jarvis", _make_icon_image(), "JARVIS · 就緒", menu)
        self._tray = icon
        threading.Thread(target=icon.run, daemon=True).start()
        self._ui_queue.put(("log", "[ok] 系統匣已啟動"))

    def run(self) -> None:
        """Block on Tk mainloop."""
        self.start_hotkey()
        self.start_tray()
        self._start_show_watch()
        self.request_show()
        self.set_status("● 就緒（背景運行中）", kind="idle")
        self.append_log("JARVIS Shell 就緒。輸入 open CS2 / 開 Cursor …")
        self.append_log("提示：語音識別已移除 — 請打字；設定改 LLM／Hermes／開機自啟。")
        cfg = load_settings()
        hermes = "on" if cfg.hermes_enabled else "off"
        self.append_log(f"[ok] 設定：LLM={cfg.llm_model} Hermes={hermes}")
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
