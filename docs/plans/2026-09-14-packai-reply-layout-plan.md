# Plan v3 — packai 答案版面修正（模組化工具卡片歸屬／標題去重／物品名行位）

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

## 3. 方案（v3）

### S0 — 開工第一步：1 行 log instrument（零行為改動）
目的：解開「三張截圖嗰啲卡（quest 獎勵／Create 自動攪拌）喺 collect 時 `outputs()` 到底有冇真 ItemStack」。
- 改 `logic/RenderRecipeCardsAskTool.java:108-110` 嗰條 log：加 `outputsSize=`、`primaryOutputId=`、`hasVariant=`（`ItemVariantKeys.hasVariantKeys`），**唔改任何行為**。
- SK 問同一題（`tetra:modular_sword` 單件）→ 我讀 `latest.log` → 用實測數據定 R5 判定鏈。
- 若 `outputs()` 原來係空 → R5 只可以靠 `primaryOutputId()` ＋ category／名做保守判定（唔准亂 drop）。

### K3 — 模組化工具單件模式（config，預設 ON）
- 新 config `modularToolSingleItem`（default **true**）＋ Settings toggle。
- **判定**：用 `ToolBuildFacts.Scan` **非空**（真有零件）；**唔准**用 `ModularToolScan.purposeLines` 非空 —— 後者喺解析失敗時回 `unparsedBlock()`（`ToolBuildFacts.java:200-202`），連空框架都會被當模組化工具。
- **一次過 gate 三條通道**（唔准只 gate prompt）：prompt 段（`AskService.java:683`／`:731`／`:791`）、catalog cards（`:1972-1974`）、JEI（`:2006`）→ 被 drop 嘅 extras **一張卡都唔准出**。
- Single choke point（更正：要連 AI emission 一齊鎖）：`extrasFor` / `collectAskRecipeCards`（`AskService.java:1954`／`:1972-1974`）＋ **AI 路徑** `RenderRecipeCardsAskTool.java:415-432`（`item_id` 要鎖焦點；上限 `AskLoopState.MAX_CARD_EMISSIONS:123`）→ 否則 extras 一樣可以經 LLM 工具出卡。
- log：`Pack AI modularToolSingleItem applied focus=<id> dropped=<n>`。

### K1 — 卡歸屬（**取代舊 id-equality 規則**）
每張卡計出「歸屬物品」= 卡輸出 id（quest 卡＝獎勵物 id；`RecipeCard.promptRole()=="quest"`）。
1. 卡歸屬 == **焦點** → 貼「怎么来」block **段頭**（唔准貼材料步驟行）。
   - ⚠️ 結構澄清：全篇只有**一個**「怎么来」heading（`ReplyLang.sectionHowToGet:753`→`zh_cn.json:397`），Tetra 組裝步驟係 splice 入同一 heading 之下（`AskEngine.java:1493-1535`、`AskService.java:694-705`）→ **唔存在「焦點段 vs 組成段」兩個 section**；正確模型＝一個 block＝**段頭（焦點卡）＋逐條 numbered step（材料卡貼該步行下）**，對應現有實作 `RecipeEmbed.findEmissionInsertIndex:1085-1092`。
