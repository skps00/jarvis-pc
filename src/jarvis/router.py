"""Pattern-first intent router: verb + name, restore phrases, no LLM."""

from __future__ import annotations

import re
from dataclasses import dataclass

from jarvis.config import Profile, Registry


@dataclass
class Intent:
    """Structured result of local routing (Hands never trusts free paths)."""

    kind: str  # open_profile | close_profile | restart_profile | restore_battlefield | refuse | unknown | query | system_power
    profile_id: str | None = None
    open_verb: str | None = None
    target_raw: str | None = None
    target_modifier: str | None = None
    caption: str = ""
    force_last_mc: bool = False
    force_new: bool = False
    power_action: str | None = None  # shutdown | sleep | reboot


_TAIL_PARTICLES = re.compile(r"(啦|啊|先|please|plz)\s*$", re.I)
_LEAD_PARTICLES = re.compile(r"^(please|plz|唔該|拜託|请|請)\s+", re.I)
_TAIL_PUNCT = re.compile(r"[。．\.！!？\?，,、；;：:\s]+$")
# 粵語「開 X 出嚟」——指令尾，唔係 app 名
_TAIL_DIRECTIVES = re.compile(r"(出嚟|出来|出來|出黎)\s*$")
_CLASSIFIER_GE = re.compile(r"^個\s*")

_LAST_MODIFIERS = frozenset({"上次", "上一次", "last", "previous"})
_FORCE_NEW_MODIFIERS = frozenset(
    {
        "new window",
        "新視窗",
        "再開",
        "另開",
        "多開",
        "another",
        "一個新嘅",
        "一個新",
        "新嘅",
        "新的",
        "new",
        "新",
    }
)
_FORCE_NEW_VERBS = frozenset({"再開", "另開", "多開"})
_CLOSE_VERBS = (
    "關閉",
    "關掉",
    "關上",
    "close",
    "quit",
    "kill",
    "閂",
    "關",
)
_RESTART_VERBS = (
    "重新開啟",
    "重新打開",
    "重新開",
    "restart",
    "reboot",
    "重開",
    "重啟",
)

# 整句電源指令（唔用「關」開頭亂配，避免「關 Chrome」）
_POWER_PHRASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "shutdown",
        (
            "shut down now",
            "shut down",
            "shutdown now",
            "shutdown",
            "power off",
            "turn off computer",
            "turn off pc",
            "關電腦",
            "關掉電腦",
            "關機啦",
            "關機",
            "关机",
        ),
    ),
    (
        "reboot",
        (
            "restart computer",
            "restart pc",
            "reboot now",
            "reboot",
            "重新開機",
            "重啟電腦",
            "重啟機",
            "重启电脑",
        ),
    ),
    (
        "sleep",
        (
            "go to sleep",
            "sleep now",
            "hibernate",
            "sleep",
            "進入睡眠",
            "睡眠模式",
            "休眠",
            "睡眠",
            "睡覺",
            "瞓覺",
            "去瞓",
        ),
    ),
)

# SenseVoice / 簡中 STT → 繁中指令字（最長優先）
_ASR_SIMP_TO_TRAD: tuple[tuple[str, str], ...] = (
    ("帮我打开", "幫我打開"),
    ("帮我开", "幫我開"),
    ("打开", "打開"),
    ("开启", "開啟"),
    ("启动", "啟動"),
    ("开始", "開始"),
    ("进入", "進入"),
    ("开返", "開返"),
    ("还原战场", "還原戰場"),
    ("恢复战场", "恢復戰場"),
    ("还原", "還原"),
    ("恢复", "恢復"),
    ("浏览器", "瀏覽器"),
    ("战场", "戰場"),
    ("上次", "上次"),
    ("关闭", "關閉"),
    ("关掉", "關掉"),
    ("关上", "關上"),
    ("重启电脑", "重啟電腦"),
    ("重新开机", "重新開機"),
    ("重启", "重啟"),
    ("重开", "重開"),
    ("关机", "關機"),
    ("关", "關"),
    ("开", "開"),
    ("请", "請"),
    ("个", "個"),
)


