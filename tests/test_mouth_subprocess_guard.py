"""mouth subprocess must forward guard= so lenient chat is not strict-swallowed."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from jarvis import mouth


def test_subprocess_code_includes_lenient_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codes: list[str] = []

    def fake_run(cmd, **_kw):
        # [_tts_python(), "-c", code]
        codes.append(cmd[2])
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(mouth, "_prefer_subprocess", True)
    monkeypatch.setattr(subprocess, "run", fake_run)
    ok = mouth.speak(
        "Sir, the year is 2026 = fine.",
        guard="lenient",
        blocking=True,
        force=True,
    )
    assert ok is True
    assert codes
    assert "guard='lenient'" in codes[0]
