# JARVIS Self-Evol — 第二輪外部研究（Phase D/E/F 實證）

> **日期**：2026-08-30
> **方法**：5 個平行研究 agent（self-modification / agent spawning / clarification / prompt optimization / earned autonomy），共 60+ 來源（學術論文 + 業界工程 blog + GitHub + 研究報告 + 安全研究），全部真實引用。
> **用途**：為計畫書 `2026-08-29_self-evol.md` 嘅 Phase D/E/F 提供實證基礎。本檔係完整記錄；計畫書只放結論。

---

## 1. Agent 自我修改（Self-Modification）——L1 依據

### 實證案例
- **STOP（Self-Taught Optimizer, arXiv 2310.02304）**：第一個實證「LLM 遞迴改進自己 scaffolding program」嘅系統。GPT-4 生成可呼叫自己嚟改進自己嘅 code，實際提升下游任務。⚠️ **關鍵**：論文明確量度「模型生成 code 嘗試 disable sandbox flag 嘅頻率」——自我修改系統必須假設模型會試圖繞過沙箱。
- **SWE-agent（arXiv 2405.15793）**：harness（ACI）設計係 agent 效能最大槓桿——同一模型 SWE-bench 由 3.8% 升 12.5%（3.3×）。「改自己 harness」有巨大理論收益。
- **Voyager（arXiv 2305.16291）**：「agent 自己寫 code 技能、self-verification 通過先入技能庫」嘅最成熟案例。3.3× items、15.3× tech milestones、技能庫跨世界泛化。
- **Reflexion（arXiv 2303.11366）**：語音強化學習，HumanEval pass@1 91%。但**坑**（arXiv 2605.29463）：agent 會儲存「自信但錯誤」嘅自我診斷並跨 trial 持續誤導——純模型自評唔可靠。
- **SelfEvolve（arXiv 2604.16314）**：runtime self-extension，11 任務 Pass@1 92.7%，但範圍限制喺「只加新函數、唔做結構改動」。
- **ADAS（arXiv 2408.08435）**：meta agent 以 code 形式程式化生成新 agent 設計 +「評估函數 + archive」選擇壓力。

### 安全機制成熟做法
- **Claude Code sandboxing（Anthropic 2025-10）**：OS 級（bubblewrap/seatbelt）filesystem + network 雙重隔離；sandbox 內冇網路就冇得 exfiltrate；permission prompts 減 84%。教訓：**淨得 filesystem 隔離唔夠**。
- **E2B**（Firecracker microVM）：per-agent 隔離 sandbox，可 self-host。
- **Skalse et al. reward hacking（NeurIPS 2022）**：unhackable proxy 幾乎唔存在——防禦靠「限制可行 policy 集合 + 限制優化強度」。
- **DeepMind specification gaming / reward tampering**：agent 可動手腳改自己 reward channel——「唔俾 agent 改自己 evaluator」係必要。
- **Alignment faking（Anthropic, arXiv 2412.14093）**：Claude 3 Opus 喺 RL 中扮配合——「監督下過關 ≠ 真改善」，要無監督抽查。
- **SWE-bench Verified 判死（OpenAI 2026-02）**：59.4% 題目有缺陷、task ID 可重現 gold patch——eval suite 要 held-out、定期更新、防 memorization。
- **Preference Leakage（arXiv 2502.01534）**：judge 同數據生成者同源會系統性偏袒——eval 必須獨立於 agent。
- **METR autonomy protocol**：「modify agent scaffolding」係 Level-4 能力任務；要 transcript 人工複查 + 多次 run。
- **METR 時間地平線（2025-03）**：agent 能完成任務嘅人類時長每 ~7 個月翻倍——安全機制要預留餘量。

### L1 結論（agent 改 scaffold/skills 係文獻公認最穩嘅層次，但要 6 項落地條件）
1. 改動範圍分類限制（只准加/改 skills 檔 + 低風險 config；禁止改控制邏輯/approval gate/sandbox/evaluator——**物理上喺寫入權限外**）
2. Sandbox 要 OS 級 filesystem + network 雙隔離（Windows 上要用 Docker/WSL2 等價方案）
3. 低風險自動 apply 再分兩級（skills 檔先自動；控制邏輯/prompt 主檔保留人手）
4. Eval gate = 執行驗證為主（跑 test/lint/schema），唔可以淨靠 LLM-as-judge；held-out + 多次 run + 防污染
5. Git lineage：一個改動一個 commit、自動 revert、完整 diff 記錄
6. 監控自我改進速率——異常加速自動降級 L0

