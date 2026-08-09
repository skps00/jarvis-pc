# Hermes ↔ Jarvis alerts HTTP MCP

Watcher (`jarvis serve`) enqueues short English pings; Hermes TTS speaks them.

## Topology

```text
jarvis serve
  → AlertStore JSONL
  → HTTP MCP 127.0.0.1:8765/mcp   (Hermes tools / debug)
  → poller ~2s (scripts/hermes_alert_poll_loop.py) → Hermes Edge TTS → ack

Hermes cron (backup, ≥1m): jarvis-alerts-speak --no-agent
  → scripts under %LOCALAPPDATA%\hermes\scripts\jarvis_alert_speak_once.py
  needs: hermes gateway running
```

## FACT — cron cannot do 2s

Hermes schedule units are **minutes+** (`every 1m` min for intervals). Gateway ticks ~**60s**.  
Eng plan 「~2s poll」→ use **`hermes_alert_poll_loop.py`** (started by `jarvis serve` when `alert_tts=hermes`). Cron = slow backup only.

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
# expect 4 tools: peek_alert, ack_alert, list_alerts, alert_stats
```

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

## Cursor — official stop hook (recommended)

Same pattern as [agent-notify](https://github.com/cfngc4594/agent-notify) / [tinynudge](https://github.com/hiskuDN/claude-notify): Cursor fires `stop` → script enqueues → poller speaks.

```powershell
cd C:\Users\skps9\Documents\Code_Project\jarvis-pc
$env:PYTHONPATH = ".\src"
python -m jarvis cursor-hooks install
python -m jarvis cursor-hooks status
```

Writes/merges `%USERPROFILE%\.cursor\hooks.json`:
- `stop` → finished / error
- `preToolUse` → SwitchMode / Ask* (when Cursor fires it)

Enable **Hooks** in Cursor Settings; reload window.

| Event | Phrase |
|-------|--------|
| stop completed | Cursor finished its work. |
| preToolUse SwitchMode | Cursor wants plan mode. |
| UIA exact `Waiting for approval` | Cursor needs your approval. (fallback; AskQuestion often skips hooks — [Cursor bug](https://forum.cursor.com/t/cursor-cli-askquestion-tool-skips-pretooluse-and-posttooluse-hooks/161836)) |

| Key | Values |
|-----|--------|
| `alert_cursor` | master + exact UIA wait |
| `alert_cursor_watch` | `false` (default) — no Toast/title/flash. `true` = noisy fallback |

## Settings

| Key | Values |
|-----|--------|
| `alert_tts` | `hermes` (default) / `piper` / `off` |
| `alerts_mcp_port` | default `8765` |

## Spike

`docs/hermes_speak_spike.md`
