"""alert_shadow_report CLI: read-only ledger / heartbeat aggregates."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "alert_shadow_report.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("alert_shadow_report", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().isoformat()


def test_build_report_counts(tmp_path: Path) -> None:
    mod = _load_mod()
    t0 = 1_700_000_000.0
    ledger = tmp_path / "shadow_ledger.jsonl"
    hb = tmp_path / "shadow_heartbeat.jsonl"
    rows = [
        {"ts": _iso(t0), "kind": "whatsapp", "decision": "hold", "reason": "gaming"},
        {"ts": _iso(t0 + 1), "kind": "discord", "decision": "digest", "reason": "policy"},
        {"ts": _iso(t0 + 2), "kind": "gpu_hard", "decision": "speak", "reason": "critical"},
        {"ts": _iso(t0 + 3), "kind": "extra", "decision": "drop", "reason": "policy"},
        "not-json",
        {"ts": _iso(t0 - 100_000), "kind": "old", "decision": "speak", "reason": "policy"},
    ]
    ledger.write_text(
        "\n".join(json.dumps(r) if isinstance(r, dict) else r for r in rows) + "\n",
        encoding="utf-8",
    )
    hb.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "ts": _iso(t0),
                        "v1_gaming": False,
                        "is_gaming_v2": True,
                    }
                ),
                json.dumps(
                    {
                        "ts": _iso(t0 + 45),
                        "v1_gaming": True,
                        "is_gaming_v2": False,
                    }
                ),
                "bad-line",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    report = mod.build_report(hours=24, alerts_dir=tmp_path, now=t0 + 60)
    assert report["decisions"] == {"speak": 1, "hold": 1, "digest": 1, "drop": 1}
    assert report["reasons"]["gaming"] == 1
    assert report["kinds"]["whatsapp"] == 1
    assert report["heartbeat"]["lines"] == 2
    assert report["heartbeat"]["gaming_v2_true"] == 1
    assert report["heartbeat"]["gaming_v1_true"] == 1
    assert report["fp_hint"] == {"v1_only": 1, "v2_only": 1}
    assert report["heartbeat"]["game_active_hours"] == pytest.approx(45 / 3600.0)


def test_missing_files_zero(tmp_path: Path) -> None:
    mod = _load_mod()
    empty = tmp_path / "empty"
    empty.mkdir()
    report = mod.build_report(hours=24, alerts_dir=empty, now=1_700_000_000.0)
    assert report["decisions"] == {"speak": 0, "hold": 0, "digest": 0, "drop": 0}
    assert report["reasons"] == {}
    assert report["kinds"] == {}
    assert report["heartbeat"]["lines"] == 0
    assert report["fp_hint"] == {"v1_only": 0, "v2_only": 0}


def test_cli_path_flag(tmp_path: Path) -> None:
    import time as time_mod

    t0 = time_mod.time()
    ledger = tmp_path / "shadow_ledger.jsonl"
    ledger.write_text(
        json.dumps(
            {
                "ts": _iso(t0),
                "kind": "test",
                "decision": "speak",
                "reason": "policy",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "shadow_heartbeat.jsonl").write_text("", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--path",
            str(tmp_path),
            "--hours",
            "24",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_SCRIPT.parents[1]),
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout.strip())
    assert data["decisions"]["speak"] == 1
    assert "heartbeat" in data
