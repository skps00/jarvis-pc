"""Unit checks for Discord / Cursor / WhatsApp alert heuristics."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.alerts import (
    alert_phrase_for,
    classify_exe,
    cursor_titles_busy,
    cursor_toast_is_done,
    discord_taskbar_unread,
    discord_unread_count,
    parse_extra_apps,
    toast_app_kind,
)


def test_discord_unread_max():
    assert discord_unread_count([]) == 0
    assert discord_unread_count(["Discord"]) == 0
    assert discord_unread_count(["(3) Discord"]) == 3


def test_discord_taskbar_unread():
    assert discord_taskbar_unread("Discord") == 0
    assert discord_taskbar_unread("Discord - 1 個通知尚未讀取") == 1
    assert discord_taskbar_unread("Discord - 3 unread messages") == 3
    assert discord_taskbar_unread("DiscordPTB - 2 notifications") == 2
    assert discord_taskbar_unread("Discord - Unread Messages") == 1


def test_cursor_busy_keywords():
    assert not cursor_titles_busy(["Cursor Agents"])
    assert cursor_titles_busy(["Cursor — Generating"])


def test_classify_exe():
    assert classify_exe(r"C:\x\Discord.exe") == "discord"
    assert classify_exe(r"C:\x\Cursor.exe") == "cursor"
    assert classify_exe(r"C:\x\WhatsApp.exe") == "whatsapp"


def test_toast_whatsapp_and_extra():
    assert toast_app_kind("WhatsApp") == "whatsapp"
    assert toast_app_kind("", aumid="com.squirrel.Discord.Discord") == "discord"
    assert toast_app_kind("Telegram Desktop", extra=["telegram"]) == (
        "extra:Telegram Desktop"
    )
    assert parse_extra_apps("Telegram, Slack") == ["telegram", "slack"]
    assert "WhatsApp" in alert_phrase_for("whatsapp")
    assert cursor_toast_is_done(["Done — x", "Open Cursor to view the agent's output."])


if __name__ == "__main__":
    test_discord_unread_max()
    test_discord_taskbar_unread()
    test_cursor_busy_keywords()
    test_classify_exe()
    test_toast_whatsapp_and_extra()
    print("all passed")
