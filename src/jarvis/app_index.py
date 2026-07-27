"""Installed-app name index: spelling fuzzy + Jyutping (粵拼) match."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from jarvis.config import Registry

_HAN = re.compile(r"[\u4e00-\u9fff]")
_TONE = re.compile(r"[0-9]")
_NON_ALPHA = re.compile(r"[^a-z]+")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_WORD = re.compile(r"[a-z0-9\u4e00-\u9fff]+")
# 開／關 後目標（畀 ASR 改寫）
_VERB_TARGET = re.compile(
    r"^("
    r"再開|另開|多開|打開|開啟|啟動|關閉|關掉|關上|重開|重啟|"
    r"關|閂|開|"
    r"close|quit|kill|open|launch|start|play|restart"
    r")\s+(.+)$",
    re.I,
)
_CLOSE_VERBS = frozenset(
    {
        "關閉",
        "關掉",
        "關上",
        "關",
        "閂",
        "close",
        "quit",
        "kill",
    }
)
_RESTART_VERBS = frozenset({"重開", "重啟", "restart", "reboot", "重新開", "重新開啟", "重新打開"})


@dataclass(frozen=True)
class AppEntry:
    """One matchable installed / profile app name."""

    label: str
    norm: str
    jyut: str  # tone-stripped compact, e.g. dongonzunggun


_INDEX_CACHE: list[AppEntry] | None = None
_INDEX_TS = 0.0
_INDEX_TTL = 300.0
_INDEX_SIG = ""


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").lower())


def _latin_skeleton(s: str) -> str:
    """Keep only ascii letters/digits for mixed STT noise (e.g. what石)."""
    return _NON_ALNUM.sub("", (s or "").lower())


def _jyutping_compact(text: str) -> str:
    """Han → tone-stripped jyutping letters; ASCII letters kept."""
    if not text or not _HAN.search(text):
        return ""
    try:
        import ToJyutping
    except ImportError:
        return ""
    parts: list[str] = []
    try:
        pairs = ToJyutping.get_jyutping_list(text)
    except Exception:
        return ""
    for ch, jp in pairs:
        if jp and jp not in ("…", "[…]"):
            parts.append(_TONE.sub("", jp.lower()))
        elif ch.isascii() and ch.isalnum():
            parts.append(ch.lower())
    return "".join(parts)


def _query_jyut_key(query: str) -> str:
    """Query as jyutping key: Han→jyut, or latin treated as romanization."""
    q = (query or "").strip()
    if not q:
        return ""
    if _HAN.search(q):
        return _jyutping_compact(q)
    # dong2 on3 / dong-on → dongon
    return _NON_ALPHA.sub("", q.lower())


def spelling_score(query: str, name: str) -> float:
    """Latin/spacing near-match (whatapp↔whatsapp)."""
    q, n = _norm(query), _norm(name)
    if not q or not n:
        return 0.0
    if q == n:
        return 100.0
    if q in n or n in q:
        return 80.0 + min(len(q), 10)
    q_toks = set(re.findall(r"[a-z0-9\u4e00-\u9fff]+", query.lower()))
    n_toks = set(re.findall(r"[a-z0-9\u4e00-\u9fff]+", name.lower()))
    if q_toks and q_toks <= n_toks:
        return 75.0 + min(len(q), 10)
    if min(len(q), len(n)) >= 4:
        ratio = SequenceMatcher(None, q, n).ratio()
        if ratio >= 0.86:
            return 70.0 + 25.0 * (ratio - 0.86) / 0.14
    # mixed CJK noise after latin stem: what石 / whata下
    ql, nl = _latin_skeleton(query), _latin_skeleton(name)
    if ql and nl and ql != q:
        if ql == nl:
            return 95.0
        if ql in nl or nl in ql:
            return 78.0 + min(len(ql), 10)
        if min(len(ql), len(nl)) >= 3:
            ratio = SequenceMatcher(None, ql, nl).ratio()
            if ratio >= 0.84:
                return 66.0 + 24.0 * (ratio - 0.84) / 0.16
    return 0.0


def jyutping_pair_score(query: str, name: str) -> float:
    """粵拼／近音：漢字或拼音串對 label。"""
    jq = _query_jyut_key(query)
    jn = _jyutping_compact(name) if _HAN.search(name or "") else ""
    if not jq or not jn:
        # latin query vs latin name already handled by spelling; jyut of English empty
        return 0.0
    if len(jq) < 3:
        return 0.0
    if jq == jn:
        return 98.0
    if len(jq) >= 4 and (jq in jn or jn in jq):
        return 86.0 + min(len(jq), 8)
    if min(len(jq), len(jn)) >= 4:
        ratio = SequenceMatcher(None, jq, jn).ratio()
        if ratio >= 0.86:
            return 72.0 + 20.0 * (ratio - 0.86) / 0.14
    return 0.0


def pair_score(query: str, name: str) -> float:
    """Best of spelling + jyutping."""
    return max(spelling_score(query, name), jyutping_pair_score(query, name))


def _profile_labels(registry: Registry) -> list[str]:
    out: list[str] = []
    for p in registry.profiles.values():
        if not p.enabled:
            continue
        out.append(p.display_name)
        out.extend(p.names)
        out.extend(p.locale_hints)
    out.extend(registry.name_aliases.keys())
    return out


def _build_entries(labels: list[str]) -> list[AppEntry]:
    seen: set[str] = set()
    entries: list[AppEntry] = []
    for label in labels:
        label = (label or "").strip()
        if len(label) < 2:
            continue
        key = _norm(label)
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            AppEntry(label=label, norm=key, jyut=_jyutping_compact(label))
        )
    return entries


def get_app_index(registry: Registry | None = None, *, force: bool = False) -> list[AppEntry]:
    """
    Cached index of installed app labels (+ profiles).

    Built from Get-StartApps / Start Menu / Desktop stems / profile names.
    """
    global _INDEX_CACHE, _INDEX_TS, _INDEX_SIG
    from jarvis.discover import iter_installed_labels

    labels = list(iter_installed_labels())
    if registry is not None:
        labels.extend(_profile_labels(registry))
    sig = str(len(labels))
    now = time.time()
    if (
        not force
        and _INDEX_CACHE is not None
        and (now - _INDEX_TS) < _INDEX_TTL
        and sig == _INDEX_SIG
    ):
        return _INDEX_CACHE
    _INDEX_CACHE = _build_entries(labels)
    _INDEX_TS = now
    _INDEX_SIG = sig
    return _INDEX_CACHE


def clear_app_index() -> None:
    """Test helper."""
    global _INDEX_CACHE, _INDEX_TS, _INDEX_SIG
    _INDEX_CACHE = None
    _INDEX_TS = 0.0
    _INDEX_SIG = ""


def best_label_match(
    query: str,
    registry: Registry | None = None,
    *,
    min_score: float = 72.0,
    entries: list[AppEntry] | None = None,
) -> tuple[str, float] | None:
    """Return (label, score) best match against app index, or None."""
    q = (query or "").strip()
    if len(q) < 2:
        return None
    pool = entries if entries is not None else get_app_index(registry)
    best: tuple[str, float] | None = None
    for e in pool:
        if not _label_plausible_for_query(q, e.label):
            continue
        sc = pair_score(q, e.label)
        if sc < min_score:
            continue
        if best is None or sc > best[1]:
            best = (e.label, sc)
    return best


def _label_plausible_for_query(query: str, label: str) -> bool:
    """Block sentence-like labels for short app targets."""
    q_words = _WORD.findall(query.lower())
    l_words = _WORD.findall((label or "").lower())
    if not l_words:
        return False
    # query usually short app token; skip long sentence labels from StartApps
    if len(q_words) <= 2 and len("".join(q_words)) <= 10:
        if len(l_words) >= 5:
            return False
        if len(label) >= 28:
            return False
    return True


@dataclass(frozen=True)
class CommandSlots:
    """Verb + app query slots from a short command utterance."""

    verb: str
    app_query: str
    verb_kind: str  # open | close | restart


def parse_command_slots(text: str) -> CommandSlots | None:
    """
    Split「動詞 + 目標」into slots.

    Does not resolve the app — only structural parse.
    """
    t = (text or "").strip()
    m = _VERB_TARGET.match(t)
    if not m:
        return None
    verb = m.group(1)
    query = m.group(2).strip()
    if not query:
        return None
    vlow = verb.lower()
    if verb in _CLOSE_VERBS or vlow in {x.lower() for x in _CLOSE_VERBS}:
        kind = "close"
    elif verb in _RESTART_VERBS or vlow in {x.lower() for x in _RESTART_VERBS}:
        kind = "restart"
    else:
        kind = "open"
    return CommandSlots(verb=verb, app_query=query, verb_kind=kind)


def apply_learned_alias(
    text: str,
    *,
    memory_path: Path | None = None,
) -> tuple[str, str | None]:
    """Replace app_query (or bare token) using learned stt_aliases."""
    from jarvis import memory as mem

    t = (text or "").strip()
    if not t:
        return t, None

    slots = parse_command_slots(t)
    if slots:
        prefix, core = _split_force_new_prefix(slots.app_query)
        hit = mem.get_stt_alias(core, memory_path)
        if hit and _norm(hit) != _norm(core):
            new_q = f"{prefix} {hit}".strip() if prefix else hit
            new = f"{slots.verb} {new_q}"
            return new, f"alias：{core!r} → {hit!r}"
        return t, None

    # bare token
    hit = mem.get_stt_alias(t, memory_path)
    if hit and _norm(hit) != _norm(t):
        return hit, f"alias：{t!r} → {hit!r}"
    return t, None


def rewrite_command_target(
    text: str,
    registry: Registry | None = None,
    *,
    memory_path: Path | None = None,
    learn: bool = True,
) -> tuple[str, str | None]:
    """
    If text is「開／關 X」, resolve X via alias then fuzzy／粵拼 app index.

    On successful fuzzy match, optionally learn alias (garbled → label).
    """
    from jarvis import memory as mem

    t = (text or "").strip()
    slots = parse_command_slots(t)
    if not slots:
        return t, None

    verb, target = slots.verb, slots.app_query
    # 唔好食掉「new window Chrome」→ 只對最後 app 段做近匹配
    prefix, core = _split_force_new_prefix(target)
    if not core:
        return t, None

    aliased = mem.get_stt_alias(core, memory_path)
    if aliased and _norm(aliased) != _norm(core):
        new_target = f"{prefix} {aliased}".strip() if prefix else aliased
        new = f"{verb} {new_target}"
        return new, f"alias：{core!r} → {aliased!r}"

    hit = best_label_match(core, registry)
    if not hit:
        return t, None
    label, score = hit
    if _norm(label) == _norm(core):
        return t, None
    if learn:
        mem.learn_stt_alias(core, label, memory_path)
    new_target = f"{prefix} {label}".strip() if prefix else label
    new = f"{verb} {new_target}"
    return new, f"app 近匹配（{score:.0f}%）：{core!r} → {label!r}"


def _split_force_new_prefix(target: str) -> tuple[str, str]:
    """Return (modifier_prefix, remainder) for force_new／上次 phrases."""
    try:
        from jarvis.router import _FORCE_NEW_MODIFIERS, _LAST_MODIFIERS
    except ImportError:
        return "", target
    mods = sorted(
        {*(m.lower() for m in _FORCE_NEW_MODIFIERS), *(m.lower() for m in _LAST_MODIFIERS)},
        key=len,
        reverse=True,
    )
    rest = target.strip()
    kept: list[str] = []
    changed = True
    while changed and rest:
        changed = False
        lower = rest.lower()
        for mod in mods:
            if lower == mod or lower.startswith(mod + " "):
                kept.append(rest[: len(mod)].strip())
                rest = rest[len(mod) :].strip()
                changed = True
                break
    return " ".join(x for x in kept if x), rest
