# Hermes ↔ Jarvis alerts HTTP MCP

Watcher (`jarvis serve`) enqueues short English pings; Hermes TTS speaks them.

## Topology

```text
jarvis serve
  → AlertStore JSONL
  → HTTP MCP 127.0.0.1:8765/mcp   (Hermes tools / debug)
  → poller ~1s (scripts/hermes_alert_poll_loop.py) → Hermes TTS (alert_tts=hermes) → ack

Hermes cron (backup, ≥1m): jarvis-alerts-speak --no-agent
  → scripts under %LOCALAPPDATA%\hermes\scripts\jarvis_alert_speak_once.py
  needs: hermes gateway running
```

## FACT — cron cannot do 1s

Hermes schedule units are **minutes+** (`every 1m` min for intervals). Gateway ticks ~**60s**.  
Eng plan 「≤1s poll」→ use **`hermes_alert_poll_loop.py`** (started by `jarvis serve` when `alert_tts=hermes`). Cron = slow backup only.

## Alert pipeline (v5.1, 2026-09-12) — raw 字串永遠唔准出聲

```text
producer → AlertStore.enqueue(kind, phrase, detail, dedupe_key)
   ↓ L1 shape   alert_policy.shape()        raw metrics / URL / CJK → deterministic English template
   ↓ L2 policy  alert_policy.policy_for()   kind × settings → speak_now | digest | drop（CRITICAL 唔可降級）
   ↓ L3 gate    speak_gate.should_speak()   gaming / voice_call → hold（critical 穿透）
   ↓ speaker    scripts/hermes_alert_poll_loop.py（唯一出路）→ mark_spoken → TTS → ack → miss_ledger
```

**硬規則**：任何 raw 字串（`fires=…`、URL、中文 toast body）**永遠冇通道去到 TTS**；`mouth.speak()` 出口有 validator（fail-closed）。講／唔講 **100% deterministic**（`alert_policy.policy_for` ＋ `speak_gate.should_speak`）；LLM（L4）只可以做 digest 潤飾，**永遠唔可以 suppress／降級**，默認 `off`。

| 模組 | 責任 |
|---|---|
| `src/jarvis/alert_policy.py` | 純函數：`shape()`（template）／`policy_for()`／`priority_for()`／`sanitize()`／`is_speakable()`／`CRITICAL` |
| `src/jarvis/speak_gate.py` | `should_speak(row) -> SpeakPlan`（`speak`／`hold`／`digest`／`drop`）＋ `is_gaming_v2()`（process-based，唔靠 foreground） |
| `src/jarvis/alert_shadow.py` | shadow mode：只寫 `%APPDATA%\Jarvis\alerts\shadow_ledger.jsonl`（＋heartbeat），零執行改動 |
| `src/jarvis/alert_store.py` | 狀態機 pending／held／digest／spoken／dropped；`miss_ledger.jsonl` append-only（每次狀態轉變 ＋ reason，>2MB rotate `.1`，fail-open） |
| `scripts/hermes_alert_poll_loop.py` | 唯一 speaker：release held → digest flush（30 分鐘 或 gaming→idle 一句）→ `peek(lease_s ≥ 300)` → `mark_spoken` → TTS |

**新 settings keys**（`src/jarvis/settings.py`；全部默認 = 今日行為）：

| Key | Default | 意思 |
|---|---|---|
| `alert_policy_mode` | `off` | `off`／`shadow`（只寫 ledger）／`enforce` |
| `alert_gaming` | `hold` | 打機時 `hold`／`drop` |
| `alert_hold_ttl_s` | `900` | hold 最長幾久（過期轉 digest） |
| `alert_held_cap` | `64` | held 行上限（防黑洞） |
| `alert_digest_interval_s` | `1800` | digest 一句嘅間隔 |
| `alert_digest_ttl_s` | `86400` | digest 行 TTL |
| `alert_dedupe_window_s` | `300` | 同 kind 去重（0 = 停用） |
| `alert_llm_polish` | `off` | ⚠️ **未接線**（Task 10 暫緩：冇 runtime reader、冇 UI 控件） |
| `alert_llm_timeout_s` | `3.0` | ⚠️ **未接線**（同上；預留畀 Task 10） |

