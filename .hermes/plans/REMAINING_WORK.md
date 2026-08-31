# JARVIS 剩餘工作計畫書（REMAINING WORK）

> 2026-08-28 起草。原則：**做到晒為止**；遇到問題先上網查（GitHub issues → 官方 docs → 社群）再動手；**需要 SK 人手實測嘅全部留到最後**。
> 狀態：🔴 進行中 ｜ ⏳ 排期 ｜ 🟡 等 SK（最後先做） ｜ ✅ 完成

---

## H. 2026-08-29 Fragility Review（pass2）——三個月後最脆弱位 ⏳

> 完整報告：`.hermes/plans/2026-08-29-fragility-review-pass2.md`（cursor review，10 findings）

**✅ 已修（0.4.2，2026-08-29）：**
1. **H1 host config 抽出**——`%APPDATA%\Jarvis\host.json`（{python, jarvis_pc_dir}）+ env（JARVIS_PYTHON/JARVIS_PC_DIR）fallback；PYTHON/JARVIS_PY 統一用 SIDECAR_PY
2. **H2 settings 單一 writer**——`settings.save_settings_patch()`（dir-lock + atomic + pending-apply）；sidecar `POST /settings` endpoint（Bearer auth）；Electron settings:save 改 POST（fallback 直接寫）；self-monitor 統一用 patch；shell_app `_start_settings_apply_watch`（live wake_threshold 更新）——實測 POST → `settings applied: wake_threshold=0.47` ✓
3. **H3 Electron SPOF health**——`sidecarRunning()` 由 TCP connect 改 HTTP GET /health（防止 stale listener 當 healthy）

**剩低（記低，唔急）：** ML 依賴 pin 已做（torch<3 + aec/speaker extras）、Mage-VL revision pin 已做、voice_status ISO + stale 灰已做（0.4.3）、settings clamp 統一已做（0.4.3）、activity 單一 writer（lock 已加）、Hermes bridge auth rotation 文檔、secrets DPAPI、tk settings_ui 凍結/移除、settings.html load/collect field-map（pass1 #3 skip）。

---

## A. Phase 8 JARVIS ONE 剩餘（Electron 一個 app）

### A1. 8.2 完整 — Settings 搬遷 tkinter → Electron Iron Man HTML 🔴
- **現狀**：Companion window 已做（Iron Man HTML + reply 串流）。Settings 仲係 tkinter（settings_ui.py 1182 行）。
- **做法**：
  1. 新 `settings.html`（Iron Man 風格，沿用 companion.html 語言）——常用設定優先：wake threshold / mic device / TTS device / AEC 開關+reference / speaker gate / ASR provider / 熱鍵
  2. preload IPC：`settings:load`（讀 settings.json）→ `settings:save`（寫 settings.json，經 save_settings 邏輯保留未知鍵）
  3. tray menu 加「設定」→ 開 settings.html window
  4. 進階 tab（LLM/Hermes/Alerts/音訊診斷）逐個搬，最後 tkinter settings_ui 移除
- **驗證**：開設定改 threshold → serve 即時生效（wake_debug thr 變）；無 tkinter 視窗
- **⚠️ 上網查**：Electron frameless 窗 drag 區域、IPC contextBridge 模式

### A2. 8.3 語音 sidecar IPC 🔴
- **做法**：Electron ↔ sidecar 狀態通道——sidecar 寫 `%APPDATA%\Jarvis\voice_status.json`（wake on/off、STT 中、TTS 中）或者 sidecar HTTP /status 端點；Electron 每 1-2s 讀 → HUD/Companion 顯示狀態
- **驗證**：喊「hey jarvis」→ Companion 狀態變「● 聽候中 → ● 處理中」

### A3. 8.4 HUD 融合 ✅（2026-08-29 完成）
- **做法**：HUD overlay + Companion 共用 CSS/JS 體系（一個 `hud-theme.css`）；dock/遊戲隱藏保留
- **完成**：companion.html / home.html / settings.html 已 link `hud-theme.css`（196 行共用 theme）✅；**dock 已整個移除（0.4.9）**；HUD 主窗遊戲隱藏保留（checkActivity）✅；renderer/index.html 視覺已統一（同一 `--blue #00aaf8` / Orbitron+Rajdhani / rgba(0,170,248) 透明度系）——唔 link hud-theme.css 係避免全屏 overlay CSS 衝突，屬刻意設計
- **驗證**：視覺統一 + 遊戲中全部隱藏

