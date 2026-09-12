# Alert Pipeline v3（raw 字串永不出聲；講/唔講 100% deterministic；SK Q1/Q2 已定案）

> **Review record**：Round 1（09:1x）反方 **8:2**（LLM 擺 real-time 決策點 → 否決）；Round 2（13:1x）反方 **6:4**（4 個 HIGH 規格缺陷）＋ cursor review-only `NEEDS-FIX`（2 blockers）。
> **v3 = 修完上述所有缺陷之後嘅版本**，含 **SK 定案（Q1 digest 30 分鐘；Q2 開住 game 唔玩 = 唔算打機）** 同 **P0→P1 shadow→P2 enforce→P3 LLM 分階段開工**。
> v1→v2：LLM 移出 critical path（唔可以 suppress alert），講/唔講改由 deterministic policy 決定；v2→v3：critical 只用 code hard 門檻、held 要有人 release、eviction 保護 held/critical、gate 由 store 改擺 speaker 出口。

**Goal:** 玩家／SK 聽到嘅每一句 alert 都係英文短句；raw 字串（metrics、URL、中文）**永遠冇通道去到 TTS**；打機／通話時一律唔出聲；每次出聲／唔出聲都有 audit。

**Architecture（4 層，單一 speaker 路徑）**
```
producer → AlertStore.enqueue(struct: kind, phrase, detail, dedupe_key)
   ↓
[L1 shape]  kind → deterministic English template（唔識 → 用 kind policy 嘅 generic 句）
   ↓
[L2 policy] deterministic table：kind × priority → {speak_now | digest | drop}
   ↑（priority 可由 L4 LLM 提升，但**唔可以降級／suppress**）
   ↓
[L3 gate]   gaming / voice_call → hold（真正 hold 得住，見 Task 2 ttl 修正）
   ↓
[speaker]   poll_loop 單一路徑 → TTS → ack → audit log
   ↑
[L4 LLM 離線加分（非阻塞）] Hermes/DeepSeek：改寫更好英文句 + priority tag + idle digest 總結
```
**Fail 行為**：L4 死 → 用 L1 template 照講（高優先 kind）／照入 digest（低優先）；**只有「raw text 直接出聲」係絕對禁止（fail-closed）**。

---

## Review Round 1 捉到嘅 blocker（全部要喺 v2 修，反方 8:2 依據）

| # | Blocker | 證據（我親自驗） | v2 對策 |
|---|---|---|---|
| B1 | Hermes API **冇 per-request 關 tools**，triage 會變完整 agent run；SSE deadline / approval default-deny → 6s timeout 必爆 → fail-closed 全靜 | `hermes_bridge.py:757-761` body 只有 `{input, session_id, instructions}`；tools 只有全域 `hermes tools disable`（`:388-403`）；`:687` approval 無 ask_approve 即 deny | **唔用 agent run 做 triage**；L4 只係非阻塞「改寫＋tag」，用現有 LLM key 直接 chat（或 Hermes API 但**唔可以 suppress**，見 L2） |
| B2 | fail-closed ＋ 白名單太窄 = 99% traffic 靜默（whatsapp 254/258） | `serve.log` `[alert]` = 258（whatsapp 254、discord 4） | policy table 明列每 kind 預設（唔係白名單黑洞）；LLM 唔可以 suppress |
| B3 | hold 900s 會被 GC 120s 殺（無聲蒸發） | `alert_store.py:17 DEFAULT_TTL_S=120.0`、`:41 expired()`、`:215 _gc_unlocked()`、`enqueue ttl_s` 預設 120 | held row **唔准被 GC**：`expired()` 對 `state=="held"` 回 False；hold 用自己嘅 `hold_until`（TTL 15 分鐘） |
| B4 | 1s 單線程 poll ＋ 30s lease ＋ 慢 triage → redeliver → 雙重出聲 | `hermes_alert_poll_loop.py:39 peek(lease_s=max(30, interval*10))` | 出聲前先「`mark_spoken`（原子）」再 TTS；或 lease 覆蓋整個出聲窗；L4 一律非阻塞（唔阻住 loop） |
| B5 | plan 驗證係空炮（`tests/check_*.py` 唔存在） | `find` = 0 個 check_*.py；jarvis-pc tests 係 `tests/test_*.py`（30+ 個）；`tests/test_alert_store.py:61-67 test_stats` 斷言 status 只有 leased/pending | 全部測試檔用 `tests/test_*.py`；同日要改 `test_alert_store.py` |
| B6 | 改 `self_monitor.run_once()` 回傳 tuple 會爆 CLI | `self_monitor.py:300 main()` 係 `summary, notable = run_once()` | 用 `NamedTuple`／dataclass 回傳（向後兼容）＋改埋 `main()` |
| B7 | Gaming gate 要收歸一處；cron 出聲路徑冇 gate | `scripts/hermes_alert_speak_once.py:221-233 main()` 冇 gaming 檢查 | gate 收歸 `AlertStore.peek()`（唯一入口），poll loop 同 cron 都經佢 |
| B8 | dedupe／verdict cache 會誤殺真事件／永久 mute 一類 | whatsapp phrase 重複極高（`貼圖`/`K`/`😂`） | dedupe 只限 `kind=="self-monitor"`（同一 summary 5 分鐘內一次）；**唔做 verdict cache** |

