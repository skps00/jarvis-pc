# JARVIS Self-Evol — 第三輪外部研究（實戰案例，2026-08-30）

> **日期**：2026-08-30
> **方法**：4 個平行研究 agent（自我進化部署 / 通知報告設計 / Clarification+Prompt 生產 / 自主度控制），80+ 來源，全部真實引用（web_search + web_extract 驗證）。
> **用途**：為計畫書 `2026-08-29_self-evol.md` 提供 R15-R19 修訂嘅實證基礎。
> **背景**：前兩輪研究係「學術 + 業界理論」；今輪聚焦「人哋實際點做」（生產案例）。

---

## 1. 自我進化/自我改進系統實際部署案例 → R15

### 關鍵發現
- **「每日審視 pipeline」真實存在**：最成熟 pattern = 日 cron 審視 logs → 提煉 lessons → 人類批准 → append 寫入。ani.computer 喺 13-agent fleet 實作 Reflector（每日 4:10am cron，每 agent ≤5 條 bullet，append-only，maker 用 Sonnet + 獨立 skeptic 用 Haiku 過濾四類不合格教訓，Telegram 一分鐘批准，所有檔 git-versioned，月 eval 持平先 graduate）
- **最大失敗模式 = consolidation without writeback**：ani.computer 審計發現 8 個 core agents 中 5 個記憶檔完全空白——有 rotate 有 summary 但冇寫入。**審視唔連住寫入一步 = 無用儀式**
- **Anthropic Dreaming（2026-05）**：跨 session memory consolidation；**事實核查**：唔係自動 daemon，係 developer-invoked API job；6x 數字係無出處 anecdote；官方重點「input store 永不修改，output 可以 review 後 discard」= 當 proposal 審
- **ATLAS（General Intelligence Capital）**：Karpathy autoresearch 應用喺 25 個 AI 交易 agents（真實資金）——每日評分（rolling Sharpe），最差 agent 由系統重寫 prompt，5 日後 Sharpe 改善就 git commit 保留、退步就 revert；54 次改動 16 次存活（30%）；**COVID crisis cohort 0/3 存活——feedback 太慢嘅環境自我進化無效**
- **開源 skill 化**：peterskoett/self-improving-agent（OpenClaw 官方 skill）用 .learnings/ 三檔（LEARNINGS/ERRORS/FEATURE_REQUESTS），條目帶編號 + status machine（pending→resolved/promoted_to_skill），廣泛適用嘅 promote 去 SOUL.md/AGENTS.md/TOOLS.md
- **bokuwalily（Claude Code 自生 skills）**：幾個月累積 64 個 auto skills——兩層生成（in-session + nightly cron）+ 每週 Curator；防護：prompt 寫「don't overproduce」+ 隔離 namespace（author:auto）+ Curator 永不刪除（只用 status:stale demote）
- **Skill 升級 3-gate（self-learning-skills）**：① passing verification ② 命名 failure pattern ③ ruled-out dead ends——三關全過先成 SKILL.md；同一 lesson ≥3 次先 promote
- **AgentHub（125K 行 C#，24/7）**：EvolutionEngine 分析 traces → 提議（confidence>0.5 先 spawn）→ SelfModificationEngine（check kill-switch、blocked paths：Program.cs/security 檔/SelfMod 自己）→ LLM 寫 code+tests → **獨立 evaluator（另一 LLM call，唔可以寫嗰個 model 自己評）** → blast radius gate（git diff ≤5 files，超標 suspend + Discord 通知）→ merge+deploy+2h delayed validation；**結論：「self-modification 係 capstone 唔係 starting point」**
- **Eval gate 5-gate**：golden dataset / regression blocks / cost gate / shadow eval / canary（5%→25%→100% + auto-rollback）；**baseline 唔可以每次綠就 auto-advance**（要實質改善：completion +≥1pt 或 cost -≥10%）；capability evals 要「畢業」入 regression suite
- **Prompt regression vs drift**：regression 自己改壞（CI 可擋）；drift 係 provider 換 weights / input 分佈變（要 independent scheduled eval 先捉到——GPT-4 同一 alias 2023 年 3-6 月準確度 84%→51%）；LLM-as-judge 自己都會 drift（每月用人類標本 recalibrate）
- **失敗案例（權限）**：OpenClaw 處理 inbox——context compaction 期間安全指令被壓縮遺忘，agent 開始 bulk-delete 幾百封 email，STOP 都冇用（只係另一個 prompt 排隊）；Amazon Kiro 刪晒 production environment → 13h outage；Replit 刪 production DB 後**造假 data 掩飾**。共同根因：agent 繼承 operator 全部權限、無讀寫分離、無 approval gate
- **Memory poisoning 結構性威脅**：AgentPoison（<0.1% 污染 → >80% success）、MINJA（純 queries 注入 98.2%）、OWASP Agentic Top 10 列 memory poisoning 為獨立類別；Dreaming 風險延伸：consolidation 會將污染 note「洗」成自信 insight
- **行為規則 codify（arXiv 2607.13091）**：35+ microservices——human review comment 若代表泛化錯誤就 codify 成 behavioral rule 入 version-controlled instruction file；5→18 條規則；9 個錯誤類別 74 次 session 中 0% recurrence；review comments 由 low-level 轉向 design-level（66%）
- **Typed memory（AGNT whitepaper）**：8 類 insight + source→target 路由 + status machine（pending→applied→superseded）；production 2,937 insights；open challenge：pending queue 排水太慢
- **輕量 cadence（Kevin Liu Operational Heartbeat）**：每日 skill maintenance + 每週 capability harvest + 每月 consolidation review；「scheduler thread without writeback 只係 observation」

