"""Repair noisy SenseVoice text into Jarvis command shapes."""

from __future__ import annotations

import re

from jarvis.config import Registry
from jarvis.router import (
    _FORCE_NEW_MODIFIERS,
    apply_verb_kind_limits,
    normalize_utterance,
    route,
)

# 口語／STT 常見誤聽 → 正規指令片段（最長優先）
# 英文專名好短，SenseVoice 成日聽錯——唔關口音
_CONFUSIONS: tuple[tuple[str, str], ...] = (
    # force_new 短語（先於專名）
    ("new windows", "new window"),
    ("knew window", "new window"),
    ("nu window", "new window"),
    ("new win dow", "new window"),
    ("new win", "new window"),
    ("新事窗", "新視窗"),
    ("新式窗", "新視窗"),
    ("在開", "再開"),
    ("載開", "再開"),
    ("再看", "再開"),  # ponytail: STT 常見；真「再看」指令極少
    ("令開", "另開"),
    ("亮開", "另開"),
    # 閂／minecraft 常見 STT 變體（SenseVoice 成日寫錯字）
    ("冂", "閂"),
    ("闩", "閂"),
    ("閞", "閂"),
    ("macraft", "minecraft"),
    ("ma craft", "minecraft"),
    ("mycraft", "minecraft"),
    ("mine craft", "minecraft"),
    ("my craft", "minecraft"),
    ("開线", "開 CS"),
    ("开线", "開 CS"),
    ("開線", "開 CS"),
    ("开線", "開 CS"),
    ("開c s", "開 CS"),
    ("開cs2", "開 CS2"),
    ("开cs2", "開 CS2"),
    ("開cs", "開 CS"),
    ("开cs", "開 CS"),
    ("開 caa", "開 CS"),
    ("开 caa", "開 CS"),
    ("開caa", "開 CS"),
    ("开caa", "開 CS"),
    ("開 ka", "開 CS"),
    ("开 ka", "開 CS"),
    ("開kaa", "開 CS"),
    ("開 sea", "開 CS"),
    ("开 sea", "開 CS"),
    ("開 see", "開 CS"),
    ("開 cura", "開 Cursor"),
    ("开 cura", "開 Cursor"),
    ("開cura", "開 Cursor"),
    ("开cura", "開 Cursor"),
    ("開 cur", "開 Cursor"),
    ("开 cur", "開 Cursor"),
    ("開 kura", "開 Cursor"),
    ("开 kura", "開 Cursor"),
    ("開 curso", "開 Cursor"),
    ("开 curso", "開 Cursor"),
    ("開 chrome", "開 Chrome"),
    ("开 chrome", "開 Chrome"),
    ("開 guge", "開 Chrome"),
    ("counter strike", "CS2"),
    ("counter-strike", "CS2"),
    ("curser", "Cursor"),
    ("cursur", "Cursor"),
    ("cura", "Cursor"),
    ("caa", "CS"),
    ("卡索", "Cursor"),
    ("柯索", "Cursor"),
)

# 唔含 new／新——避免食掉 force_new 修飾詞
_FILLER = re.compile(
    r"(測試|测试|试下|試下|嗯+|呃+|嗱|嗱嗱|呢個|那个|那個|就是|然後|然后)"
)
_TRAIL_PARTICLES = re.compile(r"[嘅的了啦呀哦喔咧咯唓]+")
# SenseVoice 常把 browser 寫成「包+沙系」；第二字每次漂
_BROWSER_BAU_SAA = re.compile(r"包[耍刷搜沙洒灑紗莎啥撒傻廈厦]")
_CLOSE_HINT = re.compile(
    r"(閂|冂|闩|散|傘|伞|蒜|算|山|三|關閉|關掉|關上|\bclose\b|\bquit\b|\bkill\b|(?<![再另多重新])關)",
    re.I,
)
# SenseVoice 常把「閂」(saan) 聽成散／s／三…；後接 MC 別名 → 強制關
_MC_LIKE = re.compile(
    r"(my\s*craft|macraft|mycraft|minecraft|\bmc\b|我的世界)",
    re.I,
)
_SAAN_CLOSE_PREFIX = re.compile(
    r"^(散|傘|伞|蒜|算|山|三|閃|冂|闩|閂|關|关闭|關掉|關上|san|saan|s|打)(?:\s+|$)",
    re.I,
)
_CLEAR_OPEN_PREFIX = re.compile(
    r"^(再開|另開|多開|打開|開啟|啟動|開|open|launch|start|play|run)\b",
    re.I,
)
_OPEN_PREFIX = re.compile(
    r"^(再開|另開|多開|開|打开|打開|開啟|啟動|open|launch|start|play)\s+(.+)$",
    re.I,
)
_FORCE_NEW_VERBS = frozenset({"再開", "另開", "多開"})

