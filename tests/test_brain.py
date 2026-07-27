"""Brain unit checks — mock HTTP, no live API."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.brain import (
    intent_from_llm_json,
    llm_configured,
    looks_ambiguous,
    resolve_ambiguous,
)
from jarvis.config import load_registry
from jarvis.engine import execute_utterance
from jarvis.router import apply_verb_kind_limits, route


def _reg():
    return load_registry(ROOT / "config" / "profiles.example.yaml")


def test_llm_configured_false_without_key():
    import jarvis.brain as brain

    with mock.patch.object(brain, "_load_dotenv", lambda: None):
        with mock.patch.dict(
            os.environ,
            {"JARVIS_LLM_API_KEY": "", "OPENAI_API_KEY": ""},
            clear=False,
        ):
            assert llm_configured() is False


def test_intent_from_json_force_new_browser():
    r = _reg()
    intent = intent_from_llm_json(
        {
            "intent": "open_profile",
            "target_raw": "browser",
            "profile_id": None,
            "force_new": True,
            "speak_caption": "新開瀏覽器",
        },
        r,
        raw_text="开个 new browser",
    )
    assert intent is not None
    assert intent.kind == "open_profile"
    assert intent.profile_id == "browser-main"
    assert intent.force_new


def test_intent_rejects_path_and_illegal_id():
    r = _reg()
    bad = intent_from_llm_json(
        {
            "intent": "open_profile",
            "target_raw": r"C:\Evil\hack.exe",
            "force_new": False,
        },
        r,
        raw_text="open hack",
    )
    assert bad is not None
    assert bad.kind == "refuse"

    dropped = intent_from_llm_json(
        {
            "intent": "open_profile",
            "target_raw": "Chrome",
            "profile_id": "not-a-real-id",
            "force_new": False,
        },
        r,
        raw_text="開 Chrome",
    )
    assert dropped is not None
    assert dropped.kind == "open_profile"
    assert dropped.profile_id == "browser-main"


def test_resolve_ambiguous_mocked():
    r = _reg()
    fake = json.dumps(
        {
            "intent": "open_profile",
            "target_raw": "Cursor",
            "profile_id": None,
            "force_new": True,
            "speak_caption": "新開 Cursor",
        }
    )
    with mock.patch("jarvis.brain._chat", return_value=fake):
        # 須有明確開動詞，否則 hard gate 會 refuse／改關
        intent = resolve_ambiguous("搞個 open Cursor 出嚟", r)
    assert intent is not None
    assert intent.kind == "open_profile"
    assert intent.profile_id == "cursor"
    assert intent.force_new


def test_resolve_ambiguous_no_verb_refuses():
    r = _reg()
    fake = json.dumps(
        {
            "intent": "open_profile",
            "target_raw": "Cursor",
            "profile_id": "cursor",
            "force_new": False,
            "speak_caption": "開 Cursor",
        }
    )
    with mock.patch("jarvis.brain._chat", return_value=fake):
        intent = resolve_ambiguous("Cursor", r)
    assert intent is not None
    assert intent.kind == "refuse"


def test_resolve_ambiguous_close_hint_flips():
    r = _reg()
    fake = json.dumps(
        {
            "intent": "open_profile",
            "target_raw": "Cursor",
            "profile_id": "cursor",
            "force_new": False,
            "speak_caption": "開 Cursor",
        }
    )
    with mock.patch("jarvis.brain._chat", return_value=fake):
        intent = resolve_ambiguous("close Cursor", r)
    assert intent is not None
    assert intent.kind == "close_profile"


def test_looks_ambiguous():
    r = _reg()
    i = apply_verb_kind_limits(route("開 未知軟體xyz", r), r)
    assert i.kind in ("refuse", "unknown")
    assert looks_ambiguous(i, "開 未知軟體xyz")
    clear = apply_verb_kind_limits(route("開 Cursor", r), r)
    assert clear.kind == "open_profile"
    assert not looks_ambiguous(clear, "開 Cursor")


def test_engine_query_without_key():
    with mock.patch("jarvis.engine.llm_configured", return_value=False):
        result = execute_utterance("幫我查點樣開 Chrome", repair_asr=False)
    assert result.ok
    assert any("caption" in line or "查詢" in line for line in result.lines)
    assert any("warn" in line.lower() or "API_KEY" in line for line in result.lines)


def test_engine_ambiguous_brain_then_dry_run():
    fake = json.dumps(
        {
            "intent": "open_profile",
            "target_raw": "browser",
            "profile_id": None,
            "force_new": True,
            "speak_caption": "新開",
        }
    )
    with mock.patch("jarvis.engine.llm_configured", return_value=True):
        with mock.patch("jarvis.brain._chat", return_value=fake):
            result = execute_utterance(
                "開 完全未知軟體xyzabc",
                dry_run=True,
                repair_asr=False,
            )
    assert any("[brain]" in line for line in result.lines), result.lines
    assert any("browser-main" in line or "force_new" in line for line in result.lines)
    assert result.ok


def test_engine_query_with_mocked_llm():
    with mock.patch("jarvis.engine.llm_configured", return_value=True):
        with mock.patch("jarvis.brain._chat", return_value="用「開 Chrome」即可。"):
            # answer_query calls _chat; also need llm_configured in dispatch
            result = execute_utterance("怎樣開 Chrome？", repair_asr=False)
    assert result.ok
    assert any("開 Chrome" in line for line in result.lines)


if __name__ == "__main__":
    for fn in (
        test_llm_configured_false_without_key,
        test_intent_from_json_force_new_browser,
        test_intent_rejects_path_and_illegal_id,
        test_resolve_ambiguous_mocked,
        test_resolve_ambiguous_no_verb_refuses,
        test_resolve_ambiguous_close_hint_flips,
        test_looks_ambiguous,
        test_engine_query_without_key,
        test_engine_ambiguous_brain_then_dry_run,
        test_engine_query_with_mocked_llm,
    ):
        fn()
        print("ok", fn.__name__)
    print("all passed")