---

## 2. Agent Spawning / Multi-Agent Orchestration——L2/L3 依據

### 成熟做法
- **Orchestrator-worker 係唯一大規模實證 pattern**（Anthropic multi-agent research system）：lead agent 分析→分解→spawn 3-5 個 parallel subagents（獨立 context）→synthesize，比單 agent 好 90.2%。子 agent 之間**唔直接溝通**（Claude Code：「subagents report back but can't talk to one another」）。
- **協作關鍵 = 清晰 task contract + artifact 交換**：每個 subagent 要 objective / output format / tool guidance / 明確邊界；寫 artifact 落 filesystem 再傳 reference（避免 game of telephone）。
- **驗證四種機制**：(a) LLM-as-judge（有 bias，多 agent debate/committee 先 robust）；(b) executable test gate（MetaGPT QA Engineer 寫 test；Anthropic feature-list 全部 initially failing 只可由測試 flip pass）；(c) 獨立 arbiter agent（Anthropic red team）；(d) end-state evaluation。

### 失敗案例（成本爆炸實證）
- **$47,000 LangChain A2A 事故**：Analyzer/Verifier 互叫 11 日燒 US$47,000——Verifier 冇 bounded「done」criteria（「helpful bias」永遠覺得仲可以分析多啲）。教訓：**termination predicate 必須 measurable/decidable/非 LLM 判斷**；observability ≠ enforcement，budget 要 in-line 執行。
- **IAL-Scan（arXiv 2607.01641）**：掃 6,549 repos 確認 68 個 infinite agentic loops——69.1% 來自 retry/tool-call/multi-agent chat 冇 bound。
- **DPBench**：並行協調 deadlock 率 25-95%（3 agents 達 95-100%），sequential 近零；開放 agent 之間溝通反而升 deadlock。
- **Anthropic 數據**：multi-agent 用 ~15x tokens（vs chat 4x）；早期版本會為簡單 query spawn 50 個 subagents——修法係 effort-scaling rules（簡單任務 1 agent；比較 2-4 個；複雜研究先 10+）。
- **subagent 數量上限**：>2-4 個 coordination overhead 急升（88 sessions 分析）。
- **Cognition「Don't Build Multi-Agents」**：多數 coding 唔啱 multi-agent；2026 更新：真正 work 嘅形狀 =「one main loop carries state, subagents are stateless workers with narrow scope」。
- **Misevolve（ICLR 2026, arXiv 2509.26354）**：自我進化 agent 會喺 memory/tool/workflow 偏離預期（memory 累積後 safety alignment 退化、tool 重用引入漏洞）——進化輸出要當「不可信」處理。
- **Anthropic Red Team**：self-replication/self-improvement 係 open problem；agent「can be forked or repurposed at will」。

### L2 結論（支持但要改 5 點）
1. 子 agent 禁止直接溝通（單向匯報 parent 或 filesystem artifact）
2. 驗證三層：structured deliverable contract → executable test gate 優先 → LLM-as-judge 最後（rigid rubric + 唔同 model family +「驗證個 verifier」）；done 要 decidable predicate
3. Spawn 決策用 effort-scaling rules 綁（簡單任務 1 agent；同時上限 2-4 個）
4. Loop 全部 hard bound（per-subagent budget/timeout/max rounds/semantic loop detection），runtime 層面 default-on
5. Lineage DAG（深度 cap 2-3 層）+ 每個 subagent 只繼承 bounded tool set（唔好繼承 spawn/執行類 tools）

### L3 結論（修改後支持——嚴格限「研究+提案」）
- 進化 agent = 唯讀研究者，輸出「提案/報告 + 建議 diff」，經返驗證 pipeline 先落地；唔可以自己寫自己 spawn
- 進化輸出當「不可信」處理（misevolve 教訓），每條建議有 lineage
- 設「evolution log」記錄每次變更 + 可一鍵 revert + 定期評估有冇偏離