## Non-goals
- ❌ 唔加 Hermes cron poll（AGENTS.md：race／double speak）
- ❌ 唔改 wake／ASR 線（08:50 false-wake ＋ sensevoice 幻聽 = 另一條 pending，等 SK 揀 ASR）
- ❌ L4 唔可以 suppress 任何 policy 話要講嘅 alert

---

## Task 1 — AlertStore 狀態機（v3：held 唔准 GC ＋ 保護 eviction ＋ **唔喺 store 做 gate**）
**Files:** Modify `src/jarvis/alert_store.py`、`tests/test_alert_store.py`
- `StoredAlert` 加 `state: str = "pending"`、`hold_until: float = 0.0`、`priority: str = "normal"`、`dedupe_key: str = ""`（⚠️ 現時**冇** `sender`／`dedupe_key` 欄，全部新加）
- `expired()`：`state in ("held","digest")` → `False`（唔准逾時蒸發）；**但 `hold_until` 已過就要轉 `digest`/`drop`**，唔可以永久豁免
- **`peek()` 保持中性（唔加 gate）** — gate 擺 speaker 出口（Task 4），保住 MCP `peek_alert`/`list_alerts` 查詢通道
- 新 `hold()` / `release_held()` / `mark_spoken()` / `mark_digest()` / `drop(reason)`：**全部行同一 `_DirLock`**（`alert_store.py:63-94`）
- `enqueue()` eviction 保護：超 `max_depth=32` 時**只可剔 `state=='pending' and priority=='normal'`**（held/critical 唔可以被丟）
- **明文 caller**：`poll_loop` 每輪讀 activity → `gaming=False` → `release_held()`
- `list_open()`／`stats()` 要識新 state，`test_alert_store.py:61-67 test_stats` 同步更新
**驗證（新）**：`tests/test_alert_store_gate.py`：held 唔會 GC；hold_until 過期→digest；32 條以上含 held/critical 時 eviction 唔可以剔佢哋；兩個 process 同時 hold+enqueue 唔會丟更新。

## Task 2 — Shaping（A）＋ self-monitor 講人話（v3：**唔開第三個表**）
**Files:** Create `src/jarvis/alert_policy.py`；Modify `src/jarvis/alerts.py:218-238`、`src/jarvis/self_monitor.py:223/296-300`、`src/jarvis/shell_app.py:550-580`
- `shape(kind, phrase, detail) -> str` **delegate 去現有** `alerts.alert_phrase_for()`／`sensors.gpu_health.gpu_health_phrase()`；`alert_policy` 只加：① self-monitor 專用英文 template ② 「純 ASCII 保證」wrapper（raw/metrics/URL/CJK 一律唔會出聲）
- self-monitor：`run_once()` 回 `MonitorResult(NamedTuple)`（`summary, notable, spoken`）＋改 `main()`（現時 `summary, notable = run_once()`）
- `shell_app._enqueue_alert` 簽名加 `detail`（現時 `(kind, phrase, *, app, log_prefix)` 冇 detail）→ passthrough 落 `AlertStore.enqueue`
**驗證**：`tests/test_alert_policy.py`：全 kind × 有／冇 detail → 出句必 ASCII、零 `=`、零 URL、零 CJK、以 `Sir,` 或大寫開頭。

