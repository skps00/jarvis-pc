# Plan v3 — Tetra「組成」歸段（＋ T5 真機發現嘅 `role=` 洩漏）

> 觸發：SK 真機煙測（2026-09-13，jar `450c3a76`）：① Tetra 工具嘅零件／材料／強化清單被寫入「怎麼用」；② 最新答案嘅【來源】行出現內部欄位名 `role=output／input`（真洩漏，令 `check_ask_display_leak.py` 由綠變紅）。
> Repo：`super_minecraft_AI_player`（雙樹）。**呢份係 plan，未開工。**
>
> **v3 改動（R2 反方 4:6 → 修；以下全部有 R2 實跑證據）**：
> 1. **拆錯 causal 假設**：v2 打算喺 `ToolBuildFacts.format()` **首行**加提示 —— 實測會撞 mirror：`check_tetra_tool_build.py:296/321/322` 係 `startswith(HEADER)`、`:365` 係 **exact equality**（`empty_mod == HEADER + "\n" + UNPARSED`）；而且 mirror 係**另一份 Python 重寫**（`format_scan:143-170`），repo **冇任何 test** 比對 Java 輸出 == mirror 輸出 → 只改 Java 會**靜默失同步（假綠）**。⇒ **取消 v2 T1b**，改為「先量度、後改、再量度」實驗設計。
> 2. **量測 harness 三處硬傷修正**（R2 實測）：`latest.log` **cp950 strict 解碼會失敗**（byte `0x99` @1445831）→ 現有 `check_ask_display_leak.py:44-50` 會 fallback **cp1252**（CJK 全變 mojibake）；display body 係**單一 log 行**、內含**字面 `\n`**（backslash+n），唔 unescape 就切唔到段；真機 heading 係**簡體**「怎么来／怎么用」而 v2 regex 只列繁體。
> 3. **統計設計重做**：v2 寫 15 樣本 + 門檻 ≤1/15 ⇒ 我自己用二項分佈計：假過率 **p=0.05 → 82.9%**、p=0.10 → **54.9%**、p=0.20 → 16.7%（v2 寫嘅「21%」係用錯規則＝thr=0 嘅數）。⇒ 改為 **門檻 0 且 n ≥ 29**（p=0.10 → 假過 4.7%）或 **門檻 ≤1 且 n ≥ 46**（4.8%）。
> 4. **§0 baseline 第二次更正**：現時真係 **4 FAIL**（3 個 pre-existing ＋ `check_ask_display_leak` 因新款真洩漏轉紅）→ 真洩漏列做 **D0 前置**。
> 5. **LD6 補 rule 12**：`check_reply_prompt_keys.py:434-438` 鎖嘅係 **rule 12**（`[TETRA_USE]` 在場時「怎麼用」必須寫 Tetra 工作台安裝），v2 只 scope 咗 rule 24 → 兩 rule 同時在場會對撞。⇒ scope 句同時點名 rule 12＋24。
> 6. **規模更正**：3 key 值**跨樹 byte-identical** ⇒ 實際只需設計 **9 條 unique 文本**（寫入 18 處）。
> 7. **SoT 防護升級為必做**（R2 F5）：`tests/update_reply_prompts.py:11-16` 嘅 `KEYS` 生成 `llm_style`，`:566-576` `--full` 會用 EN dict **覆寫** `llm_style`（EN dict 冇新措辭）→ 跑一次就把 T2 還原。⇒ 加入 3 key 入 `KEYS` ＋封 `--full` 覆寫。

---

## 0. Baseline manifest（2026-09-13 14:5x 實跑；R1／R2 reviewer 各獨立核對）

