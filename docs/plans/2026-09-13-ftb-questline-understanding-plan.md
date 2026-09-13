# Plan v2 — FTB 任務線理解：AI 讀成條 quest line 去答「呢件嘢點用／會發生咩事」

> SK 原話（2026-09-13）：「add a new plan on mcmod, let AI can think or read whole FTB quest line and find how to use that item」
> SK 補充 scope（同日）：「**I want it can know what will happen when use that item with right click and left click or the system that behind it**」
> SK 決定：**cache 放 `%APPDATA%`／mod config（唔污染實例目錄）**（問題 3 = a）
> Repo：`super_minecraft_AI_player`（雙樹）。**plan，未開工；要 review 過關 ＋ SK 批才實作。**
>
> **v2 改動（R1 反方 3:7 → 修；以下全部有 reviewer 實跑證據）**：
> 1. **§1 gap3 錯**：**工具已經存在** —— `logic/QuestFetchAskTool.java`（`name()` = `"quest_fetch"`），`AskToolLoop.java:37`（`FIRST_ROUND_TOOLS`）＋`:40`（`CAPABLE_TOOLS`）已含佢，`AskToolLoop.java:347/354` 仲會自動 run。⇒ **LD3 改為「擴充 `quest_fetch`」，唔新開工具**（新名會因 ALLOWLIST 閘被**靜默丟棄**：`AskToolLoop.java:137-143` `register()`、`:292` `run()`、`LlmClient.nativeToolsSchema():606`；`registerExternal` 只回 `OK_STORED_NOT_ALLOWLISTED`）。
> 2. **§0 事實更正**：`quests/lang/` **唔存在**（唔係「空」）；語料實數 = chapters **50 檔／1,601,903 B**、tree **1,609,136 B**、最大 chapter **158,035 B**；`QuestGuide.java:138` **`Files.size(p) > 500_000` 就靜默 return**（跳過大檔、冇 log）→ headroom 只 3.16×，pack 更新即可能整章消失。
> 3. **LD2 加 degree cap**：depth-2 會爆（實測 `cold_sweat:item_insulation` d2 = 196 任務／4,015 字；`gateways:gate_pearl` d2 = 94／4,326；樞紐任務 `3E9DD0B78886A183` 有 **162 dependents**；depth-2 closure p90 = 1.6%、max 8.9% ≈ 224 任務）⇒ 加「**每節點出度 cap ≤8**＋總預算」。
> 4. **Harness 加 6 條真陷阱 assert**（見 §5 V1）：NBT-object item（1,665 處）、`itemfilters:or`／`:tag`、CRLF（66,247）、426 個轉義引號、14 行 raw JSON component、**48.7% 任務冇 description**。
> 5. **矛盾書面解決**：§7 cache 位置 vs §6「唔准郁 ALLOWLIST」；另加「描述內贊助／宣傳連結要剔走」。
> 6. **Scope 依 SK**：目標由「點用」擴為「**用嗰件嘢（右鍵／左鍵／觸發）會發生咩事＋背後系統**」；任務線係**其中一個證據來源**，要同現有機制來源並用（`graphFacts` `on:/right_click/desc`、KubeJS 腳本片段、tooltip、`[CONSUME_USE]`／`[TETRA_USE]`／`[SCROLL_*]`）。

---

## 0. Baseline（2026-09-13 實查；方框內數字係 reviewer 或我自己跑出嘅）

