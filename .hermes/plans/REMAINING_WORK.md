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

**剩低（記低，唔急）：** ML 依賴 pin 已做（torch<3 + aec/speaker extras）、Mage-VL revision pin 已做、voice_status ISO + stale 灰已做（0.4.3）、settings clamp 統一已做（0.4.3）、activity 單一 writer（lock 已加）、secrets DPAPI、tk settings_ui 凍結/移除、**Hermes bridge auth rotation 文檔 ✅（2026-08-31：docs/hermes-bridge-auth.md）**、**settings.html load/collect field-map ✅（2026-08-31：docs/settings-field-map.md，pass1 #3 skip 補返）**。

---

## A. Phase 8 JARVIS ONE 剩餘（Electron 一個 app）

### A1. 8.2 完整 — Settings 搬遷 tkinter → Electron Iron Man HTML ✅（2026-08-31 完成：settings.html + tkinter 凍結）
- **現狀**：Companion window 已做（Iron Man HTML + reply 串流）。Settings 仲係 tkinter（settings_ui.py 1182 行）。
- **做法**：
  1. 新 `settings.html`（Iron Man 風格，沿用 companion.html 語言）——常用設定優先：wake threshold / mic device / TTS device / AEC 開關+reference / speaker gate / ASR provider / 熱鍵
  2. preload IPC：`settings:load`（讀 settings.json）→ `settings:save`（寫 settings.json，經 save_settings 邏輯保留未知鍵）
  3. tray menu 加「設定」→ 開 settings.html window
  4. 進階 tab（LLM/Hermes/Alerts/音訊診斷）逐個搬，最後 tkinter settings_ui 移除
- **驗證**：開設定改 threshold → serve 即時生效（wake_debug thr 變）；無 tkinter 視窗
- **⚠️ 上網查**：Electron frameless 窗 drag 區域、IPC contextBridge 模式

### A2. 8.3 語音 sidecar IPC ✅（2026-08-31 完成：voice_status.json 由 sidecar 寫 + HUD/Companion 讀）
- **做法**：Electron ↔ sidecar 狀態通道——sidecar 寫 `%APPDATA%\Jarvis\voice_status.json`（wake on/off、STT 中、TTS 中）或者 sidecar HTTP /status 端點；Electron 每 1-2s 讀 → HUD/Companion 顯示狀態
- **驗證**：喊「hey jarvis」→ Companion 狀態變「● 聽候中 → ● 處理中」

### A3. 8.4 HUD 融合 ✅（2026-08-29 完成）
- **做法**：HUD overlay + Companion 共用 CSS/JS 體系（一個 `hud-theme.css`）；dock/遊戲隱藏保留
- **完成**：companion.html / home.html / settings.html 已 link `hud-theme.css`（196 行共用 theme）✅；**dock 已整個移除（0.4.9）**；HUD 主窗遊戲隱藏保留（checkActivity）✅；renderer/index.html 視覺已統一（同一 `--blue #00aaf8` / Orbitron+Rajdhani / rgba(0,170,248) 透明度系）——唔 link hud-theme.css 係避免全屏 overlay CSS 衝突，屬刻意設計
- **驗證**：視覺統一 + 遊戲中全部隱藏

### A4. 8.5 MCP 整合（Hermes ⇄ JARVIS 雙向）✅（2026-08-31：4 個 MCP tools live——speak/wake_status/sensors/alert；sidecar 已 restart）
- **做法**：`mcp_alerts_http.py` 加 tools：
  - `mcp_jarvis_speak(text)`——叫 Jarvis 唸（限頻 ≤1 req/2s、playing 拒絕、只限 SK DM source）
  - `mcp_jarvis_wake_status()`——wake 狀態/裝置
  - `mcp_jarvis_sensors()`——GPU/CPU（NVML 已有）
  - `mcp_jarvis_alert(phrase)`——推 alert 入隊
- Hermes `mcp_servers` config 已註冊 jarvis-alerts——擴展 tools 即可
- **驗證**：Hermes 內 call `mcp_jarvis_speak` 成功 + 安全 gate 生效
- **⚠️ 上網查**：FastMCP tool 定義 + Hermes MCP env 過濾

---

