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

## Task 0（P0）— `alert_policy.py` 純函數（**零接線**）
**Files:** Create `src/jarvis/alert_policy.py`；Create `tests/test_alert_policy.py`
- `shape(kind, phrase, app_label="") -> str`：**delegate** `alerts.alert_phrase_for()`（已知 kind）＋ self-monitor／test／bare `extra` 三個**新增** template；**永不回傳 raw**
- `is_speakable(text) -> bool` / `sanitize(text) -> str`：純 ASCII 保證（**禁** `=`、URL、CJK、非 ASCII）；唔過 → caller 拒講
- **唔改任何現有句子**、唔 import store／唔讀 settings（純函數，可即測）
**驗證**：`pytest tests/test_alert_policy.py -q`：全 kind × 有／無 detail → ASCII、零 `=`、零 URL、零 CJK。

## Task 1（P0）— Settings keys ＋ clamp ＋ golden 同步
**Files:** Modify `src/jarvis/settings.py`、`src/jarvis/settings_ui.py`、`src/jarvis/eval_gate.py`、`.hermes/plans/self-evol-golden-set.md`
- **`alert_policy_mode = "off" | "shadow" | "enforce"`（默認 `off`）**、`alert_gaming="hold"`、`alert_hold_ttl_s=900`（clamp 30–3600）、`alert_held_cap=64`（clamp 8–256）、`alert_digest_interval_s=1800`（clamp 300–7200）、`alert_digest_ttl_s=86400`、`alert_dedupe_window_s=300`、`alert_llm_polish="off"`、`alert_llm_timeout_s=3.0`
- 新 test 檔要同步 `GOLDEN_SUITES` ＋ golden-set doc（`eval_gate.py:296-322`），跑 `--lock` 再 `--all`
- **默認全部保守（off）** → 零行為改動
**驗證**：`tests/test_settings_alert_keys.py`（亂值 clamp；`alert_policy_mode` 非法值 → fallback `off`）。

## Task 2（P2）— AlertStore 狀態機（**store 純資料，唔讀 settings**）
**Files:** Modify `src/jarvis/alert_store.py`、`tests/test_alert_store.py`
- `StoredAlert` 加 `state`（`pending|held|digest|spoken|dropped`）、`hold_until`、`priority`、`dedupe_key`
- **`peek()` 只回 `state=='pending'`**（中性，唔做 gate）；`hold(row_id)` **必須即時釋放 lease**（否則最舊 held 每 1s 被 re-lease → critical 飢餓）
- `hold()` / `release_held()` / `mark_spoken()` / `mark_digest()` / `drop(reason)`：全部行同一 `_DirLock`；**ledger append 一定 fail-open**（try/except + rate-limited `[warn]`，絕不影響 queue）
- `expired()`：`held`／`digest` 唔准逾時蒸發，但 **`hold_until` 過期 → 轉 digest**；**digest TTL 24h → `drop(reason='digest_expired')`**
- **eviction**：只剔 `state=='pending' and priority=='normal'`；**要有 escape 唔可以揸住鎖空轉**；**held 硬上限 64**（同 `kind+app` 只留最新；normal 超額即轉 digest）
- `enqueue(..., priority=...)` 由 **caller 傳**；**policy 以參數注入**（`AlertStore(policy=...)`）→ 測試唔會跟你當日 settings 漂移
- `dedupe_key` **要真 enforce**（`kind+dedupe_key+window` 重複 → digest／`drop(reason='dedupe')`），唔可以留死欄位
- `list_open()`／`stats()` 要識新 state；`test_alert_store.py:61-67` 同步
**驗證**：`tests/test_alert_store_gate.py`：held 唔會再被 peek；hold 唔會 ack；critical 唔排喺 held 後；32+ 條含 held/critical 時 eviction 唔剔佢哋；打機 3 小時模擬後 **queue 長度有界**；ledger 不可寫時 enqueue/peek 照常；dedupe 生效。

## Task 3（P1）— Policy table ＋ CRITICAL（＋ `gpu_hard` 結構化 flag）
**Files:** Modify `src/jarvis/sensors/gpu_health.py`（加 explicit hard flag／kind）、`src/jarvis/alert_policy.py`、`src/jarvis/settings.py`
- **先決條件**：`GpuHealthHit.kind` 今日永遠係 `"gpu_health"`（`gpu_health.py:114-131,173-184`），hard/soft 只藏喺 `detail` → **要加結構化 flag**（例如 `hit.is_hard` 或 `kind="gpu_hard"`），否則「只有 hard 穿透」做唔到
- POLICY 由現有 settings 布林 derive（`alert_voice/discord/cursor/whatsapp`，`settings.py:112-121`）
- `CRITICAL = {"gpu_hard", "sidecar_down", "cursor_approve"}`；**soft 83 唔穿透**（打機時入 digest）
- 測試斷言：**digest kind 唔可以出現喺 CRITICAL 集合**
**驗證**：`tests/test_alert_policy.py` ＋ `tests/test_gpu_health.py`（hard/soft flag 分流）。

