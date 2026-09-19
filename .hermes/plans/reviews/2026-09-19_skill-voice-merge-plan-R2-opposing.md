# 反方 review R2 — 語音 skill 3 合 1 plan **v2**（opposing）

> 2026-09-19；reviewer＝反方 subagent（只讀；唯一寫入＝本檔）。
> 對象：`.hermes/plans/2026-09-19-skill-voice-merge-plan.md`（**v2**，引 `plan:Ln`）。R1＝正方 4 : 反方 6。
> 方法：全部數字我自己跑（Hermes venv python + `hermes curator` 唯讀子命令）；無改任何 plan／skill／archive。

## ① 驗過嘅事實（真／假／未核實）

| # | v2 主張 | 判定 | 我自己跑嘅證據 |
|---|---|---|---|
| F1 | A1 基準 120／31／13 | **真** | `_find_all_skills()`（tools/skills_tool.py）→ TOTAL=**120**、software-development=**31**、autonomous-ai-agents=**13** |
| F2 | `.archive` 唔會入 index | **真** | `agent/skill_utils.py:33 EXCLUDED_SKILL_DIRS` 含 `.archive`；實測 `git-branch-integration` 唔在 index、但在 `skills/.archive/` |
| F3 | §0.1 原生 archive 已修好 | **真** | `hermes curator ledger`＝`552fa7a25278 user archive git-branch-integration`；`.usage.json` 該 skill `archived_at=2026-09-19T09:59:07+00:00`；`list-archived`＝1 個名 |
| F4 | A3 總數 221,887 可重現 | **真** | predicate＝原文 raw bytes decode utf-8、**CRLF 保留**：150,405＋57,440＋14,042＝**221,887**；若用 `read_text()`（CRLF→LF）＝**219,355**（差 2,532＝全樹 2,532 個 `\n`）。分區恆等 ⇒ 「221,887＋Δ」可滿足 |
| F5 | A3「Δ 逐項列明」可預先算 | **假（部分）** | 新 ~10 行指標節未寫 → Δ 事後才知；「total＝221,887＋Δ」係定義式（Δ＝殘差），只有靠 A2 sha1 表才有鑑別力 |
| F6 | pipeline `:143` 指 umbrella、`:147` 要改名 | **真** | `sed -n`：`:143`＝`見 **jarvis-voice-assistant skill references/aec-implementation.md**`（正確保留）；`:147`＝裸 `` `references/aec-implementation.md` `` |
| F7 | 「4 個裸路徑（`:36/:85/:112/:187/:193`）」 | **假** | 裸 `scripts/*.py` 只有 **4 行**：`:36 record_jarvis_wake.py`／`:112 hermes_alert_poll_loop.py`／`:187 jarvis_self_monitor.py`／`:193 mage_vision.py`。`:85` 冇裸路徑（係 `CommandLine -match 'jarvis'` 句，只提檔名） |
| F8 | 「唯一 5 行」＝完整 | **假** | 同型裸路徑仲有 2 行在**被 copy 嘅 reference doc**：`references/speaker-verification-ecapa.md:32`（`scripts/enroll_voice.py`，jarvis-pc 真有此檔）、`references/unprompted-speech-triage.md:16`（`scripts/hermes_alert_poll_loop.py`）⇒ 按 plan 自己嘅影子化標準應係 **7 行** |
| F9 | 新 description 動詞開頭、**≤57 字** | **假（數字）／真（動詞）** | 實測 **68 字**；`extract_skill_description` → index 只出 `Enable/verify/debug JARVIS + Hermes voice on Windows (STT...`（全見上限＝60 字，`skill_utils.py:1175`）；首 57 字含 enable/verify/debug ✓ |
| F10 | A5「列出新 references（29 個）」 | **假** | listing＝`references_dir.glob("*.md")`（`tools/skills_tool.py:1644-1646`，無上限）；合併後＝19＋9＋1＋**2 個 SKILL.md 副本**＝**31** |
| F11 | A7「curator status archived ＋2、active −2」 | **假（觀察唔到）** | 今日已有 1 個原生 archived skill，`curator status` 仍 `archived 0`、`list-archived 1`；機制＝`curated_report()` 由 `base.rglob("SKILL.md")`＋`is_excluded_skill_path`（含 `.archive`）算 ⇒ 真值應係 managed/active **124→122**、**archived 0→0**、`list-archived 1→3` |
| F12 | A6 已知 4 處白名單＝齊 | **假（漏一處）** | skills/ 內（排除 `.usage.json`／`.curator_backups`／`.archive`／ledger）共 9 行命中；合併後剩 7 行；A6 只列 6 行（4 條目）→ 漏 `hermes/hermes-skill-library-governance/SKILL.md:107`（講 `hermes-voice-windows` 嘅歷史敍述） |
| F13 | §3.6 防重建法（marker＋ledger） | **半真 + 方向對** | `hermes curator archive` 自動寫 ledger ✓、`.usage.json` state 同步 ✓。但 `pin` **唔可以**用：`background_review.py` prompt 明文「Bundled, hub, **pinned**, and user-owned skills are off-limits」⇒ pin 咗 umbrella 反而令未來 session 唔可以 patch 佢，被推向「CREATE A NEW CLASS-LEVEL UMBRELLA」＝正好係要防嘅重建風險。`adopt` 只處理 unmanaged（三者已 curator-managed：`curator usage` 顯示 source=agent）⇒ v2 嘅選擇（marker 行＋事後驗證）係正確路線 |
| F14 | HOLD 段 L10–22 不變 | **真（內容）** | `## ⛔ 語音／mic 線 HOLD` 喺 `:10`，下一節 `## Projects` 喺 `:23`；v2 只改 frontmatter＋加節 ⇒ 內容可 diff＝空 |
| F15 | A2「12 個 copy 檔 sha1＝原檔」 | **假（少 2）** | 實際搬 **14 檔**（10 refs ＋ 2 SKILL.md ＋ 2 個 hvow scripts：`verify_voice_stack.py`／`voice_test_tts.py`）；sha1 表漏 2 個 script |
| F16 | 背景重建風險嘅最終答案 | **未核實** | 要真跑「做語音工作嘅 session ＋ `hermes curator run`」才知（見 ④） |

