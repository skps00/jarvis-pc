# Slice 1 換版 RUNBOOK（JARVIS 側車重啟循環修復）

> 2026-10-03 備料完成（Hermes 靜態自驗）。計劃全文：`2026-09-23_1500-jarvis-sidecar-restart-loop-fix.md`（v4，裁判 `v3_adequate = true`）。
> **狀態：材料齊、未換版。等 SK 一句「窗口 1 開」。**

## 0. 預檢結果（2026-10-03 19:5x 親跑）

| 檢查 | 結果 |
|---|---|
| Slice 1 四檔 diff | `hud/main.js` +25/−?、`hud/settings.html` +5、`src/jarvis/settings.py` +4、`src/jarvis/shell_app.py` +75 → **86 insertions / 23 deletions** |
| 代碼內容核對 | ✅ `_ensure_control_http()`（無條件起 HTTP）＋ `_probe_control_http()`（5 秒 self-probe，失敗寫 `hud_error.log`、**唔自動重試**）＋ `_ensure_alerts_mcp()` 只剩 alert 行為；`main.js` 判準收緊成 `body.ok===true && body.service==='jarvis'`；8765 凍結（`main.js clampSettingsPatch`、`settings.py _clamp`、`settings.html` readonly） |
| `node --check hud/main.js` | PASS |
| `env -u PYTHONPATH python -m py_compile src/jarvis/*.py` | PASS |
| 關鍵函數仍在 | `whenReady / ipcMain / globalShortcut / mediaBridge / listen(8771 / stopSidecar / spawnSidecar / startSidecarHealthCheck` → 39 處命中 |
| 還原 patch | ✅ `%LOCALAPPDATA%\hermes\backups\jarvis-sidecar-slice1-20261003.patch`（8,586 B；另有 09-23 舊版同大小 patch） |
| 現行 exe（rollback 用） | `hud/dist/JARVIS-ONE-0.4.13.exe`（72.5 MB，09-16 09:47）**保留**；`package.json` version = `0.4.13` |
| 換版工具 | ✅ `...\jarvis-hud-electron-editing-pitfalls\scripts\swap_hud_version.ps1`（09-16 實測 0.4.11→0.4.12→0.4.13） |
| 現狀 | JARVIS 行緊（4 個 `JARVIS ONE.exe` ＋ wrapper）、8765 `/health` = `{"ok":true,"service":"jarvis","wake_on":false}` |

## 1. 開工前（5 分鐘，Hermes 做）

1. `cronjob pause 6a98a79be95f`（`jarvis-sidecar-health`）—— 佢每 2–3 分鐘出指紋會污染歸因。⚠️ 佢**只報告、唔會自動救**。
2. 記 baseline：`serve.log` 行數、`netstat` 見 `8765/8770/8771/8642` LISTEN、跑緊嘅係 0.4.13。
3. 確認 SK **唔打機**（窗口 1 要開 HUD）＋ activity = idle。
4. 確認 `alert_voice=false`、`alert_tts=hermes`（現值），並記落嚟做還原基準。

## 2. Task 3：打包＋換版（夾喺兩個窗口之間，SK idle）

```bash
# 2a. bump hud/package.json 0.4.13 -> 0.4.14（patch 工具，唔好手改）
# 2b. build（零閃窗，經 VBS hidden wrapper）
cd "C:/Users/skps9/Documents/Code_Project/jarvis-pc/hud" && npm run dist
# 2c. 驗產物存在
ls -la "C:/Users/skps9/Documents/Code_Project/jarvis-pc/hud/dist/JARVIS-ONE-0.4.14.exe"
# 2d. 換版（kill 全部 JARVIS* → 開新 → 驗 health/ports → 更新 3 個 .lnk）
powershell -NoProfile -ExecutionPolicy Bypass -File "<skill>\scripts\swap_hud_version.ps1" -Version 0.4.14
```

- ⚠️ 跑緊嘅 portable exe 會鎖住自己個檔 → **一定要 bump version**（新檔名）先 build。
- ⚠️ 單例鎖：第二次啟動會靜默 quit（exit 0、冇 process）＝ 易假判「成功」。驗證要用 **process StartTime 變新** ＋ 4 個 port LISTEN。
- 驗收要證明「跑緊嘅係新 build」：`Get-CimInstance Win32_Process` 睇 `%TEMP%\<hash>\JARVIS ONE.exe` 路徑，或 exe 版本。

## 3. 窗口 1（HUD 開，15–20 分鐘）

