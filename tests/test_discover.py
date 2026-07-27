"""Discover sources: Start Menu / Desktop / Local Programs / Get-StartApps."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.discover import (
    Candidate,
    _score_name,
    clear_start_apps_cache,
    discover_candidates,
)
from jarvis.persist import commit_candidate


def _empty_registry():
    reg = mock.MagicMock()
    reg.profiles = {}
    return reg


def test_score_whatsapp():
    assert _score_name("whatsapp", "WhatsApp") == 100.0
    assert _score_name("Whats", "WhatsApp") >= 80.0
    assert _score_name("whatapp", "WhatsApp") >= 50.0


def test_start_apps_whatsapp_candidate():
    clear_start_apps_cache()
    with mock.patch(
        "jarvis.discover._load_start_apps",
        return_value=[
            ("WhatsApp", "5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"),
            ("Discord", "com.squirrel.Discord.Discord"),
        ],
    ):
        # also silence filesystem scans
        with mock.patch("jarvis.discover._from_start_menu", return_value=[]):
            with mock.patch("jarvis.discover._from_desktop", return_value=[]):
                with mock.patch("jarvis.discover._from_local_programs", return_value=[]):
                    with mock.patch("jarvis.discover._from_steam", return_value=[]):
                        hits = discover_candidates("whatsapp", _empty_registry())
    assert hits
    assert hits[0].label == "WhatsApp"
    assert hits[0].launch_hint["type"] == "shell_app"
    assert "WhatsAppDesktop" in hits[0].launch_hint["app_id"]


def test_desktop_lnk_preferred_over_start_apps_same_score():
    clear_start_apps_cache()
    desk = Candidate(
        label="WhatsApp",
        kind="desktop",
        launch_hint={"type": "app_exe", "lnk": r"C:\Users\x\Desktop\WhatsApp.lnk"},
        score=100.0,
    )
    store = Candidate(
        label="WhatsApp",
        kind="start_apps",
        launch_hint={"type": "shell_app", "app_id": "X!App"},
        score=100.0,
    )
    with mock.patch("jarvis.discover._from_start_menu", return_value=[]):
        with mock.patch("jarvis.discover._from_desktop", return_value=[desk]):
            with mock.patch("jarvis.discover._from_local_programs", return_value=[]):
                with mock.patch("jarvis.discover._from_start_apps", return_value=[store]):
                    with mock.patch("jarvis.discover._from_steam", return_value=[]):
                        hits = discover_candidates("whatsapp", _empty_registry())
    assert len(hits) == 1
    assert hits[0].kind == "desktop"


def test_commit_shell_app():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "profiles.yaml"
        path.write_text("profiles: []\n", encoding="utf-8")
        cand = Candidate(
            label="WhatsApp",
            kind="start_apps",
            launch_hint={
                "type": "shell_app",
                "app_id": "5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
            },
            score=100.0,
        )
        pid = commit_candidate(cand, path=path)
        text = path.read_text(encoding="utf-8")
        assert pid == "whatsapp"
        assert "shell_app" in text
        assert "WhatsAppDesktop" in text
        assert "WhatsApp.exe" in text


def test_commit_local_exe():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "profiles.yaml"
        path.write_text("profiles: []\n", encoding="utf-8")
        cand = Candidate(
            label="FooApp",
            kind="local_programs",
            launch_hint={"type": "app_exe", "exe": r"C:\Users\x\AppData\Local\Programs\Foo\FooApp.exe"},
            score=100.0,
        )
        pid = commit_candidate(cand, path=path)
        text = path.read_text(encoding="utf-8")
        assert pid == "fooapp"
        assert "FooApp.exe" in text


if __name__ == "__main__":
    test_score_whatsapp()
    test_start_apps_whatsapp_candidate()
    test_desktop_lnk_preferred_over_start_apps_same_score()
    test_commit_shell_app()
    test_commit_local_exe()
    print("all passed")
