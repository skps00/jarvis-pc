# JARVIS

**Just A Rather Very Intelligent System**

Windows 本機管家：熱鍵／系統匣細窗 → **打字**或**語音**指令 → 白名單 Hands（可選 Hermes／TTS）。

設計定稿：`%USERPROFILE%\.gstack\projects\jarvis-pc\*-design-*.md`（Status: APPROVED）

## 快速開始

```powershell
cd C:\Users\skps9\Documents\Code_Project\jarvis-pc
python -m pip install -e ".[ear,wake,alerts]"

python -m jarvis -c "開 Cursor"
python -m jarvis serve
# 或雙擊 JARVIS.vbs（無黑窗）；JARVIS.bat 同效果

# 開機自啟
python -m jarvis autostart on
```

細窗：**Enter** 送出；**Ctrl+Alt+J** 顯示／隱藏。設定可開關**聽候**（OWW「Jarvis」）→ VAD 收音 → 本機／雲端 ASR → 執行。自訓 wake 見 [docs/train_wake_jarvis.md](docs/train_wake_jarvis.md)。

可選 extras：`ear`（ASR）、`wake`（聽候）、`alerts`（Windows Toast 語音提醒）。

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
| 聽候／ASR | OWW wake → SenseVoice（預設）／Fun-ASR／雲端 ASR；語音路徑會做 ASR repair |
| 語音提醒 | Discord／WhatsApp／Cursor 等 Windows Toast → 英文 TTS stub（需 `.[alerts]`） |
| 查詢／歧義 | 小 LLM（`.env`：`JARVIS_LLM_*`，預設 DeepSeek）；Hands 仍只信白名單 |
| Hermes | 設定啟用後，query／閒聊經 WSL Hermes（開 App 仍本機） |

```powershell
copy .env.example .env   # 填 JARVIS_LLM_API_KEY=
```

見 [REMINDERS.md](REMINDERS.md)。