| 檢查 | rc | 備註 |
|---|---|---|
| `tests/check_tetra_tool_build.py` | 0 | mirror（`startswith` ＋ `:365` exact） |
| `tests/check_tetra_material_use.py` / `check_tetra_schematic_facts.py` | 0 / 0 | |
| `tests/check_reply_lang.py` / `check_reply_prompt_keys.py` | 0 / 0 | `:378/391` 鎖 `[TOOL_BUILD]` literal；`:434-438` 鎖 **rule 12** |
| `tests/check_reply_structure_scrub.py` / `check_prompt_notools_no_toolwords.py` | 0 / 0 | |
| `tests/check_dual_tree_diff_symmetry.py` | 0 | added-lines 對稱 |
| **`tests/check_ask_display_leak.py`** | **1（紅）** | **真洩漏**：`latest.log` body[3]（`gud_toolkit:miracle_milk`）【來源】行寫 `配方卡 role=output／input`；另 `PURPOSE` 字面都出現喺同一行 |
| `tests/check_jar_contains_fix.py` | 0 | 已部署 jar |
| **全量 python checks** | 101 檔 / **4 FAIL**（**v1 寫 4、v2 寫 3 都唔準，以實跑為準**） | 4 = `check_ask_tool_context`／`check_heavy_script_corpus`／`check_recipe_io_and_consume_use`（pre-existing，worktree `7317763` 證實）＋ `check_ask_display_leak`（新真洩漏） |
| 兩樹 Java | — | `ToolBuildFacts.java` byte-identical `0f344d8d`；`ReplyLang.java` 唔同步（`571fd24d`/`c035de1d`，diff 5 行＝註釋）；`LlmClient.java` 兩樹同 |
| 兩樹 lang 6 檔 | — | 3 key 值跨樹 byte-identical（`tool_build` 672/309/309、`llm_style` 8266/4199/4199、`llm_style_notools` 8292/4056/4055） |
| 真機樣本 | — | `latest.log` 2.85MB：**16 條 display body**，其中 **3 條**係已知 Tetra 錯位（`14:10:57` modular_sword、`14:16:58` modular_single ×2） |
| 解碼事實 | — | `latest.log` **cp950 strict 失敗**（`0x99` @1445831）→ 必須 **逐行 `cp950, errors="replace"`**；body 內容係字面 `\n` 要 unescape |

## 1. 問題（實錘）

**P1 — Tetra 組成歸錯段**（真機 14:10:57／14:16:58，同 v1／v2 §1 一致）
- 根因鏈：`ReplyLang.java:1082-1090` `factCheck()` append `tool_build`＋`tetra_use`；`lang/en_us.json:361-362` `llm_style`／`llm_style_notools` 明文「[TOOL_BUILD] → **lead with** parts/sockets/improvements」經 `LlmClient.java:378` 注入**每一條** prompt；`AskService.java:449-456` 將 `[TOOL_BUILD]` **prepend 喺 `[PURPOSE]` 區塊內**；`AskEngine.java:516-518` 將該區塊掛喺 `ReplyLang.sectionHowToUse`（`## 怎麼用`）→ **結構上，組成資料一出世就坐喺「怎麼用」段**（R1＋R2 雙方各自 trace）。
- 下游 heading 係閉集（`AskReplyScrub:53/143/185-199`、`AskCardFallback:29/37/38`、`RecipeEmbed:64/66`、`AskService:1287-1288`）→ 新增「組成」heading 會靜默漏卡（`grep 組成` = 0 命中）。

**P2 — `role=` 真洩漏（T5 新發現）**
- 顯示 body：【來源】JEI（**配方卡 role=output／input**）、物品用途資料（**PURPOSE**：可飲用）、整合包本地取得索引（無掉落／任務路徑）
- 內部欄位名／區塊名（`role=`、`PURPOSE`）出現喺玩家可見文字 → 屬顯示層洩漏；`check_ask_display_leak.py:88-90` 已斷言禁止 `role=`。

## 2. 目標 / 非目標

**目標**
- G1：`[TOOL_BUILD]` 在場嘅答案，「怎麼來」段＝組成（零件／材料／插槽／強化）；「怎麼用」段零組成清單。
- G2：玩家可見文字**零**內部欄位名（`role=`、`PURPOSE` 等）→ `check_ask_display_leak.py` 回綠。
- G3：量度機械化＋有統計力（可重跑、可對前後比較）。