| 項 | 實況 | 證據 |
|---|---|---|
| 現有任務程式 | `logic/QuestGuide.java` **1594 行**；`index(gameDir, scanners, preferredLang, filterHidden)` → `List<Hit>`；`MAX_HITS = 3`（`:23`）；描述 cap **120／400** 字（`:799`）；**`Files.size(p) > 500_000` → 靜默 skip**（`:138`） | read_file／grep |
| **現有 agentic 工具** | **`quest_fetch` 已經存在**：`logic/QuestFetchAskTool.java`；`AskToolLoop.java:37` `FIRST_ROUND_TOOLS`、`:40` `CAPABLE_TOOLS`、`:347/:354` 自動 run；`AskEngine.java:37`（註冊） | grep |
| 呼叫點／UI | `client/chat/ChatSession.java:31/303/312`（`lastQuests`）、`client/gui/AiAssistantScreen.java:431/968/987/1314`（任務卡＋開任務書）、`client/QuestBookOpener.java` | grep |
| 現有任務測試 | 7 個（`check_quest_*`，全 rc=0） | 全量 checks |
| 語料實數 | `quests/chapters/*.snbt`：**50 檔／1,601,903 B**；`quests/` tree **1,609,136 B**；最大 chapter **158,035 B**；`quests/lang/` **唔存在**；子目錄只有 `chapters/` 同 `reward_tables/` | Python `os.walk`＋`os.path.getsize` |
| 語料內容量（reviewer 量化） | **2,517 條任務**；cleaned 描述共 **114,089 字元**；**2,380 個 distinct item id** 由 tasks／rewards 錨定（總 ref 3,993）；**2,225 個只錨 1 條任務**；**91%（2,294／2,517）任務有 ≥1 dependency**；dangling dep refs 只 **1／655**；**48.7% 任務冇 description** | reviewer 實跑（同我抽樣一致） |
| 現行 prompt 政策 | `fact_check`／`llm_style`／`reply_pattern`：任務只用名、唔准 hex ID；「除非 tasks／rewards 列出 heldItem.id，禁止宣稱該任務教取得／合成」；任務文字唔可以當用途證據 | grep（zh_cn.json:365/391/392） |
| 設定基建 | `config/PackAiConfig.java`（911 行 ForgeConfigSpec）；GUI 4 tab 含 **Quests tab**；**已有防劇透開關 `showHiddenQuests`（預設 false，註釋 "anti-spoiler: match quest book visibility"）**；`attachRelatedQuests`／`questMatchHotbar`／`preferObtain`；guidebook 有 `guidebookScope`／`guidebookRelatedHop` pattern | grep |
| 全量 checks baseline | 101 檔 / **4 FAIL**（3 pre-existing ＋ `check_ask_display_leak`） | 實跑 |
| 上游參考 | FTB Quests 官方 docs／changelog；SNBT 工具：PyPI `ftb-snbt-lib`、`snbtlib`、`Krutoy242/ftbq-nbt`、`zack-zzq/FTBQuestLocalizerPython` | web_search |

## 1. 需求 vs 現狀 gap

**需求**：AI 要「想／讀成條 FTB 任務線」，用嚟答 **「用呢件物品（右鍵／左鍵／觸發）會發生咩事」＋「背後系統／機制」＋「喺進度邊度用」**。

**現狀 gap（v2 更正）**
1. `QuestGuide` 只做關鍵詞命中 × top 3、描述截 120／400 字 → **冇讀成條線**（冇依賴鏈／章節順序／前後關係）；`>500KB` 檔靜默跳過。
2. **已有 `quest_fetch` 工具**，但佢今日只回**有限**內容（top-3 命中＋短描述），冇 depth／冇依賴鄰域／冇完整描述 → 要**擴充**佢，唔係新開。
3. 任務文字**被政策禁止**當用途／取得證據（只准名）→ 連任務描述白紙黑字寫「用呢件嘢做 X」都唔敢用。
4. 機制來源（右鍵／左鍵行為）**已散落**喺 `graphFacts`／KubeJS／tooltip／`[CONSUME_USE]`／`[TETRA_USE]`／`[SCROLL_*]`，但同任務線**未打通**（用户問「用嗰陣會點」時，冇一個整合答案）。

## 2. 目標 / 非目標

**目標**
- G1：由物品（id／顯示名／別名）查任務線：命中任務（tasks／rewards／description）＋**依賴鏈 depth 1–2（有出度 cap）**＋章節／order_index。
- G2：把命中任務嘅**完整描述**（去色碼／去 `{image:}`／去宣傳連結）做「點用／幾時用／點解要」嘅證據，**標來源＝任務線**。
- G3：同現有機制來源（右鍵／左鍵／消耗／觸發、KubeJS、tooltip）**並用**，答得出「用嗰陣會發生咩事」。
- G4：**擴充 `quest_fetch`**（args：`item`／`query`／`depth`／`limit`），維持喺 `FIRST_ROUND_TOOLS`／`CAPABLE_TOOLS`（**唔改 ALLOWLIST**）。
- G5：離線可驗（corpus harness）＋真機可驗（SK 5 題）。

**非目標**
- 唔讀玩家**任務完成進度**（要 FTB API／存檔）。
- 唔改任務書 UI／任務卡（除 feeding 內容）；唔引入 FTB compile-time 依賴。
- 唔把整條任務線 dump 入 git fixture（只 ≤3 任務樣本＋來源註明）。

