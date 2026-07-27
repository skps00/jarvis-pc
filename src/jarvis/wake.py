"""Wake word: openWakeWord hey_jarvis (edge-trigger, no record loop)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# ~80ms @ 16kHz
_CHUNK = 1280
_SAMPLE_RATE = 16000
DEFAULT_THRESHOLD = 0.55
# Must fall below this before next wake（防分數黏高狂錄）
_REARM_BELOW = 0.25
# After command/mic resume, ignore wakes this long
_POST_RESUME_S = 2.0
_COOLDOWN_S = 1.0

CUSTOM_WAKE_DIR = Path.home() / "AppData" / "Roaming" / "Jarvis" / "wake"


def wake_available() -> bool:
    """True if openwakeword + sounddevice importable."""
    try:
        import openwakeword  # noqa: F401
        import sounddevice  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


def custom_wake_models() -> list[Path]:
    """User-trained ONNX under %APPDATA%\\Jarvis\\wake\\."""
    if not CUSTOM_WAKE_DIR.is_dir():
        return []
    return sorted(CUSTOM_WAKE_DIR.glob("*.onnx"))


def has_custom_jarvis_model() -> bool:
    """True if custom *.onnx stem contains jarvis."""
    for p in custom_wake_models():
        stem = p.stem.lower().replace("-", "_").replace(" ", "_")
        if "jarvis" in stem:
            return True
    return False


def _hey_jarvis_model_paths() -> list[str]:
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


def _wake_model_paths() -> list[str]:
    paths: list[str] = []
    bundled = _hey_jarvis_model_paths()
    if bundled:
        paths.append(bundled[0])
    for p in custom_wake_models():
        s = str(p)
        if s not in paths:
            paths.append(s)
    return paths


def _load_model() -> Any:
    import openwakeword
    from openwakeword.model import Model

    openwakeword.utils.download_models()
    paths = _wake_model_paths()
    if paths:
        return Model(wakeword_models=paths, inference_framework="onnx")
    return Model(inference_framework="onnx")


def _norm_wake_text(text: str) -> str:
    return "".join((text or "").strip().lower().split())


def text_is_wake(text: str) -> bool:
    """True if transcript is a short English wake phrase."""
    compact = _norm_wake_text(text)
    if not compact or len(compact) > 14:
        return False
    for w in ("hey jarvis", "heyjarvis", "jarvis"):
        wn = _norm_wake_text(w)
        if wn and (compact == wn or compact.startswith(wn)):
            return True
    return False


def _jarvis_score(scores: dict[str, Any]) -> float:
    best = 0.0
    for name, score in scores.items():
        nlow = str(name).lower().replace(" ", "_")
        if "jarvis" in nlow:
            best = max(best, float(score))
    return best


def run_wake_loop(
    on_detect: Callable[[], None],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    stop_event: threading.Event | None = None,
    pause_event: threading.Event | None = None,
    text_wake: bool | None = None,
) -> None:
    """
    Stream mic → hey_jarvis → on_detect (edge-triggered).

    After a hit, must see score drop below _REARM_BELOW before next hit.
    """
    _ = text_wake
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
    cool_until = 0.0
    armed = True  # edge: only fire on rising edge after re-arm

    def _fire() -> None:
        nonlocal cool_until, armed
        armed = False
        cool_until = time.time() + _COOLDOWN_S
        pause.set()
        try:
            on_detect()
        except Exception:
            pass

    def _callback(indata, frames, time_info, status) -> None:  # noqa: ARG001
        nonlocal cool_until, armed
        if stop.is_set() or pause.is_set():
            return
        now = time.time()
        if now < cool_until:
            return
        mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
        pcm = (np.clip(mono, -1.0, 1.0) * 32767.0).astype(np.int16)
        try:
            scores = model.predict(pcm)
        except Exception:
            return
        if not scores:
            return
        best = _jarvis_score(scores)
        if best < _REARM_BELOW:
            armed = True
            return
        if armed and best >= threshold:
            _fire()

    while not stop.is_set():
        while pause.is_set() and not stop.is_set():
            time.sleep(0.1)
        if stop.is_set():
            break
        # after command: hold off + require re-arm from low scores
        armed = False
        cool_until = time.time() + _POST_RESUME_S
        time.sleep(0.4)
        if pause.is_set():
            continue
        try:
            with sd.InputStream(
                samplerate=_SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=_CHUNK,
                callback=_callback,
            ):
                while not stop.is_set() and not pause.is_set():
                    time.sleep(0.05)
        except Exception:
            time.sleep(0.75)
