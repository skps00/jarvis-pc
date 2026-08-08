#!/usr/bin/env bash
set -euo pipefail
export PATH="/mnt/c/Program Files/Docker/Docker/resources/bin:${HOME}/bin:${PATH}"
echo "PATH ok"
ls "/mnt/c/Program Files/Docker/Docker/resources/bin" | head -40
echo "===="
which docker-credential-desktop.exe || true
which docker
docker version
echo "===="
docker run --rm hello-world
