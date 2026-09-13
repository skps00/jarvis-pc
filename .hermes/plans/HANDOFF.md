# HANDOFF — jarvis-pc（狀態區塊 + 逐日 index）

<!-- STATE:BEGIN -->
## 狀態（每次 session 尾／cron **改寫**；新 section 一律加喺本區塊**之下**）

- **目標**：JARVIS ONE（語音／HUD／alerts）穩定收尾 ＋ MC packai（Forge 1.19.2 primary）DSML 修復落地。計畫書：`.hermes/plans/REMAINING_WORK.md`
- **現狀（2026-09-13 13:0x 改寫）**
 - **jarvis-pc**：branch `feature/hermes-alerts-mcp`；PR #12 已 merge（`96be515`）；HANDOFF 重排（狀態區塊＋逐日 index）＋cron 修正（停 `git add -A`）今日完成 → commit 見下
 - **packai DSML**：T1–T4（`db245f5`）＋P1/P2/P5（`e85c4a5`）完成並親驗——真 bytes 偵測 false→true、解析 0→2 call、效能 4134ms→25ms、跨路徑去重 2 次；**T5 真機煙測未做**（要 SK 熄 MC 才 build／換 jar）
 - **alert pipeline**：live shadow 跑緊（sidecar 8765 UP、`alert_policy_mode: shadow`）；未夠 48h → 未可上 `enforce`
 - **語音**：sensevoice 短句粵語 garble（09-11 全日 6 句）→ 三選一（打字／MiMo 雲端／本地 Fun-ASR-Nano）等 SK 揀
 - **AI_Studio（非 JARVIS）**：Phase 0 完成；Phase 1 spike spec staged（等 SK 揀時段）；H3 workflows＋Ref2VA checkpoint 已備
 - **GPU**：5090 driver T581.42 TDR 已知（SK 決定唔郁）；重服務用完即卸
- **唔准郁（硬限制）**
 - 打機／用緊電腦：**零彈窗、零搶焦點**（先讀 `state/sk_activity.json`）
 - GUI 窗一律開**第二副屏幕**（SK 要睇嘅先主螢幕）；Chrome 主動開 = `bg_launch.py --minimized`
 - `AGENTS.md` 受保護（要 SK 明確 go）；唔准 `curl|sh`；**唔准入 secrets**（HANDOFF 視為可公開）
 - 長跑分支**唔准 squash-merge**；packai code 一律經 cursor-agent；郁 packai code 前必讀 skill `minecraft-modpack-ai-development`
- **未解（等 SK 決）**：① 語音 ASR 三選一 ② T5 時段 ③ 架構 fork-vs-light A/B/C ④ AI_Studio Phase 1 時段
- **下一步（優先序）**：T5 真機煙測（build→備份 jar→部署→真 log 檢查）→ 用數據決定 P3（hop-limit 出口仍漏）→ alert `enforce` 前真機驗收 → AI_Studio Phase 1
- **歸檔索引**：≤2026-09-11 全部搬 `plans/archive/HANDOFF-2026-09.md`；更舊見 `plans/archive/HANDOFF_2026-08-*.md`
- **參考段（喺檔尾）**：陷阱（重溫）／語音·硬體設定（驗證過）
<!-- STATE:END -->

## 逐日 index（一行一件；blocker 例外可 2 行）

## 2026-09-13 12:4x — 契約規則 ×2、Chrome 零搶焦點實測、packai DSML 修復（P1/P2/P5）
- **2026-09-13 13:0x**：停用 cron `jarvis-bglaunch-idle-test`（每 5 分鐘）—— SK 指示 stop；6 種開法已測完，cron **paused**（可 resume，非刪除）


**SK 今日新增嘅契約規則（已寫入 `C:\Users\skps9\AGENTS.md` ＋源頭 copy，md5 一致；兩次改動都先備份 `.bak-<ts>`）**：
1. **第一規則**（置頂）：做事前 → 風險評估 → 最壞情況 → 確認可用現有資源／工具還原（**資料零損失、指名 backup**）→ 才動手；還原唔到／有損失風險唔准做；重大決策先得 SK 批准。
2. **Plan／Idea Review 上限 3–4 輪**：到第 3–4 輪仍未達 8:2 → **停手、問 SK**（報告要齊：逐輪比分／卡死決定／最貴未知／建議）；每輪之間必須有實質修改。

**Chrome 代開（1c 定案）**：
- 實測 6 種開法（`bg_launch_focus_probe.py`，數字喺 `state\bg_launch_focus_probe.json`）：**只有「最小化開」零搶焦點**；任何「顯示出嚟」Chrome 都會自己 `SetForegroundWindow`（`LockSetForegroundWindow` 由背景 process 叫係無效，實測 return False）。
- 已改 `bg_launch.py` 加 `--minimized`（`SW_SHOWMINNOACTIVE`＋移窗唔用 `SWP_SHOWWINDOW`），默認行為不變；改前備份 `bg_launch.py.bak-20260913-105323`。**SK 定：佢叫 → 顯示；JARVIS 主動 → 最小化**（AGENTS.md 條款待 SK go 才更新）。
- 教訓已寫入 skill `windows-app-launch-focus`。

