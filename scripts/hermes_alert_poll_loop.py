#!/usr/bin/env python3
"""Tight poll (~2s): peek → Hermes TTS → ack. Meets <3s better than cron.

Hermes cron min interval is 1 minute and gateway ticks ~60s — too slow for alerts.
Run this alongside ``jarvis-mcp`` / ``jarvis serve``.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_once = _HERE / "hermes_alert_speak_once.py"
_spec = importlib.util.spec_from_file_location("hermes_alert_speak_once", _once)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
_speak_hermes = _mod._speak_hermes


def main() -> int:
    from jarvis.alert_store import AlertStore

    interval = float(os.environ.get("JARVIS_ALERT_POLL_S", "2") or "2")
    st = AlertStore()
    print(f"[ok] alert poll loop every {interval}s → {st.path}", flush=True)
    while True:
        try:
            row = st.peek(lease_s=max(30.0, interval * 10))
            if row is not None:
                ok = _speak_hermes(row.phrase)
                if ok:
                    st.ack(row.id)
                    print(f"[ok] spoke {row.kind}: {row.phrase}", flush=True)
                else:
                    print(f"[fail] speak {row.id[:8]}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] poll: {exc}", flush=True)
        time.sleep(max(0.5, interval))


if __name__ == "__main__":
    raise SystemExit(main())
