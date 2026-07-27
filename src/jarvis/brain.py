"""Small-LLM Brain: query captions + ambiguous JSON (OpenAI-compatible)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from jarvis.config import Registry
from jarvis.router import (
    Intent,
    _FORCE_NEW_MODIFIERS,
    apply_verb_kind_limits,
    route,
)

_ENV_LOADED = False
_PATH_LIKE = re.compile(r"[\\/].*\.(exe|bat|cmd|ps1|lnk)$", re.I)
_JSON_BLOB = re.compile(r"\{[\s\S]*\}")
_CLEAR_OPEN_ANY = re.compile(
    r"(再開|另開|多開|打開|開啟|啟動|\bopen\b|\blaunch\b|\bstart\b|\bplay\b|(?<![再另多])開)",
    re.I,
)
# 僅用於「無開動詞」閘：有明確關意先允許改關，否則 refuse（防漏「開」誤關）
_CLEAR_CLOSE_ANY = re.compile(
    r"(閂|冂|闩|關閉|關掉|關上|\bclose\b|\bquit\b|\bkill\b|(?<![再另多重新])關)",
    re.I,
)


def _load_dotenv() -> None:
    """Load KEY=VAL from .env in cwd / package parents (no python-dotenv)."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",  # repo root
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
        break


def llm_configured() -> bool:
    """True when an API key is available."""
    _load_dotenv()
    return bool(os.environ.get("JARVIS_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def _api_key() -> str:
    _load_dotenv()
    return (os.environ.get("JARVIS_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()


def _base_url() -> str:
    _load_dotenv()
    return (
        os.environ.get("JARVIS_LLM_BASE_URL") or "https://api.deepseek.com"
    ).rstrip("/")


def _model() -> str:
    _load_dotenv()
    return os.environ.get("JARVIS_LLM_MODEL") or "deepseek-chat"


def _registry_summary(registry: Registry) -> str:
    lines: list[str] = []
    for p in registry.profiles.values():
        if not p.enabled:
            continue
        names = ", ".join([*p.names[:6], *p.locale_hints[:3]])
        lines.append(f"- id={p.id} names=[{names}] kind={p.kind}")
    aliases = ", ".join(f"{k}→{v}" for k, v in list(registry.name_aliases.items())[:30])
    if aliases:
        lines.append(f"aliases: {aliases}")
    return "\n".join(lines) if lines else "(empty registry)"


def _chat(messages: list[dict[str, str]], *, json_mode: bool = True) -> str:
    """Call OpenAI-compatible chat completions; return assistant text."""
    key = _api_key()
    if not key:
        raise RuntimeError("未設定 JARVIS_LLM_API_KEY（或 OPENAI_API_KEY）")

    url = f"{_base_url()}/v1/chat/completions"
    body: dict[str, Any] = {
        "model": _model(),
        "messages": messages,
        "temperature": 0.2,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Some providers reject response_format — retry once without it
        if json_mode and exc.code in (400, 422):
            return _chat(messages, json_mode=False)
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
    except OSError as exc:
        raise RuntimeError(f"LLM 連線失敗：{exc}") from exc

    try:
        return str(payload["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"LLM 回應格式異常：{payload!r}"[:200]) from exc


def _parse_json_obj(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_BLOB.search(text)
        if not m:
            raise
        obj = json.loads(m.group(0))
    if not isinstance(obj, dict):
        raise ValueError("JSON root must be object")
    return obj


def answer_query(text: str, registry: Registry) -> str:
    """Short Traditional Chinese caption; never launches apps."""
    summary = _registry_summary(registry)
    messages = [
        {
            "role": "system",
            "content": (
                "你是 JARVIS 管家的唯讀助手。只用繁體中文短答（1–3 句）。"
                "不可開啟應用、不可給出 exe／bat／任意 shell 路徑、不可假裝已執行。"
                "可參考已登錄 profile 名稱表回答「點樣講口令」類問題。\n"
                f"profiles:\n{summary}"
            ),
        },
        {"role": "user", "content": text},
    ]
    # query answers are prose, not JSON
    return _chat(messages, json_mode=False)


def looks_ambiguous(intent: Intent, text: str) -> bool:
    """Whether refuse/unknown should try LLM before Discover."""
    if intent.kind not in ("refuse", "unknown"):
        return False
    if intent.open_verb:
        return True
    if intent.kind == "unknown":
        return True
    lower = text.lower()
    for m in _FORCE_NEW_MODIFIERS | {"再開", "另開", "多開"}:
        if m.isascii():
            if m.lower() in lower:
                return True
        elif m in text:
            return True
    return bool((intent.target_raw or "").strip())


def intent_from_llm_json(data: dict[str, Any], registry: Registry, *, raw_text: str) -> Intent | None:
    """Map model JSON → Intent; re-resolve via registry (never trust paths)."""
    kind = str(data.get("intent") or "unknown").strip()
    allowed = {
        "open_profile",
        "close_profile",
        "restart_profile",
        "restore_battlefield",
        "query",
        "system_power",
        "refuse",
        "unknown",
    }
    if kind not in allowed:
        kind = "unknown"

    speak = str(data.get("speak_caption") or "").strip()
    target_raw = data.get("target_raw")
    target_raw = str(target_raw).strip() if target_raw is not None else ""
    if target_raw and _PATH_LIKE.search(target_raw):
        return Intent("refuse", caption="LLM 回傳路徑已拒絕", target_raw=target_raw)

    profile_id = data.get("profile_id")
    profile_id = str(profile_id).strip() if profile_id else None
    if profile_id:
        ok_id = profile_id == "_pending_default_mc" or (
            profile_id in registry.profiles and registry.profiles[profile_id].enabled
        )
        if not ok_id:
            profile_id = None

    force_new = bool(data.get("force_new"))
    force_last = bool(data.get("force_last_mc"))
    power = data.get("power_action")
    power = str(power).strip() if power else None
    if power not in ("shutdown", "sleep", None):
        power = None

    if kind == "query":
        return Intent("query", caption=speak or f"查詢：{raw_text}", target_raw=raw_text)

    if kind == "close_profile":
        # reuse open resolve then flip
        if target_raw:
            local = apply_verb_kind_limits(route(f"關 {target_raw}", registry), registry)
            if local.kind == "close_profile":
                if speak:
                    local.caption = speak
                return local
        if profile_id and (
            profile_id == "_pending_default_mc"
            or (profile_id in registry.profiles and registry.profiles[profile_id].enabled)
        ):
            name = (
                "Minecraft"
                if profile_id == "_pending_default_mc"
                else registry.profiles[profile_id].display_name
            )
            return Intent(
                "close_profile",
                profile_id=profile_id,
                open_verb="關",
                target_raw=target_raw or profile_id,
                caption=speak or f"關閉 {name}（需確認）",
            )
        return Intent("refuse", caption=speak or "唔知關邊個")

    if kind == "restart_profile":
        if target_raw:
            local = apply_verb_kind_limits(route(f"重開 {target_raw}", registry), registry)
            if local.kind == "restart_profile":
                if speak:
                    local.caption = speak
                return local
        if profile_id and profile_id in registry.profiles and registry.profiles[profile_id].enabled:
            return Intent(
                "restart_profile",
                profile_id=profile_id,
                open_verb="重開",
                target_raw=target_raw or profile_id,
                caption=speak or f"重開 {registry.profiles[profile_id].display_name}（需確認）",
            )
        return Intent("refuse", caption=speak or "唔知重開邊個")

    if kind == "system_power":
        if power not in ("shutdown", "sleep"):
            return Intent("refuse", caption="LLM 電源動作無效")
        label = "關機" if power == "shutdown" else "睡眠"
        return Intent(
            "system_power",
            power_action=power,
            caption=speak or f"{label}（需確認）",
            target_raw=raw_text,
        )

    if kind == "restore_battlefield":
        return Intent(
            "restore_battlefield",
            caption=speak or "還原戰場",
            target_raw=raw_text,
        )

    if kind in ("refuse", "unknown"):
        return Intent(kind, caption=speak or kind, target_raw=target_raw or raw_text)

    # open_profile — re-resolve through local router when possible
    if target_raw:
        rebuilt = f"開 {target_raw}"
        if force_new and not any(
            target_raw.lower().startswith(m.lower()) for m in _FORCE_NEW_MODIFIERS
        ):
            rebuilt = f"開 new {target_raw}"
        if force_last:
            rebuilt = f"開上次 {target_raw}"
        local = apply_verb_kind_limits(route(rebuilt, registry), registry)
        if local.kind == "open_profile":
            local.force_new = local.force_new or force_new
            local.force_last_mc = local.force_last_mc or force_last
            if speak:
                local.caption = speak
            else:
                local.caption = f"LLM→{local.caption}"
            return local

    if profile_id and (
        profile_id == "_pending_default_mc"
        or (profile_id in registry.profiles and registry.profiles[profile_id].enabled)
    ):
        cap = speak or f"開啟 {profile_id}"
        if force_new and not cap.startswith("新開"):
            cap = f"新開 {cap}"
        return Intent(
            "open_profile",
            profile_id=profile_id,
            open_verb="開",
            target_raw=target_raw or profile_id,
            force_new=force_new,
            force_last_mc=force_last,
            caption=cap,
        )

    return None


def has_clear_open_verb(text: str) -> bool:
    """True if utterance clearly asks to open/launch."""
    return bool(_CLEAR_OPEN_ANY.search(text or ""))


def has_clear_close_verb(text: str) -> bool:
    """True if utterance clearly asks to close/quit."""
    return bool(_CLEAR_CLOSE_ANY.search(text or ""))


def resolve_ambiguous(text: str, registry: Registry) -> Intent | None:
    """Ask small LLM for intent JSON; return gated Intent or None."""
    summary = _registry_summary(registry)
    schema = (
        '{"intent":"open_profile|close_profile|restart_profile|restore_battlefield|'
        'query|system_power|refuse|unknown",'
        '"target_raw":"string|null","profile_id":"id from list or null",'
        '"force_new":false,"force_last_mc":false,'
        '"power_action":"shutdown|sleep|null","speak_caption":"短字幕"}'
    )
    open_ok = has_clear_open_verb(text)
    close_ok = has_clear_close_verb(text)
    messages = [
        {
            "role": "system",
            "content": (
                "你是 JARVIS 意圖解析器。只輸出一個 JSON 物件，不要 markdown。\n"
                "規則：target_raw／profile_id 必須對得上 profiles；不可發明 exe 路徑。\n"
                "關／閂／close／shut（含 STT 亂碼如 |-] dico）→ close_profile，唔好 open_profile。\n"
                "無明確開動詞（開／open／launch／打開）時，禁止 open_profile；宁可 refuse。\n"
                "無開亦無關提示時，輸出 refuse，唔好猜開或關。\n"
                f"本句是否有明確開動詞：{'yes' if open_ok else 'NO — do not open'}。\n"
                f"本句是否有明確關動詞：{'yes' if close_ok else 'no'}。\n"
                f"schema: {schema}\n"
                f"profiles:\n{summary}"
            ),
        },
        {"role": "user", "content": text},
    ]
    raw = _chat(messages, json_mode=True)
    data = _parse_json_obj(raw)
    intent = intent_from_llm_json(data, registry, raw_text=text)
    if intent is None:
        return None
    # Hard gate: no clear open verb → never open; flip to close only with close hint
    if intent.kind == "open_profile" and not open_ok:
        if close_ok and (intent.profile_id or intent.target_raw):
            target = intent.target_raw or intent.profile_id or ""
            flipped = apply_verb_kind_limits(route(f"關 {target}", registry), registry)
            if flipped.kind == "close_profile":
                return flipped
            if intent.profile_id:
                return Intent(
                    "close_profile",
                    profile_id=intent.profile_id,
                    open_verb="關",
                    target_raw=intent.target_raw,
                    caption="關閉（無開動詞，有關提示）（需確認）",
                )
        return Intent(
            "refuse",
            caption="聽唔清開定關，請講「開 X」或「關 X」",
            target_raw=text,
        )
    return intent
