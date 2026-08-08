#!/usr/bin/env bash
set -euo pipefail
export PATH="/mnt/c/Program Files/Docker/Docker/resources/bin:${HOME}/bin:${PATH}"
docker run --rm -v /mnt/c/HermesSandbox:/workspace -w /workspace alpine \
  sh -c 'echo DOCKER_MOUNT_OK > /workspace/docker_mount_test.txt && cat /workspace/docker_mount_test.txt'
ls -la /mnt/c/HermesSandbox/docker_mount_test.txt
