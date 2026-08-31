"""JARVIS 聲紋 enrollment（GUI 版）：螢幕窗口倒數 + 錄音進度提示。

用法：python scripts/enroll_voice.py
"""
from __future__ import annotations

import os
import sys
import time

SR = 16000
DUR = 30


def _load_model():
    import shutil
    from pathlib import Path

    import speechbrain.utils.fetching as F

    def _copy(src, dst, *args, **kw):
        if dst.exists():
            dst.unlink()
        shutil.copy2(src, dst)

    F.link_with_strategy = _copy
    from huggingface_hub import snapshot_download

    model_dir = Path(__file__).resolve().parent.parent / ".cache" / "ecapa-voxceleb"
    if not (model_dir / "embedding_model.ckpt").exists():
        snapshot_download("speechbrain/spkrec-ecapa-voxceleb", local_dir=str(model_dir))
    from speechbrain.inference.speaker import EncoderClassifier

    return EncoderClassifier.from_hparams(source=str(model_dir), savedir=str(model_dir))


def main() -> int:
    import tkinter as tk

    import numpy as np
    import sounddevice as sd

    try:
        import json
        from pathlib import Path

        cfg_path = Path(os.environ.get("APPDATA", "")) / "Jarvis" / "settings.json"
        dev = json.load(open(cfg_path, encoding="utf-8")).get("wake_mic_device") if cfg_path.exists() else None
    except Exception:
        dev = None

    root = tk.Tk()
    root.title("JARVIS 聲紋錄音")
    root.geometry("520x220")
    root.attributes("-topmost", True)
    big = tk.Label(root, text="準備錄音", font=("Microsoft JhengHei UI", 26, "bold"))
    big.pack(expand=True)
    sub = tk.Label(root, text="", font=("Microsoft JhengHei UI", 14))
    sub.pack(pady=(0, 20))

    def show(main_text, sub_text=""):
        big.config(text=main_text)
        sub.config(text=sub_text)
        root.update()

    show("準備錄音", "戴好 Arctis Nova 7 耳機，準備讀嘢（數數字/讀新聞/講指令）")
    for i in range(3, 0, -1):
        show(f"{i}", "準備...")
        time.sleep(1)

    show("▶ 開始錄音！", "請即刻開始講嘢 30 秒，自然噉講")
    rec = sd.rec(int(DUR * SR), samplerate=SR, channels=1, dtype="float32", device=dev)
    for sec in range(1, DUR + 1):
        time.sleep(1)
        show(f"錄音中 {sec}s / {DUR}s", "繼續講嘢...")
    sd.wait()

    show("錄音完成", "建立聲紋中（第一次要下載 model，可能幾分鐘）...")
    rms = float(np.sqrt(np.mean(np.square(rec[:, 0]))))
    if rms < 0.02:
        show("⚠️ 錄音太靜！", f"RMS={rms:.3f}——可能冇錄到你把聲。建議重新錄（會關閉窗口）")
        root.after(4000, root.destroy)
        root.mainloop()
        return 1

    model = _load_model()
    import torch

    wav = torch.from_numpy(rec[:, 0]).unsqueeze(0)
    with torch.no_grad():
        emb = model.encode_batch(wav).squeeze().cpu().numpy()

    profile_dir = Path(os.environ.get("APPDATA", "")) / "Jarvis"
    profile_dir.mkdir(parents=True, exist_ok=True)
    np.save(str(profile_dir / "voice_profile.npy"), emb)

    # 記低 enrollment 用嘅 mic + 時間——換 mic 聲紋會跌，靠 meta 提示重新 enroll
    from jarvis.speaker_gate import save_meta

    save_meta(mic_device=dev, duration_s=DUR, sample_rate=SR)

    show("✅ 聲紋建立完成！", f"RMS={rms:.3f}（>0.02 合格）· mic_id={dev} · 可以關閉窗口")
    root.after(3000, root.destroy)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