## Task 4（P1 shadow／P2 enforce）— Speak gate ＋ `is_gaming_v2()`
**Files:** Create `src/jarvis/speak_gate.py`；Modify `scripts/hermes_alert_poll_loop.py`、`scripts/hermes_alert_speak_once.py`
- `should_speak(row, activity) -> SpeakPlan(action, reason)`：`speak | hold | digest | drop`；**兩條出聲路共用**
- **另開 `is_gaming_v2()`**（**唔改** `activity.gaming()` — 佢同時餵 `ear.py:36-38 should_stt_use_gpu()` 同 `mcp_alerts_http.py:374 jarvis_speak` gate；P1 只 v2 寫 shadow，P2 才逐個 consumer 切換＋驗）
- v2 規則：**有 game process AND（前景=game OR fullscreen OR idle<120）**；**freshness 窗 180s**（cron 係 1 分鐘寫一次）；**release 要連續 non-gaming ≥180s**（防 flap）
- `voice_call` hold **要有自己 release 條件**（`not gaming AND not voice_call`）
- **hold verdict 一定要 `hold(row.id)` + 釋放 lease + continue**（唔可以就地 ack，否則 critical 被靜音）
**驗證**：`tests/test_speak_gate.py`：今日真實 fixture（CS2+MC 行緊、前景=Discord → hold）；`voice_call=True, gaming=False → 唔 release`；flap 窗；gamepad 實測（見下）。

## Task 5（P2）— **Speaker choke point（raw 字串真正封死）**
**Files:** Modify `scripts/hermes_alert_poll_loop.py:41`、`scripts/hermes_alert_speak_once.py:228`
- `_speak_hermes()` 之前**必經** `alert_policy.is_speakable()`；唔過 → **拒講** ＋ ledger `drop(reason='non_ascii')`
- 理由：舊 queue 行、MCP `jarvis_alert(phrase)`（Hermes 自由填字）、`cursor_hook_alert.py:151` 直入 store 嘅字，全部會原句出聲，而 `alert_tts='hermes'` 路徑**冇 CJK 檢查**（只有 `mouth.py:304` Piper 有）
**驗證**：`tests/test_alert_speaker_choke.py`：直接 enqueue CJK／URL／`=` 行 → 斷言唔會到 TTS 且 ledger 有 drop 記錄。

## Task 6（P1）— Shadow mode（量數據，零執行改動）
**Files:** Modify `src/jarvis/speak_gate.py`；Create `tests/test_alert_shadow.py`
- `alert_policy_mode=="shadow"`：speak_gate 計完 SpeakPlan → append **`%APPDATA%\Jarvis\alerts\shadow_ledger.jsonl`**（`row.id / decision / would_be_action / reason / ts`）→ **照用今日行為出聲**（enforce 唔生效）
- 量度：**M1** 打機時 GPU soft 警報頻率（目標 ≤2 次/小時）；**M2/M3** `is_gaming_v2()` FP 率（Prism 開住唔玩 30 分鐘，目標 <5%）
**驗證**：測試斷言 shadow 期間執行路徑不變；shadow ledger 有行；`mode` 非法 → `off`。

## Task 7（P2）— Ledger ＋「what did I miss」
**Files:** Modify `src/jarvis/alert_store.py`（append）、`src/jarvis/router.py:263-276`、`src/jarvis/engine.py`（**hook 喺 `execute_utterance` line 121-126 之間，即 Hermes short-circuit `:127` 之前**，唔係 `_dispatch_intent:271`）
- Ledger：`%APPDATA%\Jarvis\alerts\miss_ledger.jsonl`（queue 同層）由 AlertStore **內部**喺每次狀態轉變 append（enqueue／spoken／held／digest／dropped + reason code）；>2MB rotate `.1`；讀只取 24h；**fail-open**
- Router：加明確 phrase match（`what did i miss` / `miss咗啲咩`）＋ local handler（讀 ledger）＋ **bypass Hermes**；**輸出前強制 ASCII**
**驗證**：`tests/test_miss_ledger.py`：每次狀態轉變都有行；rotate；route 命中；輸出 ASCII。

