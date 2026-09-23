# JARVIS Sidecar 無限重啟循環 — 修復計劃 **v4（R3 中立裁判：v3_adequate = true）**

**日期**：2026-09-23（v1 → v2 → v3 → v4）
**狀態**：**可以開工** —— 裁判裁定 `v3_adequate = true`（前提：D1–D4 以裁判版本寫入本版）；等 SK 揀驗收窗口
**此計劃只做規劃，未改任何 code**
**檔名註**：檔名 `1500` 係本檔建立時間（v3 已修正 header 時間戳錯誤；本版 20:5x 修訂）
**Review 歷史**：R1（v1）正方 2:8 → R2（v2）4:6 → R3（v3）3:7 → **中立裁判 4:6 ＋ `v3_adequate = true`**（反方分級系統性偏嚴一格；核心設計「liveness 唔可以綁功能開關」三輪未被撼動）

---

## 修訂記錄 v3 → v4（逐條對應裁判 D1–D5 同反方餘項）

| # | 裁決 | v4 處理 |
|---|---|---|
| **D1** | 無條件起 server 之後嘅失敗面：`shell_app.py:499-512` 嘅 `try` 包唔到 thread 內嘅 bind 失敗，而且 `:505-510` 會**照印 `[ok] …（Hermes peek）`** ＝假成功 | 改動 1 加：**起完 5 秒 self-probe**（socket connect 或 `/health`）；**成功才印 `[ok]`**、失敗印**會變嘅**指紋 ＋ 寫 `hud_error.log`；**明文「唔自動重試」**（8765 被佔多數係人手錯，靜默重試＝新循環源） |
| **D2** | port 硬編碼實測 **6 處**（`main.js:90/573/674`、`hermes\config.yaml:254`、`jarvis_sidecar_health.py:15`、`swap_hud_version.ps1:45-48`）→ 裁定**凍結 8765** | `clampSettingsPatch` 只收 8765；`settings.html` 該欄位標「唯讀／boot-time」；`main.js` 保持 8765＝凍結值；**刪驗收 #5**；計劃明寫「alerts_mcp_port 唔准改；要改＝要動四個外部消費者（反轉成 resolver，見反轉條件）」 |
| **D3** | 驗收 #3/#4 假綠：兩道閘只喺 boot（`shell_app.py:1889`→`:487`）同 Tk 儲存（`:443`）生效 | #3/#4 加步驟：**改值 → kill serve → 確認以新閘 boot 之後 8765 仍 LISTEN** |
| **D4** | 監控靜音唔止「首 run 唔叫」 | 改動 2 加 **`OFF` 指紋**（＝「HUD process 唔在 ∧ 冇 `jarvis serve` python」→ 印 `OFF`，**唔帶時間桶**）；state 檔讀／寫失敗 → 出**另一個**指紋（唔准靜靜當「首次 DOWN」） |
| **D5** | Task 0 次序 | 明寫：`alert_voice` 保持 false ＋ 佔 8765 **前先 `stopSidecar`** ＋ 做完**交還 port**（否則 dummy 同真 sidecar 相撞＝落進 D1 靜默死路徑） |
| 小修 a | 前置①寫「cron 每 2 分鐘會自己救返」＝**事實錯**（該 job 只 print ＋ 叫醒 agent，**唔會重啟任何嘢**） | 已改（見驗收前置） |
| 小修 b | 驗收 #6「≤15 秒 respawn」會被 `main.js:110-121` 嘅 **60 秒 crash-loop rate-limit（≥3 spawn/60s）** 弄成假紅 | #6 加註：相鄰 kill 測試**隔 >60 秒**；並分辨 exit path／health path |
| 小修 c | #1 冇 assert「跑緊嘅係新 build」（單例鎖靜默 quit 會假判換版成功） | #1 加：核 process path／exe 版本＝新 build |
| 小修 d | 兩把尺唔一致：main.js 收緊判準，但 monitor 仍只睇 `body.get("ok")` | monitor 同步改為 `ok is True and service == "jarvis"` |
| 小修 e | plan 曾寫「呼叫點保持一次，確保 server 早起」＝錯（同一 call site ≠ 更早起） | 已刪錯誤措辭；改為明寫「server 起喺 `shell_app.py:487` 呢個 boot 路徑」 |
| 小修 f | 任務 1–3 冇 commit 步驟，但還原表寫 `git revert <commit>` | Slice 1 開工前**先存 patch**（`git diff > backups\*.patch`）；commit 要 SK 批（AGENTS.md：唔擅自 commit） |
| 新（裁判補） | `/settings` 回**解密後**金鑰（`mcp_alerts_http.py:479-489`，token 係明文檔）＋ `/health` 免 token → 語音 HOLD 期間新增常開面 | 列作**知悉項**（待答問題 3）；若 SK 反對 → 加 gate |

