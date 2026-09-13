# Douyin 收藏 → Improve Plan（吸收提議 v1）

> 基於 101 條 AI/coding 收藏分析（2026-09-02）。Purpose：對照社群 best practice vs JARVIS/Hermes 現狀 → gap → 具體改進提議。**全部提議要 SK 批準先落地。**

## Goal

將 SK 收藏反映嘅頂尖 Agent/vibecoding practices 對照我哋現有 workflow，列出**真正值得吸收嘅 gap**（唔係全部吸收——噪音已過濾），每個 gap 有具體落點（改邊個 skill / 調整邊個 workflow / 評估咩工具）。

## Gap 對照表（社群 practice vs 我哋現狀）

| # | 社群 practice（來源收藏） | 我哋而家 | Gap? | 提議 | 優先級 |
|---|---|---|---|---|---|
| G1 | **上下文隔離/任務拆解**（#17）：拆獨立子任務、唔好塞晒文檔入 prompt | 有 delegate_task/cron 但無系統性「拆解+隔離」方法論；今日 session 已 context compact ×2 | ✅ 真 gap | 將 3 步拆解法（精準拆解→獨立子任務→隔離上下文）寫入 self-evol/plan 相關 skill，複雜任務強制先拆 | 高 |
| G2 | **Codex 8 官方最佳實踐**（#55）：AGENTS.md/驗收/Plan/自動化/權限/Worktree/檢查點/分線程 | AGENTS.md ✓ 驗收 ✓ Plan ✓ 自動化(cron) ✓ 分線程(delegate) ✓；**權限粒度？檢查點？Worktree？未 audit** | ⚠️ 未驗證 | 做一次 8 條 audit（每條 confirm 或補）——結果寫入 AGENTS.md/skill | 高 |
| G3 | **永久記憶/知識庫**（#34/40/75）：Obsidian 知識庫做 Agent 長期記憶 | Memory 已 99% 滿（2140/2200）；有 session_search + Obsidian skill（vault 未整合做「成長知識庫」） | ✅ 真 gap | 評估：長期知識（projects/lessons/研究 notes）入 Obsidian vault 結構化儲存，memory 只留 pointer | 中（要試） |
| G4 | **AI 接力包**（#12）：Chat→Agent 交接標準格式 | cursor-agent 每次 instructions 重新寫（%TEMP%）；HANDOFF.md 有但 cursor dispatch 無標準 template | ✅ 真 gap | 設計標準「cursor dispatch template」（context/scope/驗證/報告固定格式）——存入 cursor-cli-integration skill | 中 |
| G5 | **可複用工作流 = skill**（#53） | Skills 系統已有（100+）且今日已自動 patch 2 個（反映緊） | ✓ 已實行 | 繼續：複雜任務完成 → offer save skill（已有規則）——**唔使改** | 低 |
| G6 | **第一版後 code review + 脆弱位**（#31） | pass1/pass2 已有 | ✓ 已實行 | 唔使改 | — |
| G7 | **驗收標準**（#13） | SK 規則已有 | ✓ 已實行 | 唔使改 | — |
| G8 | **多角度決策（COO 5 顧問）**（#5） | adversarial review 三階段已有 | ✓ 已實行（更嚴謹） | 唔使改 | — |
| G9 | **工具精選**（#33）：50 工具塞 prompt 反模式 | 23+ deferred tools（tool_search 按需載入）——架構上已避免 | ✓ 已實行 | 唔使改 | — |
| G10 | **操作→Skill 生成**（#38 Browser-BC） | 只有「完成後 offer save」——無自動捕捉操作軌跡 | ⚠️ 潛在 | 低優先：觀察 Browser-BC 類工具成熟度，暫唔裝 | 低 |
| G11 | **Agent 事故防範**（#4）：工具選擇/規劃錯誤 | AGENTS.md 工程判斷有（操作者可能錯/驗證假設） | ✓ 大部分 | 唔使改 | — |
| G12 | **馴服 AI 程序員 3 問題**（#66）：唔思考就編碼/過度複雜/刪有效 code | requesting-code-review + 工程判斷 cover 大部分 | ✓ 大部分 | 唔使改 | — |

