# HANDOFF — JARVIS 交接（固定檔）

> **呢個係固定 handoff 檔**（2026-08-30 起）：每次 session 結束**更新呢份**，唔好開新日期檔；舊交接版本移入 `plans/archive/`。
>
> **排序規則（2026-09-10 起）**：新 session 一律**加喺最頂**（時間倒序）；唔好 append 落尾。更新完先 commit（`docs(handoff): ...`，唔 push）。
>
> 下次 session 起點：**JARVIS ONE 0.4.10 跑緊；`1bdac68`（alerts ctypes fix）已 push 且 09-10 23:4x 重啟 sidecar 後已生效（ctypes flood 清零、serve.log 已 truncate）；**jarvis-pc 由 2026-08-10 起 59 個 commit 全部未 push**（remote main = `ca463a3`，2026-09-12 `ls-remote` 實測；舊稿寫「已 push」／「ahead 3-4 docs」全部係錯）；**MC 線 09-11 早：Arch-3/3a `1ba048f` 已 push ✅（真機驗收 PASS）；DSML scrub fix 已改／已驗／review SHIP 但**未 commit**；新 jar `012da9cc` 已 deploy（09-12 01:59 SK 真機跑：**DSML fix 生效 ✅**，但兜底路徑漏內部 FACT——見最頂 09-12 section）；OpenClaw/Hermes 架構比較已寫入 → 建議 A/B/C 未拍板**；09-11 凌晨診斷過 GPU driver TDR（SK 決定唔郁）**。讀呢份之前先讀：
> 1. `jarvis-pc\AGENTS.md`（專案 context——**自動載入規則已寫入主契約，唔使 SK 叫**）
> 2. `C:\Users\skps9\AGENTS.md`（主契約——Code Review 兩次規則已升格入契約）
> 3. `REMAINING_WORK.md` + `2026-08-29_self-evol.md`（計畫書，R1-R20b 齊全）

---

## 今日（2026-09-12 凌晨 session，Discord）—— MC 線：兜底路徑漏內部 FACT（實錘）＋ config `off` 未還原；history 核對捉到 3 處 drift

**1. MC 線（詳見 `super_minecraft_AI_player/.hermes/plans/HANDOFF.md` 最頂）**
- 09-11 嗰個 DSML 顯示層 fix **確認喺 deployed jar 跑緊**（sha256 前綴 `012da9cc`；`javap` 見 `dropResidualDsmlLines`／`DSML_PIPE_RUN`）→ 今日 01:59 SK 真機 run **冇再漏 markup** ✅。
- 但同一 run 暴露**新一層**：兜底路徑（`askNativeTools="off"`）之下，model 把**整份 LLM-facing FACT／指令文**回吐入答案（玩家見到「勿宣稱無法合成」「推薦合成／取得時…」「注意：JEI 可能混入 NBT 變體」等內部字 + 內部 id）。log 實錘：單輪冇 tools、`prompt=9450 / completion=1237`；字串同 payload 逐字對得上（連 tag 剝走後嘅前導空格都保留）；尾行【來源】係 `ReplySources.ensure()` 加嘅。
- ⚠️ **09-11 寫「測完 config 已還原 auto」係錯**：instance 檔一直係 `off`（即係一路行兜底）→ 02:09 SK 自己改返 `auto`（檔案已寫入 ✅，即時生效、唔使重啟）。教訓：mod config 要 game 關咗先改 + 讀檔驗，唔好信改完嗰一刻。
- 未拍板：**加 raw-reply log**（一行，分辨「AI 照抄 payload」vs「程式貼 facts 兜底」）→ 定案後才修；另 09-11 DSML scrub fix（4 檔）**仍未 commit**。

**2. ⚠️ History 核對：3 處 drift（實錘，唔係照抄舊稿）**
- **(a) jarvis-pc 由 2026-08-10 之後 59 個 commit 全部未 push。** 實測 `git fetch origin main` + `git ls-remote` → remote main = `ca463a3`（2026-08-10 10:57，PR #11）。舊 HANDOFF 寫「`1bdac68` 已 push」「ahead 3/4 docs」**全部係錯**（實際上 `1bdac68` 同之後嘅 docs 都喺未 push 嘅 59 個入面）。
- **(b) 09-11 23:36 深夜 session（`jarvis-a1692f57`）未記錄**：連續 5 句廣東話語音被本地 ASR（sensevoice）聽錯（「大心你去哎下。」「去就可以孭噶啦。」…），當時提咗三選一 —— ① 打字重講 ② 轉 MiMo 雲端 ASR（key 已配）③ 試本地 Fun-ASR-Nano —— **SK 未答** → 浮返 pending（語音線）。
- **(c) `.hermes/plans/self-evol-SUGGESTIONS.md` 有未 commit 改動**（+3 行，09-11 self-review append）→ 未 commit（留返畀 SK 決定）。

---

## 今日（2026-09-11 早 session，Discord，續）—— 為咩 OpenClaw / Hermes **唔會有** DSML 漏出問題（SK 問，架構比較）

> 結論：**佢哋都撞過**，只係架構「唔確定就唔出街」；PackAI 係「照出，事後 regex 洗」→ 黑名單永遠追唔完（= SK 講嘅「not every times」**根因**）。

**實錘 ①：OpenClaw 撞過一模一樣嘅**
`openclaw/openclaw` PR **#128882**（merged 2026-08-29，closes #128858）：
> fix(deepseek): **doubled-bar DSML tool calls are delivered as text and never executed**

—— 連「never executed」都中（今次 log：`toolCards emission=0`，靠 `autoEmission` 補卡 = model 想叫工具但用戶乜都冇發生）。

**實錘 ②：三邊架構對比**

| | **OpenClaw** | **Hermes** | **PackAI** |
|---|---|---|---|
| 偵測位置 | transport **串流層**（文字未到 UI） | adapter normalize 之後 | UI 前最後一步，**事後 regex** |
| 變體處理 | `["\|","｜","｜｜"]` **一次明列三種**（含雙豎線），recovery + filter 共用同一份 grammar | `_TOOL_CALL_LEAK_PATTERN`（`to=functions.x`） | `DSML_PIPE` = **淨一條** |
| 撞到之後 | **Recovery：解析返做真 call 並執行** + 文字過濾 | **當回合 `incomplete`** → 清空 `final_text` → 重試要模型用正式 `tool_calls` | **淨刪唔執行** → 行動蒸發 |
| 唔確定 | **fail-closed**（pair 唔上嘅 tag 唔准授權工具 + 256KB cap） | **fail-incomplete** | **fail-open** |

- **OpenClaw 檔案**：`packages/ai/src/transports/deepseek-dsml-grammar.ts`（`DEEPSEEK_DSML_MARKERS`）、`deepseek-text-filter.ts`（串流 filter + buffer split tag 前綴）、`openai-completions-dsml.ts`（`RecoveredDeepSeekDsmlToolCall` = **執行返**）。PR 金句「**Each invocation, parameter, and suppressed block must close with its opening marker**」← 正解 review 提嘅 over-match LOW。
- **Hermes 檔案**：`hermes-agent/agent/codex_responses_adapter.py` → `_TOOL_CALL_LEAK_PATTERN` + `leaked_tool_call_text`；註釋寫明「**no audit trail and no tools actually ran**」。主 loop 每回合都帶 tools（`tools=None` 只見於內部 summary call）→ 結構上少撞。

**實錘 ③：PackAI 已經有救嘅機器，係兜底路線冇叫佢出嚟**
- 已有 `hasLeakedToolXml()` / `parseEmbeddedToolCalls()` / `parseLeakedToolXml()`；但 `AskToolLoop.firstAsk` **L332** `if (!offer) return nz(llm.askNoTools());` ← 直接 return，冇經 recovery（`capableLoop` L373、`continueAfterAsk` L487 **有**行）。
- ⚠️ **同一盲點第二個 site**：`AskToolLoop.DSML_TOKEN`（L72-73）同一個**單豎線 class** → **連偵測都認唔到**雙豎線。今日只修顯示層，**偵測層未修**。

**建議（未拍板）**：**A** 放寬 `DSML_TOKEN`（細）｜**B** 抄 recovery：解析 → **真執行**（中，解「想叫工具但冇嘢發生」）｜**C** close tag 配對 + cap 取代鈍刀 `dropResidualDsmlLines()`（結構，順手清 over-match LOW）。

**已寫入 skill**：`llm-tool-calling-reliability` → `references/tool-call-markup-leaks.md`，新 section「How the big runtimes avoid it (checked 2026-09-11)」（含 PR 編號／檔案路徑／audit-every-detector 提醒）。

---

## 今日（2026-09-11 早 session，Discord）—— MC 線：Arch-3/3a 真機驗收 PASS ＋ 新捉到 DSML scrub bug（已修／已驗／已 review）

> Discord session（SK「read hand off」→「what it fix」→「go」）。**全部 MC repo；JARVIS ONE 無 code 改動。**

**1. Arch-3/3a（`1ba048f`）—— 舊 handoff 嘅「等你 restart game 煙測」係唔準確**
- 實錘：commit 之後**根本冇 build 過 jar**（最後 build 09-10 01:53；commit 09-10 23:42）→ 即係「唔係等你測，係未 build」。
- 今次補做：backup → 雙樹 build（forge JDK17／neo JDK21，`--rerun-tasks`）→ symbol 驗證（新 jar 有 `jeiForLlmFull`／`mergeJeiCatalogFull`／`capableForTools`，backup jar 完全冇）→ deploy。
- **真機驗收 PASS**：config 暫設 `askNativeTools="off"` 強制走兜底路徑 → SK 問「铁镐…用途/配方/取得方式」（focus = `minecraft:iron_pickaxe`）→ log 實錘：**淨 1 輪 LLM、冇 tool_calls**（= 確實行咗 `askNoTools()`）、prompt 嘅 `jei` payload **開頭就係真 `[RECIPE_CARDS]` catalog**：5 條 index 0–4（`role=output/output/input/input/input`），同 `recipe cards focus=… count=5` 逐張對得上。舊 jar 技術上做唔到（jar 內冇嗰個 function）。
- **`1ba048f` 已 push**（`96ad78a..1ba048f → main`；ahead/behind 0/0）。
- ⚠️ 測完 config 已還原 `auto`。

**2. 🐛 新捉到：DeepSeek DSML 標記漏入 UI（SK 截圖實錘）—— 已修**
- 症狀：兜底路徑下 model 用**文字**寫工具呼叫 → 垃圾原樣顯示喺 UI。
- Root cause（用**真 `AskReplyScrub` class** 跑真 reply ＋ reflection 逐個 pattern 實測）：model 今次吐**雙豎線 U+FF5C（`｜｜`）**＋ 容器字 **`calls`**（唔係 `tool_calls`）→ 四個 pattern 全部 `find=false` → 清唔走。（舊單豎線 case 有 test 守住，所以一路冇發現 → 典型「not every times」。）
- Fix（經 cursor-agent，雙樹 lockstep）：① `DSML_PIPE_RUN` = 一條**或連續多條**豎線 ② 容器字放寬 `(?:tool_)?calls?` ③ `LEFTOVER_TOOL_TOKEN` 加 catch-all `</?[^<>]*DSML[^<>]*>` ④ 新 `dropResidualDsmlLines()` 最後防線（任何仍含 `DSML` 嘅整行丟棄）。
- 驗收（全部 Hermes 自己跑，唔信 cursor 自報）：雙樹 `cmp` **byte-identical**｜雙樹 `compileJava --rerun-tasks` **BUILD SUCCESSFUL**｜`AskReplyScrubCheck -ea` **OK**（新 case K1–K4 全過）｜**真 reply 端到端 556 → 51 字**（DSML／invoke／parameter／item id 全清、合法【來源】行保留）｜python checks **FAIL=3 = baseline 一個唔差**。
- cursor read-only review（V1–V6）：**SHIP**。2 個 LOW：catch-all 對「prose 含 literal `DSML`」有理論 false positive；測試可再補 3 個 case（兩段 block 中間 prose、結尾【來源】行、無尖括號嘅殘留 `DSML` 行）。
- ⚠️ **Pre-existing 發現**：`AskReplyScrubCheck` L193（`!purpose.contains("[shift]")`）**喺 HEAD baseline 一樣 fail**（已對照實錘）→ 唔關今次改動；但因 `compileTestJava` 早已壞，呢個 check 一直冇跑。今次繞過方法：`javac -cp build/classes/java/main` 單獨編該 test class ＋ `java -ea` 跑（唔靠 gradle）。

