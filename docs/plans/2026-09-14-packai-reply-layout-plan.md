# Plan v2 — packai 答案版面修正（模組化工具卡片歸屬／標題去重／物品名行位）

- 建立：2026-09-14（Discord session）；v2：加入 SK 決定（R4-b）＋新需求（R5 直接合成）＋反方 review（7:3, PLAN-FIX）全部 must-do；v3：R5 改用現成 primitive（`RecipeCard.outputs()` ＋ `JeiFocusMatch.craftingResultMatches`，SK 提議「經 JEI 拎 recipe 睇 output」）
- 狀態：**PLAN（等 SK go 才實作）**。Task K（舊版本）已**停**、未寫任何檔（repo clean），因為其 K1 規則同 R5 衝突，需用本 v2 規格重派
- Repo：`super_minecraft_AI_player`（雙樹 `forge/1.19.2` ＋ `neoforge/1.21.1`）
- ⚠️ 部分檔兩樹有 MC API shim（`Registry`→`BuiltInRegistries`、`Forge`→`NeoForge`）→ **行號有偏差**（例：`ModularToolScan.purposeLines` forge:33 / neo:36；`PackAiConfig.setShowHiddenQuests` forge:548 / neo:560）；唔可以純靠行號同步，要逐字檢查

## 1. 目標（一句）
令答案（尤其 Tetra 模組化工具）**每張卡都屬該行講嘅物品、標題齊全、物品各自成段**；同時唔會剷走真·直接合成／任務獎勵等**真取得途徑**。

## 2. 問題與證據（全部真機，MC 實例 log）

| ID | 問題 | 證據 | 影響 |
|---|---|---|---|
| K1b | 組成段 1/2/3/4 步嘅卡**全部屬焦點這把劍**（Crafting 空框架／任務獎勵×2／自動攪拌），按行數派落 | 截圖 ×3 ＋ log `renderCards item=tetra:modular_sword role=output scannedCats=4 foundOutput=4 afterFilter=4`；`recipe cards focus=… count=0` | 材料行顯示完全無關嘅卡（SK 指正：第 2 步都錯）|
| R1 | 多件答案第 2 件嘅「怎么用」標題被剷 | raw reply「怎么用」×2 → display body ×1 | 使用清單冇標題、似接住上一段 |
| R2 | 物品名 widget 貼喺上一行右邊 | 截圖 `3. 自帶耐久 VII…　賢者之杖` | 兩件物品分界唔清 |
| R3 | 卡嘅物品全篇冇被提及仍然出卡 | 同上 | 版面雜訊 |

Log 原文路徑：`…\instances\AI_test_NFWC_DIM\minecraft\logs\latest.log`（cp950，需逐行解碼；`display body ver=`、`LLM raw reply chars=`、`renderCards item=`、`ask reply before ensureCards` 為關鍵 marker）。

## 3. 方案（v2）

### K3 — 模組化工具單件模式（config，預設 ON）
- 新 config `modularToolSingleItem`（default **true**）＋ Settings toggle。
- **判定**：用 `ToolBuildFacts.Scan` **非空**（真有零件）；**唔准**用 `ModularToolScan.purposeLines` 非空 —— 後者喺解析失敗時回 `unparsedBlock()`（`ToolBuildFacts.java:200-202`），連空框架都會被當模組化工具。
- **一次過 gate 三條通道**（唔准只 gate prompt）：prompt 段（`AskService.java:683`／`:731`／`:791`）、catalog cards（`:1972-1974`）、JEI（`:2006`）→ 被 drop 嘅 extras **一張卡都唔准出**。
- Single choke point：`extrasFor` / `collectAskRecipeCards` 入口（`AskService.java:1954`／`:1972-1974`）。
- log：`Pack AI modularToolSingleItem applied focus=<id> dropped=<n>`。