### A4. 8.5 MCP 整合（Hermes ⇄ JARVIS 雙向）🔴
- **做法**：`mcp_alerts_http.py` 加 tools：
  - `mcp_jarvis_speak(text)`——叫 Jarvis 唸（限頻 ≤1 req/2s、playing 拒絕、只限 SK DM source）
  - `mcp_jarvis_wake_status()`——wake 狀態/裝置
  - `mcp_jarvis_sensors()`——GPU/CPU（NVML 已有）
  - `mcp_jarvis_alert(phrase)`——推 alert 入隊
- Hermes `mcp_servers` config 已註冊 jarvis-alerts——擴展 tools 即可
- **驗證**：Hermes 內 call `mcp_jarvis_speak` 成功 + 安全 gate 生效
- **⚠️ 上網查**：FastMCP tool 定義 + Hermes MCP env 過濾

---

## B. Mage-VL「眼」整合 🔴

- **現狀**：spike 完成（✅ 本地跑通：load 10.4s / VRAM +9.5GB / inference 0.86-3.9s；圖理解正確）。⚠️ 需要 `check_imports` monkeypatch（streammind_gate mamba_ssm 問題）。
- **做法**：
  1. `jarvis/mage_engine.py`——MageVLEngine：lazy load（第一次用先載）、`understand_image(path, prompt)`、frame-sampled video
  2. settings `mage_enabled`（default off——9.5GB VRAM 唔可以常駐；用先載）
  3. 整合入 Hands/指令：SK 講「睇呢張圖」→ Mage-VL 理解 → 回覆
  4. **Streaming gate（進階）**：codec-native 需要 mamba_ssm（Windows 唔 practical）——deferred，記低
- **驗證**：MageVLEngine.understand_image 真圖出真描述
- **⚠️ 上網查**：transformers 5.x dynamic module import workaround、Windows mamba_ssm 替代

---

## C. 擴展連接 ❌（2026-08-31 SK 決定：用 Discord 就夠，取消）

~~C1 WhatsApp / C2 Telegram / C3 Hue / C4 MCP servers~~ —— **刪除**（SK：「del 5, we just use dc for now」）

---

## D. Phase 7 易做項 🔴

- **D1. Hermes push/notify** ✅（2026-08-29 確認已由 sidecar 完成）：sidecar `_ensure_alert_poller` 起 `scripts/hermes_alert_poll_loop.py`（pythonw，~1s interval，peek→Hermes TTS→ack），比 Hermes cron（gateway tick ~60s、min 1m）快好多。serve.log 確認 `alert poller ~2s` spawn；實測 enqueue→4s 內 lease。**注意：唔好再加 Hermes cron poll**（會同 poller race / double speak）；用 MCP tools（peek/ack/speak）係俾 Hermes agent 主動查，唔係取代 poller。
- **D2. Minecraft ready alert**：偵測 MC 啟動（javaw.exe 出現 + 標題「Minecraft*」→ 「Minecraft is ready, sir.」）——activity_monitor 已 detect playing；加「首次偵測」alert
- D3. HWiNFO SHM / GPU-Z failover：💤 重，deferred

---

## E. 自我迭代 🔴

- **E1. 已做**：self-monitor script + cron（wake 誤觸/STT miss/rtf/AGC + threshold 自動調）
- **E2. STT 準確度追蹤**：SenseVoice 轉錄後用戶更正（asr_repair 命中率）統計 → 自動加 hotwords
- **E3. Response 延遲統計**：喊完 → 有聲時間（wake_debug 到 TTS 開始）→ 寫 log → 自動提示 bottleneck

---

## F. Cursor Review 剩餘 MED/LOW 🔴

- F1. `tts_output_device` int → name resolve（AEC 自動匹配用）——✅ 已做（handoff 確認）
- F2. `voice_call_state.json` 加 file lock（atomic write 已做，lock 未）——✅ 已做（activity_monitor singleton lock）
- F3. pycaw 失效時 fail-closed 選項 ✅（2026-08-29）：settings 加 `vc_fail_closed`（default False=保持 fail-open）；activity_monitor `detect_voice_call` pycaw import/API 失敗 → 讀 settings 決定（True=當 voice call mute / False=唔 mute）；settings.html + clampSettingsPatch 已加 toggle。實測：set true → `_vc_fail_closed()` True；還原 false OK
- F4. `_vc_gate_stop` 喺 quit_app 已做（✅）——確認
- F5. settings_ui 加 AEC 已做（✅）

