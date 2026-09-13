"""Speaker verification gate — Phase 6 A4.

Wake 觸發後，用 speechbrain ECAPA-TDNN 比對聲紋：係 SK（voice_profile.npy）
先醒，其他人講嘢唔觸發。Iron Man「識分人」核心——「唔係聽到聲就醒，
係識分人」。

- Profile: ``%APPDATA%/Jarvis/voice_profile.npy``（192d ECAPA embedding）
- Meta:    ``%APPDATA%/Jarvis/voice_profile_meta.json``（mic device + timestamp）
- Threshold: cosine >= 0.50（2026-08-27 實測：同人 0.9142 vs 異人 <=0.20）
- Windows pitfalls（speechbrain）：
  1. symlink fail（WinError 1314）→ monkeypatch ``link_with_strategy`` 用 copy
  2. model 要 ``huggingface_hub.snapshot_download`` 落 local 再 from_hparams

用法（wake.py）：
    ok = speaker_gate.warm()                       # wake loop 開始時預載
    res = speaker_gate.verify_pcm(pcm, threshold)  # {"accept", "score", "reason", "skip"}
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import time
from pathlib import Path

import numpy as np

PROFILE_PATH = Path(os.environ.get("APPDATA", "")) / "Jarvis" / "voice_profile.npy"
META_PATH = Path(os.environ.get("APPDATA", "")) / "Jarvis" / "voice_profile_meta.json"
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / ".cache" / "ecapa-voxceleb"
MODEL_REPO = "speechbrain/spkrec-ecapa-voxceleb"
DEFAULT_THRESHOLD = 0.50
# 有效音訊少過呢個長度（秒）→ 唔夠特徵，fail-closed（唔醒）
MIN_AUDIO_S = 0.30

_model = None
_model_lock = threading.Lock()
_model_device: str | None = None


# --------------------------------------------------------------------------
# Profile I/O
# --------------------------------------------------------------------------
def profile_path() -> Path:
    return PROFILE_PATH


def profile_exists() -> bool:
    return PROFILE_PATH.is_file()


def load_profile() -> np.ndarray | None:
    """Return 192d embedding vector or None."""
    if not PROFILE_PATH.is_file():
        return None
    try:
        arr = np.load(PROFILE_PATH)
    except Exception:
        return None
    arr = np.asarray(arr, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return None
    return arr


def profile_meta() -> dict:
    try:
        return json.loads(META_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_meta(*, mic_device: int | None, duration_s: float, sample_rate: int = 16000) -> None:
    """記錄 enrollment 用嘅 mic + 時間——換 mic 偵測用（聲紋會跌，要重新 enroll）。"""
    meta = {
        "mic_device": mic_device,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_s": round(float(duration_s), 1),
        "sample_rate": sample_rate,
    }
    try:
        META_PATH.parent.mkdir(parents=True, exist_ok=True)
        META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    except OSError:
        pass


# --------------------------------------------------------------------------
# Model load (Windows-safe)
# --------------------------------------------------------------------------
def _monkeypatch_link() -> None:
    """speechbrain ``from_hparams`` 想 symlink HF cache → Windows 冇權限 → 用 copy。"""
    import speechbrain.utils.fetching as F

    def _copy(src, dst, *args, **kwargs):
        src = Path(src)
        dst = Path(dst)
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            if dst.exists():
                dst.unlink()
            shutil.copy2(src, dst)

    F.link_with_strategy = _copy


def _load_model(device: str = "auto"):
    """Lazy-load EncoderClassifier（thread-safe）。device: auto|cuda|cpu。"""
    global _model, _model_device
    with _model_lock:
        if _model is not None:
            return _model
        _monkeypatch_link()
        if not (MODEL_DIR / "embedding_model.ckpt").exists():
            from huggingface_hub import snapshot_download

            snapshot_download(MODEL_REPO, local_dir=str(MODEL_DIR))
        from speechbrain.inference.speaker import EncoderClassifier

        run_opts: dict = {}
        if device in ("auto", "cuda"):
            try:
                import torch

                if torch.cuda.is_available():
                    run_opts["device"] = "cuda:0"
            except Exception:
                pass
        try:
            _model = EncoderClassifier.from_hparams(
                source=str(MODEL_DIR), savedir=str(MODEL_DIR), run_opts=run_opts
            )
        except Exception:
            if run_opts:  # CUDA 起唔到 → CPU fallback
                _model = EncoderClassifier.from_hparams(
                    source=str(MODEL_DIR), savedir=str(MODEL_DIR)
                )
            else:
                raise
        _model_device = "cuda:0" if run_opts else "cpu"
        return _model


def warm(device: str = "auto") -> bool:
    """Wake loop 開始時預載 model。成功 True。"""
    try:
        _load_model(device)
        return True
    except Exception:
        return False


def model_device() -> str | None:
    return _model_device


def _encode(model, wav_float32: np.ndarray) -> np.ndarray:
    """float32 [-1,1] mono → 192d embedding。"""
    import torch

    wav = torch.from_numpy(np.asarray(wav_float32, dtype=np.float32)).unsqueeze(0)
    dev = getattr(model, "device", None)
    if dev is not None:
        try:
            wav = wav.to(dev)
        except Exception:
            pass
    with torch.no_grad():
        emb = model.encode_batch(wav).squeeze().cpu().numpy()
    return np.asarray(emb, dtype=np.float64).reshape(-1)


def verify_pcm(pcm_int16, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Verify 一段 16k mono 音訊係咪 SK。

    回傳 {"accept": bool, "score": float, "reason": str, "skip": bool}
    - no_profile / model_fail / encode_fail → skip=True, accept=True（fail-open：
      gate 冇得跑就唔好整死 wake；有得跑就嚴格執行）
    - too_short → skip=False, accept=False（fail-closed：唔夠聲證明係你 → 唔醒）
    """
    if pcm_int16 is None:
        return {"accept": False, "score": 0.0, "reason": "empty", "skip": True}
    arr = np.asarray(pcm_int16)
    if arr.size == 0:
        return {"accept": False, "score": 0.0, "reason": "empty", "skip": True}
    if np.issubdtype(arr.dtype, np.floating):
        wav = arr.astype(np.float32)
    else:
        wav = (arr.astype(np.float32) / 32768.0).clip(-1.0, 1.0)
    dur_s = wav.size / 16000.0
    if dur_s < MIN_AUDIO_S:
        return {
            "accept": False,
            "score": 0.0,
            "reason": f"too_short_{dur_s:.2f}s",
            "skip": False,
        }
    prof = load_profile()
    if prof is None:
        return {"accept": True, "score": 0.0, "reason": "no_profile", "skip": True}
    prof_norm = float(np.linalg.norm(prof))
    if prof_norm < 1e-6:
        return {"accept": True, "score": 0.0, "reason": "profile_zero", "skip": True}
    try:
        model = _load_model()
    except Exception as exc:  # noqa: BLE001
        return {"accept": True, "score": 0.0, "reason": f"model_fail:{exc}", "skip": True}
    try:
        emb = _encode(model, wav)
    except Exception as exc:  # noqa: BLE001
        return {"accept": True, "score": 0.0, "reason": f"encode_fail:{exc}", "skip": True}
    emb_norm = float(np.linalg.norm(emb))
    if emb_norm < 1e-6:
        return {"accept": True, "score": 0.0, "reason": "emb_zero", "skip": True}
    score = float(np.dot(emb, prof) / (emb_norm * prof_norm))
    accept = bool(score >= float(threshold))
    return {
        "accept": accept,
        "score": score,
        "threshold": float(threshold),
        "reason": "accept" if accept else "reject",
        "skip": False,
    }
