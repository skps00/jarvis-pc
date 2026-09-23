# JARVIS Sidecar 無限重啟循環 — 修復計劃

**日期**：2026-09-23
**症狀**：SK 打機時鍵盤輸入間歇性延遲（「隨機、唔係每次」）
**狀態**：根因已 100% 實測確認；**此計劃只做規劃，未改任何 code**

---

## Goal（一句話）

消除 `jarvis serve`（Python sidecar）每 ~90 秒被 Electron 殺掉重啟嘅循環，令系統唔再每 1.5 分鐘出現一次 CPU／磁碟 I/O 尖峰。

---

## 根因（Root Cause — 全部有實測證據）

### 證據鏈

| # | 證據 | 來源 |
|---|---|---|
| 1 | `hud/main.js:157-179` — 每 30 秒 fetch `/health`，**連續 3 次失敗（= 90 秒）→ `sidecarProc.kill()` → 重新 spawn** | 讀 code |
| 2 | serve 每次啟動都要 **下載／檢查 20 個模型檔案**（走網絡）＋載入 1.2GB（STT SenseVoice + TTS Piper） | `%APPDATA%\Jarvis\serve.log` |
| 3 | 實測重啟間隔：**14:34:26 → 14:35:56 → 14:37:29 → 14:38:58**（≈1.5 分鐘）；log 內共 **294 次**模型下載紀錄 | serve.log 時間戳 |
| 4 | 關掉 JARVIS ONE 之後 **100 秒內 `serve.log` 增長 = 0 bytes**（循環停止） | 本 session 實測 |
| 5 | SK 確認：「打字順返」 | SK 2026-09-23（message `1552234812281069569`） |

### 因果

```
serve 啟動需時 > 90 秒
   → Electron health check 3 次 miss（90 秒）
   → kill + respawn
   → 又需 > 90 秒 → 再被 kill
   → 無限循環（每 1.5 分鐘）
   → 每次重載 1.2GB 模型 = CPU + 磁碟 I/O 尖峰
   → 遊戲中輸入執行緒排隊 = 鍵盤延遲
```

### 為何最近才發生

每次啟動都要走網絡檢查模型（modelscope）+ 模型體積增加 → 啟動時間**跨越 90 秒臨界點**。之前啟動 <90 秒所以一直無事（符合 SK「以前冇」）。

---

## 業界做法（Research First — 有 source）

| Source | 內容 |
|---|---|
| Kubernetes 官方文檔 | *"Protect slow starting containers with startup probes"* / *"**Slow starters without a startup probe get killed by liveness instead**"* |
| AWS Auto Scaling 文檔 | *"**health check grace period** specifies the minimum amount of time to keep a new instance in service before terminating it"* |
| sokuji（Electron + Python sidecar 實例） | *"**Handshake Timeout: a 90-second watchdog** is used to account for [slow model loading]"* |
| Stack Overflow（agents 版）blueprint | *"**The model takes 30–60s to load** … keep one Python process alive you get warmth"* |
| Docker PR #28938 | 固定 grace period 難定 → 寧願長 |

**結論**：業界標準 = ①啟動期唔計 liveness fail（startup probe）②盡量縮短啟動（model warmth / 本地快取）。我哋兩樣都缺。

---

## 方案（3 個改動，逐個獨立可驗證）

### 改動 1（治標，立即止血）：main.js 加 startup grace period

**檔案**：`C:\Users\skps9\Documents\Code_Project\jarvis-pc\hud\main.js`

**現狀（157-179 行）**：spawn 之後即刻開始 30 秒健康檢查 → 90 秒就殺。

**改法**（照 K8s startup probe 概念）：
- spawn 時記錄 `sidecarSpawnedAt = Date.now()`
- health check 內加條件：**spawn 後 N 秒內（N = 由量測決定，暫定 300 秒）唔計 fail**
- 啟動期內改為只檢查「**進程仍然存活**」（`sidecarProc.exitCode === null`）——進程活住就唔殺
- ready 之後（首次 `/health` 成功）恢復現有 30 秒 × 3 次邏輯

**注意（skill §20 教訓）**：
- `exitCode === null` 係「仍然活住」唯一可靠判斷（`killed` 唔可信）
- kill 後**唔好即刻 spawn**（port 未 release → bind race）→ 保持現有 5 秒 respawn timer
- exit handler 一定要 identity-check（`if (sidecarProc === child)`）

### 改動 2（治本）：加速 serve 啟動

