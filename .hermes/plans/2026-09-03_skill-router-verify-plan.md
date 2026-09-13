# Skill 揀選驗證層 Plan（skill-router-verify plugin）

> 2026-09-03 · 源頭：抖音條片「Agent 重大線上事故——問天氣查數據庫」三層方案（工具治理/調用編排/安全成本）套落 Hermes skill 層。
> **SK 指令：「跟條片方案再進一步」**＝唔止做 skill 整合（工具治理第一步），仲研究/落地「skill 揀選驗證」（條片核心：淨靠 LLM 揀 tool 冇驗證 → 選錯係常態）。

---

## 背景：條片 vs Hermes 現況

| 條片三層方案 | Hermes skill 現況 | Gap |
|---|---|---|
| 工具註冊中心統一管理 | `<available_skills>` index（name+description 全入 prompt）+ `.skills_prompt_snapshot.json` 快取 | 有 index，但**冇獨立 router／驗證**：`skill_view` 由 LLM 自己揀，揀錯冇人攔 |
| 「分類器 + 大模型」雙重驗證 | **冇**——單靠 LLM 睇 description（skill 層同款「問天氣 call 查數據庫」事故） | **呢個 plan 填嘅位** |
| 參數 JSON Schema 驗證 | skill_view 只收 `name`（冇參數風險） | 不適用（skill 冇複雜參數） |
| 返回結果結構化解析 | skill_view 回 markdown body | 不適用 |
| 調用編排（死循環/超時） | Hermes 已有 stall guard（重複 call 防護） | 已 cover |
| 全鏈路可觀測 | **冇** skill 揀選 log（邊次揀咗邊個、事後啱唔啱） | 呢個 plan 一併填 |
| 成本管控 | skill index snapshot 已控制 prompt 成本 | 已 cover |

**研究結論（source 證據，2026-09-03）：**
- Hermes skill 揀選 = `agent/prompt_builder.py::_build_skills_system_prompt_inner` 將全部 skill 的 name+description 入 system prompt → LLM 自己 call `skill_view(name)`。無任何 pre-load 驗證 component。
- `learn_prompt.py:98` 明文禁寫 router/index/hub **skill**（system prompt 已有 index，router skill 只會加噪音）——所以驗證層**唔可以係 skill**，要放 plugin／tool 層。
- **Hermes 有 plugin hook 系統**（`hermes_cli/plugins.py` + docs）：`ctx.register_hook("pre_tool_call", cb)` 可對任何 tool call 回 `{"action":"block","message":...}`（message 變成 tool result 畀 model 睇）或 `{"action":"modify","args":...}`（改 args）。`pre_llm_call` hook 攞到當前 `user_message`（docs 範例 memory plugin 確認）——即 classifier 嘅 task context 有來源。
- User plugins 放 `~/.hermes/plugins/<name>/`（`plugin.yaml` + `__init__.py::register(ctx)`），gated by `plugins.enabled`（config 改動 → Ask first）。
- Plugin 注入 context 係加喺 **user message** 而唔係 system prompt（docs 明言：preserve prompt caching）——加驗證層唔會破壞 prompt cache 不變式。

---

## 方案：`skill-router-verify` Hermes plugin（兩層）

一個 user plugin，兩條 hook，全部**本機零 LLM cost**（keyword classifier，128 skills index 預載入 memory）：

### Layer 1 — 可觀測（observer，必做，低風險）
`post_tool_call` hook 攔 `skill_view` → append JSONL 記錄：
```
{ts, session_id, skill_viewed, task_snippet(first 120 chars of latest user msg), turn_id}
```
→ `~/.hermes/logs/skill_selection.log.jsonl`
**用途**：事後統計「邊啲 skill 成日 load、邊啲 load 完冇下文（揀錯信號）、邊啲 task 對邊個 skill」。呢個就係條片「全鏈路可觀測」→ 數據驅動 tune description。

### Layer 2 — 揀選驗證（classifier + 大模型雙重驗證嘅「分類器」腳）
`pre_tool_call` hook 攔 `skill_view(name=X)`：
1. 攞最近 user message（module-level 由 `pre_llm_call` hook 快取 latest user_message + session_id）。
2. Classifier：將 task text 同全部 skill 的 name+category+description keyword 做輕量 match（預載 index，TF 式 scoring，<5ms）。
3. 決策：
   - `X` 喺 classifier top-3 內 → **放行**。
   - `X` 唔喺 top-3 且 top-1 score 顯著高 → `{"action":"block","message":"[skill-router] Task 似係 '<top1 skill>（score..）' 範疇；你 call 嘅 '<X>' 唔 match。考慮 skill_view('<top1>') 或 skills_list 再確認。"}`
   - 其他（低信心／X 喺 top-5）→ 放行（fail-open，唔阻正常 flow）。
4. **Fail-open 原則**：block 只喺「明顯唔 match」先發生；classifier 自己出錯／index 讀唔到 → 一律放行。block message 只係提示，model 可以喺下一 turn 解釋點解佢啱然後再 call（唔會無限 block：同一 turn 內重複 block 會 throttle——跟 Hermes stall guard 精神）。