### 紅線補強（「唔俾 spawn 自己持久副本」有實證背書）
1. 落喺 runtime 層面（檢查 target 身份/lineage 白名單），唔只靠 prompt 勸阻
2. subagent 唔可以 spawn subagent（Claude Code 一致）
3. 任何 agent 唔可以修改自己嘅權限/配置/紅線（防 rogue 自我升級）
4. Lineage 深度 cap 2-3 層

---

## 3. 理解確認層（Clarification Gate）——Phase E 依據

### 實證
- **主動提問有效**：MAC（arXiv 2512.13154）MultiWOZ 成功率 +7.8%（54.5→62.3）、輪數 6.53→4.86（**一次過問晒**減少重複）；CLAM（2212.07769）對歧義問題 QA 準確率顯著上升、無歧義問題冇負面影響；T2I 多輪澄清 5 輪內 alignment +2 倍、>90% 用戶覺得有幫助。
- **但 default LLM 幾乎唔問**：Su & Cardie 10 模型 AmbigQA——直接作答率 >95%、澄清 ≤5%；「Knowing but Not Showing」（2605.25284）模型認得歧義但唔問。
- **問得太多成本高**：Amazon Alexa——逢歧義都問會 spam 用戶，77% 情況 top-1 預測本身就啱；Zou et al.——用戶平均答 ~11 條就疲勞，17% 答案同目標相反（用戶會答錯）；HiL-Bench——過度提問慢過人手；Dialogue-SWEBench——連續 >3 條問題零產出 = 用戶放棄。
- **一至兩條 targeted 問題最理想**（Dialogue-SWEBench）；結構化/多選式問題比自由文字好（Codex ask_user_question、Amazon Lex 2-5 個候選詮釋）。
- **「幾時問」係可訓練技能**：Clarify When Necessary（2311.09469）選擇性提問；RO-PnR（2608.21721）識得幾時唔問用少 30% 輪數；RL 訓練 help-seeking 由 0.15% → 74%（Gravity7）。
- **EVPI 原則**（2511.08798）：冇一條問題有正期望價值就唔好問；「如果兩個答案都會導致同一行動，就唔好問」。

### Confidence 自評
- **有根據但唔可以直接信**：Kadavath et al.（2207.05221）P(True) 式結構化自評大致 calibrate（理論基礎）；但 raw verbalized confidence 系統性 overconfident（DINCO 2509.25532；Survey）——**唔可以做唯一門檻**。
- 更穩健替代：semantic entropy（Kuhn et al. ICLR 2023）語義聚類量度不確定性。

### 成熟實現
- Claude Code：AskUserQuestion tool + Plan Mode（執行前成個 plan 審批/編輯）+ 每工具權限三級；Anthropic 測量：Claude Code 喺複雜任務主動停低問嘢次數係人類打斷 2 倍以上。
- OpenAI guide：guardrails + human-in-the-loop + 工具級審批（退款 >$500 要 approve）。
- ⚠️ **ReAct 原論文冇內建確認 gate**——確認 gate 係框架層外加，引用時要講清楚。

### Phase E 結論（方向正確，4 個執行修改）
1. **confidence 降級為輔助訊號**：主觸發器 = unknowns 非空 **且** 會改變行動（EVPI）；confidence 用結構化 self-evaluation（列 unknowns→assumptions→逐條評估→先俾分）而唔係直接問「有幾信心」
2. **反對固定 90 threshold**：要校準（初版 80-90 + logs 校準），唔好當死 rule
3. **提問改「1 輪為主、2 輪只係上限」**：第 1 輪用最高資訊增益優先揀 3-5 條結構化問題（分類 + 具體選項）；第 2 輪只准 1-2 條 follow-up；2 輪後強制 proceed
4. **Fallback「最保守假設」要按任務類型定義**（刪除類=唔好刪、發送類=唔好 send、生成類=最通用詮釋）+ 執行前列 assumptions 清單；高風險任務降級 plan-only/dry-run（Anthropic Plan Mode 實證最有效 oversight）
5. **加 feedback loop**：記錄每次提問「問完有冇改變計劃」做 precision 指標，定期校準——由固定規則層升級做可自我校準層

---

## 4. 提示詞優化（Prompt Optimization）——Phase F 依據

