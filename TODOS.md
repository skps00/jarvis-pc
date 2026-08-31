# TODOS

> 合併來源：JARVIS_MASTER_PLAN.md + Cursor tasks + 歷史 session 未完項（2026-08-28）。
> 狀態圖例：✅ 完成 ｜ 🔄 進行中 ｜ ⏳ 排期 ｜ 📌 已確認決定 ｜ 💤 deferred ｜ 🟡 做咗未驗證

---

## JARVIS 主線（master plan 剩餘）

### 🟡 A4 — Speaker gate 收尾（做咗，未真正可用）

- **What:** ECAPA-TDNN 聲紋——係 SK 嗌先醒。Code 已完成（`speaker_gate.py` + wake 整合 + `verify_voice.py` + tests），serve 顯示 `spk_gate ready dev=cuda:0 thr=0.5`。
- **Blocked by:** ⚠️ **cross-mic 問題** — enrollment 用 Arctis（`wake_mic_device=2`）、測試樣本用 Sonar → cosine 得 0.13-0.38（threshold 0.5）。同 mic 同人應 0.6+。
- **Next:** SK 用 Arctis 錄 ~30s 重新 enrollment（`scripts/enroll_voice.py`）→ `verify_voice.py` 驗證 → threshold 微調。
- **Status:** 🟡 等 SK re-enrollment

### ⏳ AEC（voice call 安全）

- **What:** WebRTC AEC3 濾走 voice call 對方聲；pycaw 已裝；speexdsp fallback。
- **Why:** SK 會用 Discord/WhatsApp voice chat——通話中 JARVIS 絕不可出聲（對方聽到）或因對方聲誤觸。
- **Status:** ⏳ 未做（spike 測試 `python-webrtc-audio-processing` 裝唔裝到）

### ⏳ Streaming TTS

- **What:** Hermes 流式輸出 + JARVIS 逐句唸（首句 1-2s 出聲，唔使等成段）。
- **Status:** ⏳ 未做

### ⏳ 狀態檢測 daemon（秒級）

- **What:** cron 最細分鐘 → 自己寫秒級 daemon（滑鼠移動 + 遊戲進程實時判斷）。
- **Status:** ⏳ 未做

### ⏳ Context → JARVIS 管道（master plan 缺口 #1）

- **What:** sk_activity.json / sensors（NVML）feed 入 JARVIS，令佢「睇情況俾意見」。
- **Status:** ⏳ 未做

### 🔄 JARVIS ONE（Phase 8）— 前台一體化

- **What:** voice + HUD + 管理整合一個 Electron app + Python sidecar、一個 tray 全背景、MCP 雙向整合 Hermes。
- **已做:** jarvis-alerts MCP@8765 已註冊；HUD 已有。
- **Status:** 🔄 進行中（master plan=`.hermes/plans/JARVIS_MASTER_PLAN.md`）

### ⏳ Proactive 機制

- **What:** 點樣「根據情況主動俾意見」而唔 spam（throttle/優先度）。
- **Status:** ⏳ 未做

### ⏳ 喚醒詞重訓

- **What:** 210/1000 樣本，欠 790。低優先（語音主線落地後先有意義）。
- **Status:** ⏳ 低優先

### ⏳ C: 碟 91% 滿

- **Status:** ⏳ 低優先（背景健康）

### ⏳ CPU 溫度 N/A

- **What:** WMI 讀唔到 9950X3D 溫度。
- **Status:** ⏳ 低優先

---

## Follow-up: Hermes push / notify (cut alert latency)

- **What:** After AlertStore enqueue, actively push Hermes (webhook / gateway hook) instead of relying only on 1s poll.
- **Why:** Design premise — faster speak while keeping Hermes TTS; poll already 1s, push can go sub-second.
- **Pros:** Lower end-to-end latency for GPU/safety pings.
- **Cons:** Needs Hermes API spike; dual path (push + poll fallback) complexity.
- **Context:** After speak-path harden (`alert_tts=hermes` → Hermes TTS only + Windows-safe timeout/taskkill).
- **Depends on / blocked by:** Stable hermes alert_tts path (T1/T2 from eng-review).
- **Status:** deferred
- **Added:** 2026-08-12 via /plan-eng-review (D13 A)