**點解咁設計：**
- 唔改 core（Hermes AGENTS.md：core 係 narrow waist，capability 喺 edge——plugin 正路）。
- 唔係 router skill（learn_prompt 禁令唔違反；plugin 唔係 skill）。
- 唔破壞 prompt caching（只 pre_tool_call block／observer，唔郁 system prompt）。
- Classifier 唔 call LLM（零成本、零 latency）；「大模型」嗰層就係現有嘅主 agent——即係條片講嘅「分類器+大模型雙重驗證」完整落地。

---

## 執行步驟（按 review 裁決修訂——先治本後治標，Layer 2 延後）

**裁決（adversarial review 2026-09-03）：先做 integration（root cause）+ Layer 1 observer（數據），Layer 2 真 block 延後——要數據證明先開。**
理由：skill load 錯成本低（load 錯 = 浪費一次 tool call，唔似 tool 執行錯會做錯嘢）；而家 skills 重疊先係揀錯主因（integration 未做）；keyword classifier 對中文 task + 英文 description 嘅準度未驗證。

1. **Phase A（治本）**：執行 `2026-09-02_203000-skills-consolidation-plan.md`（A1-A5 整合——description 唔重疊、trigger 清）——root cause fix。
2. **Phase B（治標+數據）**：寫 `skill-router-verify` plugin **淨 Layer 1**（observer only：`post_tool_call` 記 JSONL）：
   - `~/.hermes/plugins/skill-router-verify/`（plugin.yaml + __init__.py）
   - Observer 同時喺 log 記「would-block」事件（模擬 Layer 2 決策，但唔 block）——收集 classifier 準度數據
   - `hermes plugins doctor . --ci` 驗證
   - Enable plugin（config 改動 → **Ask first**）
3. **Phase C（觀察）**：一週真實使用 → 分析 skill_selection log：
   - Would-block 率 <5% → Layer 2 唔使做（model 本身揀得準，整合已夠）
   - Would-block 率 >15% 且 classifier 判斷正確 → 先開 Layer 2 log-only 再 tune threshold
4. **Phase D（可選）**：Layer 2 真 block（要 would-block 數據證明有需要先做）

## 驗收標準

- [ ] Phase A：skills 128 → ~115（A1-A5 完成，merge 前 diff 冇 lose content）
- [ ] Phase B：`hermes plugins doctor . --ci` 過（0 error）；plugin enable 後 Layer 1 JSONL append 正常
- [ ] Phase C：一週 log 有得分析（would-block 率報告出嚟）
- [ ] Layer 2（如有）實測：明顯揀錯 skill → block message 出現；正常 task → 0 誤 block
- [ ] Prompt caching 不受影響（plugin 唔改 system prompt）
- [ ] 冇 SK 未批准改動（enable plugin 前問）

## Risks

- R0. **pre_tool_call timeout = fail-closed block**（source：`plugins.py:443` `_HOOK_TIMEOUT_FAIL_CLOSED_HOOKS={"pre_tool_call"}`；callback timeout 預設 30s）——如果 classifier callback 太慢／hang，會 block 晒所有 tool call 而唔係只係 skill_view。緩解：classifier 純 memory index（啟動時 load 一次，之後零 disk I/O），target <5ms；callback 內 try/except 包晒，任何 exception → return None（放行）。寫 plugin 後用 `plugins doctor` + 實測 latency。
- R1. **False-positive block 阻正常 flow**（最大風險）：threshold 太鬆 → 成日 block → agent 慢／煩。緩解：fail-open + top-1 顯著才 block + 一週實測數據先 tune；block message 設計成「提示」而唔係「禁止」（model 可反駁）。
- R2. **Plugin 同 Hermes 升級相容**：plugin API 有行為相容保證（docs：evolve additively；hook payload keyword-based；callback 收 `**kwargs`）——寫 code 時 callback 一律 `**kwargs`，跟 docs 範例。
- R3. **User message tracking 喺 gateway 多 session 混淆**：`pre_llm_call` 快取要以 `(session_id)` key 分開（Discord 同時多 session 時唔好 cross-contaminate）。
- R4. **「最近 user message」可能唔係 task context**（例如 user 講緊舊嘢，model 做緊新 sub-task）——所以 classifier 只做「明顯唔 match」先 block，寧願漏報唔好誤報。
- R5. Plugin 係新 code——按 SK 規則：裝任何新嘢前 online review（呢個係自家寫嘅 plugin，唔係第三方——但 code 質素要過 review）。
- R6. **Background/self-evol 嘅 skill_view 會被攔**（background_review 都會 call skill_view）——無 user_message 快取時一律放行（fail-open），唔好攔 background flow。

## Open Questions（SK 拍板）

1. **Phase A（skills 整合）同 Phase B（plugin Layer 1）一齊做定分開？** 裁決建議：**A 先**（治本，已 planned 只差執行）；B 可以同步開寫（plugin 唔依賴整合完成——observer 對 128 定 115 skills 都 work）。要唔要而家就開 A1/A4/A5（低風險組）？
2. **Layer 1 log 放邊？** 預設 `~/.hermes/logs/skill_selection.log.jsonl`（跟 Hermes logs 慣例）——OK？
3. **Enable plugin 嘅時機**：Phase B 寫完 + doctor 過 → 問你 enable（config 改動 Ask first）——定係你想先睇 plugin code 再決定？

## 檔案位置
- Plan: 本檔（jarvis-pc plans 目錄，跟隨之前 skills-consolidation plan 慣例）
- Plugin 開發參考：docs `https://hermes-agent.nousresearch.com/docs/developer-guide/plugins`（calculator 範例完整）