## Task 8（P2）— Digest flush（**明文 owner**，消滅黑洞）
**Files:** Modify `scripts/hermes_alert_poll_loop.py`、Create `tests/test_alert_digest_flush.py`
- **owner = poll_loop**：每 `alert_digest_interval_s`（默認 1800s）**或** gaming→idle 轉換時：讀 `state=='digest'` 行 → **一句英文（唔靠 LLM）**＝每 kind 一句 template ＋ 總數（例：`"Sir, 3 messages and 2 GPU notices while you were away."`）→ `mark_spoken` ＋ ack **全部**
- **release 收斂**：每次只放 critical ＋ **最新一條** normal，其餘交 digest flush（唔可以 20+ 條連續講 40–120 秒）
- `last_digest_ts` **持久化落 state 檔**（同一 `_DirLock`；sidecar restart ~90s 唔會重覆／漏）
**驗證**：`tests/test_alert_digest_flush.py`：打機 3 小時模擬 → queue 有界、digest 一行出、無 zombie；restart 後唔會重覆 digest。

## Task 9（P2）— Lease／雙重出聲
**Files:** Modify `scripts/hermes_alert_poll_loop.py:37-49`、`scripts/hermes_alert_speak_once.py:221-233`
- `peek(lease_s=300)` → `mark_spoken`（原子）→ TTS → ack；TTS 失敗 → 釋放 lease 留待下輪
**驗證**：`tests/test_alert_poll_race.py`（慢 speak 期間再 peek → 唔會攞到同一行）。

## Task 10（P3，暫緩）— L4 LLM（只做 digest polish）
- 實測 5.86s > timebox 3s → **只做 digest 句子潤飾**（唔做即時）；ranking prompt benchmark **p95 ≤3s** 才開工
- Fail-open：LLM 死／垃圾 JSON → template 照講；寫 `alerts\triage.jsonl`（>2MB rotate）
**驗證**：`tests/test_alert_llm.py`：正常／timeout／垃圾 JSON → 三種都必須有聲。

## Task 11 — Docs ＋ baseline
- `docs/hermes_alerts_mcp.md` 加 pipeline 圖＋「raw 字串幾時都唔准出聲」；AGENTS.md 一句；handoff 更新
- Baseline：改完後 **新 pytest 總數（>379）** ＋ **新 eval_gate hash**（`0b88e6f6bab43269` 失效）＋ `--lock` 一致 → 三者全綠
- Repo root 殘留（`_staging/`、`_tmp_test_write.txt`、`nonexistent/`、`_compile_check2.py`、`_apply_and_compile.bat`）→ **問 SK 先清**

---

## 開工編排（v4，SK 2026-09-12 Q1／Q2 已定案）
| 階段 | 內容 | 通關條件 |
|---|---|---|
| **P0（即刻）** | Task 0（純函數）＋ Task 1（settings keys 默認 **off** ＋ golden 同步） — **唔接線、唔改任何現有句子** | 新 test 綠；379 baseline 零 regression；`--lock` 一致 |
| **P1（shadow）** | Task 3（＋`gpu_hard` flag）＋ Task 4（**只 v2 寫 shadow**）＋ Task 6（shadow ledger，零執行改動） | **shadow ledger ≥48h 樣本**；**M1** 打機時 GPU soft ≤2 次/小時；**M3** Prism 開住唔玩 30 分鐘 FP <5%；SK 手制實測 idle |
| **P2（enforce）** | Task 2＋4（enforce）＋5（choke point）＋7＋8＋9 | P1 全達標；enforce 後真機驗（打機／通話／idle 三情境） |
| **P3（LLM）** | Task 10（只做 digest polish） | ranking benchmark p95 ≤3s |
| **P4（future）** | WinRT toast sender 抽取 ＋ per-sender 白名單（＝真正做到「按邊個發」嘅重要性） | 未排 |

**SK 定案（2026-09-12）**
- **Q1**：digest ＝ **唔即時講**；累積，最多 **30 分鐘一句英文**；**打機一律 hold 到 idle 才講**
- **Q2**：**開住 game 唔玩 = 唔算打機**；要有 game process **＋** 近 2 分鐘有輸入活動才算
- **Q3**：L4 用 **DeepSeek**（現有 key；實測 5.86s → 只做 digest）；Hermes API 唔用於即時
- **Q4**：先做 P0，再 shadow，再 enforce

**唔做（v3 明確刪走）**：「同一 sender 15 分鐘第 2 條 → 升級」（`StoredAlert` 冇 sender 欄，要 WinRT toast 抽取先做得，列入 future）

## Review Round 3 — cursor review-only 裁決（2026-09-12）+ v3.1 修正

**VERDICT: NEEDS-FIX（1 個 P0 blocker）** — 全部 file:line 已驗。

