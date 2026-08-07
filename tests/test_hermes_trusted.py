"""Trusted / Safe Hermes toolset helpers (mocked WSL)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_docker_available_ok():
    from jarvis import hermes_bridge as hb

    fake = mock.Mock(returncode=0, stdout="29.6.2\n", stderr="")
    with mock.patch.object(hb, "_wsl_bash", return_value=fake):
        ok, ver = hb.docker_available()
    assert ok is True
    assert ver == "29.6.2"


def test_apply_trusted_requires_docker():
    from jarvis import hermes_bridge as hb

    with mock.patch.object(hb, "docker_available", return_value=(False, "nope")):
        ok, msg = hb.apply_hermes_trusted_toolsets()
    assert ok is False
    assert "Docker" in msg


def test_apply_trusted_enables_terminal():
    from jarvis import hermes_bridge as hb

    fake = mock.Mock(returncode=0, stdout="ok\n", stderr="")
    with (
        mock.patch.object(hb, "docker_available", return_value=(True, "29")),
        mock.patch.object(hb, "_wsl_bash", return_value=fake) as wsl,
    ):
        ok, msg = hb.apply_hermes_trusted_toolsets()
    assert ok is True
    assert "Trusted" in msg
    cmd = wsl.call_args.args[0]
    assert "tools enable --platform api_server terminal" in cmd
    assert "tools disable --platform api_server" in cmd


if __name__ == "__main__":
    test_docker_available_ok()
    print("ok docker")
    test_apply_trusted_requires_docker()
    print("ok require")
    test_apply_trusted_enables_terminal()
    print("ok enable")
    print("all passed")