## ② 問題（severity ＋ 證據）

- **B1 [HIGH] A5、A7 兩條驗收「照字面永遠對唔上」＝幽靈閘（同 R1 O1 同一族）。** A5 觀察值會係 **31**（F10，code＋算術都定死），A7 嘅 `archived ＋2` 按 F11 永遠唔會出現。照 v2 執行 → 收貨時自報「驗收未通過」，而 plan §8 要出「§5 全部輸出」。
- **B2 [HIGH] description 68 字（自稱 ≤57）＋routing 倒退。** ① `(STT/wake/TTS)` 被截（hvow 原本 53 字係全見）＝R1 O3 嗰種「唯一有實證嘅功能損失」只係被搬去尾截；② 原 umbrella 描述嘅 **`HUD` 完全消失**，而 umbrella 同時係 HUD 覆蓋 skill（HUD 係 route 訊號）；③ Hermes 自己會即場警告：`_add_description_prompt_preview` 會回 `System prompt will show: "…(STT..."`（`skill_manager_tool.py:930-940`；>60 只擋 create、唔擋 patch，所以會照寫入但帶警告）。
- **B3 [MED] 枚舉衛生四項（全部係「寫死」級，非設計級）。** A3 冇寫計數 predicate（221,887 vs 219,355，差 2,532，實作者重測會誤判失敗）；A2 12 vs 真值 14；A6 4 處 vs 真值 5 處／7 行；§3.3 行號清單含冇關嘅 `:85` 且 5 行 vs 真值 7 行（F7／F8／F12／F15）。
- **B4 [LOW] 新指標節＋「已吸收」行嘅插入位置未寫死。** 若插喺 L10 之前，HOLD 段行號漂移；A4 必須寫「抽 HOLD 段做 diff（唔靠絕對行號）」。
- **B5 [LOW] §3.6／§7 冇任何機械 gate，且冇明文「唔准 pin」。** 依 F13，錯用 `pin` 會令風險變差；建議一句寫死。

