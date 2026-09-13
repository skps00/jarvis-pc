"""Thin bridge: jarvis → Windows Hermes (same instance as Discord gateway).

Primary: local Hermes API Server ``127.0.0.1:8642`` Runs + SSE approval
(on the Windows ``hermes gateway`` that also hosts Discord).
Fallback: ``hermes chat -q`` via ``%LOCALAPPDATA%\\hermes`` venv (not WSL).
Never ``--yolo``. Hands (open/close/power) stay in engine — not here.
"""

from __future__ import annotations

import base64
import json
import os
import re
import secrets
import shlex
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# ponytail: one shared session window; upgrade to per-user store if multi-UI
_SESSION_ID: str | None = None
_SESSION_TS: float = 0.0
_SESSION_TTL_SEC = 600.0  # G5: 10 min after wake/use

_HEARTBEAT_RE = re.compile(r"(?:⟦JV⟧|\[JV\])")
_CRED_BLOCK_RE = re.compile(
    r"(?ms)^\s*可信度：.*?(?=^\s*$|\Z)"
)
_URL_RE = re.compile(r"https?://\S+")
_RESUME_RE = re.compile(
    r"hermes\s+--resume\s+(\S+)", re.IGNORECASE
)
_SESSION_LINE_RE = re.compile(
    r"^(?:session_id|Session)\s*:\s*(\S+)",
    re.IGNORECASE | re.MULTILINE,
)
_SPEAK_LINE_RE = re.compile(
    r"(?im)^[ \t]*SPEAK\s*:\s*(.+?)\s*$"
)

_SPEAK_INSTRUCTIONS = (
    "You are Jarvis's backend assistant. Source tag: jarvis. Never request YOLO. "
    "Reply the main answer in Traditional Chinese (繁體中文). "
    "End with exactly one final line: SPEAK: <short English, max ~20 words for TTS>. "
    "Do not put Chinese in the SPEAK line."
)

_SPEAK_QUERY_HINT = (
    "\n\n[Jarvis] Main reply in Traditional Chinese. "
    "End with one line: SPEAK: <short English ≤20 words>"
)

_WSL_PATH_EXPORT = (
    'export PATH="/mnt/c/Program Files/Docker/Docker/resources/bin:'
    '$HOME/bin:$HOME/.local/bin:$PATH"'
)

_SAFE_TOOLSETS_OFF = ("terminal", "browser", "computer_use", "cronjob")
_TRUSTED_TERMINAL_ON = ("terminal",)

API_HOST = "127.0.0.1"
API_PORT = 8642
API_BASE = f"http://{API_HOST}:{API_PORT}"
_API_KEY_PATH = Path.home() / "AppData" / "Roaming" / "Jarvis" / "hermes_api.key"
_JARVIS_SESSION_PREFIX = "jarvis-"
_MAX_IMAGE_BYTES = 12 * 1024 * 1024
_IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}


def _hermes_home() -> Path:
    raw = os.environ.get("HERMES_HOME")
    if raw:
        return Path(raw)
    return Path.home() / "AppData" / "Local" / "hermes"


def _hermes_python() -> Path:
    return _hermes_home() / "hermes-agent" / "venv" / "Scripts" / "python.exe"


def _hermes_env() -> dict[str, str]:
    env = dict(os.environ)
    home = str(_hermes_home())
    env["HERMES_HOME"] = home
    agent = str(_hermes_home() / "hermes-agent")
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = agent if not prev else f"{agent}{os.pathsep}{prev}"
    return env

AskApproveFn = Callable[[str], bool]


@dataclass
class HermesReply:
    """Parsed Hermes response for UI + TTS."""

    ok: bool
    caption: str  # full text minus heartbeat (subtitle / log)
    spoken: str  # short oral stub (CJK → mouth skips anyway)
    raw: str
    session_id: str | None
    error: str = ""


def reset_session() -> None:
    """Drop session continuity (tests / mode change)."""
    global _SESSION_ID, _SESSION_TS
    _SESSION_ID = None
    _SESSION_TS = 0.0


def _active_session() -> str | None:
    global _SESSION_ID, _SESSION_TS
    if not _SESSION_ID:
        return None
    if time.monotonic() - _SESSION_TS > _SESSION_TTL_SEC:
        _SESSION_ID = None
        return None
    return _SESSION_ID