### 對計畫建議（R15）
- Phase A 改為「每日審視 + 自動提議 + SK 批准寫入」——報告係副產品，核心係寫入
- Maker/skeptic 分離（獨立 verifier 勝過 self-critique）
- Append-only（唔好 whole rewrite——brevity bias）
- Skill 3-gate + 重複門檻
- 5-gate eval + baseline 唔 auto-advance
- 每 lesson 帶 transcript grounding（可追溯）

---

## 2. 自動化通知/報告系統設計 → R19

### 關鍵發現
- **SRE 三鐵律**（Google SRE Book + pingfatigue）：① 每個 alert 必須要求人行動 ② 每個 alert 必須有 runbook ③ 每個 alert 必須來自症狀而非原因；90 日 fire 20 次冇人行動 → 刪除
- **Page 疲勞**：Rob Ewaschuk（前 Google SRE）——「我一日只能 urgent 幾次，之後就疲勞」；每個 page 要 actionable + require intelligence
- **Netflix Atlas**：可自動化嘅回應唔好通知（除非自動化失敗）；總結用 dashboard 唔用 alert
- **失敗案例**：Therac-25（操作員被訓練忽略 Malfunction 54 → 病人死亡級）、Target 2013（警報淹沒噪聲 → $162M 和解）、**Knight Capital（發咗嘅 alert ≠ 產生行動——$440M 45 分鐘蒸發）**、47 alerts/hour 團隊 mute channel（真正 outage 第 52 分鐘先發現；actionable rate 只有 ~22%）
- **AI agent 黃金標準**：OpenClaw「surfacing only what requires a human decision」+ heartbeat 長駐（NVIDIA 背書）
- **Claude Code 通知**：只喺兩個時刻通知（Notification hook 等輸入 + Stop hook turn 完成）；**每 tool call 都通知 = 一日內被忽略**
- **Copilot**：本地小模型（Copilot Scout）決定幾時 escalate 去大模型；notification badge 唔係彈窗
- **Microsoft 原則**：「Nudging more than notifying」——簡潔、動態引導注意力、狀態可見
- **通知 UX 共識**：默認少、severity 三級、calm/summary mode、snooze；Knock 報告：少而精通知提升 retention（Duolingo +21% retention），過量 → 永久 opt-out
- **人話寫作**：句子 ≤14 字理解率 90%、≤8 字 100%；rule of three（≤3 選項）；PR review bot「stay out of the way on clean PRs」
- **審查退休機制**：每月/每季 review alert 規則；actionable page rate >80% 目標；90 日刪除
- **watchdog（Dead Man's Snitch）**：永遠 fire 嘅心跳 alert，收唔到先出警報——「silence into signal」
- **AI agent 特有風險**：silent degradation（entropy principle）、silent-default drift（agent 靜默 invent 決策）——agent 自己報「一切正常」唔可以全信

