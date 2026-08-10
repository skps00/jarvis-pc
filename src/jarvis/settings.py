"""App settings: %APPDATA%/Jarvis/settings.json (overrides .env)."""

from __future__ import annotations

import json
import os
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
    tts_length_scale: float = 0.85  # <1 faster
    tts_volume: float = 1.6  # 1.0 = Piper default
    tts_output_device: int | None = None  # sounddevice output index; None = default
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


_cache: Settings | None = None


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
    s.wake_threshold = max(0.35, min(0.99, s.wake_threshold))
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
    try:
        s.alerts_mcp_port = int(getattr(s, "alerts_mcp_port", 8765))
    except (TypeError, ValueError):
        s.alerts_mcp_port = 8765
    s.alerts_mcp_port = max(1024, min(65535, s.alerts_mcp_port))
    s.alerts_mcp_token = str(getattr(s, "alerts_mcp_token", "") or "").strip()
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


def _from_dict(data: dict[str, Any]) -> Settings:
    known = {f.name for f in fields(Settings)}
    kwargs = {k: v for k, v in data.items() if k in known}
    if "custom_models" in kwargs and not isinstance(kwargs["custom_models"], list):
        kwargs["custom_models"] = []
    return _clamp(Settings(**kwargs))


def load_settings(*, force: bool = False) -> Settings:
    """
    Load settings.json; seed from env only when file missing.

    Cached in-process; pass force=True after save or external edit.
    """
    global _cache
    if _cache is not None and not force:
        return _cache
    path = SETTINGS_PATH
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                s = _from_dict(raw)
            else:
                s = default_settings()
        except (OSError, json.JSONDecodeError):
            s = default_settings()
    else:
        s = default_settings()
    s = _fill_from_env(s)
    _cache = s
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
    global _cache
    s = _clamp(s)
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(asdict(s), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _cache = s
    return SETTINGS_PATH


def invalidate_settings_cache() -> None:
    """Drop in-process cache (tests / after external write)."""
    global _cache
    _cache = None


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
