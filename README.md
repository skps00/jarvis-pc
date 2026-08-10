# JARVIS

**Just A Rather Very Intelligent System**

Windows 本機管家：**Hermes = 對話／語音／alert TTS**；**Jarvis = 桌面提醒眼睛＋Approve 伴侶殼**。

設計定稿：`%USERPROFILE%\.gstack\projects\jarvis-pc\*-design-*.md`（Status: APPROVED）  
架構：`docs/hermes_architecture.md`｜Alerts MCP：`docs/hermes_alerts_mcp.md`｜Speak spike：`docs/hermes_speak_spike.md`

## 快速開始

```powershell
cd C:\Users\skps9\Documents\Code_Project\jarvis-pc
python -m pip install -e ".[alerts]"

# companion（桌面提醒眼睛 + alerts MCP + poller）
python -m jarvis serve
# 或雙擊桌面 JARVIS.lnk / JARVIS.vbs（無黑窗）

# CLI Hands 仍可用：
python -m jarvis -c "開 Cursor"
```

細窗＝**companion**：log／狀態／試語音提醒／設定；**唔打字開 app**（對話用 Hermes）。  
熱鍵顯示／隱藏。預設 `alert_tts=hermes`（Jarvis Piper 聲經 Hermes）。

## 能力

| 功能 | 說明 |
|------|------|
| 規則開場 | `open`／`開`／倒裝／STT 錯字動詞 |
| 新開 | `再開 X`／`開 new X`／`開新視窗 X` → 強制再開（Chrome=`--new-window`）；`開個 X` 只係普通開 |
| Steam 遊戲 | 已開再講「開」→ **確認後關閉**（`process_names`）；`再開` 仍強制 launch |
| 關 app | 優先殺 Jarvis 開過時記住嘅 PID（`memory.json` → `profile_pids`）；否則 `process_names`／lnk exe |
| 關閉 | `關 CS`／`閂 MC`／`close Cursor` → **先確認**再關 |
| 重開 | `restart CS`／`重開 CS`／`重啟 Chrome` → **確認**後關再開 |
| 電源 | `關機`／`睡眠`／`重啟電腦`／`reboot` → **先確認**再執行 |
| Chrome 還原 | `--restore-last-session`；已開則 focus；多窗冷開請用選單「結束」 |
| Discover | 未知 `open xxx` → Start Menu／Desktop／Local Programs／Get-StartApps／Steam／Prism → 確認後寫入 profiles；目標自動拼寫／粵拼近匹配 |
| 查詢／歧義 | 小 LLM（`.env`：`JARVIS_LLM_*`，預設 DeepSeek）；Hands 仍只信白名單 |
| Hermes | Voice wake＋barge-in；query／閒聊經 bridge；Hands 經 MCP（唔經裸 terminal） |
| 語音提醒 | Discord／WhatsApp／Cursor Toast → 短英 stub（`alert_tts=hermes` 預設） |

```powershell
copy .env.example .env   # 填 JARVIS_LLM_API_KEY=
```

見 [REMINDERS.md](REMINDERS.md)。
