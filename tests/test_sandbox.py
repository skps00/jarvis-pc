"""Tests for jarvis.sandbox (L1a Docker sandbox, 2026-08-31 #6).

All docker calls are mocked — no real Docker Desktop needed in CI.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.sandbox import SandboxRunner  # noqa: E402


class _P:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


def _mock_run(responses: list[tuple[int, str, str]]):
    calls: list[list[str]] = []

    def fake(args, **kwargs):
        calls.append(list(args))
        rc, out, err = responses[min(len(calls) - 1, len(responses) - 1)]
        return _P(rc, out, err)

    patcher = mock.patch("jarvis.sandbox.subprocess.run", side_effect=fake)
    patcher.start()
    return calls, patcher


def test_docker_available_cached():
    calls, patcher = _mock_run([(0, "27.1.1\n", "")])
    try:
        s = SandboxRunner()
        assert s.docker_available() is True
        assert s.docker_available() is True  # cached — one call only
        assert len(calls) == 1
    finally:
        patcher.stop()


def test_docker_unavailable_fail_closed():
    calls, patcher = _mock_run([(1, "", "cannot connect")])
    try:
        s = SandboxRunner()
        assert s.docker_available() is False
        assert s.ready() is False  # never claims ready on paper
    finally:
        patcher.stop()


def test_ensure_creates_container():
    # version ok, inspect missing, run ok
    calls, patcher = _mock_run([(0, "27.1.1", ""), (1, "", "no such container"), (0, "", "")])
    try:
        s = SandboxRunner(workdir=Path("nonexistent") / "l1a")
        ok, msg = s.ensure()
        assert ok is True
        create = calls[2]
        assert create[0:3] == ["docker", "run", "-d"]
        assert "--network" in create and "none" in create
        assert "/work" in create  # allowlisted mount
        assert "~/.ssh" not in " ".join(create)  # never credentials
    finally:
        patcher.stop()


def test_ensure_skips_when_container_exists():
    calls, patcher = _mock_run([(0, "27.1.1", ""), (0, "exists", "")])
    try:
        s = SandboxRunner()
        ok, msg = s.ensure()
        assert ok is True
        assert len(calls) == 2  # version + inspect; no create
    finally:
        patcher.stop()


def test_run_fails_closed_when_sandbox_down():
    # version fails (2 = real error, not "already starting") -> fail fast
    calls, patcher = _mock_run([(2, "", "daemon down"), (2, "", "daemon down")])
    try:
        s = SandboxRunner()
        code, out = s.run(["echo", "hi"])
        assert code != 0
        assert "unavailable" in out
    finally:
        patcher.stop()


def test_run_execs_inside():
    calls, patcher = _mock_run([(0, "27.1.1", ""), (0, "exists", ""), (0, "hello\n", "")])
    try:
        s = SandboxRunner()
        code, out = s.run(["echo", "hello"])
        assert code == 0
        assert "hello" in out
        assert calls[2][0:3] == ["docker", "exec", "-i"]
    finally:
        patcher.stop()


def test_run_env_cleared_no_credentials():
    # The docker child must not inherit host env (fail-closed).
    captured: dict = {}

    def fake(args, **kwargs):
        captured["env"] = kwargs.get("env")
        return _P(0, "", "")

    with mock.patch("jarvis.sandbox.subprocess.run", side_effect=fake):
        s = SandboxRunner()
        s.docker_available()
        assert captured["env"] is not None
        assert "APPDATA" not in captured["env"]
        assert "USERPROFILE" not in captured["env"]


def test_stop():
    calls, patcher = _mock_run([(0, "", "")])
    try:
        s = SandboxRunner()
        ok, _ = s.stop()
        assert ok is True
        assert calls[0] == ["docker", "stop", "jarvis-sandbox"]
    finally:
        patcher.stop()


def test_ready_requires_daemon_and_container():
    calls, patcher = _mock_run([(0, "27.1.1", ""), (0, "exists", "")])
    try:
        s = SandboxRunner()
        assert s.ready() is True
        assert len(calls) == 2
    finally:
        patcher.stop()
