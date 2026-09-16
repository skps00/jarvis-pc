# Plan: HUD sidecar spawn-失敗之後永遠唔再 spawn（bug fix，v0.4.11）

日期：2026-09-16｜狀態：待 review → 派 cursor 實作
相關：`hud/main.js`（`spawnSidecar`／`startSidecarHealthCheck`／`ensureSidecar`／`stopSidecar`）

## 1. 背景 + 根因（A 級證據，2026-09-16 實測）

今日 07:41 Hermes gateway 因 Surfshark 防毒誤判（`Drop.Win64.UserProfileSelfRun.710`）刪走 uv
CPython 3.11 `python.exe` 而 crash loop；同時 `%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe`
亦消失（同類事件）。08:2x 我修好 python.exe 之後，**JARVIS sidecar（8765）仍然唔返**：

- `%APPDATA%\Jarvis\hud_error.log` 只有兩行、相隔 ~5 分鐘：`Error: spawn …pythoncore-3.14-64\python.exe ENOENT`
  （07:44:11、07:49:26）→ 之後完全靜晒。
- `netstat` 8765 一直冇 LISTEN；`main.js` 30s health check / 90s force respawn 完全冇作用。
- 即時 recovery：`taskkill /F /IM "JARVIS ONE.exe"` ＋ 重開 portable exe → sidecar 幾秒內起返。

**根因**：`spawn()` 失敗（ENOENT）時 Node **只 emit `'error'`（＋`close`），唔會 emit `'exit'`**，
而清 `sidecarProc` 嘅邏輯寫喺 `child.on('exit', …)`（main.js:124-133）→ `sidecarProc` 永遠留住嗰個
死 child → `spawnSidecar()` 開頭 `if (sidecarProc && !sidecarProc.killed) return;`（:98）**永久 early-return**；
health check（:139-153）見到 `sidecarProc` 非 null 只會 `sidecarProc.kill()`（對已死 child 無效）→
**sidecar 永遠拉唔返，即使底層原因已修好**。呢個就係「HUD 有 watchdog 但唔 work」嘅真身。

## 2. 範圍（逐項）

1. **`spawnSidecar()`：加 `error` 處理**（核心修）
   - `child.on('error', (err) => { … })`：identity-check（`if (sidecarProc === child) sidecarProc = null`）
     ＋ 寫 `%APPDATA%\Jarvis\hud_error.log`（同 `uncaughtException` handler 同格式，ISO timestamp ＋ stack）
     ＋ 用**同一個 5s respawn timer 路徑**排重試（`sidecarRespawnTimer`；排之前 clear 舊 timer，避免疊）。
   - 重試前一樣要 `sidecarRunning()` 檢查（8765 可能已由其他途徑起返）。
2. **`spawnSidecar()` 早退條件收緊**：`if (sidecarProc && !sidecarProc.killed && sidecarProc.exitCode === null) return;`
   ——即使有殘留 ref（任何未預期路徑），已退出嘅 child 唔可以再擋住 respawn。
3. **`startSidecarHealthCheck()`**：kill 分支唔變；但 `sidecarProc` 已死（`exitCode !== null`）時
   直接 `sidecarProc = null; spawnSidecar();`（唔好 call `.kill()` 當做過嘢）。
4. **唔改**：`stopSidecar()`、crash-loop rate limit 語意（≥3 spawns/60s → back off 60s）、
   `ensureSidecar()`、`windowsHide`／`JARVIS_ELECTRON_HOST` env、`fs.closeSync(out)` FD 處理、
   mediaBridge/replyServer/activity 等所有其他功能。**唔加新依賴、唔加新檔（如非必要）**。

## 3. 非範圍

- 唔改 sidecar Python（`src/jarvis/*`）。
- 唔改 Hermes watchdog（另見 `2026-09-16-hermes-gateway-watchdog-hardening.md`）。
- 唔做「防毒誤判」補救（Surfshark 排除目錄係 SK 手動做）。

## 4. 驗收標準（要實際跑，唔可以只 `node --check`）

