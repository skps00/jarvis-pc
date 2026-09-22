# Mini-plan v3：自我監測提示靜音（修兩個假陽性源頭）

- 狀態：**⏸ 停手（SK 2026-09-22 選 C：等新 mic 一次過做）**。以下 R1–R3 全部結論保留做將來重啟用：R1 2:8 → R2 反方 blocker 2 → R3 反方仍列 blocker，並**推翻 v3 嘅對照量測**：v3 寫「3,000 條抽樣 false-mute 0.00%」係**抽樣假綠**；反方全檔重算 373,113 條 → 用「±40 行窗口含 marker」實際誤吞 **36 條**真事故 traceback。核實方另建議改用「**該 Traceback 所屬 log record（由上一條 record header 起）含 marker**」＝現檔 30/30 照過、備份唔誤吞（已由核實方實測）。附：v3 另外兩點被攻——`resp_lat 30.0` 係樣本只有 21 個嘅魔術數（且 wake 已關 → 該條件已 inert）；`benign_tb=` 冇 reader，fail-visible 只係名義。**R3 後 Hermes 已停手，等 SK 揀（A 收窄版／B 第四輪／C 全部等新 mic）。**
- 過程：v1（加 `alert_self_monitor` 開關）→ R1 反方 **2:8**（一刀切 mute 違反 fail-visible；驗收用 `queue.jsonl` 無效）→ v2（改修 err 源頭）→ R2 反方（**匹配幾何脆弱**：loguru 80 欄會將 marker 斷開；且**今日响嘅唔止 err 一個原因**）→ v3（本檔）。

## 目標（一句）
令自我監測提示唔再因為「假陽性」而響；真事故照樣會響。

## 實錘（全部 Hermes 自己量，2026-09-22 17:2x）

### A. err 假陽性（100%）
- `serve.log`：**17,396 行**（universal-newline 定義；同一檔 `wc -l` = 17,074，差 320 個 bare CR —— 引用數字必須寫明定義）；`Traceback` **30 條**，用 ±8/12 視窗判定 **30/30 全部**屬 asyncio Windows proactor `handle: <Handle _ProactorBasePipeTransport._call_connection_lost()>` 良性 noise；非良性 **0**。
- `UnicodeDecodeError`／`stream_err` 全檔 **0**。
- 對照組（真事故類）：rotate 備份 `serve.log.bak-20260910.gz`（1,883,384 行、**373,175 條** Traceback，`alert.py IsWindowVisible` flood）抽 3,000 條 → 用同一 filter **false-mute 0.00%**。
- `self_monitor.log` 266 行 `err` 分佈：`0×199｜3×28｜2×13｜1×5｜4×3｜147×2｜398×2｜399×4`（max 399）。

### B. 第二個假陽性：`resp_lat > 5.0s` 條件係恆真
- `resp_lat` 觀測值（非 n/a，21 個樣本）：`6,6,8,8,8,9,9,12,12,14,14,17,17,18,18,18,23,26,26,47,47` → **最小值 6.0s > 門檻 5.0s** ⇒ 只要有語音活動就 100% 觸發。p90 = 26s。
- 今日 5 條 summary 之中，`err>0` **全部**成立；其中 08:29／08:49／09:05 同時 `resp_lat=8.0s`（兩個原因一齊響）；17:17（我手動跑）／17:22（重啟後 catch-up）只有 `err=2`。
- 响嘅紀錄：`alerts/miss_ledger.jsonl`（`kind=self-monitor`，全檔 40 行；今日 4 次：08:29 catch-up、08:49、09:05 每日、17:22 catch-up）。⚠️ **`queue.jsonl` 唔可以當證據**（poller 約 1 秒 ack，檔案長年 0 bytes）。
- ⚠️ 更正：**shadow ≠ 唔出聲**（`scripts/hermes_alert_speak_once.py:235-264` 記完決策照行 speak path）。