**檔案**：`C:\Users\skps9\Documents\Code_Project\jarvis-pc\src\jarvis\`（模型載入處，待定位）

**方向**：
- 模型下載改用**本地快取**（`local_files_only=True` / 已下載就跳過網絡檢查）
- 目標：啟動由 90+ 秒 → 10 秒內
- **先量測**（見 Task 0）確認時間花喺邊：網絡檢查 vs 模型載入 vs 音訊初始化

### 改動 3（順帶）：log 輪替

**檔案**：`hud/main.js`（`jarvis_hud_activity.log` 寫入處）
- 現時 `%LOCALAPPDATA%\Temp\jarvis_hud_activity.log` = **88 MB**（每 5 秒一行、從未輪替）
- 加：超過 N MB 就 rotate（保留 1 個舊檔）

---

## 執行步驟（bite-sized）

### Task 0：量測 serve 啟動時間（**必須先做**，決定 grace period 參數）
1. 確認 JARVIS 已關（`Get-Process | Where-Object { $_.Name -match '^JARVIS' }` → 空）
2. 確認 8765 free（`netstat -ano | grep ':8765'` → 無 LISTEN）
3. 手動 spawn serve 並計時：
   ```bash
   cd "C:/Users/skps9/Documents/Code_Project/jarvis-pc"
   PYTHONPATH=".../src" JARVIS_ELECTRON_HOST=1 \
     "C:/Users/skps9/AppData/Local/Python/pythoncore-3.14-64/python.exe" -m jarvis serve
   ```
4. 每 2 秒 poll `http://127.0.0.1:8765/health`，記錄「spawn → 首次 200」秒數
5. **同時記錄**：下載階段耗時 vs 載入階段耗時（由 log 時間戳）
6. 測完 kill，記錄數字入本 plan
7. **驗收**：拿到「啟動總秒數」+「網絡檢查佔幾多秒」

### Task 1：main.js 加 startup grace period
1. 改 `main.js`（**經 cursor-agent**，唔好手改）
2. `node --check hud/main.js`
3. Grep 驗證關鍵函數仍在：`whenReady|ipcMain|globalShortcut|mediaBridge|listen(8771|stopSidecar|spawnSidecar`
4. **驗收（negative control）**：用 dev instance + `JARVIS_PYTHON=<bogus>` 確認 ENOENT path 行為無回歸（照 skill §20 嘅 A/B harness）

### Task 2：加速模型載入
1. 定位模型載入 code（`grep -rn "snapshot_download\|AutoModel\|local_files_only" src/jarvis/`）
2. 改為本地快取優先
3. `env -u PYTHONPATH python -m py_compile src/jarvis/*.py`
4. **驗收**：重跑 Task 0 量測 → 啟動時間明顯下降

### Task 3：log 輪替
1. 改 `main.js` 寫入處加 size check + rotate
2. **驗收**：手動造一個 >上限嘅 log → 重啟 → 確認 rotate 發生

### Task 4：打包 + 換版 + 端到端驗收
1. bump `hud/package.json` version（例 0.4.13 → 0.4.14）
2. `npm run dist`（**必須經 VBS hidden-console wrapper，零閃窗** — skill `cursor-cli-integration`）
3. `scripts/swap_hud_version.ps1 -Version 0.4.14`（殺舊 → 開新 → 更新 3 個 .lnk）
4. 端到端驗收（見下）

---

## 驗收標準（開工前定好 — SK 規則）

| # | 驗收項 | 方法 | 通過條件 |
|---|---|---|---|
| 1 | **重啟循環消失** | 監測 `serve.log` 15 分鐘 | spawn **只 1 次**；無重複 "download models" 週期 |
| 2 | **健康持續** | poll `/health` | 連續 200，無中斷 |
| 3 | **CPU 無週期尖峰** | 每 10 秒採樣 `jarvis serve` CPU 15 分鐘 | 無 90 秒週期性尖峰 |
| 4 | **進程數穩定** | `Get-Process python \| grep jarvis` | PID 15 分鐘內不變 |
| 5 | **SK 主觀** | SK 打機打字 | 無間歇延遲 |
| 6 | **回歸：sidecar 死後仍能救援** | kill serve PID | ~90 秒內自動 respawn（skill §20 驗收） |
| 7 | **回歸：ENOENT path** | bogus python 路徑 | 有 error log + rate limit backoff（唔可以永久卡死） |

---

## 風險 / 還原

| 風險 | 影響 | 還原 |
|---|---|---|
| 改 `main.js` 引入新 bug | HUD 功能受損 | 舊 exe 保留（`dist/JARVIS-ONE-0.4.13.exe`）→ 重開舊版即可 rollback |
| grace period 太長，真死機唔重啟 | sidecar 死後長時間無服務 | 設上限（例如 300 秒後強制回復現行邏輯）；Task 5 驗收覆蓋 |
| 改模型載入影響 STT 準確度 | 語音辨識變差 | 只改「下載／快取」路徑，唔改模型本身；語音線本身 HOLD（等新 mic） |
| 打包／換版彈窗 | SK 打機中被打擾 | 全部經 VBS hidden wrapper；**SK idle 時才做** |

**現時狀態**：JARVIS ONE 已關（HUD／提醒暫停）→ 完成 Task 1 換版後才重開。

---

## 待答問題（執行前）

1. serve 啟動實際需時？（Task 0 量測）
2. grace period 用固定秒數，抑或等 serve 自己發 "ready" 訊號？（後者更準，但要 sidecar 配合——已 plan Task 2 改 sidecar，可一併做）
3. `jarvis_hud_activity.log` 上限定幾多？（建議 5 MB × 2 檔）

---

## Lessons（入 skill）

- Electron＋Python sidecar 架構：**health check 一定要有 startup grace period**（否則啟動慢就無限重啟 → 週期性全系統卡頓）
- 呢個 bug 嘅 signature：`serve.log` 出現重複「download models from model hub」週期 + SK 報「間歇性系統卡頓」
- 診斷入口：`serve.log` 嘅重複週期 + 進程 `StartTime` 一直變