**非目標**
- 唔改 `ToolBuildFacts` 抽取邏輯（v3 明確**唔加**首行提示；見 §4）。
- 唔改卡／`[card:N]`／`[TETRA_USE]` 語義／`AskReplyScrub` 段判定行為。
- 唔改 `ReplyLang.java`（除非 Phase 2 觸發）。

## 3. 載重決定（R3 review 用）

| ID | 決定 | v3 立場 |
|---|---|---|
| **LD1** | 用**現有「怎麼來」heading** | 保留（R1/R2 雙方一致；新 heading 漏卡） |
| **LD2** | 唔郁 `ReplyLang.java`（Phase 1） | 保留 |
| **LD3** | Phase 1 edit set ＝ 6 檔 × 3 key（**18 處寫入、9 條 unique 文本**）；**取消** v2 嘅資料層提示行 | **修正**（R2 證據：mirror exact assert ＋無 Java↔mirror cross-check） |
| **LD4** | 「怎麼用」只准工具動作／屬性／持有效果／右鍵效果 | 保留 |
| **LD5** | 下游 4 parser 唔需要改 | 保留 |
| **LD6** | 新 rule 明文 scope：只適用 `[TOOL_BUILD]` 在場；`[TETRA_USE]` 在場時**跟 rule 12 同 rule 24** | **再修正**（R2 F6：必須同時點名 rule 12） |
| **LD7** | 量測門檻：**0 錯位 且 n ≥ 29**（p=0.10 → 假過 4.7%）；或 **≤1 且 n ≥ 46**（4.8%） | **重做**（v2 的 15/≤1 = 假過 54.9%） |
| **LD8** | Phase 2（條件性）：結構性分流 —— 將 `[TOOL_BUILD]` 由 `[PURPOSE]` 區塊搬出（`AskService.java:449-456`），並掛喺 `ReplyLang.sectionHowToGet`（`AskEngine.java:516-518`）之下 | 修正（由 v2 嘅「搬 ReplyLang 區塊」改為對準真正結構成因） |
| **LD9** | 殘餘風險逐項聲明（唔准只寫一個數字） | 修正（見 §5 V7 清單） |
| **LD10** | **實驗次序**：先量度（現狀 baseline rate）→ 後改 → 再量度同一 harness；兩邊樣本量同門檻 | **新增**（令因果可驗） |

## 4. 執行內容

### T0（前置，修 T5 發現嘅洩漏 — 獨立於 Tetra）
- 範圍：令玩家可見文字唔出現內部欄位名（`role=`、`PURPOSE`）。實作待 cursor 判斷（最小：來源行措辭＋scrub 白名單；唔准為變綠而放寬 `check_ask_display_leak.py`）。
- 驗收：`check_ask_display_leak.py` rc=0（真機 log 16 條全過）；全量 checks 由 4 FAIL 回落 **3 FAIL**。

### T1（量測 harness，先做，用嚟做前後對照）
- 新 `tests/check_tetra_reply_section.py`：
  1. 逐行 `cp950, errors="replace"` 解碼（**唔可以**沿用 whole-file 多 codec 嘗試）；
  2. unescape 字面 `\n`；
  3. heading 需同時涵蓋**簡繁**（`怎么来|怎麼來|怎样来|怎樣來` vs `怎么用|怎麼用|用途`），限行首；
  4. 段界：止於下一個 heading 或 `【來源】`／`[Sources]`；
  5. 斷言「怎麼用」段零命中 `零件|強化|插槽|improvement|part `；
  6. **no-heading 樣本 = FAIL/INCONCLUSIVE（唔准 skip，唔准當過）**；
  7. `--fixture`（已知 3 條錯位 body 必須 FAIL；構造乾淨樣本 PASS）＋ `--min-samples N`（預設 29）；
  8. 樣本來源支援：`latest.log` ＋ `logs/*.log.gz` 歷史（累積到 n≥29）。
