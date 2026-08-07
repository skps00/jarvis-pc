"""TTS: Piper + jgkawell/jarvis (J.A.R.V.I.S. voice, Paul Bettany style).

Usage:
    from jarvis.mouth import speak
    speak("Opening Minecraft, sir.")

Speed／volume／喇叭：設定頁 → 朗讀 TTS。
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

_MODEL_DIR = Path.home() / "AppData" / "Roaming" / "Jarvis" / "models" / "piper"
_ONNX = _MODEL_DIR / "jarvis-high.onnx"
_CFG = _MODEL_DIR / "jarvis-high.onnx.json"

_voice: Any = None
_voice_lock = threading.Lock()
_USE_SETTINGS_DEVICE = object()


def _has_cjk(text: str) -> bool:
    """True if text contains any CJK (Chinese/Japanese/Korean) character."""
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _load() -> Any:
    global _voice
    with _voice_lock:
        if _voice is not None:
            return _voice
        from piper.voice import PiperVoice

        _voice = PiperVoice.load(str(_ONNX), config_path=str(_CFG))
        return _voice


def _tts_params() -> tuple[bool, float, float, int | None]:
    """Return (enabled, length_scale, volume, output_device)."""
    try:
        from jarvis.settings import load_settings

        s = load_settings()
        return (
            bool(s.tts_enabled),
            float(s.tts_length_scale),
            float(s.tts_volume),
            s.tts_output_device,
        )
    except Exception:
        return True, 0.85, 1.6, None


def speak(
    text: str,
    *,
    blocking: bool = False,
    length_scale: float | None = None,
    volume: float | None = None,
    output_device: Any = _USE_SETTINGS_DEVICE,
    force: bool = False,
) -> None:
    """Synthesize and play *text* with Jarvis voice.

    Only ASCII/English text is spoken — CJK is skipped. Speed／volume／speaker
    from Settings unless overridden (settings preview).
    """
    if not text.strip() or _has_cjk(text):
        return
    enabled, ls, vol, out_dev = _tts_params()
    if not enabled and not force:
        return
    if length_scale is not None:
        ls = float(length_scale)
    if volume is not None:
        vol = float(volume)
    if output_device is not _USE_SETTINGS_DEVICE:
        out_dev = output_device

    def _play() -> None:
        try:
            import numpy as np
            import sounddevice as sd
            from piper.config import SynthesisConfig

            voice = _load()
            syn = SynthesisConfig(length_scale=ls, volume=vol)
            chunks = list(voice.synthesize(text, syn_config=syn))
            audio = b"".join(c.audio_int16_bytes for c in chunks)
            a16 = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32767.0
            peak = float(np.max(np.abs(a16))) if a16.size else 0.0
            if peak > 1.0:
                a16 = a16 / peak
            play_kw: dict[str, Any] = {"samplerate": voice.config.sample_rate}
            if out_dev is not None:
                play_kw["device"] = int(out_dev)
            sd.play(a16, **play_kw)
            sd.wait()
        except Exception:
            pass  # TTS is best-effort; never crash the app

    if blocking:
        _play()
    else:
        threading.Thread(target=_play, daemon=True).start()


def available() -> bool:
    """True if the Jarvis voice model files exist."""
    return _ONNX.is_file() and _CFG.is_file()