def _touch_session(sid: str | None) -> None:
    global _SESSION_ID, _SESSION_TS
    if sid:
        _SESSION_ID = sid
        _SESSION_TS = time.monotonic()


def strip_heartbeat(text: str) -> str:
    """Remove compliance heartbeat markers."""
    return _HEARTBEAT_RE.sub("", text).strip()


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def split_speak_footer(text: str) -> tuple[str, str]:
    """
    Split Hermes body into (caption, spoken).

    Takes the **last** ``SPEAK:`` line; strips all SPEAK lines from caption.
    Spoken must be non-empty ASCII/English (no CJK) or returns ``\"\"``.
    """
    raw = (text or "").strip()
    if not raw:
        return "", ""
    matches = list(_SPEAK_LINE_RE.finditer(raw))
    spoken = ""
    if matches:
        spoken = matches[-1].group(1).strip()
        # drop every SPEAK line from caption
        caption = _SPEAK_LINE_RE.sub("", raw)
        caption = re.sub(r"\n{3,}", "\n\n", caption).strip()
    else:
        caption = raw
    if not spoken or _has_cjk(spoken):
        spoken = ""
    # trim to ~20 words for TTS
    if spoken:
        words = spoken.split()
        if len(words) > 24:
            spoken = " ".join(words[:20]).rstrip(".,;:") + "."
    return caption, spoken


def spoken_stub(text: str) -> str:
    """ASCII-only short oral fallback when no SPEAK footer (never CJK)."""
    t = strip_heartbeat(text)
    t = _CRED_BLOCK_RE.sub("", t)
    t = _URL_RE.sub("", t)
    t = re.sub(r"\n{2,}", "\n", t).strip()
    # Prefer explicit footer
    _cap, speak = split_speak_footer(t)
    if speak:
        return speak
    if _has_cjk(t):
        return ""
    para = t.split("\n", 1)[0].strip()
    parts = re.split(r"(?<=[.!?])\s*", para)
    parts = [p for p in parts if p.strip()]
    stub = " ".join(parts[:2]).strip() if parts else para
    return stub[:240]


def parse_hermes_output(raw: str) -> HermesReply:
    """Extract final answer + session id from ``hermes chat -Q`` output."""
    text = (raw or "").strip()
    if not text:
        return HermesReply(False, "", "", "", None, error="空回覆")

    sid = None
    m = _RESUME_RE.search(text) or _SESSION_LINE_RE.search(text)
    if m:
        sid = m.group(1).strip().rstrip("`")

    body = text
    low = body.lower()
    cut = len(body)
    for marker in (
        "\nresume this session with:",
        "\nsession:",
        "\nsession_id:",
        "\nduration:",
    ):
        idx = low.find(marker)
        if idx >= 0:
            cut = min(cut, idx)
    body = body[:cut].strip()
    lines = body.splitlines()
    if lines and lines[0].lower().startswith("query:"):
        body = "\n".join(lines[1:]).strip()
    body = re.sub(r"(?m)^Initializing agent\.\.\.\s*$", "", body).strip()
    body = re.sub(r"(?m)^─+\s*$", "", body).strip()
    body = re.sub(
        r"(?ms)^┌─\s*Reasoning\s*─+.*?^└─.*?(?:\n|$)",
        "",
        body,
    ).strip()

    if not body:
        return HermesReply(False, "", "", text, sid, error="無正文")

    cleaned = strip_heartbeat(body)
    caption, spoken = split_speak_footer(cleaned)
    if not spoken:
        spoken = spoken_stub(cleaned)
    if not spoken:
        try:
            from jarvis.brain import translate_to_english_short
            spoken = translate_to_english_short(caption) or ""
        except Exception:
            spoken = ""
    return HermesReply(
        ok=True,
        caption=caption,
        spoken=spoken,
        raw=text,
        session_id=sid,
    )


def _build_inner_bash(
    user_text: str,
    *,
    resume: str | None,
    image_wsl: str | None = None,
) -> str:
    """Shell fragment run inside WSL Ubuntu."""
    # CLI has no separate instructions — append SPEAK hint to query
    q = shlex.quote(user_text + _SPEAK_QUERY_HINT)
    cmd = [
        _WSL_PATH_EXPORT,
        "hermes chat -q " + q + " -Q --max-turns 12 --source jarvis",
    ]
    if image_wsl:
        cmd[-1] += " --image " + shlex.quote(image_wsl)
    if resume:
        cmd[-1] += " --resume " + shlex.quote(resume)
    return "; ".join(cmd)


