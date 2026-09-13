"""Deterministic TTS shaping for alert kinds (pure; no I/O).

Maps raw alert kinds / metric dumps into speakable English phrases.
Delegates known kinds to ``alerts.alert_phrase_for`` / ``gpu_health_phrase``.
INVARIANT: shape() never returns a string containing a run of 4+ digits.

``sidecar_down`` is reserved — no producer in-repo (add back only with a real
watchdog). ``speak_gate`` treats critical via ``priority_for``, not by
re-reading ``CRITICAL`` alone.
"""

from __future__ import annotations

import re
from typing import Any

from jarvis.alerts import alert_phrase_for
from jarvis.sensors.gpu_health import gpu_health_phrase

# Kinds that alert_phrase_for / gpu_health_phrase already cover (explicit arms).
_KNOWN_ALERT_KINDS = frozenset(
    {
        "discord",
        "cursor",
        "cursor_plan",
        "cursor_approve",
        "whatsapp",
        "gpu_health",
        "gpu_hard",
    }
)
_KNOWN_GPU_REASONS = frozenset({"clock_drop", "hot", "mem_hot"})

# Always speak_now; must never default to digest/drop (enforced by tests).
# speak_gate uses priority_for() as source of truth (not a second CRITICAL copy).
CRITICAL: frozenset[str] = frozenset({"gpu_hard", "cursor_approve"})

# Default delivery class per kind (settings booleans can force "drop").
POLICY: dict[str, str] = {
    "self-monitor": "speak_now",
    "test": "speak_now",
    "extra": "digest",
    "discord": "digest",
    "whatsapp": "digest",
    "cursor": "digest",
    "cursor_plan": "digest",
    "cursor_approve": "speak_now",
    "gpu_health": "digest",
    "gpu_hard": "speak_now",
}

# kind → settings attr that hard-overrides to "drop" when False.
_KIND_SETTING_OVERRIDE: dict[str, str] = {
    "discord": "alert_discord",
    "whatsapp": "alert_whatsapp",
    "cursor": "alert_cursor",
    "cursor_plan": "alert_cursor",
    "cursor_approve": "alert_cursor",
}


def policy_for(kind: str, settings: Any | None = None) -> str:
    """Return ``speak_now`` / ``digest`` / ``drop`` for *kind*.

    Settings booleans (``alert_voice`` / discord / whatsapp / cursor) are hard
    overrides: False → ``drop``. Unknown kinds in ``CRITICAL`` → ``speak_now``.

    CRITICAL kinds (``gpu_hard`` / ``cursor_approve``) are not affected by
    ``alert_voice`` / per-kind switches and always speak — same first
    short-circuit as ``speak_gate.should_speak``.
    """
    k = (kind or "").strip()
    if k in CRITICAL:
        return "speak_now"  # 唔受 alert_voice／per-kind 開關影響（plan 鐵則）
    if settings is None:
        from jarvis.settings import load_settings

        settings = load_settings()
    if not bool(getattr(settings, "alert_voice", True)):
        return "drop"
    attr = _KIND_SETTING_OVERRIDE.get(k)
    if attr is not None and not bool(getattr(settings, attr, True)):
        return "drop"
    cls = POLICY.get(k)
    if cls is not None:
        return cls
    return "digest"


def priority_for(kind: str) -> str:
    """AlertStore priority vocabulary: ``critical`` iff *kind* in CRITICAL."""
    return "critical" if (kind or "").strip() in CRITICAL else "normal"


_RE_FIRES = re.compile(r"\bfires=(\d+)")
_RE_FP = re.compile(r"\bfp=(\d+)")
_RE_ERR = re.compile(r"\berr=(\d+)")
_RE_THR = re.compile(r"\bthr=([^\s|]+)->([^\s|]+)")
_RE_URL = re.compile(r"https?://\S+")
_RE_DIGIT_RUN = re.compile(r"\d{4,}")