**「what did I miss」**：講 `"what did i miss"`（或 `did i miss anything`／`miss咗啲咩`…）→ router `alert_miss` intent → **本機處理**（唔經 Hermes，即使 `hermes_enabled`）→ 讀 24 小時 `miss_ledger.jsonl` → 一句 ASCII 英文（例：`"Sir, 3 alerts went unanswered while you were away: whatsapp x2, gpu health x1."`；冇嘢 = `"Sir, nothing missed."`）。

**⚠️ 未啟用**：`alert_policy_mode` 默認 `off`（settings.json 亦未寫入新 keys）——要 restart sidecar，再以 `shadow` 收 ≥48 小時樣本（M1 打機時 GPU soft ≤2 次/小時、M3 Prism 開住唔玩 FP <5%）才上 `enforce`。

## 2026-09-13 修復輪（fix1–fix9，全部由 Hermes 親跑收貨）

| 修咗咩 | 實錘 |
|---|---|
| 「what did I miss」**報大數**（把 ledger 事件行當未答 alert） | 按 id 去重、只計未 `spoken`；`over 999` 句法；label 消毒次序修好 |
| `release_held()` 之後行即刻 `ttl_expired` **靜默消失** | release 時 refresh `ts` → 仍可講／入 digest |
| release 窗寫 180s、實際 3 秒 | 改純時間窗 `RELEASE_QUIET_S = 180` |
| 生產 `AlertStore()` **冇注入 policy**（critical 變 normal） | 新 `default_store()` 工廠，生產點全部走佢 |
| settings key **寫得入冇人讀** | 真接線（held cap／dedupe window／digest TTL）；未接線 LLM key 由 UI 拆走 |
| digest flush **先講後 clear** → 撞鎖會重講 | 先 `mark_spoken` claim → 講 → 失敗還原、`clear` 包 try |
| `alert_tts=piper` 係**第二條 speaker**（繞過 gate） | piper 分支改走 `should_speak` ＋ `alert_dispatch.enforce` |
| release **一次過放晒**（打機完連珠炮發） | 只放 critical ＋最新一條 normal，其餘留 held → digest 一句講完 |
| `[warn] release_held noop` 每秒印（~86k 行/日） | 60 秒 rate-limit |
| **dedupe key 用常數**（吞真事件） | 改 `hash(summary)`（同內容才 dedupe） |
| **`guard` 冇傳落 TTS 子進程**（聊天回覆被 strict 吞） | `guard` 傳落 subprocess |
| `should_speak` **忽略 `row.priority`** | `priority == "critical"` 第一短路口；critical 由 `priority_for` 單一來源 |
| `sidecar_down` **冇 producer**（假安全感） | 明文移除（要真 watchdog 才加返） |
| mode 切 `off` 之後 held／digest **變殭屍** | off 模式照 gc ＋ 講一次 digest ＋ 放 held |
| MCP `peek_alert` lease 仍 30s（可重讀同一句） | 300s |
| `default_store()` fallback 冇 policy | fallback 都注入 |
| `gpu_hard` producer 傳 **空 phrase** → `enqueue()` raise → **critical alert 靜默消失**（fix8 引入、fix9 修） | producer 傳 `alert_phrase_for(kind)`；`shape()` delegate 同一函數（單一來源）＋ 空 phrase 防守 |
| LOW | 刪死碼（`is_metric_noise`／`quiet_iters`／`process_row`／`_ = gaming`）｜`--json` 真生效｜`label_for` 統一｜`enforce` 重用 `effective_action`｜`HB_INTERVAL_S` 匯出｜mouth strict 同 choke 同一 validator |

## Baseline（2026-09-13 01:2x，親跑）

```text
python -m pytest tests/ -q          → 522 passed / 0 failed
python -m jarvis.eval_gate --lock   → 一致（52 test files）
python -m jarvis.eval_gate --all    → golden / regression / stress 三 suite ok=True
                                      HASH 655b15e8bca241de
```

## TTS modes (`alert_tts`)

| Value | Behavior |
|-------|----------|
| `hermes` (default) | Hermes TTS subprocess only (60s hard timeout + `taskkill /F /T` on hang) |
| `piper` | In-process Jarvis Piper mouth |
| `off` | Drain/ack without speaking |

## GPU health (P0)