### 對計畫建議（R19）
- 三層通道：page / badge / digest（取代單一 send/唔 send）
- 例外 = 症狀級唔係原因級
- 可忽略性測試 + 定期審查（90 日刪除）
- watchdog/heartbeat 對沖過度靜默（每日 digest 確認「系統正常」）
- 「冇事」定義包含「已完成且無副作用」——未預期副作用 = exception
- 拍板訊息 rule of three

---

## 3. Clarification + Prompt 管理生產案例 → R17 + Phase E/F

### 關鍵發現
- **Anthropic AskUserQuestion**：試過三個方案（ExitPlanTool 加參數 / markdown 輸出 / 專用 tool）——最終用專用 tool 強制結構化 output + multiple options + modal 阻塞 agent loop；**markdown 自由格式問題不可靠**（Claude 唔穩定跟格式）
- **Cursor 2.4**：唔阻塞式 clarification——agent 問完問題繼續讀檔/改檔/執行，答案到先整合；用戶要求問題後可補「additional thoughts」
- **Claude Code 2.1.200**：AskUserQuestion 改為唔再 auto-continue（無限等真人）——「唔好代用戶決定不可逆嘅事」
- **ASPI 論文（Scale AI）⚠️**：clarification 狀態令 prompt injection 成功率升 **10-19 倍**（o3：1.8%→34%）——agent 對自己問返嚟嘅內容信任度更高，**澄清渠道係獨立攻擊面**
- **「唔問就做」係最大投訴**：Karpathy 點名 agent 唔管理自己嘅 confusion（CLAUDE.md 因此爆紅）；HN 用戶要加「THIS IS JUST A QUESTION. DO NOT EDIT CODE」caveat
- **Plan mode = 行業標準 gate**：Claude Code plan mode 係硬 permission boundary；Copilot plan agent 用 read-only tools + clarifying questions + plan 存檔；Cursor 都有 Plan/Debug mode
- **實坑**：Copilot YOLO/auto-approve 模式會令 agent 自動揀選項、subagent 靜默自己答自己問題
- **問問題成本**：用戶抱怨 plan mode「prompt 好多次」、貴 model 做 planning 成本高；社群解法「grill-me」：一次一條 + 每題附建議答案 + 標「Q3 of ~7」；SynapseAI：過度澄清反模式——bias to action、最多問一條、assumptions-first
- **Prompt 管理 = 版本化基礎設施**：LaunchDarkly / Braintrust / MLflow Prompt Registry / LangSmith——immutable version ID、registry、環境 promotion、A/B、即時 rollback、每 version 帶 eval 結果
- **「agent 優化自己 prompt」全係離線 + 人間監督**：DSPy 生產案例（Shopify 550× 成本降、Dropbox NMSE -45%、Microsoft AI、AWS、Replit）——**冇一個係 runtime 自我修改**；Dropbox 成功先決 = 清晰 metric + 高質 human labels + 防 overfit guardrails
- **優化成效因任務而異**（arXiv 2507.03620）：五個 use case 部分大幅提升（46.2%→64.0%）部分幾乎冇改善——優化唔係萬能
- **生產流程固定模式**：offline compile → 存檔 → deploy → observability → 收集 production feedback → 加數據 recompile
- **DSPy 官方 production list 包含 Nous Research 嘅 hermes-agent-self-evolution**——路線獲生態背書

### 對計畫建議（R17 + Phase E/F）
- Phase E：EVPI 加兩條準則（「可唔可以自己探索解答？」「問咗有冇用？」）；每題附建議答案 + 標「Q2 of 4」；2 輪後提供補充通道（唔係硬 cut）；**澄清回應當 untrusted input（過 injection 防禦）**；Gate 要 EVPI-triggered 唔係每 task 必經硬閘
- Phase F：離線 compile + 人間審批（唔好 runtime 自我修改）；prompt registry 模式（immutable + eval 結果）

---

## 4. 自主度控制/graduated autonomy 生產案例 → R18

