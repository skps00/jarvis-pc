#!/usr/bin/env python3
"""Record many 16 kHz mono WAVs for openWakeWord custom ``jarvis`` training.

Compatible with CoreWorxLab/openwakeword-training ``my_real_samples/`` layout:
``jarvis_0001.wav``, ``jarvis_0002.wav``, …

Example:
  python scripts/record_jarvis_wake.py
  python scripts/record_jarvis_wake.py --target 1000 --seconds 2.0
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import wave
from pathlib import Path


SAMPLE_RATE = 16000
CHANNELS = 1


def default_out_dir() -> Path:
    """%APPDATA%\\Jarvis\\wake_recordings\\my_real_samples on Windows."""
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "Jarvis" / "wake_recordings" / "my_real_samples"


def list_wavs(out_dir: Path) -> list[Path]:
    """Sorted existing sample paths."""
    return sorted(out_dir.glob("*.wav"))


def next_index(out_dir: Path, prefix: str) -> int:
    """Next 1-based index from ``prefix_NNNN.wav`` files."""
    n = 0
    for p in out_dir.glob(f"{prefix}_*.wav"):
        stem = p.stem
        if "_" not in stem:
            continue
        tail = stem.rsplit("_", 1)[-1]
        if tail.isdigit():
            n = max(n, int(tail))
    return n + 1


def record_wav(path: Path, *, seconds: float) -> float:
    """
    Record mono int16 PCM to ``path``.

    Returns peak RMS (0..1) so caller can warn about silence.
    """
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise SystemExit(
            '需要 sounddevice + numpy：pip install "jarvis-pc[wake]" 或 sounddevice numpy'
        ) from exc

    frames = int(seconds * SAMPLE_RATE)
    print("  … SPEAK NOW …", flush=True)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32")
    sd.wait()
    mono = audio.flatten()
    rms = float(np.sqrt(np.mean(np.square(mono))))
    pcm = (np.clip(mono, -1.0, 1.0) * 32767.0).astype("int16")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return rms


def play_wav(path: Path) -> None:
    """Play a wav on default output (best-effort)."""
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        print("  (no sounddevice — skip play)")
        return
    with wave.open(str(path), "rb") as wf:
        rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
        width = wf.getsampwidth()
    if width != 2:
        print("  (unsupported sample width)")
        return
    pcm = np.frombuffer(raw, dtype=np.int16).astype("float32") / 32767.0
    sd.play(pcm, rate)
    sd.wait()


def countdown(sec: int = 1) -> None:
    """Short count before capture."""
    for i in range(sec, 0, -1):
        print(f"  {i}…", end=" ", flush=True)
        time.sleep(1.0)
    print()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI args."""
    p = argparse.ArgumentParser(description="Record jarvis wake samples (16 kHz mono)")
    p.add_argument("--wake-word", default="jarvis", help="Phrase to say (default: jarvis)")
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output dir (default: %%APPDATA%%\\Jarvis\\wake_recordings\\my_real_samples)",
    )
    p.add_argument("--target", type=int, default=1000, help="Goal sample count")
    p.add_argument("--seconds", type=float, default=2.0, help="Seconds per clip")
    p.add_argument("--countdown", type=int, default=1, help="Countdown seconds before SPEAK")
    p.add_argument(
        "--min-rms",
        type=float,
        default=0.01,
        help="Warn if peak RMS below this (possible silence)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Interactive record loop. Returns process exit code."""
    args = parse_args(argv)
    out_dir = args.out_dir or default_out_dir()
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.wake_word.strip().lower().replace(" ", "_") or "jarvis"
    if not prefix.replace("_", "").isalnum():
        print(f"Bad wake-word slug: {prefix!r}")
        return 2

    existing = list_wavs(out_dir)
    count = len(existing)
    idx = next_index(out_dir, prefix)
    last_path: Path | None = existing[-1] if existing else None

    print("=" * 56)
    print(f' Jarvis wake recorder — say "{args.wake_word}" ')
    print("=" * 56)
    print(f" Out:    {out_dir}")
    print(f" Format: {SAMPLE_RATE} Hz mono PCM16, {args.seconds}s")
    print(f" Now:    {count}  Target: {args.target}")
    print()
    print(" Keys (then Enter):")
    print("   [empty]  record next")
    print("   r        re-record last")
    print("   p        play last")
    print("   s        status / count")
    print("   q        quit")
    print()
    print(" Tips: vary speed, volume, distance, angle. Batches of 50–100 OK.")
    print()

    while True:
        left = max(0, args.target - count)
        prompt = f"[{count}/{args.target}  left~{left}] ENTER=rec  r/p/s/q > "
        try:
            raw = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        cmd = (raw or "").strip().lower()

        if cmd == "q":
            break
        if cmd == "s":
            print(f"  files={count} next_index={idx} last={last_path}")
            continue
        if cmd == "p":
            if last_path and last_path.is_file():
                print(f"  play {last_path.name}")
                play_wav(last_path)
            else:
                print("  no last clip")
            continue
        if cmd == "r":
            if not last_path or not last_path.is_file():
                print("  nothing to redo")
                continue
            path = last_path
            print(f"  redo {path.name}")
            countdown(args.countdown)
            rms = record_wav(path, seconds=float(args.seconds))
            print(f"  saved {path.name}  rms={rms:.3f}")
            if rms < args.min_rms:
                print("  WARN: very quiet — check mic / speak louder")
            continue
        if cmd not in ("",):
            print("  unknown — use ENTER / r / p / s / q")
            continue

        path = out_dir / f"{prefix}_{idx:04d}.wav"
        countdown(args.countdown)
        rms = record_wav(path, seconds=float(args.seconds))
        last_path = path
        count += 1
        idx += 1
        print(f"  saved {path.name}  rms={rms:.3f}  total={count}")
        if rms < args.min_rms:
            print("  WARN: very quiet — check mic / speak louder (or press r to redo)")
        if count >= args.target:
            print(f"\n Target {args.target} reached. Keep going or q to quit.")

    print()
    print(f"Done. {count} wav(s) in:\n  {out_dir}")
    print("Next: copy/symlink this folder as my_real_samples/ into openwakeword-training,")
    print('      then train with --wake-word "jarvis". See docs/train_wake_jarvis.md')
    return 0


if __name__ == "__main__":
    sys.exit(main())
