#!/usr/bin/env bash
# Point WSL Hermes voice back to WSL-primary; prefer desktop client mic capture.
set -euo pipefail
CFG="$HOME/.hermes/config.yaml"
python3 - <<'PY'
from pathlib import Path
import re
p = Path.home() / ".hermes" / "config.yaml"
text = p.read_text(encoding="utf-8")
bak = p.with_suffix(".yaml.bak-wsl-primary")
if not bak.exists():
    bak.write_text(text, encoding="utf-8")
    print("backup", bak)

# Ensure wake_word.capture: client (stable Windows mic → WSL backend via desktop)
if "wake_word:" not in text:
    text += """
wake_word:
  enabled: true
  provider: openwakeword
  phrase: "hey jarvis"
  capture: client
  openwakeword:
    model: hey_jarvis
"""
elif "capture:" not in text.split("wake_word:", 1)[-1].split("\nvoice:", 1)[0]:
    text = text.replace(
        "wake_word:\n  enabled: true",
        "wake_word:\n  enabled: true\n  capture: client",
        1,
    )
else:
    text = re.sub(
        r"(wake_word:.*?^\s*)capture:\s*\w+",
        r"\1capture: client",
        text,
        count=1,
        flags=re.M | re.S,
    )

if "barge_in:" not in text:
    text += "\nvoice:\n  barge_in: true\n  auto_tts: true\n"
elif "barge_in: false" in text:
    text = text.replace("barge_in: false", "barge_in: true")

p.write_text(text, encoding="utf-8")
print("OK WSL-primary: capture=client, barge_in on")
# show wake block
import re as _re
m = _re.search(r"(?ms)^wake_word:.*?(?=^[a-zA-Z_]|\Z)", p.read_text(encoding="utf-8"))
print(m.group(0)[:500] if m else "no wake block")
PY
