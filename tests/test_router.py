"""Router self-checks — run: python -m pytest tests/test_router.py -q"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.config import load_registry
from jarvis.router import apply_verb_kind_limits, route


def _reg():
    return load_registry(ROOT / "config" / "profiles.example.yaml")


def test_open_cs2():
    r = _reg()
    i = apply_verb_kind_limits(route("open CS2", r), r)
    assert i.kind == "open_profile"
    assert i.profile_id == "cs2"


def test_open_mc_alias():
    r = _reg()
    i = route("開 Minecraft", r)
    assert i.kind == "open_profile"
    assert i.profile_id == "_pending_default_mc"


def test_play_cursor_refused():
    r = _reg()
    i = apply_verb_kind_limits(route("play Cursor", r), r)
    assert i.kind == "refuse"


def test_unknown_refused():
    r = _reg()
    i = route("open not-registered-app-xyz", r)
    assert i.kind == "refuse"


def test_restore():
    r = _reg()
    i = route("還原戰場", r)
    assert i.kind == "restore_battlefield"


def test_inverted():
    r = _reg()
    i = apply_verb_kind_limits(route("CS open", r), r)
    assert i.kind == "open_profile"
    assert i.profile_id == "cs2"


def test_chrome_restore_phrase():
    """「Chrome 還原」= open browser_session，唔係還原戰場。"""
    r = _reg()
    i = apply_verb_kind_limits(route("Chrome 還原", r), r)
    assert i.kind == "open_profile"
    assert i.profile_id == "browser-main"


def test_restore_non_browser_refused():
    r = _reg()
    i = apply_verb_kind_limits(route("還原 Cursor", r), r)
    assert i.kind == "refuse"


def test_design_verbs_and_stt_typos():
    r = _reg()
    assert apply_verb_kind_limits(route("唔該開 Cursor", r), r).profile_id == "cursor"
    assert apply_verb_kind_limits(route("please open Cursor", r), r).profile_id == "cursor"
    assert apply_verb_kind_limits(route("lanuch CS2", r), r).profile_id == "cs2"
    assert apply_verb_kind_limits(route("swith on CS2", r), r).profile_id == "cs2"
    assert apply_verb_kind_limits(route("開返 Chrome", r), r).profile_id == "browser-main"
    assert apply_verb_kind_limits(route("fire up CS2", r), r).profile_id == "cs2"
    assert apply_verb_kind_limits(route("bring up Cursor", r), r).profile_id == "cursor"
    assert apply_verb_kind_limits(route("resume Chrome", r), r).profile_id == "browser-main"
    assert apply_verb_kind_limits(route("restore tabs", r), r).profile_id == "browser-main"
    assert route("還原上次戰場", r).kind == "restore_battlefield"
    assert route("restore desktop", r).kind == "restore_battlefield"
    # resume last still battlefield, not browser
    assert route("resume last", r).kind == "restore_battlefield"


def test_query_caption_only():
    r = _reg()
    i = route("幫我查 CS2 點樣開", r)
    assert i.kind == "query"


def test_sensevoice_simplified_open():
    """SenseVoice 常出簡體「开」；要當「開」用。"""
    r = _reg()
    i = apply_verb_kind_limits(route("开 cs 。", r), r)
    assert i.kind == "open_profile"
    assert i.profile_id == "cs2"
    i2 = apply_verb_kind_limits(route("打开 Cursor", r), r)
    assert i2.profile_id == "cursor"


def test_asr_repair_noisy():
    from jarvis.asr_fix import repair_asr_text

    r = _reg()
    fixed, note = repair_asr_text("測試开线嘅。", r)
    assert note is not None
    i = apply_verb_kind_limits(route(fixed, r), r)
    assert i.kind == "open_profile"
    assert i.profile_id == "cs2"


def test_asr_repair_english_mishear():
    """短英文專名 STT 誤聽：caa→CS、cura→Cursor。"""
    from jarvis.asr_fix import repair_asr_text

    r = _reg()
    for raw, pid in (("开 caa。", "cs2"), ("开 cura。", "cursor"), ("開 cura", "cursor")):
        fixed, note = repair_asr_text(raw, r)
        assert note is not None, raw
        i = apply_verb_kind_limits(route(fixed, r), r)
        assert i.kind == "open_profile", raw
        assert i.profile_id == pid, (raw, fixed, i)


def test_force_new_modifier():
    r = _reg()
    # 量詞「個」唔算 new
    i0 = apply_verb_kind_limits(route("開個 browser", r), r)
    assert i0.profile_id == "browser-main"
    assert not i0.force_new
    # new / 再開
    i1 = apply_verb_kind_limits(route("開 new browser", r), r)
    assert i1.profile_id == "browser-main" and i1.force_new
    i2 = apply_verb_kind_limits(route("开個 new Cursor", r), r)
    assert i2.profile_id == "cursor" and i2.force_new
    i3 = apply_verb_kind_limits(route("再開 CS2", r), r)
    assert i3.profile_id == "cs2" and i3.force_new
    i4 = apply_verb_kind_limits(route("開 new window Chrome", r), r)
    assert i4.profile_id == "browser-main" and i4.force_new


def test_asr_repair_force_new():
    """STT 誤聽 new window／再開；修完仍帶 force_new。"""
    from jarvis.asr_repair import _FILLER, repair_asr_text

    r = _reg()
    assert _FILLER.search("new") is None
    assert _FILLER.search("開 new browser") is None
    for raw, pid in (
        ("在開 Cursor", "cursor"),
        ("開 knew window Chrome", "browser-main"),
        ("開 new win browser", "browser-main"),
        ("再開 cura", "cursor"),
    ):
        fixed, note = repair_asr_text(raw, r)
        assert note is not None, raw
        i = apply_verb_kind_limits(route(fixed, r), r)
        assert i.kind == "open_profile", (raw, fixed)
        assert i.profile_id == pid, (raw, fixed, i)
        assert i.force_new, (raw, fixed, i)


def test_asr_browser_chutlei():
    """ear: 开个新包耍／包沙／包洒出嚟 → browser + force_new。"""
    from jarvis.asr_repair import repair_asr_text

    r = _reg()
    for raw in (
        "开个新包耍出嚟。",
        "开个新包沙出嚟。",
        "开个新包洒出嚟。",
    ):
        fixed, note = repair_asr_text(raw, r)
        assert note is not None, (raw, fixed, note)
        i = apply_verb_kind_limits(route(fixed, r), r)
        assert i.kind == "open_profile", (raw, fixed)
        assert i.profile_id == "browser-main", (raw, fixed)
        assert i.force_new, (raw, fixed)
        assert "出嚟" not in fixed


def test_system_power_route():
    r = _reg()
    for raw, action in (("關機", "shutdown"), ("睡眠", "sleep"), ("shutdown", "shutdown"), ("sleep", "sleep")):
        i = route(raw, r)
        assert i.kind == "system_power", raw
        assert i.power_action == action, raw
    # 唔好誤殺「關」開頭開 app（若有）
    i_open = apply_verb_kind_limits(route("開 Chrome", r), r)
    assert i_open.kind == "open_profile"


def test_system_power_needs_confirm():
    from jarvis.hands import system_power

    refused = system_power("shutdown", ask_confirm=None)
    assert not refused.ok
    cancelled = system_power("sleep", ask_confirm=lambda _p: False)
    assert not cancelled.ok
    assert "取消" in cancelled.message


def test_discover_score_helpers():
    from jarvis.discover import _score_name

    assert _score_name("Cursor", "Cursor") >= 100
    assert _score_name("chrome", "Google Chrome") >= 80


if __name__ == "__main__":
    # ponytail: no pytest required for a smoke run
    for fn in (
        test_open_cs2,
        test_open_mc_alias,
        test_play_cursor_refused,
        test_unknown_refused,
        test_restore,
        test_inverted,
        test_chrome_restore_phrase,
        test_restore_non_browser_refused,
        test_design_verbs_and_stt_typos,
        test_query_caption_only,
        test_sensevoice_simplified_open,
        test_asr_repair_noisy,
        test_asr_repair_english_mishear,
        test_force_new_modifier,
        test_asr_repair_force_new,
        test_asr_browser_chutlei,
        test_system_power_route,
        test_system_power_needs_confirm,
        test_discover_score_helpers,
    ):
        fn()
        print("ok", fn.__name__)
    print("all passed")
