# JARVIS Sidecar 無限重啟循環 — 修復計劃 **v3（經 R2 反方 review 修正）**

**日期**：2026-09-23（v1 → v2 → v3）
**狀態**：待 R3 review（R1 2:8、R2 4:6，兩輪都未達 8:2）
**此計劃只做規劃，未改任何 code**
**檔名註**：檔名 `1500` 係本檔建立時間；內容最後修訂 2026-09-23 20:4x（數字核實方捉到「檔名 1500 ≠ mtime 16:48」→ 以此註解為準）

---

## 修訂記錄 v2 → v3（逐條對應 R2 review 嘅指控）

| # | R2 指控（反方） | v3 處理 |
|---|---|---|
| B1 | **1b（只警告唔 kill）＝主動放棄 wedge 救援，阻塞級** | **1b 取消**。只做 1a（server 無條件起）＝沿用現有 kill 路徑，唔會失去任何現有覆蓋。另在「已知限制」明文寫 `/health` 只覆蓋 HTTP thread，audio wedge 本來（alert_voice=True 年代）都冇覆蓋 —— 唔係本次改動引入。可選 heartbeat 列 Slice C（唔做） |
| B2 | **閘有兩道**（495-496 `alert_voice`、497-498 `alert_tts != "hermes"`），v2 寫「一個開關」唔準 | 修法改為**兩道閘一齊解耦**；驗收加 `alert_tts=piper` 情境 |
| B3 | `sidecarRunning()` **硬編碼 8765**，無視 `alerts_mcp_port`（UI 改得到）→ 改 port 循環復發 | main.js 改為由 `settings.json` 讀 `alerts_mcp_port`（fallback 8765，沿用 main.js:649 嘅 clamp）；驗收加改 port 情境 |
| B4 | 1a 副作用：`jarvis_speak`（mcp_alerts_http.py:371-400）**唔查 alert_voice** → 8765 一開即恢復一條 TTS 出路 | 明文承認並定案：**MCP 工具唔受 alert 開關 gate**（`jarvis_speak` 自帶 gaming／voice_call／rate-limit／speakability 閘）＝**預期行為**；列為驗收項（語音線 HOLD 下仍可 Discord voice-out）。如 SK 反對 → 改成 tool 內部 gate |
| B5 | 改動 2 狀態存邊、桶級距、頻率全部空 | 見「改動 2」：state 檔位置＋時間桶級距＋「每桶只出一次」＋`except` 保護（避免空 stdout 永久靜音） |
| B6 | fingerprint 直接放「持續時長」＝每 2 分鐘嘈一次 | 用**桶化**（bucket），唔係連續值 |
| B7 | 改動 3（88 MB log 輪替）係**唯一不可逆**改動、無 backup、風險表零行 | **改動 3 移出本計劃** → 另開 Slice B（無資料刪除＝本計劃零不可逆） |
| B8 | 「`scripts/swap_hud_version.ps1` 唔存在」係**錯**（v1 錯路徑、v2 反向誤判） | 正確路徑：`%LOCALAPPDATA%\hermes\skills\software-development\jarvis-hud-electron-editing-pitfalls\scripts\swap_hud_version.ps1`（71 行、實測跑過 0.4.11→0.4.13）→ Task 3 直接指名用 |
| B9 | Task 4「換 exe」冇寫 skill §20 兩個實測陷阱（portable exe 喺 `%TEMP%\<hash>\`；單例鎖會靜默 quit） | Task 3 指名用 swap script（已包 kill 全部 `JARVIS*` ＋驗 `/health`／port ＋更新 3 個 .lnk）＋保留 §20 清單 |
| B10 | 改動 2／Task 0 缺還原行；`%LOCALAPPDATA%\hermes\scripts` **唔受版控**（本輪實查：`fatal: not a git repository`） | 「風險／還原」表補齊每項（含 `.bak-<timestamp>` 做法） |
| B11 | 驗收 #5（kill PID → 90 秒 respawn）**永遠綠**；#1–#4 只測「冇重啟」；#6 負控係重跑舊測試；缺 cron pause 前置 | 驗收表重寫（見下）：分開 exit path／health path、加 wedge 負控、加 cron pause 前置 |
| B12 | #7「SK 主觀打機唔延遲」有 4 個 confounder（GameInput／USB 省電／TRCC／Surfshark） | 明文標注 confounder；主觀項**唔可以**做唯一 end-to-end 證據 |
| B13 | `shell_app.py:493` 係 `def` 唔係 guard（guard 喺 495-496）；「20 檔檢查 0.00 秒」實測 ~0.55 秒；`1.04 GiB`／`4.4 秒`／`100 秒冇 LISTEN` 需起 process（未驗） | 事實表逐項標「已核（靜態）／未驗（需量測）＋快照時間」 |

---

## Goal

消除 `jarvis serve`（Python sidecar）每 90 秒被 Electron 殺掉重啟嘅循環 —— 循環每次重載 STT／TTS，令系統每 1.5 分鐘出現 CPU／磁碟 I/O 尖峰（= SK 打機時鍵盤間歇延遲來源之一）。

**本計劃另外附帶修好一個未記錄嘅副作用**：8765 唔存在 ⇒ Electron 設定視窗靜靜跌落 fallback（`hud/main.js:567-579` 讀檔）：DPAPI 加密欄位顯示成 `dpapi:` 密文、儲存繞過「單一寫入者」（直接寫 `settings.json`）→ 解耦後兩者一齊復原。

---

## 根因（v3 — 全部有靜態證據；數字見「事實表」）

**核心錯配：Electron 用 8765 `/health` 做 sidecar 嘅唯一存活判準，但 8765 嘅生死由兩個可選功能開關決定。**

```python
# src/jarvis/shell_app.py:493-505（_ensure_alerts_mcp）
if not bool(getattr(cfg, "alert_voice", True)):      # 495-496 → return   ← 閘①
    return
