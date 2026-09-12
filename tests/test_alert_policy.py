"""Unit tests for alert_policy.shape / sanitize / is_speakable."""

from __future__ import annotations

from types import SimpleNamespace

from jarvis.alert_policy import (
    CRITICAL,
    POLICY,
    is_speakable,
    policy_for,
    sanitize,
    shape,
)

_DOCUMENTED = (
    "self-monitor",
    "gpu_hard",
    "test",
    "extra",
    "extra:Slack",
    "discord",
    "cursor",
    "cursor_plan",
    "cursor_approve",
    "whatsapp",
    "gpu_health",
    "clock_drop",
    "hot",
    "mem_hot",
)

_SAMPLE_DETAIL = (
    "2026-09-12 09:00:00 | fires=5 fp=0 stt_miss=0 "
    "avg_best=0.00 thr=0.50->0.55"
)


def test_documented_kinds_speakable_with_and_without_detail() -> None:
    for kind in _DOCUMENTED:
        for detail in ("", _SAMPLE_DETAIL):
            out = shape(kind, detail=detail)
            assert is_speakable(out) is True, (kind, detail, out)


def test_self_monitor_raised_no_fp() -> None:
    detail = (
        "2026-09-12 09:00:00 | fires=5 fp=0 stt_miss=0 thr=0.50->0.55"
    )
    out = shape("self-monitor", detail=detail)
    assert out == (
        "Sir, self monitor: 5 wake events, no false positives, "
        "0 errors, threshold raised."
    )
    assert "=" not in out
    assert "fires" not in out
    assert is_speakable(out) is True


def test_self_monitor_fp_and_unchanged() -> None:
    detail = (
        "2026-09-12 09:00:00 | fires=5 fp=3 stt_miss=0 err=2 thr=0.50->0.50"
    )
    out = shape("self-monitor", detail=detail)
    assert out == (
        "Sir, self monitor: 5 wake events, 3 false positives, "
        "2 errors, threshold unchanged."
    )
    assert "=" not in out
    assert "fires" not in out


def test_self_monitor_unparsable() -> None:
    out = shape("self-monitor", detail="")
    assert out == "Sir, self monitor finished."
    assert is_speakable(out) is True


def test_gpu_hard_test_extra() -> None:
    assert shape("gpu_hard") == "Sir, GPU critical limit reached."
    assert shape("test") == "Sir, this is a test alert."
    assert shape("extra") == "Sir, you have a notification."
    assert shape("extra:Slack") == "Sir, Slack has a notification."


def test_extra_cjk_label_falls_back() -> None:
    out = shape("extra:測試")
    assert out.isascii()
    assert out == "Sir, you have a notification."
    assert is_speakable(out) is True


def test_unknown_kind_cjk_app_ascii() -> None:
    out = shape("weird_kind", app_label="測試App")
    assert out.isascii()
    assert "a new alert" in out
    assert is_speakable(out) is True


def test_is_speakable_rejects_metrics_and_accepts_shaped() -> None:
    assert is_speakable("GPU=95C mem=88 http://x") is False
    assert is_speakable("Sir, GPU critical limit reached.") is True


def test_is_speakable_digits_rule() -> None:
    assert is_speakable("Sir, 3 messages.") is True
    assert is_speakable("Sir, 12345 events.") is False


def test_sanitize_url_and_noise() -> None:
    s = sanitize("Foo=bar | https://evil.example/x -> baz")
    assert "=" not in s
    assert "|" not in s
    assert "->" not in s
    assert "http" not in s
    assert "a link" in s
    assert s.isascii()


def test_known_kinds_delegate_wording() -> None:
    assert shape("discord") == "Discord has a new message."
    assert shape("gpu_health") == "GPU health warning."
    assert shape("hot") == "GPU thermal stress."


def test_self_monitor_caps_large_counts() -> None:
    detail = (
        "2026-09-12 09:00:00 | fires=12345 fp=0 err=1200 thr=0.65->0.65"
    )
    out = shape("self-monitor", detail=detail)
    assert "over 999" in out
    assert "12345" not in out
    assert is_speakable(out) is True


def test_self_monitor_count_boundaries() -> None:
    out_999 = shape(
        "self-monitor",
        detail="fires=999 fp=0 err=0 thr=0.50->0.50",
    )
    assert "999 wake events" in out_999
    out_1000 = shape(
        "self-monitor",
        detail="fires=1000 fp=0 err=0 thr=0.50->0.50",
    )
    assert "over 999 wake events" in out_1000


def test_self_monitor_singular_plural() -> None:
    out1 = shape(
        "self-monitor",
        detail="fires=1 fp=0 err=0 thr=0.65->0.65",
    )
    assert "1 wake event," in out1
    out2 = shape(
        "self-monitor",
        detail="fires=2 fp=0 err=0 thr=0.65->0.65",
    )
    assert "2 wake events," in out2
    out_err1 = shape(
        "self-monitor",
        detail="fires=5 fp=0 err=1 thr=0.65->0.65",
    )
    assert "1 error," in out_err1
    out_fp1 = shape(
        "self-monitor",
        detail="fires=5 fp=1 err=0 thr=0.65->0.65",
    )
    assert "1 false positive," in out_fp1
    out_fp0 = shape(
        "self-monitor",
        detail="fires=5 fp=0 err=0 thr=0.65->0.65",
    )
    assert "no false positives" in out_fp0


def test_self_monitor_full_real_line() -> None:
    detail = (
        "2026-09-12 09:00:00 | fires=5 fp=0 stt_miss=0 "
        "avg_best=0.00 avg_peak=0.04 agc=6.0x agc_boost_pct=99% aec=on "
        "stt_rtf=1.2 repair=0 tts_ok=3 resp_lat=2.1s "
        "err=3 vram=8.2 thr=0.65->0.65"
    )
    out = shape("self-monitor", detail=detail)
    assert out == (
        "Sir, self monitor: 5 wake events, no false positives, "
        "3 errors, threshold unchanged."
    )
    assert is_speakable(out) is True


def test_sanitize_space_separators() -> None:
    assert sanitize("a=b|c->d") == "a b c d"
    assert sanitize("label http://x.com") == "label a link"


def test_policy_critical_invariant() -> None:
    """No CRITICAL kind may default to digest/drop."""
    bad = CRITICAL & {k for k, v in POLICY.items() if v != "speak_now"}
    assert bad == set()


def test_policy_for_defaults_and_overrides() -> None:
    base = SimpleNamespace(
        alert_voice=True,
        alert_discord=True,
        alert_whatsapp=True,
        alert_cursor=True,
    )
    assert policy_for("gpu_hard", settings=base) == "speak_now"
    assert policy_for("whatsapp", settings=base) == "digest"
    off = SimpleNamespace(
        alert_voice=True,
        alert_discord=True,
        alert_whatsapp=False,
        alert_cursor=True,
    )
    assert policy_for("whatsapp", settings=off) == "drop"


def test_policy_for_critical_ignores_all_off() -> None:
    """CRITICAL kinds speak even when alert_voice + per-kind switches are False."""
    all_off = SimpleNamespace(
        alert_voice=False,
        alert_discord=False,
        alert_whatsapp=False,
        alert_cursor=False,
    )
    assert policy_for("gpu_hard", settings=all_off) == "speak_now"
    # FIX7 AA: sidecar_down reserved / no producer — no longer CRITICAL
    assert policy_for("sidecar_down", settings=all_off) != "speak_now"
    assert "sidecar_down" not in CRITICAL
    assert policy_for("whatsapp", settings=all_off) == "drop"