**🔴 P0 blocker：Task 2 唔係「零行為改動」**
- 我 plan 話 P0「零風險、唔改變你聽到嘅嘢」係**錯**：`shell_app.py:577-578` 一改 enqueue `spoken` 英文句，self-monitor 條 metrics 就**即刻唔再讀**（＝正是今次想修嘅嘢）。
- **修法**：拆做 **P0a（真零改動）**＝新建 `alert_policy.py`（純函數）＋ Task 7 settings keys ＋ 測試，**唔接線**；**P0b（即刻見效）**＝接 self-monitor 出聲句（＝修好你聽到「numbers + =」嗰單），有明確 acceptance。
- 誠實講：P0b **係**有行為改動，但改嘅係你今日投訴嗰句，所以係 fix 唔係風險。

**🔴 非 P0 但必須修（Task 3 前提）**：`gpu_health` 今日**冇** hard/soft 之分 —— `GpuHealthHit.kind` 永遠係 `"gpu_health"`，hard/soft 只藏在 `detail`／reason（`gpu_health.py:114-131,173-184`）。→ Task 3 要先加結構化 flag／新 kind（例如 `gpu_hard`），**唔可以今日就 key kind 字串**。

**🟠 其他**
- **Task 6 hook 位置寫錯**：要掛在 `execute_utterance` **line 121-126 之間**（Hermes short-circuit `:127` 之前）；`_dispatch_intent:271` 在 Hermes 開住時根本唔會行到。
- **Held 無上限**（cursor 指出係 deadlock-class 風險）：eviction 保護 held/critical 之後，如果冇 eligible victim，`while` 迴圈可能**揸住 `_DirLock` 空轉** → 全部 alert 操作停擺。→ Task 1 要**明文上限**（held 硬上限，例如 64；超出 → 最舊 held 轉 digest／drop）＋ 迴圈一定要有 escape。
- **冇 template 嘅 kind**：`self-monitor`（正是今次主角）、`test`、bare `extra` → Task 2 要明確覆蓋。
- **確認 Task 2 係真新邏輯**（唔係薄 wrapper）：今日 `mouth.py:35-40,304-305` **只跳 CJK**，`=`／URL／非 ASCII 一樣照讀 → 所以「純 ASCII 保證」係新 code（亦證實 bug 面）。
- **OK 確認**：settings `alert_voice/discord/cursor/whatsapp` 存在（`settings.py:112-121`）＋`_clamp`；`gpu_health` soft 83 / hard 90 / mem 95 真值；`gpu_policy.gaming_now()` 真係 relay 去 `activity.gaming()`（同一個 foreground bug）；`router._QUERY_MARKERS` 冇 miss 字眼；加新 test 檔**一定要**改 golden-set doc（`eval_gate.py:296-322`）；tests 34 個 `test_*.py`，CI = `pytest tests/ -q`（冇 GitHub Actions）。

## Review Round 3 — 中立裁判裁決（2026-09-12 14:0x）+ v4 修正

**比數：反方贏 7:3**（Round 1 8:2 → Round 2 6:4 → Round 3 7:3）。今輪反方兩個 CRITICAL 都係我自己引入嘅新問題，唔係舊問題：

**🔴 CRITICAL-1：digest 係新嘅無底黑洞（＝Round-1「無聲蒸發」改名）**
v3 令 `expired()` 對 `digest` 回 False、`hold_until` 過期又轉 digest，**但全 plan 冇寫邊個讀 digest、幾時 summarise、幾時 ack**。→ 打機 3 小時 = 幾十條永久卡死喺 `queue.jsonl`（唔出聲、唔會 GC、冇 emitter）。
**修正（v4）**：**owner = poll_loop**：每 `alert_digest_interval_s` **或** gaming→idle 轉換時，讀 `state=='digest'` 行 → **一句英文（唔靠 LLM：每 kind 一句 + 總數）** → `mark_spoken` + ack 全部；**digest TTL 24h** 過期 → `drop(reason='digest_expired')` 寫 ledger；`last_digest_ts` **持久化落 state 檔**（restart 唔會重覆／漏）。

**🔴 CRITICAL-2：P1「shadow 只寫 ledger」根本量唔到數，而且默認就 enforce**
決策喺 speaker（Task 4）、ledger 喺 store（Task 6）→ shadow 期間冇真實狀態轉變 = **冇 ledger 行** → P2 依賴嘅兩個 metric 永遠計唔出；而 `alert_policy_enabled='on'` 默認 = **落地即 enforce**。
**修正（v4）**：改用 **`alert_policy_mode = off | shadow | enforce`（默認 `off`）**；shadow 由 **speak_gate 計完 SpeakPlan 寫獨立 `shadow_ledger.jsonl`**（`row.id / decision / would_be_action / reason / ts`），**零執行路徑改動**；P2 才 `enforce`。P1 通關條件 = shadow ledger **≥48 小時樣本**。

