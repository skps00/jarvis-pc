# Alert Pipeline v2（唔照讀 raw 字串；alert 內容經 JARVIS 判斷，但**唔准** LLM 決定講唔講）Implementation Plan

> **Review record — Round 1（2026-09-12 09:1x）**：adversarial 三階段 review（反方 subagent＋正方 subagent＋我中立裁判）。
> **裁決：反方 8:2**（詳見文末「Review Round 1」）。原 v1（LLM 擺喺 real-time 講/唔講決策點）被否決；以下係修好 blocker 之後嘅 v2。
> v2 核心改動：**LLM 移出 critical path**（唔可以 suppress alert），講/唔講改由 **100% deterministic policy table** 決定；fail 行為由「靜」改成「用 template 照講（高優先）／入 digest（低優先）」。

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

## Task 1 — AlertStore：state ＋ held 唔准 GC ＋ 單一 gate
**Files:** Modify `src/jarvis/alert_store.py`（`:17,37,41,104-220`）、`tests/test_alert_store.py`
- `StoredAlert` 加 `state: str = "pending"`（`pending|held|digest|spoken|dropped`）、`hold_until: float = 0.0`、`priority: str = "normal"`、`dedupe_key: str = ""`
- `expired()`：`state in ("held","digest")` → 回 `False`（唔准 GC）
- `peek()`：只回 `state=="pending" and hold_until<=now`；**並喺呢度做 gaming/voice_call gate**（讀 `%LOCALAPPDATA%\hermes\state\sk_activity.json` ＋ `voice_call_state.json`）；打機 → `hold(ttl=alert_hold_ttl_s)`
- 新：`hold()`, `release_held()`, `mark_spoken()`, `mark_digest()`, `drop(reason)`
- `list_open()`/`stats()` 要識新 state（唔好報 held 做 pending）
**驗證（新）**：`tests/test_alert_store_gate.py`：held 唔會 GC；打機 peek 回 None；release 之後照出。

## Task 2 — policy table ＋ deterministic shaping（A/C）
**Files:** Create `src/jarvis/alert_policy.py`；Modify `src/jarvis/shell_app.py:550-580`
- `POLICY = {"self-monitor": speak_now, "cursor": speak_now, "hermes": speak_now, "system": speak_now, "discord": digest, "whatsapp": digest, "extra": digest}`
- `shape(kind, phrase, detail) -> str`：已知 kind → 英文 template（例 self-monitor：`"Sir, self-monitor report: five wake fires, no false positives, three serve errors."`）；未知 → `"Sir, you have a new alert from <app>."`（**永遠唔會出 raw 字串**）
- `self_monitor.run_once()` 改回 `MonitorResult` NamedTuple（`summary, notable, spoken`）＋改 `main()`
- `shell_app._enqueue_alert("self-monitor", phrase=spoken, detail=summary)`
**驗證**：`tests/test_alert_policy.py`：所有 kind × 有／冇 detail → 出句必為 ASCII 英文、零 `=`、零 URL、零 CJK。

## Task 3 — 修 lease／雙重出聲（B4）
**Files:** Modify `scripts/hermes_alert_poll_loop.py:37-49`、`scripts/hermes_alert_speak_once.py:221-233`
- 兩個 script 都改：`peek(lease_s=300)` → speak → `mark_spoken(atomic)` → ack；TTS 失敗 → 釋放 lease（`release`）留待下輪
**驗證**：`tests/test_alert_poll_race.py`（mock store：慢 speak 期間再 peek → 唔會攞到同一行）。

## Task 4 — L4 離線 LLM 加分（SK 要嘅「先經我判斷」，非阻塞、唔可 suppress）
**Files:** Create `src/jarvis/alert_llm.py`；Modify `scripts/hermes_alert_poll_loop.py`（背景 thread）
- 對**已經決定要講**嘅 alert：背景問一次 LLM（現有 DeepSeek key，直接 chat，**唔係 agent run**）→ 更好嘅英文句 + `priority`（只可升）+ idle digest 用嘅一句總結
- **Timebox 3s**：唔回就用 L1 template 照講（**唔會靜音**）
- 另一個用途：idle 時（SK 喺 game → 唔講）將 `digest` kind 累積，隔 30 分鐘用一句英文講／或寫入 HUD，交由 SK 決定要唔要
- 每次寫 `%APPDATA%\Jarvis\alerts\triage.jsonl`（**要 rotate：>2MB 就 rename .1**）
**驗證**：`tests/test_alert_llm.py`（mock：正常／timeout／垃圾 JSON → 三種都必須有聲出，且句子合規）。

## Task 5 — Settings keys ＋ clamp
**Files:** Modify `src/jarvis/settings.py`（`_clamp` 一齊加）、`src/jarvis/settings_ui.py`
- `alert_policy_enabled="on"`、`alert_gaming="hold"`、`alert_hold_ttl_s=900`（clamp 30–3600）、`alert_llm_polish="on"`、`alert_llm_timeout_s=3.0`（clamp 1–10）、`alert_digest_interval_s=1800`
**驗證**：`tests/test_settings_alert_keys.py`：亂值（`"banana"`／負數）→ clamp 到合法值。

## Task 6 — Docs ＋ 收尾
- `docs/hermes_alerts_mcp.md` 加 pipeline 圖 ＋ 「raw 字串幾時都唔准出聲」規則；`AGENTS.md` 加一句；handoff 更新
- 收尾：repo root 有 `_staging/`、`_tmp_test_write.txt`、`nonexistent/`、`_compile_check2.py`、`_apply_and_compile.bat` 等殘留 → 問 SK 要唔要清（**唔自己刪**）
- CI：`env -u PYTHONPATH python -m py_compile src/jarvis/*.py scripts/*.py` ＋ `env -u PYTHONPATH python -m pytest tests/ -q`（jarvis-pc 係 pytest）＋ `python -m jarvis.eval_gate --all`

---

## Open questions（等 SK）
1. **digest 定義**：whatsapp/discord toast 我建議「唔即時講，累積成 30 分鐘一句英文 digest」（打機時尤其）——OK？
2. 打機時 `speak_now` kind（self-monitor/cursor/hermes）：**hold 到 idle 補講**（建議，TTL 15 分鐘）定一律唔講？
3. L4 用邊條 key：**現有 DeepSeek（平、快）**定 Hermes API（我本人、但慢＋貴＋approval 風險）？→ 建議 DeepSeek，Hermes API 留做 idle digest 嗰層。
4. 要唔要而家就開 cursor-agent 落 Task 1-2（deterministic 部分），L4 之後再落？

## Review Round 1 — 完整記錄（三階段）
- **Stage 1 反方（最強反）**：否決 v1 Task 5／Task 2 實作；8 條 HIGH（B1-B8 上表）全部有 file:line。
- **Stage 2 正方（最強支持）**：認為 v1 嘅方向係結構性（刪通道，唔係叫模型自律）＋同 `clarify_gate`、`jarvis_speak` 既有 gate 一致；但**同意 v1 嘅 Hermes API 前提要驗**。
- **Stage 3 中立裁判**：**反方 8:2**。原因：反方 HIGH 全部係 code-verified blocker（唔係口味），照 v1 落會即日壞；正方勝在認清問題層次（要刪通道），故保留其目標、換 placement。
- **最大未知**：L4（LLM 改寫）實際延遲／質量；如果 background polish 慢過出聲，L4 價值就只剩 digest。
- **反轉條件**：如果 Hermes API 證實可以 per-request tools-off 且 p95 < 2s（實測），而 SK 接受「LLM 可 suppress」，v1 式設計可以重評。
