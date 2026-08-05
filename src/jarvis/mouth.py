"""TTS: Piper + jgkawell/jarvis (J.A.R.V.I.S. voice, Paul Bettany style).

Usage:
    from jarvis.mouth import speak
    speak("Opening Minecraft, sir.")
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


def speak(text: str, *, blocking: bool = False) -> None:
    """Synthesize and play *text* with Jarvis voice.

    Only ASCII/English text is spoken — CJK (Chinese) input is skipped
    silently, since the Piper jarvis model is English-only and would
    garble it.
    """
    if not text.strip() or _has_cjk(text):
        return

    def _play() -> None:
        try:
            import numpy as np
            import sounddevice as sd

            voice = _load()
            chunks = list(voice.synthesize(text))
            audio = b"".join(c.audio_int16_bytes for c in chunks)
            a16 = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32767.0
            sd.play(a16, samplerate=voice.config.sample_rate)
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