def windows_to_wsl_path(path: str | Path) -> str:
    """``C:\\foo\\bar.png`` → ``/mnt/c/foo/bar.png``."""
    p = Path(path).resolve()
    s = str(p)
    if len(s) >= 2 and s[1] == ":":
        drive = s[0].lower()
        rest = s[2:].replace("\\", "/")
        if not rest.startswith("/"):
            rest = "/" + rest
        return f"/mnt/{drive}{rest}"
    return s.replace("\\", "/")


def image_to_data_url(path: str | Path) -> str:
    """Encode local image as ``data:image/...;base64,...`` for Runs multimodal."""
    p = Path(path)
    raw = p.read_bytes()
    if len(raw) > _MAX_IMAGE_BYTES:
        raise ValueError(
            f"圖太大（{len(raw) // (1024 * 1024)}MB＞{_MAX_IMAGE_BYTES // (1024 * 1024)}MB）"
        )
    if len(raw) < 32:
        raise ValueError("圖檔太細／可能損毀")
    mime = _IMAGE_MIME.get(p.suffix.lower(), "image/png")
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def build_runs_input(
    text: str, *, image_path: str | Path | None = None
) -> str | list:
    """Plain string or OpenAI-style multimodal user message for ``POST /v1/runs``."""
    if not image_path:
        return text
    data_url = image_to_data_url(image_path)
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]


def save_clipboard_image() -> Path | None:
    """Save clipboard image (or first image file path) into HermesSandbox inbox."""
    from PIL import Image, ImageGrab

    inbox = Path(r"C:\HermesSandbox\_inbox")
    inbox.mkdir(parents=True, exist_ok=True)
    grabbed = ImageGrab.grabclipboard()
    if grabbed is None:
        return None
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = inbox / f"paste_{stamp}.png"
    if isinstance(grabbed, Image.Image):
        grabbed.convert("RGB").save(out, format="PNG")
        return out
    if isinstance(grabbed, list):
        for item in grabbed:
            src = Path(str(item))
            if src.is_file() and src.suffix.lower() in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".gif",
                ".bmp",
            }:
                out.write_bytes(src.read_bytes())
                return out
    return None


def _no_window_flags() -> int:
    """CREATE_NO_WINDOW on Windows; 0 elsewhere."""
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        return int(subprocess.CREATE_NO_WINDOW)
    return 0


def _wsl_bash(inner: str, *, timeout: float = 60.0) -> subprocess.CompletedProcess[str]:
    """Run ``bash -lc`` inside Ubuntu WSL (no console flash)."""
    return subprocess.run(
        ["wsl", "-d", "Ubuntu", "-e", "bash", "-lc", inner],
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
        creationflags=_no_window_flags(),
    )


def docker_available() -> tuple[bool, str]:
    """True if WSL can talk to Docker Desktop engine."""
    try:
        proc = _wsl_bash(
            f"{_WSL_PATH_EXPORT}; docker version --format '{{{{.Server.Version}}}}'",
            timeout=30.0,
        )
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    out = (proc.stdout or "").strip()
    if proc.returncode != 0 or not out:
        err = (proc.stderr or proc.stdout or "docker 失敗").strip()
        return False, err[:200]
    return True, out


def apply_hermes_safe_toolsets() -> tuple[bool, str]:
    """Safe：關 terminal／browser／computer_use／cronjob（api_server＋cli）。"""
    names = " ".join(_SAFE_TOOLSETS_OFF)
    inner = (
        f"{_WSL_PATH_EXPORT}; "
        f"hermes tools disable --platform api_server {names}; "
        f"hermes tools disable --platform cli {names}"
    )
    try:
        proc = _wsl_bash(inner, timeout=60.0)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    msg = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        return False, msg[:300] or f"exit {proc.returncode}"
    return True, "Safe toolsets"


