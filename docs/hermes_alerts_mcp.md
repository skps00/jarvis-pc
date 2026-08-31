# Hermes ↔ Jarvis alerts HTTP MCP

Watcher (`jarvis serve`) enqueues short English pings; Hermes TTS speaks them.

## Topology

```text
jarvis serve
  → AlertStore JSONL
  → HTTP MCP 127.0.0.1:8765/mcp   (Hermes tools / debug)
  → poller ~1s (scripts/hermes_alert_poll_loop.py) → Hermes TTS (alert_tts=hermes) → ack

Hermes cron (backup, ≥1m): jarvis-alerts-speak --no-agent
  → scripts under %LOCALAPPDATA%\hermes\scripts\jarvis_alert_speak_once.py
  needs: hermes gateway running
```

## FACT — cron cannot do 1s

Hermes schedule units are **minutes+** (`every 1m` min for intervals). Gateway ticks ~**60s**.  
Eng plan 「≤1s poll」→ use **`hermes_alert_poll_loop.py`** (started by `jarvis serve` when `alert_tts=hermes`). Cron = slow backup only.

## TTS modes (`alert_tts`)

| Value | Behavior |
|-------|----------|
| `hermes` (default) | Hermes TTS subprocess only (60s hard timeout + `taskkill /F /T` on hang) |
| `piper` | In-process Jarvis Piper mouth |
| `off` | Drain/ack without speaking |

## GPU health (P0)

NVML (`nvidia-ml-py`) primary → nvidia-smi CSV fallback. Dynamic clock baseline + hard temp ceiling (≥90°C). Per-reason cooldown.

## Token / MCP

- Token file: `%APPDATA%\Jarvis\alerts\mcp_token.txt` (auto)
- Env: `JARVIS_ALERTS_MCP_TOKEN`
- Hermes client: `%LOCALAPPDATA%\hermes\config.yaml` → `mcp_servers.jarvis-alerts`

```yaml
mcp_servers:
  jarvis-alerts:
    url: "http://127.0.0.1:8765/mcp"
    headers:
      Authorization: "Bearer <token>"
    timeout: 30
```

Verify:

```powershell
hermes mcp list
hermes mcp test jarvis-alerts
# expect 10 tools: peek_alert, ack_alert, list_alerts, alert_stats,
#   jarvis_speak, jarvis_wake_status, jarvis_sensors, jarvis_alert,
#   jarvis_clarify_gate (Self-Evol Phase E: EVPI 問唔問), jarvis_autonomy_state (Phase D: 自主度等級)
```

Self-Evol tools（2026-08-31 wiring）:
- `jarvis_clarify_gate(task, task_type, unknowns[], assumptions[], confidence)` → `should_ask` + 保守假設；答案一律當 untrusted（R17）
- `jarvis_autonomy_state()` → `level`（L0/L1a/L1b/L1c）+ `sandbox_ready` + 最近 H_auth events；level 持久化喺 `%APPDATA%\Jarvis\autonomy_state.json`
- 詳情：skill `jarvis-self-evol-ops`

## Cron (backup)

```powershell
# already created as jarvis-alerts-speak (every 1m, --no-agent)
hermes cron list
hermes gateway          # required or jobs never fire
# or: hermes gateway install
```

## Fast path (recommended)

```powershell
# jarvis serve starts MCP + poller when alert_tts=hermes
# or manual:
$env:PYTHONPATH = "C:\Users\skps9\Documents\Code_Project\jarvis-pc\src"
python scripts\hermes_alert_poll_loop.py
```

Needs: Windows Hermes + `piper-tts` in Hermes venv + Jarvis model  
`%APPDATA%\Jarvis\models\piper\jarvis-high.onnx` + `ffplay` on PATH.

Hermes `config.yaml`:

```yaml
tts:
  provider: piper
  piper:
    voice: "C:/Users/skps9/AppData/Roaming/Jarvis/models/piper/jarvis-high.onnx"
```

## Cursor triggers (pick in companion 設定 → 提醒)

| Key | Default | Meaning |
|-----|---------|---------|
| `alert_cursor` | `true` | Master switch |
| `alert_cursor_hooks` | `true` | stop / preToolUse → queue. **Windows:** install uses `cmd /c … python -u` ([forum](https://forum.cursor.com/t/hooks-not-working-on-windows/149509)). |
| `alert_cursor_toast` | `true` | Action Center; skips Done only if a hook fired in last ~30s |
| `alert_cursor_uia` | `true` | Exact UIA `Waiting for approval` — keep ON if Ask/plan silent |
| `alert_cursor_watch` | `false` | Title busy→idle + taskbar flash (noisy) |

Debug hooks: Cursor **View → Output → Hooks**. Reinstall after pull: `python -m jarvis cursor-hooks install` then reload window.

```powershell
cd C:\Users\skps9\Documents\Code_Project\jarvis-pc
$env:PYTHONPATH = ".\src"
python -m jarvis cursor-hooks install
python -m jarvis cursor-hooks status
```

Writes/merges `%USERPROFILE%\.cursor\hooks.json`:
- `stop` → finished / error
- `preToolUse` → SwitchMode / Ask* (when Cursor fires it)

Enable **Hooks** in Cursor Settings; reload window. If hooks feel unstable: uncheck Hooks, keep Toast + UIA.

| Event | Phrase |
|-------|--------|
| stop completed | Cursor finished its work. |
| preToolUse SwitchMode | Cursor wants plan mode. |
| Toast / UIA wait | Cursor needs your approval. / plan phrase |

## Settings

| Key | Values |
|-----|--------|
| `alert_tts` | `hermes` (default) / `piper` / `off` |
| `alerts_mcp_port` | default `8765` |

## Spike

`docs/hermes_speak_spike.md`
