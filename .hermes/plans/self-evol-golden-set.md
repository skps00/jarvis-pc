# Self-Evol Golden Set（Task 7，Phase D 先決，R11）

> **Golden set = frozen + 人手標註 + agent 改唔到**。Eval Gate 用執行型驗證（跑 test/lint/語法/schema），**唔靠 LLM 自評**。
> 對應 machine mapping 喺 `src/jarvis/eval_gate.py`（`GOLDEN_SUITES`）——改呢份檔 + mapping 都要 SK 批准。
> 每次改動 eval 跑多次取統計結果（METR：同 prompt 多次 run variance 大）——`python -m jarvis.eval_gate --suite golden --repeat 3`。
> **紅線**：golden set 唔可以由 model output 刷新；升階（L0→L1）要求 golden 0 regression。

## 三類 eval

| 類別 | 目的 | 內容 | 對應測試 |
|---|---|---|---|
| **Golden tasks** | 核心能力不可退化 | 語音喚醒/路由/自我審視/Clarification Gate/autonomy/prompt pipeline/alert/Hands/self-evol 全部核心 module（**唔含 test_eval_gate.py——佢會 nested 重跑本 suite 做成 recursion**） | `test_alert_store.py`、`test_alert_tts_sink.py`、`test_alerts.py`、`test_app_index.py`、`test_autonomy.py`、`test_autostart.py`、`test_brain.py`、`test_clarify.py`、`test_clarify_stats.py`、`test_cursor_hooks.py`、`test_discover.py`、`test_gpu_health.py`、`test_hands_mc.py`、`test_hermes_bridge.py`、`test_hermes_trusted.py`、`test_prompt_pipeline.py`、`test_router.py`、`test_self_review.py`、`test_settings.py`、`test_shell_wake_restart.py`、`test_speaker_gate.py`、`test_wake.py` |
| **Failure regression** | 已修問題不可復發 | ISSUE-003 settings UI、MCP alerts HTTP 認證 | `test_settings_ui_smoke.py`、`test_mcp_alerts_http.py` |
| **Stress** | 壓力/對抗案例 | 大量合成數據、邊界條件、garbled 輸入、hysteresis/rate alarm | `test_self_review.py`（合成 7 日趨勢）、`test_autonomy.py`、`test_clarify.py` |

## 人手標註記錄

| 日期 | 標註人 | 項目 | 備註 |
|---|---|---|---|
| 2026-08-30 | SK (via Hermes) | Golden set 初版 | Task 7 建立；frozen |

## 使用

```bash
# 跑 golden suite（改動前後都要跑）
env -u PYTHONPATH "C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m jarvis.eval_gate --suite golden
# 全部三類
... -m jarvis.eval_gate --all
# 統計結果（R11）
... -m jarvis.eval_gate --suite golden --repeat 3
# 驗證 mapping 冇被改（immutable hash）
... -m jarvis.eval_gate --hash
```

> ⚠️ L1 自動 apply 開放前，eval suite 必須搬去 agent 寫入權限外嘅位置（immutable + hash 驗證）。而家 L0 人手 gate 保證。
