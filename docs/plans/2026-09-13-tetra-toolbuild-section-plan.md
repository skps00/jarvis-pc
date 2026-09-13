# Plan — Tetra「組成」歸段：零件／材料 唔應該出現喺「怎麼用」

> 觸發：SK 真機煙測（2026-09-13 14:1x，jar `450c3a76`）見到 Tetra 工具嘅**零件／材料／強化清單**被寫入「**怎麼用**」段。
> SK 原話：「why tetra's tool material is in how to use? I think it is how it craft」。
> Repo：`super_minecraft_AI_player`（雙樹 Forge 1.19.2 / NeoForge 1.21.1）。**呢份係 plan，未開工。**

---

## 0. Baseline manifest（2026-09-13 14:2x 實跑，唔准抄）

| 檢查 | rc | 備註 |
|---|---|---|
| `tests/check_tetra_tool_build.py` | 0 | ToolBuildFacts mirror |
| `tests/check_tetra_material_use.py` | 0 | |
| `tests/check_tetra_schematic_facts.py` | 0 | |
| `tests/check_reply_lang.py` | 0 | lang 檔鍵值一致 |
| `tests/check_reply_prompt_keys.py` | 0 | |
| `tests/check_reply_structure_scrub.py` | 0 | |
| `tests/check_prompt_notools_no_toolwords.py` | 0 | |
| `tests/check_dual_tree_diff_symmetry.py` | 0 | added-lines 對稱 |
| `tests/check_ask_display_leak.py` | 0 | 真機 11 題樣本 |
| `tests/check_jar_contains_fix.py` | 0 | 已部署 jar |
| **全量 python checks** | 101 檔 / **4 FAIL** | 3 = baseline（`check_ask_tool_context`／`check_heavy_script_corpus`／`check_recipe_io_and_consume_use`，已用 worktree `7317763` 證實 pre-existing）；1 = `check_ask_display_leak` 未跑真機前嘅 NO LOG LINES（今次已轉綠） |
| 兩樹檔案同步狀態 | — | `ToolBuildFacts.java` **兩樹 byte-identical**（md5 `0f344d8d`）；`ReplyLang.java` **兩樹唔同**（`571fd24d` vs `c035de1d`）→ 改動要兩樹各自落 |
| 兩樹 lang 檔 | — | forge／neoforge 同一個 lang 檔 md5 **唔同**（例如 `zh_tw.json`：`de06de4d` vs `803bccfb`）→ **6 個檔（2 樹 × 3 語）要分別改** |

## 1. 問題（實錘，唔係推測）

**真機證據**（`latest.log` cp950 解碼，`Pack AI display body` 行）：
- `tetra:modular_sword`（突擊守望）：「怎麼用」第 1 條 = 「組成零件（按劍例讀取）：刃=適應之刃、護手=異界心臟、手柄=活性手柄、劍首=狂怒眼眸、血槽=傳奇墨水…」，第 2 條 = 「已安裝強化：磨刃·傷害 5…」
- `tetra:modular_single`（噬者之杖）：「怎麼用」1–4 條 = 頭部／手柄／插槽零件＋已安裝強化；第 5 條才係工具動作
→ 零件／材料／強化 = **組成**（把呢件工具砌出嚟嘅嘢）被歸入「**怎麼用**」。

**根因（`file:line`）**
1. `logic/ReplyLang.java:1082-1090` `factCheck()` 將 `packai.reply.tool_build`（規則 23）＋ `packai.reply.tetra_use`（規則 24）**append 落 fact-check／用途指示區塊**尾。
2. `lang/*.json` → `packai.reply.tool_build`（zh_tw:459）明文寫「**先講這把的組成（parts＋socket／improvement＋名稱／id）**」，但冇指定**放邊一段**，而佢所在嘅區塊係「用途／怎麼用」語境 → 模型把「組成」寫入「怎麼用」。
3. 下游係按 heading 分段的：`AskReplyScrub.java:53/143/187-191`（`怎麼用/用途 → how_to_use`、`怎麼來 → how_to_get`）、`AskService.java:1288`、`AskCardFallback.java:29/38`、`RecipeEmbed.java:64` → 呢組 parser **只認現有 heading**。

