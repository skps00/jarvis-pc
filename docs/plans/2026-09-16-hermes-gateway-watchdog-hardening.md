# Plan: Hermes gateway watchdog 加固（pre-flight ＋ 自癒 ＋ 零彈窗 ＋ 報告講真話）

日期：2026-09-16｜狀態：待 review → 派 cursor 實作
目標檔（live）：`C:\Users\skps9\AppData\Local\hermes\scripts\hermes-gateway-watchdog.ps1`
（skill 副本：`skills/devops/hermes-windows-operations/scripts/hermes-gateway-watchdog.ps1`）

## 1. 背景（2026-09-16 實測，A 級證據）

- 07:39 開機 → 07:41-07:55 watchdog 每 2 分鐘試拉起 gateway **6 次全部失敗**（4 次被 crash-loop guard 擋），
  每次 `WScript.Shell.Run` 拉唔到 interpreter → **彈 Windows Script Host 對話框 error 80070002**（SK 見到 6 次）。
- 真因：Surfshark 防毒 09-14 13:52 誤判 `hermes-agent\venv\Scripts\python.exe` 為
  `Drop.Win64.UserProfileSelfRun.710` 並刪走；uv trampoline 指向嘅 uv CPython 3.11 `python.exe` 亦唔見。
- 07:57 SK 叫 cursor 重建 venv 後恢復。
- **報告機制講大話**：watchdog reporter cron（`c965f9da778f`）07:58 出嘅報告寫
  「死咗 → 自動復活」×6——其實 6 次全部失敗（reporter 只讀 events JSONL 嘅 `action: restart`，
  **冇核實 gateway 真係返咗**）。同一個報告仲印咗 stale 心跳（引用 09-11 嘅 diag 行）。

## 2. 範圍（逐項）

1. **Pre-flight interpreter 檢查（每次 tick，早退前唔使做，只在「判定死亡、準備重啟」時做）**
   - 驗 `hermes-agent\venv\Scripts\python.exe` **存在** 且 **跑得**：
     `& $venvPy -c "import sys"`，timeout 15s、`-WindowStyle Hidden`／hidden 方式（**零彈窗**）。
   - 失敗 → 標記 `interpreter_broken`。
2. **自癒（bounded，只喺 interpreter_broken 時）——要修兩件 artifact，唔止一件**
   （2026-09-16 review blocker 修正：壞嘅係 **venv trampoline** `hermes-agent\venv\Scripts\python.exe`
   （45,568 B）＋ **uv base CPython** `%APPDATA%\uv\python\cpython-3.11-*\python.exe`（91,648 B）兩層；
   淨跑 `uv python install --reinstall` 只補返 base，trampoline 仲係缺 → 仍然 80070002。）
   - 步驟 1：讀 `hermes-agent\venv\pyvenv.cfg` 攞 `version_info`（例如 `3.11`）→
     `<uv> python install <ver> --reinstall`（uv 路徑：`%LOCALAPPDATA%\hermes\bin\uv`；全部 hidden）。
   - 步驟 2：`<uv> venv --allow-existing --python <ver> "…\hermes-agent\venv"` 重建 venv launcher
     （`--allow-existing` 保留 site-packages；今日 07:57 成功 recovery 就係 `uv python install 3.11 --reinstall`
     ＋ `uv venv --allow-existing`，見 HANDOFF 2026-09-16）。
   - 步驟 3：再驗 trampoline 跑得；仍然失敗 → `heal_failed`（含兩步 stderr 摘要）＋**唔好** call VBS。
   - 每次 tick 最多一次 heal；成功／失敗都寫入 `state\gateway-watchdog-events.jsonl`（新 `action: heal`）。
3. **重啟後核實（報告講真話）**
   - call VBS 之後，poll `http://127.0.0.1:8642/health`（最多 ~90s，每 5s 一次）：
     200/401/403 → 事件寫 `result: "success"`；逾時 → `result: "failed"`（連最後 error 摘要）。
   - `action: restart` 事件同時寫 `attempt_pid`（新 process PID，如攞到）。
   - reporter（`scripts\gateway_watchdog_reporter.py`）改為**只讀 `result` 欄**：
     `success` → 「已自動復活」；`failed`／缺欄（舊事件）→「⚠️ 重啟失敗，需要人處理」；
     `heal` 事件 → 一行「自癒嘗試：成功／失敗」。