---

## G. 需要 SK 人手實測（🟡 全部留到最後）

1. **Tier 1 完成指標**：BGM 30s 0 誤觸 + 喊完→有聲 ≤3s（AGC 後 wake 叫醒）
2. **A4 聲紋 enrollment**（mic 穩定後）
3. **AEC / voice_call 真實場景**（voice call 中對方聲唔觸發 + 自己叫照醒）
4. **8.1 tray / 8.2 Companion 實際顯示**（撳 tray menu 睇）
5. **擴展連接**：提供 WhatsApp/Telegram/Hue credentials

---

## I. Self-Evol 自我進化（新，2026-08-29 深夜 SK 提出）

- **計畫**：`.hermes/plans/2026-08-29_self-evol.md`（Phase A 自我審視 / Phase B 改進管道 + 能力擴展層 / Phase C 閉環 / **Phase D Autonomy Ladder v2 / Phase E Clarification Gate v2 / Phase F Prompt Pipeline v2**）
- **三階段 review 已跑**（反方/正方/裁判）——最終結論：
  - Phase 1 = **安裝永遠人手**（full auto 推 Phase 2）
  - 安全用**信任分層**：🟢 官方 vendor URL-only（唔執行本地 code）｜🟡 Nous PR-reviewed catalog（SK 只答「要唔要」，唔使審）｜🔴 Community skill（預設拒絕）
  - MCP 安全研究實證（Invariant Labs Tool Poisoning / CVE-2025-49596 / 1,862 無認證 servers）支持保守方向
