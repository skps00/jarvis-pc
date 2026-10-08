# Plan: HUD sidecar spawn-失敗之後永遠唔再 spawn（bug fix，v0.4.11）

日期：2026-09-16｜狀態：待 review → 派 cursor 實作
相關：`hud/main.js`（`spawnSidecar`／`startSidecarHealthCheck`／`ensureSidecar`／`stopSidecar`）

## 1. 背景 + 根因（A 級證據，2026-09-16 實測）

今日 07:41 Hermes gateway 因 Surfshark 防毒誤判（`Drop.Win64.UserProfileSelfRun.710`）刪走 uv
CPython 3.11 `python.exe` 而 crash loop；同時 `%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe`
亦消失（同類事件）。08:2x 我修好 python.exe 之後，**JARVIS sidecar（8765）仍然唔返**。

**時序（反方 review 後修正；原文有兩處唔準確）**
- 07:39 開機 → 07:44:11 HUD（login autostart）`ensureSidecar` → ENOENT #1
- **07:47:08 SK 重新啟動部機**（System log：User32 07:47:08／EventLog stopped 07:47:19／Kernel-Power
  07:47:24／開機 07:48:05）→ HUD 進程係跟機死，**唔係自己 crash**（反方一度懷疑 app 自殺，已用 boot 紀錄排除）
- 07:49:23 HUD 再 autostart → 07:49:26 ENOENT #2 → **之後永久靜**
- **第三條 launch path（新增發現）**：Startup `JARVIS.vbs` → `pythonw.exe -m jarvis serve`
  （無 `JARVIS_ELECTRON_HOST=1`、無 stdout 重定向）→ `wake_debug.log` 見到 07:44:20／07:49:34 兩個 session，
  各活 ~2-3 分鐘、**唔係 HUD 拉起**。即 07:44–07:52 之間其實短暫有過 sidecar（原因未明），
  HUD 嗰兩次 ENOENT 只係另一條路徑嘅失敗。
- **真正冇 sidecar 嘅窗口**：07:52:35 → 08:40:18 ≈ **47m43s**（唔係原本寫嘅「2+ 小時」）；
  08:29 python.exe 修好之後 HUD 帶住有效 interpreter **約 10 分鐘完全冇自救**，要我 08:40 手動重啟
- 即時 recovery：`taskkill /F /IM "JARVIS ONE.exe"` ＋ 重開 portable exe → sidecar 幾秒內起返
- 註（08:35 實測）：**呢條 path 令 8765 可能被「非 HUD 起嘅 sidecar」佔住** —— HUD 嘅 `sidecarRunning()`
  會當佢健康（唔會 spawn），而 `stopSidecar()` 殺唔到佢（app 退出後留 orphan）。屬已知限制（見 §8）。

**根因**：`spawn()` 失敗（ENOENT）時 Node **只 emit `'error'`（＋`close`），唔會 emit `'exit'`**，
而清 `sidecarProc` 嘅邏輯寫喺 `child.on('exit', …)`（main.js:124-133）→ `sidecarProc` 永遠留住嗰個
死 child → `spawnSidecar()` 開頭 `if (sidecarProc && !sidecarProc.killed) return;`（:98）**永久 early-return**；
health check（:139-153）見到 `sidecarProc` 非 null 只會 `sidecarProc.kill()`（**對已死 child 無效：
實測 `kill()` 回 false、`killed` 保持 false、唔 emit error**）→ **sidecar 永遠拉唔返，即使底層原因已修好**。
呢個就係「HUD 有 watchdog 但唔 work」嘅真身。

**實測 predicate（我親自用本機 Electron binary 量度：`ELECTRON_RUN_AS_NODE=1 electron.exe probe.js`，
Electron 33.4.11 / node v20.18.3；反方喺 Node 24.16.0 亦一致）**
```
ERROR code=ENOENT errno=-4058 syscall="spawn C:\nope\nope\python.exe" pid=undefined exitCode=-4058 killed=false
CLOSE code=-4058 pid=undefined exitCode=-4058 killed=false
exitCode after 2s: -4058   kill() returns false
```
→ 三個必須記住嘅事實：
1. **`err.syscall` 係 `"spawn <path>"`（連路徑），唔係 `'spawn'`** → 寫 `err.syscall !== 'spawn'` 會永遠成立、
   直接把 handler 廢掉（我 round 2 就係咁中過，實測退化成 76s 內只試 1 次）。
2. **唔會 emit `'exit'`**（只有 `'error'` ＋ `'close'`）→ 清 ref 一定要喺 `'error'` 做。
3. 「child 活住」嘅可靠判斷係 **`exitCode === null`**（`killed` 唔可信）；「spawn 從未成功」嘅可靠判斷係
   **`child.pid === undefined`**（同 Node 版本／syscall 字串格式無關）→ clear-ref ＋ retry 只用呢個條件，
   其他 error（kill 失敗／IPC）保留 ref 交 health check 決定。

## 2. 範圍（逐項）

1. **`spawnSidecar()`：加 `error` 處理**（核心修）
   - `child.on('error', (err) => { … })`：寫 `%APPDATA%\Jarvis\hud_error.log`（ISO＋stack）
     ＋ **predicate = `child.pid === undefined`**（spawn 從未成功）先 identity-check 清 ref
     ＋ 共用 5s respawn timer（`scheduleSidecarRespawn`）。**唔用** `err.syscall === 'spawn'`
     （實測係 `"spawn <path>"`；round 2 退化）。
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

## 8. 反方 review 補充（2026-09-16）＋ 量度修正 ＋ 已知限制

