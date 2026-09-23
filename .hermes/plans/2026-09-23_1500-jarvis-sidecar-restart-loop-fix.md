# JARVIS Sidecar 無限重啟循環 — 修復計劃 **v2（經 review 修正）**

**日期**：2026-09-23（v1 → v2）
**狀態**：診斷已確認（v1 診斷**已被推翻並修正**，見「v1 錯咗嘅地方」）
**此計劃只做規劃，未改任何 code**

---

## Goal

消除 `jarvis serve`（Python sidecar）每 90 秒被 Electron 殺掉重啟嘅循環，令系統唔再每 1.5 分鐘出現 CPU／磁碟 I/O 尖峰（= SK 打機時鍵盤間歇延遲來源）。

---

## 根因（v2 修正版 — 全部有實測證據）

**核心錯配：Electron 用 8765 `/health` 做 sidecar 嘅「唯一」存活判準，但 8765 嘅存在取決於一個可選功能開關 `alert_voice`。**

```python
# shell_app.py:493
def _ensure_alerts_mcp(self, cfg: Settings) -> None:
    if not bool(getattr(cfg, "alert_voice", True)):
        return          # ← alert_voice=False → 8765 永遠唔會啟動
```

### 證據

| # | 證據 | 來源 |
|---|---|---|
| 1 | `settings.json`：**`alert_voice = False`**；與 `.bak-20260922_171207` diff：`alert_voice: True → False`、`voice_frontend: jarvis → hermes` | settings.json（mtime **09/22 17:33**） |
| 2 | `/health` 同 `/settings` 住喺**同一個 8765 server**；`serve_in_thread` 唯一 call site = `shell_app.py:504`（全 src grep 確認，冇第二條路開 8765） | code |
| 3 | **8765 最後一次真正服務 = 09/22 19:05:05**（serve.log 最後一條 `Processing request of type`）；之後冇任何一次啟動 bind 到 8765 | serve.log |
| 4 | 獨立測試 MCP server 本身 → **8 秒內 bind + /health 200**（server 冇壞） | 本 session 實測 |
| 5 | 獨立測試 bind 127.0.0.1:8765 → **BIND OK / CONNECT OK 0.000s**（唔係防火牆／端口阻擋） | 反方 reviewer 實測 |
| 6 | spawn serve 實測：**載入 4.4 秒完成**，之後 **100 秒以上冇 LISTEN**、CPU **0.7%**（= blocked，唔係 spin） | 反方 reviewer 實測 |
| 7 | cron monitor fingerprint 由 **09/22 19:10** 至今**冇變過**（一直 `DOWN URLError`）→ 監控盲點：唔會再發警報 | cron jobs.json |

### 完整因果鏈

```
09/22 17:33 SK 關咗 alert_voice（語音線 HOLD）
  → serve 啟動時 _ensure_alerts_mcp 立即 return → 8765 從來冇 LISTEN
  → Electron 每 30 秒問 8765「你仲在唔在？」→ 永遠問唔到（main.js:157-179）
  → 90 秒（3 次 miss）→ sidecarProc.kill() → 5 秒後 respawn
  → 每次重啟重新載入 STT（stt_preload=True，實測 1.04 GiB RAM）＋ TTS
  → 每 1.5 分鐘一次 CPU + 磁碟 I/O 尖峰
  → 打機時輸入執行緒排隊 = 鍵盤間歇延遲
```

**「以前冇」嘅答案**：09/22 17:33 之前 `alert_voice=True` → 8765 有起 → Electron 覺得健康 → 冇循環。

---

## v1 錯咗嘅地方（自我修正記錄）

| v1 講法 | 實情 | 影響 |
|---|---|---|
| 「serve 啟動需時 > 90 秒（下載 20 個模型檔走網絡）」 | **錯**。實測 20 檔檢查 **0.00 秒**（本地 cache 命中），整體載入 **4.4–16 秒**。問題係**啟動完之後永遠唔 bind 8765** | v1 改動 1（grace period）同改動 2（加速下載）**都係醫錯病** |
| 「log 內共 294 次模型下載」 | 實測 **300 次**（294 係截至 14:38:58 嘅過時快照；另有 `serve.log.bak-20260910.gz` 內 54 行） | 數字修正 |
| 「1.2GB 模型」 | 實測 **1.04 GiB（= 1.118 GB）** | 高估 13% |
| 引用 `scripts/swap_hud_version.ps1` | **該檔唔存在** | 換版流程要改用實際存在嘅方法 |
| 「根因已 100% 實測確認」 | 當時關鍵參數（啟動需時）未量測 → 措辭過早 | 已由本輪量測補上 |

