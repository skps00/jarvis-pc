# HANDOFF — JARVIS 交接（固定檔）

> **呢個係固定 handoff 檔**（2026-08-30 起）：每次 session 結束**更新呢份**，唔好開新日期檔；舊交接版本移入 `plans/archive/`。
>
> 下次 session 起點：**JARVIS ONE 0.4.10 跑緊 + Self-Evol Task 0-9 全部完成（Phase A-E 基建落地）**。讀呢份之前先讀：
> 1. `jarvis-pc\AGENTS.md`（專案 context——**自動載入規則已寫入主契約，唔使 SK 叫**）
> 2. `C:\Users\skps9\AGENTS.md`（主契約——Code Review 兩次規則已升格入契約）
> 3. `REMAINING_WORK.md` + `2026-08-29_self-evol.md`（計畫書，R1-R20b 齊全）

---

## 現行狀態（2026-08-31 晚 session 尾）

- **JARVIS ONE 0.4.10**：`jarvis-pc\hud\dist\JARVIS-ONE-0.4.10.exe`（**monorepo**：jarvis-hud 已搬入 `hud/` 子目錄，git 歷史保留）；3 個 .lnk 全指新位置；Electron 仲行緊舊位置 process（下次重啟切換）
- **Sidecar 8765**：PID 37496（restart 多次）；health OK wake_on=true；**onnxruntime 已 downgrade 1.27.0**（1.28 bug 令 openwakeword 輸出全 0——已 pin `<1.28`）
- **Voice 診斷結論（2026-08-31 晚）**：① onnxruntime 1.28 = OWW 全 0（已修）② **Arctis headset 休眠 = mic rms=0.000（而家就係呢個狀態）——戴返/喚醒 headset 先叫到** ③ wake_threshold 0.75 可能偏高（self-monitor 調出嚟）——戴 headset 試完再決定
- **Qwen2.5-VL-7B video server**：`127.0.0.1:8643`——**關閉**（要睇片先手動開）
- **Ports**：8765（alerts MCP + /settings）、8770（reply）、8771（media bridge）、8642（Hermes API）、8643（Qwen video，關）
- **cron**：sk-activity-monitor（1m）、Gateway watchdog（2m）、jarvis-daily-self-review（09:00，monitor）、**jarvis-sidecar-health（2m，monitor——8765 DOWN 先醒）**
- **Git**：`feature/hermes-alerts-mcp` branch；HEAD `1061218`（onnxruntime pin）；working tree 乾淨

## 今日完成（2026-08-31）

### Voice 診斷 session（SK 報「只能喚醒一次」）
1. **Root cause #1（已修）：onnxruntime 1.28 bug**——openwakeword 0.6.0 喺 onnxruntime 1.28 上模型輸出全 0（melspectrogram 前處理壞，predict 靜默返回 0）→ wake best 卡 0.001 永遠唔 fire。**downgrade 1.27.0**（py3.14 可用最後版本）+ pyproject pin `<1.28`；修復後 OWW 恢復（peak_best 0.129）。wake.py predict except 加 `oww_predict_err` log（診斷用）
2. **Root cause #2（環境）：Arctis headset 休眠**——rms=0.000 持續 = mic 斷連；「只能喚醒一次」= 第一次戴住喚醒 → headset 休眠 → 叫唔醒。戴返/喚醒 headset 即 work
3. 診斷流程（記錄）：wake_debug best 0.001 檢查 → piper 合成「Hey Jarvis」餵 OWW（得分 0 = 模型問題）→ predict keys 檢查（key 由 `hey_jarvis_v0.1` 變 `hey_jarvis`，但 `_jarvis_score` substring match 無影響）→ onnxruntime 版本排查

### 未完成項處理 session（SK「do 4,6,8,10,11,12 / del 5」）
1. **#12+#4 Settings**：settings.html 加 stt_preload；tkinter SettingsWindow 凍結（統一由 Electron 管）
2. **#6 Sandbox 決定**：Docker Desktop 勝出（WSL2 唔夠隔離）→ `src/jarvis/sandbox.py`（lazy、network none、無 credentials）+ 9 tests
3. **#8 Prompt Optimizer 完成**：`prompt_optimizer.py`（GEPA 進化 + score-driven PatternStore + injection 防禦）+ 10 tests
4. **#10 Mage-VL video**：`analyze_video_sampled`（OpenCV 抽幀）替代 mamba_ssm streaming + 6 tests
5. **#11 GPU failover**：`gpu_metrics_with_fallback`（nvidia-smi → HWiNFO SHM；GPU-Z 冇 API 記錄唔做）+ 7 tests
6. **#5 刪除**：C 擴展連接取消（用 Discord 就夠）
7. **驗證**：317 passed + eval_gate --all 全綠（hash 8db6be8acd0e85c6）

