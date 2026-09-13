# HANDOFF — JARVIS 交接（固定檔）

> **呢個係固定 handoff 檔**（2026-08-30 起）：每次 session 結束**更新呢份**，唔好開新日期檔；舊交接版本移入 `plans/archive/`。
>
> 下次 session 起點：**JARVIS ONE 0.4.10 跑緊 + Self-Evol Task 0-9 全部完成（Phase A-E 基建落地）**。讀呢份之前先讀：
> 1. `jarvis-pc\AGENTS.md`（專案 context——**自動載入規則已寫入主契約，唔使 SK 叫**）
> 2. `C:\Users\skps9\AGENTS.md`（主契約——Code Review 兩次規則已升格入契約）
> 3. `REMAINING_WORK.md` + `2026-08-29_self-evol.md`（計畫書，R1-R20b 齊全）

---

## 現行狀態（2026-08-30 晚上 session 尾）

- **JARVIS ONE 0.4.10**：`jarvis-hud\dist\JARVIS-ONE-0.4.10.exe`；3 個 .lnk 全指佢
- **Qwen2.5-VL-7B video server**：`127.0.0.1:8643`（`$LOCALAPPDATA\hermes\scripts\qwen_vl_server.py`，**background 進程要開住先用到 video_analyze**；~16GB VRAM，睇片先開、打機前關）；Hermes `auxiliary.video` 已指去 localhost + Discord `video` toolset 已 enable（**新 session 生效** → `video_analyze` tool）。⚠️ **已關閉（2026-08-30 晚上 session 尾，SK 指示）**——下次要睇片先手動開返（重啟電腦後亦要手動開）
- **視覺雙模型分工**：睇片總結 = Qwen2.5-VL（16 幀 + temporal）；單幀/遊戲精讀 = Mage-VL 4B（`src/jarvis/mage_engine.py`）
- Ports：8765（alerts MCP + /settings）、8770（reply）、8771（media bridge）、8642（Hermes API）、**8643（Qwen2.5-VL video server）**
- cron：sk-activity-monitor（1m）+ Gateway watchdog（2m）——冇 JARVIS alert cron（sidecar poller 做緊）

## 今日完成（2026-08-30 session）

### Self-Evol 計畫（大更新）
1. **第二輪研究**（5 agent，127 來源）：`2026-08-30_self-evol-research-round2.md`——Phase D/E/F v2（R10-R14：per-operation 分級 / 執行型 eval gate / Clarification v2 / Prompt Formatter+Optimizer / 審批疲勞）
2. **第三輪實戰研究**（4 agent，80+ 來源）：`2026-08-30_self-evol-research-round3.md`——POV review 判決 8:2 支持，補 R15-R19（writeback 管道 / memory poisoning 防禦 / clarification untrusted / 轉換規則+證據包 / 三層報告通道+watchdog）
3. **執行範式：Loop Engineering**（SK 要求，weii.dev/loop-engineering）——4 種 loop（Heartbeat/Cron/Hook/Goal）+ Kilo 五階段 + 失敗模式防禦
4. **技術參考**（降低研發成本）——`%TEMP%\ref-self-improving`（OpenClaw self-improving skill，MIT）做 Phase A 參考；DSPy 直接用 library；Hermes 內建能力清單
5. **Token 成本優化（R20/R20b）**——prompt caching / 工具輸出過濾（詳細表）/ 靜態 context 轉圖片（pxpipe/ctx2img——**要做 spike 驗證 DeepSeek billing 先決定**）/ model routing / history summarization
6. **報告層設計確認**（SK feedback「報告唔識睇」→ 人話報告 A0 + 零打擾 + 報告 agent 做 L2 第一應用 + 安全三原則）

### Task 0-2 完成（Phase A 基礎）
- `src/jarvis/self_review.py`（新）：parse_log / aggregate_by_day / detect_trend（連續 3 日）/ build_findings（schema：confidence/source/contradicts/expires/provenance）/ `--fingerprint`
- `tests/test_self_review.py`（新）：**14 個測試全過** + 真實數據驗證（fingerprint=NONE，2 日數據唔誤報）
- Code Review 兩次：pass2 脆弱位已記低（log 格式耦合 / 缺日 / metric 硬編碼）
- `%APPDATA%\Jarvis\self_review.json` 已可生成

