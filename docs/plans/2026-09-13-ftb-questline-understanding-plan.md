# Plan v1 — FTB 任務線全文理解（AI 讀成條 quest line 找「呢件嘢點用」）

> SK 原話（2026-09-13 Discord）：「add a new plan on mcmod, let AI can think or read whole FTB quest line and find how to use that item」
> Repo：`super_minecraft_AI_player`（雙樹）。**呢份係 plan v1，未開工；要 SK 批 + review 過關才實作。**

---

## 0. Baseline（2026-09-13 實查，唔准抄）

| 項 | 實況 | 證據 |
|---|---|---|
| 現有任務程式 | `logic/QuestGuide.java` **1594 行**：`index(gameDir, scanners, preferredLang, filterHidden)` → `List<Hit>`（chapter／title／description／source／items／questId／system／canRepeat）；`MAX_HITS = 3`（`:23`）；描述 cap **120／400** 字（`:799`） | read_file ＋ grep |
| 呼叫點 | `client/chat/ChatSession.java:31/303/312`（`lastQuests`，`MAX_QUEST_SLOTS`）、`client/gui/AiAssistantScreen.java:431/968/987/1314`（任務卡＋開任務書）、`client/QuestBookOpener.java` | grep |
| 現有任務測試 | 7 個：`check_quest_card_dedupe`／`check_quest_demote_when_jei`／`check_quest_focus_id_prefer`／`check_quest_match_extras`／`check_quest_priority`／`check_quest_strip_icons`／`check_quest_title_prefer`（全 rc=0） | 全量 checks |
| Agentic 工具樣板 | `logic/GuideFetchAskTool.java`（`AskTool`：`name()`／`description()`／`argsSchemaJson()`／`toolMissNote()`／`run()`；回傳 `AskToolContext.clipChars(text, 2000)`） | read_file |
| 資料語料 | `…/instances/AI_test_NFWC_DIM/minecraft/config/ftbquests/quests/`：**50 個 chapter**（`chapters/*.snbt`）＋ `chapter_groups.snbt`／`data.snbt`／`reward_tables/`；**總 1.7MB**；`lang/` 目錄**空**（描述內嵌，帶 FTB 色碼 `&5`／`&r`） | `ls`／`du`／`head` |
| SNBT 結構（抽樣） | `chapters/1.snbt`：chapter 級 `filename/id/group/icon/order_index/quest_links`；`quests: [ { dependencies: ["72D090FF4C44DAAD"], description: [ "…" ], id, x, y, … } ]` | `head -c 1200` |
| 現行 prompt 政策（要改嘅位） | `lang/*.json` `packai.reply.fact_check`／`llm_style`／`reply_pattern` 明文：任務**只用名稱、唔准 hex ID**；「除非 tasks／rewards 列出 heldItem.id，禁止宣稱該任務教取得／合成焦點物」；任務文字**唔可以當用途證據** | grep（zh_cn.json:365/391/392 等） |
| 全量 checks baseline | 101 檔 / **4 FAIL**（3 pre-existing ＋ `check_ask_display_leak`）→ 見 Tetra plan §0（同一 baseline） | 實跑 |
| 上游參考 | FTB Quests 官方 changelog／docs（`docs.feed-the-beast.com`）；SNBT 解析工具：PyPI `ftb-snbt-lib`、`snbtlib`、`Krutoy242/ftbq-nbt`（Java/Kotlin，可做 Java 側參考）、`zack-zzq/FTBQuestLocalizerPython`（抽字串做 i18n，格式相容參考） | web_search |

## 1. 需求 vs 現狀 gap

**需求（SK）**：AI 要「想／讀成條 FTB 任務線」，用嚟答「**呢件物品點用／喺進度邊度用**」——即係任務線係一個**知識來源**，唔止係「任務名」。

