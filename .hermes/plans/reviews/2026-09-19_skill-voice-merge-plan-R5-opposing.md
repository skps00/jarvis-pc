# 反方 review R5 — 語音 skill 3 合 1 plan **v5**（彩排實測版）

> 2026-09-19；reviewer＝反方 subagent（**只讀**；唯一寫入＝本檔）。對象：`.hermes/plans/2026-09-19-skill-voice-merge-plan.md`（v5）。
> 軌跡：R1 4:6 → R2 6:4 → R3 7:3 → R4 7:3（SK 要求加班一輪）。本輪範圍：**驗 v5 嘅彩排實測值真假＋彩排是否真對應實機**，加新角度。
> 方法：唔信彩排腳本輸出——我自己由**實機原檔**重算全部值（Hermes venv python；`_find_all_skills()` 真 index；raw bytes `newline=''`）；彩排樹只當 claim。無改 plan／skill／archive／ledger。

## ① 驗過嘅事實（真／假／未核實）

| # | v5 主張 | 判定 | 我自己跑嘅證據 |
|---|---|---|---|
| F1 | **彩排無作弊**（量嘅係同一堆真檔） | **真** | 腳本由 `%LOCALAPPDATA%\hermes\skills\` copytree 出三個 skill 再量，無寫死數字；我由實機原檔獨立算出 base＝150,405＋57,440＋14,042＝**221,887**（＝§2 值），檔數 21／10／4＝**35**，合併樹**仍係 35 檔** ⇒ 彩排確實讀實機同一批檔 |
| F2 | A3 **222,982**、Δ＝+274／+746／+75 | **真（逐項獨立重算）** | 舊 fm **105** → 新 fm **379** ⇒ **+274**；指標節 **+746**；7 行 **+75**（`windows-voice-pipeline.md` +55＝+15 改名＋4×+10、`ecapa:32` +10、`triage:16` +10）⇒ Δ＝**+1,095**、221,887＋1,095＝**222,982** ✓（R4 估 109／270／744＝錯；v5 實測值才對） |
| F3 | A2 ＝ **11 逐字一致（含改名檔）＋3 有改動** | **真** | 逐檔 sha1／bytes 比對 14 個搬入檔：**identical 11**（含改名 `voice-pipeline-aec-implementation.md`）、edited 3＝`windows-voice-pipeline.md`／`speaker-verification-ecapa.md`／`unprompted-speech-triage.md`。11＋3＝14 閉合 |
| F4 | 7 行改動「改對、只改指定行」 | **真** | 逐行 diff 原檔：`:147` 改名（+15）、`:36/:112/:187/:193` 各 +10、`ecapa:32` +10、`triage:16` +10；**每個改動行恰 1 個 token 被替換**、無其他差異；`:143`（指 umbrella 自己）**逐字未動** ✓ |
| F5 | A4 **identical、822 字** | **真（兼有鑑別力）** | `## ⛔`→下一個 `\n## ` 抽法：old/new **sha1 相同 `3f4fe8a83507`**、len 822；**負控**：HOLD 段內改 1 字 → 即報 False（唔係恆真閘）；而 R4 講嘅舊抽法（到 `## Projects`）**確係 False** ⇒ v5 換抽法有實質作用 |
| F6 | A5 ＝ **31** refs | **真** | 合併樹 `references/*.md` ＝ 31（19＋9＋1＋2 副本） |
| F7 | A1 基準 **120／31／13** | **真** | 真 index 重跑：TOTAL **120**、software-development **31**（32 個 dir 中 `python-debugpy` 係 macos/linux 被平台閘濾走）、autonomous-ai-agents **13**；三個 skill 都在 index ⇒ 118／30／12 ✓ |
| F8 | A7 **124→122、archived 0→0、list-archived 1→3** | **真（現值）** | `hermes curator status`：managed/active **124**、archived **0**；`.archive\` 現有 1 個（`git-branch-integration`） ⇒ 兩次 archive 後 122／0／3 ✓ |
| F9 | **實機 skills 樹零改動** | **真** | 三個 skill 樹內**無任何檔 mtime > 17:50**（最新＝`hermes-voice-windows/SKILL.md` 17:47:38，早於 18:14 彩排）；21＋10＋4 檔、221,887 字同彩排前一致；`:147` 仍係舊名、umbrella frontmatter 仍係舊 4 行；`%TEMP%\skill_voice_merge_backup_*` 仍**未存在** ⇒ 彩排 100% 在 `%TEMP%` |
| F10 | A6 合併後 **11 行** | **部分假** | 我 in-memory 拼出執行後樹：predicate 後 **13 行**（見 O1）。umbrella 部分 v5 對得極準：自引 **:31/:32/:34/:35**（4 行）＋原有敍述 **:52/:128/:136**（唔係 R4 估嘅 51/127/135）✓ |
| F11 | §6「還原 3 步；已喺 `%TEMP%` 彩排過」 | **未核實（無 artifact）** | 彩排腳本冇一步做 restore，亦冇 backup dir；機制（`curator restore`＋`.archive` 保留全樹）R4 F7 已核 ⇒ 措辭應改「機制已核；未實跑」 |
| F12 | 第 8 行改動（`electron-windows-overlay:11`）安全性 | **真** | 該 skill 係 **curator-managed**（`created_by:agent`，唔在 7 個 unmanaged 名單）⇒ 唔會撞 write-refusal；其樹內提到舊名**只有 :11 一行**（grep 實證）⇒ 移除後 body 零訊息損失；改動後剩 `related_skills: [jarvis-companion, windows-desktop-automation]` |

## ② 新角度／剩餘問題

- **O1 [MED] A6 個數同「執行後現實」唔一致（三重矛盾）。** ①A6 寫「合併後 11 行」，但 11 之中包含 plan **自己第 8 行會移除**嘅 `electron-windows-overlay:11` ⇒ 執行後（當時）應係 **10**。②**18:15:48** 起 skills 樹多咗 2 行命中：`hermes/hermes-skill-library-governance/references/skill-merge-plan-acceptance.md:14/:15`（`├─ windows-voice-pipeline\`／`└─ hermes-voice-windows\`，**彩排後 1 分鐘才由 curator 寫入**）⇒ 今日執行後實數＝**12**。③作者自己嗰份 governance 文件明寫「合併後真值 **10 行**」——同一件事三處數字（11／10／12）。呢個係「寫死記帳數」同一 class，但今次根因係**樹係移動靶**：唔同行動者會令命中數漂移。1 行可修：A6 改成「**執行時實測**（彩排後已知 +2 行，逐行列出）」＋逐行處置（新 2 行＝歷史敍述、保留）。
- **O2 [LOW-MED] §6「已彩排過」係未核實斷言**（F11）。建議順手做 1 分鐘倒帶演練（彩排樹仍在，刪 14 檔＋還原 SKILL.md）才寫「已彩排」。
- **O3 [LOW] 第 8 行唔算越界（幫手），但做法可以更好。** 佢係唯一 tree 外改動，目的係免懸空 cross-ref ⇒ 屬必要；**更好＝改成 `jarvis-voice-assistant`（保留語意連結）**，唔係淨刪（淨刪令 overlay skill 由 3 個 related 變 2 個、失去「語音線」連繫）。另 §3「只准 4 個檔案共 8 行」已含此檔，措辭一致 ✓。
- **O4 [LOW] 執行後重跑舊 review 腳本會踩鬼閘／死路。** `voice_merge_rehearsal.py` 開頭 `copytree` 兩個來源 dir（歸檔後唔存在）⇒ FileNotFoundError（code 讀出，Python 語義）；`rehearsal_a4_a6.py` 嘅 A4 係「實機舊檔 vs 彩排檔」，執行後變成**自己同自己比 ⇒ 恆真**（真鬼閘）；`voice_merge_check.py`／`voice_merge_verify.py` 用 `os.walk` 冇 `exist_ok` ⇒ 靜默返 0 檔 0 字。⇒ A4 收貨時要對 **backup 檔**比，唔好對 live 比。
- **O5 [LOW] §4 未記 `platforms:[windows]` 行為改變**（umbrella 由無平台限制變只在 Windows load）。與 R4 F8 同一項，仍未入 §4；本機 win32 唔影響 A1／A7，但屬「已知行為改變」應列。

## ③ 比分 ＋ go/no-go

**正方 8 : 反方 2**（R5）。理據：R4 兩條 flip conditions —— (1) **A3 可 derive ⇒ CLOSED，而且係逐項獨立重算命中**（222,982＝221,887＋274／746／75；連 R4 自己估錯嘅 109／270／744 都被 v5 的真值糾正）；(2) **A6 用合併後值重列 ⇒ 大部分閉合**（4 行自引、:52/:128/:136 位移、`electron-windows-overlay:11` 已正名為活 cross-ref）。另外 R4 只憑腳本輸出相信嘅 A2／A4／A5／A1／A7，我**全部由實機原檔獨立重算命中**，彩排腳本無作弊、無寫死數字、測嘅確係實機同一批檔，而實機三個 skill 樹**一字未動**（mtime／檔數／字數／sha1 抽樣四重證據）。設計層（零損失、可還原、HOLD 不動）與 R4 一致：**零異議**。餘下唯一反方點＝**A6 個數（11）同執行後現實（12）差 2＋包含一個將被移除嘅行**，屬 1 行措辭／實測式修訂，唔涉設計、唔涉資料安全。

**go = true**（附 O1／O3 兩個 1 行級「執行前必改」）。理由：merge 本身可還原（3 步、`curator restore` 機制已核）、內容 byte 級零損失已證、實機安全已證；A6 個數即使照舊寫，執行時只會令**收貨報告數字對唔上**（要即場手動重算），唔會造成損失或不可逆後果 ⇒ 唔構成 no-go。**但**若 SK 要求「驗收表字面必須一次過」，就係下面 FC1 一行；SK 可直接叫作者改完即做。

**Flip conditions／執行前必改（具體到行）**：
1. **plan L79（A6 行）**：改成「**執行時實測命中數（彩排後已知 +2：`hermes-skill-library-governance/references/skill-merge-plan-acceptance.md:14/:15`）；umbrella 8 行（自引 :31/:32/:34/:35＋原有 :52/:128/:136＋`references/jarvis-hud-design.md:11`）＋`governance:107`＋`governance ref :14/:15`＋`windows-desktop-automation:139`＝12 行**」，並把 `electron-windows-overlay:11` 由「11 行之一」改成「**由 §3.4 第 8 行移除**」（唔計入後值）。
2. **plan L36**：第 8 行由「移除 `windows-voice-pipeline`」改成「**改為 `jarvis-voice-assistant`**」（保留語意連結，免 3→2 個 related）。
3. **plan L82（§6 標題）**：刪「已喺 `%TEMP%` 彩排過」，或先真做一次倒帶演練再寫。
4. **plan L68（§4）**：補一句「umbrella 由全平台變 `platforms:[windows]`」。
5. 收貨時 **A4 對 backup 檔比（唔好對 live 比）**，否則係恆真閘。

## ④ 最貴未知（未變）

背景 curator 會唔會再造一個語音 skill（三輪未解）——**今日新證據反而加強疑問**：curator 今晚 18:15 就自動寫入咗 `skill-merge-plan-acceptance.md`（8 次提到 hvow／pipeline），即係佢正活躍地就「呢單 merge」寫文件；合併後要跑一次語音 session ＋ `hermes curator run` 睇 ledger 有冇新 voice skill。次要：新 description 對真實 routing 嘅效果（仍無揀選數據）。
