"""Tests for jarvis.shell_app helpers."""

from __future__ import annotations

from jarvis.shell_app import game_ready_phrase


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