def normalize_utterance(text: str) -> str:
    """Collapse whitespace, strip punct, map common简体 ASR → 繁體 verbs."""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    t = _LEAD_PARTICLES.sub("", t).strip()
    t = _TAIL_PARTICLES.sub("", t).strip()
    t = _TAIL_PUNCT.sub("", t).strip()
    t = _TAIL_DIRECTIVES.sub("", t).strip()
    t = _TAIL_PUNCT.sub("", t).strip()
    for simp, trad in _ASR_SIMP_TO_TRAD:
        if simp in t:
            t = t.replace(simp, trad)
    return t


def route(text: str, registry: Registry) -> Intent:
    """Parse user text into an Intent using registry tables only."""
    original = normalize_utterance(text)
    if not original:
        return Intent("unknown", caption="空白指令")

    lower = original.lower()

    # 0) query → caption only (LLM later)
    q = _match_query(original)
    if q:
        return Intent("query", caption=q, target_raw=original)

    # 0b) system power（Always Yes 喺 Hands）— 必須早於「關 xxx」
    power = _match_power(original)
    if power:
        return power

    # 0c) close profile（關 CS／close Chrome）
    close_intent = _match_close(original, registry)
    if close_intent:
        return close_intent

    # 0d) restart profile（restart CS／重開 Chrome）— 早於普通 open
    restart_intent = _match_restart(original, registry)
    if restart_intent:
        return restart_intent

    # 1) restore phrases (longest first)
    for phrase in sorted(registry.restore_phrases, key=len, reverse=True):
        p = phrase.lower().strip()
        if not p:
            continue
        if lower == p or lower.startswith(p + " ") or lower.endswith(" " + p):
            return Intent("restore_battlefield", caption=f"還原戰場（匹配：{phrase}）")
        if p in lower and len(p) >= 4:
            return Intent("restore_battlefield", caption=f"還原戰場（匹配：{phrase}）")

    # 2) open verb (prefix or inverted suffix)
    verb, rest, inverted = _split_verb(original, registry.open_verbs)
    if verb is None:
        if registry.allow_bare_name:
            hit = _resolve_target(original, registry, verb="open")
            return hit
        return Intent("unknown", caption="未識別開啟動詞（open／開／launch…）")

    force_new = False
    if verb in _FORCE_NEW_VERBS:
        force_new = True
        verb = "開"

    # classifier 個 after verb（開個 browser → browser）；唔當 force_new
    rest = _CLASSIFIER_GE.sub("", rest).strip()

    # 3) modifiers
    modifier, rest2 = _split_modifier(rest, registry.target_modifiers)
    target_raw = rest2.strip()
    target_raw = _CLASSIFIER_GE.sub("", target_raw).strip()
    if not target_raw and not inverted:
        return Intent("refuse", open_verb=verb, caption="有動詞但無目標")

    # inverted already put target in rest before verb strip differently
    if inverted and not target_raw:
        target_raw = rest.strip()

    intent = _resolve_target(target_raw, registry, verb=verb)
    intent.open_verb = verb
    intent.target_raw = target_raw
    intent.target_modifier = modifier

    mod_key = (modifier or "").lower()
    if force_new or mod_key in {m.lower() for m in _FORCE_NEW_MODIFIERS}:
        intent.force_new = True
        if intent.kind == "open_profile":
            if intent.caption.startswith("開啟"):
                intent.caption = "新開" + intent.caption[2:]
            elif not intent.caption.startswith("新開"):
                intent.caption = f"新開 {intent.caption}"

    if mod_key in _LAST_MODIFIERS:
        if intent.profile_id == "_pending_default_mc" or _looks_like_mc_name(target_raw):
            intent.force_last_mc = True
            if intent.kind == "refuse":
                intent = Intent(
                    "open_profile",
                    profile_id="_pending_default_mc",
                    open_verb=verb,
                    target_raw=target_raw,
                    target_modifier=modifier,
                    force_last_mc=True,
                    caption="開上次 MC",
                )
    return intent


_QUERY_MARKERS = (
    "幫我查",
    "查下",
    "查詢",
    "點樣",
    "怎樣",
    "什麼是",
    "咩係",
    "what is",
    "what's",
    "how do",
    "how to",
    "check ",
)


