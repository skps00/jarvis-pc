# Approve 橋（Phase1 現況／Phase1.5）＋Trusted docker

Updated: 2026-08-07

## 目標（設計 G1）

危險 Hermes tool 要 Jarvis **Yes／No**，唔好卡喺睇唔見嘅 WSL TTY；**永不 `--yolo`**。

## Phase1.5（而家）

| 面 | 行為 |
|----|------|
| Hands（開／關／電源） | `ask_confirm` 彈窗 |
| Hermes 文字／附圖 | 本地 API `127.0.0.1:8642` → `/v1/runs`（圖＝multimodal base64）+ SSE `approval.request` → Jarvis Yes=`once`／No=`deny` |
| Hermes 雙輸出 | 主體**繁中** → `[caption]`；末行 `SPEAK: <短英>` → Piper TTS（無 SPEAK 則唔播） |
| API 起唔到 | 回落 `chat -q`（附圖可 `--image`；無 Approve 彈窗，危險指令易逾時） |
| **Safe（預設）** | `api_server`／`cli`：**無** terminal／browser／computer_use／cronjob |
| **Trusted（30min）** | 開 **docker terminal**（mount 只 `C:\HermesSandbox`→`/workspace`）；仍無 browser／CUA／yolo |
| API key | `%APPDATA%\Jarvis\hermes_api.key`（自動生成） |

關 Jarvis **唔強制**停 API gateway（同 dashboard）。關機先全死。Trusted 到期／關 Hermes → 回 Safe toolsets＋重載 API。

## Docker（本機）

- Docker Desktop 4.85+；WSL PATH 含 `…/Docker/resources/bin`
- Hermes `config.yaml`：`terminal.backend: docker`＋`docker_volumes: [/mnt/c/HermesSandbox:/workspace]`
- 設定腳本：`scripts/hermes_docker_terminal_setup.sh`

## Phase1 v0（歷史）

僅 `hermes chat -q`：無 stdin → 危險指令逾時／拒。

## 明確不做

- `--yolo`／`approvals.mode=off`
- Jarvis「永遠允許」
- host terminal
- computer_use（Phase2）
- Telegram／Discord messaging gateway

## 驗收

- [x] Hands 關機／關 app 仍彈確認  
- [x] bridge **無** `--yolo`  
- [x] API health + runs 煙測（PONG）  
- [x] 手測：觸發危險指令 → Jarvis 彈窗 → Yes 後續跑  
- [x] Safe：api_server 無 terminal／browser／computer_use  
- [x] Docker Desktop + `hello-world`（WSL）  
- [x] 手測：Trusted → 容器寫 `/workspace` → sandbox 見檔  
- [x] 手測：Approve 彈窗（危險指令 Yes／No）  
- [x] 手測：貼圖 + 指令 → 走 API（要批則彈窗）

## 手測清單

1. `python -m jarvis serve`，設定開 Hermes  
2. 問一句普通閒聊 → 有 `[caption]`（繁中）+ `[speak]`（短英）；Piper 念英文  
3. 問一句會觸發危險 shell 嘅（例如叫佢刪系統路徑）→ 見彈窗 → No → 被拒  
4. 設定勾 **Trusted 30 分鐘** → 儲存 → log 見 docker terminal  
5. 叫「喺 terminal 寫 `/workspace/trusted_echo.txt` 內容 TRUSTED_OK」→ Approve Yes → 檔喺 `C:\HermesSandbox\`  
6. 關機掣關 PC（唔使先關 Hermes）
