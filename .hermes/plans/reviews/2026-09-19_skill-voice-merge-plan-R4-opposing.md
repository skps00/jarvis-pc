# 反方 review R4（最後一輪）— 語音 skill 3 合 1 plan **v4**

> 2026-09-19；reviewer＝反方 subagent（**只讀**；唯一寫入＝本檔）。
> 對象：`.hermes/plans/2026-09-19-skill-voice-merge-plan.md`（**v4**）。
> 軌跡：R1 **4:6** → R2 **6:4** → R3 **7:3**（全 `go=false`）→ 本輪 **7:3**。
> 本輪範圍：只核 R3 嗰 3 項＋LOW，加 3 個**新角度**（改名可逆性／frontmatter 新欄位副作用／白名單標籤）。
> 方法：Hermes venv python 親跑——逐檔 sha1、raw-bytes decode 字數、**in-memory 拼出合併後樹**再 `grep` 模擬；`hermes curator status|list-archived`（唯讀）。無改 plan／skill／archive。

## ① 驗過嘅事實（真／假／未核實）

| # | v4 主張 | 判定 | 我自己跑嘅證據 |
|---|---|---|---|
| F1 | A2：**14 ＝ 11 逐字一致（含改名檔）＋ 3 有改動** | **真** | 搬入 14 檔＝pipeline refs 9（含改名者）＋`voice-setup-notes.md`＋hvow `scripts/` 2＋2 個 `SKILL.md` 副本。11 個 sha1 不變：6 個 pipeline refs（`8218ac008606`／`121e7982c861`／`9d41900d69b4`／`22143462e0dc`／`8e710f551ac8`／`83652527b638`）＋改名檔（`aec-implementation.md` → `voice-pipeline-aec-implementation.md`，sha1 仍 **`6b23881ed940`**）＋`2bf209e3855f`＋`077956e83a6c`／`ef65aa38a758`＋副本 `70fec0493ced`。3 個改動檔＝`windows-voice-pipeline.md`／`speaker-verification-ecapa.md`／`unprompted-speech-triage.md`。**11＋3＝14 閉合** |
| F2 | §3.4 7 行改動 Δ ＝ **+75** | **真** | 逐行真文字計：`:147` 改名 **+15**（R3 講 +14 係錯；`voice-pipeline-` 15 字）；`:36/:112/:187/:193` 各 +10；`ecapa:32`、`triage:16` 各 +10 ⇒ 15＋40＋20＝**75**；6 行各**恰 1 個**被替換 token；無第 8 行 |
| F3 | A3：新 frontmatter＋新指標節**已逐字寫入 plan** | **真** | plan L42–51（10 行 frontmatter）、L55–65（11 行指標節）逐字可抽 ⇒ R3「幽靈閘」已解 |
| F4 | A3：Δ ＝ +268／+734，總量 **222,964** | **假** | plan 自己寫「CRLF 保留」，而 umbrella `SKILL.md` 係**全 CRLF**（355 CRLF／355 `\n`）。CRLF 寫入：新 fm 379 − 舊 fm 109 ＝ **+270**；指標節 **+744** ⇒ Δ＝1,089、總量＝**222,976**（差 12）。LF 寫入：+264／+733 ⇒ **222,959**（差 5）。**222,964 兩種 convention 都計唔到**。+268 ＝ 369（LF 終結嘅新 fm）− 101（無終結符嘅舊 fm）＝**混單位減法**（一致值應 264）；+734 對唔上 733（LF）亦對唔上 744（CRLF）⇒ **gate 一跑即報錯**（唯一「零損失」閘 A2 已對，但 A3 仍係自己寫嘅數唔 derive） |
| F5 | A6：加 predicate 後「9 行 → **7 行白名單／餘 5 處**」 | **半真（未閉合）** | **合併前** predicate 後**確係** 7 行，逐條對得上：`electron-windows-overlay:11`、umbrella`:34/:110/:118`、`windows-desktop-automation:139`、`references/jarvis-hud-design.md:11`、`hermes-skill-library-governance:107`；另 2 行 `name:` 亦確係唯一其他命中 ✓。**合併後**（A6 自稱「只喺 `skills/` 樹」＝收貨後跑）唔同：新指標節**自己造出 4 行新命中**（umbrella `:31/:32/:34/:35`，因為節文內寫咗兩個 skill 名），另 umbrella 3 行歷史命中因插 11 行＋fm 增 6 行**位移 +17**（34/110/118 → **51/127/135**）。我 in-memory 合併樹實數：非排除命中 **13 行**，predicate 後 **11 行**（6 個檔）≠ 7 |
| F6 | LOW：「已吸收」行屬新指標節（第 3 行），A4 抽段 diff 仍空 | **真** | 節文第 3 行＝「- 本 skill 已吸收…」；節插喺 HOLD 段尾（`## ⛔`…`## Projects` 之前）⇒ HOLD 段**逐字未動**，A4 diff ＝ 空 |
| F7 | 新角度①：改名／還原可逆？ | **真（無新矛盾）** | `hermes curator restore` 係真 subcommand；`.archive/<skill>/` 保留**全棵樹**（實查 `git-branch-integration` 含 `references/`）⇒ 步驟 2 刪 14 檔＋步驟 3 restore 會原樣重建 `references/aec-implementation.md`（原名復原）。umbrella 自己嗰份同名但唔同內容（`6e4a08fb6911`）**唔會被覆蓋**。§0.1 講嘅修正亦真：`.archive/git-branch-integration/` 在，`skills/archive/` 唔存在 |
| F8 | 新角度②：加 `version/platforms/metadata` 副作用 | **半（未核實）** | `platforms` 係**真 hard gate**（`agent/skill_utils.py:227-272`，`PLATFORM_MAP: windows→win32`）⇒ 本機 win32 照 load，**A1／A7 數字唔受影響** ✓；但 umbrella 由「全平台」變「只 Windows」＝**第二個未記錄行為改變**（§4 只記 description 一項）。新 fm 形狀同館內慣例（`electron-windows-overlay`／`hermes-voice-windows`）一致、無欄位損失 ✓。**curator ownership**：`.usage.json` 帶 `created_by`／provenance（per skill 名），**冇** code path 由 frontmatter `author` 推 ownership（只有 `skill_linter`／`skills_sync_client` 讀 `author`）⇒ v4「唔抄 author」嘅理由**未核實**（但唔抄本身無害） |
| F9 | 新角度③：白名單標籤 | **假（標籤錯）** | `electron-windows-overlay:11` 唔係「歷史敍述」，係**活 frontmatter `related_skills`**（`[jarvis-companion, windows-desktop-automation, windows-voice-pipeline]`）⇒ 歸檔後成**懸空 cross-ref**。影響未核實（grep 級），但 A6 標籤係錯 |