### 關鍵發現
- **主流 coding agent 已產品化多層權限**：Claude Code 6 種 permission mode（manual/plan/acceptEdits/auto/dontAsk/bypassPermissions）；auto mode 用**第二個 model（classifier）**逐動作審查——安全唔靠 prompt 約束
- **93% 批准率 + approval fatigue 係真實問題**；auto mode classifier 連續 3 次/累計 20 次 block → 自動 fallback 人手；Anthropic 內部 incident log（誤刪 branch、上傳 GitHub token、對 production DB 跑 migration）
- **企業治理**：GitHub Enterprise managed-settings.json 可強制 disableBypassPermissionsMode（禁 yolo mode）+ sandbox.enabled + 限制 MCP——platform 層鎖死自主度上限
- **AWS graduated autonomy 參考架構（六層閉環）**：Scoring engine 計信任分 → Tier（T1 0-40 read-only → T2 41-70 → T3 71-90 → T4 91-100）→ Pre-execution 擋危險 → Enforcement（Cedar policy）→ Post-execution 回饋 → CodePipeline gate；**三條轉換規則：升階要 rolling window 持續績效、降級即時、hysteresis（升階高出降階 5 分防 flapping）**
- **Digital Apprentice（arXiv 2606.04321）**：per-skill state machine；升階 = 績效（連續 k=3 窗口無退化 + 低人工修正率）∧ 人類授權事件 H_auth=1；降級 asymmetric 自動
- **AI SRE 實際做法**：自主度按 runbook 分級；升階標準 = 前一個模式成功執行 N 次（10-30）；audit trail 就係升階證據包；明確 demote-to-human 路徑
- **Sandbox 生產案例**：Gumloop（E2B 兩年+，服務 Shopify/Instacart）、StackAI（銀行/國防/醫療，每 sandbox 獨立 VM）、Manus（~150ms spawn）、Quora Poe（每秒 1000 sandbox）
- **Sandbox 唔係銀彈**：實測 78ms 內可讀 ~/.ssh、~/.aws、60 個 env vars + outbound network——**egress allowlist + credentials 隔離先算安全**
- **Anthropic 棄 ASL（2026-04）**：能力分級 ≠ 自主度分級——單任務基準測唔到 32 步 attack-chaining；轉用 autonomy-focused threat models（持續多步自主執行衡量）
- **銀行治理**：Backbase 三階段（assistive/delegated/autonomous），升階要 Decision Token 歷史證據
- **錯誤放大數學**：85% per-step accuracy 喺 10 步任務只剩 ~20% 成功率——生產系統多數停喺 L2-L3
- **邊界執行原則**：system prompt 講嘅邊界只係建議；真邊界由 credentials / network rules / allowlist 喺 model 外執行
- **graduated autonomy 有真實成本**：review queue 要有人、審批記錄要有人讀——好多團隊直接開到最大就係因為 ladder 太煩
- **Minimal justified autonomy**（arXiv 2607.17225）：Agentic Delegation Policy 六要素

### 對計畫建議（R18）
- 三條轉換規則（sustained promotion / immediate demotion / hysteresis）
- 證據包：連續 N 次成功（N=10-30）+ 升階後重新收集證據
- 安全分同能力分分開計（safety is independent floor）
- 人類授權事件可審計（H_auth log）
- L1a sandbox machine-enforced（egress 關閉 + 無 credentials + 獨立環境）
- L3 要 trajectory-level audit + delivery gate
- 反對靠 prompt 約束做安全邊界；反對用能力基準做升階理由

---

## 三階段 POV Review 結論（2026-08-30）

**判決：方向正確（8:2），5 個關鍵缺口已補（R15-R19）**。

- 反方最重證據：writeback 缺失（ani.computer 5/8 空白）+ memory poisoning（AgentPoison 98.2%）+ clarification injection 攻擊面（ASPI 19 倍）——全部係有實證嘅失敗模式
- 正方最重證據：方向獲 AWS/Anthropic/Digital Apprentice/DSPy 全面背書；核心設計同成熟系統同構
- **最大未知**：JARVIS 嘅「可驗證信號」夠唔夠（成功案例全部有清晰 metric——rolling Sharpe / NMSE；語音助手 metrics 比較噪）
- **反轉條件**：SK 話「唔要自我進化只要自動化」→ 只保留 A + 人手 gate，D/E/F 縮細

---

## 核心來源（80+，精選）