def apply_hermes_trusted_toolsets() -> tuple[bool, str]:
    """Trusted：開 docker terminal（仍無 browser／computer_use／yolo）。"""
    ok_d, dmsg = docker_available()
    if not ok_d:
        return False, f"Docker 未就緒：{dmsg}"
    # keep hard offs, then enable terminal
    off = " ".join(_SAFE_TOOLSETS_OFF)
    on = " ".join(_TRUSTED_TERMINAL_ON)
    inner = (
        f"{_WSL_PATH_EXPORT}; "
        f"hermes tools disable --platform api_server {off}; "
        f"hermes tools disable --platform cli {off}; "
        f"hermes tools enable --platform api_server {on}; "
        f"hermes tools enable --platform cli {on}"
    )
    try:
        proc = _wsl_bash(inner, timeout=60.0)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    msg = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        return False, msg[:300] or f"exit {proc.returncode}"
    return True, f"Trusted terminal（docker {dmsg}）"


def recycle_api_server(*, wait_sec: float = 90.0) -> tuple[bool, str]:
    """Kill :8642 and start gateway again（toolset 變更後要重載）。"""
    _kill_api_port()
    return ensure_api_server(wait_sec=wait_sec)


def _port_listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def load_or_create_api_key() -> str:
    """Bearer key for local Hermes API (≥16 chars). Stored under APPDATA."""
    _API_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _API_KEY_PATH.is_file():
        key = _API_KEY_PATH.read_text(encoding="utf-8").strip()
        if len(key) >= 16:
            return key
    key = "jarvis-" + secrets.token_hex(16)
    _API_KEY_PATH.write_text(key + "\n", encoding="utf-8")
    return key


def _api_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {load_or_create_api_key()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _api_request(
    method: str,
    path: str,
    body: dict | None = None,
    *,
    timeout: float = 30.0,
) -> tuple[int, str]:
    data = None
    headers = _api_headers()
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        return exc.code, err_body
    except Exception as exc:  # noqa: BLE001
        return 599, str(exc)


def _api_auth_ok() -> tuple[bool, str]:
    """True if :8642 accepts our Bearer key (health alone may skip auth)."""
    code, body = _api_request("GET", "/v1/capabilities", timeout=5.0)
    if code == 401:
        return False, "API key 唔夾（埠上 gateway 用咗另一把 key）"
    if code >= 400:
        # some builds may lack capabilities; try health with auth header anyway
        code2, body2 = _api_request("GET", "/health", timeout=5.0)
        if code2 == 401:
            return False, "API key 唔夾"
        if code2 >= 400 and code >= 500:
            return False, f"API probe {code}: {body[:120]}"
        # 404 capabilities but health ok → assume key accepted if not 401
        if code2 < 400:
            return True, "health ok"
        return False, f"API probe {code}: {body[:120]}"
    return True, "ok"


def _kill_api_port() -> None:
    """Free local :8642 (stale / wrong-key listener). Windows: taskkill PID."""
    pids: set[int] = set()
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                ["netstat", "-ano", "-p", "tcp"],
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=_no_window_flags(),
            )
        except OSError:
            out = ""
        needle = f":{API_PORT}"
        for line in out.splitlines():
            u = line.upper()
            if "LISTENING" not in u:
                continue
            if needle not in line:
                continue
            parts = line.split()
            if parts and parts[-1].isdigit():
                pids.add(int(parts[-1]))
        for pid in pids:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    capture_output=True,
                    creationflags=_no_window_flags(),
                    timeout=15,
                )
            except Exception:
                pass
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and _port_listening(API_HOST, API_PORT):
        time.sleep(0.3)


