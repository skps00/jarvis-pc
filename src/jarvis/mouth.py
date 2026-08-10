"""TTS: Piper + jgkawell/jarvis (J.A.R.V.I.S. voice, Paul Bettany style).

Usage:
    from jarvis.mouth import speak
    speak("Opening Minecraft, sir.")

Speed／volume／喇叭：設定頁 → 朗讀 TTS。

If in-process onnxruntime DLL init fails (common after torch／FunASR),
falls back to a short CREATE_NO_WINDOW subprocess.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

_MODEL_DIR = Path.home() / "AppData" / "Roaming" / "Jarvis" / "models" / "piper"
_ONNX = _MODEL_DIR / "jarvis-high.onnx"
_CFG = _MODEL_DIR / "jarvis-high.onnx.json"

_voice: Any = None
_voice_lock = threading.Lock()
_play_lock = threading.Lock()
_USE_SETTINGS_DEVICE = object()
_last_error: str | None = None
_prefer_subprocess = False


def _has_cjk(text: str) -> bool:
    """True if text contains any CJK (Chinese/Japanese/Korean) character."""
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def last_speak_error() -> str | None:
    """Last speak() failure message (if any)."""
    return _last_error


def available() -> bool:
    """True if the Jarvis voice model files exist."""
    return _ONNX.is_file() and _CFG.is_file()


def _load() -> Any:
    global _voice
    with _voice_lock:
        if _voice is not None:
            return _voice
        from piper.voice import PiperVoice

        _voice = PiperVoice.load(str(_ONNX), config_path=str(_CFG))
        return _voice


def warmup() -> tuple[bool, str]:
    """Load Piper on the calling thread (call from Tk main at serve start).

    Returns (ok, note). On DLL failure sets subprocess fallback.
    """
    global _prefer_subprocess, _last_error
    if not available():
        return False, "no piper model"
    try:
        _load()
        # tiny synth to prove ORT works
        from piper.config import SynthesisConfig

        voice = _load()
        list(
            voice.synthesize(
                "ok", syn_config=SynthesisConfig(length_scale=0.85, volume=1.0)
            )
        )
        _prefer_subprocess = False
        return True, "piper ready"
    except Exception as exc:
        _last_error = f"{type(exc).__name__}: {exc}"
        _prefer_subprocess = True
        return False, _last_error


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


def _resample(audio, orig_sr: float, target_sr: float):
    """Linear resample float32 mono (no scipy)."""
    import numpy as np

    if abs(orig_sr - target_sr) < 1.0 or audio.size == 0:
        return audio
    n = max(1, int(round(audio.size * float(target_sr) / float(orig_sr))))
    x_old = np.linspace(0.0, 1.0, num=audio.size, endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=n, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def _play_once(a16, *, samplerate: float, device: int | None) -> None:
    import sounddevice as sd

    sr = float(samplerate)
    play_kw: dict[str, Any] = {"samplerate": sr}
    if device is not None:
        play_kw["device"] = int(device)
        try:
            info = sd.query_devices(int(device))
            target = float(info.get("default_samplerate") or sr)
            a16 = _resample(a16, sr, target)
            play_kw["samplerate"] = target
        except Exception:
            pass
    try:
        sd.stop()
    except Exception:
        pass
    sd.play(a16, **play_kw)
    sd.wait()


def _dll_error(msg: str | None) -> bool:
    m = (msg or "").lower()
    return "dll" in m or "onnxruntime" in m


def _src_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _speak_subprocess(text: str, *, force: bool) -> bool:
    """Play in a fresh interpreter — avoids ORT DLL fights with torch/FunASR."""
    global _last_error
    env = os.environ.copy()
    src = str(_src_root())
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src if not prev else f"{src}{os.pathsep}{prev}"
    # Keep it tiny: child loads settings + piper itself
    force_lit = "True" if force else "False"
    # Escape for double-quoted -c string
    safe = text.replace("\\", "\\\\").replace('"', '\\"')
    code = (
        "from jarvis.mouth import speak, last_speak_error; "
        f"ok=speak(\"{safe}\", blocking=True, force={force_lit}, "
        f"_allow_subprocess=False); "
        "raise SystemExit(0 if ok else 1)"
    )
    flags = 0
    if sys.platform == "win32":
        flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=flags,
        )
        if proc.returncode == 0:
            _last_error = None
            return True
        err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
        _last_error = f"subprocess TTS: {err[:300]}"
        return False
    except Exception as exc:
        _last_error = f"subprocess TTS {type(exc).__name__}: {exc}"
        return False


def speak(
    text: str,
    *,
    blocking: bool = False,
    length_scale: float | None = None,
    volume: float | None = None,
    output_device: Any = _USE_SETTINGS_DEVICE,
    force: bool = False,
    _allow_subprocess: bool = True,
) -> bool:
    """Synthesize and play *text* with Jarvis voice.

    Only ASCII/English text is spoken — CJK is skipped. Speed／volume／speaker
    from Settings unless overridden (settings preview).
    Returns True if playback succeeded.
    """
    global _last_error, _prefer_subprocess
    _last_error = None

    if not text.strip() or _has_cjk(text):
        _last_error = "empty or CJK text"
        return False
    enabled, ls, vol, out_dev = _tts_params()
    if not enabled and not force:
        _last_error = "tts_enabled=false"
        return False
    if length_scale is not None:
        ls = float(length_scale)
    if volume is not None:
        vol = float(volume)
    if output_device is not _USE_SETTINGS_DEVICE:
        out_dev = output_device

    if _prefer_subprocess and _allow_subprocess:
        if blocking:
            return _speak_subprocess(text, force=force)
        threading.Thread(
            target=lambda: _speak_subprocess(text, force=force),
            daemon=True,
        ).start()
        return True

    def _play() -> bool:
        global _last_error, _prefer_subprocess
        with _play_lock:
            try:
                import numpy as np
                from piper.config import SynthesisConfig

                voice = _load()
                syn = SynthesisConfig(length_scale=ls, volume=vol)
                chunks = list(voice.synthesize(text, syn_config=syn))
                audio = b"".join(c.audio_int16_bytes for c in chunks)
                a16 = (
                    np.frombuffer(audio, dtype=np.int16).astype(np.float32)
                    / 32767.0
                )
                peak = float(np.max(np.abs(a16))) if a16.size else 0.0
                if peak > 1.0:
                    a16 = a16 / peak
                sr = float(voice.config.sample_rate)
                try:
                    _play_once(a16, samplerate=sr, device=out_dev)
                    return True
                except Exception as exc1:
                    if out_dev is None:
                        _last_error = f"{type(exc1).__name__}: {exc1}"
                        return False
                    try:
                        _play_once(a16, samplerate=sr, device=None)
                        # Selected speaker failed → system default (log, don't silent-swap)
                        note = (
                            f"TTS device fallback: idx={out_dev} → default "
                            f"({type(exc1).__name__}: {exc1})"
                        )
                        _last_error = note
                        print(f"[mouth] {note}", file=sys.stderr)
                        return True
                    except Exception as exc2:
                        _last_error = (
                            f"device={out_dev} {type(exc1).__name__}: {exc1}"
                            f" | default {type(exc2).__name__}: {exc2}"
                        )
                        return False
            except Exception as exc:
                _last_error = f"{type(exc).__name__}: {exc}"
                if _allow_subprocess and _dll_error(_last_error):
                    _prefer_subprocess = True
                    return _speak_subprocess(text, force=force)
                return False

    if blocking:
        return _play()

    def _bg() -> None:
        _play()

    threading.Thread(target=_bg, daemon=True).start()
    return True