**Review verdict：FIX-FIRST**（根因機制判斷正確、方向正確）。已吸收：
- §1 敘事修正（見上：07:47 係 SK 重啟部機、第三條 launch path、真窗口 47m43s、predicate 實測值）
- 核心 predicate 明文（`exitCode === null`；`killed` 唔可信）
- 避免 kill 失敗時甩 ref → orphan 佔 8765：**唔可以用 `err.syscall === 'spawn'`**（round 2 咁寫 → 實測退化）
  → 改用 **`child.pid === undefined`**（round 3）。過程：round 2 上線 0.4.12 之後我跑 phase B，
  見到 **76s 內只試 1 次**（round 1 係 3 次）→ 即刻用 Electron binary 量 `err.syscall` → 發現係
  `"spawn <path>"` 而唔係 `'spawn'` → round 3 修正。**呢個就係「自己實測」嘅價值**（cursor 交嘅 code 同
  反方 review 都寫錯咗呢個值）。

**驗收量度修正（原文有 false-green 風險，要講清）**
- Phase A（舊 code）窗口 70s **短過** health check 嘅 90s 週期 → 「永久靜」唔可以單靠呢個窗口證明。
  真正證據＝生產紀錄：07:49:26 ENOENT 之後到 08:40:18 手動重啟前完全冇返（≈50 分鐘）。
- 節奏實測（新 code）：**3 次快速嘗試（t≈0/5/10s）→ crash-loop rate limit 停 retry 鏈 → 之後由
  90s health check 接手**（Phase C 恢復實測喺 t≈95s）。準確講法係「3 次快試 ＋ 每 ~90s 一次」，
  唔係「持續重試」。
- `/health` JSON **唔可以逐字比對**（實作回 `{ok, service, ts, wake_on}`；`wake_on` 可以係 null）。
- dev-instance 測試**冇真隔離**：`%APPDATA%\Jarvis`（`hud_error.log`／`serve.log`）同 8765/8770/8771
  係共享資源；今次 cleanup 有實測失敗過（08:46 `restore` 冇殺到 dev instance，8765 一度要人手救返）。
  harness 已改用 `jarvis_kill_dev.ps1`（command line 過濾 PID）＋每 phase 後核對 8765 owner。
- **正常 `exit` 路徑回歸測試（09:36 新增，PASS）**：kill 真 sidecar（PID 38824）→ **12.3s** 後自動 respawn
  （PID 41240、`/health` 200 `wake_on:true`），HUD 進程不變、`hud_error.log` 冇新增 error 行 →
  證明核心修補冇破壞原有 respawn。

**已知限制（記錄，未修／未驗，風險已知）**
1. **第三條 launch path**：Startup `JARVIS.vbs` 起嘅 sidecar 唔受 HUD 管；HUD 會當佢健康、
   `stopSidecar()` 又殺唔到 → app 退出後可能留 orphan 佔 8765。（建議日後用 ownership 判斷：只認有
   `JARVIS_ELECTRON_HOST=1` 或自己 spawn 出嘅 pid。）
2. sidecar 啟動慢（STT 預載）期間，health check 可能短暫雙 spawn；唯一防線係 1.5s HTTP 探測。
3. tray balloon（`crashLoopNotified`）喺 `createTray()` 之前觸發會靜默失效（既有問題）。
4. `stopSidecar()` 期間 pending retry 唔會 leak timer（有 `sidecarStopping` guard），但**冇測試**。
5. `hud/package.json` `build.files` 白名單：本次修補冇加新檔（已遵守）；日後如抽 module 必須同步白名單
   ＋跑 asar 檢查。
6. EACCES／EPERM 類（防毒 block 而唔係刪檔）會令新 retry 變熱循環；現時只靠 rate limit 擋。

## 9. 最終狀態（2026-09-16 10:00）

- **0.4.13** 已 build（`BUILD_EXIT=0`）＋部署＋3 個 `.lnk` 更新；`8642`／`8765`／`8770`／`8771` 正常、
  0 個可見 console 窗、`host.json` 完好、`.abtestbak` 已清。
- Harness 修正後重跑（0.4.13）：**phase B = 3 次嘗試**（12 行 error log，同 0.4.11 一致）、
  **phase C = interpreter 出現後 +115s `8765` 200、0 條新 error** → 快試 ＋ 90s health check 兩條路都 work。
- 版本軌跡：0.4.11（核心修）→ 0.4.12（predicate 寫錯，實測退化）→ **0.4.13（正確 predicate，已驗證）**。

**Harness 自身兩個 bug（已修；值得記錄——否則會出「假綠」）**
1. `kill_real()` 冇 assert 8765 真正 free → dev instance 見到 8765 健康 → 根本唔 spawn → 全程「綠」但乜都冇測。
   修：kill 之後用 netstat 核實、有 listener 就 taskkill PID、最多重試 10 次。
2. `prepare()` 見舊 `.abtestbak` 存在就唔搬 `host.json` → dev instance 讀到真 python path、拉起**真 sidecar**
   → 又係假綠。修：永遠搬走（先刪舊 bak），`restore()` 負責清 `.abtestbak`。
- 另外：Hermes cron `jarvis-sidecar-health`（每 2 分鐘）會把死咗嘅 sidecar 拉返／報狀態 → 做 HUD 隔離測試時
  要**先暫停**（`cronjob pause 6a98a79be95f`），測完 resume（今次做過）。
- 教訓：**測試 harness 嘅前置條件一定要 assert（唔可以假設）**——兩次「冇 ENOENT、8765 一直 200」
  其實都係環境干擾，唔係 code 行為。
