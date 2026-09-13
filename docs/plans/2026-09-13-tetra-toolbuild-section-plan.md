# Plan v2 — Tetra「組成」歸段：零件／材料／強化 唔應該出現喺「怎麼用」

> 觸發：SK 真機煙測（2026-09-13 14:1x，jar `450c3a76`）見到 Tetra 工具嘅**零件／材料／強化清單**被寫入「**怎麼用**」段。
> SK 原話：「why tetra's tool material is in how to use? I think it is how it craft」。
> Repo：`super_minecraft_AI_player`（雙樹 Forge 1.19.2 / NeoForge 1.21.1）。**呢份係 plan，未開工。**
>
> **v2 改動（R1 反方 4:6 → 修）**：① 範圍由「6 檔 × 1 key」修正為「**6 檔 × 3 key（`tool_build`＋`llm_style`＋`llm_style_notools`）**」＋加資料層單一編輯（`ToolBuildFacts.format()`）；② V1 重寫（保住 `[TOOL_BUILD]` literal，否則撞 `check_reply_prompt_keys.py:378`）；③ 新 rule 明文 scope 到 `[TOOL_BUILD]` 實例、排除 `[TETRA_USE]`（rule 12/24 及 `:434-438` 測試鎖）；④ 加**機械化錯位量測** `check_tetra_reply_section.py`（n 由 5 → 15）；⑤ §0 baseline 更正為 3 FAIL；⑥ 加 lang SoT 漂移防護。

---

## 0. Baseline manifest（2026-09-13 14:2x 實跑；R1 反方／正方各自獨立重跑核對一致）

| 檢查 | rc | 備註 |
|---|---|---|
| `tests/check_tetra_tool_build.py` | 0 | ToolBuildFacts mirror |
| `tests/check_tetra_material_use.py` | 0 | |
| `tests/check_tetra_schematic_facts.py` | 0 | |
| `tests/check_reply_lang.py` | 0 | |
| `tests/check_reply_prompt_keys.py` | 0 | ⚠️ `:378` 硬鎖 `tool_build` 必含 `[TOOL_BUILD]`；`:434-438` 鎖 fact_check 規則 12／24 措辭 |
| `tests/check_reply_structure_scrub.py` | 0 | |
| `tests/check_prompt_notools_no_toolwords.py` | 0 | |
| `tests/check_dual_tree_diff_symmetry.py` | 0 | added-lines 對稱 |
| `tests/check_ask_display_leak.py` | 0 | 真機 13 題樣本（已由 NO LOG LINES 轉綠） |
| `tests/check_jar_contains_fix.py` | 0 | 已部署 jar |
| **全量 python checks** | 101 檔 / **3 FAIL**（**v1 誤寫 4，已更正**） | 3 = pre-existing（`check_ask_tool_context`／`check_heavy_script_corpus`／`check_recipe_io_and_consume_use`；已用 worktree `7317763` 證實） |
| 兩樹 Java 同步 | — | `ToolBuildFacts.java` **byte-identical**（`0f344d8d`）；`ReplyLang.java` 唔同步（`571fd24d` vs `c035de1d`，diff 5 行＝全部註釋） |
| 兩樹 lang 檔 | — | 6 個檔（2 樹 × 3 語）md5 兩樹唔同；但 `tool_build` **值跨樹 byte-identical**（672／309／309） |

## 1. 問題（實錘）

**真機證據**（`latest.log` cp950 解碼）：
- `14:10:57` `tetra:modular_sword`「怎麼用」1.＝「組成零件（按劍例讀取）：刃=適應之刃、護手=異界心臟、手柄=活性手柄、劍首=狂怒眼眸、血槽=傳奇墨水」；2.＝「已安裝強化…」
- `14:16:58` `tetra:modular_single`「怎麼用」1–4＝頭部／手柄／插槽零件＋已安裝強化；5.＝工具動作
- `14:16:51/52` prompt dump：`role=tool` content = `[PURPOSE]\n[TOOL_BUILD] socket single/binding…`，同一 chunk `[TETRA_USE]` = **-1（不在場）** → **今次症狀唔係 rule 24 引起**

