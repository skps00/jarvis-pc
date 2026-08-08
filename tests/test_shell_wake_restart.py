"""apply_settings + wake pause guards."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.settings import Settings
from jarvis.shell_app import JarvisShell


def test_apply_settings_logs_hermes_and_clears_trusted_when_off():
    shell = mock.Mock()
    shell._hermes_trusted_until = 99.0
    logs: list[str] = []
    shell.append_log = logs.append
    shell.clear_hermes_trusted = mock.Mock()
    shell._wake_on = False

    JarvisShell.apply_settings(shell, Settings(hermes_enabled=False, llm_model="x"))
    shell.clear_hermes_trusted.assert_called_once()
    assert any("Hermes=off" in line for line in logs)


def test_apply_settings_keeps_trusted_hook_when_hermes_on():
    shell = mock.Mock()
    shell._wake_on = False
    logs: list[str] = []
    shell.append_log = logs.append
    shell.clear_hermes_trusted = mock.Mock()

    JarvisShell.apply_settings(shell, Settings(hermes_enabled=True, llm_model="y"))
    shell.clear_hermes_trusted.assert_not_called()
    assert any("Hermes=on" in line for line in logs)


def test_clear_hermes_trusted_noop_when_already_safe():
    shell = mock.Mock()
    shell._hermes_trusted_until = 0.0
    shell.append_log = mock.Mock()
    shell._ui_queue = mock.Mock()
    with mock.patch("jarvis.hermes_bridge.apply_hermes_safe_toolsets") as apply:
        JarvisShell.clear_hermes_trusted(shell)
    apply.assert_not_called()
    shell.append_log.assert_not_called()


def test_hermes_is_trusted_expires_and_clears():
    shell = mock.Mock()
    shell._hermes_trusted_until = time.monotonic() - 1.0
    shell.append_log = mock.Mock()
    shell.clear_hermes_trusted = mock.Mock()
    assert JarvisShell.hermes_is_trusted(shell) is False
    shell.clear_hermes_trusted.assert_called_once()
    shell.append_log.assert_any_call("[ok] Trusted 到期 → Safe")


def test_set_busy_keeps_pause_while_tts_holds():
    shell = mock.Mock()
    shell._busy = False
    shell._tts_holding_pause = True
    shell._wake_pause = threading.Event()
    shell._wake_pause.set()
    shell.btn_send = mock.Mock()
    shell.entry = mock.Mock()

    JarvisShell._set_busy(shell, False)
    assert shell._wake_pause.is_set()


def test_set_busy_clears_pause_when_idle():
    shell = mock.Mock()
    shell._busy = True
    shell._tts_holding_pause = False
    shell._wake_pause = threading.Event()
    shell._wake_pause.set()
    shell.btn_send = mock.Mock()
    shell.entry = mock.Mock()

    JarvisShell._set_busy(shell, False)
    assert not shell._wake_pause.is_set()


if __name__ == "__main__":
    test_apply_settings_logs_hermes_and_clears_trusted_when_off()
    print("ok off")
    test_apply_settings_keeps_trusted_hook_when_hermes_on()
    print("ok on")
    test_clear_hermes_trusted_noop_when_already_safe()
    print("ok noop")
    test_hermes_is_trusted_expires_and_clears()
    print("ok expire")
    test_set_busy_keeps_pause_while_tts_holds()
    print("ok tts hold")
    test_set_busy_clears_pause_when_idle()
    print("ok clear")
    print("all passed")