**🟠 v4 亦要修（反方 HIGH/MED）**
1. **`peek()` 未 filter state + hold verdict 冇定義 lease 處理** → 一係靜默 ack 丟 alert（違反 critical 唔可以被靜音），一係最舊 held 每 1s 被 re-lease 卡死 loop、critical 排唔到（**飢餓**）。→ **明文**：`peek()` 只回 `state=='pending'`；`should_speak` 回 hold 時**必須 `hold(row.id)` + 即時釋放 lease + continue 下一行**；測試：held 唔會再被 peek、hold 唔會 ack、critical 唔會排在 held 之後。
2. **held 無上限 + release 一次過洗版**：`alert_store.py:141-148` 冇 candidate 時 `for/else: break`（＝`max_depth` 對 held 完全失效），而且 release 一次過 20+ 條 = 連續講 40–120 秒（違反 Q1「最多 30 分鐘一句」）。→ **held 硬上限 64**；同 `kind+app` 只留最新；`priority=='normal'` 超額即轉 digest；release 每次只放 **critical + 最新一條 normal**，其餘交 digest flush；每次 peek 都全文重寫（O(n)）呢點要一併收斂。
3. **`idle_seconds<120` 係錯訊號**：`GetLastInputInfo` **唔計 gamepad**（手制打機 → idle 高 → 誤判「唔打機」）；反過來任何 2 分鐘 AFK（CS2 排隊／睇片）就 flush 全部 held。→ v2 規則：**game process AND（前景=game OR fullscreen OR idle<120）**；並**要 SK 用手制實測一次**（今日可做）。
4. **freshness 60s 對唔上 cron 1 分鐘寫入週期**（`activity_watch.py` every 1m）→ tick jitter 就會 flap。→ 窗改 **≥180s（3×）**；**release 要連續 non-gaming ≥180s**；flap 保護擺 gate 層。
5. **P1 改 `activity.gaming()` ＝ 唔係 shadow**：`gaming()` 另外餵 `ear.py:36-38 should_stt_use_gpu()`（STT 用唔用 GPU）同 `mcp_alerts_http.py:374 jarvis_speak` gate → 一改即時變行為（可能令 STT 意外跌落 CPU）。→ **另開 `is_gaming_v2()`**，P1 期間**只有 v2 寫 shadow ledger**，舊 `gaming()` 保持 v1；P2 才逐個 consumer 切換 + 驗。
6. **raw→TTS 冇 choke point（Goal 未真正保證！）**：兩條出聲路都係 `_speak_hermes(row.phrase)` 直接講 store 內字串；舊 queue 行、MCP `jarvis_alert(phrase)`（LLM 自由填）、`cursor_hook_alert.py:151` 直入 store 嘅字，全部原句出聲，而 `alert_tts='hermes'` 呢條路**冇 CJK 檢查**（只有 `mouth.py:304` Piper 路徑有）。→ **fail-closed validator 擺喺 speaker 出口（唯一 choke point）**：`_speak_hermes` 之前過 `shape()`＋ASCII 檢查，唔過 → **拒講**＋ledger `drop(reason='non_ascii')`；測試：直接 enqueue CJK／URL／`=` 行，斷言唔會到 TTS。
7. **voice_call hold 冇 release 路徑**：v3 只寫「gaming=False → release」→ 通話中照出聲（`shell_app.py:1655-1690` 有 `_voice_call_mute` 但只覆蓋 app 內 TTS）。→ release 條件改 **`not gaming AND not voice_call`**（或 hold 帶 reason 各自 release）；測試：`voice_call=True, gaming=False → 唔 release`。
8. **store 唔應該讀 settings**（否則 `tests/test_alert_store.py` / `test_alert_tts_sink.py` 會跟你當日 settings 漂移）→ `enqueue(..., priority=...)` 由 caller 傳；**policy 以參數注入**（`AlertStore(policy=...)`），測試傳 fake policy。
9. **`dedupe_key` 唔可以留死欄位** → 明文在 `enqueue()` 內 enforce（`kind+dedupe_key+5 分鐘`重複 → digest／`drop(reason='dedupe')`）＋測試；否則刪走個欄位。
10. **ledger 必須 fail-open**：append／rotate 包 `try/except` + rate-limited `[warn]`，**絕對唔可以影響 queue 讀寫**（否則 audit 功能會搞到全線靜音）；測試：模擬 ledger 路徑不可寫，`enqueue/peek` 照常。
11. **baseline 要寫清**：改完之後 = 新 pytest 總數（>379）＋ **新 eval_gate hash**（`0b88e6f6bab43269` 會失效）＋ `--lock` 一致，三者全綠。