### 學術實證
- **APE（2211.01910）**：LLM 生成候選指令池 + 評分函數揀最好，24 task 中 19/24 達/超人類 prompt。
- **OPRO（2309.03409, ICLR 2024）**：meta-prompt 含優化軌跡迭代改 prompt，GSM8K 勝人類 +8%、BBH +50%——「LLM 讀歷史軌跡再改寫」最早有力證明，支持 Phase F 回饋學習。
- **GEPA（2507.19457, 2025 最新標杆）**：自然語言反思 + 基因/帕累托進化，6 任務勝 GRPO 6-20%、rollouts 少 35 倍、勝 MIPROv2 10%+——同 JARVIS「多 agent 多 tool」場景最接近。
- **DSPy（2310.03714）**：prompt pipeline 當程式，teleprompter 編譯（BootstrapFewShot→COPRO→MIPROv2→GEPA 階梯）。
- **TextGrad（2406.07496）**：文字反向傳播，強模型反饋優化弱模型 prompt 有效（Object Counting 77.8→91.9%）——支持「優化行平模型、執行行主力」成本模式。
- **⚠️ 成本係最大障礙**：MIPROv2 一次 compile $50-500+、數千次 trials（The Neural Base）——**每次 dispatch 都做真優化唔現實**。
- **Viator/TripAdvisor 商業實證（2507.15884）**：APE-OPRO 混合成本效益最好，慳 18% 成本不犧牲性能。
- **Meta-prompting 名詞澄清**：Suzgun et al.（2401.12954）嘅「Meta-Prompting」= LLM 做 orchestrator + experts，**唔係**「用 LLM 優化 prompt」；Phase F 嘅證據應引 OPRO/GPO/GEPA 線。

### 「每次 dispatch 前優化」管道
- **冇人做過同名研究**——文獻係「離線優化成個 agent 系統」（ADAS、AFlow 2410.10762 MCTS 自動生成 workflow），**唔係每次任務前 inline 優化**——要當實驗性設計處理。
- Anthropic 多代理：委派描述質素係系統成敗關鍵（vague 描述→子 agent 誤解/重複），但解法係「教 orchestrator 點委派」靜態做。
- **冇 metric 嘅「優化」唔係優化**：所有有效方法依賴評分函數 + 迭代 + 驗證——淨係叫 LLM 重寫係格式化/重寫，效果唔穩定。

### Injection 風險（嚴重）
- **AdvPrompter（2404.16873）**：用另一個 LLM 生成 prompt 本身就係 jailbreak 手段——prompt optimizer 同 adversarial prompt generator 係同一種能力。
- **InjecAgent（2403.02691, ACL 2024）**：indirect injection 攻擊成功率 GPT-4 24%（hacking prompt 47%）、Llama2-70B 80%+；fine-tuned agent 7.1%——指令層級分隔越做好越安全。
- **OWASP LLM01:2025**：prompt injection = LLM 應用 #1 風險。
- **Instruction Hierarchy（2404.13208, OpenAI）**：system > user > tool/第三方資料 權限層級——低權限指令唔可以覆蓋高權限約束。
- **Sysdig 真實案例**：Cursor agent 被 indirect injection 寫入惡意 MCP config → RCE。
- **Double-hop injection**：優化器讀取嘅任務需求可能已含不可信內容（子 agent 前一個輸出）→ 污染優化器 → 污染優化後 prompt → 污染執行 agent。

### Phase F 結論（支持核心方向，大幅修改——分兩層）
1. **L1「Prompt Formatter」**（每次 dispatch 前，一次 LLM call，結構化成 目標/背景/約束/驗收標準/輸出格式 五段）——成本可控、確定性高
2. **L2「Prompt Optimizer」**（離線、只對重複性高任務跑，GEPA 式反思進化 / DSPy compile，以驗收標準自動評分，結果入 pattern 庫）
3. 可 diff + lineage 強烈支持（同時係 injection 偵測基礎）；優化輸出差異自動掃描敏感模式（權限/工具/輸出目的地/安全關鍵字），命中降級用原版
4. 安全：優化器冇工具權限、冇網絡權限（text→text）；安全約束以「不可變區塊」由系統注入（優化器無權改寫）；instruction hierarchy 標記；過 injection 偵測
5. 成本：簡單任務跳過優化器（用模板）；pattern 庫命中直接用 cached；優化行平模型
6. Pattern 庫只由「分數提升」驅動（有驗收評分先入學習 loop），唔由 LLM 自評驅動

---

## 5. 自主度分級（Earned Autonomy）——Phase D 依據

