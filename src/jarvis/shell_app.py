"""System tray + small command window + Ctrl+Alt+J hotkey + settings."""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from jarvis.engine import execute_utterance
from jarvis.settings import (
    ASR_OPENAI_AUDIO,
    ASR_SENSEVOICE,
    LLM_PRESET_CUSTOM,
    LLM_PRESET_DEEPSEEK,
    LLM_PRESET_OLLAMA,
    PRESET_LABELS,
    Settings,
    apply_llm_preset,
    list_models,
    load_settings,
    preset_from_label,
    probe_connection,
    save_settings,
    uses_cloud_asr,
)

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


class SettingsWindow:
    """
    Settings UI — tabs like OpenClaw/Cherry; provider→model like Hermes;
    connection probe like Cherry「檢測」.
    """

    def __init__(self, parent: JarvisShell) -> None:
        self.parent = parent
        self.win = tk.Toplevel(parent.root)
        self.win.title("JARVIS 設定")
        self.win.geometry("540x520+100+60")
        self.win.attributes("-topmost", True)
        self.win.transient(parent.root)

        from jarvis.brain import _load_dotenv

        _load_dotenv()
        s = load_settings(force=True)
        self._custom = list(s.custom_models)

        nb = ttk.Notebook(self.win)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab_asr = tk.Frame(nb, padx=8, pady=8)
        tab_llm = tk.Frame(nb, padx=8, pady=8)
        tab_sys = tk.Frame(nb, padx=8, pady=8)
        nb.add(tab_asr, text="語音 ASR")
        nb.add(tab_llm, text="大腦 LLM")
        nb.add(tab_sys, text="聽候／系統")

        self._build_asr_tab(tab_asr, s)
        self._build_llm_tab(tab_llm, s)
        self._build_sys_tab(tab_sys, s)

        btn = tk.Frame(self.win)
        btn.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Label(
            btn,
            text="存檔 → %APPDATA%\\Jarvis\\settings.json",
            fg="#666",
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT)
        tk.Button(btn, text="取消", command=self.win.destroy).pack(side=tk.RIGHT, padx=4)
        tk.Button(btn, text="儲存", command=self._save).pack(side=tk.RIGHT)

        self._sync_asr_cloud_visibility()
        self.win.grab_set()
        self.win.focus_force()

    def _build_asr_tab(self, frm: tk.Frame, s: Settings) -> None:
        asr_val = (
            ASR_OPENAI_AUDIO
            if s.asr_provider in (ASR_OPENAI_AUDIO, "mimo")
            else ASR_SENSEVOICE
        )
        self.var_asr = tk.StringVar(
            value=(
                f"{ASR_SENSEVOICE}（本機）"
                if asr_val == ASR_SENSEVOICE
                else f"{ASR_OPENAI_AUDIO}（雲端）"
            )
        )
        tk.Label(frm, text="供應商", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=4
        )
        cmb = ttk.Combobox(
            frm,
            textvariable=self.var_asr,
            values=(
                f"{ASR_SENSEVOICE}（本機）",
                f"{ASR_OPENAI_AUDIO}（雲端）",
            ),
            state="readonly",
            width=36,
        )
        cmb.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        cmb.bind("<<ComboboxSelected>>", lambda _e: self._sync_asr_cloud_visibility())

        self._asr_cloud = tk.Frame(frm)
        self._asr_cloud.grid(row=1, column=0, columnspan=3, sticky="ew")

        self.var_asr_key = tk.StringVar(value=s.asr_api_key or s.mimo_api_key)
        self.var_asr_base = tk.StringVar(value=s.asr_base_url or s.mimo_base_url)
        self.var_asr_model = tk.StringVar(value=s.asr_model)

        r = 0
        tk.Label(self._asr_cloud, text="API Key").grid(row=r, column=0, sticky="w", pady=2)
        tk.Entry(self._asr_cloud, textvariable=self.var_asr_key, width=36, show="*").grid(
            row=r, column=1, columnspan=2, sticky="ew", pady=2
        )
        r += 1
        tk.Label(self._asr_cloud, text="Base URL").grid(row=r, column=0, sticky="w", pady=2)
        tk.Entry(self._asr_cloud, textvariable=self.var_asr_base, width=36).grid(
            row=r, column=1, columnspan=2, sticky="ew", pady=2
        )
        r += 1
        tk.Label(self._asr_cloud, text="Model").grid(row=r, column=0, sticky="w", pady=2)
        self.cmb_asr_model = ttk.Combobox(
            self._asr_cloud,
            textvariable=self.var_asr_model,
            values=self._model_choices(s.asr_model),
            width=28,
        )
        self.cmb_asr_model.grid(row=r, column=1, sticky="ew", pady=2)
        tk.Button(self._asr_cloud, text="列出", command=self._list_asr_models).grid(
            row=r, column=2, padx=2
        )
        r += 1
        tk.Button(self._asr_cloud, text="檢測連線", command=self._probe_asr).grid(
            row=r, column=1, sticky="w", pady=6
        )
        tk.Label(
            self._asr_cloud,
            text="Hermes 式：Key／Base → 列出 → 揀 Model（MiMo＝openai_audio）",
            fg="#666",
            font=("Segoe UI", 8),
            wraplength=420,
            justify="left",
        ).grid(row=r + 1, column=0, columnspan=3, sticky="w")
        self._asr_cloud.columnconfigure(1, weight=1)
        frm.columnconfigure(1, weight=1)

    def _build_llm_tab(self, frm: tk.Frame, s: Settings) -> None:
        preset_id = s.llm_preset or LLM_PRESET_DEEPSEEK
        self.var_preset_label = tk.StringVar(
            value=PRESET_LABELS.get(preset_id, PRESET_LABELS[LLM_PRESET_CUSTOM])
        )
        tk.Label(frm, text="供應商 Preset", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=4
        )
        cmb = ttk.Combobox(
            frm,
            textvariable=self.var_preset_label,
            values=tuple(
                PRESET_LABELS[p] for p in ("deepseek", "mimo", "ollama", "custom")
            ),
            state="readonly",
            width=36,
        )
        cmb.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        cmb.bind("<<ComboboxSelected>>", self._on_preset)

        self.var_llm_key = tk.StringVar(value=s.llm_api_key)
        self.var_llm_base = tk.StringVar(value=s.llm_base_url)
        self.var_llm_model = tk.StringVar(value=s.llm_model)

        row = 1
        tk.Label(frm, text="API Key").grid(row=row, column=0, sticky="w", pady=2)
        tk.Entry(frm, textvariable=self.var_llm_key, width=36, show="*").grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=2
        )
        row += 1
        tk.Label(frm, text="Base URL").grid(row=row, column=0, sticky="w", pady=2)
        tk.Entry(frm, textvariable=self.var_llm_base, width=36).grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=2
        )
        row += 1
        tk.Label(frm, text="Model").grid(row=row, column=0, sticky="w", pady=2)
        self.cmb_llm_model = ttk.Combobox(
            frm,
            textvariable=self.var_llm_model,
            values=self._model_choices(s.llm_model),
            width=28,
        )
        self.cmb_llm_model.grid(row=row, column=1, sticky="ew", pady=2)
        tk.Button(frm, text="列出", command=self._list_llm_models).grid(
            row=row, column=2, padx=2
        )
        row += 1
        tk.Button(frm, text="檢測連線", command=self._probe_llm).grid(
            row=row, column=1, sticky="w", pady=4
        )
        row += 1

        self.var_custom_new = tk.StringVar()
        tk.Label(frm, text="自訂模型").grid(row=row, column=0, sticky="w", pady=2)
        tk.Entry(frm, textvariable=self.var_custom_new, width=28).grid(
            row=row, column=1, sticky="ew", pady=2
        )
        tk.Button(frm, text="加入", command=self._add_custom_model).grid(
            row=row, column=2, padx=2
        )
        row += 1
        tk.Label(
            frm,
            text="Ollama 例：http://127.0.0.1:11434/v1｜對齊 Codex／Claude Code 揀 model id",
            fg="#666",
            font=("Segoe UI", 8),
            wraplength=420,
            justify="left",
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=4)
        frm.columnconfigure(1, weight=1)

    def _build_sys_tab(self, frm: tk.Frame, s: Settings) -> None:
        self.var_thresh = tk.StringVar(value=str(s.wake_threshold))
        self.var_cd = tk.StringVar(value=str(s.wake_cd_seconds))
        self.var_rec = tk.StringVar(value=str(s.record_seconds))
        row = 0
        for label, var in (
            ("Wake 門檻 (0.1–0.99)", self.var_thresh),
            ("聽候 CD 秒", self.var_cd),
            ("錄音秒數", self.var_rec),
        ):
            tk.Label(frm, text=label).grid(row=row, column=0, sticky="w", pady=4)
            tk.Entry(frm, textvariable=var, width=20).grid(
                row=row, column=1, sticky="w", pady=4
            )
            row += 1

        from jarvis import autostart as auto

        self.var_auto = tk.BooleanVar(value=auto.is_enabled())
        tk.Checkbutton(frm, text="開機自啟（無黑窗 VBS）", variable=self.var_auto).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=8
        )
        row += 1
        tk.Label(
            frm,
            text="profiles.yaml／TTS 未喺呢度改。",
            fg="#666",
            font=("Segoe UI", 8),
        ).grid(row=row, column=0, columnspan=2, sticky="w")

    def _asr_provider_id(self) -> str:
        raw = self.var_asr.get()
        if ASR_OPENAI_AUDIO in raw:
            return ASR_OPENAI_AUDIO
        return ASR_SENSEVOICE

    def _sync_asr_cloud_visibility(self) -> None:
        if self._asr_provider_id() == ASR_OPENAI_AUDIO:
            self._asr_cloud.grid()
        else:
            self._asr_cloud.grid_remove()

    def _model_choices(self, current: str) -> tuple[str, ...]:
        seen: set[str] = set()
        out: list[str] = []
        for m in [current, *self._custom]:
            name = (m or "").strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                out.append(name)
        return tuple(out)

    def _refresh_model_combos(self) -> None:
        self.cmb_asr_model.configure(values=self._model_choices(self.var_asr_model.get()))
        self.cmb_llm_model.configure(values=self._model_choices(self.var_llm_model.get()))

    def _on_preset(self, _evt=None) -> None:
        pid = preset_from_label(self.var_preset_label.get())
        tmp = Settings(
            llm_preset=pid,
            llm_api_key=self.var_llm_key.get(),
            llm_base_url=self.var_llm_base.get(),
            llm_model=self.var_llm_model.get(),
        )
        apply_llm_preset(tmp, pid)
        self.var_llm_base.set(tmp.llm_base_url)
        if tmp.llm_api_key and not self.var_llm_key.get().strip():
            self.var_llm_key.set(tmp.llm_api_key)

    def _list_asr_models(self) -> None:
        self._list_into(
            self.var_asr_base.get(),
            self.var_asr_key.get(),
            self.var_asr_model,
            self.cmb_asr_model,
        )

    def _list_llm_models(self) -> None:
        self._list_into(
            self.var_llm_base.get(),
            self.var_llm_key.get(),
            self.var_llm_model,
            self.cmb_llm_model,
        )

    def _probe_asr(self) -> None:
        self._run_net(
            "ASR 檢測",
            lambda: probe_connection(self.var_asr_base.get(), self.var_asr_key.get()),
        )

    def _probe_llm(self) -> None:
        self._run_net(
            "LLM 檢測",
            lambda: probe_connection(self.var_llm_base.get(), self.var_llm_key.get()),
        )

    def _run_net(self, title: str, fn) -> None:
        """Run blocking HTTP off the Tk thread (avoid freeze)."""

        def work() -> None:
            try:
                msg = fn()
            except RuntimeError as exc:
                err = str(exc)
                self.win.after(
                    0,
                    lambda t=title, e=err: messagebox.showerror(
                        f"{t}失敗", e, parent=self.win
                    ),
                )
                return
            ok = str(msg)
            self.win.after(
                0,
                lambda t=title, m=ok: messagebox.showinfo(t, m, parent=self.win),
            )

        threading.Thread(target=work, daemon=True).start()

    def _list_into(
        self,
        base: str,
        key: str,
        model_var: tk.StringVar,
        combo: ttk.Combobox,
    ) -> None:
        def work() -> None:
            try:
                ids = list_models(base, key)
            except RuntimeError as exc:
                err = str(exc)
                self.win.after(
                    0,
                    lambda e=err: messagebox.showerror(
                        "列模型失敗", e, parent=self.win
                    ),
                )
                return

            def apply() -> None:
                merged: list[str] = []
                seen: set[str] = set()
                for m in [*self._custom, *ids, model_var.get()]:
                    name = (m or "").strip()
                    if name and name.lower() not in seen:
                        seen.add(name.lower())
                        merged.append(name)
                combo.configure(values=tuple(merged))
                if model_var.get().strip() not in merged and merged:
                    model_var.set(merged[0])
                messagebox.showinfo(
                    "模型列表",
                    f"API {len(ids)} 個 + 自訂 {len(self._custom)}。請喺下拉揀要用嘅。",
                    parent=self.win,
                )

            self.win.after(0, apply)

        threading.Thread(target=work, daemon=True).start()

    def _add_custom_model(self) -> None:
        name = self.var_custom_new.get().strip()
        if not name:
            return
        low = name.lower()
        if not any(c.lower() == low for c in self._custom):
            self._custom.append(name)
        self.var_custom_new.set("")
        self.var_llm_model.set(name)
        self._refresh_model_combos()
        messagebox.showinfo("自訂模型", f"已加入並選用：{name}", parent=self.win)

    def _save(self) -> None:
        asr = self._asr_provider_id()
        if asr == ASR_OPENAI_AUDIO and not self.var_asr_key.get().strip():
            messagebox.showwarning(
                "JARVIS 設定",
                "雲端 ASR 請填 API Key。",
                parent=self.win,
            )
            return
        preset = preset_from_label(self.var_preset_label.get())
        if preset == LLM_PRESET_OLLAMA and not self.var_llm_key.get().strip():
            self.var_llm_key.set("ollama")
        try:
            thresh = float(self.var_thresh.get().strip())
            cd = float(self.var_cd.get().strip())
            rec = float(self.var_rec.get().strip())
        except ValueError:
            messagebox.showerror(
                "JARVIS 設定", "門檻／CD／錄音秒數要係數字。", parent=self.win
            )
            return
        if not (0.1 <= thresh <= 0.99):
            messagebox.showerror(
                "JARVIS 設定", "Wake 門檻要喺 0.1–0.99。", parent=self.win
            )
            return
        if not (0.5 <= cd <= 30.0):
            messagebox.showerror(
                "JARVIS 設定", "聽候 CD 要喺 0.5–30 秒。", parent=self.win
            )
            return
        if not (1.0 <= rec <= 15.0):
            messagebox.showerror(
                "JARVIS 設定", "錄音秒數要喺 1–15。", parent=self.win
            )
            return

        asr_key = self.var_asr_key.get().strip()
        asr_base = self.var_asr_base.get().strip()
        s = Settings(
            asr_provider=asr,
            asr_api_key=asr_key,
            asr_base_url=asr_base,
            asr_model=self.var_asr_model.get().strip(),
            mimo_api_key=asr_key,
            mimo_base_url=asr_base,
            llm_preset=preset,
            llm_api_key=self.var_llm_key.get().strip(),
            llm_base_url=self.var_llm_base.get().strip(),
            llm_model=self.var_llm_model.get().strip(),
            custom_models=list(self._custom),
            wake_threshold=thresh,
            wake_cd_seconds=cd,
            record_seconds=rec,
        )
        path = save_settings(s)

        from jarvis import autostart as auto

        want_auto = bool(self.var_auto.get())
        auto_msg = ""
        try:
            if want_auto:
                auto_msg = auto.enable()
            elif auto.is_enabled():
                auto_msg = auto.disable()
        except OSError as exc:
            auto_msg = f"開機自啟失敗：{exc}"

        self.parent.apply_settings(s, restart_wake=True)
        self.parent.append_log(f"[ok] 設定已存：{path}")
        if auto_msg:
            self.parent.append_log(f"[ok] {auto_msg}")
        self.win.destroy()