2. 卡歸屬 == 正文提到嘅**材料** → 貼該材料行（見 R4-b）。
3. **空框架判定＝用「真 output ItemStack」（SK 提議：經 JEI 拎 recipe → 睇 output）**：
   - ✅ **現成 primitive（已核實）**：`JeiRecipeCards.fromVanillaCrafting`（`client/jei/JeiRecipeCards.java:761-801`）＝ `mc.level.getRecipeManager().getAllRecipesFor(RecipeType.CRAFTING)`（`:769`）＋ `JeiFocusMatch.craftingResultMatches`（`:775`）
   - ⚠️ **能力上限（要寫落報告）**：vanilla recipe manager **覆蓋 datapack＋KubeJS 合成表**，**唔覆蓋** Create 動力合成／Tetra 工作台／FTB 任務獎勵（quest 卡走 `RecipeCard.questOpenId`，`RecipeCard.java:59`／`:192-214`）
   - ⚠️ **（舊版引用作廢）** 唔可以用 `IRecipeCategory.getRecipes()`：`JeiCategoryCatalog.java:145-150` 只列 category，冇 recipe
   - **判定鏈（次序即優先序；整條鏈先 gate「焦點係模組化工具」＝`ToolBuildFacts.Scan` 非空；拎唔到證據一律 KEEP）**：
     0. **gate**：焦點唔係模組化工具 → **唔套用**任何 drop 規則（普通物品自有卡必須保留）
     1. `promptRole()=="quest"`（`RecipeCard.java:200-214`）→ **保留**（真取得途徑）→ 放段頭
     2. `outputs()` **空**（`RecipeCard.java:252-255`／`:334-356`）→ 冇證據 → **保留**（唔准 drop）
     3. 有 output：`JeiFocusMatch.nameUseful`（`:245`）／`ItemVariantKeys.hasVariantKeys`（`:246`、比對 `:260-264`）→ **有名／有 variant → 真·直接合成 → 保留**
     4. 裸 registry 物品（無名、無 variant）＋`primaryOutputId()==焦點 id`（`RecipeCard.java:434-445`）→ **空白框架 → 唔出**
     5. 輸入包含組成段提到嘅零件材料（≥1）→ 當真合成 → 保留
   - **必加 guard**：任何 `outputs().get(0)` 之前先 `isEmpty()` 檢查（quest／Create 卡可能冇 output）
   - **唔經 JEI 嘅替代**：vanilla `RecipeManager.byKey/getAllRecipesFor`（同上，覆蓋 datapack／KubeJS）；非 vanilla 類別拎唔到 output stack → **保守保留**（唔准亂 drop）
4. **任務獎勵卡**＝真取得途徑 → **保留**（已提升為判定鏈第 1 條），只放段頭。
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
- **卡 index 重編（更正）**：真正 reader＝`RecipeEmbed.resolveCardIndex`（`RecipeEmbed.java:1350`，呼叫點 `:580`）；writer＝emission refs（`RenderRecipeCardsAskTool.java:123-146` → `env.offerEmission`）＋ UI 插卡（`AiAssistantScreen.java:831-855`）。**renumber 必須喺呢兩處**，唔係 `RecipeCardsMode`（`:108-115` comment 明寫 "NEVER reorder…"）。

### R1 — 標題去重收窄（多件答案每件可各自有 heading）
- discriminator：見到 `[[item:` 開頭行 → `seen.clear()`（約 3 行，唔改 signature）。
- **另一個 collapser 都要處理**：`collapseDuplicateHowToGet`（`AskReplyScrub.java:1159-1189`，經 `ensureHowToGetBody:968`／`AskEngine.java:862-868`）會全篇只留一個「怎么来」區塊 → 否則多件答案第 2 件嘅取得內容會被整段刪。
- `[[item:]]` 標記唔保證存在（`AskService.java:1622-1625` 只係 repair prompt）→ 退化邊界優先序：`[[item:` > `--- alsoSelected:` > `{{item:` > 空行＋heading 序列。**`seen.clear()` 只可以喺真有 item 邊界時觸發**，否則既有 pin 會回歸：`AskReplyScrubCheck.java:448-450`（純雙「怎么来」仍要 collapse）＋ `tests/check_reply_structure_scrub.py:188-192`。
- **要同步改嘅既有 pin（唯一允許改 assert 嘅情況，要逐條列出）**：`AskReplyScrubCheck.java:442-458`、`tests/check_reply_structure_scrub.py:166-213`
- 兩樹 `AskReplyScrub.java` 必須逐字節相同（`check_reply_structure_scrub.py:1004-1006`）。

