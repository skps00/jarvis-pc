"""AEC (Acoustic Echo Cancellation) for the wake pipeline.

Uses ``pyaec`` (adaptive-filter AEC, SpeexDSP-compatible DLL) to subtract
speaker output (WASAPI loopback) from the mic signal before openwakeword,
so JARVIS' own TTS / voice-call peer audio / YouTube BGM don't false-trigger
the wake word, while SK's local voice still fires.

Pipeline::

    mic (Arctis)   ────────────┐
                               ├─► Aec.cancel_echo(near=mic, echo=loopback)
    loopback (speaker out) ────┘        │
                                        ▼
                                 clean 16k int16 → openwakeword

Deps (installed 2026-08-28 on Py3.14):
    pyaec (wheel: py3-none-win_amd64)  — AEC engine
    pyaudiowpatch (wheel)              — WASAPI loopback capture
"""
from __future__ import annotations

import queue
import threading
import time
from typing import Any

import numpy as np

_SAMPLE_RATE = 16000
_FRAME = 160  # 10 ms @ 16k
_QUEUE_MAX = 64


def available() -> bool:
    """True if pyaec (AEC engine) is installed."""
    try:
        import pyaec  # noqa: F401

        return True
    except ImportError:
        return False


def list_loopback_devices() -> list[tuple[int, str, int]]:
    """Return [(index, name, native_rate)] for WASAPI loopback devices."""
    import pyaudiowpatch as pyaudio

    p = pyaudio.PyAudio()
    out: list[tuple[int, str, int]] = []
    try:
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            n = str(d.get("name") or "")
            if "[Loopback]" in n or "loopback" in n.lower():
                out.append((i, n, int(d.get("defaultSampleRate") or 0)))
    finally:
        p.terminate()
    return out


def find_loopback_for_output(output_name: str) -> tuple[int, str, int] | None:
    """Match a loopback device to an output device name (e.g. '耳機 (2- Arctis Nova 7)')."""
    if not output_name:
        return None
    base = output_name.replace("[Loopback]", "").strip()
    for idx, name, rate in list_loopback_devices():
        if base and base in name:
            return (idx, name, rate)
    return None


