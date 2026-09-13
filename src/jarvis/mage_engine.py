"""Mage-VL local vision engine (lazy-loaded; ~10GB VRAM)."""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

log = logging.getLogger(__name__)

_DEFAULT_MODEL = "microsoft/Mage-VL"
# Pin exact HF revision (2026-08-29): transformers/Mage-VL remote-code is fragile —
# a snapshot update can break load or silently change behavior. Bump deliberately.
_DEFAULT_REVISION = "d88b153285f1633a61b2f693c59c8576693af185"
_engine: MageVLEngine | None = None


def get_mage_engine(model_id: str = _DEFAULT_MODEL) -> MageVLEngine:
    """Process-wide singleton — model load ~10s, keep resident."""
    global _engine
    if _engine is None:
        _engine = MageVLEngine(model_id)
    return _engine


def _ensure_streammind_gate_cached() -> None:
    """Copy streammind_gate.py from HF snapshot if missing from modules cache."""
    snap_root = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / "models--microsoft--Mage-VL"
        / "snapshots"
    )
    mod_root = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "modules"
        / "transformers_modules"
        / "microsoft"
        / "Mage_hyphen_VL"
    )
    if not snap_root.is_dir():
        return
    for snap in snap_root.iterdir():
        src = snap / "streammind_gate.py"
        if not src.is_file():
            continue
        dest = mod_root / snap.name / "streammind_gate.py"
        if dest.is_file():
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        log.info("Copied streammind_gate.py → %s", dest)
        return


class MageVLEngine:
    """Lazy Mage-VL 4B for image understanding."""

    def __init__(self, model_id: str = _DEFAULT_MODEL, revision: str = _DEFAULT_REVISION) -> None:
        self._model_id = model_id
        self._revision = revision
        self._processor = None
        self._model = None
        self._load_time_s: float | None = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def _load(self) -> float:
        """Load processor + model once; return load time in seconds."""
        if self._model is not None:
            return self._load_time_s or 0.0

        _ensure_streammind_gate_cached()

        # Heavy deps only at first use.
        from transformers import AutoModelForCausalLM, AutoProcessor, dynamic_module_utils

        # streammind_gate.py imports mamba_ssm at top level, but the gate is
        # only loaded lazily at runtime and is NOT needed for image inference.
        dynamic_module_utils.check_imports = lambda filename: []

        t0 = time.perf_counter()
        processor = AutoProcessor.from_pretrained(
            self._model_id, revision=self._revision, trust_remote_code=True
        )
        model = AutoModelForCausalLM.from_pretrained(
            self._model_id,
            revision=self._revision,
            trust_remote_code=True,
            torch_dtype="auto",
            device_map="auto",
        ).eval()
        self._processor = processor
        self._model = model
        self._load_time_s = time.perf_counter() - t0
        log.info("Mage-VL loaded in %.2fs", self._load_time_s)
        return self._load_time_s

    def warm(self) -> float | None:
        """Force model load; return load time or None if already loaded."""
        return self._load()

    def understand_image(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail.",
    ) -> str:
        """Run Mage-VL on a local image file; return decoded answer text."""
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        self._load()

        import torch
        from PIL import Image

        processor = self._processor
        model = self._model
        if processor is None or model is None:
            raise RuntimeError("Mage-VL model failed to load")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = processor(
            text=[text],
            images=[Image.open(path).convert("RGB")],
            return_tensors="pt",
        )
        inputs = {
            k: (v.to(model.device) if hasattr(v, "to") else v)
            for k, v in inputs.items()
        }
        if "pixel_values" in inputs:
            inputs["pixel_values"] = inputs["pixel_values"].to(model.dtype)

        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=256, do_sample=False)

        answer = processor.tokenizer.decode(
            output[0, inputs["input_ids"].shape[1] :],
            skip_special_tokens=True,
        )
        return answer.strip()

    def analyze_video_sampled(
        self,
        video_path: str,
        prompt: str = "What is happening in this frame? Be concise.",
        max_frames: int = 8,
    ) -> str:
        """Frame-sampled video understanding (2026-08-31 #10).

        Replaces the deferred codec-native streaming gate (needs mamba_ssm,
        not practical on Windows): extract up to `max_frames` evenly-spaced
        frames with OpenCV, run Mage-VL on each, and merge the observations
        with timestamps. Good enough for game HUD / short-clip reading.
        """
        import cv2
        import tempfile

        path = Path(video_path)
        if not path.is_file():
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")
        try:
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            if total <= 0:
                # Some formats report 0 frames — fall back to a conservative
                # estimate; `step` adapts so we still sample `max_frames` times.
                total = max_frames * 10
            if max_frames <= 0:
                max_frames = 1
            step = max(1, total // max_frames)
            if total < max_frames:
                step = 1

            observations: list[str] = []
            with tempfile.TemporaryDirectory(prefix="mage_frames_") as td:
                idx = 0
                while idx < total and len(observations) < max_frames:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                    ok, frame = cap.read()
                    if ok:
                        frame_path = Path(td) / f"f{idx:05d}.jpg"
                        cv2.imwrite(str(frame_path), frame)
                        ts = idx / fps if fps else idx
                        try:
                            desc = self.understand_image(str(frame_path), prompt)
                            observations.append(f"[{ts:.1f}s] {desc}")
                        except Exception as exc:  # noqa: BLE001
                            observations.append(f"[{ts:.1f}s] (frame error: {exc})")
                    idx += step

            if not observations:
                return "(no frames extracted)"
            return "\n".join(observations)
        finally:
            cap.release()