## Task 3 — Policy table（由 settings derive）＋ critical class（v3：只用 code hard 門檻）
**Files:** Create（同一 `alert_policy.py`）；Modify `src/jarvis/settings.py`
- POLICY 由**現有 settings 布林** derive（`alert_voice`/`alert_discord`/`alert_cursor`/`alert_whatsapp`）→ `{speak_now | digest | drop}`；**唔另開人手維護清單**
- `CRITICAL = frozenset({"gpu_hard", "sidecar_down", "cursor_approve"})` — **只認 code hard 門檻**（`gpu_health.py:60-62` hard_temp_c=90 / mem_temp_warn_c=95）；**soft 83 唔算 critical**（打機時 GPU 長期 83-88°C，soft 每 120s fire → 只可入 digest）
- 單元測試斷言：**任何被標為 digest 嘅 kind 都唔可以出現喺 CRITICAL 集合**（config 打錯 = fail-closed，唔會靜靜降級致命警報）
**驗證**：`tests/test_alert_policy.py`（同上）＋ critical/digest 互斥斷言。

## Task 4 — Speaker 出口 gate（v3：**唔擺 store**）＋ 統一 gaming 訊號
**Files:** Create `src/jarvis/speak_gate.py`；Modify `scripts/hermes_alert_poll_loop.py:37-49`、`scripts/hermes_alert_speak_once.py:221-233`、`src/jarvis/activity.py:29-36`、`src/jarvis/gpu_policy.py:14-16`
- `should_speak(row, activity) -> SpeakPlan(action, reason)`：`speak | hold | digest | drop`；兩條出聲路徑**共用**
- 統一 `is_gaming()`：讀 `sk_activity.json` `apps[].category == "game"` ＋ **freshness（timestamp ≤ 60s）** ＋ **`idle_seconds < 120`**（SK 定案：Prism 開住唔玩 = 唔算打機）→ 同時餵 `gpu_policy.gaming_now()`（今日兩處都中同一個 foreground bug）
- `voice_call` 要用 `activity.voice_call()`（**唔可以**讀 `voice_call_state.json` — 嗰個係 monitor 內部 debounce）
- **唔加 Hermes cron**（AGENTS.md）
**驗證**：`tests/test_speak_gate.py`：用今日真實現場做 fixture（CS2+MC 行緊但前景=Discord → hold）；game 退出後 180 秒 flap 窗要有 freshness 保護。

## Task 5 — 修 lease／雙重出聲（B4）
**Files:** Modify `scripts/hermes_alert_poll_loop.py:37-49`、`scripts/hermes_alert_speak_once.py:221-233`
- `peek(lease_s=300)` → `mark_spoken(atomic)` → TTS → ack；TTS 失敗 → 釋放 lease 留待下輪
**驗證**：`tests/test_alert_poll_race.py`（mock store：慢 speak 期間再 peek → 唔會攞到同一行）。