## 2. 目標 / 非目標

**目標**：Tetra 類工具（`[TOOL_BUILD]`）嘅答案裡面，**零件／材料／插槽／改裝清單必須出現喺「怎麼來」（組成）**，唔准出現喺「怎麼用」；「怎麼用」只可以有：工具動作（Tool actions）／屬性一句／持有效果／右鍵效果。

**非目標**：
- 唔改 `ToolBuildFacts` 嘅資料內容（parts／mods 抽取邏輯唔郁）。
- 唔改卡（`render_recipe_cards`）行為、唔改 `[card:N]` 掛法。
- 唔改 `[TETRA_USE]`（材料「怎麼用」＝Tetra 工作台安裝）—— 佢本身係正確嘅用途語義（見 §3 LD6）。
- 唔改顯示層 scrub 行為。

## 3. 載重決定（review 用：逐條標「存活／死」或「站得住／有保留」）

| ID | 決定 | 現時立場 |
|---|---|---|
| **LD1** | 「組成」寫入邊一段：**用現有「怎麼來」heading**（唔新發明「組成」heading） | 採用（避免下游 parser 認唔到新 heading：§1.3 已 grep 過 4 個 parser 只認現有 heading） |
| **LD2** | 改動層：**Phase 1 prompt-only**（只改 6 個 lang 檔嘅 `tool_build` 值），`ReplyLang.java` 唔郁 | 採用（最少 diff；`ReplyLang` 兩樹唔同步，郁佢成本高） |
| **LD3** | 驗收門檻：真機 5 題 Tetra，**「零件清單出現在『怎麼用』」= 0/5**；離線加 1 個新 check 斷言 3 語言 key 都含「怎麼來」指示＋明文禁止放「怎麼用」 | 採用 |
| **LD4** | 「怎麼用」保留清單：工具動作／屬性一句／持有效果；**唔准**列零件、唔准列強化等級清單 | 採用（強化清單同零件一樣屬組成；SK 投訴包含佢） |
| **LD5** | 依賴 trace：`AskCardFallback`／`AskService:1288`／`RecipeEmbed:64`／`AskReplyScrub` 對 heading 嘅依賴已 grep（見 §1.3）→ Phase 1 唔改 heading 集合，所以**唔需要**改呢批 parser | 採用（任何「因為 code 依賴所以要保留 X」嘅聲稱要 trace 到 reader；呢度 reader 存在但唔受影响） |
| **LD6** | `[TETRA_USE]`（焦點物＝Tetra 材料）保持現狀 | 採用（佢係「材料點用」＝安裝落工作台，語義正確） |
| **LD7** | Phase 2（條件性）：若真機 5 題仍有 >0 條錯位 → 結構性分流（`ReplyLang.factCheck` 將 `tool_build` 由用途區塊搬去另一區塊／或於 `ToolBuildFacts` 輸出加 section 提示） | 採用（觸發條件寫成數字） |

## 4. 執行內容

### Phase 1（唯一開工項）— 改 6 個 lang 檔嘅 `packai.reply.tool_build`
檔案（兩樹 × 3 語）：
- `forge/1.19.2/src/main/resources/assets/packai/lang/{en_us,zh_cn,zh_tw}.json`
- `neoforge/1.21.1/src/main/resources/assets/packai/lang/{en_us,zh_cn,zh_tw}.json`

改動要點（措辭由 cursor-agent 落實，意思必須齊）：
1. **明文指定段位**：零件／材料／插槽／改裝（installed modules、materials、sockets、improvements）＝「**組成**」資訊 → **必須寫喺「怎麼來」段**（第一條就可以係「組成：刃=…／護手=…」，用現有 heading，唔准新發明 heading）。
2. **明文禁止**：呢批組成資訊 **唔准**出現喺「怎麼用」段。
3. 「怎麼用」只准寫：工具動作（Tool actions: cut／mine／dig 等）、屬性一句（攻擊／攻速／耐久）、持有效果／右鍵效果。
4. 保留原有約束：唔准倒 tooltip 戰鬥／魔法數值；`ns:path` 行係已裝材料（唔准猜）；唔准原樣貼 `[TOOL_BUILD]`；空白 modular 框架合成（切石機＋木棍）唔可以當取得方式。
5. 英文／簡中／繁中三份語義一致。