- 先跑現狀 → 記低 **baseline 錯位率**（現有 3 條已知錯位；樣本量會隨 SK 再問而增）。

### T2（Phase 1 改動）
- 6 檔 × 3 key（`tool_build`／`llm_style`／`llm_style_notools`）＝18 處寫入、9 條 unique 文本：
  - 刪走「lead with／先講組成」嘅**段位未定**寫法；
  - 明文：組成（零件／材料／插槽／強化）→ **寫入「怎麼來」段**（用現有 heading）；**唔准**出現喺「怎麼用」；此規則**只**適用 `[TOOL_BUILD]` 在場；`[TETRA_USE]` 在場時**跟 rule 12／24**（材料安裝仍屬「怎麼用」）；
  - **保留** `[TOOL_BUILD]` literal token（`check_reply_prompt_keys.py:378/391`）。
- **SoT 防護（必做）**：`tests/update_reply_prompts.py` `KEYS` 加 3 key；封 `--full` 對 `llm_style`／`llm_style_notools` 嘅覆寫（或加 assert）。
- 唔郁 `ToolBuildFacts`（v2 T1b 已取消）。

### T3（改後量度）
- 同一 harness、同一門檻（**0 錯位 且 n≥29**）：達標 → Phase 1 收貨；未達標 → 進 Phase 2。

### Phase 2（條件性）
- 觸發：T3 顯示 ≥1/29 錯位。內容：結構性分流（`AskService.java:449-456` 抽出 `[TOOL_BUILD]`；`AskEngine.java:516-518` 掛喺 `sectionHowToGet` 之下），兩樹各自改；重跑 `check_reply_lang`／`check_reply_prompt_keys`／`check_dual_tree_diff_symmetry`／`check_reply_structure_scrub`。

## 5. 驗收標準（開工前定死）

| # | 驗收項 | 通過標準 |
|---|---|---|
| V0 | T0 洩漏修復 | `check_ask_display_leak.py` rc=0；全量 checks ≤3 FAIL |
| V1 | lang 3 key 文本（**文本代理，唔係結果 gate**） | 3 語言 × 3 key：帶段位指示＋明文禁「怎麼用」＋保留 `[TOOL_BUILD]` literal＋唔撞 rule 12／24 措辭 |
| V2 | lang JSON／鍵齊 | `json.load` ×6；`check_reply_lang`／`check_reply_prompt_keys` rc=0 |
| V3 | 全量 python checks | **≤3 FAIL**（T0 修好後嘅 baseline） |
| V4 | 雙樹對稱 | `check_dual_tree_diff_symmetry`／`check_tetra_tool_build` rc=0（後者證明冇動 mirror） |
| V5 | **機械化真機量測（主要 gate）** | `check_tetra_reply_section.py`：**0 錯位 且 n≥29**（或 ≤1 且 n≥46）；「怎麼來」段有組成資訊；卡片照出 |
| V6 | 無 regression | 非 Tetra 題抽 3 題（改前 vs 改後）結構一致；`[TETRA_USE]` 題行為不變 |
| V7 | 殘餘風險逐項聲明（唔准只寫一個數） | 必須列：① `LlmClient.java:473` `temperature=0.2`（單抽樣、非零隨機）；② 只測過一個 prompt 版本；③ 量度對象＝**scrub 後** body 非模型原始輸出；④ 樣本**非獨立**（同一 JVM／session、同一 log）；⑤ 舊 log 內 3 條改前錯位樣本要排除；⑥ 真機 body 只出現**簡體**（en_us／zh_tw 從未煙測）；⑦ 門檻對應嘅假過率數字（p=0.05／0.10／0.20 列齊） |

## 6. 風險評估 / 最壞情況 / 還原（第一規則）