### 分級自主有 40+ 年學術傳統
- **Parasuraman, Sheridan & Wickens (2000, IEEE SMC)**：4 階段 × 10 級 LOA 框架——分級自主經典起源。
- **Parasuraman & Manzey (2010, Human Factors)**：automation complacency/bias 實證——人監控可靠自動化時偵測能力下降（審批疲勞學術根基）。
- **Levels of AGI（Morris et al., arXiv 2311.02462, DeepMind）**：6 級 Autonomy（Tool→Consultant→Collaborator→Expert→Agent），以 SAE J3016 為藍本——「L0-L3 等級」有文獻支持。
- **Digital Apprentice（arXiv 2606.04321, 2026）**：per-skill 自主狀態機（Pre-L0 觀察→L0 建議→L1 執行→L2 自治+drift check）——同 JARVIS ladder 結構幾乎一致。關鍵：**升階要求實證 + 明確人類授權事件；agent 唔可以自己升自己；降級自動且不對稱**。

### 13.6% 來源確認（審批疲勞量化實證）
- **Anthropic 2026-08 受控研究（1,053 人）**：人類審查員只捉 13.6%（143/1053）植入嘅危險命令，auto mode classifier 捉 89%；生產數據用戶批准 97% 權限提示；人類警覺隨 session 變長由 ~17% 跌到 5%（50+ 提示後）。
- **ScaleX 第三方（40,000+ 局）**：人類平均漏 1/3 威脅（準確率 66.3%）；最易漏 exfiltration/scope violation（miss 33-35%）；32.9% session 負分。
- **AmPermBench（arXiv 2604.04978）**：classifier 本身都唔完美（0.4% FP、17% FN）——sandbox 要做最後實體邊界。

### 升階閘成熟做法
- **tianpan.co Earned Autonomy（2026-04）**：按操作類型分級（唔係 agent 整體）；人類 override rate 係最直接早期預警；升階閘例 = error rate <0.5% + override <3% + 無 anomaly spike（>2σ）+ 維持 500 ops 或 30 天；⚠️ 升階實際上不可逆（demotion 傷信任）——要設自動降級。
- **Control evaluation（Korbak et al., arXiv 2504.05259, UK AISI）**：紅隊 agent 嘗試繞過控制措施嚟驗證控制措施；AI Control Levels M1-M5；safety case 結構化安全論證。
- **Automation collapse（Irving/Korbak/Hilton 2024）**：agent 越強人類監督越不可靠——最終安全邊界由 eval gate + 監控系統承擔。
- **Golden tasks**：三類 eval（golden tasks 核心能力不可退化 / failure regression 已修問題不可復發 / stress 極端情況）；golden set 要凍結、人手標註、唔可以由 model output 刷新。
- **METR**：<4 分鐘任務 ~100% 成功、>4 小時 <10%（按任務長度設自動化上限）；rogue replication 係正式威脅模型。
- **Escalation channel 實證（arXiv 2510.05192）**：保證暫停 + 獨立審查嘅 escalation channel 令有害動作率低 4×（24,000+ trials）。
- **Agentic Misalignment（arXiv 2510.05179）**：16 個主流模型喺目標衝突下會主動做 insider threat——「唔好假設 agent 唔會做」。

### 紅線強化
1. Evaluator/golden set 行 immutable 存儲（hash 驗證），變更只能經 L0 人手流程
2. Spawn 嘅 agent 只限 ephemeral、冇 persistent state、冇能力 spawn 返 spawner
3. Cost budget 含 token/API/cost 三層 + kill switch + blast radius 上限
4. Demotion 自動且不對稱（quality degrade 即自動降級，唔使人批）；降級粒度係「權限」而唔係「成級」；保留 SK 一鍵全退
5. 新增：唔俾 agent 改自己 permission policy/config；外發動作永遠人手 + sandbox 實體隔離

### Phase D 結論（整體支持，3 個修改）
1. **由 agent 整體分級改為 per-skill/per-operation 分級**：L1 內分 L1a（sandbox 內完全自動）/ L1b（低風險 apply 自動）/ L1c（高風險人手）
2. L2/L3 係同一能力（spawn + 整合驗證）兩個規模；L2 subagent 限定 ephemeral + least-privilege + 冇權 spawn 更深層 + 冇權改 evaluator/policy
3. 升階必須人類授權事件（唔可以純績效自動升級）；降級全自動