### 歷史（R1／R2 已修事項，保留作記錄）
B1 取消 1b（避免製造「永遠冇人救」）｜B2 兩道閘（`alert_voice` ＋ `alert_tts`）一齊解耦｜B4 `jarvis_speak` 恢復可用＝預期行為（自帶四閘）｜B5 改動 2 加 state 檔＋桶級距＋`except` 保護｜B6 桶化（唔用連續值）｜B7 88 MB log 輪替移出本計劃（本計劃零不可逆）｜B8 換版用真身 `skills\software-development\jarvis-hud-electron-editing-pitfalls\scripts\swap_hud_version.ps1`（71 行、實測 0.4.11→0.4.13）｜B9 補 §20 兩陷阱（portable exe 喺 `%TEMP%\<hash>`、單例鎖靜默 quit）｜B10 monitor script 唔受版控→`.bak-<timestamp>`｜B11 驗收表重寫｜B12 標注四個 confounder

---

## Goal

消除 `jarvis serve`（Python sidecar）每 90 秒被 Electron 殺掉重啟嘅循環 —— 循環每次重載 STT／TTS，令系統每 1.5 分鐘出現 CPU／磁碟 I/O 尖峰。
⚠️ **尖峰幅度從未量測**（U5）：現時只可以話「每 90 秒一次完整 startup 週期」係客觀事實（log 已核），「= 鍵盤延遲」屬**未量化嘅因果假設**（另有 4 個 confounder，見驗收 #11）。

**附帶修好一個未記錄嘅副作用**：8765 唔存在 ⇒ Electron 設定視窗靜靜跌落 fallback（`hud/main.js:567-579`）：DPAPI 加密欄位顯示成 `dpapi:` 密文、儲存繞過「單一寫入者」→ 解耦後兩者一齊復原。

---

## 根因（v4 — 靜態證據全部已核）

**核心錯配：Electron 用 8765 `/health` 做 sidecar 嘅唯一存活判準，但 8765 嘅生死由兩個可選功能開關決定。**

```python
# src/jarvis/shell_app.py:493-505（_ensure_alerts_mcp）— 兩道閘都 return 整個 function
if not bool(getattr(cfg, "alert_voice", True)):                            # 495-496  ← 閘①
    return
if str(getattr(cfg, "alert_tts", "hermes") or "").lower() != "hermes":     # 497-498  ← 閘②
    return
...
serve_in_thread(host="127.0.0.1", port=port, token=tok)                    # 504（全 src 唯一 call site）
```

```javascript
// hud/main.js:84-94 — 硬編碼 8765；main.js:157-179 — 每 30s、連續 3 miss（90s）→ sidecarProc.kill()
```

### 完整因果鏈（含時間線張力嘅解釋）