if str(getattr(cfg, "alert_tts", "hermes") or "").lower() != "hermes":   # 497-498 → return  ← 閘②
    return
...
serve_in_thread(host="127.0.0.1", port=port, token=tok)   # 504（全 src 唯一 call site）
```

```javascript
// hud/main.js:84-94（sidecarRunning）— 硬編碼 8765，無視 alerts_mcp_port
fetch('http://127.0.0.1:8765/health', ...).then((r) => resolve(r.ok))
// hud/main.js:157-179（startSidecarHealthCheck）— 每 30s、連續 3 miss（90s）→ sidecarProc.kill()
```

### 完整因果鏈（含時間線張力嘅解釋）

```
09/22 17:33  SK 關 alert_voice（語音線 HOLD）＋voice_frontend → hermes  【settings.json mtime 17:33:34 **已核**】
  └→ 當時已經行緊嘅 serve 唔會關自己個 server ⇒ 18:59／19:02／19:05 仍見到 request
      （= serve.log 最後一條 `Processing request of type` 09/22 19:05:05 **已核**）
  └→ serve 下一次重啟起，`_ensure_alerts_mcp` 立即 return ⇒ 8765 永遠唔 LISTEN（最後一次啟動 log = line 17003，早於 17209）
Electron 每 30 秒問 8765「仲在唔在？」→ 永遠問唔到 → 90 秒（3 miss）→ kill → 5 秒後 respawn
  └→ 每個 cycle 重新載入 STT（log 實測每週期一次 `download models from model hub`，全檔 300 次）
  └→ 週期 = **90.0 秒（實測近 12 個 cycle mean／median 90.0，range 87–93）**
  └→ 打機時輸入執行緒排隊 = 鍵盤間歇延遲