### 升階條件修訂
- **L0→L1**：golden tasks 0 regression（frozen set）+ override rate 預警 + 生產-like 環境連續 2 週 + 監控 reviewer engagement（防 complacency）+ 自動 apply 範圍限短/細 blast-radius 操作
- **L1→L2**：regression 定義喺 frozen golden set + failure regression set；子 agent 驗證 = 獨立驗證者（唔共享 prompt/model/context 弱點）+ 強制暫停 + 獨立審查
- **L2→L3**：反對單一 90%——改複合閘：(a) golden set + 代表性長任務集成功率 ≥90%；(b) 0 次紅線違反；(c) 獨立 safety case review 通過；(d) lineage 完整可 audit

---

## 完整來源清單（60+）

### Self-modification（23）
1. https://arxiv.org/abs/2404.14387 — A Survey on Self-Evolution of LLMs
2. https://arxiv.org/abs/2507.21046 — A Survey of Self-Evolving Agents（TMLR 2026）
3. https://arxiv.org/abs/2607.13104 — Self-Improvements in Modern Agentic Systems
4. https://arxiv.org/abs/2310.02304 — STOP: Recursively Self-Improving Code Generation（+ github.com/microsoft/stop）
5. https://arxiv.org/abs/2405.15793 — SWE-agent（+ github.com/SWE-agent/SWE-agent）
6. https://arxiv.org/abs/2305.16291 — Voyager（+ github.com/minedojo/voyager）
7. https://arxiv.org/abs/2303.11366 — Reflexion（+ github.com/noahshinn/reflexion）
8. https://arxiv.org/abs/2304.05128 — Self-Debug（Google DeepMind）
9. https://arxiv.org/abs/2408.08435 — ADAS（+ github.com/ShengranHu/ADAS）
10. https://arxiv.org/abs/2604.16314 — SelfEvolve
11. https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills — Agent Skills
12. https://github.com/anthropics/skills — anthropic skills repo
13. https://www.anthropic.com/engineering/claude-code-sandboxing — Claude Code sandboxing（+ github.com/anthropic-experimental/sandbox-runtime）
14. https://github.com/e2b-dev/E2B — E2B sandbox
15. https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/ — Specification gaming
16. https://arxiv.org/abs/2209.13085 — Reward Hacking（Skalse et al.）
17. https://arxiv.org/abs/2412.14093 — Alignment faking
18. https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/ — SWE-bench Verified 判死
19. https://arxiv.org/abs/2502.01534 — Preference Leakage
20. https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf — OpenAI Preparedness v2
21. https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/ — METR 時間地平線
22. https://metr.org/blog/2024-03-15-example-autonomy-evaluation-protocol/ — METR autonomy protocol
23. https://arxiv.org/abs/2605.29463 — Honest Lying（confabulation）

### Agent spawning / orchestration（25）
24. https://arxiv.org/abs/2503.13657 — MASFT（14 種失敗模式）
25. https://arxiv.org/abs/2607.01641 — IAL-Scan（infinite loops）
26. https://arxiv.org/abs/2509.26354 — Your Agent May Misevolve（ICLR 2026）
27. https://arxiv.org/abs/2308.00352 — MetaGPT
28. https://arxiv.org/abs/2308.08155 — AutoGen 原始論文
29. https://arxiv.org/abs/2402.05120 — More Agents Is All You Need
30. https://arxiv.org/abs/2508.02994 — When AIs Judge AIs
31. https://www.anthropic.com/engineering/multi-agent-research-system — Anthropic multi-agent research system
32. https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents — Anthropic harnesses
33. https://www.anthropic.com/research/multiagent-systems — Anthropic Frontier Red Team
34. https://cognition.ai/blog/dont-build-multi-agents — Cognition
35. https://claude.com/blog/subagents-in-claude-code — Claude Code subagents
36. https://openai.com/index/practices-for-governing-agentic-ai-systems — OpenAI governance
37. https://github.com/vectara/awesome-agent-failures/blob/main/docs/case-studies/langchain-a2a-47k-infinite-loop.md — $47,000 A2A post-mortem
38. https://mdsanwarhossain.me/blog-multi-agent-orchestration-failures.html — Orchestration failures
39. https://tianpan.co/blog/2026-04-12-agentic-deadlock-when-ai-agents-wait-for-each-other-forever — Agentic deadlock
40. https://github.com/openai/swarm — OpenAI Swarm（deprecated）
41. https://learn.microsoft.com/en-us/agents/architecture/multi-agent-orchestrator-sub-agent — MS orchestrator-subagent
42. https://github.com/mkassaf/ai-skills/blob/main/patterns/sub-agent-spawning.md — sub-agent-spawning pattern
43. https://github.com/microsoft/llm-as-judge — MS llm-as-judge
44. https://agentswarms.fyi/blog/why-do-multi-agent-llm-systems-fail — agentswarms.fyi
45. https://github.com/taichengguo/LLM_MultiAgents_Survey_Papers — MultiAgents survey papers
46. https://whatgenerativeai.com/docs/genai-playbook/agent-orchestration-frameworks — Orchestration frameworks 比較
47. https://github.com/agentpatterns-ai/website/blob/main/multi-agent/recursive-sub-agent-delegation-depth.md — Recursive delegation depth
48. https://arxiv.org/abs/2502.12257 — InfoQuest