# 目標詞單獨誤聽（開 X 嘅 X）
_TARGET_ALIASES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(caa|ka+|kaa|c\s*aa|sea|see|si+|串|死)$", re.I), "CS"),
    (re.compile(r"^(cs2|c\s*s\s*2)$", re.I), "CS2"),
    (re.compile(r"^(cura|cur[ao]?|curso?r?|kura|kursor)$", re.I), "Cursor"),
    (re.compile(r"^(chrom[eo]?|guge|google)$", re.I), "Chrome"),
    (re.compile(r"^(包[耍刷搜沙洒灑紗莎啥撒傻廈厦]|brow+s?e?r?)$", re.I), "browser"),
    (re.compile(r"^(mc|mine.?craft|我的世界)$", re.I), "Minecraft"),
)


def _usable(intent_kind: str) -> bool:
    return intent_kind in (
        "open_profile",
        "close_profile",
        "restart_profile",
        "restore_battlefield",
        "query",
        "system_power",
    )


def _all_names(registry: Registry) -> list[str]:
    names: list[str] = []
    for p in registry.profiles.values():
        if not p.enabled:
            continue
        names.extend(p.names)
        names.extend(p.locale_hints)
        names.append(p.display_name)
    names.extend(registry.name_aliases.keys())
    return [n for n in {n.strip() for n in names if n and len(n.strip()) >= 2}]


def _command_templates(registry: Registry) -> list[str]:
    """Build short canonical phrases for fuzzy match."""
    verbs = [
        "開",
        "打開",
        "開啟",
        "啟動",
        "open",
        "launch",
        "play",
        "還原",
        "restore",
        "再開",
        "另開",
        "多開",
        "關",
        "關閉",
        "關掉",
        "閂",
        "close",
        "quit",
        "restart",
        "重開",
        "重啟",
    ]
    names = _all_names(registry)
    out: list[str] = []
    for v in verbs:
        for n in names:
            out.append(f"{v} {n}")
            out.append(f"{n} {v}")
    for n in names:
        out.append(f"開 new {n}")
        out.append(f"開 new window {n}")
        out.append(f"開新視窗 {n}")
    out.extend(registry.restore_phrases)
    return out


def _peel_force_new_mod(target: str) -> tuple[str, str | None]:
    """Strip leading force_new modifier; return (rest, mod_or_None)."""
    t = target.strip()
    for m in sorted(_FORCE_NEW_MODIFIERS, key=len, reverse=True):
        if t.lower().startswith(m.lower()):
            rest = t[len(m) :].strip()
            rest = re.sub(r"^個\s*", "", rest).strip()
            return rest, m
    return t, None


def _rebuild_open(verb: str, canon: str, mod: str | None) -> str:
    v = verb if verb in _FORCE_NEW_VERBS else "開"
    if v in _FORCE_NEW_VERBS:
        return f"{v} {canon}"
    if mod:
        return f"開 {mod} {canon}"
    return f"開 {canon}"


def _fix_open_target(text: str, registry: Registry) -> str | None:
    """If『開 xxx』and xxx looks like a known app, rebuild canonical command."""
    m = _OPEN_PREFIX.match(text.strip())
    if not m:
        return None
    verb = m.group(1)
    target = m.group(2).strip()
    # 只剝尾助詞；保留「新嘅」中間嘅 嘅（由 modifier peel 處理）
    target = re.sub(r"[了啦呀哦喔咧咯唓]+$", "", target).strip()
    if not target:
        return None

    mod: str | None = None
    if verb.lower() not in {x.lower() for x in _FORCE_NEW_VERBS}:
        target, mod = _peel_force_new_mod(target)

    for pat, canon in _TARGET_ALIASES:
        if pat.match(target):
            return _rebuild_open(verb, canon, mod)

    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        return None

    names = _all_names(registry)
    # 短英文專名用 ratio；caa↔CS 分數唔高，所以先走 _TARGET_ALIASES
    hit = process.extractOne(target, names, scorer=fuzz.WRatio, score_cutoff=70)
    if not hit:
        hit = process.extractOne(target, names, scorer=fuzz.partial_ratio, score_cutoff=80)
    if not hit:
        return None
    best, score, _ = hit
    if score < 70:
        return None
    return _rebuild_open(verb, best, mod)


