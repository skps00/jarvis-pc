# PR #13 Code Review — feat(jarvis): 0.4.14 sidecar restart-loop fix + pytest test isolation

- **Reviewer**：Hermes（2026-10-07，SK 指示）
- **PR**：`skps00/jarvis-pc#13`，base `main` ← `feature/hermes-alerts-mcp`；**42 檔、+5048/−1060**、196 commits、`mergeable: true`
- **範圍**：`git diff origin/main...HEAD`（本地 `main` 落後，用 `origin/main` 為準；PR 頁數字一致）
- **方法**：讀全份 diff（code 檔 924 行）＋對源碼／live 服務核實 ＋跑新／改動過嘅測試
- **Verdict**：**Request changes（2 warning）** — 兩個都係細改，改完可以 merge

---

## 實測證據（本輪親跑）

| 檢查 | 結果 |
|---|---|
| `/health` payload 一致性（PR 新判準 `ok:true && service:"jarvis"`） | **live 實測** `HTTP 200 {"ok":true,"service":"jarvis","ts":1791365809,"wake_on":false}` ✅ 判準唔會誤殺 |
| 新測試 `test_control_http_probe.py`＋`test_sidecar_health_monitor.py`＋`test_test_isolation.py` | **19 passed**（8.94s）✅ |
| 改動過嘅測試（self_review／settings／alert_keys／ui_smoke／brain／shell_app） | **74 passed / 1 failed** |
| 嗰 1 紅 | `test_settings_ui_smoke.py::test_settings_window_builds_five_tabs` → `ModuleNotFoundError: numpy`。**main 版本同樣會紅**（同一 test 存在於 main；`numpy` 係 `pyproject.toml` 已聲明依賴但環境未 sync）→ **唔係 PR 引入** |
| Secrets 掃描（`token=`／`password`／`api_key` 等） | 0 hit ✅ |
| Debug leftovers（`print(`／`console.log`／`TODO`／`debugger`） | 只有 watchdog 一行必要 `print(line)`（cron fingerprint 設計要求）✅ |
| Merge conflict markers | 無 ✅ |

---

## 🔴 Critical

無。

---

## ⚠️ Warnings

### W1 — `settings_ui.py` 仍然用舊常數，PR 令佢變 stale（行為不一致）
- **位置**：`src/jarvis/settings_ui.py:29-30`（import `SETTINGS_DIR`, `SETTINGS_PATH`）、`:238`（「存檔 → {SETTINGS_PATH}」）、`:656`（「開資料夾」button）、`:667`（info text）
- **問題**：本 PR 將 settings 路徑改成 **call-time resolution**（`settings_dir()`／`settings_path()`：`JARVIS_SETTINGS_DIR` → `APPDATA` → fallback），但 `settings_ui.py` 仲係讀 module-level 常數 `SETTINGS_DIR = Path.home()/"AppData"/"Roaming"/"Jarvis"`。→ 只要 override 生效（**測試就係咁做**；將來 portable mode 都會），UI 顯示／「開資料夾」會指去**真正嘅生產目錄**，而 app 其實讀寫另一個目錄。
- **影響**：UI 誤導（顯示錯誤路徑、開錯 folder）；測試環境下會打開用家真目錄。生產正常路徑下巧合一樣，所以唔會即刻爆 — 但呢個正正係 PR 想消滅嘅「靜靜唔一致」。
- **建議修法**：`settings_ui.py` 改用 `settings_path()`／`settings_dir()`（render 時 call），或者索性刪走 `SETTINGS_DIR`／`SETTINGS_PATH` 兩個常數，令所有 caller 一定要用函數。
- **驗收**：`SETTINGS_PATH` 全 repo 只剩 `settings.py` 內部（或 0 處）；設 `JARVIS_SETTINGS_DIR` 開 UI，顯示路徑要跟 override。

