"""Ear: short mic capture → SenseVoice (local) or MiMo cloud ASR → text."""

from __future__ import annotations

import base64
import json
import tempfile
import urllib.error
import urllib.request
import wave
from pathlib import Path

# Lazy-loaded local ASR models (heavy).
_sensevoice = None
_fun_asr = None
_fun_asr_failed: str | None = None  # sticky fail → always SenseVoice fallback
_FUN_ASR_IDS = (
    "FunAudioLLM/Fun-ASR-Nano-2512",
    "iic/Fun-ASR-Nano-2512",
)
# ponytail: first ModelScope/HF download can hang minutes; don't freeze UI forever
_FUN_ASR_LOAD_TIMEOUT_S = 120.0

# Default listen window — slightly longer helps short Cantonese commands.
DEFAULT_SECONDS = 4.0


def record_wav(seconds: float = DEFAULT_SECONDS, sample_rate: int = 16000) -> Path:
    """
    Record mono PCM from default mic into a temp .wav.

    Requires optional dep: sounddevice.
    """
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "語音依賴未裝：pip install \"jarvis-pc[ear]\" 或 sounddevice numpy"
        ) from exc

    frames = int(seconds * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    pcm = (np.clip(audio.flatten(), -1.0, 1.0) * 32767.0).astype("int16")

    path = Path(tempfile.mkstemp(prefix="jarvis_ear_", suffix=".wav")[1])
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return path


def pcm_to_wav(pcm: "np.ndarray", *, sample_rate: int = 16000) -> Path:
    """Write int16 mono PCM numpy array to a temp .wav.

    Use for pre-captured audio (e.g. from wake loop).
    """
    import numpy as np

    path = Path(tempfile.mkstemp(prefix="jarvis_cmd_", suffix=".wav")[1])
    arr = np.asarray(pcm, dtype=np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(arr.tobytes())
    return path


def _get_sensevoice():
    """Load SenseVoiceSmall once (FunASR)."""
    global _sensevoice
    if _sensevoice is not None:
        return _sensevoice
    try:
        from funasr import AutoModel
    except ImportError as exc:
        missing = getattr(exc, "name", None) or str(exc)
        raise RuntimeError(
            f"SenseVoice 依賴唔齊（缺 {missing}）。"
            "請：pip install \"jarvis-pc[ear]\" 同 torch／torchaudio，然後重啟 serve"
        ) from exc

    # ponytail: CPU small model；準度靠 asr_repair + hotwords 補
    _sensevoice = AutoModel(
        model="iic/SenseVoiceSmall",
        trust_remote_code=True,
        disable_update=True,
    )
    return _sensevoice


def _get_fun_asr():
    """Load Fun-ASR-Nano once (higher-accuracy local; free).

    First download can take minutes; join with timeout so caller can fall back.
    """
    import threading

    global _fun_asr, _fun_asr_failed
    if _fun_asr is not None:
        return _fun_asr
    if _fun_asr_failed:
        raise RuntimeError(_fun_asr_failed)
    try:
        from funasr import AutoModel
    except ImportError as exc:
        missing = getattr(exc, "name", None) or str(exc)
        _fun_asr_failed = f"Fun-ASR 依賴唔齊（缺 {missing}）"
        raise RuntimeError(
            f"{_fun_asr_failed}。請：pip install \"jarvis-pc[ear]\" 同 torch／torchaudio"
        ) from exc

    last_err: Exception | None = None
    for mid in _FUN_ASR_IDS:
        box: dict = {}

        def work(model_id: str = mid) -> None:
            try:
                box["m"] = AutoModel(
                    model=model_id,
                    trust_remote_code=True,
                    disable_update=True,
                )
            except Exception as exc:  # noqa: BLE001
                box["e"] = exc

        th = threading.Thread(target=work, daemon=True, name="jarvis-fun-asr-load")
        th.start()
        th.join(timeout=_FUN_ASR_LOAD_TIMEOUT_S)
        if th.is_alive():
            _fun_asr_failed = (
                f"Fun-ASR 載入逾時（>{_FUN_ASR_LOAD_TIMEOUT_S:.0f}s，{mid}）；"
                "請改設定用 SenseVoice"
            )
            raise TimeoutError(_fun_asr_failed)
        if "m" in box:
            _fun_asr = box["m"]
            return _fun_asr
        last_err = box.get("e")
    _fun_asr_failed = f"Fun-ASR-Nano 載入失敗：{last_err}"
    raise RuntimeError(
        f"{_fun_asr_failed}。可改設定用 SenseVoice。"
    ) from last_err


def _get_model():
    """Back-compat alias → SenseVoice."""
    return _get_sensevoice()


def _strip_sensevoice_tags(text: str) -> str:
    """Remove SenseVoice meta tags like <|yue|> <|NEUTRAL|>."""
    import re

    text = re.sub(r"<\|[^|]*\|>", "", text).strip()
    try:
        from funasr.utils.postprocess_utils import rich_transcription_postprocess

        text = rich_transcription_postprocess(text)
    except Exception:
        pass
    return text.strip()


def _hotword_string(extra: list[str] | None = None) -> str | None:
    """Build a space-separated hotword list from profiles when possible."""
    words: list[str] = [
        "CS",
        "CS2",
        "Cursor",
        "Chrome",
        "Minecraft",
        "開",
        "打開",
        "關",
        "閂",
        "關閉",
        "重開",
        "還原",
    ]
    if extra:
        words.extend(extra)
    # unique, keep order
    seen: set[str] = set()
    out: list[str] = []
    for w in words:
        w = w.strip()
        if len(w) < 2 or w.lower() in seen:
            continue
        seen.add(w.lower())
        out.append(w)
    return " ".join(out) if out else None


def transcribe_wav(
    path: Path,
    *,
    language: str = "yue",
    hotwords: list[str] | None = None,
) -> str:
    """
    Transcribe a wav with SenseVoice.

    language: yue | zh | en | auto …
    """
    model = _get_sensevoice()
    kwargs: dict = {
        "input": str(path),
        "cache": {},
        "language": language,
        "use_itn": True,
        "batch_size_s": 60,
        "ban_emo_unk": True,
    }
    hw = _hotword_string(hotwords)
    if hw:
        # FunASR 部分模型認 hotword / hotwords；唔支援就忽略
        kwargs["hotword"] = hw

    try:
        raw = model.generate(**kwargs)
    except TypeError:
        kwargs.pop("hotword", None)
        kwargs.pop("ban_emo_unk", None)
        raw = model.generate(**kwargs)

    if not raw:
        return ""
    first = raw[0]
    text = first.get("text", "") if isinstance(first, dict) else str(first)
    return _strip_sensevoice_tags(text)


def transcribe_fun_asr(
    path: Path,
    *,
    language: str = "yue",
    hotwords: list[str] | None = None,
) -> str:
    """Transcribe with Fun-ASR-Nano; fall back to SenseVoice on failure."""
    try:
        model = _get_fun_asr()
    except Exception as exc:
        # sticky fail already set inside _get_fun_asr when applicable
        print(f"[ear] Fun-ASR 不可用 → SenseVoice（{exc}）", flush=True)
        return transcribe_wav(path, language=language, hotwords=hotwords)

    kwargs: dict = {
        "input": str(path),
        "cache": {},
        "language": language,
        "use_itn": True,
        "batch_size_s": 60,
    }
    hw = _hotword_string(hotwords)
    if hw:
        kwargs["hotword"] = hw
    try:
        raw = model.generate(**kwargs)
    except TypeError:
        kwargs.pop("hotword", None)
        try:
            raw = model.generate(**kwargs)
        except Exception:
            return transcribe_wav(path, language=language, hotwords=hotwords)
    except Exception:
        return transcribe_wav(path, language=language, hotwords=hotwords)

    if not raw:
        return ""
    first = raw[0]
    text = first.get("text", "") if isinstance(first, dict) else str(first)
    return _strip_sensevoice_tags(text)


def transcribe_mimo(
    path: Path,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    language: str = "auto",
) -> str:
    """Alias for transcribe_openai_audio (legacy name)."""
    return transcribe_openai_audio(
        path, api_key=api_key, base_url=base_url, model=model, language=language
    )


def transcribe_openai_audio(
    path: Path,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    language: str = "auto",
) -> str:
    """
    Transcribe wav via OpenAI-compatible chat/completions + input_audio.

    Used by Xiaomi MiMo ASR and any API with the same shape.
    """
    from jarvis.settings import (
        DEFAULT_ASR_MODEL,
        DEFAULT_MIMO_BASE,
        load_settings,
        openai_chat_url,
    )

    s = load_settings()
    key = (api_key if api_key is not None else s.asr_api_key or s.mimo_api_key).strip()
    if not key:
        raise RuntimeError("未設定 ASR API Key（設定頁）")
    base = (base_url if base_url is not None else s.asr_base_url or s.mimo_base_url).rstrip(
        "/"
    )
    if not base:
        base = DEFAULT_MIMO_BASE
    mid = (model if model is not None else s.asr_model).strip() or DEFAULT_ASR_MODEL
    raw_bytes = Path(path).read_bytes()
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    data_url = f"data:audio/wav;base64,{b64}"
    url = openai_chat_url(base)
    body = {
        "model": mid,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": data_url},
                    }
                ],
            }
        ],
        "asr_options": {"language": language or "auto"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "api-key": key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        raise RuntimeError(f"ASR HTTP {exc.code}: {detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ASR 連線失敗：{exc.reason}") from exc

    choices = payload.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text") or ""))
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts).strip()
    return str(content or "").strip()


def transcribe_path(
    path: Path,
    *,
    language: str = "yue",
    hotwords: list[str] | None = None,
) -> str:
    """Route to SenseVoice / Fun-ASR-Nano / cloud openai_audio per settings."""
    from jarvis.settings import (
        ASR_FUN_ASR,
        ASR_OPENAI_AUDIO,
        load_settings,
        uses_cloud_asr,
    )

    s = load_settings()
    if uses_cloud_asr(s) or s.asr_provider == ASR_OPENAI_AUDIO:
        return transcribe_openai_audio(path, language="auto")
    if s.asr_provider == ASR_FUN_ASR:
        return transcribe_fun_asr(path, language=language, hotwords=hotwords)
    return transcribe_wav(path, language=language, hotwords=hotwords)


def listen_once(seconds: float | None = None, *, language: str = "yue") -> str:
    """Record then transcribe (provider from settings); deletes temp wav."""
    from jarvis.settings import load_settings

    if seconds is None:
        seconds = float(load_settings().record_seconds)
    path = record_wav(seconds=float(seconds))
    try:
        return transcribe_path(path, language=language)
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