- **80-POV 外部研究已完成**（2026-08-30）：`.hermes/plans/2026-08-30_self-evol-research-80pov.md`——方向獲業界/學界共識支持；計畫已按研究加 **R1-R9 修訂**（Task 0 memory schema / 執行次序調整 / eval 隔離 / 審批分層 / 成本上限 / fail-closed / 命中率預期 / 紅線）
- **第二輪 60+ POV 研究已完成**（2026-08-30）：`.hermes/plans/2026-08-30_self-evol-research-round2.md`（5 agent：self-modification / spawning / clarification / prompt optimization / earned autonomy）——**Phase D/E/F 全面修訂 v2**（R10-R14：per-operation 分級 / 執行型 eval gate / Clarification Gate 一輪為主 / Prompt Formatter+Optimizer 兩層 + injection 防禦 / 審批疲勞量化）
- **第三輪實戰案例研究已完成**（2026-08-30）：`.hermes/plans/2026-08-30_self-evol-research-round3.md`（4 agent：自我進化部署 / 通知報告設計 / Clarification+Prompt 生產 / 自主度控制，80+ 來源）——**POV review 判決 8:2 支持方向**，補 **R15-R19**（writeback 管道 / memory poisoning 防禦 / clarification untrusted / 轉換規則+證據包 / 三層報告通道+watchdog）
- **執行次序（三輪研究後）**：Task 0-2（schema + code + 合成數據測試）即刻可做 → Task 3-4 cron 等數據夠（≥7 日、每日 ≥5 事件）先上 → **Task 6 Clarification Gate（Phase E，最先落地）→ Task 7 eval gate 基建（Phase D 先決）→ Task 8 Prompt Pipeline（Phase F，等有子 agent 流程）→ Task 9 Autonomy Ladder（Phase D，最後）**；Phase A 按 R15 加入「寫入管道」（唔止報告）
- **狀態**：🟡 **Task 0-2 + Task 6 完成（2026-08-30）**：self_review.py + schema + 14 個單元測試全過 + 真實數據驗證（fingerprint=NONE）；**Task 6 Clarification Gate（Phase E v2）完成**：`src/jarvis/clarify.py`（EVPI 觸發 + 2 輪上限 + conservative fallback + precision log）+ `tests/test_clarify.py` **20 個測試全過**；**下一步 = Task 7 Golden Set + Eval Gate 基建（Phase D 先決）**，或等數據夠（≥7 日）開 Task 3-4 cron
- **狀態（2026-08-30 晚上 session）**：✅ **Task 3-9 全部完成**：
  - **Task 3**：fingerprint cron 已上線——`%LOCALAPPDATA%\hermes\scripts\jarvis_self_review_fp.py`（script+monitor 同一檔，monitor pattern 零成本）+ Hermes cron `jarvis-daily-self-review`（job 8ef18463dc73，`0 9 * * *`，deliver origin=Discord；fingerprint=NONE 時 agent 唔醒）
  - **Task 4**：`plans/self-evol-SUGGESTIONS.md`（append-only 建議檔，R5 格式 [id] 問題→建議→風險→驗證→回滾）+ cron prompt 內嵌 A0 人話報告格式（零打擾/唔准 jargon/EVPI 浮出判斷）
  - **Task 5**：全鏈驗證——232 tests 全綠 + 手動 cron run 已發射
  - **Task 7**：`src/jarvis/eval_gate.py`（執行型驗證：pytest/py_compile/node --check；`--suite/--all/--repeat/--hash`；R11 多次 run 統計）+ `plans/self-evol-golden-set.md`（golden/regression/stress 三類，frozen + 人手標註）+ `tests/test_eval_gate.py` **7 tests 全過**；golden suite 實跑 74 passed；hash `eb3c25e3496e7361`
  - **Task 8**：`src/jarvis/prompt_pipeline.py`（L1 Formatter 五段結構化 + format_simple 模板跳過 + L2 PatternStore 只收錄 score≥0.8 + INVARIANT_BLOCK injection 防禦 + scan_sensitive 敏感模式掃描→命中降級原版）+ `plans/prompt-patterns.md` + `tests/test_prompt_pipeline.py` **11 tests 全過**
  - **Task 9**：`src/jarvis/autonomy.py`（per-operation 分級 L1a/L1b/L1c + 複合閘 promotion + hysteresis 0.90/0.85 + 即時自動 demotion + H_auth log + kill switch + rate_alarm 速率監控）+ `tests/test_autonomy.py` **13 tests 全過**
  - ⚠️ 4 個 pre-existing 測試失敗已修（settings_ui 5 tabs / asr_repair garbled `|-]` early repair / test_brain 兩個 mock hermes_enabled）——**232 tests 全綠**
- **pass2 脆弱位（2026-08-30）**：① self_review.py 依賴 self_monitor.log 文字格式（格式耦合）② trend 缺日處理 ③ _TREND_METRICS 硬編碼 ④ clarify.py `_safest_option` heuristic ⑤ **clarify.py 未接入 agent 流程**（standalone library；接 Hermes clarify tool / sidecar brain 要寫 adapter）⑥ clarify precision log 冇 consumer（E4 校準 pipeline 未建）⑦ `_DEFAULT_ASSUMPTIONS` 硬編碼 ⑧ **eval_gate GOLDEN_SUITES + 路徑硬編碼**（改 suite 要改 code + 同步 golden-set.md，兩處 drift 風險；`--lock` 未實作）⑨ **prompt_pipeline Optimizer 本體未實作**（只有 Formatter + PatternStore + injection 防禦框架；GEPA/DSPy 集成係後續）⑩ **autonomy promote mapping 跳過 L1a**（sandbox 未建，L0 直接→L1b；建好 sandbox 要改）⑪ **4 個新 module 全部 standalone 未 wiring**（最大脆弱位：基建完成但未接入 Hermes 主流程——三個月後可能唔記得點用）⑫ cron monitor script ERROR 分支靠 stderr 穩定性（stderr 每次唔同會令每 tick 誤判 changed）

### ✅ Wiring 完成（2026-08-31 session）——pass2 ⑧⑪ 已修

