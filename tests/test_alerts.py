"""Unit checks for Discord / Cursor / WhatsApp alert heuristics."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.alerts import (
    alert_phrase_for,
    classify_exe,
    cursor_attention_phrase,
    cursor_needs_attention,
    cursor_titles_busy,
    cursor_toast_is_done,
    cursor_uia_name_is_wait,
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
    assert not cursor_titles_busy(["Plan Mode — Cursor"])  # bare planning gone
    assert cursor_titles_busy(["Cursor — Generating"])
    assert cursor_titles_busy(["thinking… — Cursor"])


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


def test_cursor_needs_attention_plan_and_approval():
    assert not cursor_needs_attention([])
    assert not cursor_needs_attention(["Random toast"])
    assert cursor_needs_attention(
        ["Done — x", "Open Cursor to view the agent's output."]
    )
    assert cursor_needs_attention(["Waiting for approval"])
    assert cursor_needs_attention(["Switch mode", "Switch", "Skip"])
    assert cursor_needs_attention(["Agent wants to switch to plan mode"])
    assert "plan mode" in alert_phrase_for("cursor_plan").lower()
    assert "approval" in alert_phrase_for("cursor_approve").lower()
    assert "plan" in cursor_attention_phrase(
        ["Waiting for approval", "Plan Mode"]
    ).lower()
    assert "approval" in cursor_attention_phrase(
        ["Waiting for approval"]
    ).lower()


def test_cursor_uia_wait_exact_not_chat():
    assert cursor_uia_name_is_wait("Waiting for approval")
    assert cursor_uia_name_is_wait("  waiting for approval  ")
    # Chat bubble quoting our docs must NOT match
    assert not cursor_uia_name_is_wait(
        "Cursor 切 Plan／Waiting for approval → 有講、無 CMD。Disc"
    )
    assert not cursor_uia_name_is_wait("Still waiting for approval tomorrow")


if __name__ == "__main__":
    test_discord_unread_max()
    test_discord_taskbar_unread()
    test_cursor_busy_keywords()
    test_classify_exe()
    test_toast_whatsapp_and_extra()
    test_cursor_needs_attention_plan_and_approval()
    test_cursor_uia_wait_exact_not_chat()
    print("all passed")
