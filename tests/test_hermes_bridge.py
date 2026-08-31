"""Unit checks for hermes_bridge parsers (no WSL required)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.hermes_bridge import (  # noqa: E402
    HermesReply,
    chat,
    parse_hermes_output,
    reset_session,
    spoken_stub,
    strip_heartbeat,
)


def test_strip_heartbeat():
    assert "你好" in strip_heartbeat("你好 ⟦JV⟧")
    assert "⟦JV⟧" not in strip_heartbeat("你好 ⟦JV⟧")
    assert "[JV]" not in strip_heartbeat("hi [JV]")


def test_spoken_stub_drops_cred_and_url():
    text = (
        "答案在此。第二句。\n\n"
        "可信度：82%\n計算：A=90\n"
        "依據：https://example.com/a\n"
        "⟦JV⟧"
    )
    stub = spoken_stub(text)
    # CJK body without SPEAK: → empty (mouth English-only)
    assert stub == ""
    assert "可信度" not in stub
    assert "http" not in stub


def test_split_speak_footer():
    from jarvis.hermes_bridge import split_speak_footer

    cap, sp = split_speak_footer(
        "指令已阻擋，沒有刪除任何東西。\nSPEAK: Blocked, nothing deleted."
    )
    assert "阻擋" in cap
    assert "SPEAK" not in cap
    assert sp == "Blocked, nothing deleted."

    # last SPEAK wins; earlier stripped
    cap2, sp2 = split_speak_footer(
        "你好\nSPEAK: First take.\n更多說明\nSPEAK: Final take."
    )
    assert "First take" not in cap2
    assert "SPEAK" not in cap2
    assert "更多" in cap2
    assert sp2 == "Final take."

    cap3, sp3 = split_speak_footer("只有繁中，無 footer")
    assert "繁中" in cap3
    assert sp3 == ""

    _, sp4 = split_speak_footer("ok\nSPEAK: 含中文 bad")
    assert sp4 == ""


def test_parse_with_speak_footer():
    raw = """好的，已完成。

SPEAK: All done.

session_id: 20260807_100000_abc
"""
    r = parse_hermes_output(raw)
    assert r.ok
    assert "已完成" in r.caption
    assert "SPEAK" not in r.caption
    assert r.spoken == "All done."
    assert r.session_id == "20260807_100000_abc"


def test_pick_spoken_line_prefers_speak():
    from jarvis.shell_app import _pick_spoken_line

    lines = [
        "[route] unknown | x",
        "[caption] 繁中說明很長",
        "[speak] Short English ok.",
        "[ok] ignored-if-speak-present",
    ]
    assert _pick_spoken_line(lines) == "Short English ok."
    assert _pick_spoken_line(["[caption] 只有字幕"]) is None
    assert _pick_spoken_line(["[ok] Hands done"]) == "Hands done"
    assert _pick_spoken_line(["[fail] boom"]) == "boom"


def test_parse_hermes_quiet_output():
    raw = """Query: ping
pong 測試 ⟦JV⟧

Resume this session with:
  hermes --resume 20260806_151708_357b7d

Session:        20260806_151708_357b7d
Duration:       4s
"""
    r = parse_hermes_output(raw)
    assert r.ok
    assert "pong" in r.caption
    assert "⟦JV⟧" not in r.caption
    assert r.session_id == "20260806_151708_357b7d"


def test_parse_hermes_quiet_session_id_footer():
    """Current Hermes -Q prints lowercase session_id: (not Session:)."""
    raw = """HI

