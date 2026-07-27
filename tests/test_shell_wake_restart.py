"""Wake restart race after settings save (no mic / Tk)."""

from __future__ import annotations

import sys
import threading
import time
import types
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.settings import Settings
from jarvis.shell_app import JarvisShell


def test_apply_settings_stop_then_start_when_wake_was_on():
    """Saving settings must restart wake: stop then start."""
    calls: list[str] = []
    shell = mock.Mock()
    shell._wake_on = True
    shell._busy = False
    shell._wake_thread = None
    shell._record_seconds = 4
    shell._wake_cd = 2.0
    shell._wake_threshold = 0.58
    shell.append_log = lambda *_a, **_k: None
    shell.stop_wake = lambda: calls.append("stop")
    shell.start_wake = lambda: calls.append("start")

    JarvisShell.apply_settings(shell, Settings(), restart_wake=True)
    assert calls == ["stop", "start"]


def test_apply_settings_no_restart_when_wake_off():
    calls: list[str] = []
    shell = mock.Mock()
    shell._wake_on = False
    shell._busy = False
    shell._wake_thread = None
    shell._record_seconds = 4
    shell._wake_cd = 2.0
    shell._wake_threshold = 0.58
    shell.append_log = lambda *_a, **_k: None
    shell.stop_wake = lambda: calls.append("stop")
    shell.start_wake = lambda: calls.append("start")

    JarvisShell.apply_settings(shell, Settings(), restart_wake=True)
    assert calls == []


def test_apply_settings_keeps_pause_when_busy():
    calls: list[str] = []
    shell = mock.Mock()
    shell._wake_on = True
    shell._busy = True
    shell._wake_thread = None
    shell._wake_pause = mock.Mock()
    shell._record_seconds = 4
    shell._wake_cd = 2.0
    shell._wake_threshold = 0.58
    shell.append_log = lambda *_a, **_k: None
    shell.stop_wake = lambda: calls.append("stop")
    shell.start_wake = lambda: calls.append("start")

    JarvisShell.apply_settings(shell, Settings(), restart_wake=True)
    assert calls == ["stop", "start"]
    shell._wake_pause.set.assert_called_once()


def test_stop_wake_joins_so_start_can_run():
    """
    Regression: without join, start_wake sees alive thread and returns —
    listening stays off after settings save.
    """
    stop = threading.Event()
    pause = threading.Event()

    def slow_worker() -> None:
        # Mimic wake loop: exit soon after stop, but not instantly.
        while not stop.is_set():
            time.sleep(0.05)
        time.sleep(0.15)

    shell = types.SimpleNamespace(
        _wake_on=True,
        _wake_stop=stop,
        _wake_pause=pause,
        _wake_thread=threading.Thread(target=slow_worker, daemon=True),
        _wake_threshold=0.58,
        _wake_cd=2.0,
        btn_wake=mock.Mock(),
        append_log=lambda *_a, **_k: None,
    )
    shell._wake_thread.start()
    time.sleep(0.05)

    # Old buggy path: signal stop, then immediate start check → still alive.
    stop.set()
    pause.set()
    assert shell._wake_thread.is_alive()

    JarvisShell.stop_wake(shell, join_timeout=2.0)
    assert shell._wake_thread is None or not shell._wake_thread.is_alive()
    assert shell._wake_on is False


if __name__ == "__main__":
    test_apply_settings_stop_then_start_when_wake_was_on()
    print("ok test_apply_settings_stop_then_start_when_wake_was_on")
    test_apply_settings_no_restart_when_wake_off()
    print("ok test_apply_settings_no_restart_when_wake_off")
    test_apply_settings_keeps_pause_when_busy()
    print("ok test_apply_settings_keeps_pause_when_busy")
    test_stop_wake_joins_so_start_can_run()
    print("ok test_stop_wake_joins_so_start_can_run")
    print("all passed")