**⚠️ 期望管理（要同 SK 講清楚）**：唔做 sender 之後，「重要性」**只剩 kind 級**（4 個 settings 開關 + 3 條 critical 硬門檻）。要做到「按訊息內容／邊個發」嘅重要性，**必須**先做 **WinRT toast sender 抽取**（`StoredAlert` 加 sender）＋ per-sender 白名單 → 列入 **P4（future）**，唔可以當已解。

**✅ P0 範圍收窄（反方有條件批准，v4 定案）**
- **只做**：新建 `src/jarvis/alert_policy.py` **純函數**（`shape()`＝ASCII 保證 wrapper，delegate `alert_phrase_for`）＋ 測試；Task 7 settings key 定義（`alert_policy_mode` 默認 **off**）＋ `_clamp` ＋ **eval_gate golden 同步**。
- **唔做（推去 P2，要有 shadow 數據先）**：改 `alerts.alert_phrase_for()` 現有句子（會即時改口風，而且撞 `tests/test_alerts.py:60/73-74` 字眼斷言）；`alert_policy_mode` 轉 `enforce`。

## Review Round 4 — 中立裁判裁決（2026-09-12 14:2x）+ v5 修正

**比數：反方贏 8:2**（8:2 → 6:4 → 7:3 → 8:2）。今輪捉到嘅係**設計盲點**，唔係規格細節：

**🔴 CRITICAL-1：`shape()` 冇 caller ＝ 死碼，而且照 v4 落會把「噪音」變成「靜默」**
- 全 plan grep：`shape()` 只出現喺定義同 review 記錄，**冇任何 task 負責叫佢**；Task 5 出口只做 `is_speakable()`「唔過 → 拒講」。
- 實況 `shell_app.py:576-578` 直接 enqueue `self_monitor` 條 metrics line（含 `=`）→ 照 v4 落：P2 enforce 後嗰條**唔過 ASCII → 被 drop**，而你最關心嘅 `fp>=3`（wake 誤觸）同 serve error **從此冇通道到 SK**（digest flush 只讀 `state=='digest'`，唔 cover drop）＝**旗艦 case 冇修好，只係由噪音變黑洞**。
- **修正（v5）**：① choke point 由「拒講」改成 **「先 `shape()` 成英文句 → 再 assert speakable」**，未知內容 → generic 英文句（`"Sir, you have a new alert from <app>."`），**永不消失**；② Task 0 要**明文接線**：`shell_app._enqueue_alert` 及所有 enqueue caller 出聲句經 `shape()`；③ validator 定義改成「輸出一定係 shape 白名單 template」，而唔係「唔准某幾個字元」（`=` 誤殺 + digits／`|`／`->` 照樣漏殺 = brittle proxy）。

**🔴 CRITICAL-2：Task 5 「唯一出口」唔止一條 TTS 路**
- `mcp_alerts_http.jarvis_speak`（`:368-393`）**直接 `mouth.speak`**（只擋 CJK，唔擋 `=`／URL／digits）；`shell_app.py:1437-1445` 嘅 `alert_tts=piper` 分支亦係直入 `mouth.speak`。
- **修正（v5）**：validator 擺喺**真正唯一出口 `mouth.speak()`**（或明文列 4 條 TTS 路逐條驗：poll_loop／speak_once／shell_app piper／jarvis_speak）。另外：**`speak_once.py` 今日冇任何 cron 跑**（8 個 Hermes cron job 冇 alert/speak；live 出聲路 = `shell_app.py:540-547` spawn poll_loop）→ Task 9 唔應該當佢係並存風險，真正 live 嘅第二條路係 `jarvis_speak`。

**🔴 CRITICAL-3：桌面 Settings UI 會靜默還原新欄位（＝連 SK 現有設定都中招）**
- `settings_ui.py:1501-1580 _save()` **由零建構 `Settings(...)`**，只填 UI widget 有嘅欄位；`settings.py:556-578` `save_settings` 用 `merged = {**existing, **asdict(s)}` → **新欄位一律變 dataclass 預設**。
- **實證現有 bug**：UI constructor 完全冇 `stt_preload / tts_ack / vc_fail_closed / mage_* / alert_gpu_poll_s / alerts_mcp_port / alerts_mcp_token / discord_voice_out`（grep = 0），而 live `settings.json` 明明 `stt_preload=true` → **你一按「儲存」就靜默回落 false**。
- **修正（v5）**：`_save()` 由 `load_settings()` 起手、只覆寫 UI-bound 欄位（replace-on-existing）＋加 test（UI save 後新舊非 UI 欄位不變）＋為新開關加正確 UI 控件（P0 只加喺既有「提醒」tab，**唔加新 tab**：`test_settings_ui_smoke.py:22-57` 斷言 5 個 tab）。

