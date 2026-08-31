"""Tests for jarvis.mage_engine analyze_video_sampled (2026-08-31 #10).

Mocks OpenCV capture + understand_image — no model load, no real video.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.mage_engine import MageVLEngine  # noqa: E402


class _FakeCap:
    """cv2.VideoCapture lookalike. `total` is what get() reports; `read`
    simulates `read_total` frames (so a "reports 0" camera still reads)."""

    def __init__(self, total=20, fps=10.0, opened=True, read_total=None):
        self._total = total
        self._fps = fps
        self._opened = opened
        self._read_total = read_total if read_total is not None else max(total, 1)
        self._pos = 0

    def isOpened(self):
        return self._opened

    def get(self, prop):
        # cv2 constants: CAP_PROP_FRAME_COUNT=7, CAP_PROP_FPS=5
        if prop == 7:
            return self._total
        if prop == 5:
            return self._fps
        return 0.0

    def set(self, prop, value):
        if prop == 1:  # CAP_PROP_POS_FRAMES
            self._pos = int(value)
        return True

    def read(self):
        if self._pos >= self._read_total:
            return False, None
        import numpy as np

        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        return True, frame

    def release(self):
        self._opened = False


def _dummy_video(tmp_path) -> Path:
    p = tmp_path / "fake.mp4"
    p.write_bytes(b"not a real video (cv2 is mocked)")
    return p


def test_analyze_video_sampled_extracts_frames(tmp_path):
    eng = MageVLEngine()
    eng._processor = mock.Mock()  # avoid real load
    eng._model = mock.Mock()
    eng.understand_image = mock.Mock(
        side_effect=lambda p, prompt=None: f"desc-{Path(p).stem}"
    )

    with mock.patch("cv2.VideoCapture", return_value=_FakeCap(total=20, fps=10)):
        out = eng.analyze_video_sampled(str(_dummy_video(tmp_path)), max_frames=4)

    assert "desc-f00000" in out
    assert len(out.splitlines()) == 4  # 4 frames sampled
    assert eng.understand_image.call_count == 4


def test_analyze_video_sampled_max_frames_respected(tmp_path):
    eng = MageVLEngine()
    eng._processor = mock.Mock()
    eng._model = mock.Mock()
    eng.understand_image = mock.Mock(side_effect=lambda p, prompt=None: "x")

    with mock.patch("cv2.VideoCapture", return_value=_FakeCap(total=100, fps=25)):
        out = eng.analyze_video_sampled(str(_dummy_video(tmp_path)), max_frames=8)

    assert len(out.splitlines()) == 8
    assert eng.understand_image.call_count == 8


def test_analyze_video_sampled_missing_file_raises():
    eng = MageVLEngine()
    try:
        eng.analyze_video_sampled("nonexistent.mp4")
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")


def test_analyze_video_sampled_cannot_open_raises(tmp_path):
    eng = MageVLEngine()
    p = _dummy_video(tmp_path)
    try:
        with mock.patch("cv2.VideoCapture", return_value=_FakeCap(opened=False)):
            eng.analyze_video_sampled(str(p))
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError for unopenable video")


def test_analyze_video_sampled_zero_frame_count_fallback(tmp_path):
    # Some formats report 0 frames — must still sample.
    eng = MageVLEngine()
    eng._processor = mock.Mock()
    eng._model = mock.Mock()
    eng.understand_image = mock.Mock(side_effect=lambda p, prompt=None: "x")

    with mock.patch(
        "cv2.VideoCapture",
        return_value=_FakeCap(total=0, fps=0, read_total=30),
    ):
        out = eng.analyze_video_sampled(str(_dummy_video(tmp_path)), max_frames=3)

    assert len(out.splitlines()) == 3


def test_analyze_video_sampled_frame_error_tolerated(tmp_path):
    # One frame failing must not kill the whole analysis.
    eng = MageVLEngine()
    eng._processor = mock.Mock()
    eng._model = mock.Mock()
    eng.understand_image = mock.Mock(side_effect=RuntimeError("boom"))

    with mock.patch("cv2.VideoCapture", return_value=_FakeCap(total=10, fps=10)):
        out = eng.analyze_video_sampled(str(_dummy_video(tmp_path)), max_frames=3)

    assert "(frame error:" in out