## Task 6 — Ledger ＋「what did I miss」（v3：store 內部寫，唔做第三個 source of truth）
**Files:** Modify `src/jarvis/alert_store.py`（append）、`src/jarvis/router.py:263-276`、`src/jarvis/engine.py:271-283`
- Ledger：`%APPDATA%\Jarvis\alerts\miss_ledger.jsonl`（queue 同層、**唔可以混入 queue.jsonl**）— 由 AlertStore **內部**喺每次狀態轉變 append（enqueue/spoken/held/digest/dropped + reason code）；>2MB rotate `.1`；讀只取 24h；行同一 `_DirLock`
- Router 加明確 phrase match（`what did i miss` / `miss咗啲咩`）＋ local handler（讀 ledger）＋ **bypass Hermes**（`hermes_enabled` 時 query 會 short-circuit，`engine.py:127-136`）；**輸出前強制 ASCII**（`mouth.speak` 會靜默跳過 CJK）
**驗證**：`tests/test_miss_ledger.py`：狀態轉變都有 ledger 行；rotate；route 命中；輸出 ASCII。

## Task 7 — Settings keys ＋ clamp ＋ CI／eval_gate 同步
**Files:** Modify `src/jarvis/settings.py`（`_clamp` 一齊）、`src/jarvis/settings_ui.py`、`src/jarvis/eval_gate.py`、`.hermes/plans/self-evol-golden-set.md`
- Keys：`alert_policy_enabled="on"`、`alert_gaming="hold"`、`alert_hold_ttl_s=900`（clamp 30–3600）、`alert_digest_interval_s=1800`（clamp 300–7200）、`alert_llm_polish="off"`（Phase 3 才開）、`alert_llm_timeout_s=3.0`（clamp 1–10）
- **新 test 檔要同步 `GOLDEN_SUITES` mapping ＋ golden-set.md**，跑 `eval_gate --lock` 再 `--all`（`eval_gate.py:296-322` 會逐 basename 比對）
- CI：`py_compile src/jarvis/*.py scripts/*.py` ＋ `pytest tests/ -q`（baseline **379 passed**）＋ `eval_gate --lock`／`--all`（baseline HASH `0b88e6f6bab43269`）

## Task 8 — L4 離線 LLM（**暫緩**，等 benchmark）
- 實測 5.86s > timebox 3s → **只做 digest 總結**（刪「即時 polish」幻覺）；ranking prompt benchmark p95 ≤3s 才開工
- Fail-open：LLM 死／垃圾 JSON → template 照講（唔會靜音）；寫 `alerts\triage.jsonl`（>2MB rotate）
**驗證**：`tests/test_alert_llm.py`：正常／timeout／垃圾 JSON → 三種都必須有聲。

---

## 開工編排（v3，SK 2026-09-12 Q1／Q2 已定案）
| 階段 | 內容 | 前提 |
|---|---|---|
| **P0（即刻）** | Task 2（shaping）＋ Task 7（settings keys） — 零風險、唔掂 store、即時可測 | 無 |
| **P1（shadow 48h）** | Task 3＋4＋6 **只寫 ledger 唔出聲**；量：① 打機時 GPU **soft** 警報頻率（反方反轉條件 ≤2 次/小時）② process-based 訊號 FP 率（Prism 開住唔玩 30 分鐘，FP<5%） | P0 完成 |
| **P2（enforce）** | Task 1＋4＋5 正式 gate（講/唔講＋hold＋lease） | P1 數據達標 |
| **P3（LLM）** | Task 8（只做 digest） | ranking benchmark p95 ≤3s |

**SK 定案（2026-09-12）**
- **Q1**：digest ＝ **唔即時講**；累積，最多 **30 分鐘一句英文**；**打機一律 hold 到 idle 才講**
- **Q2**：**開住 game 唔玩 = 唔算打機**；要有 game process **＋** 近 2 分鐘有輸入活動才算
- **Q3**：L4 用 **DeepSeek**（現有 key；實測 5.86s → 只做 digest）；Hermes API 唔用於即時
- **Q4**：先做 P0，再 shadow，再 enforce

**唔做（v3 明確刪走）**：「同一 sender 15 分鐘第 2 條 → 升級」（`StoredAlert` 冇 sender 欄，要 WinRT toast 抽取先做得，列入 future）

## 業界 + Iron Man canon 參考（2026-09-12 SK 要求上網查；全部有來源）

