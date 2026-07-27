"""Autostart unit checks — temp Startup folder, no real boot."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis import autostart as auto


def test_pythonw_prefers_sibling():
    """_pythonw swaps python.exe → pythonw.exe when sibling exists."""
    with tempfile.TemporaryDirectory() as d:
        folder = Path(d)
        py = folder / "python.exe"
        pyw = folder / "pythonw.exe"
        py.write_bytes(b"")
        pyw.write_bytes(b"")
        with mock.patch.object(auto.sys, "executable", str(py)):
            got = auto._pythonw()
        assert got.resolve() == pyw.resolve()


def test_pythonw_keeps_python_if_no_pyw():
    with tempfile.TemporaryDirectory() as d:
        folder = Path(d)
        py = folder / "python.exe"
        py.write_bytes(b"")
        with mock.patch.object(auto.sys, "executable", str(py)):
            got = auto._pythonw()
        assert got.resolve() == py.resolve()


def test_enable_writes_vbs_removes_cmd():
    """enable() writes silent VBS and deletes legacy .cmd."""
    with tempfile.TemporaryDirectory() as d:
        startup = Path(d) / "Startup"
        startup.mkdir()
        legacy = startup / "JARVIS.cmd"
        legacy.write_text(
            "@echo off\r\nstart python -m jarvis serve\r\n", encoding="utf-8"
        )

        with mock.patch.object(auto, "startup_dir", return_value=startup):
            with mock.patch.object(
                auto, "_pythonw", return_value=Path(r"C:\Py\pythonw.exe")
            ):
                with mock.patch.object(
                    auto, "_workdir", return_value=Path(r"C:\repo")
                ):
                    msg = auto.enable()

            vbs = startup / "JARVIS.vbs"
            assert vbs.is_file(), msg
            assert not legacy.exists()
            text = vbs.read_text(encoding="utf-8")
            assert "pythonw.exe" in text
            assert "-m jarvis serve" in text
            assert "CurrentDirectory" in text
            assert ", 0, False" in text
            assert "無黑窗" in msg
            assert auto.is_enabled()
            assert not auto.has_legacy_cmd()


def test_is_enabled_true_for_legacy_only():
    """Old .cmd alone still counts as enabled (so status doesn't lie)."""
    with tempfile.TemporaryDirectory() as d:
        startup = Path(d) / "Startup"
        startup.mkdir()
        (startup / "JARVIS.cmd").write_text("x", encoding="utf-8")
        with mock.patch.object(auto, "startup_dir", return_value=startup):
            assert auto.is_enabled()
            assert auto.has_legacy_cmd()
            assert not (startup / "JARVIS.vbs").is_file()


def test_disable_removes_both():
    """disable() clears VBS and legacy cmd."""
    with tempfile.TemporaryDirectory() as d:
        startup = Path(d) / "Startup"
        startup.mkdir()
        (startup / "JARVIS.vbs").write_text("vbs", encoding="utf-8")
        (startup / "JARVIS.cmd").write_text("cmd", encoding="utf-8")
        with mock.patch.object(auto, "startup_dir", return_value=startup):
            msg = auto.disable()
            assert "已關" in msg
            assert not (startup / "JARVIS.vbs").is_file()
            assert not (startup / "JARVIS.cmd").is_file()
            assert not auto.is_enabled()


def test_disable_legacy_only():
    """disable() when only .cmd exists must not claim '本來就未開啟'."""
    with tempfile.TemporaryDirectory() as d:
        startup = Path(d) / "Startup"
        startup.mkdir()
        (startup / "JARVIS.cmd").write_text("cmd", encoding="utf-8")
        with mock.patch.object(auto, "startup_dir", return_value=startup):
            msg = auto.disable()
            assert "未開啟" not in msg
            assert not auto.is_enabled()


def test_disable_when_nothing():
    with tempfile.TemporaryDirectory() as d:
        startup = Path(d) / "Startup"
        startup.mkdir()
        with mock.patch.object(auto, "startup_dir", return_value=startup):
            msg = auto.disable()
            assert "未開啟" in msg


if __name__ == "__main__":
    for fn in (
        test_pythonw_prefers_sibling,
        test_pythonw_keeps_python_if_no_pyw,
        test_enable_writes_vbs_removes_cmd,
        test_is_enabled_true_for_legacy_only,
        test_disable_removes_both,
        test_disable_legacy_only,
        test_disable_when_nothing,
    ):
        fn()
        print("ok", fn.__name__)
    print("all passed")
