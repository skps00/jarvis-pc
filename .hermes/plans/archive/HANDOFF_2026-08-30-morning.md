# HANDOFF — JARVIS 交接（固定檔）

> **呢個係固定 handoff 檔**（2026-08-30 起）：每次 session 結束**更新呢份**，唔好開新日期檔；舊交接版本移入 `plans/archive/`。
>
> 下次 session 起點：**JARVIS ONE 0.4.10 跑緊**。讀呢份之前先讀：
> 1. `jarvis-pc\AGENTS.md`（專案 context，2026-08-29 新寫——**自動載入規則已寫入主契約，唔使 SK 叫**）
> 2. `C:\Users\skps9\AGENTS.md`（主契約——注意：**Code Review 兩次規則已升格入契約**）
> 3. `REMAINING_WORK.md` + `2026-08-29_self-evol.md`（新計畫）

---

## 現行狀態（2026-08-30 02:51 驗證）

- **JARVIS ONE 0.4.10**：`jarvis-hud\dist\JARVIS-ONE-0.4.10.exe`（唯一 exe，舊版全刪）；3 個 .lnk 全指佢
- **Hermes Desktop 已裝**：`AppData\Local\hermes\hermes-agent\apps\desktop\release\win-unpacked\Hermes.exe`（Electron 40.10.2）
  - **Quick Entry hotkey 已改：Ctrl+Shift+Space → Ctrl+Shift+Y**（`%APPDATA%\hermes\quick-entry.json`）
- **WeSight 已 uninstall**（2026-08-30 凌晨）：Programs + Roaming + registry + `.hermes-wesight-bak` + Temp 殘留全清
- Ports：8765（alerts MCP + GET/POST /settings）、8770（reply）、8771（media bridge）、8642（Hermes API）、Hermes Desktop 自己 serve（port 隨機，同 8642 並存）
- cron：sk-activity-monitor（1m）+ Gateway watchdog（2m）——**冇 JARVIS alert cron**（sidecar poller 做緊，唔好加）

## 目錄統一（今日大掃除後嘅最終結構）

```
C:\Users\skps9\AppData\Local\hermes\     ← Hermes 唯一家（SOUL.md/config/skills/cron/state）
C:\Users\skps9\AGENTS.md                  ← 主契約（唯一有效 AGENTS.md；含語音規則/活動Gate/Code Review 兩次/JARVIS 自動載入）
C:\Users\skps9\Documents\Code_Project\    ← 測試/開發區
  ├─ Hermes\                              ← 規則包源頭（由 Documents\Hermes 搬入；已同步最新）
  ├─ jarvis-pc\  jarvis-hud\              ← JARVIS ONE
  ├─ super_minecraft_AI_player\（+3 worktree 分支，SK 話仲用緊，唔好刪）
  ├─ Earth_Online_App\  Earth Online App\（日誌路徑，AGENTS.md 有引用，唔好刪）
  └─ CS_asstant\ 等
```

