# HANDOFF — JARVIS 交接（固定檔）

> **呢個係固定 handoff 檔**（2026-08-30 起）：每次 session 結束**更新呢份**，唔好開新日期檔；舊交接版本移入 `plans/archive/`。
>
> 下次 session 起點：**JARVIS ONE 0.4.10 跑緊 + Self-Evol Task 0-9 全部完成（Phase A-E 基建落地）**。讀呢份之前先讀：
> 1. `jarvis-pc\AGENTS.md`（專案 context——**自動載入規則已寫入主契約，唔使 SK 叫**）
> 2. `C:\Users\skps9\AGENTS.md`（主契約——Code Review 兩次規則已升格入契約）
> 3. `REMAINING_WORK.md` + `2026-08-29_self-evol.md`（計畫書，R1-R20b 齊全）

---

## 現行狀態（2026-08-31 凌晨 session 尾）

- **JARVIS ONE 0.4.10**：`jarvis-pc\hud\dist\JARVIS-ONE-0.4.10.exe`（**2026-08-31 monorepo**：jarvis-hud 已搬入 `hud/` 子目錄）；3 個 .lnk 全指佢；**2026-08-31 凌晨乾淨重啟**（舊 instance 行咗 >24h，HUD window 冇建立 → taskkill + 重開 exe 修復，HUD `J.A.R.V.I.S. HUD Prototype` (0,0,2560,1440) visible=1）
- **Sidecar 8765**：**2026-08-31 凌晨手動 respawn**（Electron auto-respawn 失效——serve.log 停 8/29 22:49 之後冇起返；`pythonw -m jarvis serve` + JARVIS_ELECTRON_HOST=1 起返，wake_on=true）；⚠️ 下次再死要查 Electron health-check 點解冇 respawn
- **Qwen2.5-VL-7B video server**：`127.0.0.1:8643`（`$LOCALAPPDATA\hermes\scripts\qwen_vl_server.py`，**background 進程要開住先用到 video_analyze**；~16GB VRAM，睇片先開、打機前關）；Hermes `auxiliary.video` 已指去 localhost + Discord `video` toolset 已 enable。⚠️ **已關閉**——下次要睇片先手動開返（重啟電腦後亦要手動開）
- **視覺雙模型分工**：睇片總結 = Qwen2.5-VL（16 幀 + temporal）；單幀/遊戲精讀 = Mage-VL 4B（`src/jarvis/mage_engine.py`）
- Ports：8765（alerts MCP + /settings）、8770（reply）、8771（media bridge）、8642（Hermes API）、**8643（Qwen2.5-VL video server）**
- cron：sk-activity-monitor（1m）+ Gateway watchdog（2m）——冇 JARVIS alert cron（sidecar poller 做緊）

## 今日完成（2026-08-30 session）

### 2026-08-31 資源優化 session（SK「5.5GB 太多」+ fix them all）
1. **SenseVoice lazy load（記憶體 -65%）**：實測 SenseVoice CPU 載入 ~3.5GB → 新 settings `stt_preload`（default False）+ thread-safe lazy load；sidecar Private 5.5GB→1.9GB、WorkingSet 1.9GB→454MB
2. **UnicodeDecodeError 徹底修**：8 個 subprocess 位加 errors="replace"（taskkill/powershell/nvidia-smi/pgrep/TTS）——中文 Windows GBK 輸出不再 kill reader thread，test warning 清零（self-evol TREND-err finding 已解決）
3. **Mic 健康偵測**：wake heartbeat 連續 3 次 rms≈0 → voice_status `mic_signal_ok=false`（恢復 flip True）——HUD/MCP 顯示真實 mic 狀態
4. **Sidecar watchdog cron**：`jarvis-sidecar-health`（job 6a98a79be95f，every 2m，monitor pattern）——8765 DOWN 先醒
5. **Git commit `290ca61`**：jarvis-pc 110 files 全部工作 commit（secrets scan 乾淨）
6. **Hermes memory 清理**：personal 92% / user 90%
7. **SenseVoice remote code warning**：查證無功能影響（fallback 照 work），記錄唔修

### 2026-08-31 bug review + E4 session（check for all bug / finish the rest）
1. **獨立 reviewer ×2（fail-closed）**：全部 findings 修好——mcp_alerts_http（7：impact coercion / gain drop / options 拆字 / confidence clamp / fallback merge / log 驗證 / constant-time）、autonomy（6：save 原子+bool / kill_switch fail-open 修 / promote 審計拒絕 / demo 隔離 / load 一致性）、eval_gate（4：全路徑 regex / mapping 空 fail-closed / 檔案存在 check / 重複 basename）
2. **E4 clarify precision consumer**：`src/jarvis/clarify_stats.py`（precision 統計 + fingerprint）+ 9 tests；已入 golden suite
3. **驗證**：全套 **285 passed**（+17 adversarial tests）+ eval_gate --all 全綠（golden 254+30 py_compile / regression 16 / stress 65）+ --lock 一致；hash `c4db6e03fa849985`
4. docs/hermes_alerts_mcp.md 更新（4→10 tools + Self-Evol tools 說明）；skill gotchas 加 untrusted parsing / save 失敗教訓