### Clarification（26）
49. https://arxiv.org/abs/2512.13154 — MAC
50. https://arxiv.org/abs/2212.07769 — CLAM
51. https://arxiv.org/abs/2311.09469 — Clarify When Necessary
52. https://arxiv.org/abs/2502.04485 — Active Task Disambiguation
53. https://arxiv.org/html/2604.09408v4 — HiL-Bench
54. https://arxiv.org/abs/2412.06771 — Proactive Agents for T2I
55. https://arxiv.org/abs/2405.15784 — Clarinet
56. https://irlab.science.uva.nl/wp-content/papercite-data/pdf/zou-2020-empirical.pdf — Zou et al. clarifying questions
57. https://arxiv.org/abs/2109.12451 — Amazon Alexa SLU
58. https://www.amazon.science/blog/reducing-unnecessary-clarification-questions-from-voice-agents — Alexa blog
59. https://arxiv.org/abs/2207.05221 — Kadavath et al.（confidence calibration）
60. https://arxiv.org/abs/2509.25532 — DINCO
61. https://www.researchgate.net/publication/382633391_A_Survey_of_Confidence_Estimation_and_Calibration_in_Large_Language_Models — Confidence survey
62. https://arxiv.org/abs/2302.09664 — Semantic Entropy
63. https://www.anthropic.com/research/measuring-agent-autonomy — Anthropic measuring autonomy
64. https://www.anthropic.com/research/trustworthy-agents — Anthropic trustworthy agents
65. https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents — OpenAI practical guide
66. https://arxiv.org/abs/2210.03629 — ReAct（原論文冇確認 gate）
67. https://tianpan.co/blog/2026-05-07-ai-clarification-dialogue-convergent-flows — Convergent clarification
68. https://arxiv.org/abs/2608.21721 — RO-PnR（EMNLP 2026）
69. https://arxiv.org/html/2511.08798v2 — EVPI clarification
70. https://arxiv.org/html/2605.25284 — Knowing but Not Showing
71. https://pith.science/paper/2506.01881 — STORM
72. https://inquiringlines.com/inquiring-lines/when-should-agents-use-clarification-commands-instead-of-assuming-intent — Gravity7
73. https://vietanh.dev/blog/2026-08-08-ask-or-it-will-guess — Ask or It Will Guess
74. https://codex.danielvaughan.com/2026/07/12/dialogue-gap-interactive-coding-agents-codex-cli-dialogue-swebench-swe-together-collaborative-architecture — Dialogue-SWEBench
75. https://arxiv.org/abs/2410.19692 — AGENT-CQ

