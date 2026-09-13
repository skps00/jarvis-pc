# JARVIS 自檢整合入 App — Plan（2026-08-29）

> 目標：所有同 Hermes/JARVIS 相關嘅監察邏輯（watchdog / self-monitor / alerts speak）併入 JARVIS ONE 自己，Hermes 唔再喺外面管 JARVIS。SK 原則：**「任何 relate to hermes/jarvis 都應該 combine 入 jarvis app」**。

---

## 現況（Hermes cron 管住 JARVIS 嘅 3 個 job）

| cron job | 頻率 | script | 職責 |
|---|---|---|---|
| `jarvis-serve-watchdog` | 每 1m | hermes/scripts/jarvis_watchdog.py | serve 死咗 → 靜默 restart |
| `jarvis-self-monitor` | 每日 09:00 | jarvis_self_monitor.py | wake stats + threshold 自調（有嘢先出聲） |
| `jarvis-alerts-speak` | 每 1m | hermes/scripts/jarvis_alert_speak_once.py | poll alerts queue → mouth.speak |

**根本問題**：JARVIS ONE（Electron + Python sidecar）已經係 self-contained app（sidecar spawn 由 main.js 管），但呢三件監察仲係外掛喺 Hermes cron——即係 JARVIS 嘅健康依賴 Hermes 先 survive，架構上錯。

**Sidecar 現有基礎**（整合唔使由零寫）：
- `main.js` 已 spawn sidecar（`spawn(PYTHON, ['-m','jarvis','serve'], {env:{JARVIS_ELECTRON_HOST:'1'}})`）＋ `sidecarProc.on('exit')` handler 存在
- sidecar 有 `alert_store.py`（queue）、`mouth.py`（TTS）、`mcp_alerts_http.py`（8765）
- `wake.py` 已有 threshold 自調邏輯（0.25–0.75 range 保護）喺 self-monitor script 內

---

## 執行狀態（2026-08-29）

- **Phase 1 ✅ 完成**：發現 sidecar 內置 alert poller（`_ensure_alert_poller` → `hermes_alert_poll_loop.py`，~1-2s poll → Hermes TTS → ack）**一早存在**（2026-08-28 實作），cron `jarvis-alerts-speak` 只係冗餘 fallback。已驗證完整鏈路（enqueue → poller speak → ack ✓）+ 刪 cron `9401f46a1454`。
- **Phase 2 ✅ 完成**：`jarvis_self_monitor.py` 搬入 `src/jarvis/self_monitor.py`（module 化，`run_once()` 回傳 `(summary, notable)`，CLI 仍可用）；`shell_app.py` 加 `_ensure_self_monitor()`（daemon thread：啟動後 600s catch-up + 每日 09:00，notable → `AlertStore().enqueue(kind="self-monitor")` → poller 講）。已刪 cron `55baa90ff7b0` + hermes/scripts copy；serve 已重啟驗證 `[ok] self-monitor daily 09:00（in-app）`。
- **Phase 3 ✅ 全部完成（2026-08-29 實測通過）**：`main.js` sidecar 管理重寫——`spawnSidecar()`（crash-loop rate limit：60s 內 ≥3 次 → back off + tray 通知一次）、`startSidecarHealthCheck()`（30s probe，3 連 miss → kill + respawn）、exit handler identity-check（`sidecarProc === child`，防舊 child exit 清新 ref）、`stopSidecar` 加 stopping flag + clear timers、spawn 後 closeSync FD。**Cursor review 通過**（1 HIGH + 5 MED/LOW 全修）。**0.4.0 exe 已打包並換版生效**（SK 授權我用電腦換版：taskkill 0.3.1 → 開 0.4.0）。**實測：kill serve → 0.4.0 自動 respawn（新 serve parent=Electron 39856）✓，wake/alerts MCP/poller/self-monitor 全 healthy ✓**。**cron `jarvis-serve-watchdog` 已刪**——JARVIS 三件監察全部 in-app，Hermes cron 淨返自身 2 個。

---

## 方案（三階段，各自獨立可落地）

### Phase 1 — alerts-speak 併入 sidecar（最簡單，即日可做）
- **而家**：Hermes cron 每 1m 行 `jarvis_alert_speak_once.py` poll alert store → speak
- **改**：sidecar 內加 consumer thread（`alerts.py` 或新 `alert_consumer.py`）：loop poll alert store（無 alert 就 sleep ~5s）→ 有 alert 就 `mouth.speak()` → ack
- **刪**：Hermes cron `jarvis-alerts-speak`
- **驗證**：`jarvis_alert` MCP 塞一個 alert → 自己講出嚟（唔使等 cron）

### Phase 2 — self-monitor 併入 sidecar（簡單，即日可做）
- **而家**：Hermes cron 每日 09:00 行 `jarvis_self_monitor.py`（讀 wake_debug.log 統計 + threshold 自調）
- **改**：邏輯搬入 `src/jarvis/self_monitor.py` module；sidecar 啟動時 spawn daily thread（每日 09:00 跑，或啟動後 1h 內補跑一次）；有問題 → push 去 alert store（自然由 Phase 1 consumer 講出嚟）
- **刪**：Hermes cron `jarvis-self-monitor` + hermes/scripts copy
- **驗證**：手動觸發一次 self-monitor module → 正常產出 log + 有問題時 alert

### Phase 3 — serve watchdog 併入 Electron main（中等，要小心 crash loop）
- **而家**：Hermes cron 每 1m 檢查 8765 listener，死咗 restart（`JARVIS_ELECTRON_HOST=1` spawn）
- **改**：`main.js` 加：
  - `sidecarProc.on('exit')` → 自動 respawn（已有一半，補 restart 邏輯）
  - periodic health check（每 30s fetch `http://127.0.0.1:8765/health`，fail N 次 → respawn）
  - **crash-loop 保護**：60s 內 restart ≥3 次 → 停手 + tray 通知（防止壞 code 無限重啟）
- **刪**：Hermes cron `jarvis-serve-watchdog`
- **驗證**：kill sidecar PID → Electron 30s 內 respawn，8765 回復

---

## 風險評估

| 風險 | 等級 | 緩解 |
|---|---|---|
| Phase 3 crash loop（壞 code 無限重啟） | 中 | restart 限次 + backoff + tray 通知 |
| Phase 1：sidecar 死咗 → alerts 唔會講（而家 cron 喺 Hermes 都唔會理 sidecar 死） | 低 | sidecar 死 = JARVIS 成個死，Electron 會 respawn（Phase 3） |
| threshold 自調邏輯搬遷後行為唔同 | 低 | 原邏輯原封搬，先跑一次對比 log |
| 刪 cron 後 Hermes 冇咗 JARVIS 監察 | 低 | 三步做完先刪；中途任何一步失敗就停，保留 cron |

---

## 執行順序（依賴鏈）

1. Phase 1（alerts consumer）→ 2. Phase 2（self-monitor module）→ 3. Phase 3（Electron watchdog）
4. 全部驗證通過後 → 刪 3 個 cron job
5. 更新 HANDOFF + REMAINING_WORK

**測試 SOP**：dev 版 `JARVIS_OPEN_HOME=1` Electron + sidecar，用 MCP/curl 觸發各情境，睇 serve.log。

---

## 唔做嘅嘢（Out of scope）

- Hermes gateway 自身 watchdog（`gateway-watchdog-reporter`）——係 Hermes 自己，唔關 JARVIS
- HUD/Dock/Home 視覺改動
- voice input（等新 mic）