4. **零彈窗（login 路徑都要守住）**
   - 新增 `scripts\hermes-gateway-launch-guard.vbs`：先驗 venv python 存在＋可跑（用 `WScript.Shell.Run(..., 0, True)`
     取 exit code），OK 才 call 官方 `gateway-service\Hermes_Gateway.vbs`；唔 OK 就寫 log（`logs\gateway-watchdog.log`）
     後 `WScript.Quit 0`——**永遠唔會彈 WSH 對話框**。
   - watchdog 每次 tick 做「ensure guard」：若 `Startup\Hermes_Gateway.vbs` 未指住 guard（例如 `hermes update`
     重寫過），就重寫佢（idempotent，內容 = 現有 Startup VBS 形狀但 target 指 guard）。
   - watchdog 自己嘅 restart 一律 call guard，唔直接 call 官方 VBS。
5. **唔改**：crash-loop guard 上限語意（3/10min）、`StartWhenAvailable`、process/port 雙檢邏輯、
   task action（wscript + `hermes-gateway-watchdog-launch.vbs`）、UTF-8-with-BOM + CRLF 要求。

## 3. 非範圍

- 唔改 Hermes core（`hermes-agent\**`）、唔改 `config.yaml`。
- 唔代 SK 加 Surfshark 排除目錄。
- 唔改 HUD sidecar（另一份 plan）。

## 4. 驗收標準（要跑，唔可以只睇 code）

1. `powershell -NoProfile -ExecutionPolicy Bypass -File <copy>` 語法／執行零 error（用**沙盒副本**跑，
   pitfall：唔可以對真 gateway 測 restart——副本要換成 fake process pattern ＋ fake VBS ＋ fake health URL）。
2. **三情境沙盒實測（同一份副本）**：
   - (a) interpreter OK → 照舊 call guard（log 有 RESTART），事件有 `result: success`（fake health server 回 200）。
   - (b) interpreter missing（fake venv 路徑）→ **唔會** call guard、寫 `interpreter_broken` ＋ 試 heal（fake uv stub 回非零）→ 寫 `heal_failed`、**零彈窗**。
   - (c) heal 成功（fake uv stub 造返個 fake python.exe）→ 之後 tick 正常 restart、事件 `result: success`。
3. Reporter：用 3 行假事件 JSONL（success／failed／無 `result` 欄）跑 `gateway_watchdog_reporter.py`，
   確認輸出三分支文字正確（failed 唔可以再寫「已自動復活」）。
4. Guard VBS：`cscript //nologo hermes-gateway-launch-guard.vbs` 對 fake target 路徑跑 —— exit 0、零對話框、
   log 有行；對 OK 路徑跑 → 會 call 官方 VBS（fake 版）。
5. 真機部署後：一個 tick 內 `gateway-watchdog.log` 冇新增 RESTART（gateway 健康）、
   events 冇新行、`hermes gateway status` PID 不變。
6. 舊 live 檔備份：`hermes-gateway-watchdog.ps1.bak-<ts>`、`gateway_watchdog_reporter.py.bak-<ts>`。

## 5. 風險／最壞情況／還原

- 風險：watchdog 誤判（例如 pre-flight 太嚴 → 明明健康都當壞）→ 會唔 restart；或自癒亂郁 uv。
  → 守則：pre-flight 只在「已判定 gateway 死亡」之後才跑；heal 最多一次／tick 且有 60s 退避；
  一切照 crash-loop guard 上限。
- 最壞情況：watchdog 完全唔 restart → 等於今日（gateway 死要人手修）。**唔會比現狀差**。
- 還原：兩個 live 檔有 `.bak-<ts>` 即時覆蓋就返舊版；task／Startup guard 改動都可逆
  （Startup VBS 原本內容有備份）。

