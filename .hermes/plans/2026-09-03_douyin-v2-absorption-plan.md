# Douyin 收藏 v2 吸收 Improve Plan（2026-09-03）

> For Hermes：文件/分析任務。承接 content-absorption framework P4-P7。
> 來源：2026-09-03 douyin scan v2（205 條；14 新、7 AI 全 ASR 深讀）。
> Notes：`%TEMP%\douyin_v2_import_notes.md`；數據：browser-use workspace `20260903_142520_35664e25\douyin_favorites_v2_classified.json`。

**Goal:** 7 條新 AI 收藏 → 有幾多值得吸收（skill/workflow/知識）？逐項 SK 批准先落地。

## Gap 表（收藏反映嘅 practice vs 我哋現狀）

| # | practice（收藏） | 我哋現狀 | gap? | proposal | priority |
|---|---|---|---|---|---|
| G1 | Harness+Memory 優先思維（#5 DSH 片：值得學係 harness+memory，唔係單一 agent 產品） | Hermes（main harness）+ JARVIS self-evol（autonomy/prompt pipeline/memory 治理）+ Loop Engineering path；Prime Agent review 啱啱都偷咗「compute over data」 | 冇新 gap——方向一致 | 記錄入 self-evol/REMAINING_WORK 參考 | 記錄 |
| G2 | De-AI 寫作審校 skill（#7 Sepia：查空話/事實/結構，Codex+Claude Code 用） | humanizer（strip AI-isms）+ sk-reporting-style + requesting-code-review；冇獨立「事實/空話審校」step | **部分 gap**——我哋 review 冇 systematic 空話/可驗證性 check | A1 深睇 Sepia（clone read-only → 結構對照 → 提吸收建議） | 評估先 |
| G3 | Vibe Coding 教材（#6 Easy Vibe ★19.2k 等） | SK 已重度 vibe coding（Cursor）；冇教材缺口 | 冇實質 gap | 記錄（有需要先掃） | 記錄 |
| G4 | 平台 skill store 生態（#3 豆包 SKILL 示範） | Hermes skill library + 治理（router verify/整合）已有 | 冇 gap | 唔使改 | 記錄 |
| G5 | 桌面整理工具（#1）／面試協修（#2） | 同 stack 無關 | 冇 | 唔吸收 | — |
| G6 | AI 挖漏洞自動化（#4） | 賣課/傭金引流 | — | **噪音**，唔吸收 | 剔除 |

## 提議分類

### A. 即刻做
- （無——7 條冇一條需要即時改 skill/workflow；吸收閘照舊 SK 逐項批）

### B. 評估先（獨立 experiment）
- **A1（G2）Sepia 深睇**：`git clone`（read-only，入 `%TEMP%`）→ 讀佢 SKILL/rules 結構 + 同 humanizer/sk-reporting-style/requesting-code-review 對照 → 出「值唔值得吸收：a) 學佢 review 規則（空話/事實 check）入 requesting-code-review；b) 直接翻譯成 Hermes skill；c) 唔吸收只記錄」。驗收：對照表 + 建議。~30 分鐘。
- **A2（G3，低優先）Easy Vibe 教材掃描**：README/目錄結構掃 → 有冇可偷嘅 vibe coding 方法論（prompt 框架/工作流）入 cursor/skill。驗收：一頁發現。可揀唔做。

### C. 記錄（之後再睇）
- **C1（G1）**：DSH「Harness+Memory 優先」insight 記入 jarvis-pc REMAINING_WORK（self-evol 參考），唔開新工作。
- **C2（G3/G4）**：Easy Vibe / 影視颶風 SKILL 記錄（有需要時再睇）。

## 驗收
- [x] SK 逐項批 A/B/C——**2026-09-03 SK 批：A1 做 + C1/C2 記錄**（「1, and some of those video is related to our project's idea or similar, so we can mark it down」）
- [x] 批准嘅項有結果（A1 對照表 + 建議）——見下方執行記錄
- [x] 冇未批準改動

## SK 補充要求：同我哋 project 相關嘅收藏標記（2026-09-03）
SK 指出部分新片同 JARVIS/Hermes/agent 路線相關——標記落嚟（有 url 可以之後深睇）：

| 片 | 相關性 | 點相關 |
|---|---|---|
| #5 7675337117291023652 DeepSeek-Harness 面試片 | 🔴 高 | Harness+Memory 優先思維；agent 可組裝運行底座——同 Hermes/JARVIS self-evol/Loop Eng 同路線 |
| #7 7680768247804775707 Sepia | 🔴 高 | De-AI 寫作審校——同 humanizer/sk-reporting-style/requesting-code-review 直接互補 |
| #6 7680862878856908095 Easy Vibe 等 3 項目 | 🟡 中 | Vibe coding 工作流/課程——SK 重度 Cursor 用家 |
| #3 7670844233401552162 影視颶風 SKILL | 🟡 中 | 平台 skill 生態 + 內容 hook 方法——skill 概念參考 |
| #1 7680477991545195810 桌面整理工具 | ⚪ 低 | 桌面 UX——同 HUD/桌面自動化無直接關係 |
| #2/#4 | ⚫ 無關/噪音 | 面試技巧／賣課引流 |