**根因**（`file:line`，逐條已 grep 核實）
1. `logic/ReplyLang.java:1082-1090` `factCheck()` append `tool_build`（規則 23）＋`tetra_use`（規則 24）落**用途／fact-check 指示區塊**。
2. **最大反向拉力（v1 漏咗）**：`lang/en_us.json:361-362`（`llm_style`／`llm_style_notools`）明文「When PURPOSE has [TOOL_BUILD]: **lead with** this instance's parts／sockets／improvements」，經 `client/LlmClient.java:378` `ReplyLang.llmStyle()` **注入每一條 prompt** → 模型必然最先講組成。
3. `AskService.java:449-456`：`[TOOL_BUILD]` 係 **prepend 喺 `[PURPOSE]` 區塊內**，而 `llm_style` 定義 PURPOSE＝用途 → 組成資料一出世就坐喺「用」語境。
4. 下游 heading 係**閉集**：`AskReplyScrub.java:53/143/185-199`（`怎麼來→how_to_get`）、`AskCardFallback.java:29/37/38`、`RecipeEmbed.java:64/66`、`AskService.java:1287-1288`；`canonicalSectionKey` 對未知 label 只 `return lower`（`:199`）→ **新發明「組成」heading 會靜默漏卡**（`grep -rn "組成\|组成" forge neoforge` = 零命中）。

## 2. 目標 / 非目標

**目標**：`[TOOL_BUILD]` 在場嘅答案裡，**零件／材料／插槽／強化（組成）必須喺「怎麼來」段**，「怎麼用」段**零**組成清單；「怎麼用」只准：工具動作（Tool actions）／屬性一句／持有效果／右鍵效果。

**非目標**：
- 唔改 `ToolBuildFacts` 嘅抽取邏輯（只可加一行段位提示）。
- 唔改卡（`render_recipe_cards`）／`[card:N]` 掛法／顯示層 scrub 行為。
- **唔改 `[TETRA_USE]`（焦點物＝Tetra 材料）語義**：材料「怎麼用」＝安裝落 Tetra 工作台，係正確用途（rule 12／24，被 `check_reply_prompt_keys.py:434-438` 鎖）。
- 唔改 `ReplyLang.java`（v1 立場保留；Phase 2 才考慮，見 §3 LD8）。

## 3. 載重決定（R2 review 用：逐條標「存活／死」）

| ID | 決定 | v2 立場 |
|---|---|---|
| **LD1** | 「組成」用**現有「怎麼來」heading**，唔新發明 heading | 保留（R1 雙方一致站得住；新 heading 會漏卡） |
| **LD2** | Phase 1 **唔郁 `ReplyLang.java`** | 保留（`factCheck` 係唯一 append 點；兩樹唔同步，郁佢成本高） |
| **LD3** | Phase 1 edit set = **6 檔 × 3 key**（`tool_build`／`llm_style`／`llm_style_notools`）＋ **`ToolBuildFacts.format()` 加段位提示行**（兩樹 byte-identical ⇒ 單一 canonical edit，mirror 已用 substring/startswith assert） | **修正**（v1 只改 1 key → 被反方判死） |
| **LD4** | 「怎麼用」保留清單＝工具動作／屬性／持有效果；**唔准**列零件、強化、插槽 | 保留（parts 同 mods 同屬一次 scan：`ToolBuildFacts.java:60/76`） |
| **LD5** | 下游 4 個 parser 唔需要改（heading 集不變） | 保留（R1 雙方 trace 一致） |
| **LD6** | 新 rule 明文 **scope 到 `[TOOL_BUILD]` 在場嘅實例**，並寫明「`[TETRA_USE]` 在場時嘅零件用途說明仍跟規則 24」 | **加強**（免 rule 23/24 自相矛盾；`:434-438` 測試鎖） |
| **LD7** | 量測機械化：新 check `tests/check_tetra_reply_section.py` 讀 `latest.log`，斷言「**「怎麼用」段區間內零命中 `零件\|強化\|插槽\|improvement`**」；真機抽樣 **5 題 × 3 次 = 15 樣本**，門檻 **≤1/15** | **修正**（v1 靠 n=5 人眼，統計力不足：真錯率 10% 時有 59% 誤判） |
| **LD8** | Phase 2（條件性）：若機械化量測 ≥2/15 錯位 → 結構性分流（`ReplyLang.factCheck` 區塊次序／`AskService` prepend 位置） | 修正（觸發由人眼改數字；並納入 `AskService:449-456` prepend 位置） |
| **LD9** | 文件誠實性：量測殘餘風險明寫（15 樣本、真錯率 10% → 仍有 21% 誤判「已修好」） | 新增（唔准扮夠統計力） |

## 4. 執行內容

