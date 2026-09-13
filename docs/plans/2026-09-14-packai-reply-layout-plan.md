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
| R2 | 物品名 widget 貼喺上一行右邊 | 截圖 `3. 自帶耐久 VII…　　賢者杖` | 兩件物品分界唔清 |
| K1b | **該段 3 張卡全部係「焦點工具自己」嘅取得卡**（唔止任務獎勵）| SK 截圖 ×3 ＋ log：`renderCards item=tetra:modular_sword role=output scannedCats=4 foundOutput=4 afterFilter=4` → **4 張卡全部屬這把劍**（Crafting 空框架／任務獎勵×2／自動攪拌），`recipe cards focus=… count=0`；卡按行數派落 1/2/3/4 步 | 材料行（劍刃／劍柄／護手）顯示嘅卡同該材料**完全無關**（SK 2026-09-14 指正：第 2 步嗰張都係錯）|
| R3 | 卡嘅物品**全篇冇被提及**時仍會出卡 | 同上（任務獎勵卡輸出＝焦點劍，但被貼去材料行） | 版面雜訊 |

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
- R3（新增，證據＝SK 3 張截圖）：卡如果**全篇都冇提及該卡輸出物**（或冇被任何行指名）→ **丟棄**（唔准堆段尾），log `cardsDroppedUnmentioned n=…`；理由：堆段尾只會製造雜訊（K1b 就係咁出現）
  - 注意：K1 已覆蓋「輸出 id == 焦點 id」嘅卡（截圖嗰兩張任務獎勵卡正是此類）；R3 覆蓋其餘「有卡但無行對應」情況

### R4（未定，等 SK 揀）
組成段嘅卡應該係邊種？
- **R4-a**：組成段**唔出任何卡**（Tetra 零件冇普通合成；只留文字＋物品連結）
- **R4-b**：出**材料物品自己**嘅卡（要新 collector：掃正文 `{{item:…}}` 提到嘅材料，逐件收卡；而唔係只掃焦點）→ SK 要有心理準備：多數 Tetra 材料係刷怪／掉落，可能冇配方卡
- **R4-c**：保留但**標明係「空白模組合成」**（唔建議，仍然誤導）

## 4. 驗收標準（做完點算完成）

**自動（我跑）**
1. Java：`AskReplyScrubCheck`、`AskToolLoopCheck`、`JeiInfoFactsCheck` 全綠；新增 card placement／frame-card／heading-scope 案例全綠
2. Python：`tests/check_*.py` 全量（期望 100+ PASS、只餘 3 個既有 stale FAIL：`check_ask_tool_context`／`check_heavy_script_corpus`／`check_recipe_io_and_consume_use`）
3. 雙樹 added-lines 對稱 OK；`gradlew jar` BUILD SUCCESSFUL
4. `PackAiConfig.modularToolSingleItem` default == true（測試釘死）

- **驗收（用 SK 2026-09-14 三張截圖做案例，必須逐張對）**
- 組成段（1/2/3/4 步）**一律唔准**出現「輸出==焦點劍」嘅卡（Crafting 空框架／任務獎勵×2／自動攪拌）
- 第 2 步（劍刃「適應之劍」）**都係錯**（SK 指正）→ 唔准再見「自動攪拌·動力攪拌器」
- 全篇唔准出現「卡嘅輸出物冇被任何行提及」嘅孤兒卡
- **未定（等 SK 揀）**：組成段**應否**顯示「材料物品自己」嘅卡（例如異類心臟點整）→ 見 §3 R4

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