**packai DSML 修復（見該 repo `.hermes\plans\HANDOFF.md` 同 `docs\plans\`）**：plan v1→v3 經 R1（反方 7:3）／R2（正方 8:2）兩輪 review；T6（P1 有界 grammar／P2 canonical args＋跨路徑去重／P5 真 bytes 驗收）完成並由 Hermes 親驗（偵測 false→true、解析 0→2、主路徑唔再吐垃圾、病態效能 4134ms→25.5ms、全量 96 PASS／5 FAIL＝baseline、雙樹對稱）。commits：`db245f5`（T1–T4）、`e85c4a5`（P1/P2/P5）。
**未做**：`AskToolLoopCheck` K30–K34 未跑（要 gradle classpath）、mod 全量 compile、**T5 真機煙測（要 SK 熄 MC）**；hop-limit 出口仍漏（P3 等 T5 數據）。

**其他**：`docs/plans/` 現有兩份新報告（DSML 業界研究、fork vs 輕量評估）；PR #12 merge 早已完成（`96be515`）。

**下次（優先序）**：
1. **T5 真機煙測**（SK 熄 MC → build jar → 備份舊 jar → 部署 → 15 題 → 跑真 log 檢查＋`check_jar_contains_fix.py`＋gradle 跑 `AskToolLoopCheck`）→ 出報告。
2. 用 T5 數據決定 **P3**（hop-limit 出口 recovery）。
3. AGENTS.md 加「主動開 → `--minimized`」條款（等 SK go）。
4. 待 SK 決定：真機驗收清單（alert enforce）、AI_Studio Phase 1（4b 排後）、A/B/C 架構（5a 已解釋）。

# HANDOFF — JARVIS 交接（固定檔）

> **呢個係固定 handoff 檔**（2026-08-30 起）：每次 session 結束**更新呢份**，唔好開新日期檔；舊交接版本移入 `plans/archive/`。
>
> **排序規則（2026-09-10 起）**：新 session 一律**加喺最頂**（時間倒序）；唔好 append 落尾。更新完先 commit（`docs(handoff): ...`，唔 push）。
>
> 下次 session 起點：**JARVIS ONE 0.4.10 跑緊；`1bdac68`（alerts ctypes fix）已 push 且 09-10 23:4x 重啟 sidecar 後已生效（ctypes flood 清零、serve.log 已 truncate）；**jarvis-pc：feature 分支 `feature/hermes-alerts-mcp` 已 push ＋ 開咗 PR #12（<https://github.com/skps00/jarvis-pc/pull/12>，base `main`＝`ca463a3`，**未 merge**；2026-09-13 03:3x `git rev-list --count origin/main..HEAD` = **87**，**09-13 05:4x cron 再測 ＝ 89**（再加 `e55f1ea`／`ed4d3cf` 兩個 docs commit，已 push 上 feature 分支）實測——包含 08-10 之後所有未推工作，唔止 alert pipeline）；**MC 線 09-11 早：Arch-3/3a `1ba048f` 已 push ✅（真機驗收 PASS）；DSML scrub fix 已改／已驗／review SHIP 但**未 commit**；新 jar `012da9cc` 已 deploy（09-12 01:59 SK 真機跑：**DSML fix 生效 ✅**，但兜底路徑漏內部 FACT——見最頂 09-12 section）；OpenClaw/Hermes 架構比較已寫入 → 建議 A/B/C 未拍板**；09-11 凌晨診斷過 GPU driver TDR（SK 決定唔郁）**。讀呢份之前先讀：
> 1. `jarvis-pc\AGENTS.md`（專案 context——**自動載入規則已寫入主契約，唔使 SK 叫**）
> 2. `C:\Users\skps9\AGENTS.md`（主契約——Code Review 兩次規則已升格入契約）
> 3. `REMAINING_WORK.md` + `2026-08-29_self-evol.md`（計畫書，R1-R20b 齊全）

---

- **2026-09-13 13:0x（HANDOFF 重排，SK 批准）**：新增頂部狀態區塊（五元素）＋逐日 index 規則；搬 ≤09-11 sections 入 `archive/HANDOFF-2026-09.md`；「剩低」併入 `REMAINING_WORK.md`；改 `AGENTS.md`（新 section 加喺狀態區塊之下／只讀狀態區塊＋近 3 日／HANDOFF 可公開）＋修 cron `git add -A`