**現狀 gap**
1. `QuestGuide` 只做**關鍵詞命中 × top 3**，描述截到 120／400 字 → **冇讀成條線**（冇依賴鏈、冇章節順序、冇前後關係）。
2. 任務文字**被政策禁止**當用途／取得證據（只准名）→ 就算任務描述白紙黑字寫「用呢件嘢做 X」，AI 都唔敢用。
3. 冇 agentic 工具畀 AI **主動**查任務線（現有工具：`guide_fetch`（Patchouli）／`render_recipe_cards`／`repair` 等）。
4. 1.7MB／50 章唔可以整個塞入 prompt（budget）→ 必須檢索。

## 2. 目標 / 非目標

**目標**
- G1：由物品（registry id／顯示名／別名）查任務線：命中任務（tasks／rewards／description 提及）＋其**依賴鏈**（前後 1–2 層）＋所屬章節／順序。
- G2：把命中任務嘅**描述文字**（去色碼、去 UI 雜訊）提供畀 AI 做「點用／幾時用／點解要」嘅證據，**標明來源＝任務線**。
- G3：以 **agentic tool** 形式接入（AI 自己決定幾時查），回傳受預算限制；同時 FACT 可出一行「此物在任務線有相關章節」嘅提示。
- G4：離線可驗（corpus harness）＋真機可驗（SK 問 5 條問題）。

**非目標（v1 明確唔做）**
- 唔讀玩家**任務完成進度**（要 FTB API／存檔；另開 plan）。
- 唔改任務書 UI／任務卡顯示（除咗 feeding 內容）。
- 唔引入 FTB Quests **compile-time 依賴**（soft-dependency／反射另議，見 LD1）。
- 唔做多語任務（語料係簡中內嵌；v1 只處理語料原文）。

## 3. 載重決定（review 用）

| ID | 決定 | v1 立場 |
|---|---|---|
| **LD1** | 資料源＝**直接讀 `config/ftbquests/quests/**` SNBT**（沿用／擴充 `QuestGuide` 現有 parser），唔用 FTB in-game API | 採用（零新依賴、雙樹一致、離線可測；API 版本耦合＋反射風險留 Phase 2） |
| **LD2** | 規模策略＝**檢索式**：物品 id／名 → 命中任務 → 依賴圖鄰域（depth 1–2），唔整個語料入 prompt | 採用（1.7MB 不可能全塞） |
| **LD3** | 暴露方式＝**新 agentic tool `quest_line_lookup`**（照 `GuideFetchAskTool` 模式；args：`item`／`query`／`depth`／`limit`）＋ FACT 一行提示 | 採用（唔改 prompt 就能用；可獨立 disable） |
| **LD4** | 內容政策改動＝放寬到**可用任務描述做用途／進度證據**（標來源），但保留：唔准捏造、唔准用任務名當物品證明、唔准 hex ID | 採用（要改 3 語言 × 2 樹嘅 `fact_check`／`llm_style`／`reply_pattern`；要核 7 個 quest checks 會唔會紅） |
| **LD5** | 預算：回傳 ≤2000 字（`clipChars` 同款）；命中 ≤5 任務；每個任務描述 ≤300 字；依賴鏈 ≤2 層；總輸出要包「章節→任務→描述→依賴」結構 | 採用（避免答案爆炸） |
| **LD6** | 離線驗收＝**corpus harness** 對真 SNBT（50 章）：抽 ≥5 個真實物品，斷言命中正確／依賴鏈正確／描述去色碼／唔捏造；真機＝SK 5 題 | 採用 |
| **LD7** | 效能＝快取索引（照 `GuidebookIndexCache` 模式）＋以 `mtime`／檔案數失效 | 採用（1.7MB 每次 query 重讀會 lag） |
| **LD8** | 唔做玩家進度（QuestFile progress） | 採用（避免 FTB API 耦合） |
| **LD9** | 語料**可公開**？—— 任務描述係 pack 內容（CF 1643097），harness fixture 只可入**少量**樣本（避免 dump 整條任務線入 git） | 採用（fixture ≤3 任務、加註來源） |

## 4. 執行內容（草案）