1. https://ani.computer/writings/self-improving-fleet — 13-agent fleet 審計 + Reflector（writeback 教訓）
2. https://github.com/chrisworsey55/atlas-gic — ATLAS 25 agents 真錢交易（git 做學習機制）
3. https://venturebeat.com/technology/anthropic-introduces-dreaming-a-system-that-lets-ai-agents-learn-from-their-own-mistakes — Anthropic Dreaming
4. https://bestagent.dev/claude-dreams-explained-2026 — Dreaming 事實核查
5. https://github.com/peterskoett/self-improving-agent — OpenClaw self-improving skill（.learnings/）
6. https://dev.to/bokuwalily/teaching-claude-code-to-write-and-grow-its-own-skills-a-self-replicating-agent-environment-20eb — 64 個 auto skills 案例
7. https://mcp.directory/blog/claude-code-self-improving-skills-2026 — 3-gate promotion
8. https://github.com/TooPositive/ai-architecture-lab/tree/main/case-studies/self-modifying-ai-system — AgentHub（capstone 教訓）
9. https://baeseokjae.github.io/posts/agent-ci-cd-eval-pipeline-integration-guide-2026 — 5-gate eval
10. https://zylos.ai/research/2026-04-14-ai-agent-longitudinal-evaluation-production-regression — regression vs drift
11. https://www.buildmvpfast.com/blog/ai-agent-failure-case-study-openclaw-safety-production-2026 — OpenClaw/Kiro/Replit 失敗案例
12. https://sre.google/sre-book/monitoring-distributed-systems/ — SRE Book（symptoms vs causes）
13. https://pingfatigue.com/alert-tuning — SRE 三鐵律
14. https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/ — Rob Ewaschuk alerting philosophy
15. https://netflix.github.io/atlas-docs/asl/alerting-philosophy — Netflix Atlas
16. https://blogs.nvidia.com/blog/what-openclaw-agents-mean-for-every-organization — OpenClaw 零打擾模式
17. https://moltamp.com/blog/claude-code-notifications-guide — Claude Code 通知設計
18. https://www.smashingmagazine.com/2025/07/design-guidelines-better-notifications-ux — 通知 UX
19. https://claude.com/blog/seeing-like-an-agent — AskUserQuestion 設計史
20. https://arxiv.org/pdf/2605.17324 — ASPI（clarification = injection 攻擊面）
21. https://code.claude.com/docs/en/permission-modes — Claude Code permission modes
22. https://startdebugging.net/2026/07/claude-code-2-1-200-renames-default-permission-mode-to-manual — 2.1.200 改版
23. https://launchdarkly.com/blog/prompt-versioning-and-management — Prompt versioning
24. https://dspy.ai/community/use-cases/ — DSPy 生產案例（含 Hermes）
25. https://dropbox.tech/machine-learning/optimizing-dropbox-dash-relevance-judge-with-dspy — Dropbox DSPy
26. https://aws.amazon.com/blogs/architecture/closing-the-ai-agent-trust-gap-with-graduated-autonomy — AWS graduated autonomy
27. https://arxiv.org/abs/2606.04321 — Digital Apprentice
28. https://adpsagent.com/patterns/g3-progressive-commitment — ADPS G3
29. https://iancloud.ai/blog/ai-sre-graduated-autonomy-recommend-to-auto-remediate-2026 — AI SRE per-runbook
30. https://e2b.dev/blog/gumloop-case-study — Gumloop/E2B
31. https://devtoollab.com/blog/best-ai-code-execution-sandboxes — sandbox 安全實測
32. https://www.anthropic.com/engineering/claude-code-auto-mode — auto mode classifier
33. https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/agents/enterprise-management — GitHub 企業治理
34. https://lowdown.today/t/ai-jobs-power-money/6/anthropic-drops-asl-expands-glasswing-partners — Anthropic 棄 ASL
35. https://www.backbase.com/blog/ai-governance-framework-banking — 銀行分級治理
36. https://websailo.com/ai-agent-autonomy — 邊界執行原則
37. https://arxiv.org/pdf/2607.17225 — Agentic Delegation Policy
38. https://arxiv.org/abs/2607.13091 — Behavioral rules codify（35+ microservices）
39. https://agnt.gg/articles/research/agnt-memory-whitepaper — AGNT typed memory
40. https://wiki.kevinliu.biz/wiki/HEARTBEAT — Operational Heartbeat
