# 反方 review R3 — 語音 skill 3 合 1 plan **v3**（opposing，有界輪）

> 2026-09-19；reviewer＝反方 subagent（**只讀**；唯一寫入＝本檔）。
> 對象：`.hermes/plans/2026-09-19-skill-voice-merge-plan.md`（**v3**）。
> 軌跡：R1 正方 4 : 反方 6 → R2 正方 6 : 反方 4（go=false）→ 本輪。
> 本輪範圍：只核 R2 三條 flip conditions ＋ 專審「v3 新寫嘅字／新數字」（唔加新要求）。
> 方法：全部數字我自己跑（Hermes venv python 直接叫 `tools.skills_tool._find_all_skills()`／`hermes curator status|list-archived` 唯讀）。無改 plan／skill／archive。

## ① 驗過嘅事實（真／假／未核實）

| # | v3 主張 | 判定 | 我自己跑嘅證據 |
|---|---|---|---|
| F1 | 新 description 58 字、首 57 自足、HUD 保留 | **真** | `len("Debug JARVIS + Hermes voice/HUD on Windows (wake/STT/TTS).")=58`；首 57＝`Debug JARVIS + Hermes voice/HUD on Windows (wake/STT/TTS)`；`extract_skill_description()` 原字返回（58 ≤ `SKILL_PROMPT_DESC_LIMIT=60`，`agent/skill_utils.py:1175/1188`）、`is_skill_description_truncated_for_prompt=False` ⇒ index 全見，R2 B2 三點全解 |
| F2 | pipeline `SKILL.md` 裸路徑只在 `:36/:112/:187/:193`、`:85` 冇 | **真** | `grep -n 'scripts/' windows-voice-pipeline/SKILL.md` 恰 4 行（36/112/187/193）；`:85` 只提檔名（`CommandLine -match 'jarvis'` 句），無裸路徑 |
| F3 | `:143` 指 umbrella（唔改）、`:147` 指自身副本（改名） | **真** | `:143`＝「見 **jarvis-voice-assistant skill \`references/aec-implementation.md\`**」；`:147`＝裸 `` `references/aec-implementation.md` `` |
| F4 | 另外 2 行＝`speaker-verification-ecapa.md:32`、`unprompted-speech-triage.md:16`，合共 **7 行** | **真** | `grep -rn 'scripts/'` 喺 pipeline 全樹（SKILL.md＋9 refs）＝**6** 行，ecapa:32／triage:16 佔 2 ⇒ 7；**無第 8 行**；兩個副本內其他 `references/*.md` 指向嘅檔名（`unprompted-speech-triage`／`wake-mic-latency-debugging`／`mage-vl-spike`／`speaker-verification-ecapa`）合併後同名保留，只有 aec 一個要改名 |
| F5 | 7 行改寫嘅目標檔真存在 | **真** | `jarvis-pc/scripts/` 實有 `enroll_voice.py`、`hermes_alert_poll_loop.py`、`jarvis_self_monitor.py`、`mage_vision.py`、`record_jarvis_wake.py` ⇒ `ecapa:32` 嗰句「寫 enrollment script（`scripts/enroll_voice.py`）」改成 `jarvis-pc/scripts/…` **唔改語意**（該檔真在該處），反而去除歧義 |
| F6 | 檔案數：pipeline 9 refs＋hvow 1 ref＋2 scripts＋2 SKILL.md 副本＝**14**；hvow 共 4 檔 | **真** | `find` 實數：jv-assistant 21 檔、pipeline 10 檔、hvow **4** 檔 |
| F7 | A5＝**31**（19＋9＋1＋2 副本） | **真** | refs `*.md`：umbrella 19、pipeline 9、hvow 1；`references_dir.glob("*.md")` 無上限（`tools/skills_tool.py:1645`）；`windows-voice-pipeline.md`／`hermes-voice-windows.md` 兩個副本名唔撞現有 refs ⇒ 31 |
| F8 | A7 真值：managed/active 124→122、archived 0→0、list-archived 1→3 | **真（現值已核）** | `hermes curator status`＝`curator-managed 124 / active 124 / archived 0`；`list-archived`＝`git-branch-integration`（1 個）；機制：`.archive/` 在 `EXCLUDED_SKILL_DIRS`（`skill_utils.py:33`）＋`.usage.json` 133 條（132 active／1 archived，archived 者唔入 124）⇒ 兩次 archive 後 122／0／3 |
| F9 | A1 基準 120／31／13 | **真** | 我親跑 `_find_all_skills()`：TOTAL=**120**、software-development=**31**、autonomous-ai-agents=**13**；兩個被併 skill 各佔一格 ⇒ 120→118／31→30／13→12 |
| F10 | §2 字數 221,887（CRLF 保留）、§3.4 插入點（HOLD `:10` → `## Projects` `:23`） | **真** | 逐檔 raw bytes decode：150,405＋57,440＋14,042＝221,887；`grep -n '^## '` 見 HOLD 在 `:10`、下一節 `## Projects` 在 `:23` |
| F11 | A2「**14** 個檔案…**12** 個逐字一致；改名檔＋3 個改動檔另列 diff」 | **假（自相矛盾）** | 12＋1＋3＝**16 ≠ 14**。真值：**11 個逐字一致**（9 個 pipeline refs 之中 6 個＋改名者 `voice-pipeline-aec-implementation.md`（內容同 bytes）＋`voice-setup-notes.md`＋2 個 hvow scripts＋`hermes-voice-windows.md` 副本）＋**3 個改行檔**（`windows-voice-pipeline.md` 5 行、`speaker-verification-ecapa.md`、`unprompted-speech-triage.md`）＝14。R2 嗰個「12」係舊 12 檔模型嘅殘留（v3 把檔數由 12 升 14，冇 re-derive 個拆分） |
| F12 | A3「總量＝221,887＋Δ（Δ 逐項列明）」可執行 | **假（定義式）** | 7 行改動嘅 Δ 其實**可預先算**（+14 改名＋4×10＋10＋10 ＝ **+74 bytes**），frontmatter 可由源檔 copy 出；但**新指標節（約 10 行）全文未寫入 plan** ⇒ Δ 嘅最大一項未知 ⇒ 任何結果都「對」＝零鑑別力 |
| F13 | A6 五處白名單＝完整處置 | **假（漏 2 行）** | 合併後 `grep -rn`（排除 `.usage.json`／`.curator_backups/`／`.archive/`／`.curator_ledger.jsonl`／`archive/`）仍 **9 行**命中：白名單嘅 7 行（electron-windows-overlay:11、umbrella:34/110/118、windows-desktop-automation:139、jarvis-hud-design.md:11、hermes-skill-library-governance:107）＋**2 行副本 frontmatter `name:`**（`hermes-voice-windows/SKILL.md:2`→`references/hermes-voice-windows.md:2`；`windows-voice-pipeline/SKILL.md:2`→`references/windows-voice-pipeline.md:2`）。逐字 copy 令 `name:` 留喺 umbrella 樹內，A6 冇 predicate 排除佢 |
| F14 | 背景 curator 會唔會重建 | **未核實** | 同 R2 ④；要真跑「語音 session ＋ `hermes curator run`」才知 |

## ② 逐條評 v3

- **R2 FC1（A5=31／A7 真值）：RESOLVED。** 兩條都親驗為正確（F7／F8），且 A7 嘅機制（archived 者跌出 count）有 `.archive/` 排除證據支持 —— 唔再係幽靈閘。
- **R2 FC2（description）：RESOLVED（比我原本建議更好）。** 58 字、index 全見、HUD 保留、刪咗「≤57 字」字眼（F1）。
- **R2 FC3（枚舉寫死）：PARTIAL。** 做到：A2 檔數 12→14 ✓、§3.3 「7 行」正確且**完整**（F2/F4）、刪 `:85` ✓、A6 補第 5 處 ✓、A3 加 predicate ✓、新指標節插入點寫死 ✓、§4「唔准 pin」✓。未閉合：**A2 拆分算術自相矛盾（F11）**、**A3 仍係定義式（F12）**、**A6 漏 2 行（F13）**、**§3.7「已吸收」行位置冇寫死**（若落入 HOLD 段範圍，A4 抽段 diff 就唔係空）。
- **新缺陷嘅來源＝v3 自己新寫嘅數字行**（F11/F12）：呢個係「上一輪修法自己帶新洞」嘅典型 —— v3 修 FC3 時改咗檔數同加咗 predicate，但兩個都冇 re-derive 落去。**A2 係全 plan 唯一「內容零損失」閘**，寫成 16≠14 即係收貨時必然自報未通過（要麼假綠、要麼卡死交付）。
- **A2 表述本身夠唔夠清楚？** §5 A2 寫「另列 `diff`」對「同一份 sha1 表定分開兩份」其實**夠清楚**（豁免已修 3 檔）——問題純粹係**個數錯**，唔係結構錯。改一個數字 + 改 §3.4 措辭（「唯一 7 行」→「3 個檔案共 7 行」）就閉合。
- 其餘（F5 路徑真存在、F6/F7/F9/F10 數字）**全部真** ⇒ v3 冇任何「捏造／未核」級問題。

## ③ 「連 7 行都免」嘅更簡單方法 —— 有，但我唔建議，理由如下

| | 路線 A（v3 現狀：改 7 行） | 路線 B（**0 行改動**：新指標節加一句「本文內 `scripts/*` 一律指 jarvis-pc repo，非本 skill 嘅 `scripts/`」） |
|---|---|---|
| 動到幾多檔 | 3 個 copy 檔（5＋1＋1 行） | 1 個（umbrella `SKILL.md`，本來就要加節） |
| 零損失閘 | 要拆成 11 真一致＋3 改動（易寫錯，本輪就係寫錯） | **14/14 sha1 逐字一致** —— 最乾淨、可機械驗、A2/A3 兩個問題一次消失 |
| 單獨閱讀副本時 | 每行**自我描述**（`jarvis-pc/scripts/…`），脫離 umbrella 都唔會誤讀 | 靠讀過 umbrella 頭先知；`skill_view(file_path='references/windows-voice-pipeline.md')` **只回該檔**，唔會帶 umbrella 註解 ⇒ 單獨讀副本時歧義仍在 |

**反方裁決**：路線 B 表面最省，但弱點係真實嘅（副本可被單獨讀取）；而且 7 行改動我已逐條核實**全部正確、無第 8 行、語意唔變**（F2–F5）。所以**保留路線 A**，只補 3 個記帳缺陷——唔值得為省 7 行而換走自我描述性。若 SK 想要絕對最小 diff，B 可以行，但要明文接受上面嗰個代價。

## ④ 比分 ＋ flip conditions ＋ go/no-go

**正方 7 : 反方 3**（R3）。理由：R2 三條 flip conditions —— FC1／FC2 **全解**（兩者都親驗為真，且 description 修法比 R2 建議更乾淨）；FC3 **大部分解**（7 行清單完整正確、插入點／唔准 pin 都寫死），但 v3 自己新寫嘅兩個數字行帶出 **1 條自相矛盾（A2，14 vs 12＋1＋3＝16）**＋**1 條仍係定義式（A3 Δ 不可預先算）**＋**1 條漏 2 行（A6）**。方向／機制仍然全部企得住，餘項全部係「一個數字／一句 predicate／一句位置」級 —— 唔屬路線問題，但 A2 係唯一零損失閘，寫成對唔上就唔可以當達標。

**仍要修（3 項，全部一行級）**：
1. **A2 拆分寫死**：`14 = 11 逐字一致（含改名檔 voice-pipeline-aec-implementation.md，內容 bytes 相同）＋ 3 改行檔（windows-voice-pipeline.md 5 行、speaker-verification-ecapa.md、unprompted-speech-triage.md）`＋§3.4 措辭改「3 個檔案共 7 行」。（或改用路線 B ⇒ 變 14/14 全等。）
2. **A3 由定義式改成可斷言**：把**新指標節＋frontmatter 嘅逐字文字**寫入 plan（7 行改動嘅 Δ 已可算＝**+74 bytes**），並寫死最終總數；否則刪 A3、只留 A2。
3. **A6 閉合**：加 predicate 排除（或白名單補）2 行副本 frontmatter `name:`（合併後 9 行命中要「逐條有處置」）；順手寫死 §3.7「已吸收」行位置（放新指標節內），保住 A4 抽段 diff＝空。

**Flip conditions（做齊 → 我下一輪給 ≥8:2）**：上面 3 項全做，且 R2 嘅 FC1／FC2／FC3 其餘項維持 RESOLVED、冇新自相矛盾。**若你覺得任何前提係錯／發現新 blocker，照講。**

**go = false**（R3 未達 8:2）。仍在 SK 3–4 輪預算內；三項都係一行級，唔涉設計改動 ⇒ 下一輪可達標。

## ⑤ 最貴未知

**背景 review／curator 會唔會喺合併後再造一個 voice skill？**（同 R2 ④，未解）v3 只做到事後觀察（§7），無事前 gate；我今輪唯一新增證據係「archived skill 確實跌出 managed count 同 index」（F8：`.archive/` 排除 + `.usage.json` archived 1 條唔入 124），但「curator 見到 umbrella 已吸收會唔會照 create」仍未核實。解開要：合併後跑一次「語音 session ＋ `hermes curator run`」，睇 ledger／`curator usage` 有冇多一個語音 skill。次要未知：新 description 喺真實揀選情境嘅 would-block 效果（兩個評審都只有 index 文字，冇揀選數據）。