- **⑧ eval_gate --lock 實作**：`check_doc_lock()` 對比 `self-evol-golden-set.md`（doc）同 `GOLDEN_SUITES`（mapping）列出嘅 test files（basename normalize）；drift 即 fail。**GOLDEN_SUITES 擴大到全核心**（golden=21 files pytest+29 py_compile / regression=2 / stress=3）；`test_eval_gate.py` 刻意唔入 golden（會 nested recursion 實測）；golden-set.md 已同步。新 hash `4418ea8cd1a9b12a`
- **⑪ 4 個 module wiring 完成**：
  1. **eval_gate → CI gate**：jarvis-pc AGENTS.md Commands 加「改動後強制 `eval_gate --lock + --all`」+ skill `jarvis-self-evol-ops`（完整 SOP）
  2. **clarify → MCP tool**：`jarvis_clarify_gate`（8765，stateless EVPI gate；只揀 impactful questions；fallback 對齊 ClarifySession.proceed；答案當 untrusted R17）
  3. **autonomy → 實際 gate + MCP tool**：`AutonomyState` 加 **persistence**（`%APPDATA%\Jarvis\autonomy_state.json`，promote/demote/kill_switch 後 save，restart 唔 reset）；`jarvis_autonomy_state` MCP tool（level/sandbox/H_auth events）
  4. **prompt_pipeline → delegate_task 規則**：skill 寫明 spawn subagent 前用 `format_task`/`format_simple` 五段式 + injection 防禦
- **附加修復**：gpu_health cooldown sentinel bug（`_last_emit.get(reason)` 用 None——0.0 會喺 boot<cooldown 時誤擋第一次 emit，實測 flaky 根因）
- **驗證**：全套 259 passed（246+13 新 tests）+ `eval_gate --all` 全綠（golden 239+py_compile 29 / regression 9 / stress 59）+ `--lock` 一致（24 files）
- ⚠️ **MCP tools 要 restart sidecar（8765）先生效**——等 SK 批准（Ask first：重啟服務）

### ✅ Bug Review 修復（2026-08-31，獨立 reviewer 2 個，全部 fail-closed findings 已修）

- **mcp_alerts_http.py（reviewer A，7 findings 全修）**：
  1. impact string truthiness coercion（`"false"`→True）→ 只收 bool 或 `"true"/"false"` literal
  2. malformed gain 靜默 drop unknown（連保守假設消失）→ tolerant parse + default，唔 drop
  3. options string 逐字符拆 → 必須 list[str]
  4. confidence 冇 error handling/clamp → try/except + isfinite + clamp [0,100]（NaN 會整壞 JSON）
  5. fallback 冇 merge caller assumptions → `force_proceed_assumptions`（對齊 ClarifySession.proceed）
  6. autonomy_state_impl 未驗證 h_auth log 內容 → 只收 dict + 單行 4KB cap
  7. Bearer `!=` → hmac.compare_digest（constant-time）
- **autonomy.py（reviewer B，HIGH 全修）**：`_save()` 回傳 bool + temp+os.replace 原子寫；kill_switch/demote save 失敗 loud log（磁碟舊高 level restart 還原 = fail-open）；promote 冇 H_auth 審計記錄 → 拒絕（R18）；promote save 失敗 rollback；`_demo` 改 temp path（唔掂真實 APPDATA）；`_load` L1a+無 sandbox → fail-closed L0
- **eval_gate.py（reviewer B）**：`_DOC_TEST_RE` 接受全路徑 mention；mapping 全空 fail-closed；--lock stat 檔案存在 + warn 未覆蓋 tests/；重複 basename detect
- **附加**：`test_clarify_stats.py` 加入 golden suite（新 E4 consumer 受 CI gate 保護）
- **驗證**：全套 **285 passed**（+17 新 adversarial tests）+ eval_gate --all 全綠（golden 254+py_compile 30 / regression 16 / stress 65）+ `--lock` 一致；新 hash `c4db6e03fa849985`

### ✅ Clarify precision log consumer（E4，2026-08-31）

- `src/jarvis/clarify_stats.py`（新）：讀 `%APPDATA%\Jarvis\clarify_log.jsonl` → precision（changed_plan True/False 比例）+ questions/rounds/assumptions 統計 + `--fingerprint`（monitor pattern：NO_DATA 或 PRECISION <rate>|<asked>|<n>）
- `tests/test_clarify_stats.py`：9 tests 全過（empty/malformed/precision/unrecorded）
- ⏳ 等真實數據累積（而家 log 得 1 條）——數據夠先接 cron monitor（R2）

### ✅ 資源優化 + 系統審視修復（2026-08-31 下午，SK「fix them all」）

