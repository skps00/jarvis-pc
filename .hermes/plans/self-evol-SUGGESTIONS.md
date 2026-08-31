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