## 3. 載重決定（R2 review 用）

| ID | 決定 | v2 立場 |
|---|---|---|
| **LD1** | 直接讀 `config/ftbquests/quests/**` SNBT（擴充 `QuestGuide`），唔用 FTB API | 保留；**但必須處理 `:138` 500KB 靜默 skip**（提高上限／分段讀／至少加 log） |
| **LD2** | 檢索式：item → 命中任務 → 依賴鄰域 depth 1–2，**每節點出度 cap ≤8**、總回傳 ≤2,000 字、命中 ≤5 | **修正**（加 cap；用 reviewer 實測數字驗） |
| **LD3** | **擴充現有 `quest_fetch`**（加 `depth`／`limit`／`full_desc` args），**唔新開工具名**、唔改 ALLOWLIST | **修正**（R1 反方：新名會被靜默丟棄） |
| **LD4** | 政策放寬：可用任務描述做用途／進度證據（標來源）；保留反幻覺規則（唔捏造、唔准 hex ID、任務名≠物品證明） | 保留（改 `fact_check`／`llm_style`／`reply_pattern` 3 語言 × 2 樹；核 7 個 quest checks） |
| **LD5** | 預算：回傳 ≤2,000 字；命中 ≤5；每描述 ≤300 字（可 config）；depth ≤2；出度 ≤8 | 保留（+cap） |
| **LD6** | 離線 harness 對真 SNBT：≥5 物品命中正確／依賴鏈正確／去色碼乾淨／**6 條真陷阱全過**／negative control 空命中老實講 | **加強**（加 6 陷阱） |
| **LD7** | 快取索引（照 `GuidebookIndexCache` 模式），**cache 放 `%APPDATA%`／mod config**（SK 2026-09-13 決定），以 mtime／檔案數失效 | **修正**（位置由 SK 定；同時解決同 §6 ALLOWLIST 嘅矛盾：cache 位置同 ALLOWLIST 無關，兩者分開講） |
| **LD8** | 唔做玩家進度 | 保留 |
| **LD9** | fixture 只可入 ≤3 任務樣本＋來源註明（pack 內容，唔可以整條線入 git） | 保留 |
| **LD10** | **描述內容衛生**：剔走色碼、`{image:}`／`hover`／`click` UI 雜訊、**贊助／宣傳連結**；保留可讀文本 | **新增**（R1 反方 F10） |
| **LD11** | **設定**：新 `questLineScope`（off／excerpt／full，預設 `excerpt`）＋沿用 `showHiddenQuests` 防劇透；GUI 加落現有 **Quests tab** | **新增**（待 SK 確認設計） |
| **LD12** | **機制並用**：答「用嗰陣會點」時，任務線描述同 `graphFacts`／KubeJS／tooltip／`[CONSUME_USE]`／`[TETRA_USE]`／`[SCROLL_*]` 一齊做證據，衝突時以遊戲事實（JEI／腳本／tooltip）優先 | **新增**（依 SK scope 補充） |

## 4. 執行內容（草案）

- **T1 harness 先行**：`tests/check_questline_index.py` 對真 50 章語料：索引正確性（2,380 item 錨定）、依賴鏈、去雜訊、6 條陷阱、negative control；**先鎖現狀 baseline**。
- **T2 索引層**：擴充 `QuestGuide`（或新 `QuestLineIndex`，內部 class）：全 chapter parse（**處理 500KB skip**）、任務節點（id／chapter／order_index／title／full description／tasks／rewards item ids／dependencies／hidden）、反向索引 item→quest、依賴圖（入度／出度）。
- **T3 檢索層**：`lookup(item|query, depth=2, limit=5, degreeCap=8)`；去色碼／UI 雜訊／宣傳連結；depth 1–2 鄰域＋章節順序。
- **T4 暴露層**：擴充 `QuestFetchAskTool`（args：`depth`／`limit`／`full_desc`）＋回傳格式（章節→任務→描述→依賴）；`toolMissNote` 講清「任務線冇相關」。
- **T5 設定層**：`PackAiConfig` 加 `questLineScope` ＋ GUI（Quests tab）＋ lang 鍵（3 語言 × 2 樹）。
- **T6 政策層**：`fact_check`／`llm_style`／`reply_pattern` 政策改動（LD4／LD12）。
- **T7 驗收**：真機 5 題（含 1 題冇任務關聯＋1 題問右鍵行為）＋全量 checks。