**🟠 HIGH 修正（v5）**
4. **`gpu_hard` flag 到唔到 store**：`alerts.py:735-743` 用 `hit.kind` 轉發，Task 3 Files 冇列 `alerts.py` → 要一齊改（`kind = "gpu_hard" if hit.is_hard else "gpu_health"`）＋**由 monitor 到 enqueue 嘅 end-to-end 測試**（唔止測 monitor 內部 flag）；Task 0 要補 `gpu_hard` template。
5. **P1 gate M1 係循環依賴**：「打機時 soft ≤2 次/小時」要靠 P2 enforce 才做到（今日 soft 83°C＋120s cooldown ≈ 30 次/小時）→ P1 **永遠達唔到**。修正：M1 降為**診斷輸入**；P1 通關改「**shadow ledger 覆蓋 ≥6 個 game-active 小時** ＋ hard 事件 0 次 ＋ soft 完整分類」；「≤2 次/小時」搬去 **P2 驗收**。
6. **M3 同 Q2／v2 規則矛盾**：v2 寫「前景=game OR fullscreen OR idle<120」 vs Q2「要有輸入活動」→ 排隊／menu／launcher 前景 = 判 gaming（違反 Q2）。→ **要 SK 裁決：launcher／排隊／menu 算唔算打機**；量測分開報「launcher 前景」同「真 playing」兩類。
7. **Shadow ledger 結構上量唔到 M3**（冇 alert = 冇行，FP 分母 0）→ 加 **heartbeat sampler**（同 process，每 30–60s append `shadow_heartbeat.jsonl`：raw activity + `is_gaming_v2()` + v1 `gaming()` + foreground／fullscreen／idle）→ M2/M3 由心跳計，M1 由 ledger 計。
8. **唔使等 wall-clock 48h**：用現成 `serve.log`（**268 條 `[alert]`、122 unique**）**重播 decision table** → 即刻有 kind 分佈；gate 改用 **game-active 小時**。
9. **State/priority 遷移要覆蓋全部 enqueue call site**（`alerts.py:781,797,879,916,1094`、`shell_app.py:554`、`mcp_alerts_http.py:423`、`cursor_hook_alert.py:151`）＋舊 queue row（`from_dict` 默認 `state="pending"`、`priority="normal"`）→ 漏一個 = `TypeError` 被 `except Exception` 吞 = alert 靜默消失；改 frozen golden test（`test_alert_store.py:61-67`）要寫明係「擴大斷言」。
10. **GC 做狀態轉換會令 `list_open()/stats()` 語義分裂**（MCP 會見到永不出聲嘅 digest 當 open）→ `stats()` 回分佈 `{pending, held, digest, dropped, spoken}`、`list_alerts` 只回 pending（或加 `include=`）、GC 只做單向且唔喺讀路徑寫檔。
12. **serve.log 每條 alert 寫兩次**（`alerts.py:766` ＋ `shell_app.py:1407`）→ **頻率指標一律由 ledger 計**，唔好數 serve.log（否則 M1 假番一倍）。
14. **P0「零改動」要收窄定義**：`settings.json` 一定會新增 key、`--hash` 會變（但 `tests/test_eval_gate.py` 冇斷言舊 hash、repo 又冇 CI → 唔會紅）；真紅線 = **`--lock` doc↔mapping 一致**（`eval_gate.py:296-322`）＋ **5-tab 斷言**（`test_settings_ui_smoke.py:22-57`）。

**🟡 正方唯一殘留矛盾（必修）**：plan L16／L22 仲寫「priority 可由 L4 LLM 提升／L4 輸出 priority tag」→ 同 Task 10「只做 digest polish」矛盾，而且係 **LLM 影響講/唔講嘅後門**。→ **v5 明刪**，改成 invariant：**「L4 永不改 priority」＋測試斷言**。