- **T1 索引層**：擴充 `QuestGuide`（或新 `QuestLineIndex`）parse 全部 chapter → 任務節點（id、chapter、title、description（全文，唔截）、tasks／rewards 的 item ids、dependencies、x/y、hidden）→ 建反向索引（item id → quest ids）＋依賴圖。
- **T2 檢索層**：`lookup(item|query, depth=2, limit=5)` → 命中任務＋依賴鄰域＋章節順序；描述去 FTB 色碼（`[&§][0-9a-fk-or]`）＋去空行／image 行。
- **T3 暴露層**：新 `QuestLineAskTool`（`AskTool`）＋ 註冊（同 `GuideFetchAskTool` 一樣路徑）＋ `toolMissNote`（無命中要老實講，唔准捏造）。
- **T4 政策層**：lang 3 語言 × 2 樹改 `fact_check`／`llm_style`／`reply_pattern`：加「任務線證據可以用（標來源）；任務描述≠物品存在證明；唔准 hex ID；唔准把任務完成進度當已知」。
- **T5 驗收**：corpus harness（T1 前先寫，鎖 baseline）→ 改後重跑；真機 5 題；全量 checks 唔增 FAIL。
- 每 task 完成即 self-review（compile／checks／grep／diff），有 bug 修到清先落下一 task（SK 規則）。

## 5. 驗收標準（開工前定死）

| # | 驗收項 | 通過標準 |
|---|---|---|
| V1 | corpus harness | 對真 50 章語料：≥5 個物品命中正確、依賴鏈正確、描述去色碼乾淨、**冇捏造**；negative control（查不存在物品）要回空並明講 |
| V2 | tool 註冊＋schema | `quest_line_lookup` 喺 tools-offered 清單出現（AI 模式）；args schema 合法；`toolMissNote` 老實 |
| V3 | 預算 | 回傳 ≤2000 字；命中 ≤5；每描述 ≤300；depth ≤2（實測長度數字寫入報告） |
| V4 | 全量 checks | 唔多過 baseline（4 FAIL；T0 修好後 3 FAIL） |
| V5 | 真機 | SK 問 5 題（含 1 題冇任務關聯嘅物品）：有任務線嘅要列章節／任務／描述並可被理解；冇嘅要老實講冇；`check_ask_display_leak` rc=0 |
| V6 | 無 regression | 7 個 quest checks 全綠；非任務題行為不變 |

## 6. 風險評估 / 最壞情況 / 還原

| 項 | 內容 |
|---|---|
| 風險 | ① 政策放寬令 AI 用任務文字過度推論（例如把任務獎勵當取得路徑）→ V1 negative control＋prompt 明文；② 1.7MB parse 每 query lag → LD7 快取；③ 50 章 SNBT 格式多樣（image／hover／click 行）→ parser 要容錯；④ 改 lang 撞 7 個 quest checks → V6 攔；⑤ 任務描述含 pack 內梗／劇透 → 需 SK 決定「照講定遮蔽」（見 §7 待決） |
| 最壞情況 | 任務線答案過長／資料唔準；唔影響資料、state、其他物品；回滾一個 commit |
| 還原 | 全部係新增 class ＋ lang 字串 → `git revert <commit>`；jar 回滾＝`dist/_smoke_backups/` 備份 |
| 唔准郁 | `AskToolLoop` ALLOWLIST／`canonicalArgsJson`；`AskReplyScrub` 段判定；`[TETRA_USE]` 語義；任務卡 UI；`check_*` 斷言（唔准為變綠改測試） |

## 7. 待 SK 決定（開工前）

1. **劇透／遮蔽**：任務描述可能含劇透或作者梗 — a) 照原文引用 b) 只抽「有用動作／材料／解鎖」句子 c) 標「任務線提示」再引用？（v1 建議 b＋c）
2. **範圍**：只做「物品點用」定同時做「點解要做／進度位置」？
3. **數據層**：要唔要**只讀**（唔寫任何 cache 檔入 instance 目錄）？v1 建議：cache 放 `%APPDATA%`／mod config 目錄，唔污染 instance。

## 8. Review record

| 輪 | 角色 | 比分 | 主要翻盤點 | 修改 |
|---|---|---|---|---|
| R1 | 待跑 | — | — | — |
