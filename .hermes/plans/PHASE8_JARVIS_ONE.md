# Phase 8 — JARVIS ONE 遷移執行計畫

> 2026-08-28 起草。目標：jarvis + HUD 一個 Electron app、一個 tray、一個入口。
> 原則：每步可驗證、背景執行鐵則（零彈窗）、SK 確認先動 code。
> 狀態圖例：✅ 完成 ｜ 🔄 進行中 ｜ ⏳ 排期

---

## 現況盤點（2026-08-28）

| 組件 | 現況 | 位置 |
|---|---|---|
| HUD overlay（Iron Man） | ✅ v0.1 運行中（8770 reply / 8771 media bridge） | `jarvis-hud`（Electron） |
| Dock | ✅ 底部感應 + 遊戲隱藏（今日修咗 activity check） | `jarvis-hud/main.js` |
| Jarvis serve（voice） | ✅ python.exe serve（wake/STT/TTS/MCP 8765/watchdog） | `jarvis-pc`（Python 3.14） |
| Companion GUI | tkinter（480x420，老氣） | `jarvis-pc/src/jarvis/shell_app.py` |
| Settings GUI | tkinter ttk.Notebook | `jarvis-pc/src/jarvis/settings_ui.py` |
| Media bridge | Chrome extension + 8771 | `jarvis-hud/chrome-extension/` |
| Alerts MCP | FastMCP 8765（Hermes 已註冊） | `jarvis-pc/src/jarvis/mcp_alerts_http.py` |

**核心矛盾**：兩個 app（Electron HUD + Python serve）各自 tray、各自生命周期。Phase 8 = 一個 Electron main 統籌 + Python voice sidecar。

---

## 目標架構

```
JARVIS ONE (Electron app)
├─ Electron main (tray = 唯一入口)
│   ├─ HUD overlay（透明 Iron Man，遊戲隱藏）
│   ├─ Dock（底部感應）
│   ├─ Companion window（on-demand，Iron Man HTML）
│   ├─ Settings window（on-demand，Iron Man HTML）
│   ├─ Media bridge 8771 + Reply server 8770
│   └─── spawn ──► Python voice sidecar（hidden）
│       ├─ wake (OWW + AEC + speaker gate)
│       ├─ STT (SenseVoice GPU)
│       ├─ TTS (Piper)
│       ├─ Hermes bridge 8642 / SPEAK
│       └─ alerts MCP 8765
```

---

## 遷移步驟

### 8.1 一個入口（Electron 起時 spawn Python sidecar）✅（2026-08-28）

**做法**：
- `jarvis-hud` Electron main 啟動時 spawn `python.exe -m jarvis serve`（CREATE_NO_WINDOW + redirect serve.log）
- Tray 統管：HUD 顯示/隱藏、Companion、Settings、退出（退出 = kill sidecar + 關 HUD）
- 移除 jarvis-pc 自己嘅 tray（`start_tray` disable）——避免雙 tray

**驗證**：
- [x] 一個 tray 一個 process tree
- [x] 退出 tray → sidecar 一齊收（無 orphan python）
- [x] 全程無 console 閃出
- [x] HUD/Dock/Media bridge/Reply server 照常 work

**風險**：
- sidecar 死咗 → Electron 要 detect + restart（有 watchdog cron 兜底，但 Electron 內建更好）→ ⏳ 待查（8/29 死冇 respawn，8/31 兩次成功——下次再死查 main.js health-check）
- python.exe spawn 要 `windowsHide: true`（Electron execFile）——已知坑

### 8.2 視窗搬遷（tkinter → Electron Iron Man HTML）✅（2026-08-31）

**做法**：
- Companion/Settings 由 tkinter 搬去 Electron BrowserWindow（內嵌 HTML，同 HUD 視覺語言 #00aaf8 / Orbitron / Rajdhani）
- 唔再 show tkinter 視窗；`request_show()` → Electron IPC 顯示 Companion
- settings_ui.py 嘅功能（裝置列表、ASR/TTS/wake 設定）→ HTML form → 寫 settings.json（經 IPC 或者直接讀寫 JSON）

**驗證**：
- [x] 無 tkinter 視窗（全 Electron）——tkinter SettingsWindow 凍結（shell_app open_settings → 統一由 Electron HUD 管）
- [x] 唔撳唔彈（on-demand）
- [x] 設定改動即時生效（同而家 apply_settings 邏輯）——sidecar POST /settings（H2 單一 writer）