**3. 現況**
- instance 現役 jar = Arch-3/3a **＋** scrub fix（sha `012da9cc…`）；config = `auto`；**新 jar 未真機 smoke**（要 SK 再 restart 一次）。
- backups（全部喺 `dist/_smoke_backups/`，`mods/` 唔留 .bak）：`…forge.jar.bak-20260911_071206`（0.2.1 原版）、`…arch3a-bak-20260911_083313`（只含 Arch-3/3a）、`packai-client.toml.bak-20260911_071206`。
- MC repo：`1ba048f` 已 push；**scrub fix 未 commit**（4 檔 modified：雙樹 `AskReplyScrub.java` ＋ 雙樹 `AskReplyScrubCheck.java`）。
- **下一件**：SK restart MC → 問同一題（`auto`）→ 確認 ① Arch-3/3a 冇 regression ② DSML 唔再漏 → PASS 就 commit scrub fix（建議 `fix(ask): harden AskReplyScrub for doubled-pipe DSML variant`）。

---

## 今日（2026-09-11 05:45 cron 核實）—— 無新 session 工作；實錘核對 + 修正 3 處狀態 drift

> jarvis-session-handoff cron（job `7b4af62c87c3`）。窗口 = 2026-09-10 06:00 → 09-11 05:45。逐個 session 核對（sessions DB：`20260910_073539_3e2db227` 07:35–09:31／`jarvis-14655cc5`＋`jarvis-8feaa634`＋`jarvis-07b64fe6` 20:0x–20:5x／`20260910_232411_ae42ba06` 23:24–23:52／`20260911_032609_bdd50fcc` 03:26–05:32）：**全部已有對應 section，冇未記錄嘅實際工作**。以下係核實出嚟嘅 drift 修正（全部有工具實錘）：

1. **改正檔頭 hash**：原寫嘅 `61c15c6` **喺 repo 唔存在**（`git log --all` 實錘）→ 實際係 `06aa722`（09-11 04:12「docs(handoff): 2026-09-11 凌晨 — GPU TDR…」）。jarvis-pc 現時 **ahead 3 docs**：`d8bfe3d`、`bee2e6d`、`06aa722`（全部未 push）。
2. **alerts.py ctypes 條目正式收口（實錘，唔再係「等 SK」）**：sidecar 09-10 23:4x 重啟之後——`GET /health` = `{"ok":true,"wake_on":true}`；`serve.log` 得 **27KB（05:44 還在寫正常 log）**；`grep -c "int too long to convert"` = **0**。即 `1bdac68` 已生效，136MB／370,905 次 flood 清零（備份 `serve.log.bak-20260910.gz` 977KB 保留）。
3. **工作區狀態**：tracked 改動只有 `.hermes/plans/self-evol-SUGGESTIONS.md`（09-10 09:01 daily self-review cron 寫入嘅 3 條 TREND-err 建議：09-05／09-06／09-10，全部圍繞同一個 ctypes flood）——本 cron 順手補「已解決」狀態行 + 一併 commit（docs only）。
4. **MC 線無變**：HEAD `1ba048f`（Arch-3/3a），working tree clean，仍等 SK 真機煙測先 push。

---

## 今日（2026-09-11 凌晨 session）—— GPU TDR「黑屏一閃」診斷（SK 決定唔做嘢）＋ handoff 補漏 ＋ skill script 修 bug

> Discord session `20260911_032609_bdd50fcc`（03:26–04:2x）。觸發：SK「check the window, it just black screen for a sec」。

**1. 診斷：唔係 window/app bug，係 NVIDIA 顯示驅動 TDR（reset）**

| 時間（09-11） | 事件 | 意義 |
|---|---|---|
| 03:23:44 | `NVIDIA OpenGL Driver` Event 1「A TDR has been detected」（pid=42008 `javaw.exe`） | 邊個 app 觸發 |
| 03:23:45 + 03:24:03 | `Display` **Event 4101**「nvlddmkm 停止回應，並已順利恢復」×2 | **= 你見到嘅黑畫面本體** |
| 03:23:47 | App Error 1000：`javaw.exe` 死於 **`nvoglv64.dll`** exc `0xc0000409` | app 被 driver fail-fast 殺 |
| 03:23:44–03:24:32 | `nvlddmkm` Event 153 ×24（48 秒 burst） | 前兆風暴 |
| 03:24:29 | JARVIS HUD（Electron）`--type=gpu-process` 重開 | 舊 GPU process 被 TDR 連帶殺死 → **HUD 都黑一黑** |
| 03:26:32 | SK 自己重開 MC | 原 instance log 停 03:23:41（native GL crash 唔會寫 crash-reports） |

**2. ⚠️ 自我更正（重要，入咗 skill）**：第一次只查 30 日 → 報「30 日內首次」，SK「but only happen this time」一句推翻 → 拉長到**事件保留期（2026-03-09 起）**實錘 **13 次同一簽名**：`javaw.exe` + `nvoglv64.dll` + `0xc0000409` + **同一偏移 `0x108eb9d`**（4-29×3、4-30×1、5-02×3、5-03×5、9-11×1）。4–5 月跑嘅係 NovaEngineering cleanroom（Java 21.0.7）、今晚跑 AI_test_NFWC_DIM 1.19.2（Java 17.0.15）——**唔同 pack、唔同 Java、同一個 driver code path**（driver 581.42 自 2025-12-12 未換）＝ 驅動 bug，唔係 pack、唔係硬件。對應 4101 分佈：3-18×1、4-29×3、4-30×1、5-02×4、5-03×7、9-11×2；最猛 5-03 15:56–15:59 連環 2 次 javaw 崩 + explorer.exe 崩 + dwm.exe 崩 + 當日 83×ev153。
**排除硬件**：WHEA 7 日 0、無 bugcheck（無 0x116）、無 reboot、無 OC 工具、power limit 600W = 原廠 default、43°C/P0 正常。

**3. SK 決定 = 唔做嘢（「maybe 4, since I am almost finish the mod pack；later we will switch to another modpack」）**——唔升 driver、唔關 threaded optimization、唔開 LocalDumps。反轉條件：變成連環／explorer·dwm 都崩／換 pack 後照出 → 先做「關 javaw Threaded Optimization（可逆）」＋「WER LocalDumps 收 minidump」。

**4. Incident 記錄**：`%LOCALAPPDATA%\hermes\state\gpu_tdr_incidents.jsonl`（2 條：09-11 事故 + 歷史更正，含 crash 日期／偏移／modpack／排除項）。

**5. Skill 更新**：`windows-hardware-monitoring` 加 TDR 段（event signature／30 秒 triage／**「講首次之前唔准只查 30 日」規則**）＋ `references/gpu-tdr-black-screen-diagnosis.md` ＋ `scripts/gpu_tdr_check.ps1`；**修咗 script 一個真 parse bug**（`foreach` statement 唔可以當 parenthesised argument 傳畀 function → 先砌 array 再傳），修完實跑 2m42s 出 17KB 報告 = 驗證 PASS。
**Sources**：NVIDIA Developer Forum `deterministic-nvoglv64-dll-crash-c0000409-fastfail…/381020`（Java/LWJGL、13 次同 offset）＋ `multiple-driver-versions-crash-and-terminate-our-app…/381146`（醫療設備廠商 400+ runs，崩潰喺 driver-owned worker thread，stack 冇 app code）。

**6. 🔍 handoff 補漏（SK 指示「also check history, some of them are not written in hand off」）**——對 sessions DB（267 sessions）逐個核 09-08～09-11：
- ✅ **sidecar DOWN monitor 修復其實 09-09 22:40 已經做咗**：`hermes/scripts/jarvis_sidecar_health.py` 而家 DOWN 時 `exit 0` + 印固定 fingerprint（照 docstring 原意），09-10 docs commit `a68cbb9` 有記；monitor_state 自 2026-08-31 未變（即一直 OK）。**但 09-09 節 §4 仍寫「下次想整先整（等 SK go）」= stale，以本條為準。**
- 🆕 **`skill-router-verify 一週觀察報告` cron（`8294250748fa`）自身有 bug**：`script` 欄填 `analyze_skill_selection.py --days 7` → runner 當成完整路徑 → **「Script not found」**，09-10 09:00 該 run 冇跑到 script（agent 手動跑分析才出到報告）；job 已 completed/disabled。**教訓：Hermes cron `script` 欄唔支援參數** → 要包一層 wrapper script 或用 `no_agent`。報告結論：would-block 84% 係假象（classifier top1 69% 都答 obsidian）→ **Layer 2 維持唔開**。
- ✅ **jarvis-pc 現時 ahead 2**（`d8bfe3d`、`bee2e6d` docs，未 push）——舊 Next 講嘅 `f07073d` 已 push。
- ✅ **MC repo**：`1ba048f`（Arch-3/3a）已 commit、未 push（ahead 1）；MC repo 自己份 HANDOFF 仍寫「code 未 commit」= 略 stale（已在 MC HANDOFF 補狀態修正行）。
- ✅ 其餘 09-08～09-10 sessions（武刃屬性 06:49／tools 拆法 16:16／sidecar DOWN+Douyin+ComfyUI 08:25／由易到難排序 14:55／MC 跨午夜 22:36–03:31／handoff #4 07:35／JARVIS voice 20:0x–20:5x＋Arch-3 落地／AI_Studio Phase 0 23:24）全部已有對應節，冇其他大漏。

## 今日（2026-09-10/11 深夜 session 2）—— 1+2+3 清單 + AGENTS.md 修 bug + AI_Studio Phase 0 開工

> Discord session（承接同日 handoff 整理）。SK 指示：「do 1+2+3 → fix agents.md → hold jarvis & mc → go for AI studio」。

**1+2+3（全部完成，有實錘）**
1. ✅ **JARVIS sidecar 重啟**（SK 批）：kill PID 24992 → **10 秒後 Electron 自動 respawn**（`/health` ok）；ctypes flood **373,158 → 0**；`serve.log` 137MB → 0（備份 gzip 977KB 留 `serve.log.bak-20260910.gz`）→ **`1bdac68`（alerts ctypes fix）正式生效**
2. ✅ **MC Arch-3/3a commit `1ba048f`**（`fix(ask): keep [RECIPE_CARDS] catalog on no-tools fallback path`；連 `code_change_log.md` 條目）——**未 push**（跟規矩：等 SK restart game 真機煙測）
3. ✅ **jarvis-pc docs push**（origin 到 `a276049`）；MC 保持 ahead 1

