"""Headless smoke: companion settings window builds (QA ISSUE-003)."""

from __future__ import annotations

import sys
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis import settings as settings_mod  # noqa: E402
from jarvis.settings import Settings, invalidate_settings_cache  # noqa: E402
from jarvis.settings_ui import SettingsWindow  # noqa: E402


def test_settings_window_builds_four_tabs() -> None:
    """Regression: ISSUE-003 — settings UI constructs without crash.

    Found by /qa on 2026-08-09
    Report: .gstack/qa-reports/qa-report-jarvis-pc-2026-08-09.md
    """
    root = tk.Tk()
    root.withdraw()
    try:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            path = tmp / "settings.json"
            with mock.patch.multiple(
                settings_mod,
                SETTINGS_DIR=tmp,
                SETTINGS_PATH=path,
            ):
                invalidate_settings_cache()
                settings_mod.save_settings(Settings())
                parent = SimpleNamespace(root=root)
                with (
                    mock.patch.object(tk.Toplevel, "grab_set"),
                    mock.patch.object(tk.Toplevel, "focus_force"),
                    mock.patch("jarvis.brain._load_dotenv", return_value=None),
                ):
                    win = SettingsWindow(parent)
                    win.win.withdraw()
                    kids = win.win.winfo_children()
                    notebooks = [c for c in kids if isinstance(c, ttk.Notebook)]
                    assert notebooks, "expected Notebook tabs"
                    nb = notebooks[0]
                    assert nb.index("end") == 4
                    win.win.destroy()
    finally:
        root.destroy()