class AecProcessor:
    """Thin wrapper over pyaec.Aec: ``process(near, echo) -> clean int16``."""

    def __init__(
        self,
        frame_size: int = _FRAME,
        sample_rate: int = _SAMPLE_RATE,
        filter_length: int = 1000,
    ):
        from pyaec import Aec

        self._aec = Aec(
            frame_size=frame_size,
            filter_length=filter_length,
            sample_rate=sample_rate,
        )
        self.frame_size = frame_size

    def process(self, near: np.ndarray, echo: np.ndarray) -> np.ndarray:
        """near/echo: int16 mono, same length. Process 160-sample subframes; append remainder raw."""
        if len(near) != len(echo):
            raise ValueError("near/echo length mismatch")
        fs = self.frame_size
        n = len(near)
        full = (n // fs) * fs
        if full == 0:
            return near.copy()
        parts: list[np.ndarray] = []
        for i in range(0, full, fs):
            out = self._aec.cancel_echo(
                near[i : i + fs].tolist(), echo[i : i + fs].tolist()
            )
            parts.append(np.asarray(out, dtype=np.int16))
        if full < n:
            parts.append(near[full:])
        return np.concatenate(parts) if len(parts) > 1 else parts[0]


class LoopbackCapture:
    """Capture speaker output via WASAPI loopback at native rate, resample to 16k.

    ``get_frame()`` returns the most recent 16k int16 frame (10 ms) or None.
    Old frames are dropped when the queue overflows so mic always gets the
    freshest reference.
    """

    def __init__(self, device_index: int, target_rate: int = _SAMPLE_RATE):
        self._device_index = device_index
        self._target_rate = target_rate
        self._q: queue.Queue[np.ndarray] = queue.Queue(maxsize=_QUEUE_MAX)
        self._pa: Any = None
        self._stream: Any = None
        self._native_rate = 0
        self._channels = 0
        self._lock = threading.Lock()
        self._buf_lock = threading.Lock()
        self._running = False
        self._chunk_buf = np.array([], dtype=np.int16)

    @property
    def running(self) -> bool:
        return self._running

    def _cleanup(self) -> None:
        try:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
        except Exception:
            pass
        try:
            if self._pa:
                self._pa.terminate()
        except Exception:
            pass
        self._stream = None
        self._pa = None
        self._running = False
        self._q = queue.Queue(maxsize=_QUEUE_MAX)
        with self._buf_lock:
            self._chunk_buf = np.array([], dtype=np.int16)

    def start(self) -> bool:
        import pyaudiowpatch as pyaudio

        with self._lock:
            if self._running:
                return True
            try:
                self._pa = pyaudio.PyAudio()
                info = self._pa.get_device_info_by_index(self._device_index)
                self._native_rate = int(info["defaultSampleRate"])
                self._channels = int(info["maxInputChannels"] or 1)
                frame = max(1, self._native_rate // 100)  # 10 ms at native rate

                # WASAPI loopback: try 1ch first (2ch loopbacks accept mono), else native ch
                ch = 1
                try:
                    self._stream = self._pa.open(
                        format=pyaudio.paInt16,
                        channels=ch,
                        rate=self._native_rate,
                        input=True,
                        input_device_index=self._device_index,
                        frames_per_buffer=frame,
                        stream_callback=self._cb,
                    )
                except Exception:
                    ch = self._channels
                    self._stream = self._pa.open(
                        format=pyaudio.paInt16,
                        channels=ch,
                        rate=self._native_rate,
                        input=True,
                        input_device_index=self._device_index,
                        frames_per_buffer=frame,
                        stream_callback=self._cb,
                    )
                self._channels = ch
                self._stream.start_stream()
                self._running = True
                return True
            except Exception:
                self._cleanup()
                return False

    def _cb(self, in_data, frame_count, time_info, status) -> Any:
        if not in_data:
            return (None, 0)
        try:
            arr = np.frombuffer(in_data, dtype=np.int16)
            if self._channels > 1 and arr.size > frame_count:
                try:
                    arr = arr.reshape(-1, self._channels).mean(axis=1)
                except ValueError:
                    pass
            if self._native_rate != self._target_rate:
                n = max(1, int(round(arr.size * self._target_rate / self._native_rate)))
                xo = np.linspace(0.0, 1.0, num=arr.size, endpoint=False)
                xn = np.linspace(0.0, 1.0, num=n, endpoint=False)
                arr = np.interp(xn, xo, arr.astype(np.float32)).astype(np.int16)
            try:
                self._q.put_nowait(arr)
            except queue.Full:
                try:
                    self._q.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self._q.put_nowait(arr)
                except queue.Full:
                    pass
        except Exception:
            pass
        return (None, 0)

    def get_frame(self, timeout: float = 0.0) -> np.ndarray | None:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_chunk(self, chunk_size: int = 1280, timeout: float = 0.0) -> np.ndarray | None:
        """Accumulate queued frames until >= chunk_size; return exactly chunk_size or None."""
        deadline = time.time() + timeout
        while True:
            with self._buf_lock:
                if self._chunk_buf.size >= chunk_size:
                    out = self._chunk_buf[:chunk_size]
                    self._chunk_buf = self._chunk_buf[chunk_size:]
                    return out
            frame = self.get_frame(timeout=max(0.0, deadline - time.time()))
            if frame is None:
                return None
            with self._buf_lock:
                if self._chunk_buf.size:
                    self._chunk_buf = np.concatenate([self._chunk_buf, frame])
                else:
                    self._chunk_buf = frame

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._cleanup()


class AecChain:
    """Chain multiple loopback→AecProcessor pairs for multi-reference AEC."""

    def __init__(self, pairs: list[tuple[LoopbackCapture, AecProcessor]]):
        self._pairs = pairs

    @property
    def active(self) -> bool:
        return len(self._pairs) > 0

    def process(self, pcm: np.ndarray) -> np.ndarray:
        clean = pcm
        for loopback, processor in self._pairs:
            echo = loopback.get_chunk(len(pcm))
            if echo is not None:
                clean = processor.process(clean, echo)
        return clean

    def stop(self) -> None:
        for loopback, _processor in self._pairs:
            loopback.stop()
