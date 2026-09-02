# HANDOFF — JARVIS 交接（固定檔）

> **呢個係固定 handoff 檔**（2026-08-30 起）：每次 session 結束**更新呢份**，唔好開新日期檔；舊交接版本移入 `plans/archive/`。
>
> 下次 session 起點：**JARVIS ONE 0.4.10 跑緊 + Self-Evol Task 0-9 全部完成（Phase A-E 基建落地）+ Content Absorption Framework 已落地（2026-09-02）**。讀呢份之前先讀：
> 1. `jarvis-pc\AGENTS.md`（專案 context——**自動載入規則已寫入主契約，唔使 SK 叫**）
> 2. `C:\Users\skps9\AGENTS.md`（主契約——Code Review 兩次規則已升格入契約）
> 3. `REMAINING_WORK.md` + `2026-08-29_self-evol.md`（計畫書，R1-R20b 齊全）

---

## 今日（2026-09-03 session）—— Skill 治理（整合 + 揀選驗證）+ C2 開始

**Skill 治理 Phase A（SK「整合現有 skills」→ 128 → 117）**
1. **A1 short-video 三合一**：刪 `short-video-content` + `short-video-platform-read`（pre-merge diff 確認全部內容已喺 `douyin-tiktok-content`）
2. **A4 llm-tool-loop 二合一**：`llm-tool-loop-integration` merge 入 `llm-tool-calling-reliability`（補 tool_call.id echo 等 3 點）
3. **A5 aux-model 二合一**：`hermes-aux-model-setup` merge 入 `hermes-aux-models`（用 setup 版更詳細 deepseek-vision.md reference）
4. **A2 Windows 群收斂**：刪 5 個（background-automation/headless-ops/focus-safe/activity-aware/headless-capture）——內容 zero-loss 搬入 `windows-desktop-automation` references/merged-*（含 sk-machine-facts/flash_catch.py 等）；`windows-screen-capture` 吸收 headless-capture（HTML→PNG）
5. **A3 MC 群四合一**：刪 3 個（minecraft-llm-assistant/pack-ai-mod/pack-ai-deepseek）——原稿 zero-loss 保留喺 `minecraft-modpack-ai-development/references/merged-*`
6. Review（requesting-code-review 流程 + 獨立 reviewer pass）：修 7 個 skill 引用已刪名（改指 umbrella）+ plugin docstring + CJK bigram 跨 gap bug

**Skill 揀選驗證 Layer 1（SK「跟條片方案再進一步」→ A+B+C 全做）**
1. 研究結論：Hermes skill 揀選無驗證（source 查證）；`learn_prompt` 禁 router **skill** → 用 **plugin** 路線；`pre_tool_call`/`post_tool_call`/`pre_llm_call` hooks 可行；plugin 注入唔破壞 prompt caching
2. **`skill-router-verify` plugin**（`~/.hermes/plugins/skill-router-verify/`）：Layer 1 observer（post_tool_call 記每次 skill_view → task + would-block 模擬）→ `logs/skill_selection.log.jsonl`；**唔 block**（Layer 2 延後，要數據證明先開）
3. Classifier：零 LLM keyword scoring（117 skills index + 中英 alias + CJK run bigram + 同 category 豁免）；實測 17/18 場景、latency 0.1ms
4. Plan：`plans/2026-09-03_skill-router-verify-plan.md`（過 adversarial review——裁決先治本後治標：整合先行 + Layer 1 數據先，Layer 2 延後）
5. **已 enable + gateway restart 生效**（verify：log 有真實 entry）；**觀察進行中**——cron `8294250748fa`（9/10 09:00 一週報告，script `analyze_skill_selection.py`）→ would-block <5% 唔開 Layer 2；>15% 先考慮
6. Skills 整合 plan：`plans/2026-09-02_203000-skills-consolidation-plan.md`（A1-A5 已執行，Plan 檔可標完成/存檔）