1. `node --check hud/main.js` → OK。
2. **A/B 對照（我用 dev instance 跑，唔用真身 app）**：
   - 裝置：`hud` 目錄 `JARVIS_PYTHON=<不存在路徑> JARVIS_PC_DIR=<repo> electron . --user-data-dir=<temp>`
     （先 `mv %APPDATA%\Jarvis\host.json` 去 .testbak，令 env 生效；測完還原）。
   - **A（修前，negative control）**：只會見到 **1** 個 ENOENT、之後永遠靜 → 重現 bug。
   - **B（修後）**：ENOENT 之後**持續重試**（60s 內 ≥2 次 spawn 嘗試、hud_error.log 繼續有新行），
     且 8765 一有得 bind 就停（rate-limit back off 行為照舊）。
3. **Recovery 測試（修後）**：dev instance 用 `%TEMP%\jarvis_test_py\python.exe` 起（該檔唔存在）→ 確認 retry 中；
   然後 copy 一個真的 python runtime（`python.exe`＋`python*.dll`＋`vcruntime*.dll`，~7MB）落該目錄 →
   **唔重啟 app** 下，下一個 retry cycle 應該成功 spawn（log 唔再出 ENOENT）。
4. `npm run dist` 出 `JARVIS-ONE-0.4.11.exe`（package.json version bump）→ 真機換版：
   `taskkill /F /IM "JARVIS ONE.exe"` ＋ `taskkill /F /IM "JARVIS-ONE-0.4.1*.exe"` → 開新 exe →
   `Get-Process` 見到新 `JARVIS ONE`／`JARVIS-ONE-0.4.11`、8765/8770/8771 LISTEN、
   `http://127.0.0.1:8765/health` = `{"ok":true,"wake_on":true}`。
5. 三個 .lnk（Desktop／shell:startup／Start Menu\Programs）TargetPath 更新指 0.4.11（用 .ps1 + `-File` 跑）。
6. 零可見 console 窗（`Get-Process python,pythonw | Where MainWindowTitle -ne ''` = 空）。

## 5. 風險／最壞情況／還原

- 風險：改 `spawnSidecar` 影響「正常路徑」嘅 sidecar 生死管理（最壞＝反覆 respawn 或雙 serve）。
  → 靠 #2 早退條件（`exitCode === null` 才當活）＋ identity-check ＋ rate limit 守住；驗收 #4 睇 `netstat`
  只有一個 8765 listener。
- 最壞情況：新版 HUD 唔能起 sidecar → 即時用舊 exe rollback（`dist\JARVIS-ONE-0.4.10.exe` 保留），
  真身 app 可以 `taskkill` ＋ 開舊 exe，30 秒內回到現狀。
- 還原：`hud/main.js` 有 git（commit 前 diff 可審）；產物 exe 新舊並存，唔覆蓋舊 version。

## 6. 未解／已知限制

- HUD portable exe 長 uptime（>24h）會靜默唔開 HUD window（skill §27）——**唔喺本 plan 範圍**，
  但換版後順便觀察。
- Surfshark 仲有權再刪 `python.exe` → 未加排除目錄之前，同一故障會再發生（會由 Hermes watchdog 自癒計劃覆蓋）。

## 7. 驗收結果（2026-09-16 09:0x，全部實測）

| 步驟 | 結果 |
|---|---|
| `node --check hud/main.js` | OK |
| **Phase A**（舊 code ＋ bogus interpreter） | ENOENT **只 1 次**，之後 70s 全靜、8765 一直 down ＝ **bug 重現** |
| **Phase B**（新 code ＋ bogus interpreter） | 11s 內 **3 次** spawn 嘗試（12 行新 log），之後按 crash-loop 退避 60s |
| **Phase C**（新 code，interpreter 25s 後出現） | t≈95s sidecar **自動起返**：`8765 /health` 200 `{"ok":true,"wake_on":true}`，**全程冇重啟 app** |
| Build | `JARVIS-ONE-0.4.11.exe`（72,577,621 B，`BUILD_EXIT=0`） |
| 換版 | kill 0.4.10 → 開 0.4.11 → 5 進程、8765/8770/8771 LISTEN、health 200 |
| .lnk ×3 | Desktop／Startup／Start Menu 全部更新指 0.4.11 |
| 零彈窗 | 冇任何 visible console（`MainWindowTitle -ne ''` 空）；換版全程用 VBS hidden-console wrapper |

Harness：`%TEMP%\hud_sidecar_ab_test.py`（phases a/b/c/restore）；換版／build 用
`%TEMP%\run_hidden.vbs`（`wscript` → `sh.Run(...,0,...)`，整條鏈共用一個 hidden console）。
未做：SK 真機主觀驗收（語音／wake 正常與否）。