## B. Mage-VL「眼」整合 ✅（2026-08-31：MageVLEngine 單幀 + video sampled + shell_app/engine wiring 完成）

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
- **D2. Minecraft ready alert** ✅（2026-08-31 確認已實現）：`shell_app._start_game_alert_watch`（run() 1781 已接）watch `sk_activity.json` 嘅 `game_started`（activity_monitor 每次 game 轉變寫 `game_start_event.json` + flag）→ enqueue `"<Game> is ready, sir."`（今日補 phrase capitalize：「minecraft」→「Minecraft」）。generic 任何 game 都 alert（唔限 MC）。無重複：`(game, started)` last_seen + started=False 時 reset。
- D3. GPU failover ✅（2026-08-31：gpu_metrics_with_fallback nvidia-smi → HWiNFO）；HWiNFO SHM / GPU-Z（冇 public API）仍 deferred

---

## E. 自我迭代 🔴

- **E1. 已做**：self-monitor script + cron（wake 誤觸/STT miss/rtf/AGC + threshold 自動調）
- **E2. STT 準確度追蹤** ✅（2026-08-31）：`src/jarvis/stt_stats.py`——engine 寫結構化 `repair_log.jsonl`（primary；serve.log `asr_repair=` 文字 parse 只做 fallback）→ repair ratio + top confusions + suggestions（同一 raw→fixed ≥3 次先建議，唔自動 apply 避免學錯 alias；`extract_alias_target` 提供 learn_stt_alias 目標）+ `--fingerprint`（`REPAIR_RATIO <r>|<h>|<n>` / NO_DATA）+ 寫 `stt_stats.log`；窗口一致（repair_log tail 2000 = wake fires 窗口；engine 20000 行 rotation）；11 tests 入 golden。⏳ 等真實數據累積先接 cron monitor（同 clarify_stats R2 一樣）。
- **E3. Response 延遲統計** ✅（2026-08-31）：mouth `tts_ok` print 加 `HH:MM:SS` timestamp（serve.log）；self_monitor 計 `resp_lat`（最近 `oww_fire` → 最近 `tts_ok`，0-60s 先計，午夜 rollover；heuristic 未做 utterance 級 pairing——alert/ack 可能被計入，docstring 已註明；tts_ok 全無 ts → `lat_fmt_err` → `resp_lat=ERR` + notable fail-visible）；summary 入 self_monitor.log；12 tests 入 golden。

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
- **2026-08-31 處理**：① ✅ self_review main 加 fail-visible（log 有內容但 parse 0 條 → ERROR + exit 2，唔再 silent NONE）② ✅ `_consecutive_days` 缺日唔當連續退化（window 參數化）③ 加註釋（有意設計：明確列出要監控 metric）④⑦ 唔改（有意識安全設計：hardcoded baseline 唔俾 untrusted 改）⑫ ✅ ERROR 分支固定輸出「ERROR」唔再每 tick 誤判 changed
- **pass2 新脆弱位（2026-08-31 E2/E3 session）——全部已修（cursor review 11 findings）**：⑬ ✅ **stt_stats 格式耦合**→ engine 寫結構化 `repair_log.jsonl`（primary）+ serve.log 文字 fallback；窗口一致（`_REPAIR_WINDOW=2000` tail + engine 20000 行 rotation）⑭ ✅ **latency 格式依賴**→ `tts_ok_no_ts` 計數 → `lat_fmt_err` → `resp_lat=ERR` + notable（fail-visible）⑮ ✅ **跨午夜**→ dt<0 +86400（cursor review 再捉 `0.0` truthiness bug 已修）⑯ **stt_stats suggestions 冇 consumer**——等數據先接 cron monitor（同 ⑥ 一樣，唔係 code bug）

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

## 執行結果（2026-08-31 全部完成 ✅）

1. **A1 settings 搬遷 MVP** ✅ → A2 voice_status IPC ✅ → A4 MCP tools ✅
2. **B Mage-VL engine** ✅（單幀 + video sampled）
3. **D1 Hermes push** ✅ → **D2 Minecraft alert** ✅ → **E2/E3 統計** ✅（2026-08-31）
4. **F1/F2 修復** ✅ → **A3 HUD 融合** ✅
5. **C 擴展連接** ❌ 取消（SK：「用 Discord 就夠」）
6. 剩低：**G 全部 SK 人手實測清單** + 排期項（自訓 wake / Discord voice out / Iron Man 視覺 / 刪舊目錄）+ 等數據（≥7 日接 cron monitor）

---

## Content 吸收——Douyin v2 相關收藏（2026-09-03，SK 批記低）

