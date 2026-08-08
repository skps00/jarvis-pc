#!/usr/bin/env bash
# One-shot: Docker PATH + Hermes terminal.backend=docker (sandbox-only mount).
set -euo pipefail

DOCKER_BIN="/mnt/c/Program Files/Docker/Docker/resources/bin"
export PATH="${DOCKER_BIN}:${HOME}/bin:${HOME}/.local/bin:${PATH}"

mkdir -p "${HOME}/bin"
SRC="/mnt/c/Users/skps9/Documents/Code_Project/jarvis-pc/scripts/wsl_docker_wrapper.sh"
if [[ -f "$SRC" ]]; then
  sed 's/\r$//' "$SRC" > "${HOME}/bin/docker"
  chmod +x "${HOME}/bin/docker"
fi

MARKER='# jarvis-docker-path'
if ! grep -qF "$MARKER" "${HOME}/.bashrc" 2>/dev/null; then
  cat >> "${HOME}/.bashrc" <<EOF

${MARKER}
export PATH="${DOCKER_BIN}:\${HOME}/bin:\${HOME}/.local/bin:\${PATH}"
EOF
fi

python3 <<'PY'
from pathlib import Path

p = Path.home() / ".hermes" / "config.yaml"
text = p.read_text(encoding="utf-8")
block = """
# jarvis Trusted docker terminal — mount ONLY HermesSandbox
terminal:
  backend: docker
  cwd: /workspace
  timeout: 180
  lifetime_seconds: 300
  docker_image: nikolaik/python-nodejs:python3.11-nodejs20
  docker_mount_cwd_to_workspace: false
  docker_volumes:
    - /mnt/c/HermesSandbox:/workspace
"""
if "backend: docker" in text or "backend: \"docker\"" in text:
    print("terminal docker already configured")
elif "\nterminal:" in text or text.startswith("terminal:"):
    raise SystemExit("terminal: exists but not docker — edit manually")
else:
    p.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
    print("appended terminal docker block")
PY

echo "docker=$(command -v docker)"
docker version --format '{{.Server.Version}}' >/dev/null
echo "OK hermes docker terminal setup"