**C2 新工具 check review（開始——優先序 C2 > Content > Jarvis > MC，SK 2026-09-03）**
1. **WeSight**：❌ 排除——**SK 已試過覺得太差**（2026-09-03）
2. **Browser-BC**（Einsia，436-548★）：❌ 排除——**冇 license** + 7 週無 push + 單一 contributor + 用途係 browser behavior cloning（同 SK stack 唔夾）
3. **Prime Agent**（PrimeIntellect-ai，19.7k★ MIT 活躍 pushed 2026-09-02，有 Windows docs）——**未判**：RLM coding harness 同 Hermes 重疊度高；待 adversarial 判斷 + SK 拍板（下次 session 繼續）

**下次 session 優先序（SK 2026-09-03 明確）**：C2（完成 Prime Agent 判斷）→ Content（bilibili adapter/douyin A5+）→ Jarvis（REMAINING_WORK sync + test_stt_stats + LHM + Phase 2）→ MC（slim regression + commit/push）最後

**規則（2026-09-03）**：每次開新 session 前必先 hand off（更新本檔）——已入 memory

## 今日（2026-09-02 晚 session）—— /compress 診斷 + Content Absorption Framework

**Hermes /compress timeout 診斷（純檢查 + config tune，SK 已批）**
1. 根因：compression 一次要 8-10 分鐘（508k tokens session → 594s），Discord interaction 15-min deadline + 壓縮期間 input 全 queue → 睇落 timeout；09-01 有多宗真失敗（deepseek streaming 600s 零 output → continuing without compression）
2. Upstream 已知：GitHub #88988（Desktop /compress 報 120s timeout 但壓縮實際成功）+ #89095/#83087/#73468（PR 全部 open 未 merge）+ #15935（summary model timeout 唔 fallback）
3. **已改 config**（備份 `config.yaml.bak-20260902_191303`）：`compression.threshold` 0.5 → **0.35**（早啲壓、細 session、stall 機會大減）；`hermes config set` 官方 CLI 改
4. 未做：auxiliary.compression.model 換快 model（要 context ≥1M 嘅 flash 先得——冇啱就唔郁）；等 upstream fix merge

**Content Absorption Framework（Douyin → 多平台，Phase 2 落地）**
1. 新 skill `content-absorption`（media/）：7 步 SOP（adapter→scan→classify→summarize→improve plan→adversarial review→**SK 批准先落地**）+ 反噪音 filter + bias 修正 + 同 douyin-tiktok-content/youtube-content 嘅界線
2. references：`SCHEMA.md`（統一 schema + 欄位覆蓋矩陣——**douyin 實測冇 url/id 係 known gap**；youtube 已 full coverage）+ `adapters/douyin.md`（實測遷移）+ `adapters/youtube.md`（**2026-09-02 實測 verified**——cookies 已 export 追加）+ `adapters/bilibili.md`（planned）
3. Plan：`plans/2026-09-02_192000-content-absorption-framework.md`（過 adversarial review，8:2 支持）
4. **YouTube PoC 已完成（2026-09-02 晚）**：SK export 咗 YouTube cookies（23 entries 追加 cookies.txt，先 backup）；yt-dlp 實測 Liked (LL) 167 條 + Watch Later (WL) 67 條全攞到（unified schema，url+id 全 capture）。**⚠️ SK 澄清：YouTube 唔係 absorption 來源——「yt is for other project, we just need u can watch or read it」**——YouTube 用途 = watch/read 能力（transcript + Qwen-VL/Mage-VL），adapter 保留做 on-demand fetch；吸收 pipeline 嘅好來源 = 特登收藏（douyin）。framework 跨平台架構仍由 douyin + youtube scan 證明，但吸收 pipeline 主力係 douyin 類「特登收藏」平台

## 現行狀態（2026-08-31 晚 session 尾）