## 5. 驗收標準（開工前定死）

| # | 驗收項 | 通過標準 |
|---|---|---|
| V1 | harness（真語料） | ≥5 物品命中正確；依賴鏈正確；**6 條陷阱全過**：① NBT-object item ② `itemfilters:or`／`:tag` ③ CRLF ④ 轉義引號 ⑤ raw JSON component 行 ⑥ **冇 description 嘅任務（48.7%）唔可以當空命中**；negative control 老實回空 |
| V2 | 工具沿用／schema | `quest_fetch` 仍喺 `FIRST_ROUND_TOOLS`／`CAPABLE_TOOLS`；新 args 合法；**冇新增工具名**；ALLOWLIST 未改 |
| V3 | 預算（實測數字入報告） | 回傳 ≤2,000 字；命中 ≤5；每描述 ≤300；depth ≤2；出度 ≤8（用 `cold_sweat:item_insulation`／`gateways:gate_pearl`／樞紐任務 `3E9DD0B78886A183` 三個真實案例驗） |
| V4 | 全量 checks | 唔多過 baseline（4 FAIL；T0 修好後 3 FAIL） |
| V5 | 真機 | SK 5 題（含 1 冇任務關聯、1 問右鍵／左鍵行為）：任務線相關要列章節／任務／描述並可理解；冇嘅老實講；機制題要講得出觸發行為＋來源；`check_ask_display_leak` rc=0 |
| V6 | 無 regression | 7 個 quest checks 全綠；非任務題行為不變；`showHiddenQuests=false` 時唔會漏隱藏任務內容 |

## 6. 風險評估 / 最壞情況 / 還原

| 項 | 內容 |
|---|---|
| 風險 | ① 政策放寬令模型用任務文字過度推論（把獎勵當取得路徑）→ V1 negative control＋prompt 明文；② depth-2 爆量 → 出度 cap＋預算（V3 用真案例驗）；③ 500KB 靜默 skip（pack 更新後整章消失）→ T2 必須處理＋加 log；④ 描述含劇透／贊助連結 → LD10＋LD11 設定；⑤ 改 lang 撞 7 個 quest checks → V6 攔；⑥ cache 寫入位置錯（污染實例）→ 用 `%APPDATA%` |
| 最壞情況 | 任務線答案過長／唔準；唔影響資料、state、其他物品；回滾一個 commit |
| 還原 | 新增 class ＋ lang／config 字串 → `git revert <commit>`；jar 回滾＝`dist/_smoke_backups/` 備份 |
| 唔准郁 | `AskToolLoop` ALLOWLIST（**擴 `quest_fetch` 唔需要改**）；`AskReplyScrub` 段判定；`[TETRA_USE]` 語義；任務卡 UI；`check_*` 斷言（唔准為變綠改測試） |

## 7. 待 SK 決定

1. ✅ **cache 位置**：`%APPDATA%`（已答 a）
2. ⏳ **設定設計**：a) 新 `questLineScope`（off／excerpt／full，預設 excerpt）＋沿用 `showHiddenQuests`（我建議）／b) 只加 on-off／c) 唔加設定
3. ⏳（原劇透問題已由 LD10＋LD11 覆蓋，等 SK 確認設定設計即可）

## 8. Review record

| 輪 | 角色 | 比分 | 主要翻盤點 | 修改 |
|---|---|---|---|---|
| R1 | 反方 | **3:7（計劃輸）** | ① `quest_fetch` 工具**已存在**（§1 gap3 錯）＋新工具名會被 ALLOWLIST 靜默丟棄（同 §6 自相矛盾）；② `:138` 500KB 靜默 skip（headroom 3.16×）；③ depth-2 爆量（樞紐 162 dependents）；④ harness 缺 6 條真陷阱；⑤ `lang/` 唔存在（§0 錯）；⑥ 描述含贊助連結 | → **v2**（本份）：LD3 改擴充、LD2 加出度 cap、LD10 加內容衛生、§0 更正、陷阱入 V1 |
| R1 | 正方 | 6:4（計劃贏） | 7／9 條 LD 實跑站得住；同一 LD3 ALLOWLIST 阻塞；baseline 3 處錯漏（lang／／漏 `quest_fetch`／語料 byte 數） | 同上 |
| R2 | 待跑 | — | — | — |