| 系統 | 做法（重點） | 對我哋嘅意義 |
|---|---|---|
| **Apple iOS**（Focus／DND ＋ Announce Notifications） | ① 允許通知 = **你揀嘅人或 app 白名單** ＋ 定時排程；② iOS 18.2「**智能打斷與靜音**」用 Apple Intelligence 讀通知內容，只放**重要**嘅打斷——但**你明確允許／靜音嘅通知照跟用戶決定** | LLM 判斷重要係可以做，但業界做法係 **LLM 只喺「你嘅規則之內」排序**，唔可以推翻你嘅白名單 |
| **Amazon Alexa** | ① 通知 = **黃圈 + 提示音**，內容**要你問**（"Alexa, what did I miss?"）→ 讀完即存 24h；② **DND 阻通知／訊息／通話，但 alarms/timers 照響**；③ 播放音樂時**唔出提示音**（只留視覺）；④ 主動通知 **22:00–07:00 一定唔播**；⑤ DND 期間累積，關咗之後一次過補 | 「出聲」係稀有事件；**其餘靠視覺＋on-demand 查**；critical 類（alarm）永遠穿透 DND |
| **Android / Google** | Priority-only 模式：可按「人／app／alarms」過濾；**critical（系統安全）一律照出，唔可以 block**；**同一個人 15 分鐘內打第二次 → 放行**；"read notifications aloud" 會暫停於 media playback | 兩條黃金規則：**critical class 唔可以被靜音** ＋ **重複次數 = deterministic 升級訊號** |
| **小米小愛／華為音箱** | 勿擾模式 ＋ 定時開關（同 Alexa 同型） | quiet hours 係標配 |
| **Iron Man（JARVIS canon）** | ① 講嘅時機 = **你問**、**致命／安全**（"Sir, there is a potentially fatal buildup of ice occurring."）、**任務狀態**（"Test complete. Preparing to power down…"）、**來電**（"Incoming call with a blocked number, sir."）；② 其餘（Pepper 打電話／訊息）= **HUD 顯示**，或者**等到對話空檔一句過講返**（"Also, Miss Potts called. She wished to know…"）；③ 永遠簡短、"sir" 開頭；④ 你叫停就停（hold calls／mute） | JARVIS 之所以「唔煩」係因為：**佢唔會 narrate 每條通知**，只有 critical／你問／狀態先出聲；其餘入 HUD＋可以問返 |

**結論（三條設計規則，直接落地到 v2）**
1. **Critical class 永遠即時講，連打機／DND 都穿透**（= Alexa alarm／Android critical）：`gpu_temp>80`、`sidecar down`、`game crash`、`cursor needs approval`（blocking 類）。
2. **你嘅規則 override LLM**（= Apple 智能打斷與靜音）：sender／app 白名單（一定講）、黑名單（一定唔講）＝ deterministic；**LLM 只喺白名單內排先後同改寫句子**，唔可以靜音白名單嘅嘢。
3. **其餘全部入 ledger ＋ 可以問返**（= Alexa "what did I miss?" ／ JARVIS HUD）：`now / idle / log` 三條線 ＋「Jarvis, what did I miss?」英文摘要（呢個就係「想你判斷」但又唔會即時打擾嘅出口）；再加 **同一 sender 15 分鐘第 2 條 → 升級出聲**（Android repeat-caller 規則）。

## 可行性實測（2026-09-12，SK：「check can those idea work or not?」）

**✅ 可行（有現成基礎，逐項附證據）**

