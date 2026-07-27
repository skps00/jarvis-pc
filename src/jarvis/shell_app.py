"""System tray + small command window + Ctrl+Alt+J hotkey."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from jarvis.engine import execute_utterance

HOTKEY = "<ctrl>+<alt>+j"


def _make_icon_image(*, recording: bool = False):
    """Tiny circle icon for the tray (blue=idle, red=recording)."""
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

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("JARVIS · 就緒")
        self.root.geometry("440x320+80+80")
        self.root.attributes("-topmost", True)
        # ponytail: withdraw until hotkey — reduces focus steal when idle
        self.root.withdraw()

        self._ui_queue: queue.Queue = queue.Queue()
        self._tray = None
        self._hotkey_listener = None
        self._busy = False
        self._countdown_left = 0
        self._wake_stop = threading.Event()
        self._wake_pause = threading.Event()
        self._wake_thread: threading.Thread | None = None
        self._wake_on = False

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

        tk.Label(frm, text="指令（Enter 送出）· Ctrl+Alt+J 顯示／隱藏").pack(anchor="w")
        self.entry = tk.Entry(frm)
        self.entry.pack(fill=tk.X, pady=(0, 6))
        self.entry.bind("<Return>", self._on_submit)

        self.log = scrolledtext.ScrolledText(frm, height=10, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)

        btn_row = tk.Frame(frm)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        self.btn_send = tk.Button(btn_row, text="送出", command=self._on_submit)
        self.btn_send.pack(side=tk.LEFT)
        self.btn_listen = tk.Button(btn_row, text="語音", command=self._on_listen)
        self.btn_listen.pack(side=tk.LEFT, padx=6)
        self.btn_wake = tk.Button(btn_row, text="聽候：關", command=self._toggle_wake)
        self.btn_wake.pack(side=tk.LEFT, padx=6)
        tk.Button(btn_row, text="隱藏", command=self.hide).pack(side=tk.LEFT, padx=6)

        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.after(100, self._drain_queue)

    def set_status(self, text: str, *, kind: str = "idle") -> None:
        """Update status bar + window title (UI thread)."""
        colors = {
            "idle": "#1a5fb4",
            "rec": "#c01c28",
            "busy": "#e5a50a",
            "ok": "#26a269",
            "fail": "#c01c28",
        }
        self.status.configure(text=text, fg=colors.get(kind, "#1a5fb4"))
        short = text.replace("● ", "").replace("…", "")
        self.root.title(f"JARVIS · {short[:40]}")
        if self._tray is not None:
            try:
                recording = kind == "rec"
                self._tray.icon = _make_icon_image(recording=recording)
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

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_send.configure(state=state)
        self.btn_listen.configure(state=state)
        self.entry.configure(state=state)
        # free mic for SenseVoice while busy; resume wake after
        if busy:
            self._wake_pause.set()
        elif self._wake_on:
            self._wake_pause.clear()

    def _ask_confirm(self, prompt: str) -> bool:
        return bool(messagebox.askyesno("JARVIS 確認", prompt, parent=self.root))

    def _on_submit(self, _event=None) -> None:
        if self._busy:
            return
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.append_log(f"> {text}")
        self._set_busy(True)
        self.set_status("● 執行指令中…", kind="busy")

        def work() -> None:
            try:
                result = execute_utterance(text, ask_confirm=self._ask_confirm_threadsafe)
                self._ui_queue.put(("result", result.lines))
                self._ui_queue.put(
                    ("status", ("● 就緒" if result.ok else "● 失敗（見日誌）", "ok" if result.ok else "fail"))
                )
            finally:
                self._ui_queue.put(("busy", False))

        threading.Thread(target=work, daemon=True).start()

    def _on_listen(self) -> None:
        """Record ~3s with visible countdown, then SenseVoice → execute."""
        if self._busy:
            return
        self._set_busy(True)
        self.append_log("[ear] 開始錄音 4 秒 — 而家講短指令（開 CS／開 Cursor）…")
        self.set_status("● 錄音中 4 — 請講指令", kind="rec")
        self._countdown_left = 4
        self.root.after(1000, self._tick_countdown)

        def work() -> None:
            try:
                from jarvis.config import load_registry
                from jarvis.ear import record_wav, transcribe_wav

                path = record_wav(seconds=4.0)
            except RuntimeError as exc:
                self._ui_queue.put(("log", f"[fail] {exc}"))
                self._ui_queue.put(("status", ("● 語音失敗", "fail")))
                self._ui_queue.put(("busy", False))
                return
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] 語音錯誤：{exc}"))
                self._ui_queue.put(("status", ("● 語音失敗", "fail")))
                self._ui_queue.put(("busy", False))
                return

            self._ui_queue.put(("status", ("● 辨識中（首次下載模型會較久）…", "busy")))
            try:
                registry = load_registry()
                hot = []
                for p in registry.profiles.values():
                    hot.extend(p.names)
                    hot.extend(p.locale_hints)
                text = transcribe_wav(path, language="yue", hotwords=hot)
            except RuntimeError as exc:
                self._ui_queue.put(("log", f"[fail] {exc}"))
                self._ui_queue.put(("status", ("● 語音失敗", "fail")))
                self._ui_queue.put(("busy", False))
                return
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] 語音錯誤：{exc}"))
                self._ui_queue.put(("status", ("● 語音失敗", "fail")))
                self._ui_queue.put(("busy", False))
                return
            finally:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass

            self._ui_queue.put(("log", f"[ear] raw={text!r}"))
            if not text.strip():
                self._ui_queue.put(("log", "[fail] 無辨識文字"))
                self._ui_queue.put(("status", ("● 無辨識文字", "fail")))
                self._ui_queue.put(("busy", False))
                return
            self._ui_queue.put(("status", ("● 執行指令中…", "busy")))
            result = execute_utterance(text.strip(), ask_confirm=self._ask_confirm_threadsafe)
            self._ui_queue.put(("result", result.lines))
            self._ui_queue.put(
                ("status", ("● 就緒" if result.ok else "● 失敗（見日誌）", "ok" if result.ok else "fail"))
            )
            self._ui_queue.put(("busy", False))

        threading.Thread(target=work, daemon=True).start()

    def _tick_countdown(self) -> None:
        """UI-only countdown while mic is open (worker records in parallel)."""
        if not self._busy or self._countdown_left <= 0:
            return
        self._countdown_left -= 1
        if self._countdown_left > 0:
            self.set_status(f"● 錄音中 {self._countdown_left} — 請講指令", kind="rec")
            self.root.after(1000, self._tick_countdown)
        else:
            # recording thread may still finish; next status comes from worker
            self.set_status("● 錄音結束，辨識中…", kind="busy")

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
        try:
            while True:
                kind, payload = self._ui_queue.get_nowait()
                if kind == "result":
                    for line in payload:
                        self.append_log(line)
                elif kind == "show":
                    self.show()
                elif kind == "toggle":
                    self.toggle()
                elif kind == "log":
                    self.append_log(str(payload))
                elif kind == "status":
                    text, st = payload
                    self.set_status(text, kind=st)
                elif kind == "busy":
                    self._set_busy(bool(payload))
                elif kind == "wake":
                    self.request_show()
                    if not self._busy:
                        self._on_listen()
                elif kind == "wake_off":
                    self._wake_on = False
                    self.btn_wake.configure(text="聽候：關")
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

    def start_hotkey(self) -> None:
        """Listen for Ctrl+Alt+J in a background thread."""
        try:
            from pynput import keyboard
        except ImportError:
            self._ui_queue.put(("log", "[warn] 未安裝 pynput，熱鍵不可用"))
            return

        def on_activate() -> None:
            self.request_toggle()

        hotkeys = keyboard.GlobalHotKeys({HOTKEY: on_activate})
        self._hotkey_listener = hotkeys
        hotkeys.start()
        self._ui_queue.put(("log", f"[ok] 熱鍵 {HOTKEY} 已註冊（再開隱藏／顯示）"))

    def start_tray(self) -> None:
        """Start pystray icon in a daemon thread."""
        try:
            import pystray
        except ImportError:
            self._ui_queue.put(("log", "[warn] 未安裝 pystray，無系統匣"))
            return

        def on_show(icon, item) -> None:  # noqa: ARG001
            self.request_show()

        def on_quit(icon, item) -> None:  # noqa: ARG001
            icon.stop()
            self.root.after(0, self.root.destroy)

        menu = pystray.Menu(
            pystray.MenuItem("開啟 JARVIS", on_show, default=True),
            pystray.MenuItem("結束", on_quit),
        )
        icon = pystray.Icon("jarvis", _make_icon_image(), "JARVIS · 就緒", menu)
        self._tray = icon
        threading.Thread(target=icon.run, daemon=True).start()
        self._ui_queue.put(("log", "[ok] 系統匣已啟動（藍點＝運行中；紅點＝錄音中）"))

    def _toggle_wake(self) -> None:
        """UI toggle for hey_jarvis listen."""
        if self._wake_on:
            self.stop_wake()
        else:
            self.start_wake()

    def start_wake(self) -> None:
        """Background hey_jarvis → auto 語音."""
        from jarvis.wake import wake_available, run_wake_loop

        if self._wake_thread and self._wake_thread.is_alive():
            return
        if not wake_available():
            self.append_log('[warn] 聽候未裝：pip install "jarvis-pc[wake]"')
            self.btn_wake.configure(text="聽候：缺")
            return
        self._wake_stop.clear()
        self._wake_pause.clear()
        self._wake_on = True
        self.btn_wake.configure(text="聽候：開")

        def on_detect() -> None:
            self._ui_queue.put(("wake", None))

        def work() -> None:
            try:
                self._ui_queue.put(("log", "[ok] 聽候中 — Hey Jarvis 或 Jarvis（英）"))
                run_wake_loop(
                    on_detect,
                    stop_event=self._wake_stop,
                    pause_event=self._wake_pause,
                )
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] 聽候錯誤：{exc}"))
                self._ui_queue.put(("wake_off", None))

        self._wake_thread = threading.Thread(target=work, daemon=True)
        self._wake_thread.start()

    def stop_wake(self) -> None:
        """Stop wake loop and release mic."""
        self._wake_on = False
        self._wake_stop.set()
        self._wake_pause.set()
        self.btn_wake.configure(text="聽候：關")
        self.append_log("[ok] 聽候已關")

    def run(self) -> None:
        """Block on Tk mainloop."""
        self.start_hotkey()
        self.start_tray()
        self.request_show()
        self.set_status("● 就緒（背景運行中）", kind="idle")
        self.append_log("JARVIS Shell 就緒。輸入 open CS2 / 開 Cursor …")
        self.append_log("提示：講 Hey Jarvis → 自動錄音；或撳「語音」。")
        self.start_wake()
        self.root.mainloop()
        self.stop_wake()
        if self._hotkey_listener is not None:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass


def run_shell() -> None:
    """Entry for `jarvis serve`."""
    JarvisShell().run()
