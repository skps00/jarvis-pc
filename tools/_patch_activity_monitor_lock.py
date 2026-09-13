#!/usr/bin/env python3
"""One-shot: add O_EXCL lock to activity_monitor._vc_write_since (F2)."""
from __future__ import annotations

from pathlib import Path

path = Path.home() / "AppData/Local/hermes/scripts/activity_monitor.py"
text = path.read_text(encoding="utf-8")

old1 = "_VC_MIN_ACTIVE_S = 5.0\n\ndef _vc_state_since():"
new1 = '_VC_MIN_ACTIVE_S = 5.0\n_VC_LOCK_PATH = _VC_STATE_PATH + ".lock"\n\ndef _vc_state_since():'
if old1 not in text:
    raise SystemExit("anchor1 missing (already patched?)")
text = text.replace(old1, new1, 1)

old2 = '''def _vc_write_since(ts):
    try:
        d = os.path.dirname(_VC_STATE_PATH)
        os.makedirs(d, exist_ok=True)
        tmp = _VC_STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"since": ts}, f)
        os.replace(tmp, _VC_STATE_PATH)
    except Exception:
        pass'''

new2 = '''def _vc_write_since(ts):
    lock_fd = None
    deadline = time.time() + 1.0
    while time.time() < deadline:
        try:
            lock_fd = os.open(_VC_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            time.sleep(0.05)
        except Exception:
            return
    else:
        return
    try:
        d = os.path.dirname(_VC_STATE_PATH)
        os.makedirs(d, exist_ok=True)
        tmp = _VC_STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"since": ts}, f)
        os.replace(tmp, _VC_STATE_PATH)
    except Exception:
        pass
    finally:
        if lock_fd is not None:
            try:
                os.close(lock_fd)
            except Exception:
                pass
            try:
                os.remove(_VC_LOCK_PATH)
            except Exception:
                pass'''

if old2 not in text:
    raise SystemExit("anchor2 missing (already patched?)")
text = text.replace(old2, new2, 1)
path.write_text(text, encoding="utf-8")
print(f"patched {path}")
