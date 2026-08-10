# Hermes-first 架構（Jarvis companion）

```text
Mic → Windows native Hermes wake / Voice / barge_in
        → Hermes agent（%LOCALAPPDATA%\hermes）
              └─ HTTP MCP → Jarvis alerts（peek → Hermes TTS → ack）
jarvis serve → Toast + Discord badge watcher → JSONL queue + alerts MCP
```

**對話大腦＋語音 UX = Windows native Hermes（主）。**  
WSL Hermes 可作開發／後備，唔係 v1 alert 宿主。  
**桌面提醒眼睛 = Jarvis**（Hermes 無 toast／badge watcher）。Hands MCP 已封存 `attic/hands_mcp/`。

## 設定

`%APPDATA%\Jarvis\settings.json`：

| 鍵 | 值 | 說明 |
|----|-----|------|
| `voice_frontend` | `hermes`（預設）／`jarvis` | `hermes` → 禁 Jarvis OWW，避雙 mic |
| `alert_tts` | `hermes`（預設）／`piper`／`off` | hermes＝入隊；piper＝本機 mouth；off＝唔讀 |
| `alerts_mcp_port` | `8765` | loopback HTTP MCP |
| alerts 開關 | Discord／WA／Toast… | 照舊 |

## 提醒路徑

1. `AlertWatcher` 組成短英 stub（**無 message body**）
2. `alert_tts=hermes` → `AlertStore` JSONL + HTTP MCP
3. Hermes skill/cron ~2s：`peek_alert` → Hermes TTS → `ack_alert`
4. Spike：`docs/hermes_speak_spike.md`；接線：`docs/hermes_alerts_mcp.md`

## 個性／TTS

- 對話／alert 朗讀：Hermes TTS（Edge 等，跟 Hermes `tts:`）
- `alert_tts=piper` 逃生艙先用 Jarvis Piper

## 相關文件

- Speak spike：`docs/hermes_speak_spike.md`
- Alerts MCP：`docs/hermes_alerts_mcp.md`
- Voice 煙測（舊 WSL 筆記）：`docs/hermes_voice_smoke.md`
- Approve：`docs/approve_bridge.md`