### Phase 1（今次開工項）

**T1a — lang 6 檔 × 3 key = 18 處 value**（措辭由 cursor-agent 落實）：
- `tool_build`（規則 23）：明文「零件／材料／插槽／強化＝**組成** → **必須寫喺「怎麼來」段**（第一條就係「組成：刃=…／護手=…」，用**現有 heading**，唔准新發明）；**唔准**出現喺「怎麼用」；本規則**只**適用 `[TOOL_BUILD]` 在場；`[TETRA_USE]` 在場時跟規則 24」
- `llm_style`／`llm_style_notools`：把「[TOOL_BUILD] → **lead with** parts/sockets/improvements」改為「組成寫入 **How to get／怎麼來**；**唔准**喺 How to use／怎麼用 領頭」；**保留** `[TOOL_BUILD]` literal token（`check_reply_prompt_keys.py:378` 需要）
- 其三語語義一致；保留原有約束（唔准倒 tooltip 戰鬥數值、`ns:path` 唔准猜、唔准原樣貼 `[TOOL_BUILD]`、空白 modular 框架合成唔算取得方式）。
- 檔案：`{forge/1.19.2,neoforge/1.21.1}/src/main/resources/assets/packai/lang/{en_us,zh_cn,zh_tw}.json`

**T1b — 資料層段位提示**：`logic/ToolBuildFacts.format()` 首行加一行（例如 `組成（怎麼來／How to get）：`），兩樹各自落（byte-identical 起點）；確認 mirror（`check_tetra_tool_build.py` 用 `startswith`／substring）唔會紅。

**T2a — 新 check** `tests/check_tetra_reply_section.py`：
- 讀 `latest.log`（沿用 `check_ask_display_leak.py` 嘅 Prism 路徑＋cp950 解碼寫法），抽 `Pack AI display body`；
- 切段（複用 `AskReplyScrub` heading 詞彙：`怎麼用|用途|How to use` vs `怎麼來|怎樣來|How to get`），斷言「**怎麼用段零命中 `零件|強化|插槽|improvement|part `**」；
- 支援 `--fixture`（離線樣本）＋ `--min-samples N`；
- **正負對照**：用今次真機 14:10:57／14:16:58 兩條已知錯位 body 做 fixture → 必須 FAIL；清乾淨樣本 → PASS（證檢查唔係假綠）。

**T2b — （低優先，防漂移）**`tests/update_reply_prompts.py` 加 `tool_build`／`llm_style`／`llm_style_notools` 入 `KEYS`；並喺 `tests/gen_reply_lang_json.py` 檔頭加硬警告（佢會剷走清單外 `packai.reply.*`，現時因 `ROOT` 指向唔存在路徑而跑唔到 = latent footgun）。若 cursor 判斷風險高，可只加警告唔改 KEYS（留待 Phase 2）。

### Phase 2（條件性，唔係今次開工項）
觸發：機械化量測 **≥2/15 錯位**。內容：`ReplyLang.factCheck()` 區塊次序重排（兩樹各自改）＋ `AskService.java:449-456` 嘅 `[TOOL_BUILD]` prepend 位置改放（唔再寄生喺 `[PURPOSE]` 內）；需重跑 `check_reply_lang`／`check_reply_prompt_keys`／`check_dual_tree_diff_symmetry`／`check_reply_structure_scrub`。

## 5. 驗收標準（開工前定死）

| # | 驗收項 | 通過標準 |
|---|---|---|
| V1 | lang 3 key 文本檢查（**係文本代理，唔係結果 gate**） | 3 語言 × 3 key 都帶段位指示（怎麼來／How to get）＋明文禁止「怎麼用」＋**保留** `[TOOL_BUILD]` literal（令 `check_reply_prompt_keys.py:378` 續綠）；唔准新增對規則 12／24 嘅衝突措辭 |
| V2 | 6 lang 檔 JSON 合法＋鍵齊 | `json.load` ×6 OK；`check_reply_lang.py` rc=0；`check_reply_prompt_keys.py` rc=0 |
| V3 | 全套 python checks | **唔可以多過 3 FAIL**（baseline；唔准新增） |
| V4 | 雙樹對稱 | `check_dual_tree_diff_symmetry.py` rc=0；`check_tetra_tool_build.py` rc=0（mirror 唔紅） |
| V5 | **機械化真機量測**（主要 gate） | SK 問 5 題 Tetra × 3 輪 = 15 樣本；`check_tetra_reply_section.py` 錯位 ≤1/15；「怎麼來」段有組成資訊；卡片照出；`check_ask_display_leak.py` rc=0 |
| V6 | 無 regression | 非 Tetra 題抽 3 題（改前 vs 改後 log）結構一致；`[TETRA_USE]` 題（例：焦點＝Tetra 材料）行為不變 |
| V7 | 殘餘風險聲明 | 報告明寫：15 樣本在真錯率 10% 下仍有 ~21% 誤判機會（唔准講「已確定修好」） |