NVML (`nvidia-ml-py`) primary → nvidia-smi CSV fallback. Dynamic clock baseline + hard temp ceiling (≥90°C). Per-reason cooldown.

## Token / MCP

- Token file: `%APPDATA%\Jarvis\alerts\mcp_token.txt` (auto)
- Env: `JARVIS_ALERTS_MCP_TOKEN`
- Hermes client: `%LOCALAPPDATA%\hermes\config.yaml` → `mcp_servers.jarvis-alerts`

```yaml
mcp_servers:
  jarvis-alerts:
    url: "http://127.0.0.1:8765/mcp"
    headers:
      Authorization: "Bearer <token>"
    timeout: 30
```

Verify:

```powershell
hermes mcp list
hermes mcp test jarvis-alerts
# expect 10 tools: peek_alert, ack_alert, list_alerts, alert_stats,
#   jarvis_speak, jarvis_wake_status, jarvis_sensors, jarvis_alert,
#   jarvis_clarify_gate (Self-Evol Phase E: EVPI 問唔問), jarvis_autonomy_state (Phase D: 自主度等級)
```

Self-Evol tools（2026-08-31 wiring）:
- `jarvis_clarify_gate(task, task_type, unknowns[], assumptions[], confidence)` → `should_ask` + 保守假設；答案一律當 untrusted（R17）
- `jarvis_autonomy_state()` → `level`（L0/L1a/L1b/L1c）+ `sandbox_ready` + 最近 H_auth events；level 持久化喺 `%APPDATA%\Jarvis\autonomy_state.json`
- 詳情：skill `jarvis-self-evol-ops`

## Cron (backup)

```powershell
# already created as jarvis-alerts-speak (every 1m, --no-agent)
hermes cron list
hermes gateway          # required or jobs never fire
# or: hermes gateway install
```

## Fast path (recommended)

```powershell
# jarvis serve starts MCP + poller when alert_tts=hermes
# or manual:
$env:PYTHONPATH = "C:\Users\skps9\Documents\Code_Project\jarvis-pc\src"
python scripts\hermes_alert_poll_loop.py
```

Needs: Windows Hermes + `piper-tts` in Hermes venv + Jarvis model  
`%APPDATA%\Jarvis\models\piper\jarvis-high.onnx` + `ffplay` on PATH.

Hermes `config.yaml`:

```yaml
tts:
  provider: piper
  piper:
    voice: "C:/Users/skps9/AppData/Roaming/Jarvis/models/piper/jarvis-high.onnx"
```

## Cursor triggers (pick in companion 設定 → 提醒)

| Key | Default | Meaning |
|-----|---------|---------|
| `alert_cursor` | `true` | Master switch |
| `alert_cursor_hooks` | `true` | stop / preToolUse → queue. **Windows:** install uses `cmd /c … python -u` ([forum](https://forum.cursor.com/t/hooks-not-working-on-windows/149509)). |
| `alert_cursor_toast` | `true` | Action Center; skips Done only if a hook fired in last ~30s |
| `alert_cursor_uia` | `true` | Exact UIA `Waiting for approval` — keep ON if Ask/plan silent |
| `alert_cursor_watch` | `false` | Title busy→idle + taskbar flash (noisy) |

Debug hooks: Cursor **View → Output → Hooks**. Reinstall after pull: `python -m jarvis cursor-hooks install` then reload window.

```powershell
cd C:\Users\skps9\Documents\Code_Project\jarvis-pc
$env:PYTHONPATH = ".\src"
python -m jarvis cursor-hooks install
python -m jarvis cursor-hooks status
```

Writes/merges `%USERPROFILE%\.cursor\hooks.json`:
- `stop` → finished / error
- `preToolUse` → SwitchMode / Ask* (when Cursor fires it)

Enable **Hooks** in Cursor Settings; reload window. If hooks feel unstable: uncheck Hooks, keep Toast + UIA.

| Event | Phrase |
|-------|--------|
| stop completed | Cursor finished its work. |
| preToolUse SwitchMode | Cursor wants plan mode. |
| Toast / UIA wait | Cursor needs your approval. / plan phrase |

## Settings

| Key | Values |
|-----|--------|
| `alert_tts` | `hermes` (default) / `piper` / `off` |
| `alerts_mcp_port` | default `8765` |

## Spike

`docs/hermes_speak_spike.md`