### K1 — 卡歸屬（**取代舊 id-equality 規則**）
每張卡計出「歸屬物品」= 卡輸出 id（quest 卡＝獎勵物 id；`RecipeCard.promptRole()=="quest"`）。
1. 卡歸屬 == **焦點** → 只可以放焦點**自己嘅取得（怎么来）段**；**唔准**貼任何材料步驟行。
2. 卡歸屬 == 正文提到嘅**材料** → 貼該材料行（見 R4-b）。
3. **空框架判定＝用「真 output ItemStack」（SK 提議：經 JEI 拎 recipe → 睇 output）**：
   - ✅ **codebase 已經有現成 primitive，唔使由零做**：
     - `RecipeCard.outputs()` 已帶真 `ItemStack`（`logic/RenderRecipeCardsAskTool.java:399-400`：`ItemStack o = c.outputs().get(0)`）
     - `JeiFocusMatch.craftingResultMatches(Object recipe, ItemStack focus)`（`client/jei/JeiFocusMatch.java:231-245`）已經用 `ItemStack.isSameItemSameTags(out, focus)`（**NBT-aware**）＋名比對
     - recipe 物件可由 JEI 側拎（`IRecipeCategory.getRecipes()`；id ↔ category 見 `JeiCategoryCatalog.java:122`／`:145-150`）
   - 判定（由強到弱）：
     1. `outputs().get(0)` **帶 NBT 或非通用名** → **真·直接合成**（例如 pack 用 KubeJS／datapack 直接出「砌好嘅」工具）→ 保留
     2. `craftingResultMatches(recipe, heldTool)` == true（`isSameItemSameTags`）→ 真配得上手上呢把 → 保留
     3. 輸出係**裸 registry 物品**（無 NBT、無名、輸出==焦點 id）＋焦點有 NBT 零件 → **空白框架** → 唔出
     4. 輸入包含組成段提到嘅零件材料（≥1）→ 當真合成 → 保留
   - **唔經 JEI 嘅替代**：vanilla `RecipeManager.byKey(id)`（datapack／KubeJS 合成表）；非 vanilla（Create／任務獎勵／FTB）要用 JEI 側 API 或 packai 自己 index → 建議「卡有 ItemStack 就用，唔夠才 by id resolve」
   - 能力上限要寫落報告：若某 category 拎唔到 output stack（例如 Create 動力合成）→ 只能用類別／名稱做保守判定
4. **任務獎勵卡**（`promptRole()=="quest"`）＝真取得途徑 → **保留**，只放焦點取得段。
5. 覆蓋 fallback 通道：`autoEmitCatalogCards`（`AskService.java:1239-1325`，由 `:296-302`／`:2063-2067` 叫）。
6. **負面測試**：普通物品（非模組化）問「怎么来」→ 自有 output 卡**必須保留**。

### R4-b — 材料自己嘅卡（SK 揀 b）
- 新 collector：掃正文 `{{item:id}}` 提到嘅物品（最低限度：組成段）→ 逐件用現有卡通道收卡（受 `recipeCardsPerItem` 上限）→ 標記歸屬物品＝該 id。
- 冇配方（Tetra 材料多數係刷怪／掉落）→ 唔出卡，**唔准**用其他卡頂替。

### K2 — 貼位（修訂）
- 卡只可以貼喺**提到其歸屬物品**嘅行之後；焦點卡只可以貼焦點段。
- 搵唔到行 → 所屬段**段尾**；段尾都對唔上（R3）→ **丟棄**，log `cardsDroppedUnmentioned n=…`。
- **入口要分路徑寫清楚**（預設 `recipeCardsMode="ai"` → `AskService.java:288-331` 完全唔行 `ensureCards`）：
  - AI 路徑：`RenderRecipeCardsAskTool.java:87-118`（收集）＋`RecipeEmbed.java:1051-1097`／`1132-1187`（貼位）＋`RenderRecipeCardsAskTool.filterRole`（`:290`）
  - KEYWORDS 路徑：`AskCardFallback.ensureCards`（`:78-188`）＋`appendAtEnd`（`:663-673`）
- **唔准**只收緊 `CRAFT_STEP_ALIASES`（`RecipeEmbed.java:1147-1151`／`:1200-1209`）就當修好：普通答案步驟只寫「去工作台合成」→ 會冇 anchor；要保留 generic craft anchor 作**次級** fallback。
- **卡 index 重編**：任何删卡／改序都要 renumber；SoT＝`RecipeCardsMode.java:108-121`（歷史錯位 bug 見 `code_change_log.md:4081`）→ plan 指定由該路徑統一 renumber。

### R1 — 標題去重收窄（多件答案每件可各自有 heading）
- discriminator：見到 `[[item:` 開頭行 → `seen.clear()`（約 3 行，唔改 signature）。
- **另一個 collapser 都要處理**：`collapseDuplicateHowToGet`（`AskReplyScrub.java:1159-1189`，經 `ensureHowToGetBody:968`／`AskEngine.java:862-868`）會全篇只留一個「怎么来」區塊 → 否則多件答案第 2 件嘅取得內容會被整段刪。
- `[[item:]]` 標記唔保證存在（`AskService.java:1622-1625` 只係 repair prompt）→ 要加「無標記」退化路徑（例如用 `{{item:}}` 或空行＋heading 序列做次級邊界）。
- **要同步改嘅既有 pin（唯一允許改 assert 嘅情況，要逐條列出）**：`AskReplyScrubCheck.java:442-458`、`tests/check_reply_structure_scrub.py:166-213`
- 兩樹 `AskReplyScrub.java` 必須逐字節相同（`check_reply_structure_scrub.py:1004-1006`）。