**Review 記錄**：反方 **2 : 8**（反方勝）—— 反方獨立搵到同一根因（alert_voice 耦合）；數字核實方 36 項中 27 一致 / 4 唔一致 / 5 無法重現。業界引文（sokuji「90-second watchdog」、SO「30–60s to load」）**網上核實唔到 → 本 plan 已移除，唔再作為依據**。

---

## 修法（v2 — 對症下藥）

### 改動 1（核心）：解耦「存活判準」與「可選功能」

**檔案**：`hud/main.js`（`sidecarRunning()`，第 84-94 行）、`src/jarvis/shell_app.py`（`_ensure_alerts_mcp`）

**方向**（二選一或並用，實作時定）：
- **1a. serve 永遠提供 health**：serve 自己起一個極輕量 health 端點（**唔受 `alert_voice` 影響**），或者令 8765 嘅 MCP server 獨立於 alert 開關（health 部分無條件啟動、alert 部分才受開關控制）
- **1b. main.js 改判準**：以「**進程存活**」為主（`exitCode === null`），`/health` 只作為輔助訊號（例如連續失敗時**只警告、唔 kill**，或者只在 `alert_voice` 啟用時才用 /health 判斷）

**業界原則**：Kubernetes 文檔 —— liveness probe **唔應該**依賴可選功能／外部依賴（"don't tie liveness to optional dependencies"）。呢個正是我哋撞中嘅經典錯誤。

**必須保留既有正確邏輯**（skill `jarvis-hud-electron-editing-pitfalls` §20）：
- `exitCode === null` = 仍然活住（`killed` 唔可信）
- `child.pid === undefined` = spawn 從未成功（`err.syscall` 係 `"spawn <path>"`，唔可以用 `=== 'spawn'`）
- spawn 失敗只 emit `'error'`（唔 emit `'exit'`）→ 清理要放 `'error'` handler
- kill 後唔好即刻 spawn（5 秒延遲，避免 port race）
- exit handler identity-check（`if (sidecarProc === child)`）
- crash-loop rate limit 保留

### 改動 2（監控補漏）：cron monitor 盲點

**檔案**：`%LOCALAPPDATA%\hermes\scripts\jarvis_sidecar_health.py`
- **現況問題**：fingerprint 一直係 `DOWN URLError` → 唔會再 alert（monitor 設計只在 fingerprint 變化時通知）
- **改法**：加「持續 DOWN 超過 N 分鐘」嘅二次提醒（例如 fingerprint 內包含持續時長，或者額外每日 heartbeat）

### 改動 3（順帶）：`jarvis_hud_activity.log` 輪替
- 現時 **88 MB**（每 5 秒一行、從未輪替）→ 加上限 + rotate

### 唔做（v1 已否決）
- ~~startup grace period~~（醫錯病；除非 Task 0 量測到真有慢啟動）
- ~~模型本地快取加速~~（實測已經係本地 cache 0.00 秒）

---

## 執行步驟

### Task 0：確認根因（**已大致完成**，剩最後一步對照實驗）
- ✅ 已做：settings 值、code 路徑、獨立 MCP 測試、bind 測試、serve spawn 量測
- ⏳ 剩：**對照實驗** —— 將 `alert_voice` 暫時設 True（或者用臨時 port 起一個 health-only server）→ 確認 8765 LISTEN → 循環消失
  - ⚠️ 改 settings 有副作用（alert 會出聲）→ 或改用**唔改 settings 嘅等價測試**：手動起一個只 bind 8765/health 嘅 dummy server → 睇 Electron 會唔會停止 kill serve
- **驗收**：確立「8765 有 LISTEN ⟺ 循環消失」