## Follow-up: GPU-Z failover deep backend

- **What:** `GpuzBackend` (CSV log and/or shared memory) as failover when `sensor_deep_reader` is not HWiNFO; never run concurrent with HWiNFO deep read.
- **Why:** Design solid-line third adapter; recovery if HWiNFO unavailable.
- **Pros:** Completes SensorBackend matrix from approved design.
- **Cons:** Fragile parsing; deep-reader conflict with HWiNFO; GUI residency.
- **Context:** After HWiNFO SHM lands; NVML remains always-on for GPU core metrics.
- **Depends on / blocked by:** HWiNFO backend TODO.
- **Status:** deferred
- **Added:** 2026-08-12 via /plan-eng-review (D12 A+)

## Follow-up: Minecraft / Prism ready alert

- **What:** Detect Prism/Minecraft ready (window title and/or log) → short stub `"Minecraft is ready."` → AlertStore → Hermes; cooldown against load spam.
- **Why:** Design P1 wow after P0 5090 safety; battlefield butler ping.
- **Pros:** Clear demo moment; reuses alerts bus.
- **Cons:** Brittle title/log signals; false ready during loading.
- **Context:** Sensor platform design APPROVED; ship after GPU health NVML + Hermes speak path harden.
- **Depends on / blocked by:** Stable hermes alert_tts path.
- **Status:** deferred
- **Added:** 2026-08-12 via /plan-eng-review

## Follow-up: HWiNFO shared-memory backend (CPU + optional 5090 hotspot)

- **What:** `HwinfoShmBackend` — CPU package temp/power/fans; optional experimental RTX 50 hotspot; `sensor_deep_reader=hwinfo` mutually exclusive with GPU-Z deep read.
- **Why:** Approved sensor-platform design (B+C); P0 ships NVML/smi GPU only.
- **Pros:** Real CPU thermals; optional hotspot for 5090 safety story.
- **Cons:** Requires HWiNFO running; free Shared Memory ~12h limit; sensor name calibration.
- **Context:** `~/.gstack/projects/jarvis-pc/skps9-feature-hermes-alerts-mcp-design-20260811-222632.md`. After dynamic gpu_health + Hermes-only speak path land.
- **Depends on / blocked by:** P0 NVML + speak-path + timeout fixes stable.
- **Status:** deferred
- **Added:** 2026-08-12 via /plan-eng-review

## Follow-up: screen/UIA “what did they say?”

- **What:** After a short alert ping, let the user ask Hermes what the message said; Hermes reads the visible chat UI via UIA/OCR (never auto-include body in the ping).
- **Why:** Approved design trajectory (office-hours A+C): butler ping now, conversational follow-up later.
- **Pros:** Feels like real Jarvis; keeps privacy default (no body in auto alerts).
- **Cons:** Fragile per-app UI; privacy-sensitive; large scope vs alerts MCP.
- **Context:** Premises in `~/.gstack/projects/jarvis-pc/skps9-main-design-20260809-094222.md`. Auto path must stay phrase-only. Platform API/bot pull is a separate later track (Hermes gateway).
- **Depends on / blocked by:** Alerts HTTP MCP + Hermes TTS path shipping and stable.
- **Status:** deferred

## Follow-up: remote Hermes → Windows alerts MCP

- **What:** Document and support reaching the Windows localhost HTTP alerts MCP from a Hermes instance on another machine via VPN or SSH tunnel (never raw public port-forward).
- **Why:** User may run Hermes 24/7 on a second PC; watcher/eyes must stay on the Discord/WhatsApp desktop.
- **Pros:** Matches long-term topology; keeps bind on 127.0.0.1.
- **Cons:** Ops complexity; auth token + tunnel must be maintained.
- **Context:** Eng review locked HTTP MCP on loopback + token. Design premise 6.
- **Depends on / blocked by:** Local alerts HTTP MCP working with Windows native Hermes.
- **Status:** deferred