### Prompt optimization（24）
76. https://arxiv.org/abs/2211.01910 — APE
77. https://arxiv.org/abs/2309.03409 — OPRO
78. https://arxiv.org/pdf/2507.19457 — GEPA
79. https://arxiv.org/abs/2310.03714 — DSPy
80. https://arxiv.org/abs/2401.12954 — Meta-Prompting（Suzgun）
81. https://arxiv.org/abs/2406.07496 — TextGrad
82. https://arxiv.org/abs/2309.08532 — EvoPrompt
83. https://arxiv.org/html/2309.16797 — PromptBreeder
84. https://arxiv.org/html/2402.17564v3 — GPO
85. https://arxiv.org/abs/2507.15884 — Prompt Smart, Pay Less
86. https://arxiv.org/pdf/2605.18869 — MO-CAPO
87. https://arxiv.org/abs/2403.02691 — InjecAgent
88. https://arxiv.org/abs/2404.13208 — Instruction Hierarchy
89. https://arxiv.org/abs/2404.16873 — AdvPrompter
90. https://arxiv.org/abs/2410.10762 — AFlow
91. https://cameronrwolfe.substack.com/p/automatic-prompt-optimization — Wolfe 綜述
92. https://genai.owasp.org/llmrisk/llm01-prompt-injection — OWASP LLM01
93. https://www.microsoft.com/en-us/msrc/blog/2025/07/how-microsoft-defends-against-indirect-prompt-injection-attacks — MSRC IDPI
94. https://www.sysdig.com/learn-cloud-native/prompt-injection — Sysdig
95. https://www.crowdstrike.com/en-us/blog/indirect-prompt-injection-attacks-hidden-ai-risks — CrowdStrike
96. https://unit42.paloaltonetworks.com/ai-agent-prompt-injection — Unit42
97. https://theneuralbase.com/dspy/learn/intermediate/cost-of-running-miprov2 — MIPROv2 成本
98. https://futureagi.com/blog/dspy-optimizers-explained — DSPy optimizers 階梯
99. https://predli.com/blog/agentic-workflows-and-prompt-optimization — Predli
100. https://cobusgreyling.medium.com/using-ai-agents-for-prompt-optimisation-language-model-selection-4b629554af26 — Greyling
101. https://www.promptingguide.ai/techniques/ape — Prompt Engineering Guide
102. https://costlayer.ai/blog/meta-prompting-token-efficiency-ai-cost-reduction — CostLayer（廠商宣傳，證據弱）

### Earned autonomy / HITL（22）
103. https://claude.com/blog/auto-mode-default-in-claude-code — Anthropic auto mode
104. https://techcrunch.com/2026/08/09/anthropic-is-turning-claude-codes-auto-mode-on-by-default/ — TechCrunch 13.6%
105. https://hyrax.dev/blog/claude-code-auto-mode-default-august-14 — Hyrax 分析
106. https://cybersecuritynews.com/claude-code-shifts-agent-security/ — Cybersecurity News
107. https://scalex.dev/blog/ai-agent-permissions-stats/ — ScaleX 權限遊戲
108. https://arxiv.org/html/2604.04978v1 — AmPermBench
109. https://arxiv.org/abs/2606.04321 — Digital Apprentice
110. https://tianpan.co/blog/2026-04-17-earned-autonomy-ai-agents-progressive-supervision — Earned Autonomy
111. https://arxiv.org/abs/2311.02462 — Levels of AGI
112. https://arxiv.org/abs/2506.12469 — Levels of Autonomy for AI Agents
113. http://cs.uml.edu/~holly/91.550/papers/sheridan-autonomy.pdf — Parasuraman 2000
114. https://doi.org/10.1177/0018720810376055 — Parasuraman & Manzey 2010
115. https://www.sae.org/standards/content/j3016_202104/ — SAE J3016
116. https://arxiv.org/abs/2504.05259 — Control evaluation（Korbak）
117. https://www.alignmentforum.org/posts/2Gy9tfjmKwkYbF9BY/automation-collapse — Automation collapse
118. https://metr.org/measuring-autonomous-ai-capabilities/ — METR 資源頁
119. https://metr.org/blog/2024-11-12-rogue-replication-threat-model/ — METR rogue replication
120. https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/strengthening-our-frontier-safety-framework/frontier-safety-framework_3-1.pdf — DeepMind FSF 3.1
121. https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf — OpenAI guide PDF
122. https://www.anthropic.com/engineering/building-effective-agents — Anthropic effective agents
123. https://arxiv.org/abs/2510.05179 — Agentic Misalignment
124. https://doi.org/10.48550/arxiv.2510.05192 — Escalation channel
125. https://yudesk.dev/en/blog/self-improving-agent — Golden tasks
126. https://adlrocha.substack.com/p/adlrocha-the-eval-problem-how-to — Golden set 陷阱
127. https://getunblocked.com/blog/ai-coding-agent-autonomy — Autonomy 設定原則
