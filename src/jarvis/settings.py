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
ASR_OPENAI_AUDIO = "openai_audio"  # chat/completions + input_audio (MiMo 等)
ASR_MIMO = "mimo"  # legacy alias → openai_audio
ASR_PROVIDERS = frozenset({ASR_SENSEVOICE, ASR_OPENAI_AUDIO, ASR_MIMO})

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
    if prov not in (ASR_SENSEVOICE, ASR_OPENAI_AUDIO):
        prov = ASR_SENSEVOICE
    s.asr_provider = prov

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
    return s


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
    if env_asr in (ASR_SENSEVOICE, ASR_OPENAI_AUDIO):
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


def preset_from_label(label: str) -> str:
    """Map UI label back to preset id."""
    for pid, lab in PRESET_LABELS.items():
        if lab == label or pid == label:
            return pid
    return LLM_PRESET_CUSTOM