```
09/22 17:33:34（settings.json mtime 已核）SK 關 alert_voice（語音線 HOLD）
  └→ 當時行緊嘅 serve 唔會關自己個 server ⇒ 18:59／19:02／19:05 仍見到 request（已核：line 17196／17207／17209）
  └→ serve 下一次重啟起，`_ensure_alerts_mcp` 立即 return ⇒ 8765 永遠唔 LISTEN（啟動 log 最後 = line 17003）
Electron 每 30 秒問 8765 → 永遠問唔到 → 90 秒（3 miss）→ kill → 5 秒後 respawn
  └→ 每 cycle 重載 STT（log：每週期一次 `download models from model hub`，全檔 300 次）
  └→ 週期 = 90.0 秒（近 12 個 cycle mean 90.00／median 89.93／range 87.6–92.9）
「以前冇」：09/22 17:33 之前 alert_voice=True ⇒ 8765 有起 ⇒ health 通 ⇒ 冇循環
```

**止血狀態（已核）**：JARVIS ONE 關閉；`serve.log`（14:48:04）同 `jarvis_hud_activity.log`（14:48:35）都停 ⇒ 問題 dormant（≈5.7 小時零增長）。

---

## 事實表（每項標狀態；R2／R3 數字核實方逐項重算）

| # | 事實 | 狀態 | 證據 |
|---|---|---|---|
| 1 | settings.json：`alert_voice=false`(31)、`voice_frontend="hermes"`(22)、`alert_tts="hermes"`(42)、`stt_preload=true`(51)、`alerts_mcp_port=8765`(43) | **已核** | settings.json；diff `.bak-20260922_171207`：31c31、22c22（另有 3 行 `dpapi:` 金鑰密文改動） |
| 2 | settings.json mtime = 2026-09-22 **17:33:34** | **已核** | `stat` |
| 3 | 8765 最後一次服務 = 09/22 **19:05:05**（line 17209；全檔 `Processing request of type` = 5,203 條；該條係 `PingRequest`） | **已核** | serve.log |
| 4 | `serve_in_thread` 全 src 唯一 call site = `:504`（def = `:493`、閘①`:495-496`、閘②`:497-498`、call 點 `:487`） | **已核** | grep／awk |
| 5 | 模型下載 = **300**（定義 `download models from model hub`；旁證 `headless serve`=300、`TTS Piper 已預載`=300；`Downloading 20 files`=**297**） | **已核** | grep -c；294 = 截至 09-23 14:38:58 舊快照，其後剛好 6 條 |
| 6 | 20 檔檢查耗時 **≈0.548 秒** | **已核** | serve.log 14:48:02.651→14:48:03.199 |
| 7 | 週期 = 90.0 秒、每 cycle 一次完整 STT 預載 | **已核** | 逐個時間戳相減 |
| 8 | cron 監控盲點：`6a98a79be95f`（**配置每 2m、實際 output 每 3.0m**）`last_changed_at=2026-09-22T19:10:37`、明文 fingerprint 一直 `DOWN URLError`（13 B）、全部 run 係 `no_change (agent run suppressed)` | **已核** | cron\jobs.json:172-185、`cron\output\6a98a79be95f\*` |
| 9 | `/health` payload = `{ok, service, ts, wake_on}`（`mcp_alerts_http.py:102-108`）；**GET `/health` 免 token**（`:467-468`）；`/settings` 要 Bearer 但**回解密值**（`:479-489`） | **已核** | 讀 code |
| 10 | `jarvis_hud_activity.log` = **92,519,586 B（88.23 MiB）**、1,589,834 行、5s 一行、`%LOCALAPPDATA%\Temp\`、唯一 writer = `main.js:303` | **已核** | stat／grep |
| 11 | STT 預載 1.04 GiB RAM／載入 4.4–16 秒／spawn 後 100 秒冇 LISTEN、CPU 0.7%／獨立 bind 測試 0.000s | **未驗（需起 process；本輪硬限制禁止）** | 要實驗：spawn serve → 每 5s 量 `Get-NetTCPConnection 8765 -Listen` ＋ `Get-Process python CPU` 120s（**放驗收窗口做**，見 U1／U2） |
| 12 | port 硬編碼 6 處；`swap_hud_version.ps1` 存在（71 行）；dist 有 0.4.10–0.4.13 四個 exe；`package.json` = 0.4.13 | **已核** | grep／ls |
| 13 | `%LOCALAPPDATA%\hermes\state\`、`backups\` 目錄存在；`%LOCALAPPDATA%\hermes\scripts` **唔受版控** | **已核** | ls／`git status` |

---

## Review 記錄（停手報告用）

| 輪 | 對象 | 比分 | 主要結果 |
|---|---|---|---|
| R1 | v1 | **正方 2 : 反方 8** | 反方獨立搵到同一根因（alert_voice 耦合）；v1 改動 1／2 醫錯病 |
| R2 | v2 | **4 : 6** | 反方 13 條（1 阻塞＝1b wedge）；數字核實 30 項：一致 22／唔一致 1／部分真 2／未驗 5 |
| R3 | v3 | **3 : 7** | 反方 4 條必修（①a 靜默死、②a 六處 port、⑤#3#4 假綠、④a 首 run 報警）；數字核實 75 項：一致 64／唔一致 3／部分真 5／未驗 3 |
| 裁判 | v3 | **4 : 6，`v3_adequate = true`** | 反方事實命中率高（載重指控 8/9 成立）但**分級偏嚴一格**；核心設計三輪未被撼動；授權：修 D1–D5 → 直接開工，唔准再開新對抗輪 |

**卡死嘅載重決定（裁判 D1–D5）**：見上表（v4 已全部寫入）。
**最貴嘅未知（要量）**：U1 spawn→8765 LISTEN 延遲（若 >90 秒 ⇒ 收緊判準會殺健康 sidecar ⇒ 設計要重審）；U2 bind 衝突可觀測性；U3 收緊判準有冇誤殺（uvicorn bind vs lifespan）；U4 `state\` 原子寫入／讀失敗行為；U5 Goal「CPU／IO 尖峰」未量化。
**反轉條件**：U1 <5 秒且 bind error 真落 serve.log ⇒ ①a 由必修降為文字；SK 要保留 port 可改 ⇒ D2 反轉成 resolver（四處同改＋#5 重寫＋#10 加註）；SK 唔想 `/settings` 解密面常開 ⇒ 加 gate；SK 接受「刻意關機都出聲」 ⇒ ④a 整條省；**U1 若真係 >90 秒才 bind ⇒ 大反轉：無條件起 server 設計要重審**；Task 0 對照失敗 ⇒ 根因重做。

---

## 修法（v4，拆兩塊）

### Slice 1（中風險）— 解耦 ＋ self-probe ＋ 凍結 port

**檔案**：`src/jarvis/shell_app.py`、`hud/main.js`、`hud/settings.html`

1. **shell_app.py**：把 `serve_in_thread(...)` 由 `_ensure_alerts_mcp` 抽出成 **`_ensure_control_http(cfg)`**，**無條件**啟動（host 127.0.0.1、port 用凍結值 8765、token 照舊）。
   - **D1**：起完 **5 秒 self-probe**（socket connect 或 `GET /health`）→ **成功才印 `[ok] …`**；失敗：印會變嘅指紋（例如 `[fail] control-http bind 失敗`）＋寫 `hud_error.log`；**唔自動重試**。
   - `_ensure_alerts_mcp(cfg)` 保留，但只負責 alert 行為：閘①`alert_voice`／閘②`alert_tts` 只 gate `_ensure_alert_poller()`，唔再 gate HTTP server。
   - 語意：**開關＝「要唔要出提醒」，唔等於「sidecar 生唔生」**。
2. **main.js**：
   - 判準收緊：`resp.ok && body.ok === true && body.service === "jarvis"`（原本任何答 200 嘅都當健康）。
   - port 維持 8765（D2 凍結）；`clampSettingsPatch` 只收 8765（UI 標「唯讀／boot-time」）→ 由「讀 settings 嘅 port」改為「凍結值」，避免六處消費者唔一致。
   - 其餘存活／respawn 邏輯**一律保留**（skill §20 不變式）：`exitCode === null`、`child.pid === undefined`、error handler 清理、5 秒延遲、identity-check、rate limit。
3. **知悉項（B4/D2 補）**：MCP 工具（`jarvis_speak`／`jarvis_clarify_gate`／`jarvis_autonomy_state`）恢復可用＝預期（`jarvis_speak` 自帶 gaming／voice_call／rate-limit／speakability 四閘）；`GET /settings` 會回解密金鑰 ＋ token 係本機明文檔 ⇒ 語音 HOLD 期間新增常開面（待答問題 3）。
4. **已知限制（明文）**：`/health` 只反映 uvicorn daemon thread；STT／wake／TTS wedge 唔會令佢變紅 —— 呢個係**現況已有**嘅限制（alert_voice=True 年代一樣），唔係本次引入。而 alert_voice=False 年代「每 90 秒被殺」呢個**意外自動重啟**會消失 ⇒ 可選 **Slice C**：sidecar 主循環寫 heartbeat、`/health` 回報 age（**本計劃唔做**）。

### Slice 2（低風險）— monitor 桶化

**檔案**：`%LOCALAPPDATA%\hermes\scripts\jarvis_sidecar_health.py`（唔受版控 → 改前 `.bak-<timestamp>`）
- 判準同 main.js 對齊：`ok is True and service == "jarvis"`（**小修 d**）。
- 印三種指紋：
  - `OK wake_on=<b>`（UP；清 state）
  - **`OFF`**（D4：「HUD process 唔在 ∧ 冇 `jarvis serve` python」＝SK 刻意關機；**唔帶時間桶**、唔叫醒 agent）
  - `DOWN <reason> t=<bucket>`（桶：`<5m`／`5-30m`／`30m-2h`／`2-6h`／`>6h`；跨級才變字串 ⇒ 每級只提醒一次）
- state 檔：`%LOCALAPPDATA%\hermes\state\jarvis_sidecar_health_state.json`（`down_since` ＋ `last_bucket`；**mkdir 加上**；**tmp + rename 原子寫**）。
- **state 讀／寫失敗要出另一個指紋**（例如 `WARN state_io`），唔准靜靜當「首次 DOWN」。
- 全段包 `try/except`、永遠印嘢（空 stdout = 永久靜音）。
- 還原：copy 返 `.bak-<timestamp>` ＋ 刪 state 檔 ＋ reset cron `monitor_state.last_output_hash`（否則還原後即叫或繼續靜音）。

### 移出本計劃（唔做）
- **Slice B**：`jarvis_hud_activity.log` 輪替（88 MB）：唯一不可逆改動 → 另開 slice（先 copy 去 `backups\`、喺 `main.js:303` 加 10 MB rotate、同步更新 skill §27）。
- **Slice C**：heartbeat wedge 偵測（見上）。

---

## 執行步驟

### Task 0：根因最後一里（**SK idle ＋ 唔打機**）
- **次序（D5）**：`alert_voice` **保持 false** → **先 `stopSidecar`** → 起 dummy HTTP server 佔 8765（答 `{"ok":true,"service":"jarvis"}`）→ 睇 Electron 會唔會停止 kill serve → **做完 stopSidecar 交還 port**。
- 驗收：確立「8765 有回應 ⟺ 循環消失」；失敗 ⇒ 根因重做（反轉條件）。
- 順手量 **U1**（spawn → 8765 LISTEN 延遲，250 ms 輪詢直至首個 200）、**U2**（佔 8765 時 spawn → serve.log 尾有冇 bind error）。

### Task 1：Slice 1（經 **cursor-agent**）
1. 開工前**先存 patch**：`git diff > %LOCALAPPDATA%\hermes\backups\jarvis-sidecar-fix-20260923.patch`（commit 要 SK 批）
2. `node --check hud/main.js` ＋ `env -u PYTHONPATH python -m py_compile src/jarvis/shell_app.py`
3. grep 驗關鍵函數仍在：`whenReady|ipcMain|globalShortcut|mediaBridge|listen\(8771|stopSidecar|spawnSidecar|startSidecarHealthCheck`
4. 行為測試（唔使開 Electron）：`alert_voice=false` 之下 spawn serve → 期望 8765 LISTEN ＋ `/health` 200（唔再靠 `[ok]` 自述）

### Task 2：Slice 2（monitor 桶化）
- 靜態測：同一桶內連續跑 3 次 → 指紋不變；跨桶 → 變；`OFF` 情境（關 HUD）→ 印 `OFF`；state 檔寫唔入（模擬）→ 出 `WARN`。

### Task 3：打包 + 換版（**SK idle 才做**，夾喺兩個驗收窗口之間）
1. bump `hud/package.json` → `npm run dist`（VBS hidden wrapper，零閃窗）
2. **用真身**：`%LOCALAPPDATA%\hermes\skills\software-development\jarvis-hud-electron-editing-pitfalls\scripts\swap_hud_version.ps1`（kill 全部 `JARVIS*` → 5s → 開新 exe → 20s → 驗 `/health` ＋ netstat 8642/8765/8770/8771 → 更新 3 個 .lnk）
3. ⚠️ 手動核對 §20 兩陷阱：portable exe 真身喺 `%TEMP%\<hash>\JARVIS ONE.exe`；單例鎖會令第二次啟動**靜默 quit**（易假判「換版成功」）

### Task 4：端到端驗收（見下；**拆兩個窗口**）

---

## 驗收標準（v4 — 拆窗口；前置修正）

**前置**：① **pause cron `6a98a79be95f`**（⚠️ 更正：呢個 job **只會報告，唔會自動救返**任何嘢 —— 但佢每 2–3 分鐘出指紋會干擾歸因，所以照 pause）；② SK 唔打機（HUD 要開）；③ 核 **跑緊嘅係新 build**（process path／exe 版本）；④ 記低 `serve.log` 行數 baseline。

**窗口 1（HUD 開，15–20 分鐘）**

| # | 驗收項 | 方法 | 通過條件 |
|---|---|---|---|
| 1 | 循環消失 | 15 分鐘：serve PID ＋ `serve.log` delta（`download models from model hub`）＋ `Get-NetTCPConnection 8765 -Listen` ＋ `/health` | 四者一致：PID 不變、delta=0、LISTEN 在、health 200 |
| 2 | `alert_voice=false`（現況）仍健康 | 同 1 | 冇 kill／respawn |
| 3 | `alert_voice=true` 仍健康 | **改值 → kill serve → 確認以新閘 boot 後 8765 仍 LISTEN**（D3） | 冇 kill／respawn；測完還原 false |
| 4 | 閘②：`alert_tts=piper` ＋ `alert_voice=true` | 同上（改值 → kill → 驗） | 冇 kill／respawn；測完還原 `hermes` |
| 5 | ~~port 可改~~ | **刪除**（D2 凍結 8765） | —— |
| 6 | 真死機（exit path） | kill serve PID | **≤15 秒**內 respawn；⚠️ 相鄰 kill 測試**隔 >60 秒**（避 `main.js:110-121` rate-limit 假紅） |
| 7 | health path 負控 | **先 `stopSidecar` → 起 dummy 503 佔 8765** → 觀察 | 90 秒內 Electron 主動 kill＋respawn（證明判準仍有效，唔會變「永遠健康」）；以 `hud_error.log` 為證 |
| 10 | 設定視窗復原 | 開 Settings tab | LLM／ASR key 顯示解密值（唔再見 `dpapi:`）；儲存 response 無 `fallback:true` |
| U1／U2 | spawn→LISTEN 延遲／bind 衝突可觀測性 | 250 ms 輪詢；佔 8765 時 spawn | 延遲 <5 秒（若 >90 秒 ⇒ 設計重審）；bind error 有落 serve.log |
| 11 | SK 主觀（**唔可作唯一證據**） | 打機打字 | 明顯改善；⚠️ 4 個 confounder（GameInput／USB 省電／TRCC／Surfshark）已列，必須同 #1–#7 客觀訊號一齊睇 |

**窗口 2（HUD 關，≥35 分鐘）**：#8 spawn 失敗負控（bogus python → error log ＋ backoff）｜#9 monitor：令 8765 持續 DOWN → 指紋由 `t=<5m>` 跨到 `t=30m`（有提醒）→ 回 UP（再一次）；順手驗 `OFF` 情境（關 HUD → 印 `OFF`、唔叫醒）。

---

## 風險 / 還原

| 改動 | 風險 | 還原（具體、可驗） |
|---|---|---|
| `hud/main.js`／`src/jarvis/shell_app.py`／`settings.html` | HUD 功能受損 | ① 開工前存 `backups\jarvis-sidecar-fix-20260923.patch`；② `git revert <commit>`（commit 前要 SK 批，branch `feature/hermes-alerts-mcp`）；③ 換版 rollback：`dist\JARVIS-ONE-0.4.13.exe` 保留，用 swap script 開返舊版＋驗 4 個 port |
| monitor script（唔受版控） | 監控失效 | `.bak-<timestamp>`；還原＝copy 返 ＋ 刪 state 檔 ＋ reset cron `monitor_state.last_output_hash` |
| 驗收 3／4 改 settings | 提醒出聲 | 用 sidecar `POST /settings`（單一 writer）還原；原值：`alert_voice=false`、`alert_tts=hermes` |
| Task 0／#7 dummy 佔 8765 | 撞真 sidecar | 明寫次序（先 `stopSidecar`）＋做完**交還 port**、殺 dummy |
| 打包／換版 | 打機中彈窗 | 全部經 VBS hidden wrapper；**SK idle 才做** |
| 本計劃 | **零不可逆**（Slice B 移出） | 88 MB log 原封不動 |

**現時止血**：JARVIS ONE 保持關閉（HUD／提醒暫停）—— 已實測有效（兩個 log 都停 14:48）。

---

## 待答問題（SK，一次過答）

1. **驗收窗口**：窗口 1（15–20 分鐘，要開 HUD、唔打機）＋窗口 2（≥35 分鐘，可打機但 HUD 閉）—— 幾時做？（Task 3 換版夾喺中間）
2. **D4「刻意關機」定義**：HUD 關住 ⇒ 印 `OFF`、**唔通知**（我建議照裁判版本做）—— 同意？
3. **常開面**（裁判新發現）：解耦後 `GET /settings` 會回**解密金鑰**、`/health` 免 token，語音 HOLD 期間呢個面會常開 —— 接受（我建議）定要加 gate？
4. **B4**：MCP 工具（含 `jarvis_speak`）恢復可用 ⇒ 當預期行為？（我建議係）
5. **Slice B**（88 MB log 輪替）做唔做？（我建議唔急）

---

## Lessons（應入 skill）

- **liveness probe 唔可以依賴可選功能**（K8s 原則）：8765 同時係 alerts MCP ＋ Electron 嘅 health ＋ settings 出入口 ⇒ 一關提醒，整個 sidecar 被誤判死。
- **一個服務同時做「健康探針」＋「功能介面」時，佢嘅生死唔可以由功能開關決定**。
- **背景 thread 內嘅失敗（bind）逃得過 caller 嘅 `try`** ⇒ 樂觀 log（`[ok]`）會變假成功；起完一定要 self-probe。
- **診斷 signature**：`serve.log` 反覆 startup 週期 ＋ 進程 StartTime 一直變 ＋ **8765 無 LISTEN**。
- **fingerprint 型 monitor 要有「持續時長」維度，但用桶化**（連續值＝疲勞、冇維度＝永久靜音），並要處理「刻意關機」語意。
- **改一行之前先數清有幾多個消費者**（本次 port 有 6 處 → 結論係「凍結」而唔係「加 resolver」）。
- **唔好喺未量測之前寫「根因 100% 確認」**；每個數字標快照時間；引用外部工具前先搵清正確路徑。