### Task 6 完成（Phase E v2 Clarification Gate，2026-08-30 晚上 session）
- `src/jarvis/clarify.py`（新）：`Understanding`/`Unknown` schema（unknowns → assumptions → confidence，P(True) 式）+ **EVPI 觸發**（unknowns 非空 且 會改變行動先問；confidence 唔做唯一門檻 R12）+ `select_questions`（資訊增益排序、round1 ≤5 / round2 ≤2）+ `ClarifySession`（2 輪上限 + 強制 proceed）+ `conservative_assumption`（delete=唔刪 / send=唔 send / generate=最通用）+ precision log `%APPDATA%\Jarvis\clarify_log.jsonl`（問完有冇改變計劃，E4 校準用）
- `tests/test_clarify.py`（新）：**20 個測試全過**（EVPI 判斷 / 問題 ≤5 / 2 輪強制 proceed / fallback 正確 / log append）
- ⚠️ standalone library，未接入 agent 流程——接 Hermes clarify tool / sidecar brain 要寫 adapter（pass2 脆弱位 ⑤）

### Task 3-9 完成（Phase A/D/E/F 基建，2026-08-30 晚上 session）
- **Task 3**：fingerprint cron 上線——`%LOCALAPPDATA%\hermes\scripts\jarvis_self_review_fp.py`（script+monitor 同一檔）+ Hermes cron `jarvis-daily-self-review`（job `8ef18463dc73`，`0 9 * * *`，deliver=Discord，fingerprint=NONE 時 agent 唔醒 = 零成本）
- **Task 4**：`plans/self-evol-SUGGESTIONS.md`（append-only，R5 格式）+ cron prompt 內嵌 A0 人話報告規則
- **Task 7**：`src/jarvis/eval_gate.py`（執行型驗證 pytest/py_compile/node --check + `--hash` immutable 驗證 + `--repeat` 統計）+ `plans/self-evol-golden-set.md`（三類 eval，frozen + 人手標註）——golden 實跑 74 passed，hash `eb3c25e3496e7361`
- **Task 8**：`src/jarvis/prompt_pipeline.py`（L1 Formatter 五段 + L2 PatternStore score≥0.8 先收錄 + INVARIANT_BLOCK injection 防禦）+ `plans/prompt-patterns.md`
- **Task 9**：`src/jarvis/autonomy.py`（per-operation 分級 + 複合閘/hysteresis + 自動 demotion + H_auth log + kill switch + rate alarm）
- **4 個 pre-existing 測試失敗已修**：settings_ui 5 tabs 同步 / asr_repair `|-]` garbled early repair（shellish guard 誤判 pipe 符號）/ test_brain 兩個 mock hermes_enabled——**232 tests 全綠**

### 其他
7. **抖音收藏掃描**：`%TEMP%\douyin_fav_items2.json`（179 條）+ `%TEMP%\douyin_ai_favs.md`（92 條 AI/coding 分類清單）——send 咗俾 SK
8. **Qwen2.5-VL setup**：model 下載 + server + 測試（Bilibili 片完整分析成功）
9. **plans 目錄整理**：舊 HANDOFF/tier detail 移入 `archive/`（18→9 個檔案）
10. **HANDOFF.md 固定檔**：以後交接更新呢份，唔開新日期檔

## 剩低（詳見 REMAINING_WORK.md）