> Plan：`.hermes/plans/2026-09-03_douyin-v2-absorption-plan.md`。SK 2026-09-03：「some of those video is related to our project's idea or similar, so we can mark it down」——同 JARVIS/Hermes/agent 路線相關嘅收藏標記，之後可深睇。

### C1. DSH（DeepSeek-Harness）insight → self-evol 參考
- 片：https://www.douyin.com/video/7675337117291023652
- 核心：值得學係 **Harness + Memory**，唔係隨時變嘅某個 Agent 產品；「Agent 由產品變成可組裝運行底座」方向唔會消失；DSH 而家係 developer preview（破壞性更新）——概念火 ≠ 成熟。
- 同我哋：Hermes + JARVIS self-evol（autonomy/prompt pipeline/memory 治理）方向一致；Prime Agent RLM review 已偷「compute over data」。**無新工作**——純 alignment 參考。

### C2. 其他相關收藏（有 url，可之後深睇）
- **Sepia**（https://www.douyin.com/video/7680768247804775707）→ repo `Nanako0129/sepia` ★1687 MIT（2026-09-03 push）：De-AI 寫作審校 skill（Codex/Claude Code，Agent-Skills 生態）——A1 深睇結果見 plan 執行記錄
- **Easy Vibe**（https://www.douyin.com/video/7680862878856908095）→ repo `datawhalechina/easy-vibe` ★19.2k：vibe coding 101 中文課程（實戰項目驅動）——SK 已重度 vibe coding，記錄備用
- **影視颶風 SKILL**（https://www.douyin.com/video/7670844233401552162）：豆包生態 skill store 示範（高流存開場技能）——平台 skill 生態參考

### 唔吸收（標記剔除）
- 桌面整理工具（7680477991545195810）——同 stack 無關；面試協修（7680845731493835491）——無關；workbuddy 挖漏洞（7680868500717505830）——**噪音**（賣課/傭金引流）

---

## 現況 sync（2026-09-03 晚）

- **A1/A2/A4/B/D1/D2/E/F 全部 ✅**（上表 markers 已對齊「執行結果 2026-08-31 全部完成」）；剩 D3 HWiNFO SHM deferred + G 人手實測 + 等數據接 cron monitor。
- **下次（Jarvis 線）待辦**：
  1. `test_stt_stats` baseline fail ✅（2026-09-03：test isolation 修——兩個 test 補 repair_log，CI 全綠 hash 0b88e6f6）
  2. **LHM 開機 tray 驗證** 🟡（2026-09-03：手動 `schtasks /run` 開返 CPU temp 73.9°C；**autostart 等 SK 真 reboot 先驗**——Event log 證實 9/2 11:34 後未 boot 過）
  3. **Phase 2 通用 app detection framework** ✅（2026-09-03：APP_DEFS registry + detect_running_apps + sk_activity `apps` 欄位，parity 16/16 + 獨立 review PASS；sidecar watch 泛化被 review 砍走——等 consumer 先做）
  4. G 人手實測（等新 mic；Settings tab 唔關 mic 事可隨時）
  5. stt_stats／clarify_stats 等數據 ≥7 日先接 cron monitor

---

## 現況 sync（2026-09-10）