def _match_power(text: str) -> Intent | None:
    """Exact-ish whole utterance → shutdown／sleep."""
    lower = text.lower().strip()
    for action, phrases in _POWER_PHRASES:
        for phrase in sorted(phrases, key=len, reverse=True):
            p = phrase.lower()
            if lower == p or lower == p + "啦" or lower == p + "啊":
                if action == "shutdown":
                    label = "關機"
                elif action == "reboot":
                    label = "重新開機"
                else:
                    label = "睡眠"
                return Intent(
                    "system_power",
                    power_action=action,
                    caption=f"{label}（需確認）",
                    target_raw=text,
                )
    return None


def _match_close(text: str, registry: Registry) -> Intent | None:
    """關／close + registered target → close_profile."""
    verb, rest, inverted = _split_verb(text, list(_CLOSE_VERBS))
    if verb is None:
        return None
    # 避免「關機」漏網（理論上 power 已截）
    if rest.strip() in ("機", "电脑", "電腦") or text.replace(" ", "") in ("關機", "关机"):
        return None
    rest = _CLASSIFIER_GE.sub("", rest.strip()).strip()
    if inverted and not rest:
        rest = text  # shouldn't happen
    if not rest:
        return Intent("refuse", open_verb=verb, caption="有關閉動詞但無目標")
    resolved = _resolve_target(rest, registry, verb="close")
    if resolved.kind != "open_profile" or not resolved.profile_id:
        return Intent(
            "refuse",
            open_verb=verb,
            target_raw=rest,
            caption=resolved.caption or f"未登錄「{rest}」，唔知關邊個",
        )
    pid = resolved.profile_id
    if pid == "_pending_default_mc":
        name = "Minecraft"
    else:
        name = registry.profiles[pid].display_name
    return Intent(
        "close_profile",
        profile_id=pid,
        open_verb=verb,
        target_raw=rest,
        caption=f"關閉 {name}（需確認）",
    )


def _match_restart(text: str, registry: Registry) -> Intent | None:
    """restart／重開 + target → restart_profile（唔係重啟電腦）."""
    verb, rest, _inverted = _split_verb(text, list(_RESTART_VERBS))
    if verb is None:
        return None
    rest = _CLASSIFIER_GE.sub("", rest.strip()).strip()
    if not rest:
        return Intent("refuse", open_verb=verb, caption="有重開動詞但無目標（重啟電腦請講「重啟電腦」）")
    # 目標係「電腦／機」→ 交俾 power（理論上整句已截）
    if rest.lower() in ("computer", "pc", "電腦", "电脑", "機", "机"):
        return Intent(
            "system_power",
            power_action="reboot",
            caption="重新開機（需確認）",
            target_raw=text,
        )
    resolved = _resolve_target(rest, registry, verb="restart")
    if resolved.kind != "open_profile" or not resolved.profile_id:
        return Intent(
            "refuse",
            open_verb=verb,
            target_raw=rest,
            caption=resolved.caption or f"未登錄「{rest}」，唔知重開邊個",
        )
    pid = resolved.profile_id
    if pid == "_pending_default_mc":
        name = "Minecraft"
    else:
        name = registry.profiles[pid].display_name
    return Intent(
        "restart_profile",
        profile_id=pid,
        open_verb=verb,
        target_raw=rest,
        caption=f"重開 {name}（需確認）",
    )


def _match_query(text: str) -> str | None:
    """Return query caption if utterance looks like a read-only question."""
    lower = text.lower()
    if any(m in lower for m in _QUERY_MARKERS):
        return f"查詢：{text}"
    return None


def _looks_like_mc_name(target: str) -> bool:
    t = target.lower().replace(" ", "")
    return t in ("mc", "minecraft", "我的世界", "方塊") or "minecraft" in t


def _split_verb(text: str, verbs: list[str]) -> tuple[str | None, str, bool]:
    """Return (verb, remainder, inverted). Longest match wins."""
    ordered = sorted({v.strip() for v in verbs if v.strip()}, key=len, reverse=True)
    lower = text.lower()
    # prefix
    for v in ordered:
        vl = v.lower()
        if lower.startswith(vl):
            rest = text[len(v) :].lstrip(" \t:-")
            return v.lower(), rest, False
        # no-space CJK: 開CS
        if not vl.isascii() and text.startswith(v):
            return v.lower(), text[len(v) :].lstrip(), False
    # inverted: "<target> <verb>" or "<target>開啦"
    for v in ordered:
        vl = v.lower()
        if lower.endswith(" " + vl):
            return v.lower(), text[: -(len(v) + 1)].strip(), True
        if lower.endswith(vl) and len(text) > len(v):
            return v.lower(), text[: -len(v)].strip(), True
    # 開啦 after target already stripped particle in normalize — handle "Cursor開"
    return None, text, False


