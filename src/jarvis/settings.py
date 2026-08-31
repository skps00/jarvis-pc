"""App settings: %APPDATA%/Jarvis/settings.json (overrides .env)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any


SETTINGS_DIR = Path.home() / "AppData" / "Roaming" / "Jarvis"
SETTINGS_PATH = SETTINGS_DIR / "settings.json"

# ASR
ASR_SENSEVOICE = "sensevoice"
ASR_FUN_ASR = "fun_asr"  # Fun-ASR-Nano (optional higher-accuracy local)
ASR_OPENAI_AUDIO = "openai_audio"  # chat/completions + input_audio (MiMo 等)
ASR_MIMO = "mimo"  # legacy alias → openai_audio
ASR_PROVIDERS = frozenset(
    {ASR_SENSEVOICE, ASR_FUN_ASR, ASR_OPENAI_AUDIO, ASR_MIMO}
)

# LLM presets (UI only; stored as base_url + optional preset name)
LLM_PRESET_DEEPSEEK = "deepseek"
LLM_PRESET_MIMO = "mimo"
LLM_PRESET_OLLAMA = "ollama"
LLM_PRESET_CUSTOM = "custom"
LLM_PRESETS = frozenset(
    {LLM_PRESET_DEEPSEEK, LLM_PRESET_MIMO, LLM_PRESET_OLLAMA, LLM_PRESET_CUSTOM}
)

DEFAULT_MIMO_BASE = "https://api.xiaomimimo.com/v1"
DEFAULT_LLM_BASE = "https://api.deepseek.com"
DEFAULT_LLM_MODEL = "deepseek-chat"
DEFAULT_ASR_MODEL = "mimo-v2.5-asr"
DEFAULT_OLLAMA_BASE = "http://127.0.0.1:11434/v1"
DEFAULT_HOTKEY = "<ctrl>+<alt>+j"

# Voice frontend: Hermes owns wake/barge-in; Jarvis = Hands/alerts companion
VOICE_FRONTEND_HERMES = "hermes"
VOICE_FRONTEND_JARVIS = "jarvis"
VOICE_FRONTENDS = frozenset({VOICE_FRONTEND_HERMES, VOICE_FRONTEND_JARVIS})

# Human labels shown in settings (value = pynput GlobalHotKeys string)
HOTKEY_PRESETS: tuple[tuple[str, str], ...] = (
    ("Ctrl+Alt+J", "<ctrl>+<alt>+j"),
    ("Ctrl+Shift+J", "<ctrl>+<shift>+j"),
    ("Ctrl+Alt+Space", "<ctrl>+<alt>+<space>"),
    ("Alt+Shift+J", "<alt>+<shift>+j"),
    ("Ctrl+Alt+`", "<ctrl>+<alt>+`"),
)

PRESET_BASES = {
    LLM_PRESET_DEEPSEEK: DEFAULT_LLM_BASE,
    LLM_PRESET_MIMO: DEFAULT_MIMO_BASE,
    LLM_PRESET_OLLAMA: DEFAULT_OLLAMA_BASE,
}


@dataclass
class Settings:
    """User-editable runtime settings."""

    asr_provider: str = ASR_SENSEVOICE
    asr_api_key: str = ""
    asr_base_url: str = DEFAULT_MIMO_BASE
    asr_model: str = DEFAULT_ASR_MODEL
    # legacy fields kept for migration / older UI code
    mimo_api_key: str = ""
    mimo_base_url: str = DEFAULT_MIMO_BASE

    llm_preset: str = LLM_PRESET_DEEPSEEK
    llm_api_key: str = ""
    llm_base_url: str = DEFAULT_LLM_BASE
    llm_model: str = DEFAULT_LLM_MODEL
    custom_models: list[str] = field(default_factory=list)

    wake_threshold: float = 0.50
    wake_cd_seconds: float = 3.0
    record_seconds: float = 4.0
    wake_mic_device: int | None = None  # None = system default
    text_wake: bool = False  # STT-as-wake; default off (game false fires)
    # Phase 6 A4：speaker gate（聲紋）——係 SK 先醒，其他人講嘢唔觸發
    speaker_gate: bool = True
    speaker_threshold: float = 0.50  # cosine vs voice_profile.npy
    # Phase1: Hermes thin bridge (default off — today's jarvis)
    hermes_enabled: bool = False
    # Trusted flag persisted as preference; shell enforces 30min + restart→Safe
    hermes_trusted: bool = False
    # hermes = companion shell (no Jarvis OWW); jarvis = local wake fallback
    voice_frontend: str = VOICE_FRONTEND_HERMES
    # pynput GlobalHotKeys string, e.g. <ctrl>+<alt>+j
    hotkey: str = DEFAULT_HOTKEY
    # Piper TTS (English SPEAK / ok / fail)
    tts_enabled: bool = True
    tts_ack: bool = True  # D2：收到指令先唸「Yes, Sir.」確認（感知延遲最低）
    tts_length_scale: float = 0.85  # <1 faster
    tts_volume: float = 1.6  # 1.0 = Piper default
    tts_output_device: int | None = None  # sounddevice output index; None = default
    # STT preload: SenseVoice CPU 載入實測 ~3.5GB RAM（2026-08-31）。Default False
    # = lazy load（第一次喚醒先載，慳 RAM）；True = 啟動即預載（首次喚醒快 5-8s）。
    stt_preload: bool = False
    # Phase 6 A3：AEC（聲學迴聲消除）——WASAPI loopback 攞喇叭 reference 濾走自己 TTS /
    # voice call 對方聲，唔誤觸 wake。default off（測試 OK 先開）。
    aec_enabled: bool = False
    aec_reference_device: str = ""  # 空 = 自動揀 TTS output 對應 loopback
    # Voice alerts (Discord unread / Cursor done) — English TTS
    alert_voice: bool = True
    alert_discord: bool = True
    alert_cursor: bool = True
    # Per-source Cursor triggers (master = alert_cursor).
    alert_cursor_hooks: bool = True  # stop / preToolUse → queue
    alert_cursor_toast: bool = True  # Action Center toast (done / needs you)
    alert_cursor_uia: bool = True  # exact UIA "Waiting for approval"
    # Title busy→idle + taskbar flash (noisy; easy false positives).
    alert_cursor_watch: bool = False
    alert_whatsapp: bool = True

    alert_always: bool = True  # Windows Toast（前景都提醒）；Flash 作後備
    # Extra toast app name needles, comma-separated (e.g. "Telegram,Slack")
    alert_extra: str = ""
    alert_cd_seconds: float = 0.0  # 0 = no cooldown between alerts
    # hermes = enqueue for Hermes TTS; piper = local mouth.speak; off = drop
    alert_tts: str = "hermes"
    alerts_mcp_port: int = 8765
    alerts_mcp_token: str = ""  # empty → env / auto file
    # P0: RTX GPU health via nvidia-smi → Hermes (no HUD)
    alert_gpu_health: bool = True
    alert_gpu_poll_s: float = 5.0
    # Mage-VL local vision ("eyes") — lazy ~10GB VRAM; default off
    mage_enabled: bool = False
    mage_prompt_default: str = "Describe this image in detail."
    # F3 (2026-08-29): pycaw voice-call detect failure → fail-closed (mute passive TTS)
    vc_fail_closed: bool = False


_cache: Settings | None = None
_cache_mtime: float = 0.0


def settings_path() -> Path:
    """Path to settings.json."""
    return SETTINGS_PATH


def default_settings() -> Settings:
    """Return defaults (new instance)."""
    return Settings()


def openai_chat_url(base: str) -> str:
    """Build .../chat/completions whether base ends with /v1 or not."""
    b = (base or "").rstrip("/")
    if b.endswith("/v1"):
        return f"{b}/chat/completions"
    return f"{b}/v1/chat/completions"


def openai_models_url(base: str) -> str:
    """Build .../models for OpenAI-compatible list."""
    b = (base or "").rstrip("/")
    if b.endswith("/v1"):
        return f"{b}/models"
    return f"{b}/v1/models"


def ollama_tags_url(base: str) -> str:
    """Ollama native tags endpoint from a /v1 or root base."""
    b = (base or "").rstrip("/")
    if b.endswith("/v1"):
        b = b[:-3].rstrip("/")
    return f"{b}/api/tags"


def _clamp(s: Settings) -> Settings:
    """Normalize / clamp values after load."""
    prov = (s.asr_provider or ASR_SENSEVOICE).strip().lower()
    if prov == ASR_MIMO:
        prov = ASR_OPENAI_AUDIO
    if prov not in (ASR_SENSEVOICE, ASR_FUN_ASR, ASR_OPENAI_AUDIO):
        prov = ASR_SENSEVOICE
    s.asr_provider = prov
    s.text_wake = bool(s.text_wake)

    # migrate legacy mimo_* → asr_*
    if not s.asr_api_key and s.mimo_api_key:
        s.asr_api_key = s.mimo_api_key
    if (not s.asr_base_url or s.asr_base_url == DEFAULT_MIMO_BASE) and s.mimo_base_url:
        s.asr_base_url = s.mimo_base_url
    s.asr_api_key = (s.asr_api_key or "").strip()
    s.asr_base_url = (s.asr_base_url or DEFAULT_MIMO_BASE).rstrip("/")
    s.asr_model = (s.asr_model or DEFAULT_ASR_MODEL).strip() or DEFAULT_ASR_MODEL
    # keep legacy mirrors in sync for older readers
    s.mimo_api_key = s.asr_api_key
    s.mimo_base_url = s.asr_base_url

    preset = (s.llm_preset or LLM_PRESET_CUSTOM).strip().lower()
    if preset not in LLM_PRESETS:
        preset = LLM_PRESET_CUSTOM
    s.llm_preset = preset
    s.llm_base_url = (s.llm_base_url or DEFAULT_LLM_BASE).rstrip("/")
    s.llm_model = (s.llm_model or DEFAULT_LLM_MODEL).strip() or DEFAULT_LLM_MODEL
    s.llm_api_key = (s.llm_api_key or "").strip()

    customs: list[str] = []
    seen: set[str] = set()
    for m in s.custom_models or []:
        name = str(m).strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        customs.append(name)
    s.custom_models = customs

    try:
        s.wake_threshold = float(s.wake_threshold)
    except (TypeError, ValueError):
        s.wake_threshold = 0.50
    s.wake_threshold = max(0.25, min(0.99, s.wake_threshold))
    try:
        s.wake_cd_seconds = float(s.wake_cd_seconds)
    except (TypeError, ValueError):
        s.wake_cd_seconds = 3.0
    s.wake_cd_seconds = max(0.5, min(30.0, s.wake_cd_seconds))
    try:
        s.record_seconds = float(s.record_seconds)
    except (TypeError, ValueError):
        s.record_seconds = 4.0
    s.record_seconds = max(1.0, min(15.0, s.record_seconds))
    if s.wake_mic_device is not None:
        if isinstance(s.wake_mic_device, str):
            s.wake_mic_device = s.wake_mic_device.strip() or None
        else:
            try:
                s.wake_mic_device = int(s.wake_mic_device)
            except (TypeError, ValueError):
                s.wake_mic_device = None
    s.hermes_enabled = bool(s.hermes_enabled)
    s.hermes_trusted = bool(s.hermes_trusted)
    vf = (getattr(s, "voice_frontend", None) or VOICE_FRONTEND_HERMES)
    vf = str(vf).strip().lower()
    if vf not in VOICE_FRONTENDS:
        vf = VOICE_FRONTEND_HERMES
    s.voice_frontend = vf
    try:
        s.hotkey = normalize_hotkey(s.hotkey or DEFAULT_HOTKEY)
    except ValueError:
        s.hotkey = DEFAULT_HOTKEY
    s.tts_enabled = bool(s.tts_enabled)
    s.tts_ack = bool(getattr(s, "tts_ack", True))
    s.stt_preload = bool(getattr(s, "stt_preload", False))
    s.speaker_gate = bool(getattr(s, "speaker_gate", True))
    try:
        s.speaker_threshold = float(getattr(s, "speaker_threshold", 0.50))
    except (TypeError, ValueError):
        s.speaker_threshold = 0.50
    s.speaker_threshold = max(0.10, min(0.99, s.speaker_threshold))
    try:
        s.tts_length_scale = float(s.tts_length_scale)
    except (TypeError, ValueError):
        s.tts_length_scale = 0.85
    s.tts_length_scale = max(0.50, min(1.50, s.tts_length_scale))
    try:
        s.tts_volume = float(s.tts_volume)
    except (TypeError, ValueError):
        s.tts_volume = 1.6
    s.tts_volume = max(0.30, min(3.0, s.tts_volume))
    if s.tts_output_device is not None:
        if isinstance(s.tts_output_device, str):
            s.tts_output_device = s.tts_output_device.strip() or None
        else:
            try:
                s.tts_output_device = int(s.tts_output_device)
            except (TypeError, ValueError):
                s.tts_output_device = None
    s.alert_voice = bool(s.alert_voice)
    s.alert_discord = bool(s.alert_discord)
    s.alert_cursor = bool(s.alert_cursor)
    s.alert_cursor_hooks = bool(getattr(s, "alert_cursor_hooks", True))
    s.alert_cursor_toast = bool(getattr(s, "alert_cursor_toast", True))
    s.alert_cursor_uia = bool(getattr(s, "alert_cursor_uia", True))
    s.alert_cursor_watch = bool(getattr(s, "alert_cursor_watch", False))
    s.alert_whatsapp = bool(getattr(s, "alert_whatsapp", True))

    s.alert_always = bool(getattr(s, "alert_always", True))
    s.alert_extra = str(getattr(s, "alert_extra", "") or "").strip()
    try:
        s.alert_cd_seconds = float(s.alert_cd_seconds)
    except (TypeError, ValueError):
        s.alert_cd_seconds = 0.0
    s.alert_cd_seconds = max(0.0, min(120.0, s.alert_cd_seconds))
    mode = str(getattr(s, "alert_tts", "hermes") or "hermes").strip().lower()
    if mode not in ("hermes", "piper", "off"):
        mode = "hermes"
    s.alert_tts = mode
    s.alert_gpu_health = bool(getattr(s, "alert_gpu_health", True))
    try:
        s.alert_gpu_poll_s = float(getattr(s, "alert_gpu_poll_s", 5.0))
    except (TypeError, ValueError):
        s.alert_gpu_poll_s = 5.0
    s.alert_gpu_poll_s = max(2.0, min(60.0, s.alert_gpu_poll_s))
    try:
        s.alerts_mcp_port = int(getattr(s, "alerts_mcp_port", 8765))
    except (TypeError, ValueError):
        s.alerts_mcp_port = 8765
    s.alerts_mcp_port = max(1024, min(65535, s.alerts_mcp_port))
    s.alerts_mcp_token = str(getattr(s, "alerts_mcp_token", "") or "").strip()
    if isinstance(s.aec_enabled, str):
        s.aec_enabled = s.aec_enabled.lower() not in ("0", "false", "off", "no", "")
    else:
        s.aec_enabled = bool(s.aec_enabled)
    s.aec_reference_device = str(getattr(s, "aec_reference_device", "") or "").strip()
    s.mage_enabled = bool(getattr(s, "mage_enabled", False))
    s.mage_prompt_default = (
        str(
            getattr(s, "mage_prompt_default", "Describe this image in detail.")
            or "Describe this image in detail."
        ).strip()
        or "Describe this image in detail."
    )
    s.vc_fail_closed = bool(getattr(s, "vc_fail_closed", False))
    return s


def normalize_hotkey(raw: str) -> str:
    """Accept ``Ctrl+Alt+J`` or ``<ctrl>+<alt>+j`` → pynput string.

    Raises ValueError if empty / no key.
    """
    import re

    s = (raw or "").strip()
    if not s:
        raise ValueError("熱鍵空白")

    # Already pynput-ish
    if "<" in s:
        parts = [p.strip().lower() for p in s.split("+") if p.strip()]
    else:
        parts = [p.strip().lower() for p in re.split(r"[+\-]", s) if p.strip()]

    if not parts:
        raise ValueError("熱鍵無效")

    mod_map = {
        "ctrl": "<ctrl>",
        "control": "<ctrl>",
        "alt": "<alt>",
        "shift": "<shift>",
        "win": "<cmd>",
        "cmd": "<cmd>",
        "super": "<cmd>",
        "meta": "<cmd>",
    }
    special = {
        "space": "<space>",
        "esc": "<esc>",
        "escape": "<esc>",
        "tab": "<tab>",
        "enter": "<enter>",
        "return": "<enter>",
    }
    out: list[str] = []
    for p in parts:
        if p in mod_map:
            out.append(mod_map[p])
            continue
        bare = p.strip("<>")
        if bare in mod_map:
            out.append(mod_map[bare])
            continue
        if p in special or bare in special:
            out.append(special.get(p) or special[bare])
            continue
        if p.startswith("<") and p.endswith(">"):
            out.append(p)
            continue
        # single char key
        if len(bare) == 1:
            out.append(bare)
            continue
        raise ValueError(f"唔識熱鍵段：{p}")

    mods_only = {"<ctrl>", "<alt>", "<shift>", "<cmd>"}
    if all(x in mods_only for x in out):
        raise ValueError("熱鍵要有實體鍵（唔可以淨係修飾鍵）")

    # dedupe mods keep order
    seen: set[str] = set()
    norm: list[str] = []
    for x in out:
        if x in mods_only and x in seen:
            continue
        seen.add(x)
        norm.append(x)
    return "+".join(norm)


def hotkey_display(pynput_hk: str) -> str:
    """``<ctrl>+<alt>+j`` → ``Ctrl+Alt+J``."""
    try:
        hk = normalize_hotkey(pynput_hk)
    except ValueError:
        return pynput_hk
    labels = {
        "<ctrl>": "Ctrl",
        "<alt>": "Alt",
        "<shift>": "Shift",
        "<cmd>": "Win",
        "<space>": "Space",
        "<esc>": "Esc",
        "<tab>": "Tab",
        "<enter>": "Enter",
    }
    bits: list[str] = []
    for p in hk.split("+"):
        if p in labels:
            bits.append(labels[p])
        elif p.startswith("<") and p.endswith(">"):
            bits.append(p[1:-1].title())
        else:
            bits.append(p.upper() if len(p) == 1 else p)
    return "+".join(bits)


def hotkey_preset_label(pynput_hk: str) -> str:
    """Match preset label or return display form."""
    try:
        hk = normalize_hotkey(pynput_hk)
    except ValueError:
        return hotkey_display(pynput_hk)
    for label, val in HOTKEY_PRESETS:
        if val == hk:
            return label
    return hotkey_display(hk)


# ---- H4 (2026-08-29): DPAPI-encrypt secrets at rest ----
# Only pure API keys consumed by this process are encrypted. Cross-process bearer
# tokens (alerts MCP token, Hermes bridge key) stay plaintext because every reader
# would need to decrypt — see docs/hermes_bridge_auth_rotation.md.

_SECRET_FIELDS: frozenset[str] = frozenset(
    {"llm_api_key", "asr_api_key", "mimo_api_key"}
)


def _decrypt_dict(raw: dict[str, Any]) -> dict[str, Any]:
    from jarvis.dpapi import decrypt_secret

    return {
        k: (decrypt_secret(str(v)) if k in _SECRET_FIELDS else v)
        for k, v in raw.items()
    }


def _encrypt_dict(merged: dict[str, Any]) -> dict[str, Any]:
    from jarvis.dpapi import encrypt_secret

    return {
        k: (encrypt_secret(str(v)) if k in _SECRET_FIELDS else v)
        for k, v in merged.items()
    }


def _from_dict(data: dict[str, Any]) -> Settings:
    known = {f.name for f in fields(Settings)}
    kwargs = {k: v for k, v in data.items() if k in known}
    if "custom_models" in kwargs and not isinstance(kwargs["custom_models"], list):
        kwargs["custom_models"] = []
    return _clamp(Settings(**kwargs))


def load_settings(*, force: bool = False) -> Settings:
    """
    Load settings.json; seed from env only when file missing.

    Cached in-process; invalidated when settings.json mtime changes
    (e.g. Electron main.js writes directly). Pass force=True to re-read.
    """
    global _cache, _cache_mtime
    path = SETTINGS_PATH
    mtime = 0.0
    if path.is_file():
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0.0
    if _cache is not None and not force and mtime == _cache_mtime:
        return _cache
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                raw = _decrypt_dict(raw)  # H4: decrypt dpapi: secrets on read
                s = _from_dict(raw)
            else:
                s = default_settings()
        except (OSError, json.JSONDecodeError):
            s = default_settings()
    else:
        s = default_settings()
    s = _fill_from_env(s)
    _cache = s
    _cache_mtime = mtime
    return s


def _fill_from_env(s: Settings) -> Settings:
    """If no settings.json yet, seed from env (compat with .env installs)."""
    if SETTINGS_PATH.is_file():
        return _clamp(s)
    if not s.llm_api_key:
        s.llm_api_key = (
            os.environ.get("JARVIS_LLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        ).strip()
    env_base = (os.environ.get("JARVIS_LLM_BASE_URL") or "").strip().rstrip("/")
    if env_base:
        s.llm_base_url = env_base
    env_model = (os.environ.get("JARVIS_LLM_MODEL") or "").strip()
    if env_model:
        s.llm_model = env_model
    env_asr = (os.environ.get("JARVIS_ASR_PROVIDER") or "").strip().lower()
    if env_asr == ASR_MIMO:
        env_asr = ASR_OPENAI_AUDIO
    if env_asr in (ASR_SENSEVOICE, ASR_FUN_ASR, ASR_OPENAI_AUDIO):
        s.asr_provider = env_asr
    env_asr_base = (
        os.environ.get("JARVIS_ASR_BASE_URL")
        or os.environ.get("MIMO_BASE_URL")
        or os.environ.get("JARVIS_MIMO_BASE_URL")
        or ""
    ).strip().rstrip("/")
    if env_asr_base:
        s.asr_base_url = env_asr_base
    if not s.asr_api_key:
        s.asr_api_key = (
            os.environ.get("JARVIS_ASR_API_KEY")
            or os.environ.get("MIMO_API_KEY")
            or os.environ.get("JARVIS_MIMO_API_KEY")
            or ""
        ).strip()
    env_asr_model = (os.environ.get("JARVIS_ASR_MODEL") or "").strip()
    if env_asr_model:
        s.asr_model = env_asr_model
    return _clamp(s)


def save_settings(s: Settings) -> Path:
    """Write settings.json and refresh cache."""
    global _cache, _cache_mtime
    s = _clamp(s)
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if SETTINGS_PATH.is_file():
        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                existing = raw
        except (OSError, json.JSONDecodeError):
            pass
    merged = {**existing, **asdict(s)}
    merged = _encrypt_dict(merged)  # H4: encrypt secrets at rest
    SETTINGS_PATH.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _cache = s
    try:
        _cache_mtime = os.path.getmtime(SETTINGS_PATH)
    except OSError:
        _cache_mtime = 0.0
    return SETTINGS_PATH


def invalidate_settings_cache() -> None:
    """Drop in-process cache (tests / after external write)."""
    global _cache, _cache_mtime
    _cache = None
    _cache_mtime = 0.0


# ---- H2 (2026-08-29): single-writer settings patch (dir-lock + atomic + pending-apply) ----

_PATCH_LOCK: Path | None = None
_pending_apply: dict[str, Any] | None = None


def _patch_lock_path() -> Path:
    global _PATCH_LOCK
    if _PATCH_LOCK is None:
        _PATCH_LOCK = SETTINGS_DIR / ".settings.lockdir"
    return _PATCH_LOCK


def save_settings_patch(patch: dict[str, Any]) -> dict[str, Any]:
    """Single-writer settings update: dir-lock + merge + atomic replace + pending-apply.

    Cross-process safe — Electron (HTTP), self-monitor, and any sidecar code all
    route settings writes through here, so concurrent writers can't lose keys.
    Returns the merged dict written to disk.
    """
    global _cache, _cache_mtime, _pending_apply
    patch = dict(patch or {})
    lock = _patch_lock_path()
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + 5.0
    while True:
        try:
            lock.mkdir(exist_ok=False)
            break
        except FileExistsError:
            if time.time() > deadline:
                try:
                    lock.rmdir()
                except OSError:
                    pass
                continue
            time.sleep(0.02)
    try:
        existing: dict[str, Any] = {}
        if SETTINGS_PATH.is_file():
            try:
                raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    existing = raw
            except (OSError, json.JSONDecodeError):
                pass
        merged = {**existing, **patch}
        # Clamp only the patched fields using the same rules as _clamp() —
        # do NOT overwrite the patch with stale load_settings() values.
        try:
            from dataclasses import replace

            base = load_settings()
            s2 = _clamp(
                replace(base, **{k: v for k, v in merged.items() if hasattr(base, k)})
            )
            for k in list(merged.keys()):
                if hasattr(s2, k):
                    merged[k] = getattr(s2, k)
        except Exception:  # noqa: BLE001
            pass
        merged = _encrypt_dict(merged)  # H4: encrypt secrets at rest
        tmp = SETTINGS_PATH.with_suffix(SETTINGS_PATH.suffix + ".tmp")
        tmp.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        tmp.replace(SETTINGS_PATH)
        try:
            s = load_settings()
            _cache = s
            _cache_mtime = os.path.getmtime(SETTINGS_PATH)
        except Exception:  # noqa: BLE001
            invalidate_settings_cache()
        _pending_apply = dict(patch)
        return merged
    finally:
        try:
            lock.rmdir()
        except OSError:
            pass


def consume_pending_apply() -> dict[str, Any] | None:
    """Pop the pending-apply patch so sidecar can reload live values (e.g. wake_threshold)."""
    global _pending_apply
    p = _pending_apply
    _pending_apply = None
    return p


def apply_llm_preset(s: Settings, preset: str) -> Settings:
    """Set llm_preset and default base_url for known presets."""
    p = (preset or LLM_PRESET_CUSTOM).strip().lower()
    if p not in LLM_PRESETS:
        p = LLM_PRESET_CUSTOM
    s.llm_preset = p
    if p in PRESET_BASES:
        s.llm_base_url = PRESET_BASES[p]
    if p == LLM_PRESET_OLLAMA and not s.llm_api_key:
        s.llm_api_key = "ollama"  # many clients require non-empty
    if p == LLM_PRESET_DEEPSEEK and s.llm_model in ("", DEFAULT_ASR_MODEL):
        s.llm_model = DEFAULT_LLM_MODEL
    return _clamp(s)


def list_models(base_url: str, api_key: str = "") -> list[str]:
    """
    List model ids for an API key / endpoint.

    Tries OpenAI GET /v1/models, then Ollama GET /api/tags.
    """
    base = (base_url or "").strip()
    if not base:
        raise RuntimeError("未填 Base URL")
    key = (api_key or "").strip()
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
        headers["api-key"] = key

    errors: list[str] = []

    # 1) OpenAI-compatible /models
    try:
        req = urllib.request.Request(
            openai_models_url(base), headers=headers, method="GET"
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        ids = _parse_openai_models(payload)
        if ids:
            return ids
        errors.append("/models 回傳空列表")
    except urllib.error.HTTPError as exc:
        errors.append(f"/models HTTP {exc.code}")
    except urllib.error.URLError as exc:
        errors.append(f"/models 連線失敗：{exc.reason}")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        errors.append(f"/models 解析失敗：{exc}")

    # 2) Ollama /api/tags
    try:
        req = urllib.request.Request(ollama_tags_url(base), method="GET")
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        ids = _parse_ollama_tags(payload)
        if ids:
            return ids
        errors.append("/api/tags 回傳空列表")
    except urllib.error.HTTPError as exc:
        errors.append(f"/api/tags HTTP {exc.code}")
    except urllib.error.URLError as exc:
        errors.append(f"/api/tags 連線失敗：{exc.reason}")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        errors.append(f"/api/tags 解析失敗：{exc}")

    raise RuntimeError("列唔到模型：" + "；".join(errors))


def _parse_openai_models(payload: Any) -> list[str]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        mid = str(item.get("id") or "").strip()
        if mid and mid.lower() not in seen:
            seen.add(mid.lower())
            out.append(mid)
    return sorted(out, key=str.lower)


def _parse_ollama_tags(payload: Any) -> list[str]:
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in models:
        if not isinstance(item, dict):
            continue
        mid = str(item.get("name") or item.get("model") or "").strip()
        if mid and mid.lower() not in seen:
            seen.add(mid.lower())
            out.append(mid)
    return sorted(out, key=str.lower)


def uses_cloud_asr(s: Settings | None = None) -> bool:
    """True when ASR goes through openai_audio HTTP."""
    cfg = s or load_settings()
    return cfg.asr_provider == ASR_OPENAI_AUDIO


def uses_hermes_voice_frontend(s: Settings | None = None) -> bool:
    """True when Hermes owns mic wake (Jarvis OWW should stay off)."""
    cfg = s or load_settings()
    return (
        str(getattr(cfg, "voice_frontend", VOICE_FRONTEND_HERMES) or "")
        .strip()
        .lower()
        == VOICE_FRONTEND_HERMES
    )


def probe_connection(base_url: str, api_key: str = "") -> str:
    """
    Health-check endpoint (OpenClaw/Cherry style).

    Success = list_models returns ≥1 id. Returns short OK message or raises.
    """
    ids = list_models(base_url, api_key)
    sample = ", ".join(ids[:5])
    more = f"…共 {len(ids)}" if len(ids) > 5 else f"共 {len(ids)}"
    return f"連線 OK — {more}：{sample}"


PRESET_LABELS = {
    LLM_PRESET_DEEPSEEK: "DeepSeek",
    LLM_PRESET_MIMO: "小米 MiMo",
    LLM_PRESET_OLLAMA: "Ollama（本機）",
    LLM_PRESET_CUSTOM: "自訂 OpenAI 相容",
}


def list_input_devices() -> list[tuple[int, str]]:
    """Return [(id, name), ...] for all host input devices. Empty list on failure."""
    try:
        import sounddevice as sd
    except ImportError:
        return []
    try:
        return [
            (idx, dev["name"])
            for idx, dev in enumerate(sd.query_devices())
            if dev["max_input_channels"] > 0
        ]
    except Exception:
        return []


def list_output_devices() -> list[tuple[int, str]]:
    """Return [(id, name), ...] for host output (speaker) devices."""
    try:
        import sounddevice as sd
    except ImportError:
        return []
    try:
        return [
            (idx, dev["name"])
            for idx, dev in enumerate(sd.query_devices())
            if int(dev.get("max_output_channels") or 0) > 0
        ]
    except Exception:
        return []


def preset_from_label(label: str) -> str:
    """Map UI label back to preset id."""
    for pid, lab in PRESET_LABELS.items():
        if lab == label or pid == label:
            return pid
    return LLM_PRESET_CUSTOM
