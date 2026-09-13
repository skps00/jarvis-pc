"""Speaker gate 單元測試：SK 真聲 vs 異人樣本。

- SK 樣本：%APPDATA%/Jarvis/wake_recordings/my_real_samples/*.wav（16k mono 2s）
- 異人樣本：jarvis-pc/.cache/ecapa-voxceleb/example1.wav + example2.flac（speechbrain repo 內建）
- Profile：%APPDATA%/Jarvis/voice_profile.npy

⚠️ MIC MISMATCH（2026-08-27 實測）：my_real_samples 用 Sonar mic（record script
用 default input），profile 用 Arctis（wake_mic_device=2）→ cross-mic cosine 只
有 0.19-0.33，**SK accept 部分會 FAIL 係預期**（唔代表 gate 壞）。真正 accept 驗證
要靠：SK 講「hey jarvis」睇 wake_debug.log，或 scripts/verify_voice.py（同 mic）。
本 test 可信嘅部分：model load、異人 reject、edge case（empty/short fail-closed）。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import wave


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wf:
        assert wf.getnchannels() == 1, f"{path}: channels={wf.getnchannels()}"
        assert wf.getframerate() == 16000, f"{path}: rate={wf.getframerate()}"
        raw = wf.readframes(wf.getnframes())
    return np.frombuffer(raw, dtype=np.int16)


def main() -> int:
    from jarvis.speaker_gate import load_profile, model_device, verify_pcm, warm

    prof = load_profile()
    print(f"profile: {'OK ' if prof is not None else 'MISSING'} dim={0 if prof is None else prof.size}")
    if prof is None:
        return 2

    t0 = time.time()
    ok = warm()
    dt = time.time() - t0
    print(f"model warm: ok={ok} dev={model_device()} load={dt:.1f}s")
    if not ok:
        return 2

    sk_dir = Path.home() / "AppData" / "Roaming" / "Jarvis" / "wake_recordings" / "my_real_samples"
    sk_files = sorted(sk_dir.glob("*.wav")) if sk_dir.is_dir() else []
    print(f"SK samples: {len(sk_files)}")

    other_files = [
        Path(__file__).resolve().parent.parent / ".cache" / "ecapa-voxceleb" / "example1.wav",
        Path(__file__).resolve().parent.parent / ".cache" / "ecapa-voxceleb" / "example2.flac",
    ]
    other_files = [p for p in other_files if p.exists()]

    # --- SK samples: expect accept ---
    sk_scores = []
    sk_rejects = []
    for p in sk_files[:20]:  # 抽 20 個 sample 夠快
        pcm = read_wav(p)
        t0 = time.time()
        res = verify_pcm(pcm, threshold=0.5)
        dt = time.time() - t0
        sk_scores.append(res["score"])
        if not res["accept"]:
            sk_rejects.append((p.name, res))
        if dt > 0.5:
            print(f"  [slow] {p.name}: verify {dt:.2f}s")
    print(f"SK:   n={len(sk_scores)} mean={np.mean(sk_scores):.3f} min={np.min(sk_scores):.3f} max={np.max(sk_scores):.3f}")
    print(f"SK rejects: {[(n, r['score']) for n, r in sk_rejects]}")

    # --- Other voices: expect reject ---
    other_results = []
    for p in other_files:
        if p.suffix == ".flac":
            import soundfile as sf
            data, sr = sf.read(str(p))
            pcm = (data * 32767).astype(np.int16) if data.dtype == np.float32 else data.astype(np.int16)
        else:
            pcm = read_wav(p)
        res = verify_pcm(pcm, threshold=0.5)
        other_results.append(res)
        print(f"OTHER: {p.name}: score={res['score']:.3f} accept={res['accept']} reason={res['reason']}")

    # --- Empty / too short: expect fail-closed ---
    for label, pcm in [("empty", np.array([], dtype=np.int16)), ("short", np.zeros(1600, dtype=np.int16))]:
        res = verify_pcm(pcm, threshold=0.5)
        print(f"EDGE:  {label}: accept={res['accept']} reason={res['reason']} skip={res['skip']}")

    # Verdict
    n_sk = len(sk_scores)
    ok_sk = n_sk > 0 and all(s >= 0.5 for s in sk_scores)
    ok_other = bool(other_results) and all(not r["accept"] for r in other_results)
    print(f"\nVERDICT: SK accept={'PASS' if ok_sk else 'FAIL'}  OTHER reject={'PASS' if ok_other else 'FAIL'}")
    return 0 if (ok_sk and ok_other) else 1


if __name__ == "__main__":
    raise SystemExit(main())
