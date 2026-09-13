# Self-Evol 建議清單（SUGGESTIONS）

> Self-Evol Phase B 產物（Task 4，2026-08-30）。**append-only**：每日審視 agent 有新 finding 就加一條，唔好改舊條目（R15：brevity bias 會壓縮知識）。
> 每條建議 = `[id] 問題 → 建議 → 風險 → 驗證方法 → 回滾方法`（R5：可 diff、可 revert）。
> 標記：🟡 待 SK / ✅ 批准 / ❌ 拒絕。執行後 update 狀態 + 記低效果（C1 月報用）。
> 呢個係內部記錄，**唔係**俾 SK 睇嘅報告——SK 睇嘅係 A0 人話格式（Discord）。

## 規則

- finding 一律帶 provenance（來源 log + trust level）；untrusted content（語音誤聽等）唔可以入 verified 區（R16）
- 每條建議要可回滾：寫明「點還原」
- 「真實語音指令完成率」係主要 signal（R3），唔好用「建議被採納率」
- 大部分建議會失敗係正常（R8：Karpathy 700 實驗得 20 真改進）——統計顯著先接受

## 建議

<!-- 新建議 append 落呢度，格式：
[ID] 問題：... → 建議：... → 風險：... → 驗證：... → 回滾：...
狀態：🟡 待 SK
-->

[TREND-err-2026-08-31] 問題：serve.log 錯誤行連續 3 日上升（0→1→3；主因=SenseVoice 子程序輸出 GBK 中文 bytes，subprocess _readerthread 以 UTF-8 解碼失敗 → UnicodeDecodeError；次因=啟動時 jarvis-alerts-mcp thread 有一次 traceback，非致命）→ 建議：subprocess stdout 解碼加 errors="replace"（或 GBK fallback），順手排查 alerts-mcp 啟動 traceback；低優先，隨下次 sidecar 改動一齊做 → 風險：吞咗真錯誤（日誌診斷能力略降）；低 → 驗證：修後連續 3 日 err=0 且 serve.log 無 UnicodeDecodeError → 回滾：git revert 解碼參數改動
狀態：✅ 已修（2026-08-31 下午「fix them all」session：8 個 subprocess 位加 encoding="utf-8", errors="replace"；test_router warning 清零；詳見 REMAINING_WORK 資源優化 section）

[TREND-err-2026-09-05] 問題：serve.log 由 2026-09-04 ~11:18（sidecar 重啟 + SenseVoice 重新下載之後）開始狂錄同一 exception——`Exception ignored while calling ctypes callback ... src/jarvis/alerts.py:292 _enum ... ctypes.ArgumentError: int too long to convert`（即 _list_windows_for_pids 嘅 EnumWindows callback 入面 `user32.IsWindowVisible(hwnd)`）。09-05 08:59 起 monitor err 暴升（[2,3,399]）；實測 ~54 次/min 持續中，累計 22,600+ 次，serve.log 脹到 9.4MB。根因：alerts.py 冇為 user32 函數宣告 argtypes → ctypes 預設 c_int 轉換 → 64-bit hwnd（>2^31，EnumWindows 遇到第一個大 handle 視窗就 abort）overflow。受影響 callers：alerts.py:1026 _tick_discord（Discord 未讀偵測）、:1101 _tick_cursor（Cursor busy/approval 偵測）→ titles 空/斷 → 呢類自動提醒可能漏；alert 播報 queue 本身冇 backlog（queue 0）、wake/STT/TTS 正常 → 建議：喺 alerts.py 模組層為 user32（IsWindowVisible/GetWindowTextLengthW/GetWindowTextW/GetWindowThreadProcessId/EnumWindows）宣告 argtypes/restype（HWND 用 wintypes.HWND），細 fix 低風險；code 改動須經 cursor-agent（SK 規則）→ 風險：若只喺 caller 包 try/except 冇用（callback 照 abort EnumWindows）；argtypes 純宣告無 side effect → 驗證：修後連續 3 日 err=0 且 serve.log 無新增 ctypes exception；Discord unread / Cursor busy 警報回復正常 → 回滾：git revert argtypes 改動 + 重啟 sidecar（kill 8765 python → Electron respawn ~90s）。註：舊 err issue（2026-08-31 subprocess UTF-8 decode）已修，呢個係另一 root cause
狀態：🟡 待 SK（2026-09-05 cron 發現；同日 append）
解決（2026-09-11 cron 核實）：✅ 已修已生效——`1bdac68`（2026-09-09 22:42 本地 commit）→ SK 09-10 晚上批准重啟 → sidecar 09-10 23:4x 由 Electron 自動 respawn → 09-11 05:45 實錘：`/health` = `{"ok":true,"wake_on":true}`、`serve.log` 27KB、`int too long to convert` = 0（舊 136MB／370,905 次）。serve.log 已 truncate（備份 `serve.log.bak-20260910.gz`）。Discord unread / Cursor busy 偵測回復正常（parse 不再 abort）。