| # | 驗收項 | 方法 | 通過條件 |
|---|---|---|---|
| 1 | 循環消失 | 15 分鐘內量：serve PID、`serve.log` delta、`Get-NetTCPConnection 8765 -Listen`、`/health` | 四者一致：PID 不變、delta=0、LISTEN 在、health 200 |
| 2 | `alert_voice=false` 仍健康 | 同 #1（現況值） | 冇 kill／respawn |
| 3 | `alert_voice=true` 仍健康 | 改值 → **kill serve** → 確認以新閘 boot 之後 8765 仍 LISTEN | 冇 kill／respawn；測完還原 `false` |
| 4 | 閘② `alert_tts=piper` ＋ `alert_voice=true` | 同上 | 冇 kill／respawn；測完還原 `hermes` |
| 6 | 真死機（exit path） | kill serve PID | **≤15 秒** respawn；⚠️ 相鄰 kill 測試**隔 >60 秒**（`main.js` 60 秒 crash-loop rate-limit） |
| 7 | **health path 負控（＝計劃 Task 0）** | **先 stopSidecar → 起 dummy HTTP 佔 8765（答 `{"ok":true,"service":"jarvis"}` 或 503）→ 觀察** | 90 秒內 Electron 主動 kill＋respawn（證明判準冇變「永遠健康」）；以 `hud_error.log` 為證。**做完交還 8765、殺 dummy** |
| 10 | 設定視窗復原 | 開 Settings | 金鑰顯示解密值（唔再見 `dpapi:`）；儲存 response 冇 `fallback:true` |
| U1 | spawn→LISTEN 延遲 | 250 ms 輪詢直至首個 200 | **<5 秒**（若 >90 秒 ⇒ 收緊判準會殺健康 sidecar ⇒ 設計要重審） |
| U2 | bind 衝突可觀測性 | 佔 8765 時 spawn | `serve.log` 見到 bind error |
| 11 | SK 主觀（**唔可作唯一證據**） | 打機／打字 | 同 #1–#7 客觀訊號一齊睇（4 個 confounder：GameInput／USB 省電／TRCC／Surfshark） |

**負控鐵律**（skill §20）：kill 完一定要 assert `8765` 真係 free（netstat）＋ assert dummy 真係佔到 —— 否則「健康」係假綠。

## 4. 窗口 2（HUD 關，≥35 分鐘）

| # | 驗收項 | 通過條件 |
|---|---|---|
| 8 | spawn 失敗負控（bogus python path，先 `mv %APPDATA%\Jarvis\host.json` 令 env 生效；測完還原） | `hud_error.log` 有 error ＋ crash-loop backoff（唔會永久停） |
| 9 | monitor 桶化（Slice 2 之後才驗） | 令 8765 持續 DOWN → 指紋由 `t=<5m>` 跨到 `t=30m`（叫醒一次）→ 回 UP；順手驗 HUD 關 ⇒ 印 `OFF`、唔叫醒 |

⚠️ 窗口 2 需要 **Slice 2（monitor 桶化）已寫**；Slice 1 換版本身唔需要窗口 2。

## 5. 還原（逐項可驗）

| 改動 | 還原 | 驗證 |
|---|---|---|
| Slice 1 四檔 | `git checkout -- hud/main.js hud/settings.html src/jarvis/settings.py src/jarvis/shell_app.py`，或用 patch `backups\jarvis-sidecar-slice1-20261003.patch` | `git status` 乾淨；重跑 py_compile／node --check |
| 換版 | `swap_hud_version.ps1 -Version 0.4.13`（舊 exe 仍在 `dist\`） | 4 個 port LISTEN ＋ health 200 ＋ 3 個 .lnk 指返 0.4.13 |
| settings 改值測試 | sidecar `POST /settings`（單一 writer）還原：`alert_voice=false`、`alert_tts=hermes` | `GET /settings` 讀返原值 |
| cron | `cronjob resume 6a98a79be95f`；若 monitor_state 壞 → reset `last_output_hash` | 下一 tick 正常出指紋 |
| dummy 佔 port | 殺 dummy、確認 8765 交還 sidecar | `netstat` 見 sidecar PID LISTEN |

**本計劃零不可逆改動**（88 MB `jarvis_hud_activity.log` 原封不動，Slice B 另議）。

## 6. 換版前需要 SK 答（3 條）

1. **幾時做窗口 1**（要 15–20 分鐘唔打機、HUD 開）？
2. **Q3 常開面**：解耦之後 `GET /settings` 會回**解密後金鑰**、`/health` 免 token，語音 HOLD 期間呢個面會常開 —— 接受（建議）定要加 gate？
3. **Q2「刻意關機」語意**（Slice 2 用）：HUD 關住 ⇒ 印 `OFF`、唔通知 —— 同意？

（Q4 MCP 工具恢復可用＝預期；Q5 Slice B 唔急 —— 兩條唔阻換版。）
