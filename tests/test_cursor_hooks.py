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


def test_hook_script_enqueues_completed() -> None:
    script = ROOT / "scripts" / "cursor_hook_alert.py"
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        env = {
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
            "APPDATA": str(tp),
        }
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({"status": "completed", "loop_count": 0}),
            text=True,
            capture_output=True,
            env=env,
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
        env = {
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
            "APPDATA": str(tp),
        }
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({"status": "aborted"}),
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
        env = {
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
            "APPDATA": str(tp),
        }
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
            env=env,
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


if __name__ == "__main__":
    test_hook_script_enqueues_completed()
    test_hook_script_skips_aborted()
    test_hook_script_pretool_switchmode()
    test_install_merges_stop()
    print("all passed")
