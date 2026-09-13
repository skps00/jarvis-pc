"""Tests for jarvis.shell_app helpers."""

from __future__ import annotations

from unittest import mock

from jarvis.shell_app import _pick_spoken_line, game_ready_phrase


def test_game_ready_phrase_minecraft() -> None:
    assert game_ready_phrase("minecraft") == "Minecraft"


def test_game_ready_phrase_cs2() -> None:
    assert game_ready_phrase("CS2") == "CS2"


def test_game_ready_phrase_counter_strike() -> None:
    assert game_ready_phrase("counter-strike 2") == "Counter-strike 2"


def test_game_ready_phrase_empty() -> None:
    assert game_ready_phrase("") == "game"


def test_game_ready_phrase_none() -> None:
    assert game_ready_phrase(None) == "game"


def test_pick_spoken_line_translates_cjk_ok() -> None:
    with mock.patch(
        "jarvis.brain.translate_to_english_short",
        return_value="Opened Cursor, sir.",
    ):
        assert _pick_spoken_line(["[ok] 已開 Cursor"]) == "Opened Cursor, sir."


def test_pick_spoken_line_cjk_without_translation() -> None:
    with mock.patch(
        "jarvis.brain.translate_to_english_short",
        return_value=None,
    ):
        assert _pick_spoken_line(["[ok] 已開 Cursor"]) == "已開 Cursor"
