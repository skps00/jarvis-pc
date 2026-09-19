# HANDOFF — jarvis-pc（狀態區塊 + 逐日 index）

<!-- STATE:BEGIN -->
## 狀態（每次 session 尾／cron **改寫**；新 section 一律加喺本區塊**之下**）

- **目標**：JARVIS ONE（語音／HUD／alerts）穩定收尾 ＋ MC packai（Forge 1.19.2 primary）設定／答案版面／卡片修復落地。計畫書：`.hermes/plans/REMAINING_WORK.md`
- **現狀（2026-09-20 06:5x 改寫；全部 Hermes 親核）**
 - **Git 位置**：HEAD ＝ `feature/hermes-alerts-mcp`（ahead 41 未 push）；`origin/main` 有 1 個未入本分支嘅 commit（PR #12 merge `96be515`）；本地 `main` behind 96
 - **JARVIS ONE**：HUD **0.4.13** 已 build＋部署＋3 個 `.lnk` 更新（09-16）；`hud/main.js`＋`hud/package.json` **未 commit**（等 SK 真機驗收）；8765／8770／8771 有應
 - **Hermes**：gateway 09-17 07:57 恢復後無再 crash；⚠️ cron `jarvis-session-handoff` 今日 05:45 run **FAILED（HTTP 429 rate limit）→ 零寫入**
 - **jarvis-pc tree**：未 commit ＝ `hud/main.js`＋`hud/package.json`＋本 HANDOFF（09-19 skill 段）；untracked ＝ `.hermes/plans/2026-09-19-skill-voice-merge-plan.md`＋`plans/reviews/`（5 份）
 - **packai（MC 主線，詳 MC repo HANDOFF）**：真 instance `AI_test_NFWC_DIM` jar ＝ **`06b5b129a114`**（09-18 07:12，親核 sha256）；**之後三批 code 未部署未 commit**（fix A 09-19／P0 崩潰 `31185e8`／v6 routes `344e805`）→ 真機驗收一律走沙盒（`packai_sandbox_ftb`，harness jar 09-20 01:00）
 - **MC tree**：**未 commit 73 檔（+4,484／−1,305）＋54 untracked**；`mod_version` 已 `0.2.3`
- **唔准郁（硬限制）**
 - 打機／用緊電腦：**零彈窗、零搶焦點**（先讀 `state/sk_activity.json`）
 - GUI 窗一律開**第二副屏幕**（SK 要睇嘅先主螢幕）；Chrome 主動開 = `bg_launch.py --minimized`
 - `AGENTS.md` 受保護（要 SK 明確 go）；唔准 `curl|sh`；**HANDOFF 視為可公開 → 唔准入 secrets**
 - packai code **一律經 cursor-agent**；**唔准 `git add -A`**；**部署只准用 `mc_mod_deploy_jar.py`**（真 instance 唔准郁）
 - cursor 派工**唔准用 `--no-desktop`**（會令 git／rg 彈 console 窗）
 - **語音／mic 線 HOLD（等 SK 新 mic）**：唔郁 `wake.py`／STT(ASR)／AEC／聲紋／wake threshold／mic device；唔為測試重啟 sidecar；唔叫 SK 測 wake（Settings tab 例外）
- **未解（等 SK 決）**：① **packai P1 次序**（worldgen 三類／D2 必答清單／tracer bullet）② **真 instance jar 落後三批 code** → 要 SK 關 MC 才可 build＋deploy＋一輪真機驗收（P0 崩潰／fix A／v6 routes）③ **MC 73 檔未 commit** 幾時收入（版本已 `0.2.3`；舊「等 bump `0.2.2`」講法已過時）④ `hud/main.js`＋`hud/package.json`（HUD 0.4.13）等 SK 真機驗收 ⑤ jarvis-pc 41 個 commit 未 push ⑥ **SK 手動**：Surfshark 加 3 個 exclusion folder（`antivirus.db` 更新過就可能再刪 `python.exe`）⑦ `jarvis-pc/AGENTS.md`「現行版本」仍寫 0.4.10（受保護檔，要 SK 明確 go）⑧ MC：`run` 報 tokens delta=0（記帳異常）；`MAX_FACTS_PER_ITEM=8` 令 raw L refs 只有 ~47% 可達
- **下一步（優先序；MC 先行）**：① SK 定 packai P1 次序（建議先 worldgen 三類）② SK 開 MC → build 最新 ＋ `mc_mod_deploy_jar.py` 部署 → 一輪真機驗收（P0 崩潰／fix A／v6 routes）③ 驗收過後處理 MC 73 檔 commit（版本已 `0.2.3`）；**JARVIS 線**：HUD 0.4.13 真機驗收 → commit `hud/main.js`；push 待 SK 拍板
- **歸檔索引**：≤2026-09-11 全部搬 `plans/archive/HANDOFF-2026-09.md`；更舊見 `plans/archive/HANDOFF_2026-08-*.md`
- **參考段（喺檔尾）**：陷阱（重溫）／語音·硬體設定（驗證過）
<!-- STATE:END -->

## 2026-09-20 06:5x（Discord；SK「read hand off」→ drift 複核）
- 讀齊兩份 HANDOFF（jarvis-pc＋MC）＋逐項對 live 核（git／mtime／sha256／cron output／instance jar）；零新 code 改動。
- 捉到 4 處過時，已修入 STATE：① jarvis-pc STATE 停留 09-17（09-17 12:00 HOLD 已過期、MC 摘要滯後）② 本檔 09-19 skill 段未 commit ③ MC STATE 未寫 73 檔未 commit 規模 ④ cron handoff 今日 05:45 FAILED(429) 零寫入。
- 親核數字：jarvis-pc HEAD `c0a6a42`（feature branch ahead 41）；真 instance jar `06b5b129a114`（09-18 07:12）；MC tree 73 檔未 commit（+4,484／−1,305）。
- SK 09-20 06:5x：「read hand off / check last session / update hand off first」 → 已讀上一個 session（09-19 08:03–09-20 01:05，3,830 msgs），本檔已更新；下一步序（a 維度／生態群系／礦物分佈｜ b 必答清單｜ c 細試點） **等 SK 覆**。
- 親核：上一個 session 嘅遊戲內測試係喺 `packai_sandbox_ftb` 沙盒跑（jar `e0fbecc77085`）；真 instance jar 仍 `06b5b129a114`——jar 內方法名核實：真 instance **冇** `routeLinesForItem`／`mergeJarRoutes`，沙盒有。


## 2026-09-19 session（Discord；Hermes skill 庫 renew ＋ 語音 skill 3合1）