### R2 — 物品名獨立一行（SK 揀 a）
- 落點：`AskReplyScrub` 喺 marker repair 之後、render 之前做 **marker newline 正規化**（任何唔喺行首嘅 `[[item:`／`{{item:` 前面插新行）→ 一條路覆蓋兩個 render 路徑。
- 唔准破壞既有 no-glue invariant：`check_recipe_embed.py:527-539`、`check_card_tool_emission.py:118-135`、mirror `check_recipe_embed.py:544-555`。

### Config plumbing（寫齊先好開工）
- `PackAiConfig.java`：field＋`define`＋getter＋setter（forge `:268-272`／`:544-551`；neo `:272`／`:556`／`:560`）
- `PackAiSettingsScreen.java`：CycleButton（forge `:378-391`；neo `:392`）
- lang：3 檔 × 4 key（label／on／off／tooltip）× 2 樹 ＝ 24 key
- 測試釘 `default == true`（pattern：`tests/check_recipe_card_role_budget.py:121-122`）

## 4. 驗收標準

**自動（我跑）**
1. Java：`AskReplyScrubCheck`、`AskToolLoopCheck`、`JeiInfoFactsCheck` 全綠＋新案例（卡歸屬／空框架／負面測試／heading scope／marker newline）
2. Python：全量 `tests/check_*.py`（今日基線 103 個 → 100 PASS、3 個既有 FAIL：`check_ask_tool_context`／`check_heavy_script_corpus`／`check_recipe_io_and_consume_use`）
3. 雙樹對稱 OK（`tests/check_dual_tree_sync.py`）；`gradlew jar` BUILD SUCCESSFUL
4. `modularToolSingleItem` default == true（測試釘死）

**真機（SK 問 3 題，我讀 log 核）**
1. 單件 Tetra 工具：組成段**只**見材料卡（R4-b）或無卡；**唔准**見焦點自己嘅空框架卡；真·直接合成／任務獎勵卡只出現喺焦點取得段
2. 多選 Tetra：只答焦點 1 件（log `modularToolSingleItem applied`），且冇孤兒卡
3. 普通物品多選：兩件都各自有「怎么来／怎么用」標題（R1）；物品名各自獨立一行（R2）

**SK 三張截圖逐張對（驗收案例）**
- 組成段 1/2/3/4 步：**唔准**再見「任務獎勵：感謝安裝黃金年代」／「任務獎勵：龍曾在這裡」／「自動攪拌·動力攪拌器」呢類屬焦點劍嘅卡
- 全篇唔准有孤兒卡

## 5. 風險與緩解

| 風險 | 緩解 |
|---|---|
| 拎唔到配方輸出 NBT → 冇法完美分「真合成 vs 空框架」| 退回「輸入相關性」判定；喺報告寫明能力上限；必要時問 SK 要唔要保守（一律唔出焦點自有卡）|
| R1 收窄令真重複標題回歸 | 只放寬「跨物品區塊」；區塊內緊接重複仍剷；兩邊測試都有 |
| K2 收緊令卡全堆段尾 | 保留 section-tail fallback＋R3 丢棄孤兒卡；真機驗收第 1／2 點必然檢查 |
| 標記 `[[item:]]` 唔存在 | R1 加退化邊界規則；缺標記時仍要保住兩件各自 heading |
| 卡 index 重編漏做 | 指定 `RecipeCardsMode.java:108-121` 統一 renumber＋加測試 |
| 兩樹行號偏差 | 逐字檢查、`check_dual_tree_sync` 把關 |

## 6. 唔做（界外）
- 唔改 TEtra 結構分流（`withToolBuildHowToGet`）、JEI 全 id 修復、footer 標籤翻譯（已完成、已 commit `8d25433`／`9f9baaf`）
- 唔改卡內容／卡數上限既有 config（`recipeCardsPerItem` 等）
- 唔加「只答 1 件」提示字（等真機再定）

## 7. Fixtures（review 要求）
今日證據只喺 MC 實例 log（repo 內冇）→ 實作前存 `tests/fixtures/`：① raw reply（`LLM raw reply chars=1128`）② `ask reply before ensureCards` 片段 ③ display body 片段。

## 8. Review 記錄
- R1（反方，subagent review-only）：**7:3 / PLAN-FIX**（2026-09-14）。主要 hole：R1 令既有 pin 回歸、第二個 collapser、K2 入口揀錯（default 係 AI 路徑）、K1 未收窄會剷主卡、K3 判定錯（要 ToolBuildFacts.Scan）、config／lang 冇寫齊、卡 index 未提、證據未入庫。**全部已吸收落 v2**。
- R2（如需）：
（上限 3–4 輪；未達 8:2 即停手問 SK）
