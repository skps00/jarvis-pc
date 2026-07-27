"""Wake word: openWakeWord hey_jarvis + STT bare English Jarvis."""

from __future__ import annotations

import tempfile
import threading
import time
import wave
from collections.abc import Callable
from pathlib import Path
from typing import Any

# ~80ms @ 16kHz — openWakeWord recommended frame
_CHUNK = 1280
_SAMPLE_RATE = 16000
DEFAULT_THRESHOLD = 0.50
_PREFERRED = ("hey_jarvis", "hey jarvis")
# 裸英文 Jarvis：短窗 SenseVoice（拷貝 buffer，唔另搶麦）
_TEXT_WAKES = (
    "hey jarvis",
    "heyjarvis",
    "jarvis",
)
_TEXT_FRAMES = int(1.2 * _SAMPLE_RATE / _CHUNK)  # ~1.2s
_RMS_MIN = 0.018


def wake_available() -> bool:
    """True if openwakeword + sounddevice importable."""
    try:
        import openwakeword  # noqa: F401
        import sounddevice  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


def _hey_jarvis_model_paths() -> list[str]:
    """Prefer bundled hey_jarvis ONNX only."""
    import openwakeword

    root = Path(openwakeword.__file__).resolve().parent
    home = Path.home() / ".openWakeWord" / "models"
    candidates = [
        root / "resources" / "models" / "hey_jarvis_v0.1.onnx",
        root / "resources" / "models" / "hey_jarvis.onnx",
        home / "hey_jarvis_v0.1.onnx",
        home / "hey_jarvis.onnx",
    ]
    return [str(p) for p in candidates if p.is_file()]


def _load_model() -> Any:
    """Download models once; load hey_jarvis ONNX when found."""
    import openwakeword
    from openwakeword.model import Model

    openwakeword.utils.download_models()
    paths = _hey_jarvis_model_paths()
    if paths:
        return Model(wakeword_models=paths[:1], inference_framework="onnx")
    return Model(inference_framework="onnx")


def _norm_wake_text(text: str) -> str:
    return "".join((text or "").strip().lower().split())


def text_is_wake(text: str) -> bool:
    """True if transcript contains a wake phrase."""
    compact = _norm_wake_text(text)
    if not compact:
        return False
    for w in _TEXT_WAKES:
        wn = _norm_wake_text(w)
        if wn and wn in compact:
            return True
    return False


def _pcm_to_wav(pcm_int16: Any, path: Path) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(pcm_int16.tobytes())


def run_wake_loop(
    on_detect: Callable[[], None],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    stop_event: threading.Event | None = None,
    pause_event: threading.Event | None = None,
    text_wake: bool = True,
) -> None:
    """
    Stream mic → Hey Jarvis (OWW) and/or bare Jarvis (STT) → on_detect.

    pause_event closes InputStream so command SenseVoice can use the mic.
    """
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError(
            '聽候依賴未裝：pip install "jarvis-pc[wake]"（openwakeword + ear）'
        ) from exc

    stop = stop_event or threading.Event()
    pause = pause_event or threading.Event()
    model = _load_model()
    cool = False
    stt_busy = False
    chunks: list[Any] = []
    lock = threading.Lock()

    def _fire() -> None:
        nonlocal cool
        cool = True
        try:
            on_detect()
        except Exception:
            pass

    def _stt_check(pcm: Any) -> None:
        nonlocal cool, stt_busy
        try:
            from jarvis.ear import transcribe_wav

            path = Path(tempfile.mkstemp(prefix="jarvis_wake_", suffix=".wav")[1])
            try:
                _pcm_to_wav(pcm, path)
                text = transcribe_wav(
                    path, language="en", hotwords=["Jarvis", "Hey Jarvis"]
                )
            finally:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            if (
                text_is_wake(text)
                and not cool
                and not pause.is_set()
                and not stop.is_set()
            ):
                _fire()
        except Exception:
            pass
        finally:
            stt_busy = False

    def _callback(indata, frames, time_info, status) -> None:  # noqa: ARG001
        nonlocal cool, stt_busy, chunks
        if stop.is_set() or pause.is_set():
            return
        mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
        pcm = (np.clip(mono, -1.0, 1.0) * 32767.0).astype(np.int16)

        try:
            scores = model.predict(pcm)
        except Exception:
            scores = None
        if scores:
            best = 0.0
            for name, score in scores.items():
                nlow = str(name).lower().replace(" ", "_")
                if not any(p.replace(" ", "_") in nlow for p in _PREFERRED):
                    continue
                best = max(best, float(score))
            if best >= threshold and not cool:
                _fire()
            elif best < threshold * 0.45:
                cool = False

        if not text_wake or cool or stt_busy:
            return

        rms = float(np.sqrt(np.mean(np.square(mono.astype(np.float64)))))
        flush = None
        with lock:
            if rms >= _RMS_MIN:
                chunks.append(pcm.copy())
                if len(chunks) >= _TEXT_FRAMES:
                    flush = np.concatenate(chunks)
                    chunks = []
            else:
                if len(chunks) >= 5:
                    flush = np.concatenate(chunks)
                chunks = []

        if flush is None:
            return
        stt_busy = True
        threading.Thread(target=_stt_check, args=(flush,), daemon=True).start()

    while not stop.is_set():
        while pause.is_set() and not stop.is_set():
            time.sleep(0.1)
            cool = False
        if stop.is_set():
            break
        chunks = []
        with sd.InputStream(
            samplerate=_SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=_CHUNK,
            callback=_callback,
        ):
            while not stop.is_set() and not pause.is_set():
                time.sleep(0.05)
