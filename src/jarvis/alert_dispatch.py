"""Shared alert-speaker dispatch (poll_loop + speak_once use the same rules)."""

from __future__ import annotations

from typing import Any, Callable


def prepare_phrase(row: Any) -> tuple[str | None, str | None]:
    """Shape + choke. Return ``(text, None)`` or ``(None, reason)``.

    Already-speakable English is a no-op (mode=off byte-identical when phrase
    is already speakable — ``shape()`` of an already-English phrase is treated
    as a no-op here).
    """
    from jarvis.alert_policy import guard_for_speech, is_speakable, shape

    kind = str(getattr(row, "kind", "") or "")
    phrase = str(getattr(row, "phrase", "") or "")
    app = str(getattr(row, "app", "") or "")
    detail = str(getattr(row, "detail", "") or "")
    if is_speakable(phrase):
        return phrase, None
    text = shape(kind, phrase, app_label=app, detail=detail)
    if is_speakable(text):
        return text, None
    reason = guard_for_speech(text) or "not_speakable"
    return None, reason


def effective_action(plan: Any, *, cfg: Any) -> str:
    """Apply gaming_drop override when ``alert_gaming == "drop"``."""
    action = str(getattr(plan, "action", "") or "")
    gaming_drop = (
        str(getattr(plan, "reason", "") or "") == "gaming"
        and str(getattr(cfg, "alert_gaming", "hold") or "hold").strip().lower()
        == "drop"
    )
    if gaming_drop:
        return "drop"
    return action


def enforce(
    store: Any,
    row: Any,
    plan: Any,
    *,
    cfg: Any,
    now: float | None = None,
    speak: Callable[[str], bool] | None = None,
    claim: bool = True,
) -> str:
    """Apply plan to *store*; return one of speak/hold/digest/drop/none."""
    import time

    t = time.time() if now is None else float(now)
    eff = effective_action(plan, cfg=cfg)

    if eff == "hold":
        ttl = float(getattr(cfg, "alert_hold_ttl_s", 900) or 900)
        n = store.hold([row.id], ttl_s=ttl, now=t)
        if not n:
            print(f"[warn] hold noop id={row.id} kind={row.kind}", flush=True)
        print(f"[alert] hold {row.kind} reason={plan.reason}", flush=True)
        return "hold"

    if eff == "digest":
        n = store.mark_digest([row.id], now=t)
        if not n:
            print(f"[warn] mark_digest noop id={row.id} kind={row.kind}", flush=True)
        print(f"[alert] digest {row.kind}", flush=True)
        return "digest"

    if eff == "drop":
        drop_reason = "gaming" if eff != plan.action else plan.reason
        store.drop([row.id], drop_reason, now=t)
        print(f"[alert] drop {row.kind} reason={plan.reason}", flush=True)
        return "drop"

    if eff != "speak":
        return "none"

    # speak
    text, reason = prepare_phrase(row)
    if text is None:
        drop_reason = reason or "not_speakable"
        print(
            f"[choke] refused kind={getattr(row, 'kind', '')} reason={reason}",
            flush=True,
        )
        try:
            store.drop([str(row.id)], drop_reason, now=t)
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] choke drop: {exc}", flush=True)
        return "drop"

    if claim:
        store.mark_spoken([str(row.id)], now=t)
    try:
        ok = bool(speak(text)) if speak is not None else False
    except Exception as exc:  # noqa: BLE001
        print(f"[fail] speak raised: {exc}", flush=True)
        ok = False
        fail_reason = str(exc)[:80] or "tts"
    else:
        fail_reason = "tts"
    if ok:
        # Unconditional spoken ledger (mode=off/shadow claim=False included).
        try:
            store._ledger(str(row.id), str(row.kind), "spoken", "speak", now=t)
        except Exception:  # noqa: BLE001
            pass
        store.ack(row.id)
        print(f"[ok] spoke {row.kind}: {text}", flush=True)
        return "speak"
    if claim:
        # Restore pending so lease expiry / next peek can retry.
        try:
            store._set_state(
                [str(row.id)], "pending", "speak_fail", reason=fail_reason, now=t
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] restore pending: {exc}", flush=True)
    print(f"[fail] speak {row.id[:8]}", flush=True)
    return "none"