def sanitize(text: str) -> str:
    """ASCII-only label scrub: drop metrics noise, URLs → 'a link'."""
    s = text or ""
    # Order: `->` before bare `-` / other tokens so arrows stay one space.
    s = s.replace("->", " ")
    for ch in ("=", "|", "\\", "<", ">", '"'):
        s = s.replace(ch, " ")
    s = _RE_URL.sub("a link", s)
    s = "".join(c for c in s if c.isascii() and c.isprintable())
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_speakable(text: str) -> bool:
    """True iff text is safe for Piper TTS (ASCII, no metric dumps)."""
    if not (text or "").strip():
        return False
    if not text.isascii():
        return False
    if "=" in text or "|" in text or "->" in text:
        return False
    if "http" in text:
        return False
    if _RE_DIGIT_RUN.search(text):
        return False
    if not text.endswith("."):
        return False
    if len(text) > 200:
        return False
    return True


# Shared strict TTS gate (mouth + speaker choke) — alias, do not redefine.
strict_ok = is_speakable


def guard_for_speech(text: str) -> str | None:
    """None if *text* is OK for general speech; else short reason.

    Reasons: ``empty`` / ``cjk`` / ``url`` / ``metric``. Pure; no I/O.
    """
    if not (text or "").strip():
        return "empty"
    if not text.isascii():
        return "cjk"
    if "http" in text:
        return "url"
    if "=" in text or "->" in text or _RE_DIGIT_RUN.search(text):
        return "metric"
    return None


def speech_guard(text: str, *, mode: str = "strict") -> str | None:
    """Guard reason for TTS. 'strict' = fail-closed (alerts); 'lenient' = never block (chat/preview)."""
    if str(mode or "").strip().lower() == "lenient":
        return None
    return guard_for_speech(text)


def _fmt_count(n: int) -> str:
    """Speakable count: 0..999 as digits; else 'over 999' (negatives → '0')."""
    if n < 0:
        return "0"
    if n <= 999:
        return str(n)
    return "over 999"


def _plural(n: int, singular: str, plural: str) -> str:
    """Pick singular iff n == 1; else plural (incl. 0 / over-999)."""
    return singular if n == 1 else plural


def _thr_direction(detail: str) -> str:
    m = _RE_THR.search(detail)
    if not m:
        return "unchanged"
    try:
        a = float(m.group(1))
        b = float(m.group(2))
    except ValueError:
        return "unchanged"
    if a == b:
        return "unchanged"
    if b > a:
        return "raised"
    return "lowered"


def _shape_self_monitor(detail: str) -> str:
    raw = detail or ""
    m_fires = _RE_FIRES.search(raw)
    if not m_fires:
        return "Sir, self monitor finished."
    fires = int(m_fires.group(1))
    m_fp = _RE_FP.search(raw)
    fp = int(m_fp.group(1)) if m_fp else 0
    m_err = _RE_ERR.search(raw)
    err = int(m_err.group(1)) if m_err else 0
    thr = _thr_direction(raw)
    fp_part = (
        "no false positives"
        if fp == 0
        else f"{_fmt_count(fp)} {_plural(fp, 'false positive', 'false positives')}"
    )
    return (
        f"Sir, self monitor: {_fmt_count(fires)} "
        f"{_plural(fires, 'wake event', 'wake events')}, {fp_part}, "
        f"{_fmt_count(err)} {_plural(err, 'error', 'errors')}, "
        f"threshold {thr}."
    )


def shape(
    kind: str,
    phrase: str = "",
    app_label: str = "",
    detail: str = "",
) -> str:
    """Return a speakable English phrase for ``kind`` (deterministic)."""
    k = (kind or "").strip()

    if k == "self-monitor":
        return _shape_self_monitor(detail)

    if k == "test":
        return "Sir, this is a test alert."

    if k == "extra":
        return "Sir, you have a notification."

    if k.startswith("extra:"):
        label = sanitize(k[6:])
        if not label:
            return "Sir, you have a notification."
        return f"Sir, {label} has a notification."

    if k in _KNOWN_GPU_REASONS:
        out = gpu_health_phrase(k)
        if out:
            return out

    if k in _KNOWN_ALERT_KINDS:
        reason = (phrase or "").strip().lower()
        if k == "gpu_health" and reason in _KNOWN_GPU_REASONS:
            out = gpu_health_phrase(reason)
        else:
            out = alert_phrase_for(k, app_label=app_label)
        if out:
            return out

    app = sanitize(app_label)
    if app:
        return f"Sir, you have a new alert from {app}."
    return "Sir, you have a new alert."