### R2 — 物品名獨立一行（SK 揀 a）
- 落點（更正）：**唔可以**放喺 `AskReplyScrub`（佢跑喺 marker repair **之前**；`AskMarkerRepair.java:66`；repair 會 reinsert／upgrade marker → 會 undo）→ 應放 `AskEngine.java:876-878` **之後**，或直接放共用 render 解析點 `AiAssistantScreen.java:831-855`（兩條路徑共用）。做法：任何唔喺行首嘅 `[[item:`／`{{item:` 前面插新行。
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
今日證據只喺 MC 實例 log（repo 內冇）→ 實作前存 `tests/fixtures/tetra_reply_layout_2026-09-14/`：
- 格式：**一案例一檔**（`raw_reply.txt`／`display_body.txt`／`ask_reply_before_ensurecards.txt`）＋ `README.md`（source log 絕對路徑、行號、時間戳、cp950 編碼 caveat：`?`＝簡體字丟失，`怎么?`＝「怎么来」）
- 每檔加 **sha256** 入 README（可回歸比對）
- ⚠️ repo 內有未追蹤 `logs/`、`forge/1.19.2/logs/` → **唔准** `git add -A`，只可以指定檔
- 我已整理暫存副本：`%TEMP%\packai_fixtures\`（等 go 才 copy 入 repo）

## 8. Review 記錄
- R1（反方，subagent review-only）：**7:3 / PLAN-FIX**（2026-09-14）。主要 hole：R1 令既有 pin 回歸、第二個 collapser、K2 入口揀錯（default 係 AI 路徑）、K1 未收窄會剷主卡、K3 判定錯（要 ToolBuildFacts.Scan）、config／lang 冇寫齊、卡 index 未提、證據未入庫。**全部已吸收落 v2**。
- R2（反方，subagent review-only）：**7:3 / PLAN-FIX**（2026-09-14）。主要 hole：R5 引用失實（`JeiCategoryCatalog` 只列 category）→ 改用 `JeiRecipeCards.fromVanillaCrafting`；判定鏈冇 guard（`outputs()` 可空）且 quest 豁免冇入鏈；「焦點段 vs 組成段」係**假二分**（全篇只有一個「怎么来」）；renumber 責任人指錯；R2 落點同 marker repair 次序矛盾；K3 漏 AI emission 通道；fixtures 格式未定。**全部已吸收落 v3**。
- **兩輪都係 7:3（未達 8:2）→ 依契約停手，等 SK 決定**（見 §9）

## 9. 停手報告（依契約：兩輪 7:3，未達 8:2）

**① 逐輪比分**：R1 反方 **7:3**（PLAN-FIX）→ R2 反方 **7:3**（PLAN-FIX）。兩輪嘅反方主要論點由「架構風險」轉為「文字引用失實＋一個未量度嘅未知」→ 唔涉架構，屬可收窄。

**② 卡死嘅載重決定**
1. R5 判定鏈要唔要**整體 gate** 喺「焦點係模組化工具」（`ToolBuildFacts.Scan` 非空）？唔 gate → 會殺普通物品嘅正常合成卡（R2 指出 plan 負面測試冇入鏈）。
2. **quest 卡**（任務獎勵）算唔算「真取得途徑」→ 保留？（我已提升為鏈頭第 1 條；如果 SK 認為任務獎勵都唔應該出卡，就要 drop）
3. 「焦點卡放段頭 vs 材料卡貼對應步」嘅 **precedence**（同一 block 內）—— R2 指我原本措辭係假二分，已改。

**③ 最貴嘅未知**（R2 指名，成本極低可解）
三張截圖嗰啲卡（quest 獎勵 ×2、Create 自動攪拌）喺 collect 時 `outputs()` **到底有冇真 ItemStack**。若係空（`RecipeCard.java:252-255`／`:334-356` 顯示可能係空）→ R5 條判定鏈對呢兩類卡完全失效，只可以靠 `primaryOutputId()`＋類別／名保守判。
**解法**：S0＝喺 `RenderRecipeCardsAskTool.java:108-110` 加 3 個 log 欄（`outputsSize`／`primaryOutputId`／`hasVariant`），**零行為改動**；SK 問同一題 → 讀 log 即知。

**④ 建議**
- **a)（建議）先做 S0 instrument** → 用實測數據定 R5 判定鏈 → 直接開工（**唔再開 review 輪**；因為剩低係文字級引用，唔涉架構）
- b) 唔 instrument，直接保守實作：拎唔到 output stack → **一律唔出焦點自有卡**（最快，但可能連有用嘅任務獎勵卡都唔出）
- c) 暫停呢個 plan，先做其他任務