| 想法 | 現成基礎 | 工作量 |
|---|---|---|
| Critical class 穿透 | `sensors/gpu_health.py` 已有 soft 83 / hard 90 / mem 95°C 門檻＋NVML 輪詢；`cursor_approve` 已經係 alert kind（`alerts.py:226`） | 只需 policy table 標記 |
| 白名單／黑名單 override | `settings.py:80` 已有 `custom_models: list[str]`（list 欄位先例）＋ sidecar 單一 writer `POST /settings` | 加 2 個 list 欄位 + `_clamp` |
| Ledger ＋「what did I miss」 | `router.py:179` 已有 `Intent("query", …)` 類型；`alert_store.ack()` 會刪行（`:185-186`）→ 要新 append-only ledger 檔 | 新 ledger + 1 個 query handler |
| LLM 排序／中譯英 | `brain.py:103/114` 已有 direct DeepSeek chat（`deepseek-chat`）＋`translate_to_english_short()`（`:477`）——**唔使 Hermes API** | reuse，加一個 ranking prompt |
| 重複 sender 15 分鐘升級 | ⚠️ **修正（cursor review-only 捉到）**：`StoredAlert` **冇** `dedupe_key`（我原本講「已有」係錯）→ Task 1 要新加 | 中 |
| Shaping（raw 永不出聲） | 新 `alert_policy.py` 純函數，但 **必須 extend 現有 `alerts.alert_phrase_for(kind)`（`alerts.py:218-238`），唔可以另開平行表** | 中 |

**Round-2 cursor review-only 額外修正（2026-09-12，VERDICT: NEEDS-FIX，2 blockers）**
- **B1（MED）**：Task 1 嘅 voice-call gate 唔可以讀 `voice_call_state.json`（嗰個係 activity_monitor 內部 debounce，`activity_monitor.py:380-393`）→ 要用 `sk_activity.json` 嘅 `voice_call` ／ `activity.voice_call()`。
- **B2（MED）**：「what did I miss」唔可以假設 `Intent("query")` 就夠：`_QUERY_MARKERS`（`router.py:263-276`）冇 miss 類字眼，而且 `hermes_enabled` 時 query 會 short-circuit 去 Hermes（`engine.py:127-136`）→ 要加明確 phrase match ＋ local handler（signature `(utterance, registry) -> str`，出英文句）＋ bypass Hermes。
- **LOW**：MCP 工具名係 `list_alerts`（`mcp_alerts_http.py:357`），唔係 `list_open`；加 `state` 欄要同步更新 `list_alerts`／`stats` 嘅 filter，否則 held/digest 會被當 open。
- **FACT**：`apps[]` 有 180 秒 flap-guard（`activity_monitor.py:614-620`）→ 遊戲退出後 3 分鐘內仲算「有 game」＝ process-based gate 嘅已知 false positive 窗。
- **FACT**：`shell_app._handle_alert`（`shell_app.py:1369-1425`）已經會 prefer watcher phrase／`alert_phrase_for` 並**擋 raw CJK toast body**；`jarvis_speak`（`mcp_alerts_http.py:368-377`）本來就有 gaming/voice_call gate —— **漏 gate 嘅係 poll_loop／`_speak_hermes` 呢條路**（即係修一條路，唔係重建）。
- **Ledger 位置（cursor 建議）**：`%APPDATA%\Jarvis\alerts\miss_ledger.jsonl`（queue.jsonl 同層），append-only、>2MB 輪替、讀時只取 24h；**唔可以混入 `queue.jsonl`**（ack 會刪行、有 max_depth/TTL GC）。

**⚠️ 真 blocker（唔改就一定唔 work）—— gaming gate 訊號係錯嘅**
- `activity.py:29 gaming()` 定義 = `sk_activity.json.state == "playing"`；而 `activity_monitor.py:335 classify()` **只喺「前景視窗 = 遊戲」先算 playing**。
- **2026-09-12 10:35 實測**：CS2 ＋ MC 兩個都行緊，但前景係 Discord → json = `state:"using"`, `game:"counter-strike 2"`, `apps:[{cs2,game},{minecraft,game}]` → **`gaming()` 回 False**。
- 後果：① 打機唔講呢條規則**間歇失效**；② 亦解釋咗「打機都聽到 JARVIS 講嘢」（poller 本身冇 gate，加 gate 都要個 signal 啱先得）。
- **修法（可行，訊號已存在）**：gate 改用 process-based 訊號 — `apps[].category == "game"`（或 `game` 欄位非空）＋ freshness；唔用 foreground state。
- ⚠️ 要 SK 定義：**開住 Prism／MC 但唔玩**算唔算「打機」（影響誤判）。

