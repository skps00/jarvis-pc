#!/usr/bin/env bash
# Ensure Docker Desktop CLI is on PATH for Hermes (Ubuntu WSL).
export PATH="/mnt/c/Program Files/Docker/Docker/resources/bin:${HOME}/bin:${PATH}"
exec docker "$@"