## 6. 未解

- 「點解 Surfshark 誤判 uv trampoline」→ 未有定論（已知 threat 名／時間；Surfshark DB 嗰條 threat 仍 `New`）。
- 若 `uv` 自己唔見（同類 AV 事件），heal 會失敗 → 只會 log，唔會自我毀滅（符合 fail-safe）。

## 7. 驗收結果（2026-09-16 09:33，全部實測）

**Cursor 實作 → 我獨立沙盒驗收。第一輪捉到 3 個真 bug**（cursor 自己嘅 harness 冇捉到；因為佢用真 python 都當壞）：

| # | Bug | 證據 | 修法 |
|---|---|---|---|
| 1 | `Test-Interpreter` 永遠 false（連真 python 都當壞） | log `PREFLIGHT: interpreter_broken (…pythoncore-3.14-64\python.exe)` | `Start-Process -ArgumentList @('-c','import sys')` → array join 甩引號 → 改**直接呼叫** |
| 2 | `Invoke-UvHidden` 拋 exception → 自癒永遠 failed | event `heal failed / uv_python_install_failed / 方法引動過程失敗…'Trim'` | redirect + `.Trim()` → 改 `(& $uv @args 2>&1 \| Out-String)` |
| 3 | Guard VBS probe 一樣爆 → **永遠 SKIP（連 gateway 都唔會開）** | guard line 31 同款 `Start-Process -ArgumentList '-c','import sys'` | VBS 自己砌引號：`sh.Run("""" & py & """ -c ""import sys""", 0, True)` |

**獨立 harness（`%TEMP%\watchdog_sandbox_test2.py`，經 production 同一條 `wscript→cmd→powershell` 鏈跑）**：
`{'a': True, 'b': True, 'c': True, 'd': True, 'e': True, 'f_no_flash': True}`
- a：正常 → `restart` ＋ `result: success` ＋ call guard
- b：壞 + 自癒失敗 → `interpreter_broken` ＋ `heal failed (simulated failure)` ＋ **唔 call guard**（＝零彈窗）
- c：壞 + 自癒成功 → `heal success (ver=3.11)` ＋ `RESTART VERIFY: success (health ok)` ＋ call guard
- d：`HEAL SKIP: backoff (60 s)` 生效
- e：reporter 只有真 `result: success` 才寫「已自動復活」
- f：**0 個前景 console 閃窗**（偵測器正控：故意開可見 cmd 窗 → 捉到 3 次 `FLASH #`，證明 0 唔係 detector 壞）

**Guard 兩向測試**（patch 指向 fake 官方 VBS ＋ marker 檔）：
- 正常 interpreter → **call** 官方 VBS（＝修好之前會永遠 SKIP 嘅 bug 已解）
- `pythonNOPE.exe` → **SKIP**、寫 `GUARD SKIP: venv python missing`、唔 call（＝登入唔會再彈 WSH 對話框）

**真機上線（09:32-09:33）**：
- 備份：`hermes-gateway-watchdog.ps1.bak-20260916_093243`、`gateway_watchdog_reporter.py.bak-<ts>`、
  Startup `Hermes_Gateway.vbs.bak-20260916_093243`
- 上線：`.ps1` 14121 B（UTF-8 **BOM** ＋ CRLF；cursor 原檔無 BOM）＋ `Parser::ParseFile` → `PARSE OK`
- 一個真 tick（`wscript hermes-gateway-watchdog-launch.vbs`）：log 出
  `ENSURE_GUARD: Startup VBS -> …hermes-gateway-launch-guard.vbs`；**gateway PID 6764 不變、8642 HTTP 200、
  events 檔大小不變（冇 restart）、0 flash**；同期 `8765 /health` 正常
- skill 副本同步：`scripts\hermes-gateway-watchdog.ps1`（v3）＋ `hermes-gateway-launch-guard.vbs` ＋
  `gateway_watchdog_reporter.py`（v2）

未做：SK 人工驗收（例如故意斷 interpreter 睇自癒）——已用沙盒等效覆蓋，唔建議喺真機玩。