def _split_modifier(text: str, modifiers: list[str]) -> tuple[str | None, str]:
    ordered = sorted({m.strip() for m in modifiers if m.strip()}, key=len, reverse=True)
    lower = text.lower()
    for m in ordered:
        ml = m.lower()
        if lower.startswith(ml + " ") or lower.startswith(ml):
            rest = text[len(m) :].lstrip(" \t")
            return m.lower(), rest
    return None, text


def _resolve_target(target_raw: str, registry: Registry, *, verb: str) -> Intent:
    """Map target string to profile id or refuse."""
    policy = registry.match_policy
    min_chars = int(policy.get("min_name_chars") or 2)
    hint_min = int(policy.get("locale_hints_min_chars") or 2)
    require_verb_for_hints = bool(policy.get("locale_hints_require_verb", True))

    raw = target_raw.strip()
    if len(raw) < min_chars:
        return Intent("refuse", caption=f"目標太短（最少 {min_chars} 字）", target_raw=raw)

    key = raw.lower()
    # aliases
    if key in registry.name_aliases:
        alias = registry.name_aliases[key]
        if alias == "_default_mc":
            return Intent(
                "open_profile",
                profile_id="_pending_default_mc",
                target_raw=raw,
                caption="預設／上次 Minecraft",
            )
        if alias in registry.profiles and registry.profiles[alias].enabled:
            return _check_verb_kind(verb, registry.profiles[alias], raw)

    hits: list[Profile] = []
    for profile in registry.profiles.values():
        if not profile.enabled:
            continue
        names = [n for n in profile.names if len(n) >= min_chars]
        hints = [h for h in profile.locale_hints if len(h) >= hint_min]
        for n in names:
            if key == n.lower() or key.replace(" ", "") == n.lower().replace(" ", ""):
                hits.append(profile)
                break
        else:
            if not require_verb_for_hints or verb:
                for h in hints:
                    if key == h.lower():
                        hits.append(profile)
                        break

    # longest unique
    if not hits:
        # partial contains for longer names
        for profile in registry.profiles.values():
            if not profile.enabled:
                continue
            for n in profile.names:
                nl = n.lower()
                if len(nl) >= min_chars and (nl in key or key in nl):
                    hits.append(profile)
                    break

    # dedupe
    uniq: dict[str, Profile] = {p.id: p for p in hits}
    hits = list(uniq.values())

    if len(hits) == 1:
        return _check_verb_kind(verb, hits[0], raw)
    if len(hits) > 1:
        ids = ", ".join(p.id for p in hits)
        return Intent("refuse", caption=f"多個候選：{ids}（請講清楚）", target_raw=raw)
    return Intent("refuse", caption=f"未登錄「{raw}」（v1 不自動搜尋；見 REMINDERS.md）", target_raw=raw)


def _check_verb_kind(verb: str, profile: Profile, raw: str) -> Intent:
    limits = None  # filled by caller registry — pass via closure
    return Intent(
        "open_profile",
        profile_id=profile.id,
        open_verb=verb,
        target_raw=raw,
        caption=f"開啟 {profile.display_name}",
    )


def apply_verb_kind_limits(intent: Intent, registry: Registry) -> Intent:
    """Reject play+non-game etc. Call after route()."""
    if intent.kind != "open_profile" or not intent.open_verb or not intent.profile_id:
        return intent
    if intent.profile_id == "_pending_default_mc":
        kinds = ["launcher_instance"]
    else:
        profile = registry.profiles.get(intent.profile_id)
        if not profile:
            return intent
        kinds = [profile.kind]
    allowed = registry.verb_kind_limits.get(intent.open_verb.lower())
    if not allowed:
        return intent
    if kinds[0] not in allowed:
        return Intent(
            "refuse",
            open_verb=intent.open_verb,
            target_raw=intent.target_raw,
            caption=f"「{intent.open_verb}」只適用於 {allowed}，唔適用於 {kinds[0]}",
        )
    return intent
