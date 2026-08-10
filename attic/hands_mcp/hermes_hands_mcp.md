# Jarvis Hands MCP — Hermes 接線

Hermes Voice／Agent 經 **MCP** 呼叫 Jarvis Hands（白名單開／關／重開／電源／Discover）。  
**唔好**用 Hermes 裸 terminal／YOLO 開遊戲。

## 本機啟動（煙測）

```powershell
cd C:\Users\skps9\Documents\Code_Project\jarvis-pc
python -m pip install -e .
python scripts\jarvis_mcp.py
# 或：python -m jarvis.mcp_hands
```

stdio 等 Hermes 連；單獨跑會「卡住」係正常（等 JSON-RPC）。

## Tools

| Tool | 行為 |
|------|------|
| `open_app` | `開 {target}` → engine／Hands |
| `close_app` | `關 {target}` → 確認後關 |
| `restart_app` | `重開 {target}` |
| `power` | `action=shutdown\|sleep` |
| `discover` | 未登錄 app → 確認寫 profile＋開 |

確認類動作：Windows **MessageBox Yes／No**（同 shell 確認語意）。無 Yes → 取消。  
**無** YOLO／無跳過白名單。`dry_run: true` 只解析唔執行。

## Hermes `mcp_servers`（Windows native）

喺 Hermes `config.yaml`（路徑跟你安裝）：

```yaml
mcp_servers:
  jarvis_hands:
    command: C:\Users\skps9\AppData\Local\Programs\Python\Python312\python.exe
    args:
      - C:\Users\skps9\Documents\Code_Project\jarvis-pc\scripts\jarvis_mcp.py
    # 若用 venv：command 改成該 venv\Scripts\python.exe
```

把 `command`／`args` 換成你本機 `where python` 同 repo 路徑。

## WSL Hermes → Windows Hands（cmd 橋）

Hands **必須**喺 Windows Python 跑（開 exe／Steam）。Hermes 若喺 WSL：

```yaml
mcp_servers:
  jarvis_hands:
    command: /mnt/c/Windows/System32/cmd.exe
    args:
      - /c
      - C:\Users\skps9\AppData\Local\Programs\Python\Python312\python.exe
      - C:\Users\skps9\Documents\Code_Project\jarvis-pc\scripts\jarvis_mcp.py
```

注意：WSL 裏路徑寫 Windows 形式畀 `cmd.exe /c`；`python.exe` 要係 **Windows** 已 `pip install -e .` 嘅環境。

## 同 Jarvis serve 一齊

| 進程 | 職責 |
|------|------|
| Hermes Voice | wake、barge-in、長答、叫 MCP |
| `jarvis serve` | Toast 提醒、tray、熱鍵、Hermes Approve SSE |
| `jarvis_mcp.py` | Hands 白名單（可由 Hermes 拉起，唔使人手常開） |

語音前端設 `voice_frontend: hermes`（預設）→ Jarvis **唔開** OWW，避免搶咪。見 `docs/hermes_architecture.md`。

## 驗收（Phase 1）

Hermes（文字或 voice）叫：「開 Cursor／閂 Discord」→ log 見 Hands `[ok]`，行程真開／關；**唔經**亂 terminal。