- **JARVIS ONE 0.4.10**：`jarvis-pc\hud\dist\JARVIS-ONE-0.4.10.exe`（**monorepo**：jarvis-hud 已搬入 `hud/` 子目錄，git 歷史保留）；3 個 .lnk 全指新位置；**2026-09-01 已重啟切換到新位置 + 舊 jarvis-hud 目錄已刪（釋放 765MB）**
- **Sidecar 8765**：PID 37496（restart 多次）；health OK wake_on=true；**onnxruntime 已 downgrade 1.27.0**（1.28 bug 令 openwakeword 輸出全 0——已 pin `<1.28`）
- **Voice 診斷結論（2026-08-31 晚）**：① onnxruntime 1.28 = OWW 全 0（已修）② **Arctis headset 休眠 = mic rms=0.000（而家就係呢個狀態）——戴返/喚醒 headset 先叫到** ③ wake_threshold 0.75 可能偏高（self-monitor 調出嚟）——戴 headset 試完再決定
- **Qwen2.5-VL-7B video server**：`127.0.0.1:8643`——**關閉**（要睇片先手動開）
- **Ports**：8765（alerts MCP + /settings）、8770（reply）、8771（media bridge）、8642（Hermes API）、8643（Qwen video，關）
- **cron**：sk-activity-monitor（1m）、Gateway watchdog（2m）、jarvis-daily-self-review（09:00，monitor）、**jarvis-sidecar-health（2m，monitor——8765 DOWN 先醒）**、**jarvis-session-handoff（每日 05:45，deliver local——reset 前自動對比 session → 更新 HANDOFF + commit docs，唔 push）**
- **Git**：`feature/hermes-alerts-mcp` branch；HEAD `84834f2`（2026-09-01 cron run：HANDOFF 自動更新）；9/1 晚 session 嘅 HANDOFF docs（Review 分類規則 + MC 摘要）由 2026-09-02 handoff commit（HEAD 再推前）

## 今日（2026-09-02 session）——Game Fix + Douyin Import + 規則

