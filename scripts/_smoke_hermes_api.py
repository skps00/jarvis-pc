"""Smoke: start Hermes API server and probe /health + /v1/runs.

Uses the same key file as Jarvis: %APPDATA%\\Jarvis\\hermes_api.key
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_NO = getattr(subprocess, "CREATE_NO_WINDOW", 0)
PORT = 8642
KEY_PATH = Path.home() / "AppData" / "Roaming" / "Jarvis" / "hermes_api.key"


def load_key() -> str:
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.is_file():
        key = KEY_PATH.read_text(encoding="utf-8").strip()
        if len(key) >= 16:
            return key
    # mirror jarvis.hermes_bridge default shape without importing package
    import secrets

    key = "jarvis-" + secrets.token_hex(16)
    KEY_PATH.write_text(key + "\n", encoding="utf-8")
    return key


def port_up() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
            return True
    except OSError:
        return False


def http(method: str, path: str, body: dict | None = None, timeout: float = 30):
    key = load_key()
    data = None
    headers = {"Authorization": f"Bearer {key}"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return resp.status, raw


def main() -> int:
    key = load_key()
    print(f"key_file={KEY_PATH} len={len(key)}")

    if not port_up():
        # do not print key; pass via env inside WSL only
        import shlex

        kq = shlex.quote(key)
        inner = (
            f'export PATH="$HOME/.local/bin:$PATH"; '
            f"export API_SERVER_ENABLED=true; "
            f"export API_SERVER_KEY={kq}; "
            f"export API_SERVER_HOST=127.0.0.1; "
            f"export API_SERVER_PORT={PORT}; "
            f"hermes gateway run"
        )
        print("starting gateway…")
        proc = subprocess.Popen(
            ["wsl", "-d", "Ubuntu", "-e", "bash", "-lc", inner],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=_NO,
        )
        for i in range(60):
            if port_up():
                print(f"up after {i+1}s pid={proc.pid}")
                break
            if proc.poll() is not None:
                out = proc.stdout.read() if proc.stdout else ""
                print("exited early", proc.returncode)
                print(out[-3000:])
                return 1
            time.sleep(1)
        else:
            print("timeout")
            proc.terminate()
            return 2
    else:
        print("already up")

    try:
        st, raw = http("GET", "/health", timeout=10)
        print("health", st, raw[:300])
    except Exception as exc:
        print("health fail", exc)
        return 3

    try:
        st, raw = http("GET", "/v1/capabilities", timeout=15)
        print("caps", st, raw[:400])
    except urllib.error.HTTPError as exc:
        print("caps HTTP", exc.code, exc.read()[:400])
        if exc.code == 401:
            print("HINT: kill wrong-key gateway: wsl fuser -k 8642/tcp")
            return 5
    except Exception as exc:
        print("caps fail", exc)

    try:
        st, raw = http(
            "POST",
            "/v1/runs",
            {"input": "Reply with exactly: PONG", "session_id": "jarvis-smoke"},
            timeout=120,
        )
        print("runs", st, raw[:800])
        obj = json.loads(raw)
        run_id = obj.get("run_id") or obj.get("id")
        print("run_id", run_id)
    except urllib.error.HTTPError as exc:
        print("runs HTTP", exc.code, exc.read()[:800])
        return 4
    except Exception as exc:
        print("runs fail", exc)
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