- **④ 語音 skill 3合1＝已執行＋驗收通過（SK `go`；Hermes 親手做）**：`jarvis-voice-assistant` 為 umbrella，吸收 `windows-voice-pipeline`＋`hermes-voice-windows`；兩者已用 **`hermes curator archive`** 歸檔（`skills\.archive\`）。**7 項實測驗收全中**：A1 `software-development 31→30`／`autonomous-ai-agents 13→12`／curator managed 124→122／`list-archived 1→3`；A2 14 個搬入檔＝**11 sha1 逐字一致＋3 有改動**；A3 總量 221,887→**222,982**（Δ＝+274 fm／+746 指標節／+75 七行）；A4 HOLD 段 identical；A5 `references/*.md`＝31；A6 舊名命中 12 行（逐行處置；`electron-windows-overlay:11` 已改指 umbrella）。備份：`%TEMP%\skill_voice_merge_backup_20260919_195843`（36 檔＋`MANIFEST.json`）；**還原 3 步已倒帶演練＝CLEAN（21/21 sha1 一致）**。plan：`.hermes\plans\2026-09-19-skill-voice-merge-plan.md`；review 5 份 `plans\reviews\2026-09-19_skill-voice-merge-plan-R{1..5}-opposing.md`（**4:6→6:4→7:3→7:3→8:2**）。
- **③ skill 庫 renew 其餘 3 項（Hermes 自己 ③ 清單）**：① 修真死路徑：`hermes-voice-windows` 內 `~/.hermes/AGENTS.md` → `$HERMES_HOME/...`（其餘 6 條經親驗為文檔／陷阱記錄＝誤報）② git 分支雙胞胎合併 → keeper `long-lived-branch-merge`（吸收政策表／invariant／診斷指令／非專家報告法），`git-branch-integration` 已原生歸檔 ③ `minecraft-modpack-ai-development` **100,306 → 56,212 字**（4 大段逐字搬 `references/`，sha1 驗證零損失）。
- **流程教訓（可重用）**：① audit 報告必須逐項親驗（今次第 1、5 項都係誤報）② **整合前先喺 `%TEMP%` 彩排 dry-run**（今次彩排揭發 2 個 bug：HOLD 抽段法錯、A6 用「合併前」值）③ 歸檔**一律用 `hermes curator archive`**——raw `mv` 會令 disk／snapshot／usage／live index 四層狀態唔一致（已修 `git-branch-integration`）。


## 2026-09-16/17 夜間（已核對，零新工作）

- 09-16 21:03–23:46 語音 session ×5（api_server）全部 ASR 亂碼（「系啊唔系…」「马叫维斯」等）→ 照 **mic HOLD**、零動作、零彈窗；00:22 SK 熄機；09-17 07:43 gateway 起返後 cron 補跑（session-handoff／daily-self-review 皆 ok）。核對：JARVIS 本體零 code 改動、零 commit、零 deploy。

## 2026-09-16 session（JARVIS HUD 0.4.13 ＋ Hermes watchdog v3）

- **HUD sidecar bug 修好**：`spawnSidecar()` 撞 ENOENT 唔清 `sidecarProc`（Node 只 emit `'error'`、**唔 emit** `'exit'`）→ 永久 early-return，sidecar 永遠拉唔返（今朝 8765 死嘅直接原因之一）。修：`on('error')` identity-check 清 ref ＋共用 5s respawn timer；早退／health check 加 `exitCode === null` 分支。A/B 實測（`%TEMP%\hud_sidecar_ab_test.py`）：舊 code 1 次嘗試後永久靜；新 code 11s 內 3 次後退避 60s；interpreter 中途出現 → **唔重啟 app** 之下 `8765 /health` 自動返 200。Build `JARVIS-ONE-0.4.13.exe`（`BUILD_EXIT=0`）＋換版＋3 個 `.lnk` 更新；8642/8765/8770/8771 正常、0 閃窗。**版本軌跡 0.4.11 → 0.4.12（predicate 寫錯，實測退化 1 次 vs 3 次）→ 0.4.13（`child.pid === undefined`，已驗證）**；反方 review 亦捉到 plan 敘事錯（07:47 係 SK 重啟部機、真窗口 47m43s、第三條 launch path）。plan `docs/plans/2026-09-16-hud-sidecar-spawn-failure-respawn.md`。**hud/main.js 未 commit**（等 SK 真機驗收）
- **Hermes watchdog v3 上線**：pre-flight（`Test-Interpreter`）＋ bounded 自癒（`uv python install <ver> --reinstall` **＋** `uv venv --allow-existing`，兩件 artifact 都要修）＋ interpreter 壞就**唔 call launch VBS**（唔會再彈 WSH 80070002）＋ login 路徑改經新 guard VBS ＋ 拉完核實 `/health` 才寫 `result: success|failed`（reporter v2 只對 success 講「已自動復活」）。cursor 實作 → 我獨立沙盒驗收**捉到 3 個真 bug**（PS 5.1 `Start-Process -ArgumentList @(...)` array 甩引號 → interpreter 永遠當壞；`-RedirectStandard*`+`.Trim()` 炸 `[Object[]]`；guard probe 同款 → 會永遠 SKIP 唔開 gateway）→ micro-fix 輪修好 → 沙盒 6 項全綠（含 0 閃窗；flash 偵測器有正控 3 次）＋ guard 兩向測試。真機 tick：PID 6764 不變、8642 200、events 無新增、0 flash、log 出 `ENSURE_GUARD`。備份 `.bak-20260916_093243`。plan `docs/plans/2026-09-16-hermes-gateway-watchdog-hardening.md`
- **真根因（要 SK 落手）**：Surfshark 防毒誤判 `Drop.Win64.UserProfileSelfRun.710`（09-14 13:52 隔離 `venv\Scripts\python.exe`）→ **未加 exclusion 之前仍有機會再刪**：`hermes-agent\venv`／`AppData\Local\Python`／`AppData\Roaming\uv\python`
- **零彈窗新法（SK 投訴過「why it keep popup」）**：`%TEMP%\run_hidden.vbs`（`wscript` → `sh.Run("cmd /c (...) > log", 0, True)`）＝整條鏈共用一個 hidden console，孫進程繼承 → cursor 派工／npm build／powershell 檢查 **0 閃窗**（已寫入 skill `cursor-cli-integration`）。HUD overlay 反覆彈出＝3 個 dev instance ＋多次重啟嘅正常副作用，唔係 bug。

## 今日完成（2026-09-16）

- Hermes gateway 停機恢復（07:41-07:57）：uv CPython 3.11 缺 `python.exe` 致 trampoline 失效（報 80070002）、crash loop；`uv python install 3.11 --reinstall` + `uv venv --allow-existing` 補回 trampoline，`hermes gateway start` 恢復，crash loop 停止；見 `code_change_log.md`。



## 2026-09-16 session（KubeJS 取得途徑線：停手 → 收窄）

- SK 問「can AI know how to craft this item?」（满溢神恩项链）→ 我報「3 條途徑」**錯**：`goety_ritual.js:1` 簽名 `GoetyRitualRecipe(craftType, ingredients, activation_item, output)` → 第 3 個 arg 係**祭品（消耗）**；真產出係 gateway pearl。`weapon_infusion.js:14` 同類。
- 真相：满溢項鍊唯一取得途徑＝**充能**（`server_scripts/curios/entity_death.js:21-27`：戴住「空」項鍊打死 4 王之一 → 變身）；空項鍊嚟自 `chestloot_2.json`（loot 索引已覆蓋）。AI 答「查唔到」係錯（路徑存在）。
- **一般化方案停手**（照 SK 3–4 輪規矩）：逐輪比分 R1 3:7／2:8、R2 5:5、R3 4:6／3:7 → 停手報告 `2026-09-15_kubejs-acquisition-path-facts-v3-stop.md`（含卡死點：map-key 來源側／方向過濾擋唔到 peer 洩漏／4 王名要 entity 名解析）。
- **研究（SK 指示 search online）**：JEI／EMI 需 per-mod plugin 才有自訂配方（本包 231 jar：47 個有 JEI plugin、**只有 2 個有 EMI plugin**）；JER 未裝；EMI Loot 已裝；**事件式轉換冇任何 viewer 覆蓋** → 只有腳本／tooltip。
- 工具落地：`tools/kubejs_mechanism_audit.py` ＋ `docs/kubejs-mechanism-coverage.{md,json}`（13 pack：863 原始 → **402 清洗後候選機制**、21 種自訂 recipe class、86 個事件家族）；`tools/kubejs_inventory_probe.py`。commit `e874d9f`／`9828a01`。
- 窄版 v4 → R1 **正方 2 : 反方 8**／**3 : 反方 7** → 拆 **plan α**（peer 行洩漏：真 trace 67 個 peer entry 有 **64 個垃圾**）＋**plan β（v4.1）**；commit `149e628`；R2 review 派咗（SK 關機中斷）。
- 更正我兩個錯：① 「唔需要改 answer layer」**錯**（新 edge 喺 `AskEngine:472-504` 冇 branch 會直接被丟）② 王名 zh_cn 係「暗夜巫妖」唔係「暗夜巫師」。
- B11 已 build＋部署（jar `97d279f7`）；115 check 全綠；我嘅負對照 2 個紅→綠。


## 2026-09-15 session（packai 主線）— Settings C 批／D 批／卡片線

- **C-0 落地**（`1b207174…`）：`renderScreen` 兩分支次序（正常＝自繪→widgets→tips 最後；fallback＝widgets→「畫面太細」→tips，plan 字面反而錯）＋ `mouseClicked` 先交 vanilla（`if (super.mouseClicked(...)) return true;`）＋ scroll 觸發 rebuild 時**保 draft**；新閘 `check_settings_render_order.py`（其後升級 allowlist＋自帶注入負對照）；其餘 3 個 screen 只加註釋（零行為）。
- **C-1 落地**（`ca6b2b36…`）：`llm.traceKeepDays`（預設 3、日清喺檔案數修剪**之前**）／`llm.askMaxToolRounds`（3、**欄位注入** `AskLoopState.maxLlmRounds`）／`llm.dailyTokenLimit`（`config/packai-usage.json`、`synchronized` 單一 writer、64 KiB 上限、缺失 usage 用估算入帳）；新檔 `logic/DailyTokenUsage.java`＋harness；新閘 `check_settings_c1.py`；負對照 2 個皆紅。
- **D 批落地**（`57e59a06…`）：**一行「模型」**＋picker 兩節（雲端／本機；`Target`＋`Row`、header 唔可揀、空節唔顯示、強制 fetch 兩個後端＋CAS pending）；**tag 單一來源** `PackAiConfig.effectiveModelTagKey()`（停用／本機／雲端／雲端・未設 key）；描述板 `Font.split` 3 行 wrap＋**Shift 全文**（1.19.2 `Screen.renderTooltip` 唔會斷行，必須先 split）；`DESC_DOCK_H 36→56`＋可見行數 ≥4 斷言；`boxX = r.x + labelW + 4`；`hiddenInUi`（保留 registry 令 reset／setters 閘唔爆）；新閘 `check_settings_model_picker.py`＋harness `ModelPickerRowsCheck`。
- **卡片線實錘**（SK 20:25–20:30 三次真機 ask，讀 `latest.log`＋trace）：`infinity_sword` 0 卡＝**正確**；`infinity_sword_organ` 4 卡＝3 正確＋1 張**tag 樣本顯示錯**（卡面 grid 兩個樣本都唔係焦點）；`tetra:modular_sword` 1 任務卡＋3 張**設計性抑制**（`toolParts path=strip`）。
- **三次診斷翻轉（全部有 file:line 否證）**：① 以為錯卡＝attribution 錯 → 否證（`recipes/common.js:171` 器官真係合法材料，focus 真喺 `#kubejs:organ`）② 以為改卡樣本可行 → 否證（`RecipeCard` 冇 ingredient provenance、格仔由 JEI drawable 畫）③ 以為正文講隱藏卡＝卡側問題 → 否證（嗰句嚟自 lang `packai.reply.tool_build` #23 提示詞）。
- **真 bug（反方搵到）**：`RecipeEmbed.placeEmissionCardsByRef:778-825` 插卡用**顯示清單 index**（唔係 refId）→ 顯示側一剷卡即**錯位**＝SK 講嘅「張冠李戴」→ **B11 為唯一修法**。
- **B11 落地**（jar `97d279f7` 已部署）：`AskToolEnv.offerEmission` 喺 refId 之前剷框架卡（純核心 `ModularFrameCards.shouldDropFrameCard` 同顯示側共用）、`AskLoopState` 新欄＋雙 bind＋兩處 auto-emit 跳過、全剷時工具明示「已隱藏」；115 check 全綠；我嘅負對照 ①拿掉過濾→紅 ②移到 refId 後→紅（`order pred=20 ref=19 add=23`）
- **B9／B10 落地**（log-only，jar `b288f80e…` 未部署）：`AskCardsDebug.visibleEmissionRefIds`（**剔唔重編**）＋ `render.cards.final.role` 統一 `promptRole()`；harness 加 2 條子斷言；負對照紅→綠、114 check 全綠。
- **B11**：plan §14 v2 過 review **正方 8 : 反方 2**（前置修：S2 次序、S1 範圍）→ **已派 cursor（跑緊）**。
- **我嘅失誤（已寫入 skill／plan）**：① 比分方向寫反（SK 兩次糾正 → 定「**正方 : 反方**」，正方寫前）② 誤報 tag 未實作（只 grep 中文字面，忽略 lang-key 間接）③ 卡 bug 三次錯判因果（上列）。

## 2026-09-15 session — alert enforce 驗收清單補送（cron FAILED）

- 09-15 03:45：一次性 cron `4695c33b8bdf`（alert-enforce 三情境驗收清單，09-13 排）**FAILED**＝`RuntimeError: Non-streaming API call timed out after 600s`，清單冇自動送。
- 09-15 05:2x：shadow 樣本已滿 48h（`shadow_heartbeat.jsonl` 最早 09-12 18:16，count 4018 行）；`--hours 48` 報告 decisions hold=7（全 gaming）／speak=0／digest=0／drop=0；gaming 落差 v1_true=312／v2_true=468／v1_only=11／v2_only=167。
- 09-15 05:2x：手動補出三情境驗收清單（打機→hold／通話→hold／idle→speak，各核 `shadow_ledger` decision）。SK 未開始驗收、未上 enforce；`alert_policy_mode` 仍＝`shadow`。
- SK 指示「check and update handoff first」（DeepSeek 模型唔穩定，隨時斷線）。零 config／code 改動、零 test alert、零 commit。

## 今日完成（2026-09-14）

- 09-14 02:2x–02:5x：packai jar `a4e689de` 部署＋真機 smoke 4/4；fix commits `8d25433`／`9f9baaf`（**未 push**）。
- 09-14 02:41：SK 要求「Tetra/Tinker 類模組化工具每次只答 1 件」→ plan **K3 `modularToolSingleItem`**（預設 ON）。
- 09-14 02:53：開 plan `docs/plans/2026-09-14-packai-reply-layout-plan.md`（`eadc008`）；SK 三張截圖列為驗收案例。
- 09-14 02:57／03:08：兩輪反方 review（read-only subagent）**R1 7:3、R2 7:3** → 依契約停手問 SK；hole 全吸收。
- 09-14 03:03–03:16：plan v2→v3（`75bdf86`／`94b3767`）；SK 提議經 JEI 拎 output → R5 改 `JeiRecipeCards.fromVanillaCrafting`。
- 09-14 03:46：SK 要「log 齊送出／檢查／模型回覆」→ S0 由 3 個 log 欄升級為**全鏈路審計 trace**（v4，`7ba52a7`）。
- 09-14 05:13：SK 定 trace 路徑＝`<instance>/packai/trace/`＋`index.jsonl`（似 KubeJS 自成一格）→ `7954e84`。
- 09-14 05:14：派 **Task S**（cursor-agent）實作 trace（零行為改動）；05:30 實況＝`AskTrace.java`×2＋`AskTraceCheck` 已寫、11 檔改動、報告 0 byte → **未 build／未驗**。
- 09-14 05:4x（cron 核實）：jarvis-pc tree clean／cron 9 個全 ok／8765 `/health` ok／`shadow` 模式；MC 前景 playing（全程零 GUI 動作）。
- 09-14 15:39：免費模型 upstage/solar-pro4:free 驗證 Through——HANDOFF agent 正常運作（Nous）。step-3.7-flash:free 曾 429 於 15:30/31。

## 逐日 index（一行一件；blocker 例外可 2 行）

- 2026-09-13 16:0x：T5 #2 輪 20 題 → `check_ask_display_leak` rc=0（4 條新答案零 `role=`／零 `PURPOSE`）＝T0 修復真機確認。
- 2026-09-13 16:2x：JEI 張冠李戴修好 — 根因 `JeiInfoFacts.sameItem():413` 只比 path 唔比 namespace；改全 id＋新 `shouldAttachForFocus`；Java check＋雙樹 md5＋4 條 python 全過。
- 2026-09-13 16:3x：Tetra 結構分流（`[TOOL_BUILD]` → 「怎麼來」）＋兩輪 review 修復；99 PASS／3 既有 stale FAIL、兩個 Java harness OK、build OK、雙樹對稱 OK。
- 2026-09-13 19:0x–20:0x：review 三輪（R1/R2/R3 全部 FIX-FIRST）→ 修 D1–J：多選組成／offline 三出口／措辭／token 統一／`role=` 廣義／footer 結構性渲染。
- 2026-09-14 02:2x：部署 `a4e689de`（MC 熄自動；舊 `551136fb` 備份落 `dist/_smoke_backups/`）；jar 開檔驗新 symbols＋3 語言 label keys 齊。
- 2026-09-14 02:3x：**真機 smoke 4/4 過**：組成喺「怎麼來」（唔喺「怎麼用」）、多選兩件都帶組成、4 條答案零 raw token、`toolCards emission=4 cardsOut=4`；`check_ask_display_leak` rc=0。
- 2026-09-14 02:5x：**已 commit（未 push）** `8d25433` fix(jei) 全 id 歸屬；`9f9baaf` fix(ask) 洩漏＋組成段位＋來源行標籤翻譯。


- 2026-09-13 15:0x：**T0 修復部署**（真實洩漏：答案【來源】行寫 `role=output／input`＋`PURPOSE`）——根因 `PLAYER_UNSAFE_MARKERS` 只過濾 FACT fallback、模型正文路徑冇剝；改 `AskReplyScrub.scrubInternalFieldEcho`＋`ReplySources` 髒 footer 換 canonical＋6 lang；我獨立 Java harness 實測真機字串通過；jar `551136fb` 部署（三邊 sha256 一致、舊 `450c3a76` 已備份）。
- 2026-09-13 15:0x：**Tetra 計劃** R1 4:6→R2 4:6→R3 6:4 未達 8:2 → 依契約停手報 SK；SK 揀 **a（結構性分流）**；已派 cursor 將 `[TOOL_BUILD]` 由 `AskService:449-452` prepend 抽出、改掛 `AskEngine:508-518` `sectionHowToGet` 之下（兩樹）。
- 2026-09-13 15:0x：**FTB 任務線 plan**（SK 要求新增）R1 3:7→R2 5:5／7:3→R3 7:3／8:2 **達標**；SK 決定 **HOLD**（只留 plan，將來做）。
- 2026-09-13 15:0x：**ASR（Fun-ASR-Nano）**：模型 08-07 已完整下載（2.0GB）；離線載入 15.2s、每條 0.6–1.2s、A/B 樣本唔夠判 → SK 決定**全線 hold 等新 mic**（同 wake／聲紋／AEC 一齊）。
- 2026-09-13 15:0x：契約更新 —— `AGENTS.md` 加「SK 叫→顯示／JARVIS 主動→`--minimized`」（第 115 行；主契約＋源頭 copy md5 `7230bf0b`）。

- 2026-09-13 13:3x–14:0x（Discord session，SK 逐項拍板）：T5 **jar 已 build＋部署**（`gradlew jar` 16s；新 `450c3a76`＝build/libs＝instance mods＝dist 三邊一致；舊 `17ebc474` 備份 `dist/_smoke_backups/packai-0.2.1+mc1.19.2-forge.jar.bak-20260913_133727`）
- 2026-09-13 14:0x：`check_jar_contains_fix.py` **OK**（T2 fail-closed symbols＋lang keys）＋K30–K34 harness **綠**（`AskToolLoopCheck`／`AskReplyScrubCheck OK`）
- 2026-09-13 14:0x：修 **pre-existing 過時 assert**（`"output"`→`"OUTPUT"`；兩樹 md5 `e18f6747`；baseline worktree `7317763` 證實執之前已壞）＋ cursor read-only 一致性分析 **VERDICT SHIP／零 FINDING**（**未 commit**，等 SK）
- 2026-09-13 14:0x：全量 python checks **101 檔 / 4 FAIL**＝baseline 3（worktree 對照證實）＋`check_ask_display_leak.py`（等真機 log）
- 2026-09-13 13:4x：`AGENTS.md` 加新條款（第 115 行）「**SK 叫→顯示；JARVIS 主動→`bg_launch.py --minimized`**」；主契約＋源頭 copy md5 `7230bf0b`；備份 `.bak-20260913-133850`
- 2026-09-13 13:4x：**兩 repo 已 push**（jarvis-pc `14b2cc3`／packai `4886346`，ahead=0）；一次性 cron `4695c33b8bdf`（09-15 03:15 alert enforce 驗收清單）
- 2026-09-13 13:4x：SK 定「**滑鼠有動＝打機**」（已入 memory；alert gaming 判定用）
- 2026-09-13 14:0x：ASR 計劃 `docs/plans/2026-09-13-asr-fun-asr-nano-plan.md`（`ear.py` 早有 `transcribe_fun_asr`）；**Fun-ASR-Nano 08-07 已完整下載**（ModelScope 2.0GB）→ T1 取消
- 2026-09-13 14:1x：ASR 離線實測（CPU）：載入 **15.2s**、每 2s clip **0.6–1.2s**（無 08-07「似凍」）；A/B 用 5 條 wake 碎片兩邊都垃圾 → 唔可判高低
- 2026-09-13 14:2x：**ASR T2 錄音 HOLD**（SK 明示：等新 mic 先做，同 wake／聲紋／AEC 一齊排）；packai test fix 已 commit `f0ac745`（未 push）

## 2026-09-13 12:4x — 契約規則 ×2、Chrome 零搶焦點實測、packai DSML 修復（P1/P2/P5）

**SK 今日新增嘅契約規則（已寫入 `C:\Users\skps9\AGENTS.md` ＋源頭 copy，md5 一致；兩次改動都先備份 `.bak-<ts>`）**：
1. **第一規則**（置頂）：做事前 → 風險評估 → 最壞情況 → 確認可用現有資源／工具還原（**資料零損失、指名 backup**）→ 才動手；還原唔到／有損失風險唔准做；重大決策先得 SK 批准。
2. **Plan／Idea Review 上限 3–4 輪**：到第 3–4 輪仍未達 8:2 → **停手、問 SK**（報告要齊：逐輪比分／卡死決定／最貴未知／建議）；每輪之間必須有實質修改。

**Chrome 代開（1c 定案）**：
- 實測 6 種開法（`bg_launch_focus_probe.py`，數字喺 `state\bg_launch_focus_probe.json`）：**只有「最小化開」零搶焦點**；任何「顯示出嚟」Chrome 都會自己 `SetForegroundWindow`（`LockSetForegroundWindow` 由背景 process 叫係無效，實測 return False）。
- 已改 `bg_launch.py` 加 `--minimized`（`SW_SHOWMINNOACTIVE`＋移窗唔用 `SWP_SHOWWINDOW`），默認行為不變；改前備份 `bg_launch.py.bak-20260913-105323`。**SK 定：佢叫 → 顯示；JARVIS 主動 → 最小化**（AGENTS.md 條款待 SK go 才更新）。
- 教訓已寫入 skill `windows-app-launch-focus`。

**packai DSML 修復（見該 repo `.hermes\plans\HANDOFF.md` 同 `docs\plans\`）**：plan v1→v3 經 R1（反方 7:3）／R2（正方 8:2）兩輪 review；T6（P1 有界 grammar／P2 canonical args＋跨路徑去重／P5 真 bytes 驗收）完成並由 Hermes 親驗（偵測 false→true、解析 0→2、主路徑唔再吐垃圾、病態效能 4134ms→25.5ms、全量 96 PASS／5 FAIL＝baseline、雙樹對稱）。commits：`db245f5`（T1–T4）、`e85c4a5`（P1/P2/P5）。
**未做**：`AskToolLoopCheck` K30–K34 未跑（要 gradle classpath）、mod 全量 compile、**T5 真機煙測（要 SK 熄 MC）**；hop-limit 出口仍漏（P3 等 T5 數據）。

**其他**：`docs/plans/` 現有兩份新報告（DSML 業界研究、fork vs 輕量評估）；PR #12 merge 早已完成（`96be515`）。

**下次（優先序）**：
1. **T5 真機煙測**（SK 熄 MC → build jar → 備份舊 jar → 部署 → 15 題 → 跑真 log 檢查＋`check_jar_contains_fix.py`＋gradle 跑 `AskToolLoopCheck`）→ 出報告。
2. 用 T5 數據決定 **P3**（hop-limit 出口 recovery）。
3. AGENTS.md 加「主動開 → `--minimized`」條款（等 SK go）。
4. 待 SK 決定：真機驗收清單（alert enforce）、AI_Studio Phase 1（4b 排後）、A/B/C 架構（5a 已解釋）。

# HANDOFF — JARVIS 交接（固定檔）

> **呢個係固定 handoff 檔**（2026-08-30 起）：每次 session 結束**更新呢份**，唔好開新日期檔；舊交接版本移入 `plans/archive/`。
>
> **排序規則（2026-09-10 起）**：新 session 一律**加喺最頂**（時間倒序）；唔好 append 落尾。更新完先 commit（`docs(handoff): ...`，唔 push）。
>
> 下次 session 起點：**JARVIS ONE 0.4.10 跑緊；`1bdac68`（alerts ctypes fix）已 push 且 09-10 23:4x 重啟 sidecar 後已生效（ctypes flood 清零、serve.log 已 truncate）；**jarvis-pc：feature 分支 `feature/hermes-alerts-mcp` 已 push ＋ 開咗 PR #12（<https://github.com/skps00/jarvis-pc/pull/12>，base `main`＝`ca463a3`，**未 merge**；2026-09-13 03:3x `git rev-list --count origin/main..HEAD` = **87**，**09-13 05:4x cron 再測 ＝ 89**（再加 `e55f1ea`／`ed4d3cf` 兩個 docs commit，已 push 上 feature 分支）實測——包含 08-10 之後所有未推工作，唔止 alert pipeline）；**MC 線 09-11 早：Arch-3/3a `1ba048f` 已 push ✅（真機驗收 PASS）；DSML scrub fix 已改／已驗／review SHIP 但**未 commit**；新 jar `012da9cc` 已 deploy（09-12 01:59 SK 真機跑：**DSML fix 生效 ✅**，但兜底路徑漏內部 FACT——見最頂 09-12 section）；OpenClaw/Hermes 架構比較已寫入 → 建議 A/B/C 未拍板**；09-11 凌晨診斷過 GPU driver TDR（SK 決定唔郁）**。讀呢份之前先讀：
> 1. `jarvis-pc\AGENTS.md`（專案 context——**自動載入規則已寫入主契約，唔使 SK 叫**）
> 2. `C:\Users\skps9\AGENTS.md`（主契約——Code Review 兩次規則已升格入契約）
> 3. `REMAINING_WORK.md` + `2026-08-29_self-evol.md`（計畫書，R1-R20b 齊全）

---

- **2026-09-13 13:0x（HANDOFF 重排，SK 批准）**：新增頂部狀態區塊（五元素）＋逐日 index 規則；搬 ≤09-11 sections 入 `archive/HANDOFF-2026-09.md`；「剩低」併入 `REMAINING_WORK.md`；改 `AGENTS.md`（新 section 加喺狀態區塊之下／只讀狀態區塊＋近 3 日／HANDOFF 可公開）＋修 cron `git add -A`

- **2026-09-13 13:0x**：停用 cron `jarvis-bglaunch-idle-test`（每 5 分鐘；6 種開法已測完，SK 指示 stop，**paused** 可 resume）；另：手誤刪過 sections（`86efdd9`）→ 已由 `4fdd92f` 還原
- **2026-09-13 13:2x（session 收尾 hand off）**：cron `jarvis-bglaunch-idle-test` 停用（paused）；HANDOFF 手誤刪事件 → 已還原（`766788b`）；DSML 修復全部落地，**只欠 T5 真機煙測**（等 SK 熄 MC）；packai/jarvis 兩 repo tree clean、未 push
## 2026-09-13 09:1x（Discord session，SK 1A/2A/3C）— Chrome 代開工具上線、PR #12 merged、packai DSML plan v3

### ① JARVIS「代開 app」上線（SK 2026-09-13 明確要求 + AGENTS.md 例外條款已批准寫入）
- 診斷：唔係 code bug —— HUD `hands.py:_launch_chrome_restore` 一直正常；係 **Hermes 語音線**因為 `sk_activity.json` = `playing` 而拒絕（75 個 session 都係咁）。→ 修「規則 + 工具」，唔改 HUD。
- 新工具（Hermes 側，agent 可直接用）：
  - `%LOCALAPPDATA%\hermes\scripts\bg_launch.py` —— no-activate 開 app（`SW_SHOWNOACTIVATE`）；開完自讀 `GetForegroundWindow()` 驗、搶到即用 `AttachThreadInput` 還原；`--monitor` 預設 **secondary**（SK：真要開就開喺第二副螢幕），移窗後**第二次獨立量度**（`GetWindowRect` 中心要落喺目標螢幕）→ `monitor_verified`；`--check` 純讀取（打機中都安全）。exit 0/3/1。
  - 3 個安全修正（cursor 原稿有洞，我改＋自己驗）：`restore_foreground` 唔再用 `SW_RESTORE`（會將全螢幕遊戲拉出全螢幕）→ 只 `IsIconic` 時 restore；`move_noactivate` un-maximize 改 `SW_SHOWNOACTIVATE`（唔 activate）；冇副螢幕時 `monitor_verified=null`（唔假報 true）。另 ctypes `IsIconic` 要 bind `argtypes`。
  - `bg_launch_idle_test.py` + cron `jarvis-bglaunch-idle-test`（`*/5 * * * *`，`no_agent`，deliver origin）—— idle ≥120s 且冇 `fullscreen:true` game 才自動試一次（成功即停、失敗最多 3 次）；非 idle **完全零輸出**（已實測：CS2 fullscreen 期間 tick → 空輸出 rc=0）。
- 規則：`C:\Users\skps9\AGENTS.md` §活動 Gate 加「例外」段（SK 明確要求開 app → no-activate 允許；切換／搶焦點仍要同意；fullscreen 遊戲唔准開窗；開完要實報有無搶焦點）＋源頭 copy `Code_Project\Hermes\AGENTS.md` 同步（md5 一致）。
- skill `windows-app-launch-focus`：核對過已載入 2026-09-13 refinement（含上述 3 個修正、idle watchdog 模式、75-refusal 教訓、layer 診斷）→ 無需重複寫。
- **狀態**：未做真機 launch（CS2 全螢幕中被 gate 擋）—— 等自動 idle 測試結果。

### ② Alert pipeline 線收尾（已完成）
- **PR #12 已 merge 落 main**（**merge commit** `96be515`，唔係 squash —— squash 正是今次 21 檔衝突嘅根源；PR #11（2026-08-10）就係 squash）。merge 前審查：cursor 自報 PARTIAL（冇真跑 diff）→ 我自寫 `audit_main_only.py` 逐檔核（24 檔只有 4 個名要人手判，全部舊版／改名）→ **(c) 真嘢被掉 = NONE**。
- 新 skill `long-lived-branch-merge`（含可執行 `scripts/audit_main_only.py`；實測對 `ca463a3` 重現 4 名、merge 後回 0）。
- merge 後：`pytest tests/ -q` **532 passed**、`eval_gate --lock` 一致（53 files）、`--all` 三 suite ok、HASH `3e5e074479192100`；live `voice_status.json` md5 不變（conftest APPDATA 隔離生效，`cfcb2de`）。

### ③ packai：玩家見到「寫畀模型嘅字」——實錘 + plan v3（**未開工**）
- 實錘（真機 `latest.log` 562/564-605，cp950 逐行解）：第 4 輪 `raw reply chars=604 toolCalls=0 body=<｜DSML｜calls>…`（prompt 叫 call 一個冇提供嘅工具）→ `proseOrFacts` 貼整份 facts → 玩家見到 `[RECIPE_CARDS] …`／`注意：JEI 可能混入同 id…`／`【JEI】…勿宣稱無法合成`／`role=quest …`。
- plan：`super_minecraft_AI_player\.hermes\plans\2026-09-13_120000-dsml-fact-leak-player-safe.md`（v1→v3；R1 反方 7:3、R2 反方 8:2；R3 有界 flip-check 跑緊）。
- 已知：`askNativeTools="auto"`；cursor 診斷 log 已 commit `d849da0`；評估報告 `2026-09-13-agent-architecture-fork-vs-light.md`（結論：唔 fork Hermes，走輕量硬化 + sidecar）。

### 下次做咩（優先序）
1. 等 R3 結果：達 8:2（計劃）→ 按 plan v3 開工（T0 baseline → T1 prompt → T2 顯示層 → T3 覆蓋 → T4 收貨工具 → T5 真機 15 問）。
2. Chrome idle 測試結果一到 → 若 pass 即正式當 JARVIS 代開工具用；若 fail（focus stolen 還原唔到）→ 修完再試。
3. 真機驗收（打機／通話／idle）→ alert pipeline 上 `enforce`；shadow 48h 樣本 **09-15 03:06** 齊。

---

## 2026-09-13 08:3x（同一 Discord session，續）—— **PR #12 已 review 過並 merge 落 main**；新 skill；MC「showing prompts」實錘

**1. PR #12 pre-merge review（SK 指示「review it before merge + 查業界做法 + 最好做成 skill」）**
- **業界查證（有 source）**：長跑分支**絕對唔可以 squash-merge** —— GitHub community #23249、StackOverflow 79825357（"never … EVER squash-merge long-running branches … unless you like going through conflict-hell"）、GitLab merge-method docs。**PR #11（8-10）就係用 squash 落 main → 正是今次 21 檔衝突根源**；正確做法 = merge commit。
- **Review 做法**：cursor read-only（自報 PARTIAL＝shell 被拒，佢冇真跑過 diff）→ 我**自己寫驗證 script** 逐檔比對「main 有、HEAD 冇」嘅 `def/class/key` 名。全 24 隻 main-only 檔只有 **4 個名**要人手判：`_win_subprocess_text_kwargs`（main 用 tasklist＋mbcs decode；HEAD 已改用 Toolhelp，caller 消失＝過時）、`_has_cjk`（HEAD 改名 `has_cjk` 公開＋alias）、`pyw`（JARVIS.vbs 舊 var；HEAD 故意用 python.exe，因 pythonw 會令 alerts MCP 靜默死 8765）、`test_settings_window_builds_four_tabs`（HEAD 已演進成 `five_tabs`）→ **(c) GENUINELY-LOST = NONE**（另 `git diff --name-status HEAD origin/main | grep ^A` 空＝分支檔案集係超集）。
- **Merge**：`gh pr merge 12 --merge`（**merge commit，唔 squash**）→ **PR #12 MERGED，commit `96be515`**（2026-09-13T00:31:38Z）。驗證：`git diff --stat origin/main HEAD` **空**（main == 我哋跑緊嘅樹）；`HEAD..origin/main` = 1（就係 merge commit）；`origin/main` 由 `ca463a3` → `96be515`。
- **新 skill**：`long-lived-branch-merge`（software-development）＋可執行 script `scripts/audit_main_only.py`（實測：對 `ca463a3` 重現 4 個名、merge 後回 0）。

**2. MC（packai）「showing prompts」實錘 —— 唔使 SK 再描述**
- 部署 jar：`packai-0.2.1+mc1.19.2-forge.jar`（09-12 07:07）**已含** raw-reply 診斷 log；真機 log = `Documents/PrismLauncher-…/instances/AI_test_NFWC_DIM/minecraft/logs/latest.log`（**cp950 編碼**）。
- SK 嗰次（07:50:52→07:51:03，問「猛者瓶怎麼用」）原文：
  - 3 輪 `LLM raw reply chars=0 toolCalls=4`（正常用 native tool call）
  - 第 4 輪 `LLM raw reply chars=604 toolCalls=0 body=<｜DSML｜calls>…<｜DSML｜invoke name="render_recipe_cards">…` → **模型把 DSML 標記當普通文字掟出嚟**
  - 之後 `ask reply before ensureCards: 怎么用`、`toolCards emission=3 cardsOut=3`
- 即係玩家睇到嘅「prompt 樣」文字 = `<｜DSML｜calls>` 洩漏；**同 09-11／09-12 兩次 DSML 修復同類，第 3 次** → 按 SK 規則（重複 2-3 次）**應開 read-only root-cause 討論，唔好再直接 patch**（等 SK 揀）。

**3. Chrome 代開（SK 2026-09-13「1 u open it」）**
- 查清：**唔係 code bug**。jarvis `hands.py:_launch_chrome_restore` 正常；75 個語音 session（例 `jarvis-fb35e32b`）全部係因為 `sk_activity.json` state=**playing** 而**拒絕代開**、只教 SK Alt+Tab。
- 方案：**(甲)** 背景開法（`SW_SHOWNOACTIVATE`）＋開完自驗前景有冇變；**(乙)** 規則要改成「SK 明確要求開 app → no-activate 背景開＝允許；搶焦點仍要 SK 同意」（AGENTS.md 屬受保護檔，要 SK 明確 go 才改）。
- **未做**：SK 當時已入 **CS2 獨佔全螢幕**（`fullscreen: true`）→ 任何窗口動作都可能令遊戲縮細／黑閃，**已停手唔試**，等 SK 揀測試時機。

**4. 其他（同一 session 早段）**：`tests/conftest.py` 隔離 `APPDATA`（`cfcb2de`，已驗證 live `voice_status.json` 唔再被測試污染）；merge 衝突 21 檔全 `--ours` 並證內容零改動（`5cdafbd`）；docs `9e3a5b4`／`33f9d6f`／`fedb768` 已 push。全量 `pytest` 532 passed、`eval_gate --all` 三 suite ok、HASH `3e5e074479192100`。

---

## 2026-09-13 08:0x（Discord session；SK 問「all set? / is that all?」）—— 測試污染修好、**PR #12 衝突已解（MERGEABLE）**、docs 收尾

**1. 做咗咩（全部本輪實證，唔靠記憶）**
- **① `pytest` 污染 live `voice_status.json` 已修**（commit `cfcb2de`）：新增 `tests/conftest.py`——session-scoped autouse fixture 將 `APPDATA` 指去 tmp 沙盒。經 cursor-agent 派工（hidden dispatch、零彈窗；report 自報 PARTIAL=shell 被拒，驗證全部我自己跑）。
  - 收貨證據：`py_compile`＋AST OK；`pytest tests/test_alert_piper_gate.py -q` = **3 passed**；**live `voice_status.json` md5 `4e1831b0…`／mtime 07:33 完全不變**；而沙盒 `%TEMP%\pytest-of-skps9\pytest-*\appdata0\Jarvis\voice_status.json` 確實出現 test 寫嘅 `wake_on:false` 檔 → **證明 test 真係有寫、只係寫入沙盒**（唔係「test 冇寫所以無污染」）。
- **② PR #12 21 個衝突已解 → `mergeable: MERGEABLE`**（merge commit `5cdafbd`，已 push；`origin/main..HEAD` = **93**、`HEAD..origin/main` = **0**）。
  - 做法：`git merge --no-commit --no-ff origin/main` → 逐個衝突 `checkout --ours` → **關鍵不變量檢查 `git diff --cached HEAD` 完全空**（＝merge 對內容零影響，只補拓撲連線）→ commit。
  - **main 完全冇郁**（一個 commit 都冇加）。
- **③ 收尾 docs**：cron 嘅 `9e3a5b4` 已 push；`.hermes/plans/self-evol-SUGGESTIONS.md` 3 行已 commit（`33f9d6f`）。
- **④ merge 後重跑驗收**：`pytest tests/ -q` = **532 passed / 0 failed**；`eval_gate --lock` 一致（53 test files）；`eval_gate --all` 三 suite `ok=True`；HASH **`3e5e074479192100`**；**全量 suite 跑完後 live `voice_status.json` 仍然 `wake_on:true`、md5 不變**（＝污染 fix 大規模驗證通過）。

**2. 而家喺邊（2026-09-13 08:1x）**
- working tree 乾淨；feature 分支 = remote（`5cdafbd`）；**PR #12 OPEN ＋ MERGEABLE（未 merge，等 SK）**。
- Shadow 仍在收（heartbeat 07:51；`settings.json alert_policy_mode="shadow"`）；48h 樣本要 **2026-09-15 03:06** 才夠。
- 真機驗收（打機／通話／idle）**未做**；`enforce` 未上。

**3. 下次做咩（優先序）**
1. **真機驗收** → 過關才上 `enforce`（SK 未定：收機後做 vs 等齊 48h 一次過）。
2. **PR #12 merge 落 main**（技術上已無阻，等 SK 一句 go）。
3. Task 10（LLM digest 潤飾）＝要先跑 ranking prompt benchmark（p95 ≤3s）。
4. 未答嘅觀察：75 個語音 session「開啟 Chrome 瀏覽器」；Chrome 一個 kill 唔到嘅 stuck GPU process（父 process 已死，可能同 TDR 條線有關）。

---

## 2026-09-13 05:4x（jarvis-session-handoff cron 核實）—— 窗口內工作已全部入檔；補記 cron 00:51 捉到嘅 **test 污染 live `voice_status.json`**（仍未修）＋ 實況／數字更正

> 窗口 = 2026-09-12 06:00 → 09-13 05:45。逐個 session 對（`state.db` 實查，唔靠記憶）：`20260912_061810_9678a999`（discord 06:18–21:0x，294 msgs ＝ 09-12 alert pipeline 全程）／`20260912_233912_482dc384`（discord 23:39–03:39，142 msgs ＝ 已對應最頂 09-13 section）／`cron_7b4af62c87c3_20260912_061713`（09-12 handoff cron）／`cron_6a98a79be95f_20260913_005101` ＋ `_030807`（sidecar-health）／13 個 subagent（plan review ×10、alert pipeline review ×3）／76 個 `jarvis-*` api_server 語音 session（其中 **75 個**標題＝「開啟 Chrome 瀏覽器」）。**除下面第 1 項，其餘已有對應 section。**

**1. 🆕 未入檔、仍未修：`pytest tests/` 會蓋掉 live `voice_status.json`**

| 項 | 實錘 |
|---|---|
| 來源 | `cron_6a98a79be95f_20260913_005101`（00:51 sidecar-health 報 fingerprint 變動）——查實**唔係 sidecar DOWN**，係 live 狀態檔被寫花 |
| 機制 | `tests/test_alert_piper_gate.py`（`be099a7` 新加）→ `_mini_shell()` → `shell._handle_alert()` → `shell_app._write_voice_status()`（`shell_app.py:1071` ＝ `os.environ["APPDATA"]/Jarvis/voice_status.json`）；test 冇 monkeypatch APPDATA，`tests/` 亦冇 `conftest.py` → **直接寫真檔**（`wake_on:false`、`status:"ready"`） |
| 我今日 safe 重現（05:46） | `APPDATA=<temp>` ＋ `pytest tests/test_alert_piper_gate.py -q` → **3 passed**，temp 目錄即刻出現 `voice_status.json` ＝ `{"wake_on": false, …, "status": "ready"}`；真檔 mtime／內容不變（今次有隔離）→ 機制確認 |
| 後果 | 每次跑 `pytest tests/` → HUD／MCP 顯示「聽候＝關」，直到 sidecar 下次寫入；sidecar-health cron 亦會誤報 fingerprint 變動（00:51 就係咁） |
| 現狀 | **未修**（`git log` 未見隔離 fix、`tests/conftest.py` 不存在）。建議（00:51 cron 原提，SK 未答）：加 `tests/conftest.py` autouse fixture 隔離 APPDATA（一行級） |

**2. 實況核對（05:4x 親查——舊 section 嘅 claims 全部成立）**
- sidecar `python.exe` pid **38860** LISTEN 8765（同 03:06 restart 記錄一致）；`settings.json` `alert_policy_mode="shadow"` ✓
- shadow 仍在收：`shadow_heartbeat.jsonl` 最後一行 **05:45:56**、`shadow_ledger.jsonl` 11 行。快照（`scripts/alert_shadow_report.py --hours 3 --json`）：`decisions speak=0 hold=1 digest=0 drop=0`、`reasons gaming=1`、`kinds self-monitor=1`、heartbeat 214 行、`gaming_v1_true=160 / v2_true=35 / v1_only=141 / **v2_only=16**`（03:2x 首批係 `18/5/13/0`）→ **`v2_only` 由 0 變 16**，即新 detector 亦有「v2 話打機、v1 唔話」情況，睇 48h 分佈時要一齊睇
- PR #12：`origin/main..HEAD` ＝ **89 commit**（03:3x 記錄 87，加咗 `e55f1ea`／`ed4d3cf` 兩個 docs commit，已 push 上 feature 分支）→ 檔頭數字已更正
- 語音：`serve.log` 自 truncate 至今共 10 條 `[ear] raw=`，窗口內最後一條 ＝ 09-12 08:50（已入 09-12 section）；窗口內**無新 garble 個案**

**3. 觀察（非工作，等 SK 一句）**：窗口內 **75 個**語音 session 標題都係「開啟 Chrome 瀏覽器」（09-12 13:0x／16:0x／17:0x×23／18:0x／23:0x、09-13 00:0x×14／01:0x×12），每個 session JARVIS 都因前景＝遊戲／使用中而**只教 SK 自己開、冇代開**。按 SK「同一問題重複 2–3 次就查根因」規則：係唔係想 JARVIS 背景代開（唔搶焦點）？定係 gating 太緊？

**4. 未 commit／等 SK（不變）**：`.hermes/plans/self-evol-SUGGESTIONS.md` 3 行仍未 commit（等 SK；本 cron 冇 touch）；真機驗收 ＝ 下次 session（4b）；Task 10 等 ranking benchmark；語音 ASR ＝ d（唔理住）；PR #12 merge 與否等 SK。

## 2026-09-13 00:0x–03:3x（Discord session）—— Alert pipeline 收尾：Task 7 收貨、**三輪獨立 review**、fix1–fix11 全部收貨、code 已 commit（`be099a7`）＋ PR #12、shadow 已生效收樣本

**1. 做咗咩（全部有實測證據）**
- Task 7（「what did I miss」）由 cursor 交付 → Hermes 自己收貨（py_compile／targeted／全量／`--lock`／`--all`／26 項 probe）。
- **三輪獨立 review**：① cursor read-only 12-area（NEEDS-FIX）② subagent 品質 review（2 HIGH＋8 MEDIUM＋8 條 spec 偏離）→ 全部 findings 我逐個自己核實（read code／probe），再派 **fix1–fix11** 修到清（fix10 修 release 收斂失效／spoken ledger 缺失／digest 句安全／clear_digest；fix11 修一個用假時間嘅 test）。
- 期間我自己 probe 捉到 review 冇捉到嘅嘢：Task 7 句子**報大數**（ledger 事件行 ≠ 未答 alert）；**fix8 引入嘅 HIGH regression**：`gpu_hard` producer 傳空 phrase → `enqueue()` raise `ValueError` → **hard GPU critical alert 靜默消失**（fix9 修，並加 2 個防守 test）。
- **最終驗收（親跑，2026-09-13 01:2x）**：`pytest tests/ -q` = **532 passed / 0 failed**；`eval_gate --lock` = 一致（**53** files）；`eval_gate --all` = 三 suite ok；HASH `3e5e074479192100`；自寫 probe（fix6 9 項、fix7 9 項）全 PASS。
- docs 已更新：`docs/hermes_alerts_mcp.md`（新增「2026-09-13 修復輪」表 ＋ 新 baseline；`alert_llm_*` 標明未接線）；plan 尾加「2026-09-13 收貨記錄」＋ 8 條規格偏離；`AGENTS.md` 坑 section 已有 alert pipeline 一句（commit `8cff405`）——**舊稿寫「AGENTS.md 做唔到」係過時，已更正**。

**1b. Runtime 動作（SK 2026-09-13 03:0x「1a」批准，已執行並驗證）**
- **Restart sidecar**：kill 舊 `python -m jarvis serve`（pid 39420）→ Electron 自動 respawn。新 process：sidecar `python.exe` pid **38860**（03:06:06 起，LISTEN 8765）、poll loop `pythonw.exe` pid **45964**（03:06:09 起）→ **兩個都係新 code**。
- **開 shadow**：`POST /settings {"alert_policy_mode":"shadow"}` → 回 `200 {"ok":true,"keys":["alert_policy_mode"]}`；`GET /settings` 同 `settings.json` 都確認 `alert_policy_mode = "shadow"`（其餘新 key 走 code default：`alert_gaming=hold`、`hold_ttl=900`、`held_cap=64`、`digest_interval=1800`、`digest_ttl=86400`、`dedupe_window=300`、`llm_polish=off`、`llm_timeout=3.0`）。
- **Shadow 已開始收樣本**：`alerts/shadow_heartbeat.jsonl` 03:06:23 寫入，`mode:"shadow"`；`shadow_ledger.jsonl` 會隨每次決策 append。第一個心跳已經有價值訊號：`game_process=true, fg_is_game=true, state=playing, idle_seconds=2370` → **`v1_gaming=true` 但 `is_gaming_v2=false`**（AFK／menu）＝正是 P1 要量嘅 v1 vs v2 落差。
- 睇樣本：`python scripts/alert_shadow_report.py`（read-only，`--json` 出 JSON）。

**1c. 收工動作（SK 2026-09-13 03:2x「23go / hand off first」）**
- ✅ **Code commit**：`be099a7 feat(alerts): alert pipeline v5.1 — deterministic policy, single speaker, ledger`（21 modified ＋ 25 新檔，正式 changelog message）。
- ✅ **清殘留**：`7d19ccf chore:`——3 個 tracked 暫存檔（`_apply_and_compile.bat`／`_compile_check2.py`／`_tmp_test_write.txt`）已刪；2 個 untracked folder（`_staging/`、`nonexistent/`）搬去 `%TEMP%\jarvis_pc_debris_backup_20260913\`（可還原）。`self-evol-golden-set.md` 同步 commit。
- ✅ **Push ＋ PR（SK 選 2a：開 PR、唔動 main）**：`git push origin feature/hermes-alerts-mcp`（`8e97a9b..7d19ccf`）→ **PR #12** <https://github.com/skps00/jarvis-pc/pull/12>（base `main` ← head `feature/hermes-alerts-mcp`，**未 merge**）。⚠️ PR 相對 `origin/main` 有 **87 commit／189 檔**（含 08-10 之後所有未推工作），PR body 已註明重點範圍。
- ✅ **Cron**：`jarvis-alert-shadow-report`（job `3dbaff9ace81`）——每 6 小時（`0 */6 * * *`，下次 06:00），`no_agent` 跑 `~/AppData/Local/hermes/scripts/jarvis_shadow_report.py` → 印 shadow 摘要（decisions／reasons／v1-vs-v2 落差），**窗口內冇任何 decision 就完全唔出聲**（watchdog 式）。
- ✅ **Decision 記錄**：真機驗收 = **4b（下次 session）**；語音 ASR 線 = **d（唔理住）**。

**1d. Shadow 首批數據（03:2x，`alert_shadow_report.py --hours 6`）**
`decisions: hold=1, speak=0, digest=0, drop=0`｜`reasons: gaming=1`｜`heartbeat lines=18, game_active_hours=0.06`｜**`gaming_v1_true=18 / v2_true=5 / v1_only=13 / v2_only=0`** → 現行前景制 gate 有 **13 次**把「game 開住但冇輸入」當成打機（FP），新 process+輸入制 0 次漏判——正正係 M3 要量嘅數字（未達 48h 樣本，未可定論）。

**1e. 第三輪獨立 review（subagent，2026-09-13 01:2x）—— verdict：CONDITIONAL PASS**
- 14 項核實：**10 CONFIRMED、3 PARTIAL、1 REFUTED**；另報 2 HIGH＋5 MEDIUM＋4 LOW。
- **唯一 REFUTED**：fix7 嘅「release 收斂」實作**無效**——`quiet_since` 喺 release 後冇 reset，每個 tick 再放一條 normal，最終全部放出（洗版原封不動）。
- **第 2 個 HIGH（新捉）**：`mode=off`／shadow（claim=False 路徑）出聲成功**冇寫任何 `spoken` ledger** → 「what did I miss」把真正講過嘅 alert 報成未答（fix1 去重判定形同虛設）。
- **MEDIUM 之中我實錘 4 個**：digest 句含 4+ 位數字（`extra:app1234`）→ `is_speakable=False` 且冇 fallback → 永遠講唔出＋每秒刷 log；`clear_digest` 永遠清唔到（先 `mark_spoken` 已非 `digest` state）＝死碼＋有機會刪未出聲行；`jarvis_speak` 用弱 validator（`guard_for_speech`）做 pre-check 但 mouth 用 strict → 回 `ok:true` 冇聲；`release_held` 空轉都重寫全檔。
- **收貨證據（Hermes 自己 probe，fix10 前後對照）**：D1 release `[3,1,1,1,1]`（洗版）→ fix10 後 `[3,0,0,0,0]` ✅；D2 ledger `["enqueue"]` → `["enqueue","spoken"]`（`Sir, nothing missed.`）✅；D3 `is_speakable=False` → `True`（label 去數字）✅；D4 `clear_digest` 回 0 → 回 1 ✅。test blind spot 全部補：release 連續 call N 次、spoken ledger 兩條路徑、digest fallback、clear_digest。
- **fix11（test-only）**：`test_digest_cap_drops_oldest` 用假 epoch（`t0=1_700_000_000`）令行被 wall-clock GC 當過期 → 期望 4 條得 1 條；我用真時間 probe 同情境 = 4 條（cap 正確）→ 判 test 錯，**只改 test，唔准遷就 production code**。

**2. 而家喺邊（2026-09-13 03:3x 更新——以下為當下事實）**
- ✅ **Code 已 commit**：`be099a7 feat(alerts): alert pipeline v5.1`（21 modified ＋ 25 新檔；`git status` 只剩 `.hermes/plans/self-evol-SUGGESTIONS.md` 未批）。
- ✅ **Pipeline 已生效（shadow）**：sidecar pid 38860 ＋ poll loop 45964（03:06 起，跑新 code）；`settings.json` 有 `alert_policy_mode="shadow"`。
- ⏳ **Shadow 樣本收集中**（03:06 開始；P1 通關條件：M1 打機時 GPU soft ≤2/hr、M3 Prism 開住唔玩 FP <5%）；每 6 小時 cron 自動報告。
- ⏳ **真機驗收未做**（SK 選 4b＝下次 session；打機／通話／idle 三情境，過關才 `enforce`）。
- ⏳ Task 10（LLM digest 潤飾）暫緩（要先 benchmark ranking prompt p95 ≤3s）。
- ⏳ **PR #12 未 merge**（等 SK 決定；PR 相對 `origin/main` 87 commit／189 檔）。
- ⏳ 未了：`self-evol-SUGGESTIONS.md` 3 行、MC 兜底 FACT 測試（等 SK 關 game）、語音 ASR（SK 選 d 唔理住）、AI_Studio Phase 1 spike。

**3. 下次做咩（優先序）**
1. ✅ **已做（09-13 03:06）** restart ＋ shadow 生效 → 等 ≥48h 樣本，用 `scripts/alert_shadow_report.py` 睇分佈（M1 打機時 GPU soft ≤2/hr、M3 Prism 開住唔玩 FP <5%）。
2. ✅ **已 commit（`be099a7`）＋ push＋開 PR #12**——merge 與否等 SK。
3. 真機驗收（SK 選 **4b＝下次 session**，唔急）→ 過關才 `enforce`。
4. ✅ 殘留檔已清（3 個 tracked 已 commit 刪除；2 個 folder 已搬去 %TEMP% 備份）。10 條規格偏離全部寫入 plan（第 9 條＝digest 句措辭；第 10 條＝三輪 review 記錄）。
5. Task 10 要跑 ranking prompt benchmark（p95 ≤3s）先開工。

**4. 順帶（side topic）**
- Chrome「cookie 設定有問題」（`accounts.google.com/CookieMismatch`）：root cause = Chrome 設定「封鎖第三方 Cookie」（`cookie_controls_mode=2`）＋ 上次 Chrome 係 crash 收場。已（SK 批准後）備份 `Preferences.bak-20260913-0048` 並改為 `1`（只在無痕封鎖）。另發現：Chrome 開機自動背景啟動（HKCU Run `GoogleChromeAutoLaunch_…`）＋ 一個 kill 唔到嘅 **stuck GPU process**（`--type=gpu-process`，父 process 已死）——同 5090 driver TDR 條線或有關，值得跟。

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