- 🔴 **wiring 4 個新 module 入 Hermes 主流程**（pass2 ⑪，最大脆弱位）：clarify→Hermes clarify tool adapter、eval_gate→CI/改動前 gate、prompt_pipeline→delegate_task、autonomy→實際 gate——等 SK 決定接入次序
- 🟡 **wiring 4 個新 module 入 Hermes 主流程**（pass2 ⑪，最大脆弱位）：clarify→Hermes clarify tool adapter、eval_gate→CI/改動前 gate、prompt_pipeline→delegate_task、autonomy→實際 gate——等 SK 決定接入次序
- ✅ **cursor-agent bug review 已完成（2026-08-30 晚）**：11 findings（C=0 H=4 M=5 L=2）**全部修好**，報告留 `plans/cursor-bug-review-2026-08-30.md`——HIGH：asr_repair shellish bypass（`|curl https://discord.gg/x` 唔再變「閂 Discord」）、clarify asked-but-unanswered fallback（加 record_answers）、clarify EVPI 只問 impactful、autonomy promote 唔跳 L1a（sandbox_ready prerequisite）；MEDIUM：demote_if_needed、apply_optimized introduced-diff、format_simple single-pass re.sub、eval_gate utf-8、self_review deque、hysteresis 測試隔離；LOW：dead symbols 清走
- ✅ **bug bot（requesting-code-review）已完成**：static scan 乾淨 + 獨立 reviewer 搵到 3 個 logic errors 全部修好（eval_gate `_run` 補 FileNotFoundError/OSError catch、prompt_pipeline PatternStore `_load` malformed JSON 防 crash + `add` 最高分保留、self_review `--days` flag 生效）——**246 tests 全綠**
- 🟡 **等數據**：self_monitor.log ≥7 日後，每日審視 cron 開始有真實 finding signal（而家 fingerprint=NONE 正常）
- 🟡 **G 人手實測**（等 SK）：Tier 1（BGM 誤觸 / 喊完→有聲 ≤3s）、聲紋 enrollment（要新 mic）、AEC voice call、Settings tab
- 🟡 **C 擴展連接**（等 credentials）：WhatsApp / Telegram / Hue
- ⏳ **L1a sandbox**（Open Q5）：Docker Desktop vs WSL2 未決定——autonomy promote mapping 跳過 L1a 係刻意（sandbox 未建）
- ⏳ **prompt_pipeline Optimizer 本體**（GEPA/DSPy 集成）+ **eval_gate --lock** + **clarify precision log 校準 consumer**——全部後續
- ⏳ **Qwen2.5-VL 自動啟動**：SK 話「要睇片先開」——暫唔加自動啟動；重啟電腦後要手動開 server

## 陷阱（重溫）

- **Settings 單一 writer**：改 settings 用 sidecar `POST /settings`（Bearer = `%APPDATA%\Jarvis\alerts\mcp_token.txt`），唔好直接寫 settings.json
- **dpapi:** 值唔好當明文讀；settings.json 已加密
- **jarvis serve** 由 Electron spawn（JARVIS_ELECTRON_HOST=1 headless）；唔好手動起第二個
- **Qwen2.5-VL server**：用 jarvis-pc env python 跑（`env -u PYTHONPATH`）；transformers video decode 壞咗 → server 內建 pyav 抽幀（16 幀 640p）；model 要 `torch_dtype=torch.bfloat16`（auto 會 OOM）
- **Mage-VL**：`check_imports` monkeypatch 已喺 mage_engine.py 內建；單幀理解
- Python：`C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe`，跑 jarvis 用 `env -u PYTHONPATH`
- 換版流程：bump version → `npm run dist` → kill JARVIS（單斜線 taskkill）→ 開新 exe → 更新 3 個 .lnk
- 語音一律英文；GUI 操作前讀 sk_activity.json（playing/using 禁彈窗）
- **Code Review 兩次**（契約規則）：pass1 刪重複/拆函數/補註釋/降耦合；pass2 三個月後脆弱位

## 語音/硬體設定（驗證過）

- wake_mic = 「麥克風 (2- Arctis Nova 7)」44.1k；TTS 輸出 = G27Q 螢幕喇叭；AEC reference = Sonar Media + Sonar Chat（唔用 Arctis loopback）
- ⚠️ Arctis 週期性 rms=0.000（headset 休眠/斷連）——叫唔醒先睇 wake_debug.log
- mic 細（avg ~0.05）→ AGC 上線；wake_threshold 0.75（self-monitor 自動調出嚟）
