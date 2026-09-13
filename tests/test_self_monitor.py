"""Tests for jarvis.self_monitor parse helpers (Self-Evol E3 latency)."""

from __future__ import annotations

from jarvis import self_monitor as sm


class TestHmsToSec:
    def test_basic(self) -> None:
        assert sm._hms_to_sec("14:05:03 oww_fire") == 14 * 3600 + 5 * 60 + 3

    def test_no_prefix(self) -> None:
        assert sm._hms_to_sec("oww_fire best=0.5") is None

    def test_empty(self) -> None:
        assert sm._hms_to_sec("") is None


class TestParseWakeDebug:
    def test_last_fire_ts(self) -> None:
        lines = [
            "14:00:01 oww_fire best=0.5 thr=0.5",
            "14:05:01 wake_heartbeat best=0.2",
            "14:06:02 oww_fire best=0.6 thr=0.5",
        ]
        w = sm._parse_wake_debug(lines)
        assert w["fires"] == 2
        assert w["last_fire_ts"] == 14 * 3600 + 6 * 60 + 2

    def test_no_fire(self) -> None:
        w = sm._parse_wake_debug(["14:00:01 wake_heartbeat best=0.2"])
        assert w["fires"] == 0
        assert w["last_fire_ts"] is None


class TestParseServeLog:
    def test_tts_ok_ts(self) -> None:
        lines = [
            "[engine] route open_profile | Cursor",
            "[mouth] tts_ok 14:06:05",
            "[mouth] tts_ok 14:07:10",
        ]
        s = sm._parse_serve_log(lines)
        assert s["tts_ok"] == 2
        assert s["tts_ok_ts"] == 14 * 3600 + 7 * 60 + 10

    def test_legacy_no_ts(self) -> None:
        # 舊版 mouth print 冇 timestamp → ts 唔好計（latency skip）
        s = sm._parse_serve_log(["[mouth] tts_ok"])
        assert s["tts_ok"] == 1
        assert s["tts_ok_ts"] is None

    def test_tts_ok_no_ts_counter(self) -> None:
        # ⑭: tts_ok 但冇 timestamp → no_ts 計數（格式改咗 → fail-visible）
        s = sm._parse_serve_log(["[mouth] tts_ok", "[mouth] tts_ok 14:00:01"])
        assert s["tts_ok"] == 2
        assert s["tts_ok_no_ts"] == 1
        assert s["tts_ok_ts"] == 14 * 3600 + 1


class TestComputeLatency:
    def test_normal(self) -> None:
        wake = sm._parse_wake_debug(["14:00:01 oww_fire best=0.5"])
        serve = sm._parse_serve_log(["[mouth] tts_ok 14:00:04"])
        assert sm._compute_latency(wake, serve) == 3.0

    def test_midnight_crossing(self) -> None:
        # ⑮: 23:59:58 fire → 00:00:01 tts_ok（跨午夜都要計）
        wake = sm._parse_wake_debug(["23:59:58 oww_fire best=0.5"])
        serve = sm._parse_serve_log(["[mouth] tts_ok 00:00:01"])
        assert sm._compute_latency(wake, serve) == 3.0

    def test_midnight_zero_truthiness(self) -> None:
        # fire at 00:00:00 → tts at 00:00:03; 0.0 must not be treated as falsy
        wake = sm._parse_wake_debug(["00:00:00 oww_fire best=0.5"])
        serve = sm._parse_serve_log(["[mouth] tts_ok 00:00:03"])
        assert sm._compute_latency(wake, serve) == 3.0

    def test_missing_side(self) -> None:
        wake = sm._parse_wake_debug(["14:00:01 oww_fire best=0.5"])
        serve = sm._parse_serve_log(["[mouth] tts_ok"])  # 舊版無 ts
        assert sm._compute_latency(wake, serve) is None

    def test_other_tts_filtered(self) -> None:
        # tts_ok 喺 fire 之前（alert/ack 唔係回應指令）→ 唔計
        wake = sm._parse_wake_debug(["14:00:01 oww_fire best=0.5"])
        serve = sm._parse_serve_log(["[mouth] tts_ok 13:59:59"])
        assert sm._compute_latency(wake, serve) is None

    def test_too_late_filtered(self) -> None:
        wake = sm._parse_wake_debug(["14:00:01 oww_fire best=0.5"])
        serve = sm._parse_serve_log(["[mouth] tts_ok 14:10:01"])
        assert sm._compute_latency(wake, serve) is None
