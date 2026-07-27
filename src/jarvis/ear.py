"""Ear: short mic capture → SenseVoice (local) → text."""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path

# Lazy-loaded SenseVoice model (heavy).
_model = None

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


def _get_model():
    """Load SenseVoiceSmall once (FunASR)."""
    global _model
    if _model is not None:
        return _model
    try:
        from funasr import AutoModel
    except ImportError as exc:
        missing = getattr(exc, "name", None) or str(exc)
        raise RuntimeError(
            f"SenseVoice 依賴唔齊（缺 {missing}）。"
            "請：pip install \"jarvis-pc[ear]\" 同 torch／torchaudio，然後重啟 serve"
        ) from exc

    # ponytail: CPU small model；準度靠 asr_fix + hotwords 補
    _model = AutoModel(
        model="iic/SenseVoiceSmall",
        trust_remote_code=True,
        disable_update=True,
    )
    return _model


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
    model = _get_model()
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


def listen_once(seconds: float = DEFAULT_SECONDS, *, language: str = "yue") -> str:
    """Record then transcribe; deletes temp wav afterwards."""
    path = record_wav(seconds=seconds)
    try:
        return transcribe_wav(path, language=language)
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