## ② 逐條評 v4（對 R3 承諾）

- **A2：CLOSED（真）。** 14＝11＋3 親驗，byte 級無損；R3 嘅 16≠14 自相矛盾消滅。✅
- **LOW「已吸收」位置：CLOSED（真）。** ✅
- **A3：PARTIAL。** 幽靈閘已解（逐字文字入 plan ✓），但**寫死嘅總量 222,964 唔 derive**（CRLF 模型 222,976／LF 模型 222,959）；+268 係混單位、+734 對唔上任何量法。**呢個就係 R3「可斷言」嘅實質：數要計得出**——而家係「有數，但數係錯」。
- **A6：PARTIAL。** 2 行 `name:` 確係唯一漏項、predicate 有效 ✓；但枚舉係**合併前**值，收貨後實況 11 行（含新節自造 4 行＋umbrella 位移 +17）⇒「逐條有處置」未成立。
- **模式觀察（重要）**：v3 帶「16≠14」、v4 帶「222,964／7 行」——**連續兩輪同一 class**（plan 自寫嘅記帳數冇 re-derive）。全部係**驗收表**級、一行內可修，但正正係 A2/A3/A6 三個完整性閘本身。
- **設計層面：零殘留問題。** 內容零損失（A2 真）、還原 3 步可行（F7）、HOLD 段不動（F6）、無新自相矛盾。

## ③ 比分 ＋ flip conditions ＋ go/no-go

**正方 7 : 反方 3**（R4）。理由：R3 承諾「3 項全做＋無新自相矛盾 ⇒ ≥8:2」。事實：**A2 全解、LOW 全解、A3／A6 各半**（合共 3/4 項到齊），而*無*新自相矛盾（F7 親驗）。方向／機制全企得住、無任何設計改動需要，但 8:2 門檻（**3 項全做**）**未達** ⇒ 不能給 8:2；同時比 R3 有實質進步（唔係原地打圈）。

**最後 flip conditions（全部 1 行／1 個數）**：
1. **A3 改成 derive 得出**：二擇一——(a) 寫死「CRLF 寫入 ⇒ 總量 **222,976**（Δ：fm +270／節 +744／7 行 +75；新 fm 379、舊 fm 109、節 744）」；(b) 或刪 A3 只留 A2（R3 已允許）。
2. **A6 用合併後值重列**：predicate 後 **11 行**（umbrella 自造 4 行＝`references/windows-voice-pipeline.md`／`hermes-voice-windows.md` 名提及 ＋ 新節文；歷史 3 行改 **51/127/135**），並把 `electron-windows-overlay:11` 正名為**活 cross-ref（非歷史敍述）**→ 明文接受或記入 REMAINING_WORK。

**go = false**（R4 未達 8:2，已用滿 SK 3–4 輪上限 ⇒ **交 SK 定**）。

## ④ 停手報告（SK 用）

1. **逐輪比分**：R1 4:6 → R2 6:4 → R3 7:3 → R4 7:3（全 go=false）。
2. **卡死嘅載重決定**：唔係設計（設計零異議），係**驗收表嘅自寫記帳數** —— A3（總量 222,964 計唔出）＋A6（白名單由 7 行變 11 行）。
3. **最貴未知**：① 背景 curator 會唔會喺合併後再造一個 voice skill（三輪未解；要「合併後跑一次語音 session ＋ `hermes curator run`」才知）。② 新 description 對真實 routing 揀選嘅效果（兩個評審都只有 index 文字，無揀選數據）。③ `platforms:[windows]` 對 curator／sync 是否有任何 ownership 副作用（未核實）。
4. **我嘅建議**：**唔需要第 5 輪**。兩個 blocker 都係算術，唔涉設計；SK 可揀 (a) **批准執行**，但要 plan 作者**執行前一併改嗰兩個數**（順手 1 分鐘，改完 A2/A3/A4/A5/A6/HOLD 全部閘都可真跑）；或 (b) 要 plan 作者先改數再開工。**除嗰兩個數，v4 我睇唔到任何阻撓落手嘅理由**——內容零損失已 byte 級證明，還原路徑已親驗。