「以前冇」嘅答案：09/22 17:33 之前 alert_voice=True ⇒ 8765 有起 ⇒ health 通 ⇒ 冇循環
```

**止血狀態（已核）**：JARVIS ONE 目前關閉；`serve.log` 同 `jarvis_hud_activity.log` 都停喺 09-23 14:48（≈6 小時零增長）⇒ 問題 dormant。

---

## 事實表（每項標明狀態 + 快照時間；R2 數字核實方逐項重算）

| # | 事實 | 狀態 | 證據 |
|---|---|---|---|
| 1 | `settings.json`：`alert_voice=false`(31)、`voice_frontend="hermes"`(22)、`alert_tts="hermes"`(42)、`stt_preload=true`(51)、`alerts_mcp_port=8765`(43) | **已核** | settings.json；diff `.bak-20260922_171207`：31c31、22c22（**另有 3 行 `dpapi:` api_key 密文改動**，v2 冇提） |
| 2 | settings.json mtime = 2026-09-22 **17:33:34** | **已核** | `stat`（R2 核實方補量） |
| 3 | 8765 最後一次真正服務 = 09/22 **19:05:05**（serve.log line 17209、全檔 5,203 條） | **已核** | serve.log:17209；8765 啟動 log 最後一次 = line 17003 |
| 4 | `serve_in_thread` 全 src 唯一 call site = shell_app.py:504（def 喺 493、guard 喺 **495-496**） | **已核** | grep（493 係 `def` 唔係 guard → v2 措辭已修正） |
| 5 | 模型下載 = **300** 次（定義：`download models from model hub`；旁證 `headless serve`=300、`TTS Piper 已預載`=300；`Downloading 20 files`=**297**） | **已核** | grep -c（v2 同時列 294 → 294 = 截至 09-23 14:38:58 嘅舊快照，其後剛好 6 條） |
| 6 | 20 檔檢查耗時 **≈0.55 秒**（log 顯示 `20/20 [00:00<00:00]`） | **已核**（v2 寫「0.00 秒」＝過度精確，已改） | serve.log 14:48:02.651→14:48:03.199 |
| 7 | 週期 = 90.0 秒、每次 cycle 一次完整 STT 預載 | **已核** | 逐個時間戳相減（近 12 週期 range 87–93；全期 mean 90.4） |
| 8 | cron 監控盲點：`6a98a79be95f`（每 2m）`monitor_state.last_changed_at=2026-09-22T19:10:37`，明文 fingerprint 一直 `DOWN URLError`（13 B） | **已核** | cron\jobs.json:172-179、`cron\output\6a98a79be95f\monitor_last_output.txt`；09/23 17:58→20:27 全部 `no_change`（agent run suppressed） |
| 9 | 停 sidecar 前 CI 語意：`/health` 由 `_health_payload()` 出，`{"ok":true,"service":"jarvis","ts":…,"wake_on":…}`；**GET /health 免 token** | **已核** | mcp_alerts_http.py:104-110、:467-468 |
| 10 | `jarvis_hud_activity.log` = **92,519,586 B（88.23 MiB）**、1,589,834 行、5s 一行、路徑 `%LOCALAPPDATA%\Temp\`（唯一 writer = main.js:303） | **已核** | stat／grep（v2 冇寫路徑；Slice B 才處理） |
| 11 | STT 預載 1.04 GiB RAM／載入 4.4–16 秒／spawn 後 100 秒冇 LISTEN、CPU 0.7%／獨立 bind 測試 | **未驗（需起 process；本輪硬限制禁止）** | 要實驗：spawn serve → 每 5s 量 `Get-NetTCPConnection 8765 -Listen` ＋ `Get-Process python CPU` 120s（**放驗收窗口做**） |

---

## Review 記錄

| 輪 | 對象 | 比分 | 主要結果 |
|---|---|---|---|
| R1 | v1 plan | **正方 2 : 反方 8** | 反方獨立搵到同一根因（alert_voice 耦合）；v1 改動 1／2 醫錯病 |
| R2 | v2 plan | **正方 4 : 反方 6** | 反方 13 條（1 阻塞＝1b wedge、12 應修／可接受）；數字核實方 30 項：**一致 22／唔一致 1／部分真 2／未驗 5**（全部靜態可核；未驗 5 項係要起 process 嘅） |
| R3 | v3 plan（本檔） | 待跑 | —— |

**R2 捉到嘅硬事實（v3 據此改）**：`swap_hud_version.ps1` **存在**（v2 反向誤判）；`shell_app.py:493` 係 def 唔係 guard；「0.00 秒」實為 ~0.55 秒；檔名 1500 ≠ mtime。

---

## 修法（v3）

### 改動 1（核心）：解耦「server 生死」與「提醒開關」

**檔案**：`src/jarvis/shell_app.py`、`hud/main.js`

1. **shell_app.py**：把 `serve_in_thread(...)` 由 `_ensure_alerts_mcp` 抽出成 **`_ensure_control_http(cfg)`**，**無條件**啟動（host=127.0.0.1、port=`alerts_mcp_port`、token 照舊）；失敗只 log `[fail] alerts MCP：…`，**唔 raise**。
   - `_ensure_alerts_mcp(cfg)` 保留，但**只負責 alert 行為**：閘① `alert_voice`、閘② `alert_tts` 只 gate `_ensure_alert_poller()`（推送／TTS），唔再 gate HTTP server。
   - 呼叫點（shell_app.py:487）保持一次，確保 server 早起。
   - 語意：**開關＝「要唔要出提醒」，唔再等於「sidecar 生唔生」**。
2. **hud/main.js**：
   - `sidecarRunning()` 改為讀 `settings.json` 嘅 `alerts_mcp_port`（fallback 8765；沿用 :649 clamp 語意），唔再硬編碼。
   - 判準收緊：`resp.ok && body.ok === true && body.service === "jarvis"`（現時任何 HTTP server 佔住 8765 都當健康）。
   - 其餘存活／respawn 邏輯**一律保留**（skill §20 不變式）：`exitCode === null`、`child.pid === undefined`、error handler 清理、5 秒延遲、identity-check、rate limit。
3. **明確聲明（B4）**：MCP 工具（`jarvis_speak`／`jarvis_clarify_gate`／`jarvis_autonomy_state`）解耦後會恢復可用 = **預期**；`jarvis_speak` 自帶 gaming／voice_call／rate-limit／speakability 閘（mcp_alerts_http.py:371-400）。
4. **已知限制（B1，明文寫落 plan）**：`/health` 只反映 uvicorn daemon thread；STT／wake／TTS wedge 唔會令佢變紅 —— 呢個係**現況（alert_voice=True 年代）已有**嘅限制，唔係本次引入。可選 Slice C：sidecar 主循環寫 heartbeat，`/health` 回報 age。**本計劃唔做**。

### 改動 2（監控補漏）：fingerprint 桶化

**檔案**：`%LOCALAPPDATA%\hermes\scripts\jarvis_sidecar_health.py`（**唔受版控** → 改前 `.bak-<timestamp>`）
- 現況：33 行、stateless，fingerprint 只有 `OK wake_on=<b>`／`DOWN <ExcName>` → 一直 DOWN 就永遠唔變（cron 由 09/22 19:10 起靜音）。
- 改法：
  - state 檔：`%LOCALAPPDATA%\hermes\state\jarvis_sidecar_health_state.json`（`down_since` ＋ `last_bucket`）。
  - UP（`body.ok`）→ 印 `OK wake_on=<b>`；清 state。
  - DOWN → 首次寫 `down_since=now`；算持續分鐘；**桶**：`<5m`／`5-30m`／`30m-2h`／`2-6h`／`>6h`（級距跨級才變字串）→ 印 `DOWN <reason> t=<bucket>`。
  - 因為 cron 係「fingerprint 變才叫醒 agent」⇒ **每跨一級只提醒一次**，唔會每 2 分鐘嘈。
  - 整段包 `try/except`，**永遠印嘢**（空 stdout = 永久靜音，見複發 blocker 目錄 §B11）。
- 還原：copy 返 `.bak-<timestamp>`＋刪 state 檔。

### 移出本計劃 → Slice B（唔做）

- **`jarvis_hud_activity.log` 輪替**（88 MB → 上限 × 1 rotate）：係本計劃唯一不可逆改動，亦同循環無關 → 另開 slice，屆時：先 copy 去 `%LOCALAPPDATA%\hermes\backups\`、再喺 main.js（唯一 writer）加 10 MB rotate、同步更新 skill §27 診斷法。
- **Slice C**：heartbeat wedge 偵測（見上）。

---

## 執行步驟

### Task 0：根因最後一里（**唔喺打機中做**）
- v2 原本諗住「暫時設 `alert_voice=True` 做對照」→ **撤銷**（會令 alert 出聲＋要重啟 sidecar）。
- 改用零副作用等價對照：起一個 dummy HTTP server 佔住 8765（回 `{"ok":true,"service":"jarvis"}`）→ 睇 Electron 會唔會停止 kill serve。**需要 HUD 開住 ⇒ 放入驗收窗口（SK 唔打機）**。
- 驗收：確立「8765 有回應 ⟺ 循環消失」。

### Task 1：改動 1（經 **cursor-agent**）
1. `node --check hud/main.js` ＋ `env -u PYTHONPATH python -m py_compile src/jarvis/shell_app.py`
2. grep 驗關鍵函數仍在：`whenReady|ipcMain|globalShortcut|mediaBridge|listen\(8771|stopSidecar|spawnSidecar|startSidecarHealthCheck`
3. 行為測試（唔使開 Electron）：`alert_voice=false` 之下 spawn serve → 期望 8765 LISTEN ＋ `/health` 200（呢個就係 B2 兩道閘都要解）

### Task 2：改動 2（monitor 桶化）
- 靜態測：`DOWN` 時連續跑 3 次 → fingerprint 應該**同一個桶內不變**；state 檔寫入正常；`body.ok` 缺失（假 server）→ 走 DOWN 分支唔拋錯。

### Task 3：打包 + 換版（**SK idle 才做**）
1. bump `hud/package.json` → `npm run dist`（經 VBS hidden wrapper，零閃窗）
2. **用現成工具**：`%LOCALAPPDATA%\hermes\skills\software-development\jarvis-hud-electron-editing-pitfalls\scripts\swap_hud_version.ps1`（kill 全部 `JARVIS*` → 5s → 開新 exe → 20s → 驗 `/health` ＋ netstat 8642/8765/8770/8771 → 更新 3 個 .lnk）
3. ⚠️ 保留 skill §20 兩陷阱作手動核對：portable exe 真身喺 `%TEMP%\<hash>\JARVIS ONE.exe`（只 kill 版本號嗰個殺唔死）；單例鎖會令第二次啟動**靜默 quit**（易假判「換版成功」）

### Task 4：端到端驗收（見下）

---

## 驗收標準（v3 — 針對本次改動，防假綠）

**前置**：① **pause cron `6a98a79be95f`**（唔停就無法歸因，每 2 分鐘會自己救返）；② SK 唔打機（HUD 要開）；③ 記低 `serve.log` 行數作 baseline。

| # | 驗收項 | 方法 | 通過條件 |
|---|---|---|---|
| 1 | 循環消失 | 15 分鐘：serve PID ＋ `serve.log` 新增行數（`download models from model hub` delta）＋ `Get-NetTCPConnection 8765 -Listen` ＋ `/health` | 四者一致：PID 不變、delta=0、LISTEN 在、health 200 |
| 2 | `alert_voice=false`（現況）仍健康 | 同 1 | 冇 kill／respawn |
| 3 | `alert_voice=true` 仍健康 | 臨時切（經 sidecar `POST /settings`） | 冇 kill／respawn；測完還原 |
| 4 | **第二道閘**：`alert_tts=piper` ＋ `alert_voice=true` | 同上 | 冇 kill／respawn（驗 497-498 已解耦） |
| 5 | **port 維度**：`alerts_mcp_port=8766` | 改 → 觀察 | sidecar bind 8766、Electron 讀 8766 → 冇 kill；測完還原 8765 |
| 6 | 真死機（**exit path**） | `kill <serve PID>` | **≤15 秒**內 respawn（唔係 90s；分辨係 exit path） |
| 7 | **health path（本次改動嘅負控）** | 起 dummy **503** server 佔 8765（process 生但 health 唔通） | 90 秒內 Electron 殺＋respawn ⇒ 證明健康判準仍然有效（唔會因改動變成「永遠健康」） |
| 8 | 負控 2：spawn 失敗 | bogus python 路徑 | 有 error log ＋ backoff，唔永久卡死（沿用舊有驗收） |
| 9 | monitor 唔再盲 | 恢復 cron；令 8765 持續 DOWN | fingerprint 由 `t=<5m>` 跨到 `t=30m` ⇒ 有提醒；回 UP ⇒ 再一次 |
| 10 | 設定視窗復原 | 開 Settings tab | LLM／ASR key 顯示解密值（唔再見 `dpapi:`）；儲存走 8765（response 無 `fallback:true`） |
| 11 | SK 主觀（**唔可作唯一證據**） | 打機打字 | 明顯改善；⚠️ 今日另有 GameInput／USB 省電／TRCC／Surfshark 四個 confounder，必須同 #1–#7 客觀訊號一齊睇 |

---

## 風險 / 還原（每項改動都要有得返轉頭）

| 改動 | 風險 | 還原（具體、可驗） |
|---|---|---|
| `hud/main.js`＋`src/jarvis/shell_app.py` | HUD／提醒功能受損 | ① `git revert <commit>`（branch `feature/hermes-alerts-mcp`）；② 換版 rollback：`dist\JARVIS-ONE-0.4.13.exe` 保留，用 swap script 開返舊版＋驗 4 個 port |
| monitor script（**唔受版控**） | 監控失效 | 改前 copy `jarvis_sidecar_health.py.bak-<timestamp>`；還原＝copy 返＋刪 state 檔（`state\jarvis_sidecar_health_state.json`） |
| 驗收 3／4／5 改 settings | 提醒出聲／port 改錯 | 用 sidecar **`POST /settings`**（單一 writer）還原，唔好直接覆蓋檔案；改前記低原值（`alert_voice=false`、`alert_tts=hermes`、`alerts_mcp_port=8765`） |
| 打包／換版 | 打機中彈窗 | 全部經 VBS hidden wrapper；**SK idle 才做** |
| 本計劃 | 無資料刪除（Slice B 移出） | 88 MB log 原封不動 |

**現時止血**：JARVIS ONE 保持關閉（HUD／提醒暫停）—— 已實測有效（兩個 log 都停 14:48）。

---

## 待答問題（SK）

1. **驗收窗口**：Task 3／4 要開 HUD 跑 30–40 分鐘（唔可以打機中做）—— 邊日邊個時段？
2. **B4 確認**：解耦後 MCP 工具（含 `jarvis_speak`）恢復可用，同意當「預期行為」？
3. **Slice B**（88 MB log 輪替）做唔做？（我建議唔急）

---

## Lessons（應入 skill）

- **liveness probe 唔可以依賴可選功能**（K8s 原則）：8765 係 alerts MCP，但佢同時係 Electron 嘅 health ＋ settings 出入口 ⇒ 一關提醒，整個 sidecar 被誤判死。同類錯誤＝把 health check 綁喺 feature flag 上。
- **一個服務如果同時做「健康探針」＋「功能介面」，佢嘅生死就唔可以由功能開關決定**。
- **診斷 signature**：`serve.log` 反覆出現 startup 週期 ＋ 進程 StartTime 一直變 ＋ **8765 無 LISTEN** ＋ CPU 偏低（blocked 唔係 spin）。
- **fingerprint 型 monitor 一定要有「持續時長」維度，但要用桶化**（連續值＝每 tick 變＝疲勞；冇維度＝永久靜音）。
- **唔好喺未量測關鍵參數之前寫「根因 100% 確認」**；每個數字標快照時間；引用外部工具前先搵清正確路徑（v2 曾誤判 `swap_hud_version.ps1` 唔存在）。