class JarvisShell:
    """Tk command panel + optional tray; hotkey shows the panel."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("JARVIS · 就緒")
        self.root.geometry("440x400+80+80")
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
        self._last_wake_ts = 0.0
        self._cd_left = 0
        self._timer_mode = ""  # "rec" | "cd" | ""
        self._settings_win: SettingsWindow | None = None

        cfg = load_settings()
        self._record_seconds = int(round(cfg.record_seconds))
        self._wake_cd = float(cfg.wake_cd_seconds)
        self._wake_threshold = float(cfg.wake_threshold)

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

        self.timer = tk.Label(
            frm,
            text="",
            anchor="center",
            fg="#c01c28",
            font=("Segoe UI", 28, "bold"),
            height=1,
        )
        self.timer.pack(fill=tk.X, pady=(0, 4))
        self.timer.pack_forget()  # hide until recording

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
        tk.Button(btn_row, text="設定", command=self.open_settings).pack(
            side=tk.LEFT, padx=6
        )
        tk.Button(btn_row, text="隱藏", command=self.hide).pack(side=tk.LEFT, padx=6)

        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.after(100, self._drain_queue)

    def apply_settings(self, s: Settings, *, restart_wake: bool = False) -> None:
        """Apply runtime knobs from Settings (after save)."""
        was_wake = bool(self._wake_on)
        self._record_seconds = max(1, int(round(s.record_seconds)))
        self._wake_cd = float(s.wake_cd_seconds)
        self._wake_threshold = float(s.wake_threshold)
        self.append_log(
            f"[ok] 已套用：ASR={s.asr_provider} REC={self._record_seconds}s "
            f"CD={self._wake_cd}s thr={self._wake_threshold}"
        )
        # Must join old wake thread before start — else start_wake early-returns
        # and listening stays off (common settings-restart race).
        if restart_wake and was_wake:
            self.stop_wake()
            if self._wake_thread is not None and self._wake_thread.is_alive():
                self.append_log("[warn] 聽候重啟失敗（舊線程未結束）；門檻可能未套用")
            else:
                self.start_wake()
                # Settings stays clickable while busy; don't steal mic mid-record.
                if self._busy:
                    self._wake_pause.set()

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
        # free mic for SenseVoice while busy; always resume wake after
        if busy:
            self._wake_pause.set()
        else:
            self._wake_pause.clear()
            if self._wake_on:
                self.append_log("[ok] 聽候 CD 開始")
                self._start_wake_cd(int(round(self._wake_cd)))

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
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] {exc}"))
                self._ui_queue.put(("status", ("● 失敗（見日誌）", "fail")))
            finally:
                self._ui_queue.put(("busy", False))

        threading.Thread(target=work, daemon=True).start()

    def _show_timer(self, seconds: int, *, mode: str = "rec") -> None:
        """Show big countdown: REC n or CD n (UI thread)."""
        self._timer_mode = mode
        try:
            self.timer.pack(fill=tk.X, pady=(0, 4), after=self.status)
        except tk.TclError:
            self.timer.pack(fill=tk.X, pady=(0, 4))
        if mode == "cd":
            self.timer.configure(text=f"CD {seconds}", fg="#e5a50a")
        else:
            self.timer.configure(text=f"REC {seconds}", fg="#c01c28")

    def _hide_timer(self) -> None:
        """Hide countdown label."""
        self._timer_mode = ""
        self._cd_left = 0
        self.timer.configure(text="")
        self.timer.pack_forget()

    def _start_wake_cd(self, seconds: int) -> None:
        """Visible cooldown until Jarvis can fire again."""
        self._cd_left = max(0, int(seconds))
        if self._cd_left <= 0:
            self._hide_timer()
            self.set_status("● 聽候就緒", kind="ok")
            return
        self._show_timer(self._cd_left, mode="cd")
        self.set_status(f"● 聽候 CD {self._cd_left}s", kind="busy")
        self.root.after(1000, self._tick_wake_cd)

    def _tick_wake_cd(self) -> None:
        """Tick wake cooldown display."""
        if self._busy or not self._wake_on:
            return
        if self._timer_mode == "rec":
            return
        self._cd_left -= 1
        if self._cd_left > 0:
            self._show_timer(self._cd_left, mode="cd")
            self.set_status(f"● 聽候 CD {self._cd_left}s", kind="busy")
            self.root.after(1000, self._tick_wake_cd)
        else:
            self._hide_timer()
            self.set_status("● 聽候就緒 — 可講 Jarvis", kind="ok")
            self.append_log("[ok] 聽候就緒")

    def _on_listen(self) -> None:
        """Record with visible countdown, then ASR → execute."""
        if self._busy:
            return
        self._set_busy(True)
        secs = self._record_seconds
        self.append_log(f"[ear] 錄音 {secs}s — 倒數開始，請講短指令")
        self._countdown_left = secs
        self._show_timer(secs, mode="rec")
        self.set_status(f"● 錄音中 {secs} — 請講指令", kind="rec")
        self.root.after(1000, self._tick_countdown)

        def work() -> None:
            path = None
            try:
                from jarvis.config import load_registry
                from jarvis.ear import record_wav, transcribe_path
                from jarvis.settings import load_settings

                # Wake released mic ~0.25s earlier; small extra settle
                time.sleep(0.15)
                cfg = load_settings()
                path = record_wav(seconds=float(self._record_seconds))
                self._ui_queue.put(("timer_hide", None))
                status_msg = (
                    f"● 辨識中（{cfg.asr_model}）…"
                    if uses_cloud_asr(cfg)
                    else "● 辨識中（首次下載模型會較久）…"
                )
                self._ui_queue.put(("status", (status_msg, "busy")))
                registry = load_registry()
                hot = []
                for p in registry.profiles.values():
                    hot.extend(p.names)
                    hot.extend(p.locale_hints)
                text = transcribe_path(path, language="yue", hotwords=hot)
                self._ui_queue.put(("log", f"[ear] raw={text!r} ({cfg.asr_provider})"))
                if not text.strip():
                    self._ui_queue.put(("log", "[fail] 無辨識文字"))
                    self._ui_queue.put(("status", ("● 無辨識文字", "fail")))
                    return
                self._ui_queue.put(("status", ("● 執行指令中…", "busy")))
                result = execute_utterance(
                    text.strip(), ask_confirm=self._ask_confirm_threadsafe
                )
                self._ui_queue.put(("result", result.lines))
                self._ui_queue.put(
                    (
                        "status",
                        ("● 就緒" if result.ok else "● 失敗（見日誌）", "ok" if result.ok else "fail"),
                    )
                )
            except RuntimeError as exc:
                self._ui_queue.put(("log", f"[fail] {exc}"))
                self._ui_queue.put(("status", ("● 語音失敗", "fail")))
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] 語音錯誤：{exc}"))
                self._ui_queue.put(("status", ("● 語音失敗", "fail")))
            finally:
                if path is not None:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
                self._ui_queue.put(("timer_hide", None))
                # critical: always unpause wake（否則只醒一次）
                self._ui_queue.put(("busy", False))

        threading.Thread(target=work, daemon=True).start()

    def _tick_countdown(self) -> None:
        """UI-only countdown while mic is open (worker records in parallel)."""
        if not self._busy or self._countdown_left <= 0:
            return
        self._countdown_left -= 1
        if self._countdown_left > 0:
            left = self._countdown_left
            self._show_timer(left, mode="rec")
            self.set_status(f"● 錄音中 {left} — 請講指令", kind="rec")
            self.append_log(f"[ear] …{left}")
            self.root.after(1000, self._tick_countdown)
        else:
            self._show_timer(0, mode="rec")
            self.set_status("● 錄音結束，辨識中…", kind="busy")
            self.append_log("[ear] 倒數完")

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
                elif kind == "settings":
                    self.open_settings()
                elif kind == "log":
                    self.append_log(str(payload))
                elif kind == "status":
                    text, st = payload
                    self.set_status(text, kind=st)
                elif kind == "busy":
                    self._set_busy(bool(payload))
                elif kind == "timer_hide":
                    self._hide_timer()
                elif kind == "wake":
                    self.request_show()
                    now = time.time()
                    if now - self._last_wake_ts < float(self._wake_cd):
                        self._wake_pause.clear()
                        left = max(0, int(self._wake_cd - (now - self._last_wake_ts)))
                        self.append_log(f"[warn] 聽候略過（CD {left}s）")
                    elif self._busy:
                        self._wake_pause.clear()
                        self.append_log("[warn] 聽候略過（忙緊）")
                    else:
                        self._last_wake_ts = now
                        self.append_log("[ok] 聽到 Jarvis — 請講指令（開／關…）")
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

    def request_settings(self) -> None:
        """Open settings from tray thread."""
        self._ui_queue.put(("settings", None))

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

        def on_settings(icon, item) -> None:  # noqa: ARG001
            self.request_settings()

        def on_quit(icon, item) -> None:  # noqa: ARG001
            icon.stop()
            self.root.after(0, self.root.destroy)

        menu = pystray.Menu(
            pystray.MenuItem("開啟 JARVIS", on_show, default=True),
            pystray.MenuItem("設定", on_settings),
            pystray.MenuItem("結束", on_quit),
        )
        icon = pystray.Icon("jarvis", _make_icon_image(), "JARVIS · 就緒", menu)
        self._tray = icon
        threading.Thread(target=icon.run, daemon=True).start()
        self._ui_queue.put(("log", "[ok] 系統匣已啟動（藍點＝運行中；紅點＝錄音中）"))

    def _toggle_wake(self) -> None:
        """UI toggle for Jarvis listen (OWW + STT hybrid)."""
        if self._wake_on:
            self.stop_wake()
        else:
            self.start_wake()

    def start_wake(self) -> None:
        """Background Jarvis wake → auto 語音."""
        from jarvis.wake import (
            has_custom_jarvis_model,
            recommended_threshold,
            run_wake_loop,
            wake_available,
        )

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
        thr = float(self._wake_threshold)
        # Soften high thr when custom onnx present (Colab simple scores low)
        if has_custom_jarvis_model() and thr > recommended_threshold():
            thr = recommended_threshold()
        cd = float(self._wake_cd)
        mode = "hey+custom+STT" if has_custom_jarvis_model() else "hey_jarvis+STT"

        def on_detect() -> None:
            self._ui_queue.put(("wake", None))

        def work() -> None:
            try:
                self._ui_queue.put(
                    (
                        "log",
                        f"[ok] 聽候中 — Jarvis（{mode} thr={thr} CD={cd}s）",
                    )
                )
                run_wake_loop(
                    on_detect,
                    threshold=thr,
                    post_resume_s=cd,
                    stop_event=self._wake_stop,
                    pause_event=self._wake_pause,
                    text_wake=True,
                )
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("log", f"[fail] 聽候錯誤：{exc}"))
                self._ui_queue.put(("wake_off", None))

        self._wake_thread = threading.Thread(target=work, daemon=True, name="jarvis-wake")
        self._wake_thread.start()

    def stop_wake(self, *, join_timeout: float = 2.5) -> None:
        """Stop wake loop, join thread, release mic."""
        self._wake_on = False
        self._wake_stop.set()
        self._wake_pause.set()
        t = self._wake_thread
        if t is not None and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=join_timeout)
        if t is not None and t.is_alive():
            self.append_log("[warn] 聽候線程未及時結束")
        elif t is not None:
            self._wake_thread = None
        self.btn_wake.configure(text="聽候：關")
        self.append_log("[ok] 聽候已關")

    def run(self) -> None:
        """Block on Tk mainloop."""
        self.start_hotkey()
        self.start_tray()
        self.request_show()
        self.set_status("● 就緒（背景運行中）", kind="idle")
        self.append_log("JARVIS Shell 就緒。輸入 open CS2 / 開 Cursor …")
        self.append_log("提示：講 Jarvis → 自動錄音；或撳「語音」／「設定」。")
        cfg = load_settings()
        self.append_log(
            f"[ok] 設定：ASR={cfg.asr_provider} REC={self._record_seconds}s "
            f"CD={self._wake_cd}s"
        )
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