def ensure_api_server(*, wait_sec: float = 90.0) -> tuple[bool, str]:
    """Start Windows Hermes gateway API on :8642 if needed (no console flash)."""
    if _port_listening(API_HOST, API_PORT):
        ok, why = _api_auth_ok()
        if ok:
            return True, f"API 已喺 {API_BASE}"
        _kill_api_port()
        if _port_listening(API_HOST, API_PORT):
            return False, f"{why}；清埠失敗，請手動停 hermes gateway"

    py = _hermes_python()
    if not py.is_file():
        return False, f"搵唔到 Hermes python：{py}"
    try:
        proc = subprocess.Popen(
            [str(py), "-m", "hermes_cli.main", "gateway", "run"],
            cwd=str(_hermes_home()),
            env=_hermes_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=_no_window_flags(),
        )
    except OSError as exc:
        return False, f"啟動 Windows Hermes 失敗：{exc}"

    deadline = time.monotonic() + max(5.0, wait_sec)
    while time.monotonic() < deadline:
        if _port_listening(API_HOST, API_PORT):
            ok, why = _api_auth_ok()
            if ok:
                return True, f"已啟動 API {API_BASE}"
            return False, f"已聽埠但 auth 失敗：{why}"
        if proc.poll() is not None:
            out = ""
            try:
                out = proc.stdout.read() if proc.stdout else ""
            except Exception:
                pass
            return False, f"API 啟動失敗：{(out or '')[-400:] or f'exit {proc.returncode}'}"
        time.sleep(0.5)

    try:
        proc.terminate()
    except Exception:
        pass
    return False, f"逾時等 :{API_PORT}"


def _approval_fields(event: dict) -> tuple[str, str]:
    """Pull command/description from flat or nested SSE payload."""
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    cmd = str(
        event.get("command")
        or data.get("command")
        or event.get("cmd")
        or data.get("cmd")
        or ""
    ).strip()
    desc = str(
        event.get("description")
        or data.get("description")
        or event.get("reason")
        or data.get("reason")
        or ""
    ).strip()
    return cmd, desc


def _format_approval_prompt(event: dict) -> str:
    cmd, desc = _approval_fields(event)
    parts = ["Hermes 要求批准危險操作："]
    if desc:
        parts.append(desc[:400])
    if cmd:
        parts.append(f"指令：\n{cmd[:800]}")
    parts.append("批准今次執行？")
    return "\n\n".join(parts)


def _consume_run_sse(
    run_id: str,
    *,
    ask_approve: AskApproveFn | None,
    timeout_sec: float,
) -> tuple[str, str | None, str]:
    """
    Read SSE until stream closes / timeout.

    Returns (assembled_text, error, last_status_hint).
    Handles approval.request → ask_approve → POST once|deny.
    """
    headers = {
        "Authorization": f"Bearer {load_or_create_api_key()}",
        "Accept": "text/event-stream",
    }
    req = urllib.request.Request(
        f"{API_BASE}/v1/runs/{run_id}/events",
        headers=headers,
        method="GET",
    )
    pieces: list[str] = []
    err: str | None = None
    deadline = time.monotonic() + max(10.0, timeout_sec)
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            while time.monotonic() < deadline:
                raw = resp.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload:
                    continue
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                et = str(event.get("event") or "")
                if et == "message.delta":
                    delta = event.get("delta")
                    if delta:
                        pieces.append(str(delta))
                elif et == "approval.request":
                    prompt = _format_approval_prompt(event)
                    ok = False
                    if ask_approve is not None:
                        try:
                            ok = bool(ask_approve(prompt))
                        except Exception:
                            ok = False
                    choice = "once" if ok else "deny"
                    code, body = _api_request(
                        "POST",
                        f"/v1/runs/{run_id}/approval",
                        {"choice": choice},
                        timeout=30.0,
                    )
                    if code >= 400:
                        err = f"approval POST {code}: {body[:200]}"
                        break
                elif et in ("run.failed", "run.cancelled"):
                    err = str(event.get("error") or et)
                    break
                elif et == "run.completed":
                    # Final output replaces streamed deltas (else caption doubles).
                    out = event.get("output") or event.get("text")
                    if out:
                        pieces = [str(out)]
                    break
    except Exception as exc:  # noqa: BLE001
        err = f"SSE：{exc}"

    text = "".join(pieces).strip()
    text = _dedupe_exact_echo(text)
    if not text and not err:
        # poll final status for output
        code, body = _api_request("GET", f"/v1/runs/{run_id}", timeout=30.0)
        if code < 400:
            try:
                obj = json.loads(body)
                text = str(obj.get("output") or "").strip()
                text = _dedupe_exact_echo(text)
                if obj.get("status") == "failed":
                    err = str(obj.get("error") or "run failed")
            except json.JSONDecodeError:
                pass
    return text, err, "ok" if text and not err else (err or "empty")