### Phase 2（條件性，唔係今次開工項）
觸發條件：真機抽樣 5 題仍有 ≥1 題「零件／強化清單」出現喺「怎麼用」。
內容：`ReplyLang.factCheck()` 將 `tool_build`／`tetra_use` 由用途區塊搬去專屬區塊（兩樹各自改）＋ 相應 lang key 重排；需重跑 `check_reply_lang`／`check_reply_prompt_keys`／`check_dual_tree_diff_symmetry`。

## 5. 驗收標準（開工前已定；完成後逐項實跑）

| # | 驗收項 | 通過標準 |
|---|---|---|
| V1 | 新增 `tests/check_prompt_tool_build_section.py` | 3 語言 key：含「怎麼來／How to get」段位指示；含禁止放「怎麼用」；唔含 `[TOOL_BUILD]` 字面標籤。**正負對照**：用改前嘅舊值跑要 FAIL（證檢查唔係假綠） |
| V2 | 6 個 lang 檔 JSON 合法＋鍵齊 | `python -c json.load` 全部 OK；`check_reply_lang.py` rc=0 |
| V3 | 全套 python checks | 唔可以多過 baseline（今次 baseline 3 FAIL；唔准新增） |
| V4 | 雙樹對稱 | `check_dual_tree_diff_symmetry.py` rc=0 |
| V5 | 真機煙測 | SK 問 5 題 Tetra（含 modular_sword／modular_single）→ 抽 `display body` 行：**「怎麼用」段冇零件／強化清單 = 5/5**；「怎麼來」段有組成資訊；卡片照出；`check_ask_display_leak.py` rc=0 |
| V6 | 冇 regression | 非 Tetra 題（例：普通合成物）答案結構唔變 —— 抽 3 題舊 log vs 新 log 對照 |

## 6. 風險評估 / 最壞情況 / 還原（第一規則）

| 項 | 內容 |
|---|---|
| 風險 | ① 模型仍然照舊寫（prompt 指示唔夠硬）→ Phase 2 觸發；② 措辭改動令 Tetra 答案變差（例如模型索性唔講組成）；③ 6 個檔改漏一個 → 某語言行為唔一致 |
| 最壞情況 | Tetra 答案質素下降（唔影響其他物品、唔影響資料、唔影響 state）；最壞要回滾一個 commit |
| 還原 | **純 lang 檔改動**：`git revert <commit>` 即回到現狀（零資料損失）；真機則重新 `gradlew jar` + 部署舊 jar（`dist/_smoke_backups/packai-0.2.1+mc1.19.2-forge.jar.bak-20260913_133727`，sha `17ebc474` = 改動前版本） |
| 前置依賴 | 無新依賴；`funasr`／torch 無關；唔郁 `ToolBuildFacts` 資料層 |
| 唔准郁 | `AskToolLoop` ALLOWLIST／`canonicalArgsJson`；`AskReplyScrub` 段判定行為；`[TETRA_USE]` 語義；卡工具 |

## 7. 執行順序 ＋ 每個 task 落地即 self-review（SK 規則）

1. **T1** lang 6 檔（措辭）→ self-review：JSON 合法＋`check_reply_lang`／`check_reply_prompt_keys`／`check_dual_tree_diff_symmetry`；逐行睇 diff；確認冇動其他 key。
2. **T2** 新 check `check_prompt_tool_build_section.py`（含正負對照）→ self-review：舊值要 FAIL、新值要 PASS；全量 checks 唔增 FAIL。
3. **T3** build jar（`gradlew jar`；`JAVA_HOME` = JDK17）→ 備份現 jar → 部署（照 skill：`dist/_smoke_backups/` 留備份、mods 只留一個 packai jar、三邊 sha256 一致）。
4. **T4** 真機 5 題（SK 配合）→ 抽 log 判 V5；未達標 → Phase 2 或停手問 SK。
5. 全程：`packai code 一律經 cursor-agent`；唔 commit／push 直到 SK 講。

## 8. Review record（會逐輪填）

- R1：待跑（反方／正方／中立裁判）
- 載重決定存活表、比分、flip conditions → 見下一節更新。