**AGENTS.md 修復（捉到 3 個真 bug）**
- ① `%USERPROFILE%\.hermes\` **根本唔存在**（檔案叫 agent 複製 SOUL.md 去嗰度）→ 改正做真實 Hermes home `C:\Users\skps9\AppData\Local\hermes`（Stack／Layout／Secrets 三處）
- ② 斷句「已知坑（實測 + 社群確認）」→ 補完整
- ③ 加規則：**HANDOFF 新 section 一律加最頂（時間倒序）**
- 源頭 `Code_Project\Hermes\AGENTS.md` 已同步；驗證 live == source；backup `AGENTS.md.bak-20260910_234227`

**AI_Studio（SK「go」）—— Phase 0 開工**
- 📄 Runbook：`AI_Studio\docs\plans\2026-09-10-phase0-runbook.md`（環境現況／Phase 0 清單／spike 三類樣片＋收貨標準／SK 決定）
- 🔧 GPU 安全閘 `AI_Studio\scripts\comfy_guard.py`（cursor 寫；Hermes 自己驗收）：pre-flight（activity gate／溫度／VRAM／ComfyUI health）＋序列 `JobLock`＋`>80°C` 自動 `/interrupt`＋job JSONL log。**實測**：`--status` 讀到真 GPU（45°C / 103W / VRAM 24951MB）；`--check` 正確 FAIL（`playing` + VRAM 7.5GB < 20GB 門檻）；py_compile OK；unittest **7/8**（1 個亂碼輸入 case fail → 已 dispatch cursor fix round）
- 🔗 **H3 API graph 已砌好**：`AI_Studio\workflows\h3_t2v.json` + `h3_i2v.json`（由官方**本地**範本 `video_minimax_h3_i2v.json` 嘅 subgraph 反推節點鏈：UNETLoader(fl2va) → LoraLoaderModelOnly(fl2v_turbo_8step) → MiniMaxH3ImageToVideo → BasicGuider / KSamplerSelect(res_multistep) / BasicScheduler(simple, steps=8) / RandomNoise / SamplerCustomAdvanced → VAEDecode(video VAE) + VAEDecodeAudio(audio VAE) → CreateVideo(24fps) → SaveVideo）；**靜態驗證對 `/object_info` PASS**（唯一提示 = LoadImage 佔位檔名，跑前換真圖）。⚠️ 真跑未做（等 SK 講時段 + power 決定）
- ⚠️ **捉到坑**：官方 `api_minimax_h3_*.json` 範本其實用**雲端付費節點**（`MinimaxHailuo03FirstLastFrameNode`），本地零成本生成用唔到 → 要用原生節點手砌 API graph；H3 原生 schema（`MiniMaxH3ImageToVideo`／`ReferenceToVideo`／`EmptyMiniMaxH3LatentAV`／`SigmaShift`／`CreateVideo`／`SaveVideo`，含 required inputs）已寫入 skill `comfyui-desktop-headless`

**SK 決定**：① 位置沿用 `Documents\AI_Studio\` ✅ ② 平台 **兩邊同出**（英 YouTube + 中文 B站/抖音）✅ ③ power limit ⏸（SK 問會唔會影響打機 → 我提議 **generation-only cap**：開 job 前 450W、完 job 還原 600W，打機零影響）④ spike 時段 ⏸（提議 auto idle 觸發）

**JARVIS + MC 已 hold**（SK 指示）——3b shot0／`compileTestJava` 修復／LHM reboot 驗證／G 人手實測全部唔郁

## Next（下次 session）
1. **push 兩隻 repo（等 SK 一句）**：jarvis-pc **ahead 3**（`d8bfe3d`、`bee2e6d`、`06aa722` docs）；MC repo 等 Arch-3/3a 真機煙測 PASSED 先 push `1ba048f`（ahead 1）
2. **AI_Studio**：等 SK 答 power 策略 + spike 時段 → Phase 1 spike（3 類樣片、idle 時段跑；H3 T2V/I2V workflow JSON 已砌好）
3. **MC**：SK restart game → Arch-3/3a 真機煙測（問題「铁镐有什麼用途、配方和取得方式」期望 5 卡）→ PASSED 先 push → 之後 3b（shot0 毒化）
4. **GPU TDR（2026-09-11 決定：唔做嘢）**：如再出黑屏 → 讀 `%LOCALAPPDATA%\hermes\state\gpu_tdr_incidents.jsonl`、跑 skill `windows-hardware-monitoring` 嘅 `scripts/gpu_tdr_check.ps1`（唯讀，先查滿保留期再講「首次」），再向 SK 提緩解選項（關 Threaded Optimization／WER LocalDumps／升 driver）
5. **JARVIS**：已清；等 SK 真 reboot 驗 LHM（hold 中）
6. backlog 不變：skill-system 暫緩；G 人手實測（等新 mic；Settings tab 可隨時測）；stt_stats／clarify_stats ≥7 日接 cron monitor

---
## 今日（2026-09-10 session）—— 全日三 session：alerts fix push + MC Arch-3/3a 落地（未 commit）+ AI_Studio 市場調查報告

> 09-10 全日 = ① 00:15–02:30 跨午夜 MC 線 ② 07:35–09:35 Discord session（`20260910_073539_3e2db227`）③ 20:05–20:56 JARVIS voice + api_server session（`jarvis-07b64fe6`）。

**深夜 00:15–02:30（MC 線，跨午夜；詳見 MC repo HANDOFF）**
- **武刃 tooltip root cause 實錘**（推翻 09-08 cursor report 嘅「NBT-gated lore」inference）：真兇 = `AskService.trimPurposeTooltip` L495 `if (kept>=8 && !claim) break;`——武刃頭 8 行係 stats、第 11 位先係綠色 claim 行，break 就剪走 → fix `900a7e4`（forge，`break`→`continue`）+ `96ad78a`（neoforge sync + bump 0.2.1），**已 push**；CF 8845552/8845554 upload + verify；instance 已 deploy `packai-0.2.1`。smoke 實錘 `claimHints src=232/out=0` → `src=278/out=1`

**07:35–09:35（Discord session「Read hand off #4」）**
1. **Backlog 三 repo 全面核對**（SK 連問「only those task left?／check more, is it all? and is it some of them are done?」）——jarvis-pc / MC / Earth_Online 逐項對 git + cron 實錘，剔走已完成項
2. **ComfyUI 線定方向 = 變現**（SK「make some money」）→ 確認環境（ComfyUI API server 8000 healthy v0.34.0；MiniMax H3 模型已齊）→ 設計書 `AI_Studio\docs\plans\2026-09-10-ai-video-production-design.md`
3. **Skills 決策（SK 問「install super power and ponytail skill first」）**：兩者 review 全綠（superpowers 284K★／ponytail 133K★，MIT、09-07/08 仍有 push）→ **唔裝成個 superpowers plugin**（14 skills 中 ≥5 個同現有重疊——systematic-debugging／TDD／requesting-code-review／writing-plans／writing-skills；會令 09-03 嘅 128→117 整合成果 + 揀選噪音回歸）；**只移植 `brainstorming`** 入 Hermes（08:09）；**ponytail 裝 Cursor rules** `~/.cursor/rules/ponytail.mdc`（08:08，headless cursor-agent 自動食，零依賴）
4. **skill-router 現狀查證**（SK 問「router 可以 cover 咩？」）：實錘 `skill-router-verify` 係 **Layer 1 observer only**（唔 block）；366 entries 中 **would-block 83.9%** → **Layer 2 唔開**（會誤殺大量正常揀選）；結論 = 唔好再加重疊 skills
5. **AI 影片市場調查 + PDF 報告**（SK「順便同我做一個詳細嘅市場調查」→「整理成報告 send 畀 friend」）：research note `AI_Studio\docs\research\2026-09-10-market-research.md`（09:22）→ 5 圖表 + 9 頁 PDF `AI_Studio\docs\report_20260910\AI影片市場調查報告-20260910.pdf`（09:31；SK 反饋標題孤兒頁 → 加 CSS 分頁控制，10→9 頁）。重點：**AI 工具教學 RPM $8-20、+340% YoY 且唔需要 5090**；Shorts RPM ~$0.13；一般 ASMR 最飽和
6. **5090 power limit 安全查證**（SK 問）：power limit 唔係免死金牌（根因 = 接頭接觸電阻）→ skill `windows-hardware-monitoring/references/rtx-5090-power-safety.md`（09:29）
7. **Skills 更新一批（09-10 全日）**：`brainstorming`（新移植）／`ai-content-monetization`（09:13）／`chart-report-pdf`（09:29）／`pdf-report-pipeline`（09:33）／`comfyui-desktop-headless` video-production-pipeline ref（09:12）／`windows-hardware-monitoring` rtx-5090-power-safety（09:29）／`sk-reporting-style`（07:49）／MC skill refs（wuren trim rootcause ×2、packai-ask-prompt-assembly、packai-java-check-harness）

**同期：09:00 cron self-review 發現 TREND-err-2026-09-10**
- serve.log 當時 87.8MB、ctypes `int too long to convert` 累計 232,011 次 → **`1bdac68` 未生效**（sidecar 由 09-09 10:36 起冇重啟，早過 commit ~12 小時）；建議 kill 8765 python + push + truncate log；狀態 🟡 待 SK（`.hermes/plans/self-evol-SUGGESTIONS.md`）

**晚 20:05–20:56（JARVIS voice + api_server session）**
8. **語音 session ×2**（20:05 `jarvis-14655cc5`／20:18 `jarvis-8feaa634`）：ASR 誤聽成「都买啦，你再是」→ 查實 settings 仍係 Arctis Nova 7、裝置清單未見新 mic → **新 mic 仍未到位，mic 相關實測繼續 pause**
9. **SK「你任意一個你点出都行」→ agent 自行拍板揀 MC 線 Arch-3/3a 並落地（code 未 commit）**：`askNoTools()` 由 `jeiForLlm()`（raw JEI、冇 `[RECIPE_CARDS]`）改 `jeiForLlmFull()` = `recipeCatalogForLlm()` ⊕ `mergeJeiCatalogFull()`（**merge 唔 replace**，剝走重複 catalog block）+ 抽 `capableForTools()`；雙樹 sync。驗收（agent 自己跑，唔信 cursor 自報）：雙樹 compileJava BUILD SUCCESSFUL；**真 AskEngine bytecode scratch harness `-ea` 8 case PASS**；python checks 93 PASS / 3 FAIL（`git stash` 對 baseline 證實 pre-existing）；cursor review 兩輪（首輪 2 MED 已修）
10. **`1bdac68` 已 push**（20:37 實錘 `origin/feature/hermes-alerts-mcp` 已含，ahead/behind 0/0）——但 **sidecar 未 restart → fix 未生效**（09-10 23:25 實測 serve.log 136MB／370,905 次 flood）
11. **23:24 本 session（Discord「read hand off, and history, find diff, then update it base on time」）**：逐項核對 git（jarvis-pc ahead 1 = `f07073d`；`1bdac68` 確認喺 origin）+ 檔案 mtime（AI_Studio 報告 09:31、skills 09-10 全日）+ cron/API session 記錄 → 補齊 09-10 全日三 session 內容、**全文改成時間倒序**（新 section 一律加最頂，規則寫入檔頭）、更新「剩低」alerts 條目 → docs commit
12. **兩邊 HANDOFF 已更新 + commit**：jarvis-pc `f07073d`（**未 push**）、MC repo docs commit（已同步）
13. ⚠️ 順手發現：MC repo **`compileTestJava` HEAD 已經壞**（2 個 error 指向 Arch-1 移除嘅 `LlmClient.toolSchemaDescription(String)`）→ repo Java harness 跑唔到，今次用 scratch harness 頂住

## Next（下次 session）
1. **等 SK 一句話（3 件一次做完）**：① kill 8765 嘅 python（Electron ~90s 自動 respawn）令 `1bdac68` 生效 → grep serve.log 確認 flood 停（**唔喺 SK 打機時做**，語音會停 ~90s）② push jarvis-pc `f07073d`（docs）③ truncate serve.log（已 136MB／370,905 次）
2. **MC Arch-3/3a commit**（建議 `fix(ask): keep [RECIPE_CARDS] catalog on no-tools fallback path`）→ SK restart game 真機煙測；之後 3b shot0（方案 A）；3c YAGNI 暫緩
3. **MC `compileTestJava` pre-existing 損壞**：要唔要另開一輪修返（恢復 repo Java harness）
4. **AI_Studio 線（等 SK 拍板）**：報告已交付；下一步 = Obsidian prompt DB／MiniMax H3 I2V 實測／路線揀邊條（報告建議雙線：AI 工具情報頻道 + 長線 AI 短劇）
5. backlog 不變：skill-system 暫緩；G 人手實測（等新 mic；**Settings tab 唔關 mic 事可隨時測**）；LHM 開機 autostart（等真 reboot）；stt_stats／clarify_stats 等數據 ≥7 日接 cron monitor

---

## 今日（2026-09-09 session）—— ⚠️ Sidecar 8765 朝早 DOWN（~06:15 後–10:37 前）→ 已自行恢復；cron pause/resume（SK 指示）；無 code 改動

> Discord session 08:25（承接 cron 05:45 已補嘅 00:15「what is 3?」問答後）。**真實權威 = 本節 + cron output 檔**（`cron/output/6a98a79be95f/`）。

1. **08:25 SK「what happen?」→ 診斷發現 sidecar 8765 DOWN**（connection refused）：`jarvis-sidecar-health` cron（6a98a79be95f）08:07–08:51 每 run 報 `DOWN URLError: [WinError 10061]`；`jarvis-alerts` MCP（指 8765/mcp）reconnect 5 次失敗後 parking、每 300s self-probe；系統冇 sidecar process（淨 Hermes gateway ×2 + `hermes_alert_poll_loop.py` pythonw）；gateway 06:39 曾 restart（06:38 `gateway-exit-diag.log`），Discord/API connected 正常。
2. **SK「stop that for now」→ 澄清係「stop that job」→ 08:53 pause `jarvis-sidecar-health`（6a98a79be95f）**；**10:38 SK「resume it」→ resume**（job enabled、照跑）。
3. **⚠️ Sidecar 已自行恢復**：10:37 resume 後首 run `no_change`（fingerprint 回 08-31 OK hash）＋ 10:39 curl `/health` 實錘 `{"ok":true,"wake_on":true}`（PID 24992 listening 8765）——實際恢復時間喺 08:53–10:37 之間（估計 Electron respawn 或 SK 開返 JARVIS，未確認）。
4. **脆弱位（記低，SK 叫唔好而家郁）**：health script DOWN 時 `exit 1` → cron 當「monitor source failed」ERROR spam（唔當 fingerprint change）→ **DOWN 唔會 wake agent、SK 收唔到 alert**——monitor pattern 對 DOWN 狀態失效（只喺恢復後 no_change）。下次想整先整：DOWN 應 `exit 0` + 印固定 DOWN fingerprint（照 docstring 原意）。
   → ✅ **2026-09-09 22:40 已修**（`%LOCALAPPDATA%\hermes\scripts\jarvis_sidecar_health.py` 而家 DOWN = `exit 0` + 固定 `DOWN <reason>` fingerprint；09-10 docs commit `a68cbb9` 有記）。**呢條唔再係 open item。**
5. **下次優先序**（承 cron 05:45 已記嘅 4 選項 backlog 不變：① push MC `dec1471` ② review skill-system plan ③ Arch-3 round ④ alerts.py ctypes fix）＋ 新加：sidecar DOWN 冇 alert 嘅 monitor 修復（可選，等 SK go）。

**（續 11:0x–15:0x，同 session 流延續——Douyin 吸收 + ComfyUI API control 打通 + compression bug 診斷；JARVIS ONE 自身無 code 改動）**

6. **Douyin 吸收 run（SK「watch tiktok → deep-read」）**：scan 383 items（base 09-07 315，coverage 差異唔當純增量）→ priority 5 + 三主題（AI 漫劇/短劇 22 + Agent/skill 16 + MiniMax H3/本地視頻 16）deep-read（19 video ASR + 11 note 圖 vision，產物 `%LOCALAPPDATA%\hermes\media_import\douyin_deepread_20260909\`）→ **11 條 high-value 入 `Documents\Hermes_Vault\03_收藏吸收\2026-09-09-douyin-*.md`**（status absorbed；MOC +11；唯一 absorb:yes = 去AI味 7682745237197851942 → humanizer patch）→ **skill patches ×2**：`humanizer` 加 CJK/中文補充 section（AI 口頭禪/扮演著/三段式/乾淨但冇心跳，映射英文 pattern 編號）；`content-absorption` 加 Trend observations + **absorb-first 規則**（≥5 條 cluster = 興趣 signal → 深睇；**興趣 ≠ 有用 gate**——純娛樂唔入庫；按調動次數決定保留；要主動）。Notes：`notes_priority5.md` + `notes_themes.md` 喺同 folder。**SK 收藏 pattern 已由 AI coding → AI 內容生產**（見 skill trend observations 實例）。
7. **SK 想同朋友上傳 AI 影片（未確定）；API 預算緊（「ran out of money」）→ 本地方案**：5090 32G 跑 MiniMax H3/ComfyUI 零 API 成本。方案概覽 `media_import\minimax_h3_local_plan_20260909.md`（官方 docs 查證）。memory user profile 已更新（本機/免費優先 + AI 影片計劃）。
8. **ComfyUI API control 打通（重要基建）**：發現 ComfyUI Desktop 已裝（v0.34.0，`Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI` source；真正 python = `Documents\ComfyUI\.venv\Scripts\python.exe` py3.12 torch2.10 cu130）+ **MiniMax H3 模型已齊**（09-04 已下載：fl2va pruned 19.5G + qwen3vl nvfp4 14.6G + 2 VAEs 5.5G + turbo LoRA——SK 已用 Desktop 跑過 11 條 MiniMax_H3 mp4，09-04→09-08）。**起咗 headless API server（port 8000）**：`python main.py --port 8000 --enable-manager --listen 127.0.0.1 --disable-auto-launch --extra-model-paths-config <ComfyUI>/extra_model_paths.yaml`（該 yaml 新寫，指向 Documents\ComfyUI\models + Comfy-Desktop\ComfyUI-Shared\models 兩個 store；server 依家見全部 13 diffusion + 12 text_encoders + 10 vae models）。**z-image turbo txt2img 實測 PASSED**：API POST /prompt（原生 nodes，唔用 subgraph templates）→ 12s 出 1024² 圖（jarvis_test_00001_.png，質素好）→ /history poll → /view 攞圖。**即係 JARVIS 可以 API-driven 全 control ComfyUI 生成**（SK 要求：JARVIS 控制劇本/人物/prompt/工作流，SK 做 creative director 只 review）。
9. **Prompt database 計劃（進行中）**：SK 想先建 prompt DB（search online：Luma 5-Element Formula Subject+Action+Setting+Camera+Style / LTX 7-part + audio；ComfyUI_PromptManager 151★ 未裝——review 門檻 + 唔配合 API control）。SK 問「obsidian 可以嗎」→ 建議獨立 Obsidian vault `Documents\AI_Studio\`（Characters/Scenes/Styles/Camera/Scripts/Test_Log，[[雙鏈]]互連）——**未拍板、未起**；Obsidian 未裝（要 check review + 裝前問 SK）。設計方案已喺對話，下次 session 可直接續。
10. **⚠️ Hermes compression bug 診斷（SK「check why can't compress context」）**：session 滾到 ~384K tokens（douyin + ComfyUI 探索）→ auto compression ≥5 次全失敗（600s zero progress）→ **root cause = upstream bug** `NousResearch/hermes-agent` **#100501**（aux 2026-09-01）：auxiliary client streaming 冇 stale stream detection（主 loop 有 `stale_stream_kill` 但 auxiliary 冇）→ 大 context stream 靜止冇 recovery → 等足 ceiling 放棄。本地 code 實錘 `_aggregate_chat_stream` 得 total_ceiling 冇 per-chunk idle。**相關 PR 全部 open 未 merged**（#100526 stop stalled aux streams / #102435 / #100024 / #94718）。**選項：開新 session（推薦，今日已 handoff）/ config workaround 試 auxiliary compression 轉 volcengine glm5（未試）/ 等 upstream**。`compression.threshold 0.35` 照舊。
11. **Backlog 更新（todo list）**：原有 b1-b5（MC push dec1471 / skill-system review / Arch-3 / alerts.py ctypes / sidecar monitor fix）＋ a3（douyin classified JSON+improve plan 可選）＋ **新線 ComfyUI**：AI_Studio vault setup（等 SK 拍板 Obsidian）、MiniMax H3 I2V 測試（等 SK go）、prompt DB 設計。Sidecar 而家 UP（PID 24992 jarvis serve）。

---

## 今日（2026-09-08 session 尾）—— MC 線 planning：friend wishlist 三層分類 + tools 拆法決策（維持現狀 8:2）（JARVIS ONE 無 code 改動）

> Discord session：承接 09-08 06:49「查看武刃武器详细属性」thread（friend wishlist 8 項討論，auto-reset 後 SK 問「which better?」）→ 重讀 history → 決策 → 歸檔。**真實權威 = MC repo 自己 plans + 本節**（jarvis-pc HANDOFF 對 MC 線一向 lag，先例一致）。

1. **SK「which better?」= 問 tools 拆法 A/B/C/D 揀邊個**（上 session 尾我列出四種拆法問 SK 揀）→ 逐項 adversarial 分析 + 實錘現況（`AskEngine.java` L30-46 硬註冊 14 個內建 tools，同一個 jar、玩家冇得揀；Scope Y `registerExternal` 已上 0.2.0 stored-only）：
   - **A. 分 jars（可選 mod 模組）✗**：dual-tree × 每 jar = 版本矩陣爆炸、玩家安裝複雜；MC 慣例係一個 mod 內 extensible API（JEI/EMI plugin），唔係拆 mod
   - **B. config 開關**：只係「閂現有」——friend 想要嘅係「加新」，B 俾唔到；只可做 registry side option
   - **C. data/logic 分離 ✗**：friend wishlist 大部份係 runtime state（飾品/器官/機台速度）+ logic（Psi）——唔係 data 餵得到；為一個 friend 做 data framework = over-engineering
   - **D. 開放 tools API ⚠️ 方向啱、時機錯**：D 受眾 = 第三方 mod dev；friend 係玩家唔寫 tool。packai 自己 player_state 都未有
   - **Verdict 8:2 = 維持現狀：唔拆 jar、唔開放**；要做只係 **D 第一步「內部 registry 化」**（14 隻 hard-code tools → registry，令 packai 自己加 player_state built-in tool 唔使改 `AskEngine`）。反轉條件：出現第二個真係想自己寫 tool 嘅人先升 public API
2. **Friend wishlist 8 項三層分類**（逐項 code 實錘）：已實現 ✅ #3 冇 item JEI 查（ItemSearchAskTool）/ #7 季節（SeasonContext）/ #8 部分 hover；要 **player-state tool** 🟡 #2 期望 DPS（SK 糾正：要連飾品/器官/藥水 buff 先係 friend 想要——raw attribute 已有但玩家 state 冇管道）/ #5 機台速度傾向（mirror coalesce 令 model 睇唔到邊部快）；要 mod 整合 ❌ #1 Psi 術式 / #4 深鏈（淺鏈 skill 可但撞 MAX_LLM_ROUNDS=3）/ #6 Regenerate UI。**教訓：skill = 最後一里——data 唔齊入 model 眼，skill 點教都冇用**（同武刃 root cause = data/capture 層一致）
3. **歸檔**：`super_minecraft_AI_player/docs/plans/friend-wishlist-2026-09-08.md` 已寫（SK「ok」批）→ **commit 待做**。MC repo HEAD = `fd7d314`（skill-system-dropin v1 docs commit，09-08 10:12；內文已引 friend-wishlist 教訓）
4. **下次 session 開頭**：commit friend-wishlist 歸檔（MC repo）→ 等 SK 煙測 R8 Fix E jar（restart MC 問「铁镐有什么用途、配方和取得方式？」→ 期望 5 卡：2 合成 + 3 用途全對應 prose、無孤兒）→ PASSED 先 push MC repo 6 commits（ahead origin）→ Arch-3 round。Friend-wishlist roadmap 下一步 = **`player_state` tool 設計**（registry 化 prerequisite）

**（續 16:22–18:39，同 session 流延續——狀態修正 tail；cron 09-09 核實補檔）**

5. **16:22 同步 commit ×2（同一秒）**：MC repo `dec1471`（docs(plan): friend wishlist 三層分類 + tools 拆法決策 2026-09-08——`docs/plans/friend-wishlist-2026-09-08.md` 16:21 寫）＋ jarvis-pc `8b80e81`（本 HANDOFF section）。MC HEAD = `dec1471`（當時以為「commit 待做」嘅記錄即刻已做咗）。
6. **⚠️ 18:38 狀態修正（上面 item 3/4 已過時，唔好照跟）**：session 尾 SK 指出 Fix E 朝早 06:45 已煙測完——debug.log 實錘 `renderCards item=minecraft:iron_pickaxe role=output scannedCats=2 foundOutput=2` → `toolCards emission=2 cardsOut=2`（2 張合成卡）→ `usesSupplement count=3`（補 3 張用途卡、全有文字錨）＝**5 卡期望 PASSED**。item 27/28 嘅「未 smoke」係 05:19 舊資料誤導（06:45 煙測喺前一個 session 尾段已發生）。
7. **真正狀態（git 實錘 09-09）**：0.2.0 release `5192862`（09:16 bump + README + CurseForge description）→ CF desc top-mod style remake `6f8e5b2`（09:46）→ skill-system drop-in v1 plan `fd7d314`（10:13）**已 commit 已 push**；MC HEAD = `dec1471`，**ahead origin 淨低 1（dec1471 未 push）**，working tree clean。skill-system plan（內文已引 friend-wishlist 教訓：武刃 = data-layer 唔係 skill 層）**未 review**。
8. **等 SK 揀（18:39 列出 4 選項，未拍板）**：① push `dec1471`（docs 一句嘢）② review skill-system plan ③ Arch-3 round（askNoTools catalog merge——設計已收斂，等 go）④ JARVIS alerts.py ctypes fix（等批）。**09-09 00:15 SK 問「what is 3?」** → 解釋 Arch-3（3a askNoTools 食 `recipeCardLines` ⊕ merge full dump 唔 replace，保 machine/REQUIREMENTS/獲取；3b shot0 毒化 fix 方案 A；3c purpose 加厚 YAGNI 暫緩）——**淨問答、冇新工作**。JARVIS ONE 自身無 code 改動（全部 MC repo）。

---

## 今日（2026-09-07 session）—— MC 線：R5.3 真機煙測 + 3 bug 實錘 + R6 cursor fix in-flight（JARVIS ONE 無 code 改動）

> Discord session 03:0x：SK「read hand off」→ 發現 **jarvis-pc HANDOFF 過時**——實際 MC main 已到 `21e119f`（09-07 01:00，全部 push origin），repair_lookup（Wave23 `4f860fa`）+ R3-R6A + R4/R5/R5.x 卡顯示架構終局早已完成 deploy（現役 jar R5.3 sha `30aaa548`）。**真實權威 = MC repo 自己嘅 `.hermes/plans/HANDOFF.md`（09-07 02:13 更新）**，唔係呢份。

1. SK 煙測 R5.3（AI_test_NFWC_DIM 真機）發現 **3 bugs**（debug.log 03:07-03:10 實錘）：
   - **Bug 1 DSML fullwidth leak**：武刃題 reply 洩漏 `<｜DSML｜tool_calls>` block——model 用 fullwidth vertical line U+FF5C 做分隔符，AskToolLoop/AskReplyScrub 全部 regex 淨識 ASCII `|` → detect/parse/scrub 全 miss → 原樣出 UI（ASCII 版會被攔截，所以「randomly」）
   - **Bug 2 autoEmission 鏡像冇合併**：鐵劍題 model 0 call tool → autoEmission fallback 出 2 張鏡像卡（工作台+動力合成器）——`coalesceMirrorEmission` 只喺 RenderRecipeCardsAskTool（tool path）行，`AskService.autoEmitCatalogCards` 冇行
   - **Bug 3 autoEmission 冇 INPUT/uses 卡**：同一題文字有「怎么用…火舌剑」section（24 條 as-material recipes 掃到）但 autoEmission（role=output count=2）淨出 OUTPUT 卡、0 張 uses 卡——catalog 似淨 OUTPUT + NONE branch output 揀到就 skip uses
2. 診斷齊 → instruction `%TEMP%\cursor_r6_smoke_fixes.md`（Fix 1: pipe char class `[|｜¦│]` unicode escape；Fix 2: autoEmission return 前 coalesceMirrorEmission；Fix 3: trace forItemParts 後補 INPUT 卡 + reply 有用途 section 就 output+uses 出卡，cap≤4）→ **cursor dispatch 03:3x**（2026.09.02-c22c1a3 hidden background，report `%TEMP%\cursor_r6_report.md`）
3. **MC repo 唔好掂**（cursor 工作中）；收 report 後自己 grep 驗證 + checks + 雙樹 compile + build jar class bytes → deploy → SK 再煙測
4. 教訓：jarvis-pc HANDOFF 唔係 MC 線權威——跨 project sync 有 lag，MC 工作 session 睇 MC repo 自己份 HANDOFF + plans 最新 mtime

**（續 03:35–04:30，同 session 流延續——R6 收斂 + R7 in-flight；05:47 cron 核實補檔）**

5. **R6 收斂**：cursor report 收咗 → grep 驗證 → **commit `7fb771a`**（MC repo 03:45「fix(ask): R6 — fullwidth DSML tool-xml scrub + autoEmission mirror coalesce & uses cards」）+ deploy
6. **SK 二輪煙測（04:16，R6 jar）→ 2 條新 root cause**（debug.log 實錘）：
   - **卡黐埋（stuck together）**：model 答 full 題寫 numbered steps 但唔寫 `[card:N]`（淨寫 prose「（见下方卡）」）→ 全部 emission 卡行 fallback——`findEmissionInsertIndex`（RecipeEmbed L900-946）每張都回同一 section 尾 index → `skipCardsAfter` 令後續黐實；needles（L980-1015）得 category/catalyst/craft aliases，**冇 output 產物名**（uses 卡 category 係「自動合成」，model step 寫「水果刀」→ needle miss）
   - **Missing 卡（火舌劍）**：`RenderRecipeCardsAskTool` L99-101 uses 24 張 matched 直接 `subList(0, PER_CALL_CAP=6)` 截頭——冇代表性/diversity 排序，排第 7+ 永遠唔出；auto path（total 4、uses≤2）更緊
7. **cursor 3-POV design discussion**（`%TEMP%\cursor_discussion_report.md`，04:29，16.8KB）判決：**renderer disperse ≫ prompt**（weak model 靠唔住）；黐埋 = fallback insert index 問題、missing = emit pick/cap 問題——**兩個獨立問題，分散 fix 修唔到 missing**；ship 順序 = ① disperse + output needles → ② lang 措辭 → ③ uses pick/mention
8. **R7 dispatch 04:30**（instruction `%TEMP%\cursor_r7_fix.md`，Part A/B/C 兩樹 lockstep）：
   - Part A RecipeEmbed：A1 `emissionMatchNeedles` 加 output hover/token needles（L1168-1186 `card.outputs()`→`getHoverName()`）；A2 `disperseUnplacedEmissionCards`（`cardsOnStep[]`：score>0 → 最高分 + 最少負載 step；score=0 → round-robin 最少負載；`findEmissionInsertIndex` 保留做 helper）
   - Part B RenderRecipeCardsAskTool：uses role 改用 private `pickUsesWithCategoryDiversity`（per-category ≤2、原序；output/upgrade 照舊截頭）——唔共用 JeiRecipeCards helper（coupling）
   - Part C lang ×6（zh_cn/zh_tw/en_us × 雙樹）：4 keys 改「獨立 numbered step + 行尾 [card:N]、禁 prose-only「见下方卡」、唔寫 N 都得（系統分散）」；刪「下方兜底」教法
   - cap 數值全部唔郁（SCAN_CAP=24/PER_CALL_CAP=6/MAX_CARD_EMISSIONS=8/auto 4）
9. **⚠️ Cron 核實（05:47）**：R7 cursor **04:39 已出 report**（`%TEMP%\cursor_r7_report.md`，Part A/B/C 兩樹實作齊，有 file:line；**NO commit、python checks 未跑**——agent shell blocked，report 要求 Hermes 跑 `tests/check_card_tool_emission.py` + `check_recipe_embed.py` + `check_ask_tool_loop.py`，如 assert 舊「下方兜底」措辭就要更新 assert）；**session 04:30 idle，report 未收**。MC working tree modified：`RecipeEmbed.java` + `RenderRecipeCardsAskTool.java` + lang ×3（兩樹）+ `code_change_log.md`；MC HEAD = `7fb771a`
10. **下次 session 開頭（照 09-07 03:35 HANDOFF 嘅下一步）**：收 R7 report → 跑 3 個 python checks（repo root）+ 雙樹 compile `--rerun-tasks` → commit R7 → deploy jar → SK 煙測（文字↔卡分散 + 火舌劍有冇出）；MC repo 自己 HANDOFF 未同步 R6/R7 tail（以本節為準，同 repair_lookup 尾先例一致）

**（續 07:2x–07:4x，同 session 流延續——R7 收斂 deploy + 煙測 bug + MC 線暫停）**

11. **R7 收斂**：3 python checks 跑（`check_card_tool_emission` 原 fail = check 過時 assert 舊 `placed[i]` loop → 更新為 `disperseUnplacedEmissionCards` → PASS）→ 雙樹 `jar --rerun-tasks` BUILD SUCCESSFUL → class bytes 驗證（4 新 symbols 兩樹 jar 齊）→ **commit `0fd90cd`**（12 files +551/-59）→ deploy AI_test_NFWC_DIM（backup `.bak-r7-*`；jar sha `7b577e`）
12. **SK 三題煙測（07:28-07:29，debug.log 實錘）→ 用途卡 missing bug**：
    - 鐵鎬/鐵劍題：model 淨 call `render_recipe_cards(role=output)`（攞工作台+動力合成器 2 張 mirror 卡）**冇 call role=uses** → 用途 prose（火舌劍/水果刀/堂吉訶德等「作为材料」step）有文字冇卡 → **R7 Part B diversity pick 冇機會行**
    - 武刃題：model 有 call uses（攞到「武刃→金?」卡）但將 `[card:1]` marker 錯配喺「武器使用」step 尾 + final prose 濃縮到一句（獲取 section 消失）
    - **Root cause**：tool path（model 有 call 但淨 output）冇 deterministic 補 uses 卡機制——R6 autoEmission 補卡只 cover model 0-call path；用途卡出唔出仍依賴 weak model 自覺（SK 09-05 唔接受嘅 not-every-times 行為）
13. **⚠️ MC 線暫停（SK 07:4x 指示「delete mc line for now」）**：R8 **未 dispatch**、未設計——下次 session 開頭 = **cursor 3-POV design discussion**（定 tool path deterministic 補 uses 卡架構；照 SK 2026-09-06 重複問題規則——卡顯示已 R5→R7 連環，先傾根因唔好自己 patch）。MC repo HEAD = `0fd90cd`（ahead origin 未 push，照舊）。煙測記錄喺本節——MC repo 自己 HANDOFF 仍停喺 02:13。
14. **抖音線（同 session side quest）**：douyin-absorption-biweekly force run（SK 批 bypass gate）完成——**315 條 baseline**（首次真 baseline；舊 scan 漏 note/冇 hashtag 卡，+117 多數係 coverage gap）；improve plan R1/R2/R6 **三項 SK 全批**（Hermes 執行緊，見 media_import）
15. **Hermes Vault MVP 建成（SK 全流程：deep-read 4 片 → design → review 2 輪 + online research + cursor review → full plan → 再 review → go）**：`Documents\Hermes_Vault\`（00_收件箱 + 03_收藏吸收 6 條 notes + MOC + README）；content-absorption skill P4/P5/Outputs/Refs/Noise patch（per-item vault notes）；douyin cron prompt update（notes→vault，raw/plan 留 media_import，backup 喺 media_import\cron_prompt_backup_20260907.txt）；AGENTS.md 加 Vault 投餵規則（SK「記低/存起」→ inbox）。**成功標準 2-3 週**：Agent ≥2 次 grep vault 避免重複提案 或 SK ≥1 次問「收藏過 X」有答案——否則 flip 砍 vault。Design/plan/review records：`media_import\2026-09-07-hermes-vault-{design,implementation-plan}.md`
16. **抖音批量 deep-read 第一批完成（SK「start read」）**：AI 89 條 triage → **70 條入 vault/03**（31 caption + 39 ASR——26 video 全 ASR 處理）+ 5 vault 重複 + 14 低價值唔入。**Vault 03 共 76 條 notes**（absorbed 27/deep-read 49）。確認大量 practice 已 cover（skill mgmt/code review 兩次/驗收/adoption gate/llm-wiki/vault 概念）；新參考 5 項（影響分析、RAG anchor、跨 model agent、Codex vs CC 分工、反迎合 prompt）記錄喺 douyin_import_notes.md。**未做**：other 25 條 triage、LOW 14 條記錄、improve plan 更新、新 gap 嘅 skill patch（如有）——下次 session 續

**（續 14:5x–15:0x，同 session 流延續——other-25 triage 補完，SK「go」）**

17. **other-25 triage 完成（15:0x）**：逐條 detail-API verify → **發現 5 條係 caption cross-card bleed 漏網 AI**（classified 卡面 caption 配錯，keyword 分類誤判 other）：
    - 2 條高價值已補入 vault/03（**Agent Loop 4 坑保險** 7682456452490189179 note 6 圖全 deep-read——坑1 冇停止條件/坑2 自治冇驗收/坑3 目標不可檢查/坑4 超單 loop 邊界，總結運行前 5 問——同 weii.dev 一致確認性吸收；**AI 編程三行 config 慳六成** 7682265273868487653 video ASR 65s——model 檔位分檔 + 思考額度 30000→10000 + gate 文化，SK 資源敏感直接相關）
    - 3 條 LOW 記錄唔入庫（Linux CLI 5 tips、AIPM 新聞、馬斯克 AI 睇市場疑似 hype）
    - 其餘 17 條真生活/廣告/娛樂全部唔入庫；7480123072914246946 API 全 fail（疑似刪）
    - **LOW 14（AI 內冇 note）id 全記錄**入 douyin_import_notes.md
18. **分類修正**：douyin_classified_20260907.json + douyin_ai_batch.json 5 條 other→ai（ai 94/other 20/noise 3；backup .bak-*）；improve plan 加 caption-bleed 實錘教訓（下次 cron 增量逐條 API verify + batch scan 存疑抽樣）；Vault 03 = **78 notes**（absorbed 29/deep 49）+ MOC 79

**（續 15:3x–15:5x，SK「hand off, then mc line」——今日 tail 收口）**

19. **SK 問「agents.md 要唔要加？」→ 結論唔使**（caption-bleed 係 pipeline 操作知識，已落 skill/plan）；但 **content-absorption skill 加 Exclusion ledger 規則**（triage 排除 item 一定要記 id + 一句原因——09-04 + 09-07 兩次「N 條冇 id」重複坑；分類/吸收前 detail-API 驗證真 desc 回寫 classified）
20. **SK 問「有冇 logic 可以用？」→ 對照 9179 Agent Loop 5 問 vs 我哋 config**：發現 `tool_loop_guardrails.hard_stop_enabled: false`（默認淨 warn 唔停）→ **SK「open it」→ 已開 true**（hermes config set，backup config.yaml.bak-20260907_153839；規則：exact_failure 5 / no_progress 5 / same_tool_failure 8 硬停，warn 2/2/3 照舊）——Agent Loop 坑1 工具層保險落地
21. **SK 拍板：「hand off, then mc line」——MC 線重開**：下一步 = R8 cursor 3-POV design discussion（tool path deterministic 補 uses 卡；根因見上 §12——model 有 call tool 但淨 output、用途卡出唔出靠 weak model 自覺；SK 2026-09-06 規則：卡顯示已 R5→R7 連環，先傾根因唔好自己 patch）

**（續 09-07 17:40–09-08 05:1x，跨午夜 session 流延續——R8 ship + Fix C/E 收斂；JARVIS ONE 無 code 改動，全部 MC repo）**

22. **R8 + Arch-3 unified design discussion 收斂**（cursor 3-POV read-only，report `%TEMP%\cursor_r8_arch3_unified_report.md` 17:31，抽樣重驗證通過）：**無硬衝突 → 分開 commit、R8 先行**。R8 = AskService 雙出口（async/sync）插 `supplementMissingUsesCards`——結構閘：emission 無 uses-role ∧ catalog 有 `isInputUse` ∧ (PURPOSE ∨ isPurposeQuestion ∨ replyHasUsesSection) ∧ maintIntent≠REPAIR；cap 2 + diversity + coalesce + log `usesSupplement count={}`；promote `pickUsesWithCategoryDiversity`（唔盲 copy）。Arch-3（後置）：3a `askNoTools` 食 `recipeCardLines` ⊕ merge full dump（**唔 replace**，保 machine/REQUIREMENTS/獲取）；3b shot0 毒化 fix 揀**方案 A**（seed 空 content 保留 fingerprint，risk 細；唔做 B 富裕覆寫泛化）；3c purpose 加厚 YAGNI。明確唔做：RecipeEmbed 改動、AskToolLoop 強制 uses call、role-agnostic 補卡框架、full rewrite builder。
23. **21:42 SK「can u review it in diff pov」（engineer/player/poor player/youtuber + 中立裁判）**：判 R8 照 ship + **amendment**——supplement 觸發但正文無 uses heading（`replyHasUsesSection=false`）時自動加一行 lead-in「用途：」先出卡，杜絕孤兒卡（SK 09-05「每張卡要有相鄰文字」；零 token、唔使 model）→ SK「ok」22:27 → R8 實作 dispatch 22:29（含 amendment）。
24. **R8 收斂 6 commits（MC repo，雙樹 lockstep；HEAD = `0f06d9a`，working tree clean，ahead origin 6 未 push）**：`3812a6a` R8 supplement + orphan-card lead-in → `d10ff86` skip when emitted already has uses → `5fd561b` smoke fixes（needle-bias uses pick + line-anchored uses-heading gate）→ `e9c727d` **Fix C**（role=uses catalog-first：[RECIPE_CARDS] 序 catalog 卡排頭）→ `b75c6cf` supplement cap follows prose needle mentions（≤4）→ `0f06d9a` **Fix E**（catalog 有 input 卡 → 淨出 catalog、唔 diversity fill）。
25. **SK 煙測輪（debug.log 實錘）**：Fix C 版 04:38「even worse now」——model 今次**自己 call uses**（上次 0-call）→ Fix C 3 catalog 卡排頭（堂吉訶德/立方捕手/初學者法術書 ✅）但**剩位 diversity fill 3 張孤兒**（ritual/召喚祭壇）返嚟（toolCards emission=8 cardsOut=8）→ root cause：Fix C 剩位 diversity fill = 殘餘孤兒源；兩條 path 應一致 = model call uses → catalog 卡；0-call → supplement needle 卡。
26. **Fix E dispatch 04:41**（instruction `%TEMP%\cursor_r8_fixe.md`：`pickUsesPreferCatalog` catalog 非空 → 淨出 catalog 卡、cap 內唔 diversity fill；catalog 空先 fallback `pickUsesWithCategoryDiversity`）→ cursor 完成 commit `0f06d9a` → **jar 04:52 deploy**（現役 `packai-0.1.16+mc1.19.2-forge.jar` sha `e187a0ce`）→ **未 smoke**。
27. **05:19 收斂（SK「check it」→ 自行驗證）**：擴 standalone mirror harness `%TEMP%\r8_supplement_mirror_test.py` 蓋 tool-path picker（`pickUsesPreferCatalog` mirror，新增 E1-E6：catalog-only／diversity fallback／JEI matched subset／cap truncation／prompt 序／supplement needle 路唔受影響）→ **29/29 全過**——邏輯層驗證完成（mirror 只證 LOGIC，real runtime 要 in-game）。
28. **下次 session 開頭**：SK restart MC 煙測 Fix E jar（問「铁镐有什么用途、配方和取得方式？」→ 期望 5 卡：2 合成 + 3 用途全對應 prose、無孤兒）→ PASSED 先 push 6 commits（ahead origin）→ Arch-3 round（3a askNoTools catalog merge + 3b shot0 方案 A）→ R8b（autoEmit uses 支線改共用 diversity helper）可選。MC repo 自己 HANDOFF 停喺 02:13 未同步 R8/Fix C/E tail（以本節為準，先例一致）。

---

## 今日（2026-09-06 session）—— MC 線：附魔 Wave 7→22 agentic `enchant_lookup` pivot + `repair_lookup` plan（cursor dispatch 已完成）（JARVIS ONE 無 code 改動）

> Discord session：MC project（super_minecraft_AI_player）。詳細交接喺 `super_minecraft_AI_player\.hermes\plans\HANDOFF-2026-09-06.md`；以下係跨 project 同步摘要。

1. **Keyword 拆字 bug 修復**：「能附**什**么**魔**」= 附/魔唔連續 → `contains("附魔")` FALSE → enchant hook 靜默失效 10+ waves（W8-W17）。W18 用 附…魔 distance≤4 修好（cursor second opinion 睇穿）。
2. **[ENCHANT_TABLE] 唔到 model 實錘**：AskEngine `jeiForLlmSlim()`（native-tools path）淨重建 card catalog、丟 merged jei → W21 slim prepend 修；W22 再 pivot：**SK 指明 agentic harness（Hermes/DeepSeek 式）——唔預注入，model 自 call tool**。
3. **Wave 22 = on-demand `enchant_lookup` native tool**（雙樹 EnchantLookupAskTool：schema 淨 item optional；registry canEnchant 掃描 18 cap；EMPTY/error 人話 message；LlmClient [TOOL_MISS] fallback）；移除 [ENCHANT_TABLE] 預注入（AskService ×2 + AskEngine slim）；TOOLTIP_HINT 保留。現役 jar sha `a324ce14`，~26 commits ahead origin（未 push）。
4. **實測教訓（入咗 skill）**：EMI vs JEI viewer divergence（PackAI 讀 JEI、SK 睇 EMI——anvil/enchant 行唔會喺 JEI manager；用 registry canEnchant 計）；debug.log Big5 encoding；SLIM path 丟 hints。
5. **Open**：SK 煙測 wave22（model 會唔會自 call enchant_lookup）；cursor review（proc 4d3b12f2ef9f）結果要收；quest relabel 冇 fire（cat title=「武刃」非「任務書」，要 uid 判斷）；claim/禮包句 data gap（held NBT capture）park；T8 review 幾輪 + T10（0.2.0 push + CF release）未做。

**（續 03:32–05:43，同 session 流延續——repair_lookup 新線）**

6. **T8a cursor review 收咗（proc 4d3b12f2ef9f）= PASS + 4 findings**；P1 決策 = **A tool-only**（SK 拍板）。**wave22c P2 fixes ×3**（empty return `""`、bad item resolve 唔 fallback focus、刪 dead enchantHintText）→ commit **`ecbd75f`**（03:37）→ jar **`32c97a8b`** 03:39 deploy（backup `.bak-033954`）。
7. **03:43 smoke（武刃維修題 maint=1）**：model 冇 call enchant_lookup（正確——維修題行 quest/JEI card，答「奥术砧 保養」）；但暴露 **repair 資料面缺口**：答唔到「鐵砧 + 鐵錠」材料修復，SK 遊戲實錘武刃+鐵錠放鐵砧修到。
8. **`repair_lookup` plan（MC `.hermes/plans/2026-09-06_repair-lookup-agentic-tool.md`）**：根因 = JEI `AnvilRecipeMaker` repair recipes **硬編碼 vanilla**（mod 物品永遠唔出現，唔係 PackAI collect 問題）→ 新 agentic tool（仿 enchant_lookup）；adversarial r1（7:3）→ independent r2 FIX-FIRST：**B1 blocker**（LLM 見到嘅 schema 源 = `LlmClient` per-name table（toolSchemaDescription/Required/toolMissNote），**唔係 tool 自己 description()**——要 patch 三處）、**B2 major**（fake AnvilMenu 唔使——javap 證 `Item.isValidRepairItem()` public predicate worker-safe，主線改 predicate）、M1（`AskJeiClient.summarize` 有 client-dispatch precedent）→ SK「go」（05:42）→ cursor dispatch `proc_09f525cf6c9a`（instruction `%TEMP%\repair_lookup_instr.md`）。
9. **Cron 核實（05:47）：cursor 已完成，working tree 有** `AnvilRepairHint.java` + `RepairLookupAskTool.java`（雙樹）+ `tests/check_repair_lookup.py`；`LlmClient.java` 雙樹各 4 處 repair_lookup ref、`AskToolLoop` CAPABLE+QUERY 註冊齊（search_files 實錘）——**未驗證/未 commit**（python checks + 雙樹 compile --rerun-tasks + jar class bytes 未跑）。
10. **⚠️ 跨 reset 交接**：session 尾 cursor 完成通知未收（proc 已 exit，output 喺 cron 唔到）；MC repo HEAD = `ecbd75f`，**32 commits ahead origin（未 push）**；MC repo 自己 HANDOFF-2026-09-06.md **未同步** repair_lookup tail（以本節為準）。
11. **Open（更新）**：驗證 repair_lookup（grep LlmClient ×3 + checks + 雙樹 compile）→ commit → deploy → SK 煙測（武刃怎么修 → repair_lookup + 鐵砧鐵錠，與奥术砧途徑並存）；SK 煙測 wave22 agentic enchant（「武刃能附什么魔」——03:43 實測係維修題，唔算）；quest relabel（uid 判斷）；claim/禮包句 data gap（park）；T10b probe 清理；T8 正式 review（Pass1/independent 幾輪）；T10（0.2.0 push + CF release）。JARVIS 線待辦不變。

---

## 今日（2026-09-05 session）—— MC 線：P1+P2 Public AskTool Plugin API 完成 + 煙測 card-marker 三層 bug 修復（JARVIS ONE 無 code 改動）

> Discord session：MC project（super_minecraft_AI_player）。詳細交接喺 `super_minecraft_AI_player\.hermes\plans\HANDOFF-2026-09-05.md`；以下係跨 project 同步摘要。

1. **Public AskTool Plugin API（Scope Y）commit `92f830c`**（61 files +1009/-268）：`api/` package（5 檔 byte-identical 雙樹）＋ `AskToolLoop.registerExternal()`（4 值 RegistrationStatus）＋ bus transport adapter（forge JavaExec runtime 實證 stored/REJECT_DUP/REJECT_RESERVED）＋ `registerExternal()` try/catch → REJECT_BAD_SCHEMA。P2 independent reviewer PASSED。**修埋 pre-existing assert bug**（AskToolLoopCheck :467 latent fail 自 2026-09-02，`additionalProperties` 應為 false）。
2. **煙測發現 card-marker 三層 bug（AskCardFallback trust/fallback gate，非 P1/P2 引入）→ 4 commits**：
   - `1fdc089`（fix 6）：bullet 材料行 separator 唔 match `N.` regex → trust gate 唔 trust。修：`separatorHasContent` 放寬任何內容行。
   - `060982d`（fix 7）：model 寫漏 USE markers → gate 見 ≥2 interleaved 就 trust → fallback 冇行。修：coverage gate（raw count ≥ needed）。
   - `047ae6c`（fix 8）：raw count 俾 duplicate markers 呃（reviewer S1）。修：distinct marked-index set `containsAll(needed)`；**off-by-one parse bug**（`[[recipe_card:0]]` double-closer `]]`，`rindex(']')` 切到 `0]` → catch 靜靜空集——Java+Python 都有，修 `rindex(']')-1`）。
   - `5aa65b2`（fix 9）：smoke 05:21——model 寫啱 0/1/2/4 markers 但漏 card 3 → 舊邏輯全部 strip+re-cluster → 連啱嘅 markers 搬走、卡 cluster 去 prose 尾。修：**partial-trust**（clean markers + coverage 唔夠 → 保留 reply 只補 missing）+ **findBlockEnd 遇 blank line 停**（唔吞 section footer prose）+ block_start 推去 method line `\n` 後。
   - `31e4baa`（more tests，SK 要求）：full-fallback+prose footer、missing-OUTPUT partial、GET prose footer。
   - 驗證：`check_ask_card_fallback OK` + 85 python checks（3 pre-existing）+ 雙樹 compileJava（--rerun-tasks）；fix 6+7 過 independent reviewer（deleg_cfeb913f）；**fix 8/9 + tests 未獨立 review**（P3 前建議補）。
3. **⚠️ 重大教訓（已入 skill `cursor-cli-integration`）**：fix 7 嘅 cursor process（3 PID）report 出咗但**一直冇退出**，background 讀返 fix 7 指示繼續改 file，喺 commit fix 8 後將 forge source 覆蓋返 fix 7 版 → 第一次 deploy 咗污染 build（jar 內冇 fix 8 method）。處理：kill 殘留 process → `git checkout HEAD --` restore → rebuild。以後：dispatch 後確認 process 真死、build 後驗證 jar class 內容、gradle 要 `--rerun-tasks`（configuration cache 假象）。
4. **Git：6 commits ahead origin 未 push**（92f830c → 1fdc089 → 060982d → 047ae6c → 5aa65b2 → 31e4baa）。**CF 仍係 0.1.16 舊 code**（未上傳任何 P1/P2/fix）。
5. **部署狀態**：AI_test_NFWC_DIM instance mods/ = `packai-0.1.16+mc1.19.2-forge.jar` sha `4f5b8171`（fix 9）——等 SK restart game 煙測「铁镐怎么用」。
6. **下次優先序**：SK 煙測 → PASSED → 補 independent review（fix 8/9/tests）→ P3 全套驗證 → P4（0.2.0 lockstep bump + push + CF release）→ **Hold project**（SK 明示做完所有 todo 先 hold）。JARVIS ONE 線待辦不變（LHM autostart 等真 reboot、Phase 2 觀察、G 人手實測等 mic）。

---

## 2026-09-05 00:5x — Pack AI：Public AskTool API plan ADOPTED
- 4 輪 adversarial review 收斂：r4 **8:2 execute**（Scope Y：registerExternal + RegistrationStatus；register() keep-gate；ask_player 死碼移除 0.2.0 wave）
- 執行未開始（P1 未郁）；plan 檔喺 MC repo `.hermes/plans/2026-09-04_public-asktool-plugin-api.md`
- 同日已完成：0.1.16 release（push/CF files 8807474/8807475/description 更新 ×3 rounds）+ round-5 smoke PASSED（Fix E）

## 2026-09-04 夜 session 2 — Pack AI release 0.1.16 完成
- MC repo：round-5 smoke PASSED（Fix E trust gate 實錘 before==after ensureCards）→ push 10 commits（main=d5bdad1）；Fix 1-3 d57d39d / Fix E 4bf351d / batch dc9b163 / mirror 07a7522 / release d5bdad1
- CurseForge：0.1.16 兩 line auto-upload（file 8807474/8807475）+ About description 更新（CDP cookie PUT 200）——流程已入 MC skill `release-curseforge-publish-2026-09-04.md`
- 坑：CF description 要 login cookie（profile ~2 週過期）；chrome_profile single-instance trap（taskkill 用單 slash）；MSYS Big5 tasklist 會假報 0 → 用 powershell ps1 check
- 待辦：GitHub Release tag（SK 未要求）

## 今日（2026-09-04 夜 session）—— MC 線：round-3 真機煙測解碼（跨 project 同步，JARVIS ONE 無 code 改動）

> Discord session 17:4x：SK 先叫我「check history and hand off first」。呢段 = MC round-3 煙測（jar `462ffbdf0d` / packai 0.1.15）結果補檔，詳細喺 `super_minecraft_AI_player\.hermes\plans\HANDOFF-2026-09-04.md`「夜晚更新」section。

1. **位置層 smoke PASSED**：14:51 真機 ask「铁镐…用途/属性/获取方式」→ debug.log 實錘 `ensureCards` after：output 卡 0/1 正確跟「1. 工作台」「2. 原版通用获取」method line；input 卡 2/3/4 全部聚喺「任务方面」後、「【来源】」前（Fix D 生效，冇再散落 USE 行）。兩張截圖 = 同一答案卡上下部分。
2. **剩低 = 文字 vs 卡內容一致性**（唔係位置）：model tool round `jei_lookup(INFO)`/`acquire`/`quest_fetch` 全 TOOL_MISS → model 以為包內冇配方，答 vanilla 通用知識並寫「本包未见铁镐参与特定配方」，但系統照樣 attach 咗 5 張卡 → 畫面文字話冇配方、下面又出 3 張用作材料卡，矛盾。已開 anomaly 1/2/3 等 SK 揀方向（1 = jei_lookup 空 vs collector 有料 分歧；2 = 方法 2 語義唔夾；3 = input 卡位置要唔要黐實材料行）。
3. **下次優先序更新**：MC 線 = SK 揀 anomaly 方向 → confirm 位置 PASSED → push 5 commits（`3ba403c`..`e7c58ee`，已過 independent reviewer）+ uncommitted 8-file 雙樹改動（怎樣 variant + Fix D + AskService debug log）commit。Jarvis 線待辦不變（LHM autostart 等 reboot、Phase 2 觀察、G 人手實測等 mic）。

---

## 今日（2026-09-04 凌晨 session）—— MC 線：卡片位置真正 root cause 修復（主 session 轉咗 MC project）

> Discord session 9/3 17:51–9/4 03:52：讀 jarvis-pc HANDOFF 後 SK 揀 MC 線（「since I can't reboot now, and I didn't buy my mic, so 2」）。**JARVIS ONE 本身冇 code 改動**——以下係跨 project 狀態同步（先例：9/1「主 session 轉 MC」、9/2「跨 Project 盤點」）。

1. **MC packai 卡片位置 root cause 已修**（super_minecraft_AI_player repo，commit `e7c58ee`）：真正原因 = `resolveAttach`（RecipeCardsMode）reorder 卡 list，但 `ensureCards` 寫嘅 marker index 係 collected index → renderer `cards.get(N)` 錯位（**index-space mismatch**，唔係之前一路修嘅 method-line 重排）。修法 = resolveAttach 唔再 reorder（return raw 原序），`pickIndices` 只做 empty-guard。驗證：雙樹 compileJava 綠、checks 85 pass + 3 pre-existing fail（無新增）、harness `tools/card_placement_test.py` 收斂、independent reviewer PASSED + 自己 Pass1/Pass2。
2. **MC main 而家 5 commits ahead origin**（`3ba403c` Numen teaching → `c75077a` 全形冒號 → `dbc73e6`/`52a6687` section-aware → `e7c58ee` index mismatch），**全部未 push**——等 SK 真機煙測（jar `1e09446a`：問「铁镐怎么合成」「硫磺花蜜」確認卡片真機跟返 method line）PASSED 先 push（SK 規則）。
3. **詳細交接**：MC 專案自己嘅 `super_minecraft_AI_player\.hermes\plans\HANDOFF-2026-09-04.md`（root cause 機制鏈/驗證/待辦/坑）。jarvis-pc 唔重複。
4. **下次 jarvis session 優先序更新**：MC 線唔再係「Numen 對照位 + slim regression」（已完成）；而家 MC 線 = **等 SK 真機煙測 → PASSED 先 push 5 commits**（可選：多餘卡 filter 後保持原序）。Jarvis 線本身待辦不變：LHM autostart 驗證（等真 reboot）、Phase 2 自然觀察、G 人手實測（等新 mic）。

---

## 今日（2026-09-04 session）—— Douyin 全量深讀 review（99 條 AI）+ 3 項落地

**Douyin 收藏全量 review（SK「check all + review every single one that about code/AI/skill」）**
1. v2 scan 99 條 AI/coding 全部有判斷：54 條 ASR 深讀（yt-dlp/detail-API fallback + faster-whisper，35+19+16 retry 三批）+ 7 條 NEW 上次已 ASR + 38 條 caption-clear 直接判斷；notes `%TEMP%\douyin_full_review_notes.md`（36 項 A 類分析）
2. **核心結論（adversarial 8:2）**：冇大型新嘢要改系統——我哋 stack 已行業界最佳做法（Karpathy 4 原則/Codex 8 最佳實踐全部對應返已有）；真 actionable 得 2 細項
3. **A7 驗證**：Karpathy 70 行 = forrestchang/andrej-karpathy-skills（70.8K★ 4 原則）——我哋 AGENTS.md 已內化，冇 gap

**SK 批咗 3 項落地（「go, and our mod is a minecraft side's harness, so we can use so AI suggestion」）**
4. ✅ `llm-tool-calling-reliability` skill 補 §7 工具調用驗證層（參數驗證/response parse 唔吞錯/失敗唔繼續推理/loop guard/tool 選擇驗證）——源自 7680499853431950655 Agent 事故片
5. ✅ 主契約 `C:\Users\skps9\AGENTS.md` 加「Agent 接力／Escalation 規則」（2026-09-04）——交接格式 + 連續失敗 3 次停止 + 失敗唔好當成功；✅ 源頭 `Code_Project\Hermes\AGENTS.md` 已同步（SK「try again」批咗，diff IDENTICAL 驗證；該目錄非 git repo，純檔案同步）
6. ✅ Numen（MC-side AI harness）深睇 → 對照已寫入 `super_minecraft_AI_player\.hermes\plans\HANDOFF-2026-09-02.md`「外部參考：Numen」section——Teaching feedback loop / prompt-lean skills / tool 排序穩定 3 個可考慮位（下次 MC session 經 cursor-agent）

**下次 session 優先序**：Jarvis（REMAINING_WORK sync + test_stt_stats baseline fail + LHM 開機 tray 驗證 + Phase 2）→ MC（Numen 對照位 + slim regression + commit/push）最後

---

**規則制度化（SK「make sure we hand off before start a new session」）**
1. **Session Hand Off 規則已寫入主契約** `C:\Users\skps9\AGENTS.md`（§Session Hand Off 規則）+ 源頭 `Code_Project\Hermes\AGENTS.md` 同步（diff IDENTICAL 驗證）——上次 approval timeout 失敗，今次 SK「try again」批咗
2. **C2 補標完成**：Prime Agent ❌ 排除（adversarial 8:2）已入 HANDOFF（commit `d2ed92e`）——C2 全完（3 個都唔裝）

**Content 工作（優先序下一站）**
3. **Bilibili adapter 完成**（`content-absorption/references/adapters/bilibili.md` stub → API-first）：fav folder/resource list endpoint 已 research + **公開夾實測通過**（code 0、無需 WBI）；SESSDATA prereq、WBI `v_voucher` fallback、browser fallback、yt-dlp `bv*+ba/b` 坑齊；SCHEMA 覆蓋矩陣 bilibili = full coverage（SK 帳戶 scan pending）；SKILL.md reference 描述同步
4. **Douyin v2 scan 完成**（SK「go」+ activity gate 許可）：205 條（190 desc）、**url/id capture gap 已閉**（card-boundary walk 配對 `a[href*="/video/"]`，SCHEMA+douyin adapter 已更新）；14 條新（7 AI）、22 條舊冇咗；產物喺 browser-use workspace `20260903_142520_35664e25\douyin_favorites_v2(_classified).json`
5. **7 條新 AI 全 ASR 深讀**（yt-dlp/curl+CDN→ffmpeg→faster-whisper base）：notes `%TEMP%\douyin_v2_import_notes.md`；1 噪音（workbuddy 賣課）；真候選 = Sepia

**吸收落地（P4-P7 全行，SK 逐項批）**
6. Plan：`.hermes/plans/2026-09-03_douyin-v2-absorption-plan.md`（過 adversarial：A1 做研究版、A2 降級記錄）
7. **Sepia 深睇 → 3 ideas 入 humanizer**（SK 批「做，入 humanizer」）：`humanizer/references/venues.md`（never-invent/calibrate/deletion/whitelist 4 principles + release notes/PR replies/postmortems/tickets/tech docs 5 venue 組）+ SKILL.md「Professional documents & hard guardrails」section；**唔裝 Sepia**（唔同 skill 生態、fiction 無關）
8. **DSH insight + 相關收藏標記入 REMAINING_WORK**（SK：「some of those video is related to our project's idea…mark it down」）——C1 DSH harness+memory 參考 + C2 Sepia/Easy Vibe/影視颶風 urls + 剔除 list

**下次 session 優先序**：Jarvis（REMAINING_WORK sync + test_stt_stats baseline fail + LHM 開機 tray 驗證 + Phase 2）→ MC（slim regression + commit/push）最後；Content 暫告一段落（下輪 douyin scan 等有新收藏 + SK idle；Bilibili 首次真掃等 SK 帳戶 + SESSDATA）

**坑新增（實測）**：browser-exec cp950 crash 源頭 = 函數參數層 decode `\uXXXX`——code/comment 全 ASCII，JS 用 `String.fromCharCode(0x…)`；douyin yt-dlp 部分 video 403「Fresh cookies」→ detail API（`www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=`）攞 play_addr CDN url → curl 直下 → ffmpeg 抽音訊（workaround 已實測）

---

## 今日（2026-09-03 晚 session）—— Memory 加大 + Jarvis 線收尾（3/3）+ Phase 2 落地

**Hermes 基建（SK 問 memory full → 加大）**
1. Config：`memory.memory_char_limit` 2200 → **4000**、`user_char_limit` 1375 → **2000**（`hermes config set`，backup `config.yaml.bak-*`）——**gateway 已 restart（PID 8960 → 3216）生效**
2. Memory cleanup：筆記 98% → 87%、profile 98% → 88%（刪同主契約重複條目）

**Jarvis 線（HANDOFF 下次優先序 1-3 全清）**
3. ✅ **REMAINING_WORK sync**：A1/A2/A4/B/D3 markers 對齊執行結果 + 底部「現況 sync」待辦
4. ✅ **test_stt_stats baseline fail 修**（commit `6eb5f39`）：根因 = `test_missing_logs`/`test_with_tmp_logs` 漏傳 `repair_log` → run_once 讀真實 `%APPDATA%\Jarvis\repair_log.jsonl`（環境依賴）——cursor 兩輪 + 自己驗證 24 passed + **eval_gate 全綠 hash `0b88e6f6`**
5. ✅ **LHM**（commit `ca9cc37` 內 docs）：task「JARVIS LHM Sensor」存在但 LHM 冇行——Event log 證實 **PC 自 9/2 11:34 未真正 boot**（SK 以為 reboot 過，實際 fast startup/sleep 唔算）；手動 `schtasks /run` 開返（CPU Tctl/Tdie 73.9°C live）。**⏳ autostart 驗證仍然等 SK 真 reboot**
6. ✅ **Phase 2 通用 app detection**：plan（`2026-09-03_phase2-general-app-detection.md`）→ adversarial review 8:2 縮 scope（砍走 watch 泛化——sidecar restart 必 false-ready；dev/media entries——零消費者；game_start_event 鏡像——冇 consumer）→ cursor 兩輪實作 + apply → **獨立 code review PASSED**（security 0/logic 0）+ suggestions 收尾（drift asserts/_TITLE_KW 簡化/lag 註釋）→ parity 16/16 ×2 + py_compile + live smoke 全綠
   - 產物：activity_monitor.py `APP_DEFS`（21 proc + 17 title-kw，語義保留唔合併）+ `detect_running_apps()` + sk_activity.json `apps` 欄位（game only）；backups `.bak-20260903_163254`（原）/`.bak-20260903_165840`（v2）；**shell_app.py 零改動**（review 決定）
   - 文件同步：主契約 AGENTS.md×2、desktop-activity-awareness SKILL.md、windows-desktop-automation references + scripts 舊副本 deprecation header；歷史 snapshot（diagnostics/merged-*）刻意保留

**下次 session 優先序**：
1. **LHM 開機 autostart 驗證**（SK 真正 reboot 後：task onlogon 觸發 → LHM tray + 8085 + HUD CPU temp 有數）——如 reboot 後都唔起先係 bug
2. **MC 線**（Numen 對照位 + slim regression + commit/push——上次 HANDOFF 排最後）
3. **Phase 2 觀察**：SK 實測場景 A-H 自然觀察（`apps` 欄位 + ready alert 零 regression）；Open Q1 flip condition（SK 要非-game alert/HUD 顯示先開 watch 泛化 + dev entries）
4. G 人手實測（等新 mic）+ stt_stats/clarify_stats 等數據 ≥7 日接 cron monitor

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

**C2 新工具 check review ✅（完成 2026-09-03——三個都唔裝）**
1. **WeSight**：❌ 排除——**SK 已試過覺得太差**（2026-09-03）
2. **Browser-BC**（Einsia，436-548★）：❌ 排除——**冇 license** + 7 週無 push + 單一 contributor + 用途係 browser behavior cloning（同 SK stack 唔夾）
3. **Prime Agent**（PrimeIntellect-ai，19.7k★ MIT 活躍 pushed 2026-09-02）——❌ **排除（adversarial 反方 8:2 勝）**：RLM coding harness 同 Hermes 重疊度高（self-improving/skills/subagents 賣點 Hermes 大部分有）；Windows 支援存疑（stable README 宣傳 macOS/Linux first）；「not a security sandbox——以 user permissions 執行 model code」（SK 對安全嚴格）；安裝係 `curl|sh`（契約禁）；又多一個 harness 要 maintain。💡 唯一偷嘅 idea：「agents should compute over data, not read data」——Hermes `execute_code` persistent kernel 已係咁用緊

**下次 session 優先序（SK 2026-09-03 明確；C2 已於 2026-09-03 完成）**：Content（bilibili adapter/douyin A5+）→ Jarvis（REMAINING_WORK sync + test_stt_stats + LHM + Phase 2）→ MC（slim regression + commit/push）最後

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

## 現行狀態

> **2026-09-11 更新（cron 核實，實錘）**：
> - **JARVIS ONE 0.4.10** 跑緊（`hud\dist\JARVIS-ONE-0.4.10.exe`；monorepo）；3 個 .lnk 指新位置
> - **Sidecar 8765**：`GET /health` = `{"ok":true,"wake_on":true}`（09-10 23:4x 重啟，之後一直 UP）；`1bdac68`（alerts ctypes argtypes fix）**已生效**——serve.log 27KB、`int too long to convert` = 0（舊 136MB／370,905 次；備份 `serve.log.bak-20260910.gz`）
> - **Ports**：8765（alerts MCP + /settings）、8770（reply）、8771（media bridge）、8642（Hermes API）、8643（Qwen video，關）
> - **cron**：jarvis-sidecar-health（2m，monitor）、jarvis-daily-self-review（09:00，monitor）、jarvis-session-handoff（每日 05:45）、Gateway watchdog（2m）＋ 一個 disabled 嘅 skill-router-verify 週報
> - **Git**：jarvis-pc `feature/hermes-alerts-mcp` **ahead 3 docs 未 push**（`d8bfe3d`／`bee2e6d`／`06aa722`）；MC repo `1ba048f`（Arch-3/3a）未 push（等真機煙測）
> - **GPU**：2026-09-11 凌晨確診 NVIDIA 驅動 TDR（13 次同簽名）→ SK 決定唔郁（反轉條件見頂部 09-11 section）；incident log `%LOCALAPPDATA%\hermes\state\gpu_tdr_incidents.jsonl`
>
> **以下 2026-08-31 版保留做歷史**（細節已過時——睇上面同頂部日期 section 為準）：

### 2026-08-31 晚 session 尾（歷史）

- **JARVIS ONE 0.4.10**：`jarvis-pc\hud\dist\JARVIS-ONE-0.4.10.exe`（**monorepo**：jarvis-hud 已搬入 `hud/` 子目錄，git 歷史保留）；3 個 .lnk 全指新位置；**2026-09-01 已重啟切換到新位置 + 舊 jarvis-hud 目錄已刪（釋放 765MB）**
- **Sidecar 8765**：PID 37496（restart 多次）；health OK wake_on=true；**onnxruntime 已 downgrade 1.27.0**（1.28 bug 令 openwakeword 輸出全 0——已 pin `<1.28`）
- **Voice 診斷結論（2026-08-31 晚）**：① onnxruntime 1.28 = OWW 全 0（已修）② **Arctis headset 休眠 = mic rms=0.000（而家就係呢個狀態）——戴返/喚醒 headset 先叫到** ③ wake_threshold 0.75 可能偏高（self-monitor 調出嚟）——戴 headset 試完再決定
- **Qwen2.5-VL-7B video server**：`127.0.0.1:8643`——**關閉**（要睇片先手動開）
- **Ports**：8765（alerts MCP + /settings）、8770（reply）、8771（media bridge）、8642（Hermes API）、8643（Qwen video，關）
- **cron**：sk-activity-monitor（1m）、Gateway watchdog（2m）、jarvis-daily-self-review（09:00，monitor）、**jarvis-sidecar-health（2m，monitor——8765 DOWN 先醒）**、**jarvis-session-handoff（每日 05:45，deliver local——reset 前自動對比 session → 更新 HANDOFF + commit docs，唔 push）**
- **Git**：`feature/hermes-alerts-mcp` branch；HEAD `84834f2`（2026-09-01 cron run：HANDOFF 自動更新）；9/1 晚 session 嘅 HANDOFF docs（Review 分類規則 + MC 摘要）由 2026-09-02 handoff commit（HEAD 再推前）

## 剩低（詳見 REMAINING_WORK.md）

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
