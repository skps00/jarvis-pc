#!/usr/bin/env bash
export PATH="/mnt/c/Program Files/Docker/Docker/resources/bin:${HOME}/bin:${HOME}/.local/bin:${PATH}"
echo "hermes=$(command -v hermes)"
hermes tools list --platform api_server | head -25
echo EXIT:$?