def _force_close_mc(text: str) -> str | None:
    """If STT garbled 閂 + Minecraft target, force canonical close command."""
    t = text.strip()
    if not _MC_LIKE.search(t):
        return None
    if _CLEAR_OPEN_PREFIX.match(t):
        return None
    if _SAAN_CLOSE_PREFIX.match(t) or _CLOSE_HINT.search(t):
        return "閂 minecraft"
    # 「s my craft」／無動詞只得 mc 名：唔亂猜開
    # 單字母／單字 + mc → 當閂
    if re.match(r"^[a-zA-Z]{1,2}\s+", t) and _MC_LIKE.search(t):
        return "閂 minecraft"
    return None


def repair_asr_text(text: str, registry: Registry) -> tuple[str, str | None]:
    """
    Return (text_for_router, note_or_None).

    note is set when repair changed the string.
    """
    raw = normalize_utterance(text)
    if not raw:
        return raw, None

    t = raw
    for bad, good in _CONFUSIONS:
        if bad.lower() in t.lower() or bad in t:
            t = re.sub(re.escape(bad), good, t, flags=re.I)
    t = _BROWSER_BAU_SAA.sub("browser", t)
    forced = _force_close_mc(t)
    if forced:
        t = forced
    t = normalize_utterance(t)

    intent = apply_verb_kind_limits(route(t, registry), registry)
    if _usable(intent.kind):
        if t != raw:
            return t, f"ASR 修正：{raw!r} → {t!r}"
        return t, None

    t2 = _FILLER.sub("", t)
    t2 = _TRAIL_PARTICLES.sub("", t2)
    t2 = normalize_utterance(t2)
    forced = _force_close_mc(t2) or _force_close_mc(raw)
    if forced:
        t2 = forced

    # 閂／關／散… 句唔好建成「開 X」
    if not (
        _CLOSE_HINT.search(t2)
        or _CLOSE_HINT.search(raw)
        or _SAAN_CLOSE_PREFIX.match(t2)
        or _SAAN_CLOSE_PREFIX.match(raw)
        or forced
    ):
        rebuilt = _fix_open_target(t2, registry)
        if rebuilt:
            t2 = rebuilt

    intent = apply_verb_kind_limits(route(t2, registry), registry)
    if _usable(intent.kind) and t2 != raw:
        return t2, f"ASR 修正：{raw!r} → {t2!r}"
    if _usable(intent.kind):
        return t2, None
    t = t2

    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        return raw, None

    templates = _command_templates(registry)
    mc_close_bias = bool(_MC_LIKE.search(t) or _MC_LIKE.search(raw)) and not (
        _CLEAR_OPEN_PREFIX.match(t) or _CLEAR_OPEN_PREFIX.match(raw)
    )
    if (
        mc_close_bias
        or _CLOSE_HINT.search(t)
        or _CLOSE_HINT.search(raw)
        or _SAAN_CLOSE_PREFIX.match(raw)
    ):
        templates = [
            x
            for x in templates
            if re.match(r"^(關|關閉|關掉|閂|close|quit|kill)(\s|$)", x, re.I)
            or re.search(r"\s(關|關閉|關掉|閂|close|quit|kill)$", x, re.I)
        ]
    if not templates:
        return raw, None

    hit = process.extractOne(
        t,
        templates,
        scorer=fuzz.token_set_ratio,
        score_cutoff=65,
    )
    if not hit:
        hit = process.extractOne(
            raw,
            templates,
            scorer=fuzz.token_set_ratio,
            score_cutoff=65,
        )
    if not hit:
        return raw, None

    best, score, _ = hit
    # 最後閘：mc 關閉偏向時拒絕任何「開…」結果
    if mc_close_bias and re.match(r"^(開|打開|開啟|open|launch|play)\b", best, re.I):
        return raw, None
    intent = apply_verb_kind_limits(route(best, registry), registry)
    if not _usable(intent.kind):
        return raw, None
    return best, f"ASR 模糊匹配（{score:.0f}%）：{raw!r} → {best!r}"
