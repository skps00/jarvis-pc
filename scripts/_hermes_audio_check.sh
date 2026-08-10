#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
PY="$HOME/.hermes/hermes-agent/.venv/bin/python"
echo "=== sounddevice ==="
"$PY" - <<'PY'
import sounddevice as sd
devs = sd.query_devices()
print("count", len(devs))
print("default", sd.default.device)
for i, d in enumerate(devs):
    if d["max_input_channels"] > 0 or d["max_output_channels"] > 0:
        print(f"{i}: {d['name']!r} in={d['max_input_channels']} out={d['max_output_channels']}")
PY
echo "=== hermes desktop/gui ==="
hermes desktop --help 2>&1 | head -30 || true
hermes gui --help 2>&1 | head -20 || true
echo "=== config wake/voice ==="
grep -nE '^(wake_word|voice|stt|tts|  [a-z_]+):' ~/.hermes/config.yaml | head -50
