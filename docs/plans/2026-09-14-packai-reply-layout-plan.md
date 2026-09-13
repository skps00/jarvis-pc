# Plan — packai 答案版面修正（模組化工具卡片／標題去重／物品名行位）

- 建立：2026-09-14（Discord session）
- 狀態：**PLAN（等 SK 批准才實作）**；其中 K1–K3 已按 SK 2026-09-14 決定「b」先行派工（實作中），R1–R2 為本 plan 新增項
- Repo：`super_minecraft_AI_player`（雙樹 `forge/1.19.2` ＋ `neoforge/1.21.1`，Java 兩樹字面必須相同）

## 1. 目標（一句）
令答案版面（尤其 Tetra／模組化工具）**卡喺正確位置、標題齊全、每件物品各自成段**，唔會出現「錯卡／標題消失／物品名貼錯行」。

## 2. 問題與證據（全部真機）

| ID | 問題 | 證據 | 影響 |
|---|---|---|---|
| K1 | 多選 Tetra 工具時，**空框架合成卡**（輸出＝焦點 id）被貼喺「到 Tetra 工作台…」之後 | 截圖 `配方：Crafting [鐵錠＋木棍→劍]`；log `renderCards item=tetra:modular_sword … foundOutput=4 afterFilter=4` | 同「不是普通合成」自相矛盾；大格卡撐爛版面 |
| K2 | 卡貼位唔一定跟提及行 | 同上（卡落喺冇提及該物品嘅行） | 版面亂 |
| K3 | 多選時模組化工具一次答多件 | 同一答案含 `tetra:modular_sword` ＋ `tetra:modular_single` | 卡片／段落交錯 |
| R1 | **第 2 件物品嘅「怎么用」標題被剷走** | raw reply 有「怎么用」×2；最終 display body 只有 ×1（`stripDuplicateSectionHeaders` 全篇去重） | 使用清單冇標題、好似接住上一段 |
| R2 | 物品名 widget 貼喺上一行右邊 | 截圖 `3. 自帶耐久 VII…　　賢者之杖` | 兩件物品分界唔清 |

## 3. 方案

### K 組（SK 已批「b」；實作中，Task K）
- K3：新 config `modularToolSingleItem`（**default true**）＋ Settings toggle；焦點 `ModularToolScan.purposeLines` 非空 → 忽略 `alsoSelected`，只答焦點一件；log `modularToolSingleItem applied focus=… dropped=…`
- K1：單件模式生效時，**排除輸出 id == 焦點 id 嘅配方卡**；材料卡保留；log `frameCardsSuppressed item=… n=…`
- K2：卡只可以插喺**正文有提及該卡物品（或其材料）**嘅行之後；搵唔到 → 段尾（**唔准**段首）

### R 組（本 plan 新增，等批准）
- R1：`AskReplyScrub.stripDuplicateSectionHeaders` 去重**收窄為「同一件物品區塊內」或「緊接重複」**：
  - 見到新嘅 `[[item:…]]` 標記後，**標題去重狀態要重置**（每件物品可以各自有「怎么来／怎么用」）
  - 只剷真正緊接重複（相鄰非空行同標題）嘅情況
  - 加回歸案例：多件回答，兩個「怎么用」都要留；單件回答重複標題仍要剷
- R2：物品名 widget（`[[item:id]] 名稱`）強制**獨立一行**：保證前面有空行、後面接內容；若模型冇寫空行，由 renderer／scrubber 補（唔准改物品名本身）

## 4. 驗收標準（做完點算完成）

**自動（我跑）**
1. Java：`AskReplyScrubCheck`、`AskToolLoopCheck`、`JeiInfoFactsCheck` 全綠；新增 card placement／frame-card／heading-scope 案例全綠
2. Python：`tests/check_*.py` 全量（期望 100+ PASS、只餘 3 個既有 stale FAIL：`check_ask_tool_context`／`check_heavy_script_corpus`／`check_recipe_io_and_consume_use`）
3. 雙樹 added-lines 對稱 OK；`gradlew jar` BUILD SUCCESSFUL
4. `PackAiConfig.modularToolSingleItem` default == true（測試釘死）

**真機（SK 一句話問 3 題，我讀 log 核）**
1. 單件 Tetra 工具 → 版面：組成段只得**材料卡**（冇 Crafting 空框架卡）；卡貼喺對應材料行後面
2. 一次勾 2 件 Tetra 工具 → 只答**焦點 1 件**（log 有 `modularToolSingleItem applied`）
3. 一件普通物品（非模組化）多選 → 照舊答多件，且**每件各自有「怎么来／怎么用」標題**（R1）；物品名各自獨立一行（R2）

## 5. 風險與緩解

| 風險 | 緩解 |
|---|---|
| 去重收窄後，模型真係重複寫標題 → 版面返到「重複標題」老問題 | R1 只放寬「跨物品區塊」，區塊內緊接重複仍剷；加兩邊測試 |
| 單件模式令 SK 少咗資訊（多選被忽略） | 預設 ON 但可 Settings 關；log 可審計；必要時答案頂加一行提示（本 plan **暫不加**，等 SK 睇真機再定） |
| 唔係 Tetra 嘅模組化工具（將來 Tinkers 類）漏判 | 判定用「組成非空」而非 namespace 白名單；殘餘風險記 skill |
| 卡貼位新規則令部分卡「搵唔到行」→ 全堆段尾 | 保留段尾 fallback；驗收第 1 點會用真機答案檢查唔會退化 |

## 6. 唔做（本 plan 界外）
- 唔改 Tetra 結構分流（`withToolBuildHowToGet`）、JEI 全 id 修復、footer 標籤翻譯（已完成並 commit）
- 唔改卡內容／卡數上限（`recipeCardsPerItem` 等既有 config 唔郁）
- 唔加「模組化工具只答 1 件」提示字（等真機再決定）

## 7. Review 記錄
- R1（cursor review-only）：
- R2（如需，adversarial）：
（上限 3–4 輪，未達 8:2 即停手問 SK）
