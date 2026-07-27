"""App index: spelling fuzzy + Jyutping."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.config import load_registry
from jarvis.app_index import (
    AppEntry,
    _label_plausible_for_query,
    best_label_match,
    jyutping_pair_score,
    pair_score,
    rewrite_command_target,
    spelling_score,
)
from jarvis.asr_repair import repair_asr_text


def test_spelling_whatapp():
    assert spelling_score("whatapp", "WhatsApp") >= 70
    assert spelling_score("what石", "WhatsApp") >= 70


def test_jyutping_han_substring():
    # 檔案 ⊂ 檔案總管 via jyutping
    sc = jyutping_pair_score("檔案", "檔案總管")
    assert sc >= 80, sc


def test_jyutping_romanization():
    # dong on ≈ 檔案 (dong2 on3)
    sc = jyutping_pair_score("dong on", "檔案總管")
    assert sc >= 70, sc


def test_best_label_from_entries():
    entries = [
        AppEntry(label="WhatsApp", norm="whatsapp", jyut=""),
        AppEntry(label="Discord", norm="discord", jyut=""),
        AppEntry(
            label="檔案總管",
            norm="檔案總管",
            jyut="dongonzunggun",
        ),
    ]
    # force jyut on entry via real compute
    from jarvis.app_index import _jyutping_compact

    entries[2] = AppEntry(
        label="檔案總管",
        norm="檔案總管",
        jyut=_jyutping_compact("檔案總管"),
    )
    hit = best_label_match("whatapp", entries=entries)
    assert hit and hit[0] == "WhatsApp"
    hit2 = best_label_match("檔案", entries=entries)
    assert hit2 and hit2[0] == "檔案總管"


def test_rewrite_open_target():
    entries = [
        AppEntry(label="WhatsApp", norm="whatsapp", jyut=""),
    ]
    with mock.patch("jarvis.app_index.best_label_match", return_value=("WhatsApp", 90.0)):
        text, note = rewrite_command_target("開 whatapp")
    assert text == "開 WhatsApp"
    assert note and "WhatsApp" in note
    with mock.patch("jarvis.app_index.best_label_match", return_value=("WhatsApp", 82.0)):
        text3, note3 = rewrite_command_target("開 what石")
    assert text3 == "開 WhatsApp"
    assert note3 and "WhatsApp" in note3


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


if __name__ == "__main__":
    test_spelling_whatapp()
    test_jyutping_han_substring()
    test_jyutping_romanization()
    test_best_label_from_entries()
    test_rewrite_open_target()
    test_pair_score_max()
    test_short_query_blocks_sentence_label()
    test_asr_bare_app_autoprefix_open()
    print("all passed")
