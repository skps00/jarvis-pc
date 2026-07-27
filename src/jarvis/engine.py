"""Shared command execution for CLI and Shell UI."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.asr_fix import repair_asr_text
from jarvis.brain import (
    answer_query,
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
from jarvis.persist import commit_candidate
from jarvis.router import Intent, apply_verb_kind_limits, route


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

    if intent.kind in ("refuse", "unknown") and looks_ambiguous(intent, utterance):
        if llm_configured():
            try:
                brain_intent = resolve_ambiguous(utterance, registry)
            except RuntimeError as exc:
                lines.append(f"[brain] 失敗：{exc}")
                brain_intent = None
            if brain_intent and brain_intent.kind not in ("refuse", "unknown"):
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
