# AGENTS.md — JARVIS ONE（jarvis-pc + jarvis-hud）

> 本檔係 jarvis-pc 專案嘅 Agent context——**任何做 JARVIS 相關任務嘅 agent 都要先讀**。
> 老闆：SK。回覆用**繁體中文**（專有名詞可原文）。人格見 `SOUL.md`（Hermes home 自動 load）。
> 來源：2026-08-29 從 master plan / REMAINING_WORK / HANDOFF 濃縮。更新時同步改 `.hermes/plans/` 文件。

## 專案簡介

**JARVIS ONE** = SK 嘅全方位 AI 語音助手（Iron Man JARVIS）。一個 Electron app（jarvis-hud）+ Python sidecar（jarvis-pc）。

```
┌─ jarvis-hud（Electron，`C:\Users\skps9\Documents\Code_Project\jarvis-hud`）────┐
│  main.js（tray + HUD overlay + Companion + Settings + media bridge）          │
│  renderer/index.html（HUD 全屏 overlay，Iron Man 視覺）                       │
│  companion.html / home.html / settings.html（共用 hud-theme.css）            │
└──┬── spawn ────────────────────────────────────────────────────────────────┘
┌─ jarvis-pc（Python sidecar，`C:\Users\skps9\Documents\Code_Project\jarvis-pc`）┐
│  `python -m jarvis serve`（wake/STT/TTS/AEC/聲紋/LLM）                       │
│  src/jarvis/（wake.py, mouth.py, ear.py, shell_app.py, settings.py,          │
│              alert_store.py, mcp_alerts_http.py, hermes_bridge.py,           │
│              speaker_gate.py, self_monitor.py, dpapi.py, mage_engine.py）    │
└────────────────────────────────────────────────────────────────────────────┘
```

## 關鍵路徑（勿寫錯）