**冇咗嘅**：`~/.hermes`（WeSight 殘留）、`Documents\Hermes`、舊 JARVIS exe（0.3.1-0.4.9，762MB）、settings/config 舊備份、`NA\` 空目錄、`AppData\Local\hermes\AGENTS.md`（語音規則併入主契約）

## 今日完成（2026-08-29 晚 → 8-30 凌晨 session）

### JARVIS ONE
1. **Dock 移除（0.4.9）**：dock.html/dock-preload/probe/apps.json 刪晒；main.js dock 全清（grep 0）；音樂控制搬 tray「音樂控制」submenu；media bridge 8771 + Chrome extension 保留
2. **H4 secrets DPAPI（0.4.10）**：`src/jarvis/dpapi.py`（ctypes CryptProtectData，prefix `dpapi:`）；settings.json llm/asr/mimo_api_key 已加密；load 解密/save 加密；sidecar `GET /settings`（解密版）+ Electron settings:load 改經 sidecar；**alerts_mcp_token + hermes_api.key 保持明文**（跨 process bearer，encrypt 會 break——見 `docs/hermes_bridge_auth_rotation.md`）
3. **F3 vc_fail_closed（0.4.10）**：settings 加 `vc_fail_closed`（default False=fail-open）；activity_monitor pycaw 失敗讀 settings 決定；settings.html toggle + clampSettingsPatch 已加
4. **D1 確認**：Hermes push/notify 已由 sidecar 2s poller 完成（`scripts/hermes_alert_poll_loop.py`）——**唔好加 Hermes cron poll**
5. **A3 尾**：renderer 視覺確認已統一（同一 --blue/字體系），冇改動（刻意）
6. **H 節剩低全清**：settings field-map（custom_models 缺口已修）、auth rotation 文檔、tk settings_ui 凍結
7. **換版 0.4.10**：build + asar 驗證 + kill/開 + 3 .lnk 更新

### 系統/環境
8. **Hermes Desktop 裝好** + **Quick Entry hotkey 改 Ctrl+Shift+Y**（原 Ctrl+Shift+Space 喺 Roblox/遊戲會誤彈）
9. **WeSight uninstall**（唔係 Hermes 一部分，SK 冇用；佢寫嘅 `~/.hermes` 係 config-only 唔影響真身）
10. **AGENTS.md 統一**：主契約一份（含語音規則）+ 源頭 Code_Project\Hermes 同步；`AppData\Local\hermes\AGENTS.md` 刪
11. **jarvis-pc\AGENTS.md 新建** + 主契約加「JARVIS 專案自動載入規則」（SK 要求 auto import——下次 session 唔使叫，自動讀 plans）
12. **Code Review 兩次規則升格入主契約**（原本只喺 agent memory；SK 2026-08-29 確認）
13. **大掃除**：舊 exe 762MB、WeSight 殘留、settings/config 備份、NA/、SOUL.md.bak——共釋放 ~800MB+

## Self-Evol 計畫（新，等 SK 最終確認）

- 計畫檔：`jarvis-pc\.hermes\plans\2026-08-29_self-evol.md`
- 內容：Phase A 自我審視（每日趨勢分析 + 報告，純讀零風險）→ Phase B 能力擴展層（自動搜 hub + manifest 審查 + 安裝 gate）→ Phase C 閉環
- **三階段 review 已跑**（反方/正方/裁判）：
  - 結論 1：**全自動安裝 MCP 唔好做**（Invariant Labs Tool Poisoning 實證 + CVE-2025-49596 + 1,862 個公網無認證 MCP servers）
  - 結論 2：SK 決定 **Phase 1 = 安裝永遠人手**，full auto 推 Phase 2
  - 結論 3（最後更新）：**安全判斷唔應該靠 SK 知識**——用「信任分層」：🟢 官方 vendor URL-only（唔執行本地 code）｜🟡 Nous PR-reviewed catalog（唔使 SK 審，只答「要唔要」）｜🔴 Community skill（預設拒絕）
  - **等 SK 確認「信任分層」設計後先開始 Phase A**
- 反轉條件已滿足：#1 人手 gate（✅ 已決定）、#2 G 清單冇錢買 mic 做唔到（✅ 消解）、#3 有人測試過（✅ MCP 安全研究結論支持保守方向）、#4 未知（人手 gate 期間保險）

## 剩低（詳見 REMAINING_WORK.md）

- 🟡 **G 人手實測**（等 SK）：Tier 1（BGM 30s 0 誤觸 + 喊完→有聲 ≤3s）、聲紋 enrollment（**要買新 mic**——SK 話暫時冇錢）、AEC voice call、Settings tab
- 🟡 **C 擴展連接**（等 credentials）：WhatsApp / Telegram / Hue
- ⏳ **Self-Evol Phase A**（等 SK 確認信任分層設計後開始）
- ⏳ 可選：Iron Man 視覺完整化、自訓 wake「jarvis」、Discord 回覆 voice out、D3 HWiNFO SHM/GPU-Z failover
- 💤 deferred：Mage-VL streaming gate（mamba_ssm Windows 唔 practical）

## 陷阱（重溫）

- **Settings 單一 writer**：改 settings 用 sidecar `POST /settings`（Bearer = `%APPDATA%\Jarvis\alerts\mcp_token.txt`），**唔好直接寫 settings.json**（H4 後 secrets 加密，直接寫會寫壞）
- **dpapi:** 值唔好當明文讀；settings.json 已加密
- **jarvis serve** 由 Electron spawn（JARVIS_ELECTRON_HOST=1 headless）；唔好手動起第二個
- asar 驗證：`npx --yes @electron/asar list "dist/win-unpacked/resources/app.asar"`；唔好 extract 入 repo（會 overwrite source——jarvis-hud 唔係 git repo）；extract 去 /c/Temp
- Python：`C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe`，跑 jarvis 用 `env -u PYTHONPATH PYTHONPATH=...src`
- 換版流程：bump version → `npm run dist` → kill JARVIS（單斜線 taskkill）→ 開新 exe → 更新 3 個 .lnk
- 語音一律英文；GUI 操作前讀 sk_activity.json（playing/using 禁彈窗）
- **Code Review 兩次**（契約規則）：做完 code 改動 → pass1 刪重複/拆函數/補註釋/降耦合 → pass2 三個月後脆弱位

## 語音/硬體設定（驗證過）

- wake_mic = 「麥克風 (2- Arctis Nova 7)」44.1k；TTS 輸出 = G27Q 螢幕喇叭；AEC reference = Sonar Media + Sonar Chat（唔用 Arctis loopback）
- ⚠️ Arctis 週期性 rms=0.000（headset 休眠/斷連）——叫唔醒先睇 wake_debug.log
- mic 細（avg ~0.05）→ AGC 上線；wake_threshold 0.75（self-monitor 自動調出嚟）
