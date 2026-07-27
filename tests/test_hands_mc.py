"""Hands MC / Steam already-running helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.config import Profile, Registry
from jarvis import memory as mem
from jarvis.hands import (
    _cmdline_matches_instance,
    _launch_or_close_steam,
    _launch_or_focus_shell_app,
    _remember_launch_pids,
    close_profile,
)


def test_cmdline_matches_instance():
    iid = "No_Flesh_Within_Chest-1.0.2-DIM"
    assert _cmdline_matches_instance(
        r"javaw -Djava.library.path=C:\instances\No_Flesh_Within_Chest-1.0.2-DIM\natives",
        iid,
    )
    assert not _cmdline_matches_instance("javaw -jar other.jar", iid)


def test_steam_toggle_close_when_running():
    launch = {"type": "steam_app", "app_id": "730", "process_names": ["cs2.exe"]}
    with mock.patch("jarvis.hands._any_process_running", return_value=True):
        with mock.patch("jarvis.hands._kill_images") as kill:
            msg = _launch_or_close_steam(
                launch,
                display_name="Counter-Strike 2",
                ask_confirm=lambda _p: True,
                force_new=False,
            )
    assert msg.startswith("已關閉")
    kill.assert_called_once()


def test_steam_toggle_cancel():
    launch = {"type": "steam_app", "app_id": "730", "process_names": ["cs2.exe"]}
    with mock.patch("jarvis.hands._any_process_running", return_value=True):
        msg = _launch_or_close_steam(
            launch,
            display_name="Counter-Strike 2",
            ask_confirm=lambda _p: False,
            force_new=False,
        )
    assert msg.startswith("已取消")


def test_steam_force_new_skips_close():
    launch = {"type": "steam_app", "app_id": "730", "process_names": ["cs2.exe"]}
    with mock.patch("jarvis.hands._any_process_running", return_value=True):
        with mock.patch("jarvis.hands._launch_steam") as launch_fn:
            msg = _launch_or_close_steam(
                launch,
                display_name="Counter-Strike 2",
                ask_confirm=lambda _p: True,
                force_new=True,
            )
    assert "已新開" in msg
    launch_fn.assert_called_once()


def test_memory_profile_pids_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        mem.set_profile_pids("discord", [111, 222], path)
        assert mem.get_profile_pids("discord", path) == [111, 222]
        mem.clear_profile_pids("discord", path)
        assert mem.get_profile_pids("discord", path) == []


def test_remember_launch_pids_merges():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        mem.set_profile_pids("discord", [100], path)
        with mock.patch("jarvis.hands._alive_remembered_pids", return_value=[100]):
            with mock.patch("jarvis.hands._wait_new_pids", return_value=[200, 201]):
                merged = _remember_launch_pids(
                    "discord", ["Discord.exe"], set(), memory_path=path
                )
        assert merged == [100, 200, 201]
        assert mem.get_profile_pids("discord", path) == [100, 200, 201]


def test_close_prefers_remembered_pids():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        mem.set_profile_pids("discord", [4242], path)
        profile = Profile(
            id="discord",
            display_name="Discord",
            kind="app",
            enabled=True,
            names=["Discord"],
            locale_hints=[],
            launch={"type": "app_lnk", "lnk": r"C:\fake\Discord.lnk"},
            restore={},
        )
        reg = mock.MagicMock(spec=Registry)
        reg.profiles = {"discord": profile}
        with mock.patch("jarvis.hands._alive_remembered_pids", return_value=[4242]):
            with mock.patch("jarvis.hands._kill_pids") as kill:
                result = close_profile(
                    reg,
                    "discord",
                    ask_confirm=lambda _p: True,
                    memory_path=path,
                )
        assert result.ok
        kill.assert_called_once_with([4242])
        assert mem.get_profile_pids("discord", path) == []


def test_close_shell_app_window_pid_fallback():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        profile = Profile(
            id="whatsapp",
            display_name="WhatsApp",
            kind="app",
            enabled=True,
            names=["WhatsApp"],
            locale_hints=[],
            launch={"type": "shell_app", "app_id": "5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"},
            restore={},
        )
        reg = mock.MagicMock(spec=Registry)
        reg.profiles = {"whatsapp": profile}
        with mock.patch("jarvis.hands._alive_remembered_pids", return_value=[]):
            with mock.patch("jarvis.hands._window_pids_title_contains", return_value=[9898]):
                with mock.patch("jarvis.hands._kill_pids") as kill:
                    result = close_profile(
                        reg,
                        "whatsapp",
                        ask_confirm=lambda _p: True,
                        memory_path=path,
                    )
        assert result.ok
        kill.assert_called_once_with([9898])


def test_shell_app_focus_when_already_running():
    launch = {"type": "shell_app", "app_id": "X!App"}
    with mock.patch("jarvis.hands._window_pids_title_contains", return_value=[1]):
        with mock.patch("jarvis.hands._focus_window_title_contains", return_value=True) as focus:
            with mock.patch("jarvis.hands._launch_shell_app") as launch_fn:
                msg = _launch_or_focus_shell_app(
                    launch, display_name="WhatsApp", force_new=False
                )
    assert "已切換" in msg
    focus.assert_called()
    launch_fn.assert_not_called()


def test_shell_app_launches_when_not_running():
    launch = {"type": "shell_app", "app_id": "X!App"}
    with mock.patch("jarvis.hands._window_pids_title_contains", return_value=[]):
        with mock.patch("jarvis.hands._focus_window_title_contains", side_effect=[False, True]):
            with mock.patch("jarvis.hands._launch_shell_app") as launch_fn:
                with mock.patch("jarvis.hands.time.sleep"):
                    msg = _launch_or_focus_shell_app(
                        launch, display_name="WhatsApp", force_new=False
                    )
    assert "已啟動" in msg
    launch_fn.assert_called_once()


if __name__ == "__main__":
    test_cmdline_matches_instance()
    test_steam_toggle_close_when_running()
    test_steam_toggle_cancel()
    test_steam_force_new_skips_close()
    test_memory_profile_pids_roundtrip()
    test_remember_launch_pids_merges()
    test_close_prefers_remembered_pids()
    test_close_shell_app_window_pid_fallback()
    test_shell_app_focus_when_already_running()
    test_shell_app_launches_when_not_running()
    print("all passed")
