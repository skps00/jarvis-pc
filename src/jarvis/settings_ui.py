"""Jarvis companion settings (multi-tab).

Tabs: 提醒 · Hermes · 系統 · 進階（Piper／legacy wake／LLM）。
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any

from jarvis.settings import (
    ASR_FUN_ASR,
    ASR_OPENAI_AUDIO,
    ASR_SENSEVOICE,
    HOTKEY_PRESETS,
    LLM_PRESET_CUSTOM,
    LLM_PRESET_DEEPSEEK,
    LLM_PRESET_OLLAMA,
    PRESET_LABELS,
    SETTINGS_DIR,
    SETTINGS_PATH,
    Settings,
    apply_llm_preset,
    hotkey_preset_label,
    list_models,
    load_settings,
    normalize_hotkey,
    preset_from_label,
    probe_connection,
    save_settings,
)

if TYPE_CHECKING:
    pass


def list_input_mics() -> list[tuple[int | None, str]]:
    """Return ``(device_index_or_None, label)`` for Combobox; first = system default."""
    return _list_audio_combo(kind="input")


def list_output_speakers() -> list[tuple[int | None, str]]:
    """Return ``(device_index_or_None, label)`` for speaker Combobox."""
    return _list_audio_combo(kind="output")


def _list_audio_combo(*, kind: str) -> list[tuple[int | None, str]]:
    rows: list[tuple[int | None, str]] = [(None, "（系統預設）")]
    try:
        import sounddevice as sd

        default_pair = sd.default.device
        default_idx = default_pair[0] if kind == "input" else default_pair[1]
        chan_key = (
            "max_input_channels" if kind == "input" else "max_output_channels"
        )
        for i, d in enumerate(sd.query_devices()):
            if int(d.get(chan_key) or 0) <= 0:
                continue
            name = str(d.get("name") or f"device {i}").strip()
            if len(name) > 52:
                name = name[:49] + "…"
            mark = " ★預設" if i == default_idx else ""
            rows.append((i, f"{i}: {name}{mark}"))
    except Exception:
        pass
    return rows


def _pick_device_label(
    rows: list[tuple[int | None, str]], saved: int | None
) -> tuple[str, list[tuple[int | None, str]]]:
    """Match saved index to label; append orphan row if missing."""
    cur_lab = "（系統預設）"
    for idx, lab in rows:
        if saved is None and idx is None:
            return lab, rows
        if saved is not None and idx == int(saved):
            return lab, rows
    if saved is not None:
        orphan = f"{saved}: （裝置已唔見／離線）"
        rows = list(rows) + [(int(saved), orphan)]
        return orphan, rows
    return cur_lab, rows


class SettingsWindow:
    """Settings UI — Alerts / Hermes / System / Advanced."""

    def __init__(self, parent: Any) -> None:
        self.parent = parent
        self.win = tk.Toplevel(parent.root)
        self.win.title("JARVIS companion 設定")
        self.win.geometry("520x560+100+40")
        self.win.minsize(480, 420)
        self.win.transient(parent.root)

        from jarvis.brain import _load_dotenv

        _load_dotenv()
        s = load_settings(force=True)
        self._custom = list(s.custom_models)

        nb = ttk.Notebook(self.win)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._build_alerts_tab(self._add_scroll_tab(nb, "提醒"), s)
        self._build_hermes_tab(self._add_scroll_tab(nb, "Hermes"), s)
        self._build_sys_tab(self._add_scroll_tab(nb, "系統"), s)
        self._build_advanced_tab(self._add_scroll_tab(nb, "進階"), s)

        btn = tk.Frame(self.win)
        btn.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Label(
            btn,
            text=f"存檔 → {SETTINGS_PATH}",
            fg="#666",
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT)
        tk.Button(btn, text="取消", command=self.win.destroy).pack(
            side=tk.RIGHT, padx=4
        )
        tk.Button(btn, text="儲存", command=self._save).pack(side=tk.RIGHT)

        self.win.grab_set()
        self.win.focus_force()

    def _add_scroll_tab(self, nb: ttk.Notebook, title: str) -> tk.Frame:
        outer = tk.Frame(nb)
        nb.add(outer, text=title)
        canvas = tk.Canvas(outer, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, padx=10, pady=8)
        inner.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _stretch(_event=None) -> None:
            canvas.itemconfigure(win_id, width=canvas.winfo_width())

        canvas.bind("<Configure>", _stretch)
        canvas.configure(yscrollcommand=sb.set)

        def _wheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _wheel))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        return inner

    def _hint(self, frm: tk.Frame, row: int, text: str, cols: int = 3) -> int:
        tk.Label(
            frm,
            text=text,
            fg="#666",
            font=("Segoe UI", 8),
            wraplength=500,
            justify="left",
        ).grid(row=row, column=0, columnspan=cols, sticky="w", pady=(0, 6))
        return row + 1

    def _build_llm_section(self, frm: tk.Frame, s: Settings, *, start_row: int = 0) -> int:
        """Legacy Hands-query LLM (buried under 進階). Returns next free row."""
        preset_id = s.llm_preset or LLM_PRESET_DEEPSEEK
        self.var_preset_label = tk.StringVar(
            value=PRESET_LABELS.get(preset_id, PRESET_LABELS[LLM_PRESET_CUSTOM])
        )
        row = start_row
        tk.Label(frm, text="本機 LLM（Hands 歧義／舊 query）", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(12, 4)
        )
        row += 1
        tk.Label(frm, text="供應商").grid(
            row=row, column=0, sticky="w", pady=4
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
        cmb.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        cmb.bind("<<ComboboxSelected>>", self._on_preset)

        self.var_llm_key = tk.StringVar(value=s.llm_api_key)
        self.var_llm_base = tk.StringVar(value=s.llm_base_url)
        self.var_llm_model = tk.StringVar(value=s.llm_model)

        row += 1
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
        return self._hint(
            frm,
            row,
            "對話大腦用 Hermes。呢度只影響本機 Hands 歧義查詢。",
            cols=3,
        )

    def _build_hermes_tab(self, frm: tk.Frame, s: Settings) -> None:
        from jarvis.settings import VOICE_FRONTEND_HERMES

        self.var_hermes = tk.BooleanVar(value=bool(s.hermes_enabled))
        self.var_hermes_trusted = tk.BooleanVar(value=False)
        # default voice frontend; radio lives under 進階
        vf = str(getattr(s, "voice_frontend", None) or VOICE_FRONTEND_HERMES).strip().lower()
        self.var_voice_frontend = tk.StringVar(value=vf or VOICE_FRONTEND_HERMES)

        tk.Label(frm, text="Approve／Trusted", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=4
        )
        tk.Checkbutton(
            frm,
            text="啟用 Hermes bridge（Approve SSE／Trusted）",
            variable=self.var_hermes,
            wraplength=460,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        tk.Checkbutton(
            frm,
            text="Trusted 30 分鐘（儲存生效；開 docker terminal；重開 → Safe）",
            variable=self.var_hermes_trusted,
            wraplength=460,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=2)

        key_path = (
            Path.home() / "AppData" / "Roaming" / "Jarvis" / "hermes_api.key"
        )
        tk.Label(frm, text="本機 Approve", font=("Segoe UI", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=(12, 4)
        )
        tk.Label(
            frm,
            text="127.0.0.1:8642  ·  Yes=once／No=deny",
            font=("Segoe UI", 9),
        ).grid(row=4, column=0, columnspan=2, sticky="w")
        tk.Label(
            frm,
            text=f"API key：{key_path}",
            fg="#666",
            font=("Segoe UI", 8),
            wraplength=460,
            justify="left",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=2)

        bf = tk.Frame(frm)
        bf.grid(row=6, column=0, columnspan=2, sticky="w", pady=8)
        tk.Button(bf, text="開 Hermes 網頁", command=self._open_hermes_dash).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        tk.Button(bf, text="檢測 API", command=self._probe_hermes_api).pack(
            side=tk.LEFT
        )
        self._hint(
            frm,
            7,
            "對話／wake／TTS 喺 Hermes。語音前端（Jarvis OWW）見「進階」。",
            cols=2,
        )

    def _build_alerts_tab(self, frm: tk.Frame, s: Settings) -> None:
        tk.Label(frm, text="桌面語音提醒", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=4
        )
        self.var_alert_voice = tk.BooleanVar(
            value=bool(getattr(s, "alert_voice", True))
        )
        tk.Checkbutton(
            frm,
            text="啟用語音提醒（短英 stub；無 message body）",
            variable=self.var_alert_voice,
        ).grid(row=1, column=0, columnspan=2, sticky="w")
        self.var_alert_discord = tk.BooleanVar(
            value=bool(getattr(s, "alert_discord", True))
        )
        tk.Checkbutton(
            frm,
            text="Discord（任務列未讀↑）",
            variable=self.var_alert_discord,
        ).grid(row=2, column=0, columnspan=2, sticky="w")
        self.var_alert_whatsapp = tk.BooleanVar(
            value=bool(getattr(s, "alert_whatsapp", True))
        )
        tk.Checkbutton(
            frm,
            text="WhatsApp（Toast／閃爍）",
            variable=self.var_alert_whatsapp,
        ).grid(row=3, column=0, columnspan=2, sticky="w")
        self.var_alert_cursor = tk.BooleanVar(
            value=bool(getattr(s, "alert_cursor", True))
        )
        tk.Checkbutton(
            frm,
            text="Cursor（官方 stop hook → 入隊）",
            variable=self.var_alert_cursor,
        ).grid(row=4, column=0, columnspan=2, sticky="w")
        self.var_alert_cursor_watch = tk.BooleanVar(
            value=bool(getattr(s, "alert_cursor_watch", False))
        )
        tk.Checkbutton(
            frm,
            text="Cursor 外望後備（Toast／標題／flash；易誤觸）",
            variable=self.var_alert_cursor_watch,
        ).grid(row=5, column=0, columnspan=2, sticky="w")
        self.var_alert_always = tk.BooleanVar(
            value=bool(getattr(s, "alert_always", True))
        )
        tk.Checkbutton(
            frm,
            text="Always：讀 Windows Toast（前景都提醒）",
            variable=self.var_alert_always,
        ).grid(row=6, column=0, columnspan=2, sticky="w")
        self.var_alert_extra = tk.StringVar(
            value=str(getattr(s, "alert_extra", "") or "")
        )
        tk.Label(frm, text="其他 app").grid(row=7, column=0, sticky="w", pady=2)
        tk.Entry(frm, textvariable=self.var_alert_extra, width=36).grid(
            row=7, column=1, sticky="w", pady=2
        )
        self.var_alert_cd = tk.StringVar(
            value=str(float(getattr(s, "alert_cd_seconds", 0.0)))
        )
        tk.Label(frm, text="冷卻秒（0=關）").grid(row=8, column=0, sticky="w", pady=2)
        tk.Entry(frm, textvariable=self.var_alert_cd, width=8).grid(
            row=8, column=1, sticky="w", pady=2
        )
        self.var_alert_tts = tk.StringVar(
            value=str(getattr(s, "alert_tts", "hermes") or "hermes")
        )
        tk.Label(frm, text="朗讀路徑").grid(row=9, column=0, sticky="w", pady=2)
        ttk.Combobox(
            frm,
            textvariable=self.var_alert_tts,
            values=("hermes", "piper", "off"),
            state="readonly",
            width=12,
        ).grid(row=9, column=1, sticky="w", pady=2)

        bf = tk.Frame(frm)
        bf.grid(row=10, column=0, columnspan=2, sticky="w", pady=8)
        tk.Button(bf, text="試語音提醒", command=self._test_alert).pack(side=tk.LEFT)

        self._hint(
            frm,
            11,
            "Cursor 完：python -m jarvis cursor-hooks install。"
            " hermes＝入隊朗讀；piper＝本機；off＝唔讀。",
            cols=2,
        )
        frm.columnconfigure(1, weight=1)

    def _build_sys_tab(self, frm: tk.Frame, s: Settings) -> None:
        from jarvis import autostart as auto
        from jarvis.config import DEFAULT_PROFILES_PATH

        self.var_hotkey = tk.StringVar(value=hotkey_preset_label(s.hotkey))
        tk.Label(frm, text="熱鍵／自啟", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=4
        )
        labels = [lab for lab, _ in HOTKEY_PRESETS]
        cur = self.var_hotkey.get()
        if cur not in labels:
            labels = [cur, *labels]
        self.cmb_hotkey = ttk.Combobox(
            frm,
            textvariable=self.var_hotkey,
            values=tuple(labels),
            width=28,
        )
        self.cmb_hotkey.grid(row=0, column=1, sticky="w", pady=4)
        tk.Label(
            frm,
            text="顯示／隱藏視窗。可打 Ctrl+Shift+J 或 <ctrl>+<shift>+j",
            fg="#666",
            font=("Segoe UI", 8),
        ).grid(row=1, column=0, columnspan=2, sticky="w")

        self.var_auto = tk.BooleanVar(value=auto.is_enabled())
        tk.Checkbutton(
            frm, text="開機自啟（無黑窗 VBS）", variable=self.var_auto
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=8)

        tk.Label(frm, text="檔案位置", font=("Segoe UI", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=(8, 4)
        )
        paths = tk.Frame(frm)
        paths.grid(row=4, column=0, columnspan=2, sticky="w")
        tk.Button(
            paths,
            text="開設定資料夾",
            command=lambda: self._open_path(SETTINGS_DIR),
        ).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(
            paths,
            text="開 profiles.yaml",
            command=lambda: self._open_path(DEFAULT_PROFILES_PATH),
        ).pack(side=tk.LEFT)

        self._hint(
            frm,
            5,
            f"settings.json：{SETTINGS_PATH}\n"
            f"profiles：{DEFAULT_PROFILES_PATH}\n"
            "桌面捷徑 JARVIS.lnk → companion；對話用 Hermes。",
            cols=2,
        )

    def _build_advanced_tab(self, frm: tk.Frame, s: Settings) -> None:
        from jarvis.mouth import available
        from jarvis.settings import (
            VOICE_FRONTEND_HERMES,
            VOICE_FRONTEND_JARVIS,
        )

        # ensure voice_frontend var exists (Hermes tab also sets it)
        if not hasattr(self, "var_voice_frontend"):
            vf = str(
                getattr(s, "voice_frontend", None) or VOICE_FRONTEND_HERMES
            ).strip().lower()
            self.var_voice_frontend = tk.StringVar(value=vf or VOICE_FRONTEND_HERMES)

        tk.Label(
            frm, text="語音前端（進階）", font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=4)
        vf_row = tk.Frame(frm)
        vf_row.grid(row=1, column=0, columnspan=3, sticky="w")
        tk.Radiobutton(
            vf_row,
            text="Hermes（預設；唔開 Jarvis OWW）",
            variable=self.var_voice_frontend,
            value=VOICE_FRONTEND_HERMES,
        ).pack(anchor="w")
        tk.Radiobutton(
            vf_row,
            text="Jarvis OWW（唔好同 Hermes Voice 一齊開）",
            variable=self.var_voice_frontend,
            value=VOICE_FRONTEND_JARVIS,
        ).pack(anchor="w")
        row = self._hint(
            frm,
            2,
            "正常用 Hermes。淨係要本機聽候先揀 Jarvis。",
            cols=3,
        )

        tk.Label(
            frm, text="Piper 逃生艙（alert_tts=piper）", font=("Segoe UI", 10, "bold")
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(8, 4))
        row += 1
        self.var_tts = tk.BooleanVar(value=bool(s.tts_enabled))
        tk.Checkbutton(
            frm,
            text="啟用本機 Piper（Hands [ok]/舊路徑）",
            variable=self.var_tts,
        ).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1
        status = (
            "模型：已就緒（jarvis-high）"
            if available()
            else "模型：未裝（%APPDATA%\\Jarvis\\models\\piper）"
        )
        tk.Label(frm, text=status, fg="#666", font=("Segoe UI", 8)).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        row += 1
        self.var_tts_speed = tk.DoubleVar(value=float(s.tts_length_scale))
        self.lbl_tts_speed = tk.Label(frm, text="")
        tk.Label(frm, text="語速").grid(row=row, column=0, sticky="w", pady=2)
        tk.Scale(
            frm,
            from_=0.50,
            to=1.50,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            length=220,
            variable=self.var_tts_speed,
            showvalue=0,
            command=self._on_tts_speed,
        ).grid(row=row, column=1, sticky="w", pady=2)
        self.lbl_tts_speed.grid(row=row, column=2, sticky="w")
        self._on_tts_speed(str(self.var_tts_speed.get()))
        row += 1
        self.var_tts_vol = tk.DoubleVar(value=float(s.tts_volume))
        self.lbl_tts_vol = tk.Label(frm, text="")
        tk.Label(frm, text="音量").grid(row=row, column=0, sticky="w", pady=2)
        tk.Scale(
            frm,
            from_=0.30,
            to=3.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=220,
            variable=self.var_tts_vol,
            showvalue=0,
            command=self._on_tts_vol,
        ).grid(row=row, column=1, sticky="w", pady=2)
        self.lbl_tts_vol.grid(row=row, column=2, sticky="w")
        self._on_tts_vol(str(self.var_tts_vol.get()))
        row += 1
        spk_rows = list_output_speakers()
        cur_spk, spk_rows = _pick_device_label(spk_rows, s.tts_output_device)
        self._spk_label_to_id = {lab: idx for idx, lab in spk_rows}
        self.var_tts_spk_label = tk.StringVar(value=cur_spk)
        tk.Label(frm, text="喇叭").grid(row=row, column=0, sticky="w", pady=2)
        self.cmb_spk = ttk.Combobox(
            frm,
            textvariable=self.var_tts_spk_label,
            values=tuple(lab for _idx, lab in spk_rows),
            state="readonly",
            width=40,
        )
        self.cmb_spk.grid(row=row, column=1, columnspan=2, sticky="ew", pady=2)
        row += 1
        bf = tk.Frame(frm)
        bf.grid(row=row, column=1, sticky="w", pady=2)
        tk.Button(bf, text="重新整理喇叭", command=self._refresh_spk_list).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        tk.Button(bf, text="試聽 Piper", command=self._tts_preview).pack(side=tk.LEFT)
        row += 1

        tk.Label(
            frm,
            text="Legacy 聽候／ASR",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(12, 4))
        row += 1
        row = self._hint(
            frm,
            row,
            "voice_frontend=jarvis 先用。預設唔開。",
            cols=3,
        )

        asr_lab = {
            ASR_SENSEVOICE: "SenseVoice（本機，預設）",
            ASR_FUN_ASR: "Fun-ASR-Nano（較準；首次下載慢）",
            ASR_OPENAI_AUDIO: "Cloud openai_audio（MiMo 等）",
        }
        cur_asr = s.asr_provider if s.asr_provider in asr_lab else ASR_SENSEVOICE
        self.var_asr_label = tk.StringVar(value=asr_lab[cur_asr])
        self._asr_label_to_id = {v: k for k, v in asr_lab.items()}
        tk.Label(frm, text="ASR 供應商").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Combobox(
            frm,
            textvariable=self.var_asr_label,
            values=tuple(asr_lab.values()),
            state="readonly",
            width=36,
        ).grid(row=row, column=1, columnspan=2, sticky="w", pady=2)
        row += 1

        self.var_asr_key = tk.StringVar(value=s.asr_api_key)
        self.var_asr_base = tk.StringVar(value=s.asr_base_url)
        self.var_asr_model = tk.StringVar(value=s.asr_model)
        tk.Label(frm, text="ASR API Key").grid(row=row, column=0, sticky="w", pady=2)
        tk.Entry(frm, textvariable=self.var_asr_key, width=36, show="*").grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=2
        )
        row += 1
        tk.Label(frm, text="ASR Base URL").grid(row=row, column=0, sticky="w", pady=2)
        tk.Entry(frm, textvariable=self.var_asr_base, width=36).grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=2
        )
        row += 1
        tk.Label(frm, text="ASR Model").grid(row=row, column=0, sticky="w", pady=2)
        tk.Entry(frm, textvariable=self.var_asr_model, width=36).grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=2
        )
        row += 1

        self.var_wake_th = tk.DoubleVar(value=float(s.wake_threshold))
        self.var_wake_cd = tk.DoubleVar(value=float(s.wake_cd_seconds))
        self.var_rec_sec = tk.DoubleVar(value=float(s.record_seconds))

        tk.Label(frm, text="Wake 門檻").grid(row=row, column=0, sticky="w", pady=2)
        tk.Scale(
            frm,
            from_=0.35,
            to=0.99,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            length=220,
            variable=self.var_wake_th,
        ).grid(row=row, column=1, sticky="w")
        row += 1
        tk.Label(frm, text="聽候 CD（秒）").grid(row=row, column=0, sticky="w", pady=2)
        tk.Scale(
            frm,
            from_=0.5,
            to=30.0,
            resolution=0.5,
            orient=tk.HORIZONTAL,
            length=220,
            variable=self.var_wake_cd,
        ).grid(row=row, column=1, sticky="w")
        row += 1
        tk.Label(frm, text="錄音秒數").grid(row=row, column=0, sticky="w", pady=2)
        tk.Scale(
            frm,
            from_=1.0,
            to=15.0,
            resolution=0.5,
            orient=tk.HORIZONTAL,
            length=220,
            variable=self.var_rec_sec,
        ).grid(row=row, column=1, sticky="w")
        row += 1

        mic_rows = list_input_mics()
        cur_lab, mic_rows = _pick_device_label(mic_rows, s.wake_mic_device)
        self._mic_label_to_id = {lab: idx for idx, lab in mic_rows}
        self.var_wake_mic_label = tk.StringVar(value=cur_lab)
        tk.Label(frm, text="麥克風").grid(row=row, column=0, sticky="w", pady=2)
        self.cmb_mic = ttk.Combobox(
            frm,
            textvariable=self.var_wake_mic_label,
            values=tuple(lab for _idx, lab in mic_rows),
            state="readonly",
            width=48,
        )
        self.cmb_mic.grid(row=row, column=1, columnspan=2, sticky="ew", pady=2)
        row += 1
        tk.Button(frm, text="重新整理清單", command=self._refresh_mic_list).grid(
            row=row, column=1, sticky="w", pady=2
        )
        row += 1
        self.var_text_wake = tk.BooleanVar(value=bool(getattr(s, "text_wake", False)))
        tk.Checkbutton(
            frm,
            text="text-wake（大聲短窗 ASR 當 wake；易誤觸，建議關）",
            variable=self.var_text_wake,
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=2)
        row += 1
        row = self._hint(
            frm,
            row,
            "麥克風：sounddevice 編號。「系統預設」＝唔寫死 device。",
            cols=3,
        )
        self._build_llm_section(frm, s, start_row=row)
        frm.columnconfigure(1, weight=1)

    def _refresh_mic_list(self) -> None:
        mic_rows = list_input_mics()
        self._mic_label_to_id = {lab: idx for idx, lab in mic_rows}
        labels = tuple(lab for _idx, lab in mic_rows)
        self.cmb_mic.configure(values=labels)
        if self.var_wake_mic_label.get() not in labels:
            self.var_wake_mic_label.set(labels[0] if labels else "（系統預設）")

    def _refresh_spk_list(self) -> None:
        spk_rows = list_output_speakers()
        self._spk_label_to_id = {lab: idx for idx, lab in spk_rows}
        labels = tuple(lab for _idx, lab in spk_rows)
        self.cmb_spk.configure(values=labels)
        if self.var_tts_spk_label.get() not in labels:
            self.var_tts_spk_label.set(labels[0] if labels else "（系統預設）")

    def _open_path(self, path: Path) -> None:
        import os

        p = Path(path)
        try:
            if p.is_file():
                os.startfile(str(p))  # noqa: S606
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                if not p.exists():
                    p.mkdir(parents=True, exist_ok=True)
                os.startfile(str(p if p.is_dir() else p.parent))  # noqa: S606
        except OSError as exc:
            messagebox.showerror("開路徑失敗", str(exc), parent=self.win)

    def _open_hermes_dash(self) -> None:
        def work() -> None:
            try:
                from jarvis.hermes_bridge import open_dashboard

                ok, msg = open_dashboard()
            except Exception as exc:  # noqa: BLE001
                ok, msg = False, str(exc)
            self.win.after(
                0,
                lambda: (
                    messagebox.showinfo("Hermes", msg, parent=self.win)
                    if ok
                    else messagebox.showerror("Hermes", msg, parent=self.win)
                ),
            )

        threading.Thread(target=work, daemon=True).start()

    def _probe_hermes_api(self) -> None:
        def work() -> None:
            try:
                from jarvis.hermes_bridge import _api_request, ensure_api_server

                ok, msg = ensure_api_server(wait_sec=20)
                if not ok:
                    raise RuntimeError(msg)
                code, body = _api_request("GET", "/health", timeout=8)
                detail = f"{msg}\nhealth {code}: {body[:200]}"
            except Exception as exc:  # noqa: BLE001
                err = str(exc)
                self.win.after(
                    0,
                    lambda e=err: messagebox.showerror(
                        "Hermes API", e, parent=self.win
                    ),
                )
                return
            self.win.after(
                0,
                lambda d=detail: messagebox.showinfo(
                    "Hermes API", d, parent=self.win
                ),
            )

        threading.Thread(target=work, daemon=True).start()

    def _on_tts_speed(self, raw: str) -> None:
        try:
            v = float(raw)
        except ValueError:
            v = 0.85
        tag = "快" if v < 0.95 else ("慢" if v > 1.05 else "中")
        self.lbl_tts_speed.configure(text=f"{v:.2f}（{tag}）")

    def _on_tts_vol(self, raw: str) -> None:
        try:
            v = float(raw)
        except ValueError:
            v = 1.6
        self.lbl_tts_vol.configure(text=f"{v:.1f}×")

    def _tts_preview(self) -> None:
        from jarvis.mouth import available, speak

        if not available():
            messagebox.showwarning(
                "TTS",
                "未裝 Piper 模型（%APPDATA%\\Jarvis\\models\\piper）",
                parent=self.win,
            )
            return
        speak(
            "Jarvis online. Speed and volume check.",
            blocking=False,
            force=True,
            length_scale=float(self.var_tts_speed.get()),
            volume=float(self.var_tts_vol.get()),
            output_device=self._spk_label_to_id.get(self.var_tts_spk_label.get()),
        )

    def _test_alert(self) -> None:
        """Speak one alert phrase via live shell watcher if present."""
        parent = self.parent
        w = getattr(parent, "_alert_watcher", None)
        if w is not None:
            w.emit_test()
            return
        from jarvis.mouth import available, speak

        if not available():
            messagebox.showwarning("TTS", "未裝 Piper 模型", parent=self.win)
            return
        speak("Alert system ready.", blocking=False, force=True)

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
        self.cmb_llm_model.configure(
            values=self._model_choices(self.var_llm_model.get())
        )

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

    def _list_llm_models(self) -> None:
        self._list_into(
            self.var_llm_base.get(),
            self.var_llm_key.get(),
            self.var_llm_model,
            self.cmb_llm_model,
        )

    def _probe_llm(self) -> None:
        self._run_net(
            "LLM 檢測",
            lambda: probe_connection(
                self.var_llm_base.get(), self.var_llm_key.get()
            ),
        )

    def _run_net(self, title: str, fn) -> None:
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
        preset = preset_from_label(self.var_preset_label.get())
        if preset == LLM_PRESET_OLLAMA and not self.var_llm_key.get().strip():
            self.var_llm_key.set("ollama")

        try:
            hotkey = normalize_hotkey(self.var_hotkey.get())
        except ValueError as exc:
            messagebox.showerror(
                "JARVIS 設定", f"熱鍵無效：{exc}", parent=self.win
            )
            return

        asr_id = self._asr_label_to_id.get(
            self.var_asr_label.get(), ASR_SENSEVOICE
        )
        wake_mic = self._mic_label_to_id.get(self.var_wake_mic_label.get())
        tts_spk = self._spk_label_to_id.get(self.var_tts_spk_label.get())
        try:
            alert_cd = float(self.var_alert_cd.get() or 0.0)
        except ValueError:
            messagebox.showerror(
                "JARVIS 設定", "提醒冷卻秒必須係數字", parent=self.win
            )
            return

        s = Settings(
            asr_provider=asr_id,
            asr_api_key=self.var_asr_key.get().strip(),
            asr_base_url=self.var_asr_base.get().strip(),
            asr_model=self.var_asr_model.get().strip(),
            mimo_api_key=self.var_asr_key.get().strip(),
            mimo_base_url=self.var_asr_base.get().strip(),
            llm_preset=preset,
            llm_api_key=self.var_llm_key.get().strip(),
            llm_base_url=self.var_llm_base.get().strip(),
            llm_model=self.var_llm_model.get().strip(),
            custom_models=list(self._custom),
            wake_threshold=float(self.var_wake_th.get()),
            wake_cd_seconds=float(self.var_wake_cd.get()),
            record_seconds=float(self.var_rec_sec.get()),
            wake_mic_device=wake_mic,
            text_wake=bool(self.var_text_wake.get()),
            hermes_enabled=bool(self.var_hermes.get()),
            hermes_trusted=False,
            voice_frontend=str(self.var_voice_frontend.get() or "hermes"),
            hotkey=hotkey,
            tts_enabled=bool(self.var_tts.get()),
            tts_length_scale=float(self.var_tts_speed.get()),
            tts_volume=float(self.var_tts_vol.get()),
            tts_output_device=tts_spk,
            alert_voice=bool(self.var_alert_voice.get()),
            alert_discord=bool(self.var_alert_discord.get()),
            alert_cursor=bool(self.var_alert_cursor.get()),
            alert_cursor_watch=bool(self.var_alert_cursor_watch.get()),
            alert_whatsapp=bool(self.var_alert_whatsapp.get()),
            alert_always=bool(self.var_alert_always.get()),
            alert_extra=self.var_alert_extra.get().strip(),
            alert_cd_seconds=alert_cd,
            alert_tts=str(self.var_alert_tts.get() or "hermes").strip().lower(),
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
        if bool(self.var_hermes_trusted.get()) and bool(self.var_hermes.get()):
            self.parent.arm_hermes_trusted(minutes=30)
        else:
            self.parent.clear_hermes_trusted()
        self.parent.append_log(f"[ok] 設定已存：{path}")
        if auto_msg:
            self.parent.append_log(f"[ok] {auto_msg}")
        self.win.destroy()