## ③ 比分 ＋ flip conditions ＋ go/no-go

**正方 6 : 反方 4**（R2）。理由：R1 嘅 8 條 flip conditions —— **4 條全解**（FC1 基準數字親跑吻合；FC5 三步還原＋倒帶演練；FC6 原生 archive 實測可用＋ledger 自動記錄；FC7 `:147` vs `:143` 完全正確）、**3 條半解**（FC2 公式可滿足但 predicate／檔數未寫死；FC3 範圍與排除清單對，但白名單漏 1 處；FC8 改動方向對，行號清單錯＋漏 2 行）、**1 條數字假**（FC4 description 68≠≤57）。方向／機制全部企得住，餘項全部係「驗收數字／predicate 未寫死」＋1 條 routing 內容損失 → 未達 8:2，但唔屬路線問題（R1 嗰 6 分之中嘅結構性風險已實質消除）。

**Flip conditions（R2；做齊 → 我下一輪給 8:2）**：
1. **A5 改 31**（19 舊 refs ＋ 10 新 ref doc ＋ 2 個 SKILL.md 副本；或明文改設計唔放 references/）；**A7 改成**「`curator status`：managed 124→122、active 124→122、archived 0 不變；`list-archived` 1→3（附輸出）」。
2. **description 改成 ≤60 字（首 57 自足）並保留 HUD**；實測合格例子：`Debug JARVIS + Hermes voice/HUD on Windows (wake/STT/TTS).`（**58 字**，index 全見）；同時刪「≤57 字」字眼、改寫「首 57 字自足、總長 ≤60」。
3. **枚舉寫死**：A3 加 predicate（`sum(len(p.read_bytes().decode("utf-8")) for p in <tree>)`，**CRLF 保留** → 221,887）；A2 12→**14**（補 2 個 hvow script sha1）；A6 加第 5 處 `hermes/hermes-skill-library-governance/SKILL.md:107`；§3.3 改成「**7 行**＝`:147` ＋ `:36/:112/:187/:193` ＋ `speaker-verification-ecapa.md:32` ＋ `unprompted-speech-triage.md:16`」並刪 `:85`；明文寫新指標節／「已吸收」行嘅插入位置（A4 用抽段 diff）；§4 加一句「**唔准 `hermes curator pin` umbrella**（會令背景 review 唔可以 patch 佢 → 反而助長重建）」。

**go = false**（R2 未達 8:2）。三條都係一行級修訂、唔涉設計改動；修完屬「實質修改」，下一輪可達標。R2 仍在 SK 嘅 3–4 輪預算之內，未觸及停手門檻。

## ④ 最貴未知

**背景 review／curator 會唔會喺下一個語音 session 之後重新造一個 voice skill？** v2 只做到「合併後事後睇有冇」（§7），冇事前 gate；我唯一驗到嘅係「archived skill 會跌出 index／`curator usage`」（F2/F13），而背景 review 嘅 prompt 係「搵唔到匹配 umbrella → CREATE NEW UMBRELLA」。解開要：合併後跑一次「做語音工作嘅 session ＋ `hermes curator run`」，睇 ledger 有冇新 voice skill、`curator usage` 有冇多一個語音 skill（成本約一個 session）。次要未知：新 description 喺真實揀選情境會唔會令 HUD／語音任務揀中 umbrella —— 現時兩個評審都只有「index 顯示咩字」，冇 would-block／揀選數據。
