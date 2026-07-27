"""App index: spelling fuzzy + Jyutping + slots/aliases."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.config import load_registry
from jarvis import memory as mem
from jarvis.app_index import (
    AppEntry,
    _label_plausible_for_query,
    apply_learned_alias,
    best_label_match,
    jyutping_pair_score,
    pair_score,
    parse_command_slots,
    rewrite_command_target,
    spelling_score,
)
from jarvis.asr_repair import repair_asr_text


def test_spelling_whatapp():
    assert spelling_score("whatapp", "WhatsApp") >= 70
    assert spelling_score("what石", "WhatsApp") >= 70


def test_jyutping_han_substring():
    sc = jyutping_pair_score("檔案", "檔案總管")
    assert sc >= 80, sc


def test_jyutping_romanization():
    sc = jyutping_pair_score("dong on", "檔案總管")
    assert sc >= 70, sc


def test_best_label_from_entries():
    from jarvis.app_index import _jyutping_compact

    entries = [
        AppEntry(label="WhatsApp", norm="whatsapp", jyut=""),
        AppEntry(label="Discord", norm="discord", jyut=""),
        AppEntry(
            label="檔案總管",
            norm="檔案總管",
            jyut=_jyutping_compact("檔案總管"),
        ),
    ]
    hit = best_label_match("whatapp", entries=entries)
    assert hit and hit[0] == "WhatsApp"
    hit2 = best_label_match("檔案", entries=entries)
    assert hit2 and hit2[0] == "檔案總管"


def test_parse_command_slots():
    s = parse_command_slots("開 whatapp")
    assert s and s.verb_kind == "open" and s.app_query == "whatapp"
    s2 = parse_command_slots("閂 Discord")
    assert s2 and s2.verb_kind == "close"
    s3 = parse_command_slots("重開 CS")
    assert s3 and s3.verb_kind == "restart"
    assert parse_command_slots("hello") is None


def test_rewrite_open_target():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        with mock.patch("jarvis.app_index.best_label_match", return_value=("WhatsApp", 90.0)):
            text, note = rewrite_command_target(
                "開 whatapp", memory_path=path, learn=True
            )
        assert text == "開 WhatsApp"
        assert note and "WhatsApp" in note
        assert mem.get_stt_alias("whatapp", path) == "WhatsApp"


def test_alias_roundtrip_skips_fuzzy():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        mem.learn_stt_alias("爱锅石", "WhatsApp", path)
        text, note = apply_learned_alias("開 爱锅石", memory_path=path)
        assert text == "開 WhatsApp"
        assert note and "alias" in note
        with mock.patch("jarvis.app_index.best_label_match") as fuzzy:
            text2, note2 = rewrite_command_target(
                "開 爱锅石", memory_path=path, learn=False
            )
        fuzzy.assert_not_called()
        assert text2 == "開 WhatsApp"
        assert note2 and "alias" in note2


def test_pair_score_max():
    assert pair_score("whatsapp", "WhatsApp") == 100.0


def test_short_query_blocks_sentence_label():
    assert not _label_plausible_for_query(
        "what石",
        "What is new in the latest version",
    )
    assert _label_plausible_for_query("what石", "WhatsApp")


def test_asr_bare_app_autoprefix_open():
    cfg = ROOT / "config" / "profiles.yaml"
    reg = load_registry(cfg if cfg.is_file() else (ROOT / "config" / "profiles.example.yaml"))
    fixed, note = repair_asr_text("whatsapp", reg)
    assert fixed.lower().startswith("開 whatsapp")
    assert note and "補開" in note


def test_force_whatsapp_learns_alias():
    with mock.patch("jarvis.memory.learn_stt_alias") as learn:
        from jarvis.asr_repair import _force_whatsapp_open_close

        out = _force_whatsapp_open_close("爱锅石")
        assert out == "開 whatsapp"
        learn.assert_called()
        assert learn.call_args[0][0] == "爱锅石"
        assert learn.call_args[0][1] == "WhatsApp"


if __name__ == "__main__":
    test_spelling_whatapp()
    test_jyutping_han_substring()
    test_jyutping_romanization()
    test_best_label_from_entries()
    test_parse_command_slots()
    test_rewrite_open_target()
    test_alias_roundtrip_skips_fuzzy()
    test_pair_score_max()
    test_short_query_blocks_sentence_label()
    test_asr_bare_app_autoprefix_open()
    test_force_whatsapp_learns_alias()
    print("all passed")