- **alerts.py ctypes 64-bit fix**：code 已修 + 已 push（`1bdac68`，09-09 22:42）；**但 sidecar 未重啟 → 未生效**（serve.log 09-10 23:25 = 136MB／370,905 次 `int too long to convert`）→ 等 SK 開聲 kill 8765 python（Electron ~90s respawn）+ truncate log
- **Skills（09-10）**：`brainstorming` 移植入 Hermes（唔裝 superpowers plugin——14 skills 中 ≥5 個同現有重疊）；`ponytail` 裝 Cursor rules（`~/.cursor/rules/ponytail.mdc`）；新增／更新 `ai-content-monetization`／`chart-report-pdf`／`pdf-report-pipeline`／`comfyui-desktop-headless`（video pipeline ref）／`windows-hardware-monitoring`（rtx-5090-power-safety）
- **skill-router**：Layer 1 observer only、would-block 83.9% → Layer 2 唔開（見 `plans/2026-09-03_skill-router-verify-plan.md`）
- **AI_Studio 線（新，非 JARVIS）**：市場調查 + 9 頁 PDF 報告已交付（`Documents\AI_Studio\docs\report_20260910\`）；設計書 `docs\plans\2026-09-10-ai-video-production-design.md`；等 SK 拍板路線
- **MC 線**：Arch-3/3a 已落地未 commit（`askNoTools` 食 `[RECIPE_CARDS]` catalog）；`compileTestJava` HEAD 已壞（pre-existing）→ 想恢復 Java harness 要另開一輪
- **仍然等 SK**：新 mic（G 人手實測 pause；Settings tab 可隨時測）／LHM 開機 autostart（等真 reboot）／stt_stats・clarify_stats 數據 ≥7 日

---

## 現況 sync（2026-09-11 05:45 cron 核實）

- ✅ **alerts.py ctypes 64-bit fix 完全收口**：`1bdac68` 已 push + sidecar 09-10 23:4x 重啟生效 → 實錘 `/health` ok、`serve.log` 27KB、`int too long to convert` = **0**（舊 136MB／370,905 次）；serve.log 已備份（`serve.log.bak-20260910.gz`）＋ truncate。→ 上一版 sync 嘅「未重啟 → 未生效」條目**作廢**。
- 🆕 **GPU driver TDR（2026-09-11 凌晨）**：`javaw.exe` + `nvoglv64.dll` `0xc0000409` 同偏移 `0x108eb9d` 累計 13 次（4-5 月 + 09-11），跨 modpack／跨 Java = driver bug 非硬件；**SK 決定唔郁**（記錄 `%LOCALAPPDATA%\hermes\state\gpu_tdr_incidents.jsonl`；反轉條件：連環／explorer·dwm 都崩／換 pack 照出）。skill `windows-hardware-monitoring` 已加 TDR 段 + `scripts/gpu_tdr_check.ps1`。
- 🆕 **AI_Studio Phase 0 開工（非 JARVIS，記錄備查）**：`scripts/comfy_guard.py` GPU 安全閘（實測 `--status` 讀真 GPU／`--check` 正確 FAIL；unittest 7/8 → 1 個亂碼 case 已 dispatch cursor）+ H3 本地 API graph `workflows/h3_t2v.json`／`h3_i2v.json`（靜態驗證對 `/object_info` PASS）；**真跑未做**（等 SK 答 power 策略 + spike 時段）。
- **MC 線**：Arch-3/3a 已 commit `1ba048f`（working tree clean，ahead 1）→ 等 SK restart game 真機煙測 PASSED 先 push。
- **Git**：jarvis-pc **ahead 3 docs 未 push**（`d8bfe3d`／`bee2e6d`／`06aa722`）＋ 本 cron docs commit。
- **仍然等 SK**：新 mic（G 人手實測；Settings tab 可隨時）／LHM autostart（等真 reboot）／stt_stats・clarify_stats ≥7 日數據／push 兩個 repo 一句話。
- ⏳ **低優先新項**：self_review `detect_trend` 加 sustained-high 規則（step-change + plateau 會靜音——來源 `self-evol-SUGGESTIONS.md` TREND-err-2026-09-06）。

---

## 現況 sync（2026-09-12 06:00 cron 核實）

> 窗口 = 2026-09-11 06:00 → 09-12 06:17（逐個 session 核對：`20260911_060629_9296dc8b` 06:06–21:52 主 Discord session／09:00 self-review cron／5 個 power 研究 subagent／4 個 H3 研究 subagent／`jarvis-32eceb44`・`jarvis-2516ecb6`・`jarvis-e87e0c3f`・`jarvis-835d07a8`・`jarvis-a1692f57`（語音 garble）／`jarvis-9912e09f`・`jarvis-86fd00c5`（09-12 凌晨閒聊）／`20260912_020019_aa00a236` 02:00–02:55 MC 線）。**JARVIS ONE 本體 09-11～09-12 無 code 改動**（工作全部喺 MC repo／AI_Studio／skills）。

- **Git**：jarvis-pc **ahead 61 未 push**（remote main 仍 `ca463a3`，即 2026-08-10 之後全部未上 GitHub；09-12 06:1x `git rev-list --count origin/main..HEAD` 實測）。`.hermes/plans/self-evol-SUGGESTIONS.md` 仍有未 commit 改動（09-11 self-review append，等 SK 決定；本 cron 冇 touch）。
- **MC 線**：09-11 早 Arch-3/3a 真機驗收 PASS（`1ba048f` 已 push）＋ 新 DSML scrub fix（4 檔，已驗／review SHIP，**未 commit**）；09-12 01:59 真機跑確認 **DSML fix 生效**，但揭出兜底路徑（`askNativeTools="off"`）漏內部 FACT 入答案 → 加 raw-reply log 未拍板；⚠️ instance config 09-11 寫錯「已還原 auto」（實際一直 `off`）→ 02:09 已由 SK 改返 `auto`（讀檔驗過）。詳見 MC repo `.hermes/plans/HANDOFF.md`。
- **AI_Studio（非 JARVIS，記錄備查）**：
  - Phase 0 完成 → **Phase 1 spike spec staged**（`docs\plans\2026-09-11-phase1-spike-jobspec.md`：3 樣片＋逐項技術 PASS 標準＋kill criteria；等 SK 揀 idle 時段）。上一版 sync 嘅「H3 真跑未做（等 SK 答 power 策略 + spike 時段）」仍然成立，但 **power 策略已定：B（唔 cap，先量真實功耗/溫度）**。
  - **5090 供電安全研究**：117 個 domain ＋ 5 個並行 subagent → `docs\plans\2026-09-11-power-limit-research.md`。結論：軟件 power limit（nvidia-smi -pl）本身安全（450W ≈ -5~8% 效能）但**保護唔到接頭熔**（500W＋降壓都熔過、-100W 照熔）→ 唔可以講「保證冇問題」；**generation-only cap 有盲點**（打機時照 600W）。交付：緊急應變卡 HTML＋PDF（`deliverables\`）＋ 機率模型 doc（`docs\plans\2026-09-11-risk-probability-model.md`，方法論／來源分級明寫，回應 SK「有冇根據」）。周邊：WireView Pro II 查證、本地修卡點（Rivia 深水埗／JKIT 新高登／張哥修電腦）→ 已入 memory + user profile。
  - **H3 多鏡頭工作流**：4 條 workflow 已砌（t2v／i2v／多鏡頭 22 節點／人物設計圖 20 節點）＋研究整合 doc（37 B站／31 YT／49 GitHub 來源）＋ workflow 圖 HTML；Ref2VA checkpoint 已下載＋SHA256／size 驗證；ComfyUI server 8000 跑住。
  - ⏸ 兩件等 idle：**Mage-VL 讀 73 note 圖**（~9.5GB VRAM；script `%TEMP%\dy_notes_mage.py`——SK 09-11 18:10 講過「no need, will consume too much vram」，所以押後唔係拒絕）、**H3 首次真跑**（峰值 ~31.8GB VRAM → 跑前要熄 MC）。
- **抖音線**：09-11 全量 deep-read 收尾 **325/327 已轉錄**（有內容 297／純音樂 28／封鎖 0，總 293,150 字；報告 `docs\plans\2026-09-11-douyin-full-deepread.md`、分類 `dy_classified.json`）。**skill 真坑已修 2 個**：① 抖音 caption anchor 位置已變（舊 `span[class*='#']` 完全失效，509/509 desc 全空 → 改用 card 內 `img[alt]`，之後 509/509 有 desc）；② batch-ASR 進度 watchdog 三坑（`Get-Process python` 判斷永遠 true→改 `Get-CimInstance` + CommandLine 過濾；`subprocess.run(timeout=)` 唔殺子進程；DONE marker 自靜音）＋ Hermes cron `script` 欄唔支援參數。
- **語音線（優先度升）**：本地 ASR（sensevoice）短句粵語 **09-11 全日 6 句 garble**（serve.log `[ear] raw=` 實錘：07:40／20:01／22:27／22:52／23:36／09-12 00:38；另 2 次空／單字誤觸）——同日英文句轉得準 → 係短句粵語系統性弱，唔係環境噪音。三選一（①打字重講 ②MiMo 雲端 ASR，key 已配 ③本地 Fun-ASR-Nano）**等 SK 揀**。其餘 mic 相關（headset wake／Tier 1／聲紋／AEC）照舊等新 mic。
- **仍然等 SK**：① push 兩個 repo ② MC raw-reply log ＋ DSML fix commit ③ 語音 ASR 方向 ④ AI_Studio Phase 1 spike 時段 ⑤ `self-evol-SUGGESTIONS.md` commit；另 LHM autostart 等真 reboot、stt_stats・clarify_stats ≥7 日數據、GPU TDR 決定唔郁（反轉條件見 HANDOFF 頂部）。

---

## 現況 sync（2026-09-13 06:00 cron 核實）

- ✅ **Alert pipeline v5.1 落地**（09-12 plan → 09-13 收貨）：`be099a7 feat(alerts): alert pipeline v5.1 — deterministic policy, single speaker, ledger`（21 modified ＋ 25 新檔）；**三輪獨立 review** 全部 findings 修完（fix1–fix11，Hermes 親手 probe 重驗）；最終驗收：`pytest` **532 passed / 0 failed**、`eval_gate --lock` 53 files 一致、三 suite ok、HASH `3e5e074479192100`。docs：`docs/hermes_alerts_mcp.md`（修復輪表＋baseline）、plan 尾「收貨記錄」＋10 條規格偏離、`jarvis-pc\AGENTS.md` 坑 section 一句（`8cff405`）。
- ✅ **Runtime 已生效（shadow）**：09-13 03:06 restart sidecar（`python.exe` pid **38860**）＋ poll loop（`pythonw.exe` 45964）；`settings.json` `alert_policy_mode="shadow"`；`shadow_heartbeat.jsonl`／`shadow_ledger.jsonl` 持續寫（05:45 仍在寫）。P1 通關條件：**M1 打機時 GPU soft ≤2 次/小時、M3 Prism 開住唔玩 FP <5%**；每 6 小時 cron `jarvis-alert-shadow-report`（job `3dbaff9ace81`，`no_agent`）自動報，窗口內冇 decision 就完全靜音。
- ⏳ **真機驗收未做**（SK 選 **4b＝下次 session**；打機／通話／idle 三情境，過關才 `enforce`）；**Task 10（LLM digest 潤飾）暫緩**（要先 benchmark ranking prompt p95 ≤3s）。
- ✅ **Git／PR**：feature 分支 `feature/hermes-alerts-mcp` 已 push ＋ **PR #12**（base `main`＝`ca463a3`，**未 merge**）；`origin/main..HEAD` ＝ **89 commit**（含 2026-08-10 之後所有未推工作）；殘留暫存檔已清（`7d19ccf`）。
- 🆕 **未修新問題（09-13 05:4x cron 實錘）**：`tests/test_alert_piper_gate.py` 冇 APPDATA 隔離（`tests/` 亦冇 `conftest.py`）→ 跑 `pytest tests/` 會寫真檔 `%APPDATA%\Jarvis\voice_status.json`（`wake_on:false`／`status:"ready"`），HUD／MCP 顯示「聽候＝關」直到 sidecar 再寫；亦令 sidecar-health cron 00:51 誤報 fingerprint 變動。建議一行級 fix：`tests/conftest.py` autouse fixture 隔離 APPDATA（等 SK go）。
- ⚠️ **等 SK**：① 真機驗收（4b，下次 session）② PR #12 merge 與否 ③ `.hermes/plans/self-evol-SUGGESTIONS.md` 3 行 commit ④ `detect_trend` sustained-high 規則（低優先）⑤ 語音 ASR 線＝**d（唔理住）**；另：新 mic（G 人手實測）、LHM autostart（等真 reboot）、stt_stats／clarify_stats ≥7 日數據、MC 兜底 FACT 測試（等 SK 關 game）、AI_Studio Phase 1 spike 時段。
- 📌 **觀察（等 SK 判斷）**：窗口內（09-12 06:00–09-13 05:45）有 **75 個**語音 session 同一條問題「開啟 Chrome 瀏覽器」；每次 JARVIS 都因前景＝遊戲／使用中而只教 SK 自己開、冇代開 → 係唔係要支援「背景代開（唔搶焦點）」？


## 由 HANDOFF 搬入（2026-09-13）


> **2026-09-12 更新（cron 核實）——現行 open items（呢條取代下面嗰條）**：① MC：加 raw-reply log（分辨「AI 照抄 payload」vs「程式貼 facts 兜底」，等 go）；② MC：commit + push 09-11 DSML scrub fix（4 檔，已驗、review SHIP，等 go）；③ jarvis-pc **61 個未 push commit** 要唔要 push（等 go）；④ **語音**：sensevoice 短句粵語**全日 6 句 garble 實錘** → ①打字重講 ②MiMo 雲端 ASR（key 已配）③本地 Fun-ASR-Nano（等揀）；⑤ `self-evol-SUGGESTIONS.md` 3 行要唔要 commit（等 go）；⑥ **AI_Studio Phase 1 spike 時段**（spec 已 staged，等揀）；⑦ 其餘不變：G 人手實測等新 mic（Settings tab 可隨時）、LHM autostart 等真 reboot、stt_stats／clarify_stats ≥7 日數據、GPU TDR 唔郁。
>
> **2026-09-11 更新（cron 核實）——現行 open items**：① 等 SK 一句 push（jarvis-pc 3 docs + MC `1ba048f`）；② MC Arch-3/3a 真機煙測（SK restart game）；③ AI_Studio：等 SK 答 power 策略 + spike 時段 → Phase 1 spike；④ GPU TDR = SK 決定唔郁（記錄完，反轉條件喺頂部）；⑤ G 人手實測等新 mic（Settings tab 可隨時）；⑥ stt_stats／clarify_stats 等數據 ≥7 日；⑦ LHM 開機 autostart 等真 reboot。**下面 2026-08-31 版清單保留做歷史**（多數已 ✅，細節睇各日期 section）：

- ⏳ **SK 實測：戴 headset 試 wake**（2026-08-31 voice 診斷後）——onnxruntime 已修 + stt_preload 已開（2026-09-01）+ sidecar 已重啟；**而家 rms=0.000 = headset 休眠**；戴返試「hey jarvis」；如果戴住都唔 fire → 調低 wake_threshold（而家 0.75 可能偏高）
- ✅ **刪舊 jarvis-hud 目錄**（2026-09-01 完成）：JARVIS 已重啟切換新位置 + 確認冇 process 由舊路徑 load → 已刪（釋放 765MB）
- ⏳ **Electron auto-respawn 失效原因**（8/29 實測死咗冇 respawn；8/31 兩次都 respawn 成功）——下次再死要查 main.js health-check
- ✅ **MCP tools restart**：已完成（jarvis_clarify_gate / jarvis_autonomy_state live）
- ✅ **prompt_pipeline Optimizer**：已完成（prompt_optimizer.py）
- ✅ **L1a sandbox**：已決定 Docker Desktop + sandbox.py 完成（sandbox_ready 仲係 False——要真開 Docker 先 promote）
- ✅ **clarify precision consumer**：已完成（clarify_stats.py）——剩「接 cron 等數據夠」
- ✅ **D2 Minecraft ready alert**：已完成（_start_game_alert_watch + game_started 事件；capitalize 微調 2026-08-31）
- ✅ **E2 STT 準確度追蹤**：已完成（stt_stats.py + 9 tests）——剩「等數據先接 cron monitor」
- ✅ **E3 Response 延遲**：已完成（mouth tts_ok timestamp + self_monitor resp_lat）——>5s 會 notable
- ✅ **文檔**：docs/hermes-bridge-auth.md + docs/settings-field-map.md
- 🟡 **等數據**：self_monitor.log / clarify_log / stt_stats.log 累積 ≥7 日先有真 finding signal（而家 fingerprint 多數 NONE）
- 🟡 **G 人手實測（等新 mic——SK 2026-09-01 決定買新 mic，mic 相關全部 pause）**：headset wake / Tier 1（BGM 誤觸、喊完→有聲 ≤3s）/ 聲紋 enrollment（要新 mic）/ AEC voice call / Settings tab（HTML 已齊——呢項唔關 mic 事，可以隨時測）
- ❌ **C 擴展連接**：已取消（SK：「用 Discord 就夠」）
- ⏳ **Qwen2.5-VL 自動啟動**：SK 決定唔加（要睇片先手動開）

- ✅ **alerts.py ctypes 64-bit hwnd bug：已完全收口（2026-09-11 cron 實錘）**——code 修 + push（`1bdac68`）→ 09-10 23:4x 重啟 sidecar → **`/health` ok、serve.log 27KB、`int too long to convert` = 0**（舊 136MB／370,905 次）；log 已 truncate（備份 `.gz`）。原 fix：cursor-agent 加 `_declare_winapi()` + 4 call sites declare user32/kernel32 argtypes；eval_gate 全綠。詳見頂部 09-11 cron 核實 section + `self-evol-SUGGESTIONS.md`（TREND-err-2026-09-05/06/10 三條同源，已標 ✅）
- ⏳ **detect_trend sustained-high 規則（未做，低優先）**：self_review 只喺「連續單調變差」先出 finding → step-change + plateau（如 ctypes flood 09-05→09-06 微跌）會靜音 3 個月；建議加「連續 ≥2 日 >10x 中位數」都出 finding（來源 `self-evol-SUGGESTIONS.md` TREND-err-2026-09-06）。要唔要做由 SK 定。