### Task 1：改動 1（解耦）
1. 經 **cursor-agent** 改（SK 規則）
2. `node --check hud/main.js` + `env -u PYTHONPATH python -m py_compile src/jarvis/shell_app.py`
3. Grep 驗證關鍵函數仍在：`whenReady|ipcMain|globalShortcut|mediaBridge|listen(8771|stopSidecar|spawnSidecar`
4. **負向對照測試**（negative control）：spawn 失敗（bogus python 路徑）→ 確認仍有 error log + rate limit backoff，唔會卡死

### Task 2：改動 2（監控補漏）
### Task 3：改動 3（log 輪替）
### Task 4：打包 + 換版 + 端到端驗收
- bump `hud/package.json` version → `npm run dist`（經 VBS hidden wrapper，零閃窗）→ 換 exe → 更新 3 個 .lnk
- ⚠️ v1 引用嘅 `scripts/swap_hud_version.ps1` **唔存在** → 實作時要確認實際換版方法（skill §21 有記錄）

---

## 驗收標準（v2 加強版 — 防「假綠」）

| # | 驗收項 | 方法 | 通過條件 |
|---|---|---|---|
| 1 | **循環消失** | 監測 15 分鐘：`serve` 進程 PID + `serve.log` | PID 不變、spawn 只 1 次 |
| 2 | **唔可以只睇 log** | 同時驗 `8765` 狀態 + 進程存活 | 三者一致（防 v1 錯誤：log 唔變但服務已死） |
| 3 | **alert_voice=False 之下仍健康** | 保持 `alert_voice=False`（SK 現況）跑足 15 分鐘 | 冇 kill/respawn |
| 4 | **alert_voice=True 之下仍正常** | 臨時切 True 測 | 冇 kill/respawn |
| 5 | **回歸：真死機仍能救援** | kill serve PID | ~90 秒內自動 respawn |
| 6 | **回歸：spawn ENOENT** | bogus python 路徑 | 有 error log + backoff，唔會永久卡死 |
| 7 | **SK 主觀** | SK 打機打字 | 無間歇延遲 |
| 8 | **監控唔再盲** | 模擬持續 DOWN | 會再提醒（改動 2 生效） |

---

## 風險 / 還原

| 風險 | 影響 | 還原 |
|---|---|---|
| 改 `main.js` 引入新 bug | HUD 功能受損 | 舊 exe 保留（`dist/JARVIS-ONE-0.4.13.exe`）→ 重開舊版 rollback |
| 改 `shell_app.py` 影響 alert 功能 | 提醒失效 | 只改「health 是否啟動」，唔動 alert 邏輯本體 |
| 打包／換版彈窗 | SK 打機被打擾 | 全部經 VBS hidden wrapper；**SK idle 時才做** |

**現時止血**：JARVIS ONE 保持關閉（HUD／提醒暫停）—— 已實測有效（serve.log 停止增長）。

---

## 待答問題

1. 改動 1 揀 1a（serve 永遠提供 health）定 1b（main.js 改判準）？→ **建議 1a 為主 + 1b 為輔**（兩邊都唔再單靠一個可選功能）
2. `jarvis_hud_activity.log` 上限定幾多？（建議 5 MB × 2 檔）
3. 監控補漏（改動 2）嘅提醒頻率？

---

## Lessons（應入 skill）

- **liveness probe 唔可以依賴可選功能**：8765 係 alerts MCP，而 alerts 由 `alert_voice` 開關控制 → 一關提醒，Electron 就以為 sidecar 死咗 → 無限重啟。同類錯誤：把 health check 綁喺 feature flag 上。
- **診斷 signature**：`serve.log` 反覆出現 startup 週期 + 進程 StartTime 一直變 + **8765 無 LISTEN** + CPU 偏低（blocked 唔係 spin）。
- **監控盲點**：fingerprint 型 monitor 一旦長期停在同一個 DOWN 狀態就唔會再提醒 → 一定要有「持續時長」維度。
- **v1 教訓**：唔好喺未量測關鍵參數（啟動需時）之前就寫「根因 100% 確認」；Plan 內每個數字都要標快照時間。
