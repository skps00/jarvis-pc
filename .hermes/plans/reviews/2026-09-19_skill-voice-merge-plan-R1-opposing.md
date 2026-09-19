# 反方 review — 語音 skill 3 合 1 plan（R1 opposing）

> 2026-09-19；reviewer＝反方 subagent（只讀，唯一寫入＝本檔）。
> 對象：`.hermes/plans/2026-09-19-skill-voice-merge-plan.md`（下稱 plan，引 `plan:Ln`）。
> 方法：全部數字／sha1／計數親跑；Hermes 側結論引 source 或 CLI 實測輸出。

## ① 驗過嘅事實（真／假／未核實）

| # | plan 主張 | 判定 | 證據 |
|---|---|---|---|
| F1 | §2 檔數／字數：21/150,405、10/57,440、4/14,042、合計 35/221,887 | **真** | os.walk + `len(str)`：21=150,405、10=57,440、4=14,042、TOTAL files 35 chars **221,887**；`SKILL.md` 62,362／28,566／7,206 逐個中 |
| F2 | 兩份 `aec-implementation.md` 內容唔同、sha1 兩邊（`6e4a08fb6911` / `6b23881ed940`） | **真** | 同 sha1；`diff -u` 顯示 79 行 vs 90 行、標題＋安裝段＋API 段全部唔同 → 兩份都要保正確 |
| F3 | 「撞名只有 aec-implementation.md」 | **真** | umbrella 19 refs ∩ pipeline 9 refs = {`aec-implementation.md`}；∩ hvow = ∅；scripts 三檔零撞名 |
| F4 | pipeline 內 `scripts/hermes_alert_poll_loop.py` 等係 jarvis-pc repo 路徑 | **真** | 4 檔全部存在於 `jarvis-pc/scripts/`（hermes_alert_poll_loop.py、jarvis_self_monitor.py、mage_vision.py、record_jarvis_wake.py） |
| F5 | archive 放 `skills/` 外＝唔會被索引 | **真（但見 O8）** | config `skills:` 只有 `creation_nudge_interval`（無 external dirs）；`hermes/archive/skills/2026-09-19/git-branch-integration` 已存在；`skills_list(category='software-development')` 返 31（無 git-branch-integration） |
| F6 | A1「skills_list 總數 31 → 29」 | **假** | 實測 `skills_list()` count=**120**；`software-development`=**31**、`autonomous-ai-agents`=**13**。合併後應為 120→118／31→30／13→12 |
| F7 | A3「字數守恆 ±0」 | **假（算式＋不可滿足）** | 算式 LHS 62,362+28,566+7,206+(9 refs 28,874)+3,597 = **130,605**，同 221,887 差 **91,282**（=被漏數嘅 umbrella 19 refs 85,914 + 3 scripts 5,368）；且 plan 自己 §3.4 加 section＋frontmatter＋L32 連結改名（+15 字）⇒ 淨值必 >221,887 |
| F8 | A6「grep 舊名（只排除 ledger）= 0」 | **假（不可達）** | 見 O3：至少 6 個位置命中，plan 只改 L32 一行、§4 又禁改寫 |
| F9 | 新 description 覆蓋原三觸發 | **假** | `skill_utils.py:1175 SKILL_PROMPT_DESC_LIMIT = 60`、`:1189-1190 return desc[:57]+"..."`；實跑：proposed 86 字 → index 只顯示 `'JARVIS voice/wake/HUD + Hermes voice (STT/wake/TTS) on Wi...'`；被併 `hermes-voice-windows` 53 字 `'Enable/verify Hermes voice (STT/wake/TTS) on Windows.'` **完全可見** |
| F10 | 三個 skill 都係 curator 可管 | **真** | `hermes curator list-unmanaged`（7 個）不含三者；`hermes curator status`：curator-managed 124、archived 0、`consolidate: off` |
| F11 | `references` 無 listing 上限（29 檔列得完） | **真** | `skills_tool.py:1644` `references_dir.glob("*.md")` 全收、無 slice；但 script ext 白名單無 `*.ps1`（`jarvis_diag.ps1` 永不出現喺 linked_files） |
| F12 | umbrella SKILL.md 62,362 加一節仍遠低上限 | **真** | `skill_manager_tool.py:547 MAX_SKILL_CONTENT_CHARS = 100_000` → 餘量 ~37.6k |

## ② 問題（severity ＋ 證據）

