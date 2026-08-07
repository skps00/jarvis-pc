"""Shared command execution for CLI and Shell UI."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.asr_fix import repair_asr_text
from jarvis.brain import (
    answer_query,
    has_clear_open_verb,
    llm_configured,
    looks_ambiguous,
    resolve_ambiguous,
)
from jarvis.config import Registry, load_registry
from jarvis.discover import discover_candidates
from jarvis.hands import (
    close_profile,
    launch_discovered,
    launch_profile,
    resolve_default_mc,
    restart_profile,
    restore_battlefield,
    system_power,
)
from jarvis.hermes_bridge import chat as hermes_chat
from jarvis.persist import commit_candidate
from jarvis.router import Intent, apply_verb_kind_limits, route
from jarvis.settings import load_settings


@dataclass
class RunResult:
    """Lines of status text plus overall ok flag."""

    ok: bool
    lines: list[str] = field(default_factory=list)


def execute_utterance(
    text: str,
    *,
    dry_run: bool = False,
    ask_confirm=None,
    repair_asr: bool = True,
    image_path: str | None = None,
) -> RunResult:
    """Route and optionally launch; never raises for normal refuse paths."""
    lines: list[str] = []
    try:
        registry = load_registry()
    except FileNotFoundError as exc:
        return RunResult(False, [str(exc)])

    utterance = text
    if repair_asr:
        utterance, note = repair_asr_text(text, registry)
        if note:
            lines.append(f"[fix] {note}")

    intent = apply_verb_kind_limits(route(utterance, registry), registry)
    lines.append(f"[route] {intent.kind} | {intent.caption}")

    hermes_on = bool(load_settings().hermes_enabled)

    # Phase1: query/unknown → Hermes; skip dual-brain when enabled
    if hermes_on and intent.kind in ("query", "unknown"):
        return _dispatch_hermes(
            intent,
            registry,
            utterance=utterance,
            dry_run=dry_run,
            lines=lines,
            image_path=image_path,
            ask_confirm=ask_confirm,
        )

    if image_path and hermes_on:
        lines.append("[warn] 附圖只經 Hermes（query／閒聊）；呢句 Hands 指令已忽略圖")
    elif image_path and not hermes_on:
        lines.append("[warn] 有附圖但 Hermes 未啟用 — 開設定勾 Hermes")

    if (
        not hermes_on
        and intent.kind in ("refuse", "unknown")
        and looks_ambiguous(intent, utterance)
    ):
        if llm_configured():
            try:
                brain_intent = resolve_ambiguous(utterance, registry)
            except RuntimeError as exc:
                lines.append(f"[brain] 失敗：{exc}")
                brain_intent = None
            if brain_intent and brain_intent.kind not in ("refuse", "unknown"):
                # belt: block open when original raw had no open verb
                if brain_intent.kind == "open_profile" and not has_clear_open_verb(
                    utterance
                ) and not has_clear_open_verb(text):
                    lines.append("[brain] 擋開：原文無開動詞（可能係關）")
                    brain_intent = None
                else:
                    lines.append(f"[brain] {brain_intent.kind} | {brain_intent.caption}")
                    intent = apply_verb_kind_limits(brain_intent, registry)
            elif brain_intent:
                lines.append(f"[brain] {brain_intent.kind} | {brain_intent.caption}")

    return _dispatch_intent(
        intent,
        registry,
        utterance=utterance,
        dry_run=dry_run,
        ask_confirm=ask_confirm,
        lines=lines,
    )


def _dispatch_hermes(
    intent: Intent,
    registry: Registry,
    *,
    utterance: str,
    dry_run: bool,
    lines: list[str],
    image_path: str | None = None,
    ask_confirm=None,
) -> RunResult:
    """query/unknown → Hermes bridge (Hands never called here)."""
    lines.append(f"[hermes] kind={intent.kind}")
    if image_path:
        lines.append(f"[hermes] image={image_path}")
    try:
        reply = hermes_chat(
            utterance,
            image_path=image_path,
            ask_approve=ask_confirm,
            dry_run=dry_run,
        )
    except Exception as exc:  # noqa: BLE001 — bridge must not crash shell
        lines.append(f"[hermes] 失敗：{exc}")
        if intent.kind == "query" and llm_configured():
            try:
                caption = answer_query(utterance, registry)
                lines.append(f"[caption] {caption}")
                lines.append("[hermes] 已回落本機 brain")
                return RunResult(True, lines)
            except Exception as exc2:  # noqa: BLE001
                lines.append(f"[brain] 回落失敗：{exc2}")
        lines.append(f"[fail] Hermes 不可用：{exc}")
        return RunResult(False, lines)

    if not reply.ok:
        lines.append(f"[hermes] 失敗：{reply.error or 'unknown'}")
        err_l = (reply.error or "").lower()
        if "approv" in err_l or "denied" in err_l or "timeout" in err_l:
            lines.append(
                "[hermes] Approve：拒／逾時；危險指令需彈窗 Yes。"
                "見 docs/approve_bridge.md"
            )
        if intent.kind == "query" and llm_configured() and not dry_run:
            try:
                caption = answer_query(utterance, registry)
                lines.append(f"[caption] {caption}")
                lines.append("[hermes] 已回落本機 brain")
                return RunResult(True, lines)
            except Exception as exc2:  # noqa: BLE001
                lines.append(f"[brain] 回落失敗：{exc2}")
        lines.append(f"[fail] {reply.error or intent.caption}")
        return RunResult(False, lines)

    if reply.raw and reply.raw.startswith("[hermes] API 失敗"):
        lines.append("[hermes] 已回落 chat -q（無 Approve 彈窗）")
    if reply.session_id:
        lines.append(f"[hermes] session={reply.session_id}")
    lines.append(f"[caption] {reply.caption}")
    if reply.spoken:
        lines.append(f"[speak] {reply.spoken}")
    return RunResult(True, lines)


def _dispatch_intent(
    intent: Intent,
    registry: Registry,
    *,
    utterance: str,
    dry_run: bool,
    ask_confirm,
    lines: list[str],
) -> RunResult:
    """Execute a gated Intent (Hands never sees free paths)."""
    if intent.kind == "query":
        if llm_configured():
            try:
                caption = answer_query(utterance, registry)
                lines.append(f"[caption] {caption}")
                return RunResult(True, lines)
            except RuntimeError as exc:
                lines.append(f"[brain] 查詢失敗：{exc}")
                lines.append(f"[caption] {intent.caption}")
                return RunResult(False, lines)
        lines.append(f"[caption] {intent.caption}")
        lines.append("[warn] 未設定 JARVIS_LLM_API_KEY — 查詢無內容答覆")
        return RunResult(True, lines)

    if intent.kind == "system_power":
        action = intent.power_action or ""
        if dry_run:
            lines.append(f"[dry-run] system_power {action}")
            return RunResult(True, lines)
        result = system_power(action, ask_confirm=ask_confirm)
        lines.append(("[ok] " if result.ok else "[fail] ") + result.message)
        return RunResult(result.ok, lines)

    if intent.kind == "close_profile":
        pid = intent.profile_id
        if not pid:
            lines.append("[fail] 無 profile_id")
            return RunResult(False, lines)
        if dry_run:
            lines.append(f"[dry-run] close {pid}")
            return RunResult(True, lines)
        result = close_profile(registry, pid, ask_confirm=ask_confirm)
        lines.append(("[ok] " if result.ok else "[fail] ") + result.message)
        return RunResult(result.ok, lines)

    if intent.kind == "restart_profile":
        pid = intent.profile_id
        if not pid:
            lines.append("[fail] 無 profile_id")
            return RunResult(False, lines)
        if dry_run:
            lines.append(f"[dry-run] restart {pid}")
            return RunResult(True, lines)
        result = restart_profile(registry, pid, ask_confirm=ask_confirm)
        lines.append(("[ok] " if result.ok else "[fail] ") + result.message)
        return RunResult(result.ok, lines)

    if intent.kind == "restore_battlefield":
        if dry_run:
            lines.append("[dry-run] restore_battlefield")
            return RunResult(True, lines)
        result = restore_battlefield(registry, ask_confirm=ask_confirm)
        lines.append(("[ok] " if result.ok else "[fail] ") + result.message)
        return RunResult(result.ok, lines)

    if intent.kind == "open_profile":
        pid = intent.profile_id
        if pid == "_pending_default_mc":
            pid, note = resolve_default_mc(registry, force_last=intent.force_last_mc)
            lines.append(f"[mc] {note}")
            if not pid:
                lines.append(f"[fail] {note}")
                return RunResult(False, lines)
        if not pid:
            lines.append("[fail] 無 profile_id")
            return RunResult(False, lines)
        if dry_run:
            extra = " force_new" if intent.force_new else ""
            lines.append(f"[dry-run] open {pid}{extra}")
            return RunResult(True, lines)
        result = launch_profile(
            registry, pid, ask_confirm=ask_confirm, force_new=intent.force_new
        )
        lines.append(("[ok] " if result.ok else "[fail] ") + result.message)
        return RunResult(result.ok, lines)

    if intent.kind in ("refuse", "unknown"):
        target = (intent.target_raw or "").strip()
        if target and intent.open_verb:
            cands = discover_candidates(target, registry)
            if cands:
                top = cands[0]
                lines.append(f"[discover] 候選：{top.label}（{top.kind}）")
                if dry_run:
                    lines.append(f"[dry-run] would confirm+launch {top.label}")
                    return RunResult(True, lines)
                prompt = f"未登錄「{target}」。係咪開「{top.label}」並寫入 profiles？"
                ok = ask_confirm(prompt) if ask_confirm else False
                if not ok:
                    lines.append("[fail] 已取消 Discover")
                    return RunResult(False, lines)
                try:
                    pid = commit_candidate(top)
                    lines.append(f"[discover] 已寫入 profile：{pid}")
                except (OSError, ValueError, FileNotFoundError) as exc:
                    lines.append(f"[fail] 寫入失敗：{exc}")
                    return RunResult(False, lines)
                result = launch_discovered(top.launch_hint, ask_confirm=ask_confirm)
                lines.append(("[ok] " if result.ok else "[fail] ") + result.message)
                return RunResult(result.ok, lines)
        lines.append(f"[fail] {intent.caption}")
        return RunResult(False, lines)

    lines.append(f"[fail] 未處理 intent：{intent.kind}")
    return RunResult(False, lines)