**✅ v5 定案：P0 / P1 重新定義**
- **P0（即刻，有真價值）**：Task 0（`alert_policy.py` 純函數 ＋ `gpu_hard`/self-monitor/test/extra template）＋ Task 1（settings keys 默認 off ＋ UI 只加喺既有 tab）＋ **接線 self-monitor 出聲句**（＝**今日之後唔再聽到「數字＋=」**，而且唔會變靜默：shape 出英文句）＋ **`mouth.speak()` 出口 validator**（shape→assert，覆蓋全部 4 條 TTS 路）
- **P1（shadow，有證據力）**：Task 3（＋`alerts.py` emit 改動）＋ Task 4（只 v2）＋ Task 6（shadow ledger **＋ heartbeat sampler**）→ 通關 = **≥6 game-active 小時樣本**、hard 事件 0、FP 由心跳計
- **P2（enforce）**：Task 2＋4＋5＋7＋8＋9（+ 前置 #3 settings UI 修好、#9 call site 清單）
- **P3/P4**：LLM（只 digest）／sender 抽取

## Review Round 4 — cursor review-only 裁決（2026-09-12 14:2x）+ v5.1 最終明確化

**VERDICT: NEEDS-FIX（2 blockers）** — 兩者都係「實作 agent 會自己發明」嘅位，所以**要在 plan 寫死**：

**🔴 B1：Task 0 冇寫死新增 template 嘅**exact English**（會變成 agent 自創 = 唔 deterministic）→ 以下為定稿（純 ASCII、零 `=`、零 URL、零 CJK）：
- `self-monitor`（notable）：`"Sir, self monitor: {N} wake events, {F}, {E} errors, threshold {T}."`
  - `{F}` ＝ `"no false positives"`（fp==0）／`"{n} false positives"`；`{T}` ∈ `{"unchanged","raised","lowered"}`（由 run_once 提供嘅 enum，唔准自由文字）；`{N}`／`{E}` 為整數
- `gpu_hard`：`"Sir, GPU critical limit reached."`（**唔加數字**，避免單位／`=` 污染）
- `test`：`"Sir, this is a test alert."`
- bare `extra`：`"Sir, you have a notification."`；`extra:<label>`：`"Sir, {label} has a notification."`（label 先過 ASCII sanitize）
- 未知 kind：`"Sir, you have a new alert from {app}."`（app 空 → `"Sir, you have a new alert."`）
- 已知 kind：**一律 delegate** `alerts.alert_phrase_for()`／`gpu_health_phrase()`（唔改佢哋原文）

**🔴 B2：Task 1 clamp／enum 未寫齊** → 定稿：
| key | 規則 |
|---|---|
| `alert_policy_mode` | enum `off｜shadow｜enforce`，非法 → `off` |
| `alert_gaming` | enum `hold｜drop`，非法 → `hold` |
| `alert_hold_ttl_s` | int 30–3600（默認 900） |
| `alert_held_cap` | int 8–256（默認 64） |
| `alert_digest_interval_s` | int 300–7200（默認 1800） |
| `alert_digest_ttl_s` | int 3600–604800（默認 86400） |
| `alert_dedupe_window_s` | int 0–3600（默認 300；**0 = 停用**） |
| `alert_llm_polish` | enum `off｜on`，非法 → `off` |
| `alert_llm_timeout_s` | float 1.0–10.0（默認 3.0） |

**🟠 其餘（v5.1）**
- **唔改 Electron HUD**（`hud/settings.html` 係主要 UI，但**改 hud/ 係反方嘅停手紅線**）→ P0/P1 用 **CLI 切換**：
  `env -u PYTHONPATH python -c "from jarvis.settings import save_settings_patch; save_settings_patch({'alert_policy_mode':'shadow'})"`（`save_settings_patch` 已有 `:644-649`）；**HUD 控件列入 P2 可選**（要改 hud 就另開任務＋先問 SK）
- **test 檔改名**：`tests/test_speak_gate.py` → **`tests/test_alert_speak_gate.py`**（避免同現有 `test_speaker_gate.py` 撞名混淆）
- **`eval_gate.py`**：除 GOLDEN_SUITES mapping，**`py_compile` 清單要加 `src/jarvis/alert_policy.py`**（plan 原本冇寫）
- **確認 FACT**：`alert_store.py` 今日唔 import settings（policy 注入＝真新工作）；`last_digest_ts` 冇現成 state 檔（新 artifact）；poll_loop 由 `shell_app.py:513-537` spawn（pythonw），Electron restart 會 ~90s 後重起 → **必須持久化 digest timer**
- **清理**：Round-3 段遺留嘅「P0b」「Task 6 hook」字眼係歷史記錄，**以 Task 0-11 為準**（避免實作 agent 跟錯）
- **未決（等 SK）**：`is_gaming_v2` 規則 (b)「前景=game」同 Q2「要有輸入活動」衝突 → 要 SK 裁決 launcher／排隊／menu

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