**風險**：
- settings_ui.py 邏輯多（dedup 裝置列表、preset 等）——搬遷要小心保留 → settings_ui.py 保留做 rollback
- 雙重寫 settings.json 競態（HTML + Python 同時改）→ H2 單一 writer 解決

### 8.3 語音 sidecar 化 ✅（2026-08-31）

**做法**：
- 保持 Python `jarvis serve` 做 voice（改動最少——8.1 已經 spawn 佢）
- Electron ↔ sidecar 溝通：IPC（stdio JSON-RPC）或 localhost HTTP（sidecar 已有 HTTP 經驗：8765/8770/8771）
- 語音狀態（wake on/off、STT 結果、TTS 播放中）→ Electron HUD 顯示

**驗證**：
- [x] 喊「hey jarvis」→ HUD 顯示 + 語音回應（全背景）——A2 voice_status.json（wake on/off、STT 中、TTS 中、mic_signal_ok）
- [x] HUD 顯示 wake 狀態（監聽中/處理中）

### 8.4 HUD 融合 ✅（2026-08-31）

**做法**：
- HUD overlay + Companion 共用 renderer 體系（一個 HTML/CSS/JS 架構，多 window 載入）
- dock/遊戲隱藏/工作列處理保留

**驗證**：
- [x] Iron Man 視覺統一（HUD + Companion + Settings 同一語言）——hud-theme.css（196 行共用 theme）；renderer/index.html 刻意唔 link（全屏 overlay CSS 衝突）
- [x] 遊戲中全部隱藏（checkActivity）

### 8.5 MCP 整合（Hermes ⇄ JARVIS 雙向）✅（2026-08-31）

**做法**：
- Jarvis 已係 MCP server（8765）——加 tools：`mcp_jarvis_speak` / `mcp_jarvis_wake_status` / `mcp_jarvis_sensors` / `mcp_jarvis_alert` / `jarvis_clarify_gate` / `jarvis_autonomy_state`
- Hermes `mcp_servers` config 已註冊 `jarvis-alerts`——擴展 tools 即可
- 安全 gate：speak 工具限頻 + 只限 SK DM + playing 時拒絕（master plan 已列）

**驗證**：
- [x] Hermes 內 call `mcp_jarvis_speak` 成功（Discord 傾偈叫 Jarvis 唸嘢）
- [x] MCP 死咗 → Hermes graceful fallback（文字）

---

## 執行結果（2026-08-31 全部完成 ✅）

1. **8.1 一個入口** ✅ 2026-08-28
2. **8.5 MCP 加 tools** ✅ 2026-08-31（jarvis_clarify_gate / jarvis_autonomy_state + restart 生效）
3. **8.3 voice IPC** ✅ 2026-08-31（voice_status.json）
4. **8.2 + 8.4 GUI 搬遷** ✅ 2026-08-31（settings.html 齊 + tkinter 凍結 + HUD 融合）

## 每步完成條件（全部達成）

- 8.1：一個 tray、退出乾淨、無 console 閃出 ✅
- 8.5：`mcp_jarvis_speak` 由 Hermes call 成功 + 安全 gate 生效 ✅
- 8.3：喊醒 → HUD 狀態顯示 + 語音回應 ✅（mic 修好後實測）
- 8.2/8.4：零 tkinter、視覺統一 ✅

---

## 風險 / 注意

- **雙 tray**：8.1 必須 disable jarvis-pc 自己 tray（`pystray` 起唔起由 Electron 控制）
- **Python spawn 隱藏**：`execFile` + `windowsHide: true`；PowerShell 要 `-WindowStyle Hidden`（已知坑）
- **Watchdog 衝突**：而家 cron watchdog 會自己起 serve——8.1 之後要改成「由 Electron 管」，watchdog 只監察 Electron main（或者 sidecar 由 Electron restart）
- **settings.json 共用**：兩個 process 讀寫同一個檔——8.2 之後統一由 sidecar/Python 管，Electron 經 IPC
- **MCP env 過濾**：MCP subprocess 只繼承安全 baseline——sidecar 要嘅 key 喺 Electron env 明確加
