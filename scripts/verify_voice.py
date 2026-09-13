"""聲紋 quick verify：錄 3 秒，睇 cos score 係咪 >= threshold。

用法：python scripts/verify_voice.py
錄完會 print score + accept/reject，用嚟：
- 驗證 enrollment 得唔得（你講嘢應該 accept，score 越高越好）
- 校 threshold（睇實際 score 分佈）

⚠️ 用同 gate 一樣嘅 mic（settings.wake_mic_device）——唔同 mic 分數會跌。
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

SR = 16000
DUR = 3.0


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

    from jarvis.speaker_gate import load_profile, model_device, verify_pcm, warm

    import sounddevice as sd

    cfg_path = Path(os.environ.get("APPDATA", "")) / "Jarvis" / "settings.json"
    try:
        dev = json.load(open(cfg_path, encoding="utf-8")).get("wake_mic_device")
    except Exception:
        dev = None

    prof = load_profile()
    if prof is None:
        print("❌ 冇 voice_profile.npy——先跑 scripts/enroll_voice.py 錄聲紋")
        return 1

    print(f"profile: dim={prof.size} · mic={dev}")
    t0 = time.time()
    ok = warm()
    print(f"model warm: ok={ok} dev={model_device()} ({time.time()-t0:.1f}s)")
    if not ok:
        print("❌ model load 失敗")
        return 1

    print(f"🎤 準備錄音 {DUR}s…… 3 秒後開始講嘢")
    time.sleep(2)
    print("▶ 講嘢！")
    rec = sd.rec(int(DUR * SR), samplerate=SR, channels=1, dtype="float32", device=dev)
    sd.wait()
    pcm = (np.clip(rec[:, 0], -1.0, 1.0) * 32767.0).astype(np.int16)
    rms = float(np.sqrt(np.mean(np.square(rec[:, 0]))))
    if rms < 0.01:
        print("⚠️ 太靜——mic 冇聲？檢查 wake_mic_device")
        return 1

    t0 = time.time()
    res = verify_pcm(pcm, threshold=float(
        json.load(open(cfg_path, encoding="utf-8")).get("speaker_threshold", 0.5)
    ))
    dt = time.time() - t0
    verdict = "✅ ACCEPT（係你）" if res["accept"] else "❌ REJECT（唔似你）"
    print(f"\nscore = {res['score']:.3f}  threshold = {res.get('threshold', 0.5)}  {verdict}")
    print(f"reason={res['reason']} skip={res['skip']}  verify={dt*1000:.0f}ms")
    print("\n提示：score 越高越確定係你。想調門檻 → settings UI「聲紋門檻」")
    return 0 if res["accept"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