def _dedupe_exact_echo(text: str) -> str:
    """If Hermes／SSE glued the same paragraph twice, keep one copy."""
    t = (text or "").strip()
    n = len(t)
    if n < 40:
        return t
    half = n // 2
    if t[:half] == t[half:]:
        return t[:half]
    return t


def _chat_via_api(
    text: str,
    *,
    session_id: str | None,
    ask_approve: AskApproveFn | None,
    timeout_sec: float,
    image_path: str | Path | None = None,
) -> HermesReply:
    """Submit one run; block on SSE + optional Yes/No approvals."""
    ok_api, msg = ensure_api_server()
    if not ok_api:
        return HermesReply(False, "", "", "", None, error=msg)

    sid = session_id or (_JARVIS_SESSION_PREFIX + secrets.token_hex(4))
    try:
        runs_input = build_runs_input(text, image_path=image_path)
    except (OSError, ValueError) as exc:
        return HermesReply(False, "", "", "", sid, error=str(exc))

    body = {
        "input": runs_input,
        "session_id": sid,
        "instructions": _SPEAK_INSTRUCTIONS,
    }
    # multimodal body can be large; allow slower POST
    post_timeout = 120.0 if image_path else 60.0
    code, raw = _api_request("POST", "/v1/runs", body, timeout=post_timeout)
    if code >= 400:
        return HermesReply(
            False, "", "", raw, sid, error=f"POST /v1/runs {code}: {raw[:300]}"
        )
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return HermesReply(False, "", "", raw, sid, error="runs 回覆非 JSON")
    run_id = str(obj.get("run_id") or "")
    if not run_id:
        return HermesReply(False, "", "", raw, sid, error="無 run_id")

    out, err, _hint = _consume_run_sse(
        run_id, ask_approve=ask_approve, timeout_sec=timeout_sec
    )
    if err and not out:
        return HermesReply(False, "", "", raw + "\n" + (out or ""), sid, error=err)
    if not out:
        return HermesReply(False, "", "", raw, sid, error=err or "空回覆")

    cleaned = strip_heartbeat(out)
    cleaned = re.sub(
        r"(?ms)^┌─\s*Reasoning\s*─+.*?^└─.*?(?:\n|$)",
        "",
        cleaned,
    ).strip()
    caption, spoken = split_speak_footer(cleaned)
    if not spoken:
        spoken = spoken_stub(cleaned)
    if not spoken:
        try:
            from jarvis.brain import translate_to_english_short
            spoken = translate_to_english_short(caption) or ""
        except Exception:
            spoken = ""
    return HermesReply(
        ok=True,
        caption=caption,
        spoken=spoken,
        raw=out,
        session_id=sid,
    )


def _chat_via_cli(
    text: str,
    *,
    resume: str | None,
    image_wsl: str | None,
    timeout_sec: float,
) -> HermesReply:
    """Fallback: Windows ``hermes chat -q`` (same HERMES_HOME as Discord)."""
    py = _hermes_python()
    if not py.is_file():
        return HermesReply(
            False, "", "", "", resume, error=f"搵唔到 Hermes python：{py}"
        )
    cmd = [
        str(py),
        "-m",
        "hermes_cli.main",
        "chat",
        "-q",
        text + _SPEAK_QUERY_HINT,
        "-Q",
        "--max-turns",
        "12",
        "--source",
        "jarvis",
    ]
    if image_wsl:
        cmd += ["--image", image_wsl]
    if resume:
        cmd += ["--resume", resume]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
            env=_hermes_env(),
            cwd=str(_hermes_home()),
            creationflags=_no_window_flags(),
        )
    except OSError as exc:
        return HermesReply(
            False, "", "", "", resume, error=f"Hermes CLI 失敗：{exc}"
        )
    except subprocess.TimeoutExpired:
        hint = f"Hermes 逾時（{int(timeout_sec)}s）"
        if image_wsl:
            hint += "；附圖回落 -q 無 Approve 彈窗，危險指令會卡住"
        return HermesReply(False, "", "", "", None, error=hint)

    out = (proc.stdout or "") + (
        ("\n" + proc.stderr) if proc.stderr else ""
    )
    reply = parse_hermes_output(out)
    if proc.returncode != 0 and not reply.caption:
        err = (proc.stderr or proc.stdout or "Hermes 失敗").strip()
        return HermesReply(
            False, "", "", out, reply.session_id, error=err[:400]
        )
    if not reply.ok:
        reply.error = reply.error or f"exit {proc.returncode}"
        return reply
    sid = reply.session_id or resume
    if sid and not reply.session_id:
        reply.session_id = sid
    return reply