| 項 | 內容 |
|---|---|
| 風險 | ① 改措辭唔夠硬 → Phase 2（已定數字觸發）；② 18 處寫入漏改／不一致（6 檔）→ V2 攔；③ 改動撞 `check_reply_prompt_keys.py` 約 100 條 style 子串 → V2 攔；④ SoT 漂移（`update_reply_prompts --full`）→ T2 防護；⑤ T0 過度 scrub 令來源行變殘 → V6 抽樣對照 |
| 最壞情況 | Tetra／來源行文字質素下降；唔影響資料、state、其他物品；最壞回滾一個 commit |
| 還原 | 純 lang 字串（＋T0 若涉 scrub 就係細 scope 改動）→ `git revert <commit>`；真機回滾＝`gradlew jar` 後部署 `dist/_smoke_backups/packai-0.2.1+mc1.19.2-forge.jar.bak-20260913_133727`（sha `17ebc474`） |
| 前置依賴 | 無新依賴；`gradlew jar`（16s，已驗） |
| 唔准郁 | `AskToolLoop` ALLOWLIST／`canonicalArgsJson`；`AskReplyScrub` 段判定；`[TETRA_USE]` 語義；卡工具；`check_*` 斷言（唔准為變綠而改測試） |

## 7. 執行順序 ＋ 每 task 落地即 self-review

1. **T0** 洩漏修 → self-review：`check_ask_display_leak` rc=0＋全量 ≤3 FAIL；抽 3 條來源行對照（唔可以變成殘句）。
2. **T1** harness（含正負對照 fixture）→ self-review：3 條已知錯位必 FAIL、構造乾淨必 PASS、no-heading 必 FAIL/INCONCLUSIVE；`--min-samples` 生效。
3. **T2** lang 18 處＋SoT 防護 → self-review：`json.load`×6、`check_reply_lang`、`check_reply_prompt_keys`（~100 條子串）、`check_dual_tree_diff_symmetry`；逐行 diff。
4. **T3** build jar → 備份 → 部署（三邊 sha256 一致、mods 只留一個 packai jar）。
5. **T4** 真機樣本（SK 配合；累積到 n≥29）→ 判 V5；未達標 → Phase 2。
6. 全程：packai code **一律經 cursor-agent**；唔 commit／push 直到 SK 講；每 task 完成即 self-review，有 bug 即修。

## 8. Review record

| 輪 | 角色 | 比分 | 主要翻盤點 | 計劃嘅實質修改 |
|---|---|---|---|---|
| R1 | 反方 | 4:6（計劃輸） | 漏 `llm_style` 反向拉力；V1 撞 `check_reply_prompt_keys:378`；rule 23 撞 rule 12／24 | → v2：3 key、V1 重寫、LD6 scope、機械化量測 |
| R1 | 正方 | 7:3（計劃贏） | 五條 LD 站得住；扣分在量度設計 | 同上 |
| R2 | 反方 | **4:6（計劃輸）** | v2 T1b 撞 mirror exact assert＋Java↔mirror 無 cross-check（假綠）；T2a 三處硬傷（cp950 strict 失敗／字面 `\n`／簡體 heading）＋段界假陽性；統計 15/≤1 假過 54.9%；§0 又錯（實為 4 FAIL，含新 `role=` 真洩漏）；LD6 未 scope rule 12；SoT 漂移 | → **v3**（本份）：取消 T1b、harness 修正、門檻 0/29、§0 更正、T0 新增、LD6 補 rule 12、SoT 必做、實驗次序 LD10 |
| R2 | 正方 | 8:2（計劃贏）**⚠️ 報告被 iteration cap 截斷** | 三條關鍵修正有真機／靜態證據；T2a 原型即跑出 3/15 錯位；扣分在結構成因（`AskEngine:516-518`）同量測規格 | 同上（其 `AskEngine` 發現已納入 v3 §1 根因鏈） |
| R3 | 待跑 | — | — | — |