**JARVIS：Game Ready 誤報修復（Phase 1 完成）**
1. **activity_monitor.py**（`%LOCALAPPDATA%\hermes\scripts\`，非 repo）：遊戲偵測由前景視窗改 **process-based**——Steam RunningAppID + tasklist + wmic Java cmdline（client/server 分——`-client.jar`/EntryPoint/knotclient/forgewrapper/newlaunch）；session latch + 180s flap guard（ts 唔 refresh）+ running-set-growth alert signal + lowercase normalize。**六輪 cursor fix + 4 輪獨立 review（11 bugs 全修）→ PASSED**。部署：`.py.bak` backup 咗
2. **shell_app.py**：game watch 改 track `last_alerted_game` + timestamp freshness gate（120s）——commit **`ea38b22`**
3. **Sidecar 已重啟**（新 PID，~60s respawn）——重啟後零誤報實測 ✓
4. 驗證：smoke 全綠（CS2+Minecraft detect）、8 場景模擬、eval_gate regression 16/16 + stress 68/68（golden 1 fail = **baseline test_stt_stats**——環境敏感，與改動無關，記低之後修 test isolation）
5. 產物：plan `2026-09-02_135000-game-session-detection-phase1.md`（Status ✅ 已更新）

**其他（早前完成）**：JARVIS_HUD.vbs 開機彈錯已清（%TEMP% backup）；LHM config 改 tray 模式（**下次開機驗證**）；voice out 問題 SK 話 ignore first（未處理）

**Douyin 收藏 → Knowledge Import（side quest 完成大半）**
1. 掃描：199 收藏 unique（browser + cookies 登入 + CAPTCHA SK 手動過一次）→ **101 條 AI/coding（51%）** 分類存 `browser-use workspace douyin_favorites_classified.json`
2. 分析 notes：`%TEMP%\douyin_import_notes.md`（101 條核心提取 + 噪音 filter）
3. Improve plan：`2026-09-02_174500-douyin-improve-plan.md`（adversarial review ×2 → 6:4 支持 patch 完）
4. **A1-A4 已執行**：A1 plan skill 加「任務拆解+上下文隔離」3 步法；A2 cursor audit（8 項無缺口）；B1 memory consolidate（99%→88%）；B2 cursor skill 加 dispatch template（4 段固定格式）
5. **新規則**（SK 2026-09-02）：裝/試任何新嘢前必查 online review（stars/ARCHIVED/社群）→ adversarial 判斷需唔需要/有冇更好 → 裝前問 SK——已入主契約 AGENTS.md（`C:\Users\skps9\AGENTS.md` + 源頭 `Code_Project\Hermes\AGENTS.md`）+ memory
6. **mcp-builder check review → 唔裝**（3 stars + ARCHIVED——抖音介紹誇大；替代：官方 MCP SDK）

## 跨 Project 全面盤點（2026-09-02 session 尾——SK「check all plan and project first」）

### 1. super_minecraft_AI_player（MC——最高優先，Ask engine）
- main = `0df2d08`（feat(ask): deepseek tool-loop reliability + workbench-first + card placement），**ahead of origin 12 commits 未 push**
- ⚠️ **實際有未 commit 改動**（同佢 HANDOFF「全 commit」描述唔一致——實際 working tree 有）：`AskEngine.java` + `AskCardFallback.java`（**Forge 1.19.2 + NeoForge 1.21.1 雙樹**）+ `tests/check_ask_card_fallback.py` + `code_change_log.md` modified；`.hermes/` untracked——疑似 09-02 凌晨尾段 purpose-miss fix + how-to-use cards fix（jarvis-pc HANDOFF 2026-09-01 記錄「未 commit」）
- 佢自己嘅 HANDOFF：`.hermes/plans/HANDOFF-2026-09-02.md`（下次 MC session 讀呢份）
- 下次重點：SK 煙測最新 jar（`packai-0.1.14+mc1.19.2-forge.jar` 已換入 NFWC instance）→ commit+push 決定 → slim（auto）模式對照
- 3 個 pre-existing python fail + neoforge compileTestJava pre-existing fail（HEAD 都 fail）
- 3 個分支 clone dirs 存在（`super_minecraft_AI_player-{ask-native-tools,bugfix-ask-fp,bugfix-summon-miss}`）——歷史用，可清理/參考

### 2. Earth_Online_App（RN 生活 RPG——次優先）
- 狀態：**MVP 封測進行中**（實機封測 → 修 blocker → 邀測）——唔好做 POI/洋界（決策排封測後）
- ⚠️ working tree 有 modified（`Earth_Online_v.2.0/`、`TODO.md`、`code_change_log.md`、`docs/beta-guide.md`、`docs/mvp-beta-testing-guide.md`）+ untracked（`docs/mvp-beta-tester-handbook.md/.docx`、`docs/eng-review-test-plan-2026-08-07-life-ledger.md`）——上次 activity ~2026-08-07，暫停一排
- 手冊：`docs/mvp-beta-tester-handbook.md`（Word/WhatsApp 發放用 .docx）
- 注意：`Code_Project/Earth Online App/`（有空格）係另一個 dir——得 code_change_log.md，疑似舊/垃圾，main 係 `Earth_Online_App/`

### 3. CS_asstant（CS2 Coach——最低優先，核心未做）
- **唔係 git repo**；有 `scripts/`（radar_cv/radar_track/overlay 等 CV 原型）+ `data/` plans（`coach_system_v3_plan.md`/`mode_matrix.md`/`final_plan.md` 等）
- 狀態：暫停（核心功能未做——plan 喺 data/*.md）

### 4. Code_Project\Hermes（規則包源頭）
- AGENTS.md / README.md / recommended-config.yaml / SOUL.md / templates——今日新規則（裝前查 review）已同步呢度

### 5. jarvis-pc（JARVIS ONE）——見上方今日 section + REMAINING_WORK（A1/A2/A4/B 未做、mic 等新 mic）

## 下次 session（2026-09-02 handoff 指示）

1. **C2：新工具 check review**（照新規則逐個）：Prime Agent（17.7k stars RLM）/ WeSight / Browser-BC——值唔值入 stack
2. **Douyin 通用多平台內容吸收 framework**（SK 之前提「it can for many diff website」——Phase 2 follow-up，另出 plan）
3. **Voice out 決定**（SK 想處理先；default 保留）
4. **LHM 開機 tray 驗證**（SK 重啟過 PC 先見到）
5. **test_stt_stats baseline fail 修**（test isolation——serve.log 環境敏感）
6. JARVIS master plan 其他項（REMAINING_WORK A1/A2/A4/B——等 SK 指示；mic 相關仍然等新 mic）

## 今日（2026-09-01 daily reset 後 session）

- **check history 補返 HANDOFF**：上個 session 尾做咗嘅 Discord Voice Out + CPU temp 未入 HANDOFF——已補（commit `4f8d048`）
- **HANDOFF 加今日 session 狀態 + what next 選項**（commit `bbde88b`）
- **建立 jarvis-session-handoff cron job**（job `7b4af62c87c3`，每日 05:45，deliver local）：每日 reset（06:00）前自動 session_search → 對比 HANDOFF → 有實際工作就更新 HANDOFF/REMAINING_WORK + commit docs（唔 push）；冇工作回 NO_WORK 唔郁檔；SK 規則「test before run」即刻 run 驗證（就係今次 run）
- **SK 計劃買新 mic**（上個 session 尾已講：「wait me buy a new mic first」）——mic 相關全部 pause（wake 實測 / 聲紋 enrollment / AEC voice call / Tier 1 / STT 準確度）
- **Review 分類規則（SK 2026-09-01 確立）**：code 質素→requesting-code-review；決策/plan→adversarial-decision-review；PR→github-code-review；唔好淨讀文件當 review 完——已入 memory
- **⚠️ 主 session 轉咗去 MC project（super_minecraft_AI_player）**：詳見下方「MC 專案 session 摘要」——jarvis 線維持等 mic，今日主力喺 MC

## MC 專案 session 摘要（2026-09-01，super_minecraft_AI_player）

**背景**：SK 問「check cursor project」→ 發現 CS2 AI Coach（最低優先）＋ 4 個 project 盤點 → MC（最高優先）全面 review → 重寫決策（adversarial review：8:2 反對 remake 成個 mod）→ 決定「Ask 核心重寫」（Strangler 並排）

**已完成：**
1. **Merge**：bugfix/ask-dsml-leak + purpose-scrub-hold-y 落 main（`42ef9ef`；ask-tool-fingerprint 已喺 PR #18；ask-summon-pack-miss 已包含）；修咗 2 個 merge conflict（SHIFT_PLUS_CHROME 復活 + method duplicate）
2. **Ask 核心重寫 Wave Slim-1**（plan：`.hermes/plans/2026-09-01_072000-ask-core-rewrite-slim.md`）：
   - Task 1-2：capable bridge split（`factsFull` fallback 全量牆 / `List.of()` capable slim + `jeiForLlmSlim`/`purposeForLlmSlim`）Forge+Neo
   - Task 3：token 量度 test（ratio 0.031 = -97% mirror 估算）
   - Task 4：質素 A/B test（3 問句）
   - Task 5+5b+5c：`ask_player` tool + `AskResult.needsPlayer`（v1 sentinel，**已移出 CAPABLE_TOOLS**——loop 冇偵測、needsPlayer 零消費者，reviewer FAIL 後修正）
   - 驗證：6 Python tests 綠 + Forge compileJava OK + requesting-code-review findings 全修
   - **未 commit / 未 push**（全部 working tree）
3. **NFWC 煙測（AI_test_NFWC_DIM，SK 開 game）**：
   - **發現 regression**：`askNativeTools=auto`（capable slim）→ 問「鐵鎬怎麼合成」答「unindexed」；`off`（舊牆）→ 答到（動力合成器 3 鐵錠 2 木棍 + 配方網格）
   - **根因**：slim 模式 round 0 冇牆，deepseek-v4-flash 冇正確 call tools（log 零 tool_calls）→ 兩頭唔到岸
   - **暫時處理**：config 改 `askNativeTools="off"`（備份 `%LOCALAPPDATA%\Temp\packai-client.toml.bak-slim`）——SK 確認 off 正常
   - **未決**：force（on）模式未試；slim 默認值要修（`PackAiConfig.askNativeToolsMode` 默認 `auto` → 應改 `off`）；「模型唔 call tools」要查（tools schema / prompt 提示）；或 slim 改為保留部分牆
   - **凋靈題**：entity 問題（非物品），`resolve_entity` tool 未實作（harness Wave 2），預期答唔到

**後續（2026-09-02 凌晨，同一 session 延續）**：
4. **purpose miss fix**（cursor-agent）：`AskEngine.ask` 加 `loop.intent() != PURPOSE` guard——用途問句唔再強行插入「本包找不到取得方式」；Forge+Neo 雙樹同步；**未 commit**
5. **how-to-use cards fix**（cursor-agent）：`AskReplyScrub` HOW_GET 偵測加「怎么用/怎麼用/how to use」→ 用途問句卡片跟方法行（唔堆底）；`tests/check_ask_card_fallback.py` mirror 更新；**未 commit**
6. **驗證 + jar**：checks 83/86 過（3 個已知 pre-existing fail）；`packai-0.1.14.jar` build（02:00 / 04:07 兩版）已換入 AI_test_NFWC_DIM instance；等 SK 開 game 煙測「动物脂肪怎么用」
7. **JEI 錯誤卡線索**：SK 指出「3 小麦+3 苹果+1 碗」配方唔存在（AI 信咗 JEI 卡答錯，卡 output 空）——`JeiRecipeCards.java` 嘅 collect/過濾邏輯要查（未查完）

**下次 session 重點（MC）**：
1. 修 slim regression（默認 off / 查 deepseek tools call / 或保留部分牆）——**經 cursor-agent**
2. 決定 commit + push Wave Slim-1（而家未 commit）
3. `ask_player` v1.5 接線（loop 偵測 + UI）或暫時唔理
4. SK 試 force（on）模式對照


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

### Discord Voice Out + CPU temp session（2026-09-01 凌晨）
1. **Discord Voice Out ✅ live**：Hermes 每次 Discord 回覆 SK 自動用 Jarvis TTS 唸英文短版（skill `jarvis-voice-out`；上個 session 尾已接好，SK 實測聽到聲）
2. **CPU temp ✅（N/A → 實時 ~70°C）**：裝 LibreHardwareMonitor（portable `%LOCALAPPDATA%\LibreHardwareMonitor`，tray-only 54MB）+ PawnIO kernel driver（AMD 讀溫必要；setup flag `-silent` 唔係 `/S`）+ LHM Remote Web Server 8085（config key `runWebServerMenuItem=true`）+ `hw_monitor.py` CPU temp WMI→LHM HTTP fallback + Task Scheduler「JARVIS LHM Sensor」onlogon /rl highest（admin 先讀到 AMD sensor）。**坑**：兩個 LHM instance race = 讀 0（GitHub #2363）；AMD 冇 MSAcpi thermal zone（WMI 一定 None）。完整方案已寫入 skill `windows-hardware-monitoring`
3. HUD main.js 每 2s poll 自動攞到 CPU TEMP（SK 確認 HUD 有數）

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

### Game Session Detection Phase 1（2026-09-02 session）
- 修「X is ready, sir.」誤報（前景切換 + Minecraft server 誤判）——process-based detection（Steam RunningAppID + tasklist + wmic java cmdline client/server split）+ session latch + running-set-growth alert
- activity_monitor.py（hermes scripts）已應用（backup .py.bak）；shell_app.py commit `ea38b22`；sidecar 已重啟生效
- 4 輪 independent review（11 findings 全修，final pass）；plan: `.hermes/plans/2026-09-02_135000-game-session-detection-phase1.md`
- 已知：`test_stt_stats::test_missing_logs` golden fail = baseline 環境問題（serve.log 有 repair 記錄）——要修 run_once fallback 或 test isolation
- 待做：SK 實測場景 A-E（開 game/切 Discord/關 game）；Phase 2 = 通用 app detection framework（SK 願景：唔止 game）
