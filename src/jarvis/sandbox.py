"""L1a sandbox runner (Self-Evol Phase D, R18) — Docker Desktop containers.

Why Docker over WSL2 (decision 2026-08-31 #6):
- R18: a sandbox must be machine-enforced — filesystem + network isolation,
  NO user credentials inside, egress closed by default. WSL2 shares the host
  kernel and can read /mnt/c (incl. ~/.ssh) — an exfiltration pipe.
- Docker gives real namespace isolation, `--network none`, and allowlisted
  volume mounts only.

Design:
- LAZY: Docker Desktop is only started on first use (it costs ~2GB RAM as a
  VM). `AutonomyState.sandbox_ready` flips True only after the sandbox
  container actually exists (never on paper).
- Container `jarvis-sandbox`: image python:3.12-slim, `--network none`,
  mounts ONLY the allowlisted workdir (never ~/.ssh, never %APPDATA%).
- Host env is NOT passed in; no credentials reach the container.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

_logger = logging.getLogger("jarvis.sandbox")

SANDBOX_CONTAINER = "jarvis-sandbox"
SANDBOX_IMAGE = "python:3.12-slim"
# Workdir mounted read-write into the container; everything else stays out.
_DEFAULT_WORKDIR = Path.home() / "HermesSandbox" / "l1a"


@dataclass
class SandboxRunner:
    """Docker-based L1a sandbox. Lazy start; fail-closed."""

    workdir: Path = field(default_factory=lambda: _DEFAULT_WORKDIR)
    container: str = SANDBOX_CONTAINER
    image: str = SANDBOX_IMAGE
    _docker_checked: bool = False
    _docker_ok: bool = False

    # ------------------------------------------------------------------
    def _run(
        self,
        args: list[str],
        *,
        timeout: float = 60.0,
        env_clear: bool = True,
    ) -> tuple[int, str]:
        """Run docker CLI. env_clear=True: never leak host credentials into
        the child (fail-closed; a docker call needs no user secrets)."""
        env = {"PATH": os.environ.get("PATH", "")} if env_clear else None
        try:
            proc = subprocess.run(
                ["docker", *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=env,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except FileNotFoundError:
            return 127, "docker CLI not found"
        except subprocess.TimeoutExpired:
            return 124, f"docker {args[0]} timeout"
        out = ((proc.stdout or "") + (proc.stderr or "")).strip()
        return proc.returncode, out[-800:]

    def docker_available(self) -> bool:
        """Daemon reachable? (cached per process)."""
        if self._docker_checked:
            return self._docker_ok
        self._docker_checked = True
        code, _ = self._run(["version", "--format", "{{.Server.Version}}"], timeout=15)
        self._docker_ok = code == 0
        return self._docker_ok

    def start_daemon(self, wait_s: float = 90.0) -> tuple[bool, str]:
        """Launch Docker Desktop (headless) and wait for the daemon."""
        if self.docker_available():
            return True, "daemon up"
        # Start Docker Desktop UI (its CLI is `start`; harmless in tray).
        code, out = self._run(["desktop", "start"], timeout=30, env_clear=False)
        if code not in (0, 1):  # 1 can mean "already starting"
            return False, f"docker desktop start: {out or code}"
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            if self.docker_available():
                return True, "Docker Desktop ready"
            time.sleep(3)
        return False, f"Docker Desktop not ready within {wait_s:.0f}s"

    def ensure(self) -> tuple[bool, str]:
        """Daemon up + sandbox container exists (create on first use)."""
        ok, msg = self.start_daemon()
        if not ok:
            return False, msg
        code, out = self._run(["container", "inspect", self.container])
        if code == 0:
            return True, "sandbox container ready"
        self.workdir.mkdir(parents=True, exist_ok=True)
        # --network none: egress closed by default (R18). Only the allowlisted
        # workdir is mounted. No host env, no credentials.
        code, out = self._run(
            [
                "run", "-d", "--name", self.container,
                "--network", "none",
                "--restart", "unless-stopped",
                "-v", f"{self.workdir}:/work",
                "--workdir", "/work",
                self.image,
                "sleep", "infinity",
            ],
            timeout=180,
        )
        if code != 0:
            return False, f"create sandbox: {out}"
        return True, "sandbox container created"

    def run(
        self,
        cmd: list[str],
        *,
        timeout: float = 120.0,
    ) -> tuple[int, str]:
        """Execute a command INSIDE the sandbox (network none, no creds)."""
        ok, msg = self.ensure()
        if not ok:
            return 1, f"sandbox unavailable: {msg}"
        code, out = self._run(
            ["exec", "-i", self.container, *cmd],
            timeout=timeout,
        )
        return code, out

    def stop(self) -> tuple[bool, str]:
        """Stop the container (image kept; restart is fast)."""
        code, out = self._run(["stop", self.container], timeout=30)
        return code == 0, out or ("stopped" if code == 0 else "stop failed")

    def ready(self) -> bool:
        """True when daemon + container both exist (for AutonomyState)."""
        if not self.docker_available():
            return False
        code, _ = self._run(["container", "inspect", self.container])
        return code == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="JARVIS L1a sandbox (Docker)")
    ap.add_argument("--check", action="store_true", help="print ready/not-ready")
    ap.add_argument("--ensure", action="store_true", help="start daemon + create container")
    ap.add_argument("--run", nargs="+", help="command to run inside sandbox")
    ap.add_argument("--stop", action="store_true", help="stop the sandbox container")
    args = ap.parse_args()

    s = SandboxRunner()
    if args.check:
        print("READY" if s.ready() else "NOT_READY")
        return 0
    if args.ensure:
        ok, msg = s.ensure()
        print(msg)
        return 0 if ok else 1
    if args.run:
        code, out = s.run(args.run)
        print(out)
        return code
    if args.stop:
        ok, msg = s.stop()
        print(msg)
        return 0 if ok else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