session_id: 20260806_174231_617616
"""
    r = parse_hermes_output(raw)
    assert r.ok
    assert r.caption.strip() == "HI"
    assert r.session_id == "20260806_174231_617616"
    assert "session_id" not in r.caption.lower()


def test_chat_dry_run():
    reset_session()
    r = chat("hello", dry_run=True)
    assert r.ok
    assert "dry-run" in r.caption
    assert "hermes chat" in r.raw
    assert "--resume" not in r.raw


def test_chat_dry_run_resume_after_touch():
    from jarvis.hermes_bridge import _touch_session, _build_inner_bash

    reset_session()
    _touch_session("20260806_174231_617616")
    r = chat("hello", dry_run=True)
    assert "--resume" in r.raw
    assert "20260806_174231_617616" in r.raw
    cmd = _build_inner_bash("x", resume="abc")
    assert "--resume" in cmd and "abc" in cmd


def test_chat_dry_run_with_image_flag():
    reset_session()
    from jarvis.hermes_bridge import _build_inner_bash, windows_to_wsl_path
    from pathlib import Path
    import tempfile

    wsl = windows_to_wsl_path(r"C:\HermesSandbox\_inbox\x.png")
    assert wsl.startswith("/mnt/c/")
    assert wsl.endswith("/HermesSandbox/_inbox/x.png")
    cmd = _build_inner_bash("見圖未", resume=None, image_wsl=wsl)
    assert "--image" in cmd
    assert "/mnt/c/" in cmd

    # dry-run labels API+image primary path
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
        tmp = f.name
    try:
        r = chat("見圖", image_path=tmp, dry_run=True)
        assert "api-runs+image" in r.caption
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_build_runs_input_multimodal():
    from pathlib import Path
    import tempfile

    from jarvis.hermes_bridge import build_runs_input, image_to_data_url

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
        tmp = Path(f.name)
    try:
        plain = build_runs_input("hi")
        assert plain == "hi"
        mm = build_runs_input("see", image_path=tmp)
        assert isinstance(mm, list)
        assert mm[0]["role"] == "user"
        parts = mm[0]["content"]
        assert parts[0]["type"] == "text" and parts[0]["text"] == "see"
        assert parts[1]["type"] == "image_url"
        url = parts[1]["image_url"]["url"]
        assert url.startswith("data:image/png;base64,")
        assert image_to_data_url(tmp).startswith("data:image/png;base64,")
    finally:
        tmp.unlink(missing_ok=True)


def test_settings_hermes_default_off():
    from jarvis.settings import Settings

    assert Settings().hermes_enabled is False
    assert Settings().hermes_trusted is False


def test_format_approval_prompt_nested():
    from jarvis.hermes_bridge import _format_approval_prompt

    p = _format_approval_prompt(
        {
            "event": "approval.request",
            "data": {"command": "rm -rf /tmp/x", "description": "delete"},
        }
    )
    assert "rm -rf" in p
    assert "delete" in p
    assert "批准今次" in p


def test_consume_sse_yes_posts_once():
    """Yes → POST choice=once; then run.completed text."""
    import io
    import json
    from unittest import mock

    import jarvis.hermes_bridge as hb

    events = [
        {
            "event": "approval.request",
            "command": "echo danger",
            "description": "test gate",
        },
        {"event": "message.delta", "delta": "DONE_"},
        {"event": "message.delta", "delta": "OK"},
        {"event": "run.completed", "output": "DONE_OK"},
    ]
    sse_bytes = b"".join(
        f"data: {json.dumps(e)}\n\n".encode("utf-8") for e in events
    )

    class FakeResp:
        def __init__(self, raw: bytes):
            self._buf = io.BytesIO(raw)

        def readline(self):
            return self._buf.readline()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    posted: list[dict] = []

    def fake_api(method, path, body=None, timeout=30.0):
        posted.append({"method": method, "path": path, "body": body})
        return 200, "{}"

    with (
        mock.patch.object(
            hb.urllib.request, "urlopen", lambda *a, **k: FakeResp(sse_bytes)
        ),
        mock.patch.object(hb, "load_or_create_api_key", lambda: "k" * 20),
        mock.patch.object(hb, "_api_request", fake_api),
    ):
        text, err, _ = hb._consume_run_sse(
            "run-1", ask_approve=lambda _p: True, timeout_sec=30.0
        )
    assert not err
    assert text == "DONE_OK"  # completed replaces deltas (no DONE_OKDONE_OK)
    assert any(
        p["path"].endswith("/approval") and p["body"] == {"choice": "once"}
        for p in posted
    )


def test_dedupe_exact_echo():
    from jarvis.hermes_bridge import _dedupe_exact_echo

    s = "Command was blocked — permission denied, so nothing was deleted."
    assert _dedupe_exact_echo(s + s) == s
    assert _dedupe_exact_echo("hello") == "hello"


def test_consume_sse_no_posts_deny():
    import io
    import json
    from unittest import mock

    import jarvis.hermes_bridge as hb

    events = [
        {"event": "approval.request", "command": "rm x"},
        {"event": "run.failed", "error": "denied by user"},
    ]
    sse_bytes = b"".join(
        f"data: {json.dumps(e)}\n\n".encode("utf-8") for e in events
    )

    class FakeResp:
        def __init__(self, raw: bytes):
            self._buf = io.BytesIO(raw)

        def readline(self):
            return self._buf.readline()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    posted: list[dict] = []

    def fake_api(method, path, body=None, timeout=30.0):
        posted.append({"method": method, "path": path, "body": body})
        return 200, "{}"

    with (
        mock.patch.object(
            hb.urllib.request, "urlopen", lambda *a, **k: FakeResp(sse_bytes)
        ),
        mock.patch.object(hb, "load_or_create_api_key", lambda: "k" * 20),
        mock.patch.object(hb, "_api_request", fake_api),
    ):
        text, err, _ = hb._consume_run_sse(
            "run-2", ask_approve=lambda _p: False, timeout_sec=30.0
        )
    assert any(
        p["body"] == {"choice": "deny"} for p in posted if p.get("body")
    )
    assert err and "denied" in err.lower()


def test_chat_api_down_falls_back_to_cli():
    """ensure_api fails → CLI path used; no yolo."""
    from unittest import mock

    import jarvis.hermes_bridge as hb

    reset_session()

    def fake_cli(text, *, resume, image_wsl, timeout_sec):
        return HermesReply(
            True, "cli-ok", "cli-ok", "raw-cli", resume or "sid-cli"
        )

    with (
        mock.patch.object(
            hb, "ensure_api_server", lambda **k: (False, "down")
        ),
        mock.patch.object(hb, "_chat_via_cli", fake_cli),
    ):
        r = chat("ping", ask_approve=lambda _p: True)
    assert r.ok
    assert "cli-ok" in r.caption
    assert "API 失敗" in (r.raw or "")
    assert "yolo" not in (r.raw or "").lower()


def test_chat_dry_run_api_mode_label():
    reset_session()
    r = chat("hello", dry_run=True)
    assert "api-runs" in r.caption


def test_ensure_api_recycles_wrong_key_port():
    """Port up + 401 → kill + start path (mocked)."""
    from unittest import mock

    import jarvis.hermes_bridge as hb

    calls = {"kill": 0, "popen": 0}

    def fake_auth():
        # first call (existing port): fail; after kill+listen: ok
        if calls["kill"] == 0:
            return False, "API key 唔夾"
        return True, "ok"

    class FakeProc:
        def poll(self):
            return None

        @property
        def stdout(self):
            return None

        def terminate(self):
            return None

    def fake_popen(*a, **k):
        calls["popen"] += 1
        calls["argv"] = list(a[0] if a else k.get("args") or [])
        return FakeProc()

    listen_state = {"n": 0}

    def fake_listen(host, port):
        listen_state["n"] += 1
        # 1st: occupied; after kill: free then up
        if calls["kill"] == 0:
            return True
        return calls["popen"] > 0

    def fake_kill():
        calls["kill"] += 1

    with (
        mock.patch.object(hb, "_port_listening", fake_listen),
        mock.patch.object(hb, "_api_auth_ok", fake_auth),
        mock.patch.object(hb, "_kill_api_port", fake_kill),
        mock.patch.object(hb.subprocess, "Popen", fake_popen),
        mock.patch.object(hb, "load_or_create_api_key", lambda: "k" * 20),
    ):
        ok, msg = hb.ensure_api_server(wait_sec=2.0)
    assert calls["kill"] >= 1
    assert calls["popen"] >= 1
    assert "wsl" not in " ".join(str(x) for x in calls.get("argv") or []).lower()
    assert "hermes_cli.main" in " ".join(str(x) for x in calls.get("argv") or [])
    assert ok
    assert "API" in msg