## 設計（單檔 `src/jarvis/self_monitor.py`，零新設定 key）
1. **err 良性過濾**（`:124-138` 計數段）：
   - `_BENIGN_TB_MARKERS = ("ProactorBasePipeTransport", "_call_connection_lost")`
   - 遇 `Traceback` 行 → 取 `lines[i-40 : i+40]`，**逐行 strip 後接成一個字串**再 substring（關鍵：loguru／rich 會硬換行，strip 拼接先可以還原被斷開嘅 marker）。
   - 命中 → **唔計 err**，改計 `benign_tb`；其他（任何真 exception、`UnicodeDecodeError`、`stream_err`）照計。
   - 已親驗：as-is **30/30** 過濾；同一批以 70 欄硬換行後仍然 **30/30**（幾何擾動下唔會靜靜失效）。
2. **`resp_lat` 門檻 `5.0 → 30.0`**（`:299`）：取實測 p90=26s 之上嘅整數；效果＝只有 47s 級別異常才出聲。註釋寫明「2026-09-22 實測 21 個樣本 p90=26s；舊門檻 5.0s < 樣本最小值 6.0s → 恆真」。
3. **fail-visible**：summary 加 `benign_tb=<n>`（吞咗幾多條，睇得見，跟 repo 既有 ⑭ 慣例；`_RE_KV` 食數字 ✓）。
4. 唔做：新設定 key（`save_settings` 係 `{**existing, **asdict(s)}` ＋ `settings_ui` 列舉式寫入 → 新 key 有被靜靜蓋回 default 嘅風險）；`dedupe_key`（`alert_dedupe_window_s=300`，跨日必不命中，唔係靜音機制）；policy／shadow／`_tune_threshold`（已凍結）。

## 驗收（逐條；R1／R2 flip condition 已納入）
1. `env -u PYTHONPATH <sidecar python> -m py_compile src/jarvis/*.py` RC=0
2. **新測試檔**（用**真 bytes fixture**，唔用合成字串）：
   - fixture 1＝由真 `serve.log` 抽嘅良性 block（原樣）；
   - fixture 2＝同一 block 以 70 欄硬換行（幾何擾動）；
   - fixture 3＝真事故樣本（由 rotate 備份抽 3 條，`alert.py IsWindowVisible` 類）；
   - 斷言：1→`err=0, benign_tb=2`；2→同樣 `err=0`；3→`err=3`（唔准被吞）。
   - **新測試檔要登記入 `eval_gate` 嘅 golden 清單**，否則永遠唔會跑（R2 反方指出）。
3. `pytest`（相關 + 新檔）全綠；`eval_gate --lock` 一致 RC=0；`eval_gate --suite golden` 跑埋新檔。
4. 真數據：跑 `run_once()` → 預期 `err=0`、`resp_lat=n/a`、`notable=False`（改前係 `err=2`）；`self_monitor.log` 新增一行做證據。
5. **Negative control（必要，唔可以省）**：同一份 fixture 清空 `_BENIGN_TB_MARKERS` → 必須回復 `err>0`／`notable=True`；再把 `resp_lat` 條件還原 5.0 → 用 fixture 4（`resp_lat=8.0s`）必須 `notable=True`。
6. Ledger 級（R1 flip condition）：重啟側車 → catch-up 窗（起動 +600s；實測 601–610s 內，**唔可以當 +600s 整**）→ 查 `miss_ledger.jsonl`：新窗內 `kind=self-monitor` 且 `event=enqueue` = **0**；同窗**正向對照**：手動 enqueue 一條 test alert 確認 ledger 寫得到（防「因為 ledger 壞而假綠」）。

## 風險／最壞／還原
- 影響面：一個檔、兩個條件；`err` 只放行一個窄 pattern（對 373,175 條歷史真 traceback false-mute 0.00%）；其他 metric／alert kind／policy 唔動。
- 最壞：a) 幾何再變 → strip 拼接＋擾動測試已覆蓋；b) 真事故長成同一個 asyncio pattern → 影響面只係「唔出聲」，`serve.log` 原文照留、`self_monitor.log` 照寫、HUD 可見；c) 遲滯失真 → `benign_tb=` 計數令吞咗幾多條仍然可見。
- 還原：**單檔未 commit 嘅 diff**（跟手先 commit；`git checkout -- src/jarvis/self_monitor.py` 或 revert 該 commit 即回現狀）。

## 唔准郁
wake 線（已停）／`_tune_threshold`（已凍結）／`alert_policy.POLICY`／`CRITICAL`／`speak_once` shadow 行為／`settings.json` 欄位集合／`alert_store` dedupe 行為。