- **記憶體大減（SK 指出 5.5GB 太多）**：SenseVoice CPU 載入實測 **~3.5GB**（torch +0.5GB / funasr +0.8GB / 模型 +3.5GB）——新增 `stt_preload`（default **False** = lazy load，第一次喚醒先載，thread-safe lock）；startup 唔再預載。**實測：Private 5.5GB → 1.9GB（-65%），WorkingSet 1.9GB → 454MB（-75%）**
- **UnicodeDecodeError 徹底修**（self-evol TREND-err finding）：8 個 subprocess 位加 `encoding="utf-8", errors="replace"`（taskkill ×2 / powershell Get-CimInstance / Get-StartApps / WScript / nvidia-smi / pgrep / TTS child）——中文 Windows GBK 輸出不再 kill reader thread；test_router warning 清零
- **Mic 健康偵測（#4）**：wake.py heartbeat 連續 3 次 rms≈0 → voice_status.json 寫 `mic_signal_ok=false`（恢復自動 flip 返 True）——HUD/MCP 顯示真實 mic 狀態，唔再「armed=True 但 mic 冇訊號」
- **Sidecar watchdog（#7/#8）**：Hermes cron `jarvis-sidecar-health`（job `6a98a79be95f`，every 2m，monitor pattern 零成本）——8765 DOWN 先醒 agent 報告
- **Git commit（#5）**：jarvis-pc 全部工作 commit `290ca61`（110 files，含 self-evol + bug fixes + 之前 session 工作；secrets scan 乾淨）
- **Hermes memory 清理（#15）**：personal 98%→92%、user 98%→90%（合併重複報告偏好）
- **#2 SenseVoice remote code warning**：查證為 transformers 載入 warning，fallback 到 pretrained params 照 work（serve.log 有成功 transcribe 證據），無功能影響——記錄唔修

### ✅ 未完成項清單處理（2026-08-31，SK「do 4,6,8,10,11,12 / del 5」）

- **#4+#12 Settings 完成**：settings.html 加 `stt_preload` toggle（load/save 全通）；tkinter SettingsWindow **凍結**（shell_app `open_settings` → 統一「由 Electron HUD 管」，import/attribute 移除；settings_ui.py 保留做 rollback）
- **#6 L1a sandbox 決定 + 實作**：**Docker Desktop 勝出（8:2）**——WSL2 共享內核可讀 `~/.ssh`（R18 實測教訓），Docker 有真 namespace 隔離。新 `src/jarvis/sandbox.py`（SandboxRunner：lazy 開 daemon、`--network none`、只 mount allowlisted workdir、無 host env/credentials、fail-closed）+ 9 tests
- **#8 prompt_pipeline Optimizer 本體完成**：`src/jarvis/prompt_optimizer.py`（GEPA 式反思進化：mutate→score→elitism；score-driven 先入 PatternStore；INVARIANT_BLOCK 不可改；只掃 mutation 新增敏感；NaN/範圍 guard）+ 10 tests
- **#10 Mage-VL video 完成**：`MageVLEngine.analyze_video_sampled`（OpenCV 抽幀 + 逐幀理解 + timestamp 合併）——替代 deferred mamba_ssm streaming（Windows 唔 practical）+ 6 tests
- **#11 GPU failover 完成**：`gpu_metrics_with_fallback`（nvidia-smi → HWiNFO SHM temp/VRAM/util → {}；**GPU-Z 冇 public API，記錄唔做**）+ 7 tests
- **#5 刪除**（C 擴展連接 WhatsApp/Telegram/Hue）——SK 決定「用 Discord 就夠」；建議從 REMAINING_WORK 移除
- **驗證**：全套 **317 passed**（+32 新 tests）+ eval_gate --all 全綠（golden 26 files + py_compile 31）+ --lock 一致（28 files）；hash `8db6be8acd0e85c6`

---

## 執行次序（一路做到晒）

1. **A1 settings 搬遷 MVP**（最常用設定 HTML）→ A2 voice_status IPC → A4 MCP tools
2. **B Mage-VL engine** 整合
3. **D1 Hermes push** → **D2 Minecraft alert** → **E2/E3 統計**
4. **F1/F2 修復** → **A3 HUD 融合**
5. 最後：**G 全部 SK 實測清單** + C 擴展連接（等 credentials）
