"""Wake word: openWakeWord + optional short STT fallback for bare Jarvis."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# ~80ms @ 16kHz
_CHUNK = 1280
_SAMPLE_RATE = 16000
DEFAULT_THRESHOLD = 0.58
# Soft default when user has custom jarvis.onnx (Colab simple models score low)
CUSTOM_DEFAULT_THRESHOLD = 0.35
# Must fall below this before next wake（防分數黏高狂錄）
_REARM_BELOW = 0.22
# After command/mic resume, ignore wakes this long
_POST_RESUME_S = 2.0
_COOLDOWN_S = 1.0
# STT text-wake: loud enough + cooldown between ASR probes
_RMS_GATE = 0.06  # ignore quiet game bleed for STT schedule
_STT_SECONDS = 2.0  # ring buffer length
_STT_COOLDOWN_S = 2.5
_LOUD_FRAMES_NEED = 4  # ~320ms
_STT_TRAIL_S = 0.65  # keep buffering after loud so word not cut off
_BUF_CHUNKS = max(8, int(_STT_SECONDS * _SAMPLE_RATE / _CHUNK))
_WAKE_DEBUG_LOG = Path.home() / "AppData" / "Roaming" / "Jarvis" / "wake_debug.log"

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


def recommended_threshold() -> float:
    """Default thr: softer when custom jarvis onnx present."""
    if has_custom_jarvis_model():
        return CUSTOM_DEFAULT_THRESHOLD
    return DEFAULT_THRESHOLD


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
    """Bundled hey_jarvis + any custom *.onnx (Hey Jarvis must keep working)."""
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


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein distance (short strings only)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (ca != cb)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


def text_is_wake(text: str) -> bool:
    """True if transcript is a short wake phrase (EN + SenseVoice mangling)."""
    import re

    compact = _norm_wake_text(text)
    if not compact or len(compact) > 22:
        return False
    needles = (
        "heyjarvis",
        "jarvis",
        "javis",
        "jarvi",
        "賈維斯",
        "加維斯",
        "driverss",
        "drivers",
        "drivefus",
        "draaws",
        "draaw",
        "daws",
        "drawfirst",
        "dawfirst",
    )
    for n in needles:
        if n in compact:
            return True
    if compact in ("daw", "daws", "draw", "draws"):
        return True
    if compact.startswith("he") and any(
        x in compact for x in ("jo", "jar", "driv", "daw", "draw")
    ):
        return True
    # fuzzy tokens vs jarvis / drivers (SenseVoice EN mangling)
    for tok in re.findall(r"[a-z]+", compact):
        if len(tok) >= 5 and _edit_distance(tok, "jarvis") <= 2:
            return True
        if len(tok) >= 5 and _edit_distance(tok, "drivers") <= 2:
            return True
    return False


def _wake_debug(msg: str) -> None:
    """Append debug line + one-line human status (pythonw has no console)."""
    try:
        _WAKE_DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        line = f"{time.strftime('%H:%M:%S')} {msg}\n"
        with _WAKE_DEBUG_LOG.open("a", encoding="utf-8") as f:
            f.write(line)
        status = _WAKE_DEBUG_LOG.with_name("wake_status.txt")
        brief = msg
        if msg.startswith("oww_fire") or msg.startswith("stt_fire"):
            brief = "OK: wake fired — speak your command now"
        elif "stt_wake" in msg and "ok=True" in msg:
            brief = "OK: Jarvis (STT) matched"
        elif "stt_wake" in msg and "ok=False" in msg:
            brief = f"MISS STT: {msg}"
        elif msg.startswith("wake_loop_start"):
            brief = "Listening… Hey Jarvis (OWW) or Jarvis (STT-en)"
        elif msg.startswith("dispatch_on_detect"):
            brief = "OK: starting command recording"
        status.write_text(brief + "\n", encoding="utf-8")
    except OSError:
        pass


def _jarvis_score(scores: dict[str, Any]) -> float:
    best = 0.0
    for name, score in scores.items():
        nlow = str(name).lower().replace(" ", "_")
        if "jarvis" in nlow:
            best = max(best, float(score))
    return best


def _pcm_chunks_to_wav(chunks: list[Any]) -> Path:
    """Write int16 mono chunks to a temp wav."""
    import tempfile
    import wave

    import numpy as np

    if not chunks:
        pcm = np.zeros(0, dtype=np.int16)
    else:
        pcm = np.concatenate(chunks)
    path = Path(tempfile.mkstemp(prefix="jarvis_wake_", suffix=".wav")[1])
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return path


def _try_stt_wake_pcm(chunks: list[Any] | None) -> bool:
    """
    Transcribe recent mic ring-buffer; True if wake phrase.

    Tries English first (bare ``Jarvis``), then Cantonese — SenseVoice ``yue``
    alone often garbes English into unrelated Chinese.
    """
    if not chunks:
        _wake_debug("stt_wake empty_buffer")
        return False
    path = None
    try:
        from jarvis.ear import transcribe_path, transcribe_wav
        from jarvis.settings import load_settings, uses_cloud_asr

        path = _pcm_chunks_to_wav(chunks)
        hot = ["Jarvis", "hey jarvis", "jarvis", "賈維斯"]
        s = load_settings()
        attempts: list[tuple[str, str]] = []
        if uses_cloud_asr(s):
            attempts.append(
                ("cloud", transcribe_path(path, language="auto", hotwords=hot))
            )
        else:
            for lang in ("en", "yue"):
                attempts.append(
                    (lang, transcribe_wav(path, language=lang, hotwords=hot))
                )
        for tag, text in attempts:
            ok = text_is_wake(text)
            _wake_debug(f"stt_wake {tag} text={text!r} ok={ok} chunks={len(chunks)}")
            if ok:
                return True
        return False
    except Exception as exc:
        _wake_debug(f"stt_wake_fail {exc}")
        return False
    finally:
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


def run_wake_loop(
    on_detect: Callable[[], None],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    post_resume_s: float | None = None,
    stop_event: threading.Event | None = None,
    pause_event: threading.Event | None = None,
    text_wake: bool | None = None,
) -> None:
    """
    Stream mic → OWW (custom jarvis and/or hey_jarvis) → on_detect.

    Hybrid: if OWW score stays low but mic is loud, STT the recent ring
    buffer for bare ``Jarvis`` / ``hey jarvis`` (default on).
    """
    from collections import deque

    use_text = True if text_wake is None else bool(text_wake)
    resume_s = float(_POST_RESUME_S if post_resume_s is None else post_resume_s)
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
    _wake_debug(f"wake_loop_start paths={_wake_model_paths()} thr={threshold}")
    cool_until = 0.0
    armed = True
    stt_pending = threading.Event()
    fire_pending = threading.Event()
    loud_frames = 0
    last_stt = 0.0
    stt_due = 0.0
    pcm_ring: deque[Any] = deque(maxlen=_BUF_CHUNKS)
    pcm_lock = threading.Lock()
    stt_snapshot: list[Any] = []

    def _trip(reason: str) -> None:
        """Signal wake hit; on_detect runs only after mic stream closes."""
        nonlocal cool_until, armed, loud_frames, stt_due
        armed = False
        loud_frames = 0
        stt_due = 0.0
        stt_pending.clear()
        cool_until = time.time() + _COOLDOWN_S
        pause.set()
        fire_pending.set()
        _wake_debug(reason)

    def _dispatch_detect() -> None:
        time.sleep(0.25)  # let WASAPI release before command record
        _wake_debug("dispatch_on_detect")
        try:
            on_detect()
        except Exception as exc:
            _wake_debug(f"on_detect_fail {exc}")

    def _callback(indata, frames, time_info, status) -> None:  # noqa: ARG001
        nonlocal cool_until, armed, loud_frames, stt_due, stt_snapshot
        if stop.is_set() or pause.is_set() or stt_pending.is_set() or fire_pending.is_set():
            return
        now = time.time()
        if now < cool_until:
            return
        mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
        rms = float(np.sqrt(np.mean(np.square(mono))))
        pcm = (np.clip(mono, -1.0, 1.0) * 32767.0).astype(np.int16)
        with pcm_lock:
            pcm_ring.append(pcm.copy())
        try:
            scores = model.predict(pcm)
        except Exception:
            return
        if not scores:
            return
        best = _jarvis_score(scores)
        if best < _REARM_BELOW:
            armed = True
        if armed and best >= threshold:
            _trip(
                f"oww_fire best={best:.3f} thr={threshold} "
                f"hey={float(scores.get('hey_jarvis_v0.1', 0)):.3f} "
                f"jarvis={float(scores.get('jarvis', 0)):.3f}"
            )
            return
        if not use_text or not armed:
            return
        if rms >= _RMS_GATE:
            loud_frames += 1
        else:
            loud_frames = 0
        if (
            loud_frames >= _LOUD_FRAMES_NEED
            and stt_due <= 0
            and now >= last_stt + _STT_COOLDOWN_S
            and best < threshold
        ):
            stt_due = now + _STT_TRAIL_S
            _wake_debug(f"stt_scheduled rms={rms:.3f} oww={best:.3f}")
        if stt_due > 0 and now >= stt_due:
            with pcm_lock:
                stt_snapshot = list(pcm_ring)
            stt_due = 0.0
            loud_frames = 0
            _wake_debug(f"stt_pending buf={len(stt_snapshot)}")
            stt_pending.set()

    while not stop.is_set():
        while pause.is_set() and not stop.is_set():
            time.sleep(0.1)
        if stop.is_set():
            break
        armed = False
        loud_frames = 0
        stt_due = 0.0
        stt_pending.clear()
        fire_pending.clear()
        with pcm_lock:
            pcm_ring.clear()
        cool_until = time.time() + resume_s
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
                    if stt_pending.is_set() or fire_pending.is_set():
                        break
                    time.sleep(0.05)
        except Exception as exc:
            _wake_debug(f"stream_err {exc}")
            time.sleep(0.75)
            continue

        if stop.is_set():
            continue

        # OWW hit: mic stream closed → then start command recording
        if fire_pending.is_set():
            fire_pending.clear()
            _dispatch_detect()
            continue

        if pause.is_set():
            continue
        if not stt_pending.is_set():
            continue
        stt_pending.clear()
        last_stt = time.time()
        snap = list(stt_snapshot)
        stt_snapshot = []
        if use_text and armed and _try_stt_wake_pcm(snap):
            pause.set()
            cool_until = time.time() + _COOLDOWN_S
            armed = False
            _wake_debug("stt_fire")
            _dispatch_detect()
        else:
            cool_until = time.time() + _STT_COOLDOWN_S