def chat(
    user_text: str,
    *,
    image_path: str | Path | None = None,
    ask_approve: AskApproveFn | None = None,
    timeout_sec: float = 120.0,
    dry_run: bool = False,
) -> HermesReply:
    """Ask Hermes one utterance; Prefer API+Approve; fallback CLI."""
    text = (user_text or "").strip()
    if not text and not image_path:
        return HermesReply(False, "", "", "", None, error="空白指令")
    if not text:
        text = "請描述呢張圖。"

    resume = _active_session()
    image_file: Path | None = None
    image_wsl = None
    if image_path:
        ip = Path(image_path)
        if not ip.is_file():
            return HermesReply(
                False, "", "", "", None, error=f"搵唔到圖：{ip}"
            )
        image_file = ip
        image_wsl = str(ip)

    # Vision + tools often slower than plain chat
    if image_file and timeout_sec < 180.0:
        timeout_sec = 180.0

    if dry_run:
        mode = "api-runs+image" if image_file else "api-runs"
        return HermesReply(
            True,
            caption=f"[dry-run hermes/{mode}] {text}",
            spoken="",
            raw=_build_inner_bash(text, resume=resume, image_wsl=image_wsl),
            session_id=resume,
        )

    # Primary: API Runs (+ multimodal image) so Approve UI works.
    reply: HermesReply
    try:
        reply = _chat_via_api(
            text,
            session_id=resume,
            ask_approve=ask_approve,
            timeout_sec=timeout_sec,
            image_path=image_file,
        )
    except Exception as exc:  # noqa: BLE001
        reply = HermesReply(
            False, "", "", "", resume, error=f"API 例外：{exc}"
        )
    if not reply.ok:
        fb = _chat_via_cli(
            text,
            resume=resume,
            image_wsl=image_wsl,
            timeout_sec=timeout_sec,
        )
        if fb.ok:
            fb.raw = (
                f"[hermes] API 失敗（{reply.error}）→ 回落 -q\n" + (fb.raw or "")
            )
            reply = fb
        elif image_file and "逾時" in (fb.error or ""):
            reply = fb  # keep clearer CLI timeout hint
        elif not reply.error:
            reply = fb

    if reply.ok:
        sid = reply.session_id or resume
        _touch_session(sid)
        if sid and not reply.session_id:
            reply.session_id = sid
    return reply


DASHBOARD_URL = "http://127.0.0.1:9119"
_DASHBOARD_PORT = 9119
_DASHBOARD_START = (
    f"{_WSL_PATH_EXPORT}; "
    "hermes dashboard --host 127.0.0.1 --port 9119 --no-open"
)


def _port_up(host: str = "127.0.0.1", port: int = _DASHBOARD_PORT) -> bool:
    return _port_listening(host, port)


def open_dashboard(*, wait_sec: float = 120.0) -> tuple[bool, str]:
    """Ensure Hermes web dashboard is up; open default browser. No console flash."""
    import webbrowser

    if _port_up():
        webbrowser.open(DASHBOARD_URL)
        return True, f"已開 {DASHBOARD_URL}"

    try:
        proc = subprocess.Popen(
            ["wsl", "-d", "Ubuntu", "-e", "bash", "-lc", _DASHBOARD_START],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=_no_window_flags(),
        )
    except FileNotFoundError:
        return False, "找不到 wsl（請確認 WSL2）"

    deadline = time.monotonic() + max(5.0, wait_sec)
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out = ""
            try:
                out = proc.stdout.read() if proc.stdout else ""
            except Exception:
                pass
            tail = (out or "").strip()[-400:]
            return False, f"dashboard 啟動失敗：{tail or f'exit {proc.returncode}'}"
        if _port_up():
            webbrowser.open(DASHBOARD_URL)
            return True, f"已啟動並開 {DASHBOARD_URL}"
        time.sleep(0.5)

    try:
        proc.terminate()
    except Exception:
        pass
    return False, f"逾時等 :{_DASHBOARD_PORT}"