### 2026-08-31 wiring session（Self-Evol 4 module 接入主流程）
1. **eval_gate --lock**（pass2 ⑧）：doc ↔ mapping drift 防禦（`check_doc_lock` basename 對比）；GOLDEN_SUITES 擴大到全核心（golden 21 files pytest + 29 py_compile / regression 2 / stress 3）；`test_eval_gate.py` 唔入 golden（nested recursion 實測）；golden-set.md 同步；hash `4418ea8cd1a9b12a`
2. **MCP tools（8765）**：`jarvis_clarify_gate`（EVPI 問唔問，stateless，只揀 impactful，fallback 對齊 proceed，答案當 untrusted R17）+ `jarvis_autonomy_state`（level/sandbox/H_auth events）——⚠️ **要 restart sidecar 先生效**
3. **AutonomyState persistence**：`%APPDATA%\Jarvis\autonomy_state.json`（promote/demote/kill_switch 後 save；restart 唔 reset；測試必須傳 state_path 隔離）
4. **gpu_health flaky 修復**：cooldown sentinel 0.0 → None（boot<cooldown 時第一次 emit 誤擋；實測 root cause）
5. **skill `jarvis-self-evol-ops`**：eval_gate/clarify/autonomy/prompt_pipeline 完整 SOP + prompt_pipeline delegate_task 格式化規則
6. **jarvis-pc AGENTS.md Commands**：加「改動後強制 eval_gate --lock + --all」
7. **驗證**：全套 **259 passed**（246+13 新）+ `eval_gate --all` 全綠 + `--lock` 一致

### 2026-08-31 凌晨 session（修復 session）
1. **Sidecar 8765 respawn**：serve.log 停喺 8/29 22:49、8765 冇 LISTEN、冇 `jarvis serve` process——Electron auto-respawn（30s health check）失效，原因未明（可能 crash-loop backoff 或主進程狀態）。手動 `pythonw -m jarvis serve`（JARVIS_ELECTRON_HOST=1）起返，/health OK（wake_on:true）、MCP tools（alert_stats/wake_status/sensors）全 live。⚠️ **下次再死要查 Electron health-check 點解冇 respawn**（main.js `sidecarRunning()` 30s interval + 3 miss force respawn 有 code，但實測冇生效）
2. **HUD window 消失修復**：SK 報「I can't see hud」——EnumWindows 確認 HUD window 根本冇建立（舊 instance 8/29 21:15 起跑咗 >24h，renderer 22:28 先 spawn，fullscreen overlay 一直唔存在；唯一大 window 係 1920×1059 無 WS_EX_TRANSPARENT，唔係 HUD）。**乾淨重啟**（taskkill JARVIS ONE.exe + JARVIS-ONE-0.4.10.exe → 重開 exe）後 `J.A.R.V.I.S. HUD Prototype` (0,0,2560,1440) visible=1 ✅。SK 確認唔改 alwaysOnTop（保持 false，桌面先見）
3. **Self-Evol 狀態確認**：Task 0-9 基建全部完成（246 tests 全綠，cursor 11 + bug bot 3 findings 已修）；剩 wiring 4 module 入 Hermes 主流程（clarify→adapter、eval_gate→CI gate、prompt_pipeline→delegate_task、autonomy→實際 gate）——等 SK 拍板接入次序
4. **Qwen2.5-VL server**：維持關閉（SK 指示「睇片先開、睇完即關」）

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

- ✅ **cursor-agent bug review（2026-08-30 晚，已完成）**：11 findings 全部修好，報告 `plans/cursor-bug-review-2026-08-30.md`（HIGH：asr_repair shellish bypass / clarify asked-but-unanswered fallback / clarify EVPI 只問 impactful / autonomy promote 唔跳 L1a；MEDIUM：demote_if_needed / apply_optimized introduced-diff / format_simple single-pass / eval_gate utf-8 / self_review deque / hysteresis 隔離；LOW：dead symbols）
- ✅ **bug bot（requesting-code-review，2026-08-30 已完成）**：static scan 乾淨 + 3 個 logic errors 修好（eval_gate catch / PatternStore malformed JSON / self_review --days）——246 tests 全綠
- ⏳ **刪舊 jarvis-hud 目錄**（SK 2026-08-31：「你之後處理」）：monorepo 搬遷後，`C:\Users\skps9\Documents\Code_Project\jarvis-hud` 舊目錄仲喺度（運行緊嘅 process 用緊，唔可以即刻刪）。**下次 JARVIS 重啟（用新位置 hud\dist exe 成功運行）後刪除**——刪前確認冇 process 由舊路徑 load。
- ⚠️ **MCP tools restart sidecar（8765）先生效**（jarvis_clarify_gate / jarvis_autonomy_state 已寫 code + tests 全綠，未 restart）——等 SK 批准重啟服務
- ✅ **wiring 4 個新 module 入 Hermes 主流程已完成（2026-08-31）**：eval_gate→CI gate（--lock + 強制指令）、clarify→MCP tool、autonomy→persistence + MCP tool、prompt_pipeline→skill 規則（詳見 REMAINING_WORK「Wiring 完成」+ skill jarvis-self-evol-ops）
- 🔴 **prompt_pipeline Optimizer 本體**（GEPA/DSPy 集成）——只有 Formatter + PatternStore，Optimizer 未實作（後續）
- 🟡 **等數據**：self_monitor.log ≥7 日後，每日審視 cron 開始有真實 finding signal（而家 fingerprint=NONE 正常）
- 🟡 **G 人手實測**（等 SK）：Tier 1（BGM 誤觸 / 喊完→有聲 ≤3s）、聲紋 enrollment（要新 mic）、AEC voice call、Settings tab
- 🟡 **C 擴展連接**（等 credentials）：WhatsApp / Telegram / Hue
- ⏳ **L1a sandbox**（Open Q5）：Docker Desktop vs WSL2 未決定——autonomy promote mapping 跳過 L1a 係刻意（sandbox 未建；persistence 已 ready，sandbox_ready=False 永遠擋 promote）
- ⏳ **clarify precision log 校準 consumer**（E4）——log 有寫，冇 consumer 分析
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
