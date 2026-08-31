"""Tests for jarvis.stt_stats (Self-Evol E2 STT accuracy consumer)."""

from __future__ import annotations

import json

from jarvis import stt_stats as ss


class TestCountFires:
    def test_counts_oww_fire_lines(self) -> None:
        lines = [
            "14:00:01 oww_fire best=0.5 thr=0.5",
            "14:05:01 oww_fire best=0.6 thr=0.5",
            "14:10:01 wake_heartbeat best=0.2",
        ]
        assert ss.count_fires(lines) == 2

    def test_empty(self) -> None:
        assert ss.count_fires([]) == 0


class TestParseRepairPairs:
    def test_single_pair(self) -> None:
        lines = ["[engine] asr_repair=ASR 修正：'cura' → 'Cursor'"]
        assert ss.parse_repair_pairs(lines) == [("cura", "Cursor")]

    def test_compound_note_takes_first_pair(self) -> None:
        # 第二個箭頭係 app 補開（同一 note 嘅後續 rewrite），唔可以 double-count
        lines = ["[engine] asr_repair=ASR 修正：'cura' → '開 Cursor'；app 補開（80%）：'x' → 'Cursor'"]
        assert ss.parse_repair_pairs(lines) == [("cura", "開 Cursor")]

    def test_ignores_non_repair_lines(self) -> None:
        lines = ["[engine] route open_profile | Cursor", "[mouth] tts_ok"]
        assert ss.parse_repair_pairs(lines) == []

    def test_malformed_note_skipped(self) -> None:
        lines = ["[engine] asr_repair=ASR 修正（冇箭頭）"]
        assert ss.parse_repair_pairs(lines) == []

    def test_raw_equals_fixed_dropped(self) -> None:
        lines = ["[engine] asr_repair=ASR 修正：'same' → 'same'"]
        assert ss.parse_repair_pairs(lines) == []


class TestExtractAliasTarget:
    def test_open_verb(self) -> None:
        assert ss.extract_alias_target("開 Cursor") == "Cursor"

    def test_close_verb(self) -> None:
        assert ss.extract_alias_target("閂 whatsapp") == "whatsapp"

    def test_force_new(self) -> None:
        assert ss.extract_alias_target("再開 Chrome") == "Chrome"

    def test_no_verb_returns_none(self) -> None:
        assert ss.extract_alias_target("今日天氣點樣") is None

    def test_empty(self) -> None:
        assert ss.extract_alias_target("") is None


class TestComputeStats:
    def test_ratio_and_top(self) -> None:
        pairs = [
            ("cura", "Cursor"),
            ("cura", "Cursor"),
            ("dico", "Discord"),
        ]
        stats = ss.compute_stats(pairs, fires=10)
        assert stats["fires"] == 10
        assert stats["repair_hits"] == 3
        assert stats["repair_ratio"] == 0.3
        assert stats["top_confusions"][0] == {
            "raw": "cura",
            "fixed": "Cursor",
            "count": 2,
        }

    def test_suggestion_only_after_min(self) -> None:
        pairs = [("cura", "開 Cursor")] * 3 + [("dico", "Discord")] * 2
        stats = ss.compute_stats(pairs, fires=10)
        assert len(stats["suggestions"]) == 1
        sug = stats["suggestions"][0]
        assert sug["raw"] == "cura"
        assert sug["fixed"] == "開 Cursor"
        assert sug["count"] == 3
        assert sug["alias_target"] == "Cursor"

    def test_no_fires_ratio_none(self) -> None:
        stats = ss.compute_stats([], fires=0)
        assert stats["repair_ratio"] is None
        assert stats["suggestions"] == []


class TestFingerprint:
    def test_no_data(self) -> None:
        stats = ss.compute_stats([], fires=0)
        assert ss.fingerprint(stats) == "NO_DATA"

    def test_ratio(self) -> None:
        stats = ss.compute_stats([("a", "b")] * 1, fires=4)
        fp = ss.fingerprint(stats)
        assert fp.startswith("REPAIR_RATIO 0.2500|1|4")


class TestLoadRepairEvents:
    def test_reads_jsonl(self, tmp_path) -> None:
        p = tmp_path / "repair_log.jsonl"
        p.write_text(
            '{"ts": 1.0, "raw": "cura", "fixed": "Cursor"}\n'
            '{"ts": 2.0, "raw": "dico", "fixed": "Discord"}\n',
            encoding="utf-8",
        )
        assert ss.load_repair_events(p) == [("cura", "Cursor"), ("dico", "Discord")]

    def test_malformed_lines_skipped(self, tmp_path) -> None:
        p = tmp_path / "repair_log.jsonl"
        p.write_text("not json\n{\"raw\": \"a\"}\n{\"raw\": \"x\", \"fixed\": \"y\"}\n", encoding="utf-8")
        assert ss.load_repair_events(p) == [("x", "y")]

    def test_missing_file(self, tmp_path) -> None:
        assert ss.load_repair_events(tmp_path / "nope.jsonl") == []


class TestRunOnce:
    def test_with_tmp_logs(self, tmp_path) -> None:
        serve = tmp_path / "serve.log"
        wake = tmp_path / "wake_debug.log"
        serve.write_text(
            "[engine] asr_repair=ASR 修正：'cura' → 'Cursor'\n", encoding="utf-8"
        )
        wake.write_text("14:00:01 oww_fire best=0.5 thr=0.5\n", encoding="utf-8")
        stats, summary = ss.run_once(serve, wake, write_log=False)
        assert stats["fires"] == 1
        assert stats["repair_hits"] == 1
        assert stats["repair_ratio"] == 1.0
        assert "fires=1" in summary
        assert "repair=1" in summary

    def test_repair_log_preferred_over_serve(self, tmp_path) -> None:
        serve = tmp_path / "serve.log"
        wake = tmp_path / "wake_debug.log"
        rlog = tmp_path / "repair_log.jsonl"
        serve.write_text(
            "[engine] asr_repair=ASR 修正：'old' → 'Old'\n", encoding="utf-8"
        )
        rlog.write_text(
            '{"ts": 1.0, "raw": "new", "fixed": "New"}\n', encoding="utf-8"
        )
        wake.write_text("14:00:01 oww_fire best=0.5\n", encoding="utf-8")
        stats, _ = ss.run_once(serve, wake, repair_log=rlog, write_log=False)
        assert stats["repair_hits"] == 1
        assert stats["top_confusions"][0]["raw"] == "new"  # 用 repair_log，唔係 serve.log

    def test_empty_repair_log_falls_back(self, tmp_path) -> None:
        serve = tmp_path / "serve.log"
        wake = tmp_path / "wake_debug.log"
        rlog = tmp_path / "repair_log.jsonl"
        rlog.write_text("", encoding="utf-8")
        serve.write_text(
            "[engine] asr_repair=ASR 修正：'cura' → 'Cursor'\n", encoding="utf-8"
        )
        wake.write_text("14:00:01 oww_fire best=0.5\n", encoding="utf-8")
        stats, _ = ss.run_once(serve, wake, repair_log=rlog, write_log=False)
        assert stats["repair_hits"] == 1  # fallback serve.log parse

    def test_missing_logs(self, tmp_path) -> None:
        stats, _ = ss.run_once(
            tmp_path / "nope.log", tmp_path / "nope2.log", write_log=False
        )
        assert stats["fires"] == 0
        assert stats["repair_hits"] == 0
        assert ss.fingerprint(stats) == "NO_DATA"
