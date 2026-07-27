"""Hands MC / Steam already-running helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.hands import (
    _cmdline_matches_instance,
    _launch_or_close_steam,
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


if __name__ == "__main__":
    test_cmdline_matches_instance()
    test_steam_toggle_close_when_running()
    test_steam_toggle_cancel()
    test_steam_force_new_skips_close()
    print("all passed")