| 項目 | 路徑 |
|---|---|
| Sidecar Python | `C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe`（**必須 `env -u PYTHONPATH` 跑**） |
| Sidecar src | `C:\Users\skps9\Documents\Code_Project\jarvis-pc\src` |
| Electron app | `C:\Users\skps9\Documents\Code_Project\jarvis-hud` |
| Settings 檔 | `%APPDATA%\Jarvis\settings.json` |
| Host config | `%APPDATA%\Jarvis\host.json`（python/jarvis_pc_dir） |
| MCP token | `%APPDATA%\Jarvis\alerts\mcp_token.txt` |
| Alerts queue | `%APPDATA%\Jarvis\alerts\queue.jsonl` |
| Activity state | `C:\Users\skps9\AppData\Local\hermes\state\sk_activity.json` |
| Plans | `C:\Users\skps9\Documents\Code_Project\jarvis-pc\.hermes\plans\` |
| Skill 陷阱 | `hermes-windows-operations`、`jarvis-hud-electron-editing-pitfalls`（§26 dock）、`electron-windows-overlay` |

## 現行版本（2026-08-29）

- **JARVIS ONE 0.4.10**：`jarvis-hud\dist\JARVIS-ONE-0.4.10.exe`；Desktop/Startup/Start Menu 3 個 .lnk 全指呢個
- **Dock 已移除**（0.4.9）：dock.html/dock-preload/probe/apps.json 刪晒；音樂控制搬 tray「音樂控制」submenu；media bridge 8771 + Chrome extension 保留
- **Secrets DPAPI**（0.4.10）：settings.json 嘅 llm/asr/mimo_api_key 加密（prefix `dpapi:`）；load 解密/save 加密；Electron settings:load 經 sidecar `GET /settings`；`alerts_mcp_token`+`hermes_api.key` 保持明文
- **Alert push**：sidecar `hermes_alert_poll_loop.py`（pythonw，~1s，peek→TTS→ack）——**唔好加 Hermes cron poll**（會 race/double speak）
- **vc_fail_closed**（0.4.10）：pycaw 失效時可選 fail-closed mute

## Ports

- **8765**：alerts MCP（sidecar）+ `GET/POST /settings`（Bearer = mcp_token.txt）
- **8770**：reply server（Electron）
- **8771**：media bridge（Chrome extension 控制 YouTube）
- **8642**：Hermes API（hermes_bridge 用）

## Commands

```bash
# 語法檢查（sidecar）
env -u PYTHONPATH python -m py_compile src/jarvis/*.py
# Electron 語法
node --check "C:/Users/skps9/Documents/Code_Project/jarvis-hud/main.js"
# ⚠️ 改動後 CI gate（Self-Evol，**必須**）：skill jarvis-self-evol-ops
env -u PYTHONPATH python -m jarvis.eval_gate --lock   # golden-set.md ↔ mapping 防 drift
env -u PYTHONPATH python -m jarvis.eval_gate --all    # golden + regression + stress
# 換版（照 skill jarvis-hud-electron-editing-pitfalls §21/§26）
#   bump package.json version → npm run dist → kill JARVIS → 開新 exe → 更新 3 個 .lnk
# 重啟 sidecar：kill 8765 嘅 python → Electron 自動 respawn（~90s）
# Settings 單一 writer：改 settings 用 sidecar `POST /settings`（Bearer），唔好直接寫檔
# MCP tools（8765）：jarvis_clarify_gate（EVPI 問唔問）/ jarvis_autonomy_state（自主度）——
#   加咗新 tool 要 restart sidecar 先生效
```

## 狀態速覽（2026-08-29 晚）

- ✅ 完成：Phase 1-8（語音/wake/AEC/聲紋/Mage-VL/alert/settings Electron 化/HUD/Media Bridge）、H1-H4（host config/settings 單一 writer/health/DPAPI）、D1/D2、F1-F5、A1-A4、B、E1-E3
- 🟡 等 SK：G 人手實測（BGM 誤觸/聲紋 enrollment/AEC voice call/Settings tab）、C 擴展連接（WhatsApp/Telegram/Hue credentials）
- ⏳ 可選：Iron Man 視覺完整化、自訓 wake「jarvis」、Discord 回覆 voice out、HWiNFO SHM/GPU-Z failover（D3）
- 📄 詳情：`jarvis-pc\.hermes\plans\JARVIS_MASTER_PLAN.md` + `REMAINING_WORK.md` + `HANDOFF.md`（固定檔，舊版喺 archive）+ `2026-08-29-fragility-review-pass2.md`

## 坑（Gotchas）

- 音訊：Arctis Nova 7 mic（wake_mic=麥克風 (2- Arctis Nova 7) 44.1k）；TTS 輸出=G27Q 螢幕喇叭；AEC reference=Sonar Media+Sonar Chat（**唔可用 Arctis loopback**）；Arctis 週期性 rms=0.000（headset 休眠，叫唔醒先睇 wake_debug.log）
- 語音一律英文（AGENTS.md 語音規則）
- `jarvis serve` 由 Electron spawn（JARVIS_ELECTRON_HOST=1 headless）；唔好手動起第二個
- asar 驗證：`npx --yes @electron/asar list "dist/win-unpacked/resources/app.asar"`（唔好 extract 入 repo，會 overwrite source——jarvis-hud 唔係 git repo）
- Windows MSYS：`taskkill /F` 用單斜線；native tool 用 `C:/...` forward-slash path
- GUI 操作前先讀 sk_activity.json（playing/using 禁彈窗）；語音/彈窗零容忍
- Secrets：`dpapi:` 值唔好當明文讀；settings.json 已加密

## Definition of done

- 需求每項有結果 + 工具證據
- 該專案 lint/syntax/test 已跑（py_compile / node --check）
- 無 secrets 外洩、無未核准破壞
- JARVIS 改動完成後更新 `.hermes/plans/REMAINING_WORK.md` + HANDOFF（如有）