- **O1 [HIGH] 3/6 驗收條目執行唔到（A1、A3、A6）。** A1 數字假（F6）；A3 算式錯＋±0 不可能（F7）；A6 要求 0 但 plan 自己禁止改寫（O3）。按 plan §8，做完拿唔到「逐項通過」→ 交付即時違反「驗收標準」。
- **O2 [HIGH] A6 與紅線自相矛盾。** 要求 `grep windows-voice-pipeline|hermes-voice-windows`＝0（只排除 ledger），實測命中至少：`electron-windows-overlay/SKILL.md:11 related_skills: [jarvis-companion, windows-desktop-automation, windows-voice-pipeline]`；umbrella 自己 `jarvis-voice-assistant/SKILL.md:34/110/118`（「完整 recipe 見 windows-voice-pipeline skill」等 3 處）；`windows-desktop-automation/SKILL.md:139`（`hermes-voice-windows-setup`，既有）；moved 檔 `references/jarvis-hud-design.md:11`；`skills/.usage.json:842/1937`；`.curator_backups/blobs/*` 大量。plan L32 只改 1 行、§4「唔改寫任何內容」→ A6=0 除非改 criteria 或者改文（自打嘴巴）。另 A6 冇定範圍（jarvis-pc repo 嘅 plan 檔都含舊名）。
- **O3 [HIGH] 描述改動 = routing 訊號倒退（唯一有實證嘅功能損失）。** F9：新 description 首 57 字食完，`enable, verify, debug` 入唔到 index；舊 `hermes-voice-windows` 嗰句「Enable/verify Hermes voice (STT/wake/TTS) on Windows.」本來係最強 trigger（動詞開頭）→ 合併後**消失**。違反治理 skill §「整合方法」3（「~57 chars 限制內揀最重要 trigger」）同 audit §6-10（把弱 description 改強）。
- **O4 [MED-HIGH] 撞手未消除，仲多返一個「新對手」。** `jarvis-companion`（index 可見 55 字）＝`Use when SK's Jarvis app can't reach Hermes or voice fails.`，同新 umbrella 首 57 字（`JARVIS voice/wake/HUD …`）重疊「JARVIS voice」；`jarvis-voice-out`＝`Reply to SK on Discord: speak short English via Jarvis TTS.`。plan §1 講「消除同一問題 3 個都被選中」→ 實情由 3-4 個候選變 2 個，未達「消除」；plan 冇任何 would-block／揀選驗證數據支持「撞手已解」。
- **O5 [MED] frontmatter 損失只提一半。** umbrella 現時 frontmatter 只有 `name/description`（親驗 L1-4）；`hermes-voice-windows` 有 `metadata.hermes.tags`(8)＋`related_skills`(3)＋`author: Hermes Agent (curator)`＋`license`＋`platforms: [windows]`＋`version`；`windows-voice-pipeline` 有 `platforms: [windows]`＋`version`。plan §3.4 只明文寫 tags／related_skills → **platforms／version／author 冇明講**。`platforms` 係真過濾欄位（實證：`apple/*` `platforms:[macos]` 唔入 Windows index：snapshot 132 vs live 120）；抄 `author: …(curator)` 更可能改變 curator ownership 判定（**未核實**）。
- **O6 [MED] §6「1 步還原」唔完整。** 合併同時改 umbrella（description＋新 section＋tags）＋新增 12 個 copy（10 refs＋2 個 SKILL.md 副本）。只「搬返兩個目錄」→ umbrella 重複 refs、落後 description、自稱 umbrella。真還原＝3 步（還原 umbrella SKILL.md 用 §6 嘅 `%TEMP%` backup、刪 12 個 copy、搬返 2 目錄）。AGENTS.md 第一規則要「具體、可驗證」還原 → 未達。
- **O7 [MED] 明明有原生 curator archive，plan 用 raw `mv`。** `hermes curator {archive,restore,list-archived,prune,ledger}` 存在（archive 移 `skills/.archive/`、可 restore、寫 ledger）。親驗後果：今日同樣 raw mv 嘅 `git-branch-integration` 在 `.usage.json` 仍 `"state": "active", "archived_at": null`；`hermes curator list-archived`＝`no archived skills`。即 raw mv 令 disk 135 SKILL.md／snapshot 132／usage 133／live index 120 四層唔一致，curator 唔知佢退役 → 之後想 `restore`／`prune` 都唔認得。
- **O8 [MED] curator 重建風險未緩解（見 ④）。** 實證：今日 15:55 curator 由 session 自動 **create** `minecraft-mod-in-game-autotest`（ledger 1372-1374）；`windows-voice-pipeline` 被 curator 自動 patch 過 5 次（ledger 89-91／517／664-665，最新 2026-09-12）。現時 consolidate off 幫到手，但 plan 冇寫任何「已整合」標記／ledger 記錄／`hermes curator adopt` 處置。
- **O9 [LOW-MED] 「只改 1 行」冇指名行號，且有 2 個候選。** pipeline `SKILL.md:143`（`見 **jarvis-voice-assistant skill references/aec-implementation.md**`，指 umbrella 自己嗰份＝**正確**）同 `:147`（指 pipeline 自己嗰份＝要改名）。plan L32 只講「改 1 行」→ 改錯行會令 L143 由啱變錯，且無法機械驗證。另 `2026-09-02_203000-skills-consolidation-plan.md:108` B4 曾定「uniq reference（一個 keep、另一個 link）」→ 本 plan 改為兩份都保（只改名）＝與舊治理取向唔一致（重複仍在）。
- **O10 [LOW-MED] 路徑影子化（scripts/）未驗。** copy 後 `references/windows-voice-pipeline.md` 內嘅裸路徑 `scripts/hermes_alert_poll_loop.py`（:85/112）、`scripts/jarvis_self_monitor.py`（:187）、`scripts/mage_vision.py`（:193）、`scripts/record_jarvis_wake.py`（:36）本來解去 jarvis-pc repo，但 umbrella 自己有 `scripts/`（`jarvis_diag.ps1`＋將收 2 個 `.py`）→ 有機會被解成 skill dir。plan §2 L21「文字仍然有效，唔需要改」冇驗收、冇證據。
- **O11 [LOW] §4 HOLD 免責大部分成立，但「純檔案操作」用詞過寬。** 親驗：合併後 umbrella SKILL.md 62,362 字＋新 section 仍 <100,000；HOLD 段（L10-22）一字不動、位置不變；skill 載入係讀取，唔會觸發 wake／TTS／sidecar → **冇隱藏 runtime 側效**。但 description 改動會改變「未來語音任務揀邊個 skill」＝行為改變（唔止檔案），呢點 plan 用「純檔案操作」帶過，並無列出。