### W2 — watchdog 會將「列進程失敗」當成「刻意關機」，靜靜蓋住真故障
- **位置**：`tools/jarvis_sidecar_health.py:809-850`（`_process_rows()` → `_is_intentional_off()` → `_fingerprint()` 出 `OFF`）
- **問題**：`_process_rows()` 遇到任何失敗（`OSError`／`CalledProcessError`／`TimeoutExpired`／JSON decode）都 `return []`。`/health` 失敗時會行 `_is_intentional_off()`：見唔到 HUD、又見唔到 `jarvis serve` → 回 `OFF`（＝靜默，冇 alert）。即係 **PowerShell 一時慢／timeout（20s；部機忙時完全可能）就會將「真係死咗」誤判成「用家自己熄咗」**，cron monitor 因為 fingerprint 唔變而永遠唔響。
- **影響**：監控工具最差嘅失敗模式＝安靜咁失效（false negative），而唔係報錯。
- **建議修法**：分辨「列舉失敗」同「列舉成功但冇 match」——失敗時 raise／回 sentinel，`_fingerprint()` 見到就用 `DOWN <reason>`（例如 `DOWN enum_failed t=<5m>`），唔好當 OFF。
- **驗收**：加一個 test：mock `subprocess.check_output` raise `TimeoutExpired` → fingerprint 必須係 `DOWN…`，唔可以係 `OFF`。

---

## 💡 Suggestions（唔阻塞）

- **S1**：`self_review.py` 新增 `SUSTAINED-…` finding 同原本 `detect_trend()` 嘅 trend finding 會為**同一 metric** 各出一個 finding。兩者語意唔同（step-change vs 連續 3 日惡化），但報告讀者會見到疑似重複 → 建議喺 `summary` 互指，或統一 severity 語言。
- **S2**：`tools/jarvis_sidecar_health.py` 內 `HEALTH_URL = http://127.0.0.1:8765/health` 硬編碼 8765。配合「port 已凍結」係正確，但呢個檔冇寫凍結理由（`main.js`／`settings.py` 都有註解）→ 建議加一句，防下一個改 port 嘅人再踩。
- **S3**：`_probe()` 將 `urllib.error.URLError(timeout)` 歸類做 `URLError`（唔係 `Timeout`）→ 診斷標籤略不準（無害）。
- **S4**（環境，非 PR）：`numpy` 已喺 `pyproject.toml` 聲明但環境未裝 → 1 個 test 紅。要 `uv sync`（未做，因為會郁依賴環境，等 SK 決定）。

---

## ✅ Looks good

- **根因修得準**：`_ensure_control_http()` 由 alert 開關抽出（`alert_voice=False` 唔再令 sidecar 看似死掉 → 90s kill/respawn loop）——正正對應 STATE 記錄嘅 2026-09-23 事故。
- **`/health` 判準前後一致**：Electron `sidecarRunning()`、shell `probe_control_http()`、watchdog `_probe()` 三把尺都係 `ok:true && service:"jarvis"`，而且**實測 live 回應符合** ✅。
- **`exitCode === null` 判斷**：正確區分「仲活着」vs「spawn 失敗（`exitCode=-4058`、`killed=false`）」，成功修好「失敗 child 卡住 respawn」；`child.on('error')` 用 `pid === undefined` 判斷而唔係 `err.syscall`，並附實測註解（Node 24 行為）→ 好。
- **log 輪替**（`appendActivityLog()` 10 MB + `.1`）用 try/catch 包住，寫唔到都唔會 throw／影響 HUD ✅。
- **settings cache 修正**：加 `_cache_path` 防「換咗路徑但 mtime 撞啱」而回錯 cache ✅；`_patch_lock_path()` 亦改為 call-time。
- **watchdog 設計符合 cron monitor 要求**：永遠一行輸出、fingerprint 無時間戳（只有 bucket 轉變才變字串）✅；state 寫入用 `os.replace` 原子換 ✅；`CREATE_NO_WINDOW` ✅。
- **測試**：新增 3 個檔、`eval_gate.GOLDEN_SUITES` 有同步加新測試 ✅；`conftest.py` 用 `JARVIS_SETTINGS_DIR` + fail-loud sentinel 做隔離 ✅。

---

## 建議（未執行，等 SK）

1. W1＋W2 兩處細改（我可以經 cursor-agent 做，改完補 test）→ 再 re-review
2. S4：要唔要 `uv sync`（會郁依賴環境）
3. 呢份 review 要唔要貼上 GitHub PR #13 做 review comment（repo 係 public → 貼＝對外發佈，要 SK 批）
