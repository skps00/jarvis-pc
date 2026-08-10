"""Cursor stop-hook → alert queue."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.cursor_hooks import (  # noqa: E402
    HOOK_MARKER,
    hook_command,
    install,
    is_installed,
    load_hooks,
    uninstall,
)


def _hook_env(tp: Path) -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
        "APPDATA": str(tp),
        "JARVIS_ALERT_CURSOR_HOOKS": "1",
    }


def test_hook_script_enqueues_completed() -> None:
    script = ROOT / "scripts" / "cursor_hook_alert.py"
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({"status": "completed", "loop_count": 0}),
            text=True,
            capture_output=True,
            env=_hook_env(tp),
            timeout=30,
        )
        assert proc.returncode == 0, proc.stderr
        assert json.loads(proc.stdout or "{}") == {}
        qpath = tp / "Jarvis" / "alerts" / "queue.jsonl"
        assert qpath.is_file(), proc.stderr
        rows = [
            json.loads(line)
            for line in qpath.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert rows[-1]["phrase"] == "Cursor finished its work."
        assert rows[-1]["kind"] == "cursor"


def test_hook_script_skips_aborted() -> None:
    script = ROOT / "scripts" / "cursor_hook_alert.py"
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({"status": "aborted"}),
            text=True,
            capture_output=True,
            env=_hook_env(tp),
            timeout=30,
        )
        assert proc.returncode == 0
        qpath = tp / "Jarvis" / "alerts" / "queue.jsonl"
        assert not qpath.is_file() or not qpath.read_text(encoding="utf-8").strip()


def test_hook_script_disabled_by_env() -> None:
    script = ROOT / "scripts" / "cursor_hook_alert.py"
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        env = _hook_env(tp)
        env["JARVIS_ALERT_CURSOR_HOOKS"] = "0"
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({"status": "completed", "loop_count": 0}),
            text=True,
            capture_output=True,
            env=env,
            timeout=30,
        )
        assert proc.returncode == 0
        qpath = tp / "Jarvis" / "alerts" / "queue.jsonl"
        assert not qpath.is_file() or not qpath.read_text(encoding="utf-8").strip()


def test_hook_script_pretool_switchmode() -> None:
    script = ROOT / "scripts" / "cursor_hook_alert.py"
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(
                {
                    "hook_event_name": "preToolUse",
                    "tool_name": "SwitchMode",
                    "tool_input": {"target_mode_id": "plan"},
                }
            ),
            text=True,
            capture_output=True,
            env=_hook_env(tp),
            timeout=30,
        )
        assert proc.returncode == 0, proc.stderr
        qpath = tp / "Jarvis" / "alerts" / "queue.jsonl"
        rows = [
            json.loads(line)
            for line in qpath.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert "plan" in rows[-1]["phrase"].lower()


def test_install_merges_stop() -> None:
    with tempfile.TemporaryDirectory() as td:
        home_cursor = Path(td) / ".cursor"
        with mock.patch("jarvis.cursor_hooks.cursor_dir", return_value=home_cursor):
            p = home_cursor / "hooks.json"
            p.parent.mkdir(parents=True)
            p.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "hooks": {"stop": [{"command": "echo other"}]},
                    }
                ),
                encoding="utf-8",
            )
            msg = install()
            assert "[ok]" in msg
            assert is_installed()
            data = load_hooks()
            stops = data["hooks"]["stop"]
            assert any("echo other" in str(e.get("command")) for e in stops)
            assert any(HOOK_MARKER in str(e.get("command")) for e in stops)
            assert any(
                HOOK_MARKER in str(e.get("command"))
                for e in data["hooks"]["preToolUse"]
            )
            assert HOOK_MARKER in hook_command()
            uninstall()
            assert not is_installed()


def test_hook_script_pretool_suppresses_following_stop() -> None:
    script = ROOT / "scripts" / "cursor_hook_alert.py"
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        env = _hook_env(tp)
        r1 = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(
                {
                    "hook_event_name": "preToolUse",
                    "tool_name": "SwitchMode",
                    "tool_input": {"target_mode_id": "plan"},
                }
            ),
            text=True,
            capture_output=True,
            env=env,
            timeout=30,
        )
        assert r1.returncode == 0, r1.stderr
        r2 = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({"status": "completed", "loop_count": 0}),
            text=True,
            capture_output=True,
            env=env,
            timeout=30,
        )
        assert r2.returncode == 0, r2.stderr
        qpath = tp / "Jarvis" / "alerts" / "queue.jsonl"
        rows = [
            json.loads(line)
            for line in qpath.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(rows) == 1
        assert "plan" in rows[0]["phrase"].lower()


def test_hook_empty_stdin_noop() -> None:
    script = ROOT / "scripts" / "cursor_hook_alert.py"
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        proc = subprocess.run(
            [sys.executable, str(script)],
            input="",
            text=True,
            capture_output=True,
            env=_hook_env(tp),
            timeout=30,
        )
        assert proc.returncode == 0
        qpath = tp / "Jarvis" / "alerts" / "queue.jsonl"
        assert not qpath.is_file()


def test_mark_waiting_refresh_extends_suppress() -> None:
    """Regression: ISSUE-001 — UIA still visible must refresh suppress window.

    Found by /qa on 2026-08-09
    Report: .gstack/qa-reports/qa-report-jarvis-pc-2026-08-09.md
    """
    import time

    from jarvis.cursor_hooks import mark_waiting, wait_flag_path, waiting_active

    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        with mock.patch.dict(os.environ, {"APPDATA": str(tp)}):
            mark_waiting(seconds=2.0)
            first = float(wait_flag_path().read_text(encoding="utf-8").strip())
            time.sleep(0.05)
            mark_waiting(seconds=180.0)
            second = float(wait_flag_path().read_text(encoding="utf-8").strip())
            assert second > first
            assert waiting_active()


if __name__ == "__main__":
    test_hook_script_enqueues_completed()
    test_hook_script_skips_aborted()
    test_hook_script_disabled_by_env()
    test_hook_script_pretool_switchmode()
    test_hook_script_pretool_suppresses_following_stop()
    test_hook_empty_stdin_noop()
    test_install_merges_stop()
    test_mark_waiting_refresh_extends_suppress()
    print("all passed")