[TREND-err-2026-09-06] 問題：ctypes ArgumentError 洪水未停——serve.log 09-06 ~09:00 已 32.9MB、累計 83,988 次「int too long to convert」、09:02 仍在寫入（昨日條目記 9.4MB）；但 self_review.json（09-06 09:00:57）報 trends.err=false / findings=[]，即「無 finding」係誤報，唔係真復原。根因：detect_trend 要求 metric 連續 3 日嚴格單調變差（lower_better 即每日 v>prev）；err 09-05=399 → 09-06=398（<1% noise）已令 counter reset（degraded=1→0，需 ≥2 先 flag），而絕對水平仍係 baseline（~1-3）嘅 ~130 倍 → step-change + plateau 場景監控會長期靜音，直到再出現連續上升先會再報。→ 建議：① 執行 TREND-err-2026-09-05 嘅 alerts.py user32 argtypes fix（主因，仍 🟡 待 SK）；② detect_trend 加 sustained-high 規則：metric 連續 ≥2 日遠超 baseline（如 >10x 中位數）都出 finding，唔好只靠單調遞增先報。→ 風險：baseline/threshold 設定差會 noise 或漏報；低（detector 改動只影響 finding 產生，唔郁 runtime）。→ 驗證：fix 後 err 連續 ≥3 日 ≤3 且 serve.log 無新增 ctypes exception；detector 喺 plateau 場景仍能出 finding。→ 回滾：git revert argtypes 改動 + 重啟 sidecar（kill 8765 python → Electron respawn ~90s）；detect_trend 改動可獨立 revert。
狀態：🟡 待 SK（2026-09-06 cron 發現；同日 append，補充 TREND-err-2026-09-05）
解決（2026-09-11 cron 核實）：① ✅ 已修（同上條，`1bdac68` 已生效）；② **detect_trend sustained-high 規則仍未做**——低優先，未經 SK 拍板，記入 HANDOFF「剩低」。

[TREND-err-2026-09-10] 問題：ctypes ArgumentError 洪水仍然活躍，而且 fix 未生效——serve.log 09-10 09:00 = 87.8MB（09-05 9.4MB → 09-06 32.9MB → 今日 87.8MB），累計 `int too long to convert` 232,011 次；實測 12 秒 +7,000 bytes（~35KB/min），即刻仍在寫。修復 commit `1bdac68`（2026-09-09 22:42，本地未 push）**未生效**：sidecar PID 24992 由 09-09 10:36 起一直冇重啟（早過 commit ~12 小時）→ 載入緊舊版 alerts.py。旁證：serve.log traceback 報 `alerts.py:292 in _enum`，但 on-disk 292 行而家係另一個函數（Python traceback 由 on-disk 源碼取行，唔匹配 = running bytecode ≠ disk code）。影響（自 09-04 起）：EnumWindows 中途 abort → `_list_windows_for_pids` 回空 → Discord 未讀偵測 + Cursor busy/approval 偵測仍然斷。注意：Electron host 正常運行（JARVIS ONE PIDs 35552/40292/41184/43336），所以 kill sidecar 會自動 respawn；但 HANDOFF 記「等 SK 話事 push／sidecar restart 生效」，即重啟係故意 deferred，唔應由 cron agent 自行執行。→ 建議：① SK go 後 kill PID 24992（Electron respawn ~90s）令 fix 生效；② push `1bdac68` 上 GitHub；③ 順手 archive + truncate serve.log（88MB；磁碟 291G free，唔急，但影響 log 診斷 + self_monitor 每朝要掃全檔）。→ 風險：restart 期間 ~90s 冇 wake/STT/TTS/alert（SK 09:00 喺 MC playing，語音影響低）；truncate 前唔備份會失診斷資料；低。→ 驗證：restart 後 5 分鐘 serve.log 增長 = 0（或 <1KB/min）且無新增 `int too long to convert`；連續 3 日 self_monitor err ≤3；Discord 未讀 / Cursor busy alert 各實測觸發一次。→ 回滾：`git revert 1bdac68` + 重啟 sidecar（kill 8765 python → Electron respawn ~90s）；log truncate 前備份 `.gz` 可還原。
狀態：🟡 待 SK（2026-09-10 cron 發現；同日 append，前接 TREND-err-2026-09-06）
解決（2026-09-11 cron 核實）：✅ 三項建議全部落地——① sidecar 已重啟（09-10 23:4x，Electron 自動 respawn；`/health` ok）；② `1bdac68` 已 push 上 GitHub（09-10 20:37 確認 origin 已含）；③ serve.log 已 archive + truncate（09-10 23:41；`serve.log.bak-20260910.gz` 977KB；現時 serve.log 27KB）。驗證條件（restart 後無新增 `int too long to convert`）**已 PASS**：09-11 05:45 grep = 0。連續 3 日 err ≤3 嘅長期驗證交給 daily self-review cron 自然觀察。

[TREND-err-closeout-2026-09-11] 問題：無（閉環記錄，非新 finding）→ 觀察：self_review.json（09-11 09:00:35）trends fp/stt_rtf/stt_miss/err 全 false、findings=[]；self_monitor err 連續 3 個讀數 = 0（09-10 23:51、09-11 03:09、09-11 09:00）；serve.log 39.6KB、`int too long to convert` grep = 0（舊值 88MB／232,011 次）。monitor fingerprint 由「FINDING err degraded 3 日 [147.0,185.0,399.0]」變回 NONE——改善令單調遞增 counter reset，屬 detector 預期行為（同 TREND-err-2026-09-06 ② 同一機制，反向）。→ 建議：無需動作；TREND-err-2026-09-05/06/10 由「長期驗證」轉為自然觀察（err 再升 detector 會再出 finding）。→ 風險：無。→ 驗證：連續 ≥3 日 err ≤3（現時只 ~1 日，未算成立，續由 daily self-review 觀察）。→ 回滾：n/a（純記錄）。
狀態：✅ 已核實（2026-09-11 cron；SK 無需動作 → 本日不發報告，[SILENT]）