## 提議分類

### A. 即刻做（改 skill/文件——SK 批準後 cursor-agent/直接）
- **A1（G1）**：新增「任務拆解 + 上下文隔離」3 步法入 plan skill——**複雜任務建議拆解**（精準拆解→獨立子任務→隔離上下文）——唔「強制」（避免過度工程）。實測確認：plan skill 現時 **0 提及** 拆解/上下文隔離——真 gap（今日 context compact ×2 係案例）
- **A2（G2→改）**：**cursor-agent 適用性 audit**——快速對照 cursor workflow 缺口（AGENTS.md/驗收/Plan Mode/自動化/權限/branch/檢查點/分線程）——**audit 前先定義決定 tree**：每項「有/冇/部分」+ 「如果有缺口，值唔值得補？」（避免 audit 完唔知點算）——缺口先補入 AGENTS.md，冇缺口就記錄

### B. 評估先（要試先知值唔值——獨立小 experiment）
- **B1（G3→改）**：**先試 Memory Consolidate，唔係直跳 Obsidian**——memory 97% 滿但入面有 entries 可精簡（例：「音訊」條長文可濃縮）——**Step 1：consolidate 現有 memory（30 分鐘）**——騰出空間後如果仲係要長期知識結構化 → 先考慮知識庫方案（Obsidian 或 notes 檔）——**實測：Obsidian vault 唔存在（SK 未用）**，由零建 = 高成本 + 同 session_search（FTS5 全文 recall）重疊——唔可以當 default 答案
- **B2（G4）**：cursor dispatch template 設計（context/scope/驗證/報告 4 段固定）——下次 dispatch 試用

### C. 記錄（之後再睇）
- C1（G10）：Browser-BC 類工具 watchlist
- C2（升級：**真正「import 新嘢」——至少揀 1 個做 PoC 級評估**）：收藏入面 Hermes 未用嘅工具——候選：mcp-builder（30 秒搭 MCP server）、Prime Agent RLM（可程式化子 Agent）、WeSight、Numen（同 super_minecraft_AI_player 概念撞，睇佢架構做 reference）——**SK 揀 1 個**，我出短評估（官方 docs → 可行性 → 值唔值入 stack）

## 自我確認 bias 修正（review round 2）

Gap 表 G5-G12「已實行」唔代表「收藏冇新嘢」——真正 import 係學收藏入面 Hermes 未用嘅工具/practices（C2 已升級）。「已實行」只係「workflow 層面確認」，工具層面（MCP/skill 生態/新 agent 架構）仍然開放。

## 唔會做（明確唔吸收）

- 噪音（營銷 caption）——記錄唔吸收
- OpenClaw 全套遷移（我哋 Hermes stack 已確立——OpenClaw 收藏當 reference）
- 一次性工具安裝潮——新工具要逐個評估

## Bias 註明（self-assessment limitation）

Gap 表 G5-G12「已實行/大部分」係我（Hermes）主觀判斷——我自己評估自己 workflow，傾向低估缺口。**SK 可以 challenge 任何一行**——特別係 G5-G12 判「已實行」嘅，如果你覺得實際運作未夠好，提出嚟我改判。

## Files

- Plan: 本檔
- 分析 notes: `%TEMP%\douyin_import_notes.md`

## 驗收

- [ ] SK 逐項批準/否決 A/B/C 提議
- [ ] 批準嘅即刻做項落地（skill/AGENTS.md 更新）
- [ ] 評估項有結果（PoC 或 trial 報告）
- [ ] 冇未批準改動

## Risks

- R1：吸收過度——收藏 content 唔等於適合我哋 stack（例如 Obsidian 方案可能同 session_search 重疊）——所以分「即刻做/評估先/記錄」
- R2：A2 audit 可能發現 AGENTS.md 大改——保守：補缺口為主，唔重寫
- R3：B1 PoC 時間成本——設 1 週時限，冇 value 就停