**⚠️ LLM 實測 5.86s → 唔可以放喺即時出聲路徑**
- `translate_to_english_short("<真實 whatsapp alert>")` 實測 **5.86s**（deepseek-chat，已含 import），輸出正常英文句。
- → 印證 Round-1 反方：LLM 只可以做 **async 加分**（改寫／排序／digest），即時出聲要靠 template；`alert_llm_timeout_s=3.0` timebox 內唔回就用 template 照講。

**🟡 未證（要再實測）**
1. Ranking prompt（而唔係 translation）嘅實際 latency／成本 → 開工前跑 10 條 batched benchmark。
2. 「what did I miss」經 router → 摘要 → TTS 嘅完整鏈路（query intent 類型存在，handler 要新寫）。
3. Process-based gaming 訊號嘅誤判率（SK 開 Prism 但唔玩）→ 要 SK 定門檻。

## Review Round 2 — 中立裁判裁決（2026-09-12）+ v3 必須修正

**比數：反方贏 6:4**（Round 1 係 8:2）——今輪雙方**同意核心方向**（deterministic policy ＋ critical class ＋ 單一 speaker gate ＋ held 唔准 GC ＋ `mark_spoken` 原子），分歧只在**Task 1 規格完整性**同**次序**。反方 4 個 HIGH 全部 code-verified，係真 defect（唔係口味）；正方亦證實 baseline 健康（379 passed / eval_gate HASH `0b88e6f6bab43269`）。

**🔴 開工前必須修（v3 REQUIRED）**
1. **Critical class 定義要跟 code 門檻**：`gpu_health` soft=83°C 每 120s 會 fire（`gpu_health.py:60-63`，打機時 GPU 長期 83-88°C）→ 若照我原本寫「>80 穿透」＝**打機 spam bomb**。→ 只有 **hard（temp≥90 / mem≥95）同 `cursor_approve` 穿透**；**soft 83 打機時入 digest**。
2. **Held → pending 嘅 release 觸發要明寫**：而家 plan 令 `expired()` 對 held 回 False（唔准 GC）但 `peek()` 只回 `pending` → 冇任何 caller 轉返 pending ＝ **永久黑洞**（全 repo grep `release_held` = 0 定義 0 caller）。→ poll_loop 每輪讀 activity：`gaming=False` → `release_held()`；且 `hold_until` 過期要轉 digest/drop，唔可以永久豁免 GC。
3. **`enqueue()` max_depth eviction 要保護 held/critical**：`alert_store.py:141-148` 超 `max_depth=32` 會刪最舊非 acked 行 → held/critical 會被當垃圾丟 ＝ 打破「critical 唔可以被靜音」承諾。→ eviction 只可剔 `state=='pending' and priority=='normal'`，並加單元測試。
4. **Gate 唔好擺 `AlertStore.peek()`**：`peek()` 係 8765 MCP `peek_alert` 同 cron 共用入口 → gate 擺入去＝打機時連查都查唔到。→ gate 擺 **speaker 出口**（`poll_loop` / `speak_once` 共用一個 `should_speak(row) -> SpeakPlan` helper），store 保持中性，**單一 speaker 仍然成立**。

