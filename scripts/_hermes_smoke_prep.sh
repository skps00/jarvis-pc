#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
echo "hermes=$(command -v hermes || true)"
echo "uv=$(command -v uv || true)"
echo "python3=$(command -v python3 || true)"

AGENT="$HOME/.hermes/hermes-agent"
if [[ -x "$AGENT/.venv/bin/python" ]]; then
  PY="$AGENT/.venv/bin/python"
  PIP="$AGENT/.venv/bin/pip"
elif [[ -x "$AGENT/venv/bin/python" ]]; then
  PY="$AGENT/venv/bin/python"
  PIP="$AGENT/venv/bin/pip"
else
  PY="$(command -v python3)"
  PIP="$PY -m pip"
fi
echo "PY=$PY"

cd "$AGENT"
if command -v uv >/dev/null 2>&1; then
  uv pip install -e ".[voice]" -e ".[wake]" || uv pip install -e ".[voice,wake]" || true
else
  $PIP install -e ".[voice]" -e ".[wake]" || $PIP install -e ".[voice,wake]" || true
fi

$PY - <<'PY'
import sys
print("python", sys.version)
for m in ("sounddevice", "numpy", "openwakeword"):
    try:
        __import__(m)
        print(m, "OK")
    except Exception as e:
        print(m, "FAIL", e)
PY

CFG="$HOME/.hermes/config.yaml"
python3 - <<'PY'
from pathlib import Path
import re
p = Path.home() / ".hermes" / "config.yaml"
text = p.read_text(encoding="utf-8")
print("has wake_word:", "wake_word:" in text)
print("has barge_in:", "barge_in" in text)
for key in ("wake_word", "voice", "stt", "tts"):
    m = re.search(rf"(?ms)^({key}:.*?)(?=^[a-zA-Z_][\w-]*:|\Z)", text)
    if m:
        print("---", key, "---")
        print(m.group(1)[:600])
PY

# Merge voice/wake/stt/tts if missing
$PY - <<'PY'
from pathlib import Path
p = Path.home() / ".hermes" / "config.yaml"
text = p.read_text(encoding="utf-8")
changed = False
block = """
# --- jarvis-pc Phase0 smoke (Hermes-first voice) ---
wake_word:
  enabled: true
  provider: openwakeword
  phrase: "hey jarvis"
  openwakeword:
    model: hey_jarvis

voice:
  barge_in: true
  auto_tts: true

stt:
  provider: local
  local:
    model: base

tts:
  provider: edge
  edge:
    voice: "en-US-AriaNeural"
"""
if "barge_in:" not in text or "wake_word:" not in text:
    # backup
    bak = p.with_suffix(".yaml.bak-jarvis-smoke")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print("backup", bak)
    if not text.endswith("\n"):
        text += "\n"
    text += block
    p.write_text(text, encoding="utf-8")
    changed = True
    print("config: appended wake/voice/stt/tts")
else:
    # ensure barge_in true
    if "barge_in: false" in text:
        text = text.replace("barge_in: false", "barge_in: true")
        p.write_text(text, encoding="utf-8")
        changed = True
        print("config: forced barge_in true")
    else:
        print("config: wake/voice already present; left as-is")
print("changed", changed)
PY

hermes config get wake_word.enabled 2>/dev/null || true
hermes config get voice.barge_in 2>/dev/null || true
hermes doctor 2>&1 | head -60 || true