### 資源優化 session（SK「5.5GB 太多」+ fix them all）
1. **SenseVoice lazy load（記憶體 -65%）**：新 settings `stt_preload`（default False）+ thread-safe lazy load；sidecar Private 5.5GB→1.9GB、WorkingSet 1.9GB→454MB
2. **UnicodeDecodeError 徹底修**：8 個 subprocess 位加 errors="replace"（taskkill/powershell/nvidia-smi/pgrep/TTS）
3. **Mic 健康偵測**：wake heartbeat 連續 3 次 rms≈0 → voice_status `mic_signal_ok=false`
4. **Sidecar watchdog cron**：`jarvis-sidecar-health`（job 6a98a79be95f，every 2m，monitor pattern——**最初漏咗 monitor 參數會 spam，已修**）
5. **Git commit**：jarvis-pc 全部工作 commit（290ca61 等，secrets scan 乾淨）
6. **Hermes memory 清理**：personal 92% / user 90%

### Monorepo 搬遷（SK「兩邊合併成一個 monorepo」）
- jarvis-hud 搬入 `jarvis-pc\hud\`（一個 repo、一個 remote、git 歷史保留）
- 路徑去硬編碼：eval_gate `__file__` 相對 + host.json + sys.executable；prompt_pipeline pattern store 相對
- .gitignore：hud/node_modules + hud/dist（766MB 唔 commit）
- 3 個 .lnk 更新指新位置；舊 jarvis-hud 目錄**待刪**（下次重啟後）
- AGENTS.md / HANDOFF / skill 同步；commit `80d3f9c` + `9224f1e`

### bug review + E4 session（check for all bug / finish the rest）
1. **獨立 reviewer ×2（fail-closed）**：全部修好——mcp_alerts_http（7）、autonomy（6）、eval_gate（4）
2. **E4 clarify precision consumer**：`clarify_stats.py` + 9 tests；入 golden suite

### wiring session（Self-Evol 4 module 接入主流程）
- eval_gate --lock、MCP tools（clarify/autonomy）、AutonomyState persistence、skill jarvis-self-evol-ops、AGENTS.md Commands

### 中文回覆 → 英文短版 TTS session（2026-09-01，SK：「I expect jarvis can reply me with a english version (shorted one)」）
- **問題**：Hermes/HANDS 中文回覆 → mouth skip CJK → 沉默／只唸英文詞
- **修復**：`brain.translate_to_english_short()`（純英文 passthrough；中文 → LLM 翻譯一句 ≤20 words 英文）；接入 `hermes_bridge.parse_hermes_output` + `_chat_via_api`（spoken 空時 fallback）+ `shell_app._pick_spoken_line`（[ok]/[fail] 中文 → 翻譯）
- **驗證**：34 tests（新 test_brain_translate 6 + hermes_bridge 2 + shell_app 1）+ 全套 **378 passed** + eval_gate 全綠（golden 33 files）+ **真實 LLM 實測**：「已開 Cursor」→「Cursor is now open.」✅ / 長句 11 words ✅ / 純英文 passthrough ✅
- **注意**：翻譯只喺「Hermes 冇出 SPEAK 英文」時先觸發（正常有 SPEAK 唔加 delay）；Hands 指令中文回覆每次 +1-2s LLM call
- 新規則（SK 2026-09-01）：**開工前設計驗收標準；完成後實際運行項目逐項驗收（面板/按鈕/數據/報錯），全過先算完成**——已入 memory；主契約 AGENTS.md 更新等 SK 批准

### 2026-08-31 凌晨 session（修復 session）
- Sidecar respawn（8/29 死因未明——下次再死要查 Electron health-check）、HUD window 消失修復

### E2/E3 + 文檔 session（2026-08-31 晚，SK「do it」）
1. **D2 確認已實現**：`shell_app._start_game_alert_watch`（run() 1781 已接）watch `sk_activity.json game_started` → enqueue `<Game> is ready, sir.`；今日補 phrase capitalize（minecraft → Minecraft）
2. **E2 STT 準確度追蹤**：新 `src/jarvis/stt_stats.py`（serve.log `asr_repair=` → repair ratio + top confusions + suggestions ≥3 次先建議，唔自動 apply）+ `--fingerprint` REPAIR_RATIO + 寫 stt_stats.log；9 tests
3. **E3 Response 延遲**：mouth `tts_ok` print 加 HH:MM:SS timestamp；self_monitor 計 `resp_lat`（oww_fire→tts_ok 0-60s；>5s notable）；9 tests
4. **文檔**：`docs/hermes-bridge-auth.md`（auth 機制/風險/rotation 方法）+ `docs/settings-field-map.md`（48 fields ↔ settings key ↔ IPC ↔ clamp + 加新項 checklist）
5. **CI**：全套 **347 passed**（+30 新 tests）+ eval_gate --all 全綠（golden 28 files 316 passed + py_compile 33 / regression 16 / stress 65）+ `--lock` 一致（30 files）；新 hash `05ec926cefc0e5e1`
6. **pass2 新脆弱位**：⑬ stt_stats 格式耦合 ⑭ mouth tts_ok 格式依賴 ⑮ 跨午夜 edge ⑯ suggestions 冇 consumer（記入 REMAINING_WORK）

### 脆弱位修復 session（2026-08-31 晚，SK「find 脆弱位就即刻修，修到冇 bug」+「any code 改動一律經 cursor」）
1. **Cursor review**（cursor-review-e2e3-2026-08-31.md）：**11 findings（2 HIGH / 5 MED / 4 LOW）全部處理**
2. **HIGH #1**：`_compute_latency` midnight `0.0` truthiness（`not ft` 食咗 00:00:00）→ `ft is None`
3. **HIGH #2**：repair_ratio 窗口唔一致（repair_log full-read vs wake tail）→ `_REPAIR_WINDOW=2000` tail + engine 20000 行 rotation（`_maybe_rotate_repair_log`）
4. **MED**：docstring overclaim（latency 係 heuristic 唔係 utterance pairing）、`capitalize()` 毀 CS2 → `game_ready_phrase`（first-char upper only）、`_consecutive_days` window 參數化、repair_log 寫失敗 silent → stderr warn、tests 補齊（test_engine/test_shell_app/00:00:00/ERROR exit 2）
5. **LOW**：docstring repair_log primary、`_tail_lines` deque（兩檔）
6. **舊脆弱位處理**：① self_review main fail-visible（parse 0 → ERROR+exit2）② 缺日唔當連續退化 ③ 註釋 ④⑦ 唔改（安全設計）⑫ ERROR 分支固定輸出
7. **CI**：全套 **368 passed** + eval_gate --all 全綠（golden 30 files 337 / regression 16 / stress 68）+ `--lock` 一致（32 files）；hash `2a29a8ef41eb43c4`
8. **規則更新（SK）**：any code 改動一律經 cursor-agent（cursor 改+review；自己唔好直接 patch jarvis code）

## 剩低（詳見 REMAINING_WORK.md）

- ⏳ **SK 實測：戴 headset 試 wake**（2026-08-31 voice 診斷後）——onnxruntime 已修，**而家 rms=0.000 = headset 休眠**；戴返試「hey jarvis」；如果戴住都唔 fire → 調低 wake_threshold（而家 0.75 可能偏高）
- ⏳ **刪舊 jarvis-hud 目錄**（SK：「你之後處理」）：monorepo 搬遷後舊目錄仲喺度（運行緊 process 用緊）。**下次 JARVIS 重啟（用新位置成功運行）後刪**——刪前確認冇 process 由舊路徑 load
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
- 🟡 **G 人手實測**（等 SK）：Tier 1（BGM 誤觸 / 喊完→有聲 ≤3s）、聲紋 enrollment（要新 mic）、AEC voice call、Settings tab（HTML 已齊）
- ❌ **C 擴展連接**：已取消（SK：「用 Discord 就夠」）
- ⏳ **Qwen2.5-VL 自動啟動**：SK 決定唔加（要睇片先手動開）

## 陷阱（重溫）

- **Settings 單一 writer**：改 settings 用 sidecar `POST /settings`（Bearer = `%APPDATA%\Jarvis\alerts\mcp_token.txt`），唔好直接寫 settings.json
- **dpapi:** 值唔好當明文讀；settings.json 已加密
- **jarvis serve** 由 Electron spawn（JARVIS_ELECTRON_HOST=1 headless）；唔好手動起第二個
- **⚠️ onnxruntime 1.28 bug（2026-08-31 實測）**：openwakeword 0.6.0 喺 onnxruntime 1.28 上模型輸出全 0 → wake 死（best 卡 0.001）。pyproject 已 pin `<1.28`；**唔好升級 onnxruntime**。wake_debug `best` 一直 0.001 + 冇 `oww_predict_err` = 呢個坑
- **Arctis headset 休眠**：rms=0.000 持續 = mic 斷連（headset 休眠）——戴返/喚醒先叫到；`mic_signal_ok=false` 喺 voice_status 顯示
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