## 執行記錄（2026-09-03）
- [x] A1 Sepia 深睇（見下）
- [x] C1 DSH insight → REMAINING_WORK
- [x] C2 Easy Vibe/影視颶風記錄
- [x] 相關影片標記入 REMAINING_WORK

### A1 結果：Sepia vs 我哋現有 skill（clone `Nanako0129/sepia` v0.5.0，read-only）

**Sepia 係咩**：portable Agent Skill（agentskills.io spec）——fiction narrative architecture（StoryScope 研究 93.2% macro-F1）＋ professional prose 分 venue rule（release notes/PR replies/postmortems/tickets/tech articles）；4 ops（write/review/refactor/recreate）；review = diagnose-only、refactor 前強制 2-stage（先 defect list 後改）。

**對照表**：

| 維度 | humanizer（我哋） | sk-reporting-style | requesting-code-review | Sepia |
|---|---|---|---|---|
| 範圍 | surface style（34 patterns，word/syntax 層） | SK 通訊 register | code 驗證 | narrative 架構 + professional domains |
| Prose 分 venue rule | ❌ 冇 | SK-only | n/a | ✅ 每個 doc type 一個 rule file |
| Diagnose→edit 兩階段 | 有 audit step（最後 anti-AI pass），非強制 | n/a | ✅ reviewer-first | ✅ 強制 |
| 「唔准作事實」guardrail | 隱含（「use specific details」） | 隱含 | n/a | ✅ hard rule：number/version 一定嚟自真 artifact，冇 → TODO/問，唔好填 |
| Calibration（唔好 over-apply） | ❌（全 patterns 套用） | 隱含 | n/a | ✅ 「aim at the band」——每條 rule 都套 = 新 fingerprint |
| Model fingerprint | ❌ | ❌ | ❌ | ✅（per-model tells，executor-aware） |

**裁決：唔安裝 Sepia**（唔同 skill 生態——Agent Skills CLI + Claude Code/Codex plugin；fiction 部分同 SK 無關；我哋已有 humanizer 覆蓋 surface 層）。**建議吸收 3 個 ideas 入 humanizer**（研究導向，唔係搬成個）：
1. **Venue rules（最有價值）**：我哋成日寫 release notes / commit / HANDOFF / docs——Sepia 嘅 release-notes rule（terse、每個 claim 帶 artifact、breaking changes 先行、刪 journey intro/outro、長度跟 release）同 AGENTS.md/我哋寫作高度啱——加一個 `references/venues.md` 入 humanizer + SKILL.md 加一小節
2. **「Never invent specifics」升做 hard guardrail**：number/version/timestamp 唔夠 → TODO/問，唔好填（SK 報告 jargon 規則都受益）
3. **Calibration 一句**：唔好每條 pattern 都套晒（「select, leave slack」）——同 Sepia 嘅「全部 rule 套晒 = 新 fingerprint」一致

→ **落地需 SK 批**（P7 吸收閘）：只改 humanizer（加 references/venues.md + SKILL.md 兩段），零新依賴。
→ **✅ 2026-09-03 SK 批已落地**：`humanizer/references/venues.md`（4 條 governing principles + 5 venue rule 組）+ SKILL.md「Professional documents (venues) & hard guardrails」section（pointer + never-invent + calibrate）。verify：skill_view 見 references/venues.md + SKILL.md patch diff。

## Adversarial review（P6，三階段，真證據）
**① 反方**：Sepia 係 Agent-Skills 生態（Anthropic Agent Skills CLI format），同 Hermes SKILL.md 格式唔同——翻譯成本高；我哋已有 humanizer+sk-reporting-style，可能重疊多；GitHub ★1687 係新 repo（推測 <1 個月），未經時間考驗；93.2% F1 claim 係佢自己 research，未獨立複現。Easy Vibe ★19.2k 係課程（唔係工具），吸收價值低。成個 7 條深讀得 1 個真候選，值唔值 30 分鐘？可能 YAGNI。
**② 正方**：Sepia 定位正中 SK 已知痛點（AI 味/空話/報告 jargon——sk-reporting-style 就係為咗呢樣而設）；佢「事實可驗證性 check」係我哋 requesting-code-review 冇 systematic cover 嘅；睇源碼/規則成本低（read-only clone，零依賴、零安裝、零風險）；就算唔吸收，對照結果都幫我哋強化現有 skill（例如加「空話偵測」規則入 sk-reporting-style 或 requesting-code-review）。Easy Vibe 課程對 SK 低價值但掃 README 成本 <5 分鐘，可 drop 或記錄。
**③ 中立裁判**：反方對「Sepia 直接吸收成本高」成立，正方對「深睇價值 = 強化現有 review 流程」成立——**兩邊唔矛盾**：A1 應該做（read-only 研究，目的係「吸收 idea 入現有 skill」而唔係「安裝 Sepia」），A2 可降級做記錄。最大未知：Sepia 規則同我哋現有 skill 重疊度實際幾高（要 clone 先知）。反轉條件：如果 clone 後發現 Sepia 核心就係 humanizer 已有內容 → A1 結論 = c（記錄，唔吸收）。
**裁決**：A1 做（研究導向，產出對照表；唔安裝、唔改 code 住）、A2 降級記錄、C1/C2 記錄。禁 55 開——裁決有明確傾斜：A1 值得，但落地形式係「吸收 ideas 入現有 skill」唔係「引入新 tool」。
