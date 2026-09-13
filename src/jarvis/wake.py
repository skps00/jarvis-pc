"""Wake word: openWakeWord + optional short STT fallback for bare Jarvis."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# ~80ms @ 16kHz
_CHUNK = 1280
_SAMPLE_RATE = 16000
DEFAULT_THRESHOLD = 0.50
# Dead Colab onnx must NOT lower thr — that caused false fires at 0.05–0.2
CUSTOM_DEFAULT_THRESHOLD = 0.50
# 分數持續低過 threshold 幾耐就重新武裝（修正「環境持續中等分數 → 叫唔醒」bug）
_REARM_TIMEOUT_S = 2.0
# After command/mic resume, ignore wakes this long
_POST_RESUME_S = 3.0
_COOLDOWN_S = 1.5
# Command capture (post-wake VAD): pre-roll + listen until silence
_CMD_PRE_ROLL_S = 0.6  # keep "Jarvis" just before fire
_CMD_MAX_S = 4.0  # hard cap
_CMD_MIN_S = 0.45  # don't cut mid-wake
_CMD_SPEECH_RMS = 0.02  # voice after wake（降低，令「開cs」等短細聲指令都判定做 speech）
_CMD_SILENCE_RMS = 0.018  # end-of-utterance
_CMD_SILENCE_FRAMES = 5  # ~400ms quiet → done（縮短等待，D3）
# STT text-wake: strict — game bleed used to schedule forever
_RMS_GATE = 0.14
_STT_SECONDS = 2.0
_STT_COOLDOWN_S = 8.0
_LOUD_FRAMES_NEED = 10  # ~800ms continuous loud
_STT_TRAIL_S = 0.35
_AGC_TARGET_RMS = 0.10  # target speech level (float32 scale, ~0.1)
_AGC_MAX_GAIN = 8.0  # never amplify more than 8x (avoid noise boost)
_AGC_NOISE_FLOOR = 0.0015  # below this: don't amplify (phantom speech from AGC)
_STT_AGC_TARGET_RMS = 0.12  # command STT needs louder than OWW keyword detect
_STT_AGC_MAX_GAIN = 24.0
_BUF_CHUNKS = max(
    8, int(max(_STT_SECONDS, _CMD_PRE_ROLL_S + _CMD_MAX_S) * _SAMPLE_RATE / _CHUNK)
)
_WAKE_DEBUG_LOG = Path.home() / "AppData" / "Roaming" / "Jarvis" / "wake_debug.log"
# Heartbeat：每 N 秒 log 一次 listening 狀態（rms/best/armed）——診斷「叫唔醒」用
_HEARTBEAT_S = 60.0
# Mic 健康：連續 N 個 heartbeat rms≈0（headset 休眠/斷連）→ mic_signal_ok=false
# 寫入 voice_status.json，等 HUD/MCP 顯示真實狀態（2026-08-31）。
_MIC_SILENT_RMS = 0.0005
_MIC_SILENT_LIMIT = 3
_mic_silent_streak = 0
_aec_applied = 0
_aec_skipped = 0
_last_agc_log = 0.0

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
    """Default OWW thr. Custom onnx no longer softens — dead models caused false fires."""
    return DEFAULT_THRESHOLD


def resolve_mic_name(name: str) -> int | None:
    """Resolve 裝置名 → 而家可用嘅 index（16k wake stream 開到嘅）。

    Windows sounddevice 會列出同一個 mic 多個變體（MME 44.1k / 48k、WDM…），
    48k 變體開唔到 16k stream（PaErrorCode -9997「Invalid sample rate」）。
    所以 settings 存**名**，喺度揀 44.1kHz 嘅 entry（16k 一定開到）。
    """
    if not name:
        return None
    import sounddevice as sd

    best: int | None = None
    for i, d in enumerate(sd.query_devices()):
        if int(d.get("max_input_channels") or 0) <= 0:
            continue
        dname = str(d.get("name") or "").strip()
        if dname != name:
            continue
        sr = float(d.get("default_samplerate") or 0)
        if abs(sr - 44100.0) < 1.0:
            return i  # 44.1k 變體：16k 必開到
        if best is None:
            best = i
    return best


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
    # vad_threshold：openwakeword 內置 Silero VAD 過濾非語音噪音。
    # 注意：0.5 太嚴會擋真人聲（叫唔醒）——暫時 disable（0），防誤觸靠 A2 rearm timeout + threshold。
    if paths:
        return Model(wakeword_models=paths, inference_framework="onnx", vad_threshold=0)
    return Model(inference_framework="onnx", vad_threshold=0)


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
        "渣維斯",
        "揸域斯",
        "查域斯",
        "渣域",
        "揸域",
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


def _update_mic_signal(ok: bool) -> None:
    """Patch `mic_signal_ok` into voice_status.json so HUD/MCP can show the
    REAL mic health (headset asleep/disconnected = rms≈0 while UI claims armed).
    Read-modify-write; best-effort — never break the wake loop over it."""
    global _mic_silent_streak
    was_bad = _mic_silent_streak >= _MIC_SILENT_LIMIT
    if ok:
        _mic_silent_streak = 0
        if not was_bad:
            return  # healthy and was healthy: leave the field as-is (no churn)
        val: bool | None = True  # recovered — flip back once
    else:
        _mic_silent_streak += 1
        if _mic_silent_streak < _MIC_SILENT_LIMIT:
            return  # one quiet beat is not a disconnect yet
        val = False
    try:
        p = _WAKE_DEBUG_LOG.with_name("voice_status.json")
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            data = {}
        data["mic_signal_ok"] = val
        data["mic_signal_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except (OSError, ValueError):
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
            for lang in ("auto", "en", "yue"):
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


def _open_input_stream(sd, input_device: int | None, callback) -> Any:
    """Open 16k mic InputStream；開唔到 -9997 就 WASAPI auto-convert retry。

    Windows 部分裝置（48kHz WASAPI 變體）唔支援 16k stream →
    PaErrorCode -9997 Invalid sample rate。社群解法（python-sounddevice
    PR #492）：PortAudio ``paWinWasapiAutoConvert=64`` + WASAPI shared mode
    自動轉換 sample rate —— 48k 裝置照開 16k stream。
    """
    kwargs: dict[str, Any] = dict(
        samplerate=_SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=_CHUNK,
        callback=callback,
        device=input_device,
    )
    try:
        return sd.InputStream(**kwargs)
    except Exception as exc:
        err = str(exc)
        if "Invalid sample rate" in err or "-9997" in err:
            try:
                _wake_debug("stream_retry wasapi_autoconvert")
                ex = sd.WasapiSettings()
                ex._streaminfo.flags = 64  # paWinWasapiAutoConvert (PR #492)
                return sd.InputStream(**kwargs, extra_settings=ex)
            except Exception:
                pass
        raise


def _init_speaker_gate() -> tuple[bool, float, bool]:
    """Phase 6 A4: speaker gate init — return (gate_enabled, gate_thr, gate_ready)."""
    gate_enabled = False
    gate_thr = 0.50
    gate_ready = False
    try:
        from jarvis.settings import load_settings as _ls
        from jarvis.speaker_gate import (
            model_device as _spk_model_device,
            profile_exists as _spk_prof,
            warm as _spk_warm,
        )

        _cfg = _ls()
        gate_enabled = bool(getattr(_cfg, "speaker_gate", True))
        gate_thr = float(getattr(_cfg, "speaker_threshold", 0.50) or 0.50)
        if gate_enabled and _spk_prof():
            _t0 = time.time()
            gate_ready = bool(_spk_warm())
            _wake_debug(
                f"spk_gate {'ready' if gate_ready else 'warm_fail'} "
                f"dev={_spk_model_device()} thr={gate_thr} "
                f"load={time.time() - _t0:.1f}s"
            )
        else:
            _wake_debug("spk_gate off (setting off / no profile)")
    except Exception as exc:  # noqa: BLE001
        _wake_debug(f"spk_gate init_fail {exc}")
    return gate_enabled, gate_thr, gate_ready


def _apply_aec(pcm, aec_chain, aec_processor, loopback, chunk_size):
    """AEC for OWW predict path only; ring/command capture stays raw."""
    global _aec_applied, _aec_skipped
    predict_pcm = pcm
    if aec_chain is not None:
        try:
            predict_pcm = aec_chain.process(pcm)
            _aec_applied += 1
            if _aec_applied == 1:
                _wake_debug("aec_first_apply")
        except Exception:
            pass
    elif aec_processor is not None and loopback is not None:
        try:
            echo = loopback.get_chunk(chunk_size)
            if echo is not None:
                predict_pcm = aec_processor.process(pcm, echo)
                _aec_applied += 1
                if _aec_applied == 1:
                    _wake_debug("aec_first_apply")
            else:
                _aec_skipped += 1
        except Exception:
            pass
    return predict_pcm


def _apply_agc(predict_pcm, now):
    """AGC boost for OWW predict only (ring/STT/command stay raw)."""
    global _last_agc_log
    import numpy as np

    rms_f = float(
        np.sqrt(np.mean((predict_pcm.astype(np.float32) / 32767.0) ** 2))
    )
    if rms_f < _AGC_NOISE_FLOOR:
        return predict_pcm
    if rms_f < _AGC_TARGET_RMS:
        gain = min(_AGC_MAX_GAIN, _AGC_TARGET_RMS / max(rms_f, 1e-4))
        predict_pcm = (
            (predict_pcm.astype(np.float32) * gain).clip(-32767, 32767).astype(np.int16)
        )
        if gain > 1.5 and now - _last_agc_log >= 10.0:
            _last_agc_log = now
            _wake_debug(f"agc_gain={gain:.1f} rms={rms_f:.3f}")
    return predict_pcm


def _apply_stt_agc(pcm):
    """Stronger AGC for command PCM right before STT (not OWW / ring buffer)."""
    import numpy as np

    if pcm is None or getattr(pcm, "size", 0) <= 0:
        return pcm
    rms_f = float(np.sqrt(np.mean((pcm.astype(np.float32) / 32767.0) ** 2)))
    if rms_f < _AGC_NOISE_FLOOR:
        return pcm
    if rms_f < _STT_AGC_TARGET_RMS:
        gain = min(_STT_AGC_MAX_GAIN, _STT_AGC_TARGET_RMS / max(rms_f, 1e-4))
        pcm = (pcm.astype(np.float32) * gain).clip(-32767, 32767).astype(np.int16)
        if gain > 1.5:
            _wake_debug(f"[ear] agc_gain={gain:.2f} rms={rms_f:.3f}")
    return pcm


def run_wake_loop(
    on_detect: Callable[[], None],
    *,
    on_command: Callable[[Any], None] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    post_resume_s: float | None = None,
    stop_event: threading.Event | None = None,
    pause_event: threading.Event | None = None,
    text_wake: bool | None = None,
    input_device: int | None = None,
    aec_processor: Any = None,
    loopback: Any = None,
    aec_chain: Any = None,
) -> None:
    """
    Stream mic → OWW (custom jarvis and/or hey_jarvis) → on_detect/on_command.

    When *on_command* is given, OWW fire keeps the mic open and captures
    post-wake audio with VAD (pre-roll + speech until silence, max
    ``_CMD_MAX_S``), then calls ``on_command(pcm_int16_array)``.

    Hybrid: if OWW score stays low but mic is loud, STT the recent ring
    buffer for bare ``Jarvis`` / ``hey jarvis`` (off by default via
    *text_wake*).
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

    gate_enabled, gate_thr, gate_ready = _init_speaker_gate()
    cool_until = 0.0
    armed = True
    stt_pending = threading.Event()
    fire_pending = threading.Event()
    loud_frames = 0
    below_thr_since = None
    last_stt = 0.0
    stt_due = 0.0
    pcm_ring: deque[Any] = deque(maxlen=_BUF_CHUNKS)
    pcm_lock = threading.Lock()
    stt_snapshot: list[Any] = []
    cmd_detected_at = 0.0
    cmd_audio: Any = None
    cmd_chunks: list[Any] = []
    cmd_speech_seen = False
    cmd_silent_frames = 0
    last_best = 0.0
    peak_best = 0.0
    peak_rms = 0.0

    def _trip(reason: str) -> None:
        """Signal wake hit. Keep stream open; VAD-capture command audio."""
        nonlocal cool_until, armed, loud_frames, stt_due, below_thr_since
        nonlocal cmd_detected_at, cmd_audio, cmd_chunks
        nonlocal cmd_speech_seen, cmd_silent_frames
        armed = False
        below_thr_since = None
        loud_frames = 0
        stt_due = 0.0
        stt_pending.clear()
        if on_command is None:
            cool_until = time.time() + _COOLDOWN_S
            pause.set()
            fire_pending.set()
            _wake_debug(f"{reason} (legacy)")
            return
        # Pre-roll: last ~0.6s so "Jarvis" not cut; then only NEW post-wake audio
        n_pre = max(1, int(_CMD_PRE_ROLL_S * _SAMPLE_RATE / _CHUNK))
        with pcm_lock:
            cmd_chunks = list(pcm_ring)[-n_pre:]
        cmd_detected_at = time.time()
        cmd_audio = None
        cmd_speech_seen = False
        cmd_silent_frames = 0
        cool_until = time.time() + _CMD_MAX_S + _COOLDOWN_S
        _wake_debug(reason)

    def _finish_cmd_capture() -> None:
        nonlocal cmd_detected_at, cmd_audio, cmd_chunks
        if not cmd_chunks:
            cmd_audio = np.zeros(0, dtype=np.int16)
        else:
            cmd_audio = np.concatenate(cmd_chunks)
        fire_pending.set()
        cmd_detected_at = 0.0
        cmd_chunks = []
        _wake_debug(f"oww_cmd_pcm dur={cmd_audio.size / _SAMPLE_RATE:.1f}s")

    def _dispatch_detect(pcm_array: Any = None) -> None:
        """OWW path: pcm_array is int16 numpy.  STT fallback: None."""
        if pcm_array is not None and on_command is not None:
            _wake_debug("dispatch_on_command")
            try:
                pcm_array = _apply_stt_agc(pcm_array)
                on_command(pcm_array)
            except Exception as exc:
                _wake_debug(f"on_command_fail {exc}")
        else:
            time.sleep(0.25)  # let WASAPI release before command record
            _wake_debug("dispatch_on_detect")
            try:
                on_detect()
            except Exception as exc:
                _wake_debug(f"on_detect_fail {exc}")

    def _callback(indata, frames, time_info, status) -> None:  # noqa: ARG001
        nonlocal cool_until, armed, loud_frames, stt_due, stt_snapshot, below_thr_since
        nonlocal cmd_detected_at, cmd_audio, cmd_chunks
        nonlocal cmd_speech_seen, cmd_silent_frames, last_best, peak_best, peak_rms
        global _aec_applied, _aec_skipped
        if stop.is_set() or pause.is_set() or stt_pending.is_set() or fire_pending.is_set():
            return
        now = time.time()
        mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
        rms = float(np.sqrt(np.mean(np.square(mono))))
        peak_rms = max(peak_rms, rms)
        pcm = (np.clip(mono, -1.0, 1.0) * 32767.0).astype(np.int16)
        predict_pcm = _apply_aec(
            pcm, aec_chain, aec_processor, loopback, _CHUNK
        )
        with pcm_lock:
            pcm_ring.append(pcm.copy())

        # --- capture mode: post-wake VAD (speech → silence → done) ---
        if cmd_detected_at > 0 and cmd_audio is None:
            cmd_chunks.append(pcm.copy())
            elapsed = now - cmd_detected_at
            if rms >= _CMD_SPEECH_RMS:
                cmd_speech_seen = True
                cmd_silent_frames = 0
            elif rms < _CMD_SILENCE_RMS:
                cmd_silent_frames += 1
            else:
                cmd_silent_frames = 0
            done = False
            if elapsed >= _CMD_MAX_S:
                done = True
            elif (
                elapsed >= _CMD_MIN_S
                and cmd_speech_seen
                and cmd_silent_frames >= _CMD_SILENCE_FRAMES
            ):
                done = True
            elif (
                elapsed >= 1.2
                and not cmd_speech_seen
                and cmd_silent_frames >= _CMD_SILENCE_FRAMES
            ):
                # No speech after wake — bail early (false wake / ambient)
                done = True
            if done:
                _finish_cmd_capture()
            return

        if now < cool_until:
            return
        predict_pcm = _apply_agc(predict_pcm, now)
        try:
            scores = model.predict(predict_pcm)
        except Exception as exc:
            # Diagnose OWW/onnxruntime failure (2026-08-31: silent except hid
            # "Invalid input shape" — best stayed 0.001 forever).
            _wake_debug(f"oww_predict_err {type(exc).__name__}: {exc}")
            return
        if not scores:
            return
        best = _jarvis_score(scores)
        last_best = best
        peak_best = max(peak_best, best)
        if best >= threshold:
            below_thr_since = None
            if armed:
                _trip(
                    f"oww_fire best={best:.3f} thr={threshold} "
                    f"hey={float(scores.get('hey_jarvis_v0.1', 0)):.3f} "
                    f"jarvis={float(scores.get('jarvis', 0)):.3f}"
                )
                return
        else:
            # rearm timeout：分數持續低過 threshold _REARM_TIMEOUT_S 秒 → 重新武裝。
            # 修正舊邏輯（要跌 < _REARM_BELOW 0.25 先 armed）——環境持續中等分數
            # （0.25-0.5，例如 BGM 有人聲）會永遠唔 rearm → 叫唔醒。
            if below_thr_since is None:
                below_thr_since = now
            elif now - below_thr_since >= _REARM_TIMEOUT_S:
                armed = True
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
        below_thr_since = None
        loud_frames = 0
        stt_due = 0.0
        stt_pending.clear()
        fire_pending.clear()
        cmd_detected_at = 0.0
        cmd_audio = None
        cmd_chunks = []
        cmd_speech_seen = False
        cmd_silent_frames = 0
        with pcm_lock:
            pcm_ring.clear()
        cool_until = time.time() + resume_s
        time.sleep(0.4)
        if pause.is_set():
            continue
        try:
            with _open_input_stream(sd, input_device, _callback):
                last_beat = time.time()  # 唔好即刻 log 第一個 beat
                while not stop.is_set() and not pause.is_set():
                    if stt_pending.is_set() or fire_pending.is_set():
                        break
                    _nb = time.time()
                    if _nb - last_beat >= _HEARTBEAT_S:
                        last_beat = _nb
                        with pcm_lock:
                            _rbuf = list(pcm_ring)[-5:]
                            _ring_n = len(pcm_ring)
                        _rms_beat = 0.0
                        if _rbuf:
                            _rms_beat = float(
                                np.sqrt(
                                    np.mean(
                                        np.square(np.concatenate(_rbuf) / 32767.0)
                                    )
                                )
                            )
                        _update_mic_signal(_rms_beat > _MIC_SILENT_RMS)
                        _wake_debug(
                            f"wake_heartbeat ring={_ring_n} "
                            f"rms={_rms_beat:.3f} peak_rms={peak_rms:.3f} "
                            f"best={last_best:.3f} peak_best={peak_best:.3f} "
                            f"armed={armed} "
                            f"pause={pause.is_set()} cool={cool_until - _nb:.0f}s"
                        )
                        peak_best = 0.0
                        peak_rms = 0.0
                    time.sleep(0.05)
        except Exception as exc:
            _wake_debug(f"stream_err {exc}")
            time.sleep(0.75)
            continue

        if stop.is_set():
            continue

        # OWW hit: mic stream closed → forward pre-captured command PCM or call on_detect
        if fire_pending.is_set():
            fire_pending.clear()
            pcm = cmd_audio
            cmd_audio = None
            _wake_debug(
                f"oww_cmd_pcm dur={pcm.size / _SAMPLE_RATE:.1f}s"
                if pcm is not None and pcm.size > 0
                else "oww_cmd_pcm empty"
            )
            # Phase 6 A4: speaker gate — 唔係 SK 把聲 → 唔醒（discard + re-arm）
            if gate_enabled and gate_ready and pcm is not None and pcm.size > 0:
                from jarvis.speaker_gate import verify_pcm as _speaker_verify

                _res = _speaker_verify(pcm, threshold=gate_thr)
                _wake_debug(
                    f"spk_gate {_res['reason']} score={_res['score']:.3f} "
                    f"accept={_res['accept']} skip={_res['skip']}"
                )
                if not _res["accept"]:
                    continue
            _dispatch_detect(pcm)
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
            # Phase 6 A4: speaker gate on STT text-wake path too
            _fire = True
            if gate_enabled and gate_ready:
                from jarvis.speaker_gate import verify_pcm as _speaker_verify

                _pcm = np.concatenate(snap) if snap else None
                _res = _speaker_verify(_pcm, threshold=gate_thr)
                _wake_debug(
                    f"spk_gate_stt {_res['reason']} score={_res['score']:.3f} "
                    f"accept={_res['accept']} skip={_res['skip']}"
                )
                if not _res["accept"]:
                    _fire = False
            if _fire:
                pause.set()
                cool_until = time.time() + _COOLDOWN_S
                armed = False
                _wake_debug("stt_fire")
                if on_command is not None and snap:
                    pcm = np.concatenate(snap)
                    _dispatch_detect(pcm)
                else:
                    _dispatch_detect()
            else:
                cool_until = time.time() + _STT_COOLDOWN_S
        else:
            cool_until = time.time() + _STT_COOLDOWN_S
