"""Repair noisy SenseVoice text into Jarvis command shapes."""

from __future__ import annotations

import re

from jarvis.config import Registry
from jarvis.router import apply_verb_kind_limits, normalize_utterance, route

# 口語／STT 常見誤聽 → 正規指令片段（最長優先）
# 英文專名好短，SenseVoice 成日聽錯——唔關口音
_CONFUSIONS: tuple[tuple[str, str], ...] = (
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

_FILLER = re.compile(
    r"(測試|测试|试下|試下|嗯+|呃+|嗱|嗱嗱|呢個|那个|那個|就是|然後|然后)"
)
_TRAIL_PARTICLES = re.compile(r"[嘅的了啦呀哦喔咧咯唓]+")
_OPEN_PREFIX = re.compile(
    r"^(開|打开|打開|開啟|啟動|open|launch|start|play)\s+(.+)$",
    re.I,
)

# 目標詞單獨誤聽（開 X 嘅 X）
_TARGET_ALIASES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(caa|ka+|kaa|c\s*aa|sea|see|si+|串|死)$", re.I), "CS"),
    (re.compile(r"^(cs2|c\s*s\s*2)$", re.I), "CS2"),
    (re.compile(r"^(cura|cur[ao]?|curso?r?|kura|kursor)$", re.I), "Cursor"),
    (re.compile(r"^(chrom[eo]?|guge|google)$", re.I), "Chrome"),
    (re.compile(r"^(mc|mine.?craft|我的世界)$", re.I), "Minecraft"),
)


def _usable(intent_kind: str) -> bool:
    return intent_kind in ("open_profile", "restore_battlefield", "query")


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
    verbs = ["開", "打開", "開啟", "啟動", "open", "launch", "play", "還原", "restore"]
    names = _all_names(registry)
    out: list[str] = []
    for v in verbs:
        for n in names:
            out.append(f"{v} {n}")
            out.append(f"{n} {v}")
    out.extend(registry.restore_phrases)
    return out


def _fix_open_target(text: str, registry: Registry) -> str | None:
    """If『開 xxx』and xxx looks like a known app, rebuild canonical command."""
    m = _OPEN_PREFIX.match(text.strip())
    if not m:
        return None
    target = m.group(2).strip()
    target = _TRAIL_PARTICLES.sub("", target).strip()
    if not target:
        return None

    for pat, canon in _TARGET_ALIASES:
        if pat.match(target):
            return f"開 {canon}"

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
    return f"開 {best}"


def repair_asr_text(text: str, registry: Registry) -> tuple[str, str | None]:
    """
    Return (text_for_router, note_or_None).

    note is set when repair changed the string.
    """
    raw = normalize_utterance(text)
    if not raw:
        return raw, None

    intent = apply_verb_kind_limits(route(raw, registry), registry)
    if _usable(intent.kind):
        return raw, None

    t = raw
    for bad, good in _CONFUSIONS:
        if bad.lower() in t.lower() or bad in t:
            t = re.sub(re.escape(bad), good, t, flags=re.I)
    t = _FILLER.sub("", t)
    t = _TRAIL_PARTICLES.sub("", t)
    t = normalize_utterance(t)

    rebuilt = _fix_open_target(t, registry)
    if rebuilt:
        t = rebuilt

    intent = apply_verb_kind_limits(route(t, registry), registry)
    if _usable(intent.kind) and t != raw:
        return t, f"ASR 修正：{raw!r} → {t!r}"
    if _usable(intent.kind):
        return t, None

    # Fuzzy against whitelist command templates (rapidfuzz comes with funasr stack)
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        return raw, None

    templates = _command_templates(registry)
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
    intent = apply_verb_kind_limits(route(best, registry), registry)
    if not _usable(intent.kind):
        return raw, None
    return best, f"ASR 模糊匹配（{score:.0f}%）：{raw!r} → {best!r}"