## ③ 比分 ＋ flip conditions

**正方 4 : 反方 6**（R1）。理由：內容零損失嘅機械部分（sha1 逐字 copy、撞名處理、份數核對）**全部親驗為真、做得對**；但 3/6 驗收條目邏輯上執行唔到、描述改動令 routing 訊號倒退（source 實證）、還原方案唔完整、原生 archive 未用、curator 重建風險零緩解。

**Flip conditions（做齊以上，該輪可翻去 8:2）**：
1. A1 改成實測基準：`skills_list() 120 → 118`、`software-development 31 → 30`、`autonomous-ai-agents 13 → 12`（並附 `skills_list(category=…)` 輸出）。
2. A3 改成**可滿足式**：`新 umbrella 樹總字數 = 221,887 + Δ（Δ = 新增 section + frontmatter + 15 字連結改名，逐項列明）`，並列出被排除檔案；或改為「逐檔 sha1 對照表：12 個 copy 檔 sha1 全部等於原檔（改名者除 1 行）」，唔用「±0」。
3. A6 改成：只在 `skills/` 樹內 grep、明確排除 `.usage.json`／`.curator_backups/`／archive／ledger，並把已知 4 處（electron-windows-overlay:11、umbrella:34/110/118、jarvis-hud-design.md:11、windows-desktop-automation:139 既有）列成**白名單式 + 逐條處置**（改字 or 明示保留）；§4 紅線同步放寬至「可改 skill 名稱引用，不改語意」。
4. 新 description ≤60 字且**動詞開頭**，例如 `Enable/verify/debug JARVIS + Hermes voice on Windows (STT/wake/TTS).`（實跑 `extract_skill_description` 確認首 57 字含 enable/verify/debug），並明文抄齊 `platforms: [windows]`／`version`／tags／related_skills；`author:` 明確寫「唔抄 curator 標記（除非查明影響）」。
5. §6 改成 3 步還原（含 umbrella SKILL.md 由 `%TEMP%` backup 還原、刪 12 個 copy、搬返 2 目錄），並在動手前先驗一次「倒帶演練」。
6. 歸檔改用 `hermes curator archive <name>`（或 raw mv ＋ ledger 記錄 ＋ 同步 `.usage.json` state），並在 umbrella 加一行「本 skill 已吸收 windows-voice-pipeline／hermes-voice-windows（2026-09-19）」防 curator 重建。
7. L32 寫明**行號**（pipeline `SKILL.md:147`，唔係 :143）＋把 :143 那句連結一齊檢查。
8. §2 L21 補一條驗收：copy 後所有 `scripts/*.py` 裸路徑要指明係 jarvis-pc repo（例如寫成 `jarvis-pc/scripts/...`）。

## ④ 最貴未知

**背景 curator 會唔會令合併白做／令狀態腐化？** 三個 skill 全部 curator-managed，而 curator 今日已實證會自動 create（`minecraft-mod-in-game-autotest`）＋多次自動 patch `windows-voice-pipeline`。現時 `consolidate: off`（7 日一跑、30 日 stale、90 日 archive）只係**時間窗**緩解，唔係機制保證——「curator 會唔會由未來 session 生成返一個 windows-voice-pipeline／語音 skill」、「raw mv 之後 curator 對『usage 話 active 但 disk 冇』嘅 skill 會點做（重建？報錯？忽略？）」兩個都**未核實**，而 plan 完全冇提。解開需要：合併後（或 replica 上）跑一次 `hermes curator run` ＋ 一個「做語音工作」嘅 session，觀察 0 新 voice skill 同 `hermes curator status` 一致性；並抽查 `.usage.json` state 有冇被自動修正。
