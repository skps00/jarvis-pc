# Prompt Patterns 庫（Task 8，Phase F，R13）

> Pattern 庫 = 離線 Optimizer 嘅產出。**只有分數證明先升格做正式 pattern**（唔由 LLM 自評驅動）。
> 每條記錄：適用場景 / 改前後 diff / 實測勝負（有分數證明）/ 失效條件。
> Machine 版本：`.hermes/plans/prompt-patterns.json`（PatternStore 管理）。
> 冇評分嘅任務唔入學習 loop（R13）。

## 規則

- Pattern 由「驗收標準自動評分」驅動：分數提升先收錄（`PatternStore.add` min_score=0.8）
- 優化器冇工具權限、冇網絡權限（純 text→text）；安全約束 INVARIANT_BLOCK 由系統注入，優化器無權改寫
- 每次優化記錄「優化器所見輸入」+「輸出」做 replay 審計；敏感模式命中 → 降級原版 + 記 log
- Instruction hierarchy：system > user > 優化輸出

## Patterns

<!-- 只有 score-backed 先寫入呢度 + prompt-patterns.json -->
（未有——等 L2 Optimizer 上線後由分數驅動填充）