## 6. 風險評估 / 最壞情況 / 還原（第一規則）

| 項 | 內容 |
|---|---|
| 風險 | ① 改措辭仍唔夠硬（llm_style 拉力未消）→ Phase 2；② 18 處 value 漏改／不一致（6 檔）→ V2 攔；③ `ToolBuildFacts` 加提示行撞 mirror assert → T1b 即場跑 `check_tetra_tool_build`；④ rule 23 新措辭撞 rule 12／24 → LD6 scope 句＋V1 條款；⑤ 模型索性唔講組成（過度抑制）→ V5 抽樣要睇「怎麼來」段有冇內容 |
| 最壞情況 | Tetra 答案質素下降（其他物品、資料、state 不受影響）；最壞回滾一個 commit |
| 還原 | 純 lang／一行 Java 字串改動 → `git revert <commit>`；真機回滾＝重新 `gradlew jar` 並部署 `dist/_smoke_backups/packai-0.2.1+mc1.19.2-forge.jar.bak-20260913_133727`（sha `17ebc474`） |
| 前置依賴 | 無新依賴；唔郁 torch／funasr；`gradlew jar`（`JAVA_HOME`=JDK17）已驗過 16s |
| 唔准郁 | `AskToolLoop` ALLOWLIST／`canonicalArgsJson`；`AskReplyScrub` 段判定行為；`[TETRA_USE]` 語義；卡工具；`check_reply_prompt_keys.py` 現有斷言（唔准為變綠而改測試） |

## 7. 執行順序 ＋ 每 task 落地即 self-review

1. **T1a** lang 18 處 → self-review：`json.load` ×6；`check_reply_lang`／`check_reply_prompt_keys`／`check_dual_tree_diff_symmetry`；逐行睇 diff（唔准動其他 key）；確認三語語義一致。
2. **T1b** `ToolBuildFacts.format()` 提示行 → self-review：`check_tetra_tool_build.py`／`check_tetra_schematic_facts.py`／`check_tetra_material_use.py` rc=0；兩樹 diff 對稱。
3. **T2a** 新 check（含正負對照 fixture）→ self-review：已知錯位樣本 FAIL、乾淨樣本 PASS；全量 checks 唔增 FAIL。
4. **T2b**（低優先）SoT 防護。
5. **T3** build jar → 備份現 jar（`dist/_smoke_backups/`）→ 部署（三邊 sha256 一致；mods 只留一個 packai jar）。
6. **T4** 真機 15 樣本（SK 配合，3 輪 × 5 題）→ 判 V5；未達標 → Phase 2 或停手問 SK。
7. 全程：packai code **一律經 cursor-agent**；唔 commit／push 直到 SK 講；每 task 完成即 review，有 bug 即修（SK 規則）。

## 8. Review record

| 輪 | 角色 | 比分 | 主要翻盤點 | 計劃嘅實質修改 |
|---|---|---|---|---|
| R1 | 反方 | **4:6（計劃／反方）** | LD2 死（漏 `llm_style`／`llm_style_notools` 反向拉力）；LD3 死（V1 撞 `check_reply_prompt_keys.py:378`＋係弱文本代理）；rule 23 撞 rule 12／24（測試鎖 `:434-438`）；§0 baseline 誤寫 4 FAIL | — |
| R1 | 正方 | **7:3（計劃／正方）** | 五條 LD 站得住；扣分集中量度設計（n=5 統計力、lang SoT 漂移、rule scope） | — |
| **R1 綜合** | 中立 | 4:6 → **未達 8:2** | 核心命題「只改 6 檔 1 key 就夠」被證偽 | **v2**：LD3 改 3 key＋資料層提示；V1 重寫；LD6 scope 句；LD7 機械化量測（15 樣本）；§0 更正 3 FAIL；新增 LD9 殘餘風險聲明 |
| R2 | 待跑 | — | — | — |