**🟠 其他要一併處理（MED）**
- **Gaming 訊號**：`apps[]` 有 **180 秒 flap-guard**（`activity_monitor.py:614-620`）＋同前景無關 → gate 要加 **freshness（timestamp ≤ N 秒）**；並且**要同 `gpu_policy.gaming_now()` 共用同一個 `is_gaming()`**（否則兩處各自定義會漂移 —— 今日已經中同一個 bug）。
- **「同 sender 15 分鐘升級」做唔到**：`StoredAlert` **冇 sender 欄**（只有 id/kind/phrase/app/detail/ts/ttl_s/status/lease_until）＋ whatsapp phrase 重複極高 → **Phase 1 刪走呢條規則**，唔好當已解；要就要先抽取 WinRT toast sender。
- **Ledger 唔可以變第三個 source of truth**：由 **AlertStore 內部**喺每次狀態轉變（enqueue/spoken/held/digest/dropped）append 單一 append-only `miss_ledger.jsonl`；「what did I miss」只讀 ledger；HUD 二選一。
- **POLICY 表唔好變第三個 hardcode**：`shape()` 要 **delegate 去 `alerts.alert_phrase_for()` / `gpu_health_phrase()`**，policy 由 **settings 欄位 derive**（已有 `alert_voice/alert_discord/alert_cursor/alert_whatsapp` 布林），唯一新增嘅係「純 ASCII 保證」。
- **L4 對即時態零價值**：實測 5.86s > timebox 3s → polish 到達時已經講完。→ **Task 4 只做 digest（坦承），刪「即時 polish」幻覺**；Task 4 暫緩至 benchmark 完。
- **eval_gate 同步**：新增 test 檔要同步 `GOLDEN_SUITES` mapping ＋ `.hermes/plans/self-evol-golden-set.md`，跑 `--lock` 唔止 `--all`（`eval_gate.py:296-322` doc↔mapping 逐 basename 比對）。
- **鎖**：新 writer（hold/mark_spoken/release_held）一律行同一 `_DirLock`（`alert_store.py:63-94`）＋補多 writer 並發測試。
- **「what did I miss」**：`_QUERY_MARKERS`（`router.py:263-276`）冇 miss 字眼＋`hermes_enabled` 時 query short-circuit 去 Hermes（`engine.py:127-136`）→ 加明確 phrase match ＋ local handler ＋ bypass；**輸出前強制 ASCII**（`mouth.speak` 會靜默跳過 CJK）。
- **`_enqueue_alert` 簽名**：現時 `(kind, phrase, *, app, log_prefix)` **冇 `detail`**（`shell_app.py:550`）→ Task 2 要一齊改。

**✅ 開工範圍（v3 定案建議，＝雙方共識交集）**
- **即做（零風險、唔掂 store、可即測）**：Task 2 `shape()` 純函數（extend `alert_phrase_for`）＋ Task 5 settings 欄位／clamp。
- **等 2 個實測**：① 打機時 GPU**軟**警報實際頻率（反方反轉條件：1 小時 ≤2 次）；② process-based 訊號 FP 率（Prism 開住唔玩 30 分鐘，FP<5%）→ **shadow mode 先做**：新 policy 只寫 ledger 唔出聲 48 小時，對比實際出聲集合，攞真數據才 enforce。
- **等 SK 定義 2 樣**：Q1 digest 定義（30 分鐘一句 vs 即時）；Q2「開住 game 唔玩」算唔算打機。
- **Task 4（LLM）** 等 ranking prompt benchmark（p95 ≤3s 才上）。
- **反轉條件（一觸即停）**：改到 `hud/`／`hermes_bridge.py`／要新 port 新 cron；或 379 baseline 有 regression。

## Review Round 1 — 完整記錄（三階段）
- **Stage 1 反方（最強反）**：否決 v1 Task 5／Task 2 實作；8 條 HIGH（B1-B8 上表）全部有 file:line。
- **Stage 2 正方（最強支持）**：認為 v1 嘅方向係結構性（刪通道，唔係叫模型自律）＋同 `clarify_gate`、`jarvis_speak` 既有 gate 一致；但**同意 v1 嘅 Hermes API 前提要驗**。
- **Stage 3 中立裁判**：**反方 8:2**。原因：反方 HIGH 全部係 code-verified blocker（唔係口味），照 v1 落會即日壞；正方勝在認清問題層次（要刪通道），故保留其目標、換 placement。
- **最大未知**：L4（LLM 改寫）實際延遲／質量；如果 background polish 慢過出聲，L4 價值就只剩 digest。
- **反轉條件**：如果 Hermes API 證實可以 per-request tools-off 且 p95 < 2s（實測），而 SK 接受「LLM 可 suppress」，v1 式設計可以重評。
