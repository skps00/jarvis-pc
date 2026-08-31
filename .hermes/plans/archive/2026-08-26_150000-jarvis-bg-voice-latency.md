# Jarvis 背景常駐語音 + 延遲優化 Implementation Plan

**Goal:** 讓 JARVIS 語音助手成為「背景常駐、喊 hey jarvis 就回應、回應快」（文字中文 + 語音英文）的可靠載體，取代脆弱的 Hermes chat 語音。

**Architecture:** 用 Jarvis app（`jarvis serve` companion）作為語音載體——它已內建 wake + STT + Hermes bridge + SPEAK（文字中文/語音英文）。本計畫：① 啟動 serve（背景常駐+開機自啟）→ ② 優化延遲（barge-in + streaming TTS）。

**Tech Stack:** Python 3.14, piper TTS, sensevoice STT, hey_jarvis wake, Hermes bridge (API 8642), mycroft MCP。

---

## Phase 0 — 背景（先確認 Hermes gateway 就緒）

- [ ] 確認 Hermes gateway 在跑（`hermes gateway start`）
- [ ] 確認 `hermes_api.key` 存在（Jarvis ↔ Hermes bridge 驗證）
- [ ] 確認 jarvis-pc 的 `src` 在 PYTHONPATH（JARVIS.vbs 已設）

## Phase 1 — 啟動 Jarvis serve [主目標]

**Objective:** 背景常駐語音助手就緒（wake「hey jarvis」→ 對話 → SPEAK 英文唸）。

**Files:**
- Run: `JARVIS.vbs`（無 console 背景跑 `pythonw -m jarvis serve`）
- Create: 開機自啟捷徑 → `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\JARVIS.lnk`

**Steps:**
1. 啟動 `pythonw -m jarvis serve`（JARVIS.vbs 方式）→ 確認 tray/alert poller 跑（2 個 pythonw）
2. 驗證 wake 監聽「hey jarvis」（`wake_mic_device=2`, threshold 0.41）
3. **開機自啟**：複製 JARVIS.vbs 的 `.lnk` 到 Startup（或註冊排程）
4. **加「遊戲中不醒」規則**（activity-aware）：
   - Jarvis wake 觸發前 → 讀 `C:\Users\skps9\AppData\Local\hermes\state\sk_activity.json`
   - `state == playing`（CS2/MC 等）→ **不觸發 wake / 不回應語音**（靜音）
   - `state == idle/using` → 正常監聽回應
5. 喊「hey jarvis 現在幾點」→ 確認：wake 亮 → STT → Hermes → **SPEAK 英文唸**（"It's 4:30 PM, Sir."）

**驗證：** `wmic process where "name='pythonw.exe'" get commandline | grep "jarvis serve"`（≥1 進程）；實際喊話測 SPEAK 英文；**開 CS2 → 喊話 → 應無回應（遊戲中不醒）**。

## Phase 2 — barge-in（說話打斷）[確定做]（VAD-based + Echo Prevention）

**Objective:** 說話立即中斷（用 VAD 而非純音量——更準、更有效）。

**Files:**
- Modify: `src/jarvis/engine.py:execute_utterance`（播放時段）
- Modify: `src/jarvis/mouth.py`（加 `stop_play()` / 播放可中斷）
- Modify: `src/jarvis/ear.py`（Silero VAD 層——speech 播放時偵測說話→中斷）

**Approach（最佳實踐）:**
1. **Silero VAD**（streaming、更準）——偵測你說話（音量 + 語音特徵，比純 RMS 準）
2. **barge-in**：speech 播放中 VAD 檢出「有人說話」→ `mouth.stop_play()`
3. **⛔Echo Prevention（關鍵）**：TTS 播放期間**暫停 VAD 偵測**（避免 Jarvis 聽到自己唸的聲音誤觸中斷）——只在 TTS 結束後恢復 VAD
4. 閾值：Silero VAD 阈值 + 持續 ≥300ms

**驗證：** 唸長句時說話 → 立即停止（且 TTS 自身不誤觸）。

## Phase 3 — streaming TTS（邊生成邊唸）[延遲優化]

**Objective:** LLM 一回覆開始就唸，不等完整生成＋整段合成（省 1-2s）。

**Files:**
- Modify: `src/jarvis/mouth.py:speak`（逐 chunk 合成→播放，而非整段）
- Modify: `src/jarvis/hermes_bridge.py`（若 streaming 回覆，先給開頭再補）

**Approach:**
1. **先唸短句確認**：LLM 回覆一出，立即唸「Yes, Sir.」（~0.6s 感知延遲最低）
2. **streaming TTS**：正式 SPEAK 逐 chunk 合成播放（mouth queue、chunk 依序餵）——不倒等整段
3. **streaming LLM**：Hermes bridge 用 streaming token（首 token 盡快出）→ 越早唸
4. **(可選) streaming STT**：sensevoice/faster-whisper 邊說邊轉（更早辨識）
5. **並行**：TTS 合成跟 LLM 生成重疊（不等完整）

**驗證：** 回應「說話前延遲」明顯縮短（首個音節更快出現）。

## Phase 4 — 回覆語言確認

**Objective:** 語音英文、文字中文（SPEAK 機制）。

**Files:** 無改動（Hermes prompt 已強制 `SPEAK: <English>`；mouth 僅唸 spoken）。

**驗證：** 喊話 → 螢幕中文主文 + 語音英文。

---

## 風險／tradeoffs

- **barge-in**：誤觸發風險（環境噪音）——需較高閾值；會改 ear/engine（謹慎測試）。
- **streaming TTS**：piper 逐 chunk 音質/節奏可能略變；改 mouth 較深。
- **serve 常駐**：佔 RAM（~數百 MB）＋每次開機自啟（SK 本就要常駐語音）。
- **優先順序**：先 Phase 1（啟動 serve＝語音就緒，立即有效）→ Phase 2/3（延遲優化，較深改動）。

## 已確認決定（SK）

1. **Phase 2/3（barge-in + streaming）現在就做** ✅
2. **加「遊戲中不醒」規則**（activity-aware，Phase 1 step 4）✅
3. **接受 serve 常駐佔記憶體** ✅

## Open Questions（已決定 by SJ/agent）

1. **barge-in 閾值**：**音量突增（RMS > -20dB）+ 持續 ≥300ms → 中斷**（mouth.stop_play()）。保守閾值避免環境聲誤觸；若誤觸再調。
2. **遊戲判定**：用 `sk_activity.json`（activity_monitor.py 每分鐘寫）✅
3. **streaming 做法**：**「先唸短句確認」+「逐 chunk 串流 SPEAK」**——LLM 回覆一出開頭，先唸「Yes, Sir.」立即回饋（~0.6s），同時正式 SPEAK 依 chunk 合成播放（mouth 播放用 queue，chunk 依序餵）。

## Phase 5 — GUI 重做（Iron Man 風格）[較大工程，可後續]

**Objective:** Jarvis 的 companion/設定視窗從 tkinter（老氣）改成 Iron Man 風格（webview + HTML，跟 HUD 一致）。

**Files:**
- Modify: `src/jarvis/shell_app.py`（companion 主視窗 → pywebview 載入 Iron Man HTML）
- Modify: `src/jarvis/settings_ui.py`（設定視窗 → webview Iron Man）
- Create: `src/jarvis/ui/assets/*.html`（Iron Man 藍色 #00aaf8、透明、科技感 UI）
- Create: Django/pywebview 橋接（Python↔JS 事件）

**Approach:**
1. 用 **pywebview**（or 簡易 local HTML server）+ 載入 Iron Man HTML
2. 視窗：companion（聊天/狀態）、settings（設定分頁）——同 HUD 視覺語言
3. tray 保留（pystray/win tray——系統功能不改）
4. 事件橋接：Python `webview.py` → JS（狀態/提醒 push）；JS → Python（設定/指令）

**驗證：** 開啟 companion/settings 視窗 → Iron Man 藍色科技感、透明、無 tkinter 老氣感。

**風險：** GUI 框架重寫（tkinter→webview）是大工程；travers 保留但視窗橋接需重做。**建議：** 先完成 Phase 1-4（語音就緒+延遲），Phase 5 獨立排期。

## Files likely to change
- `JARVIS.vbs`（已存在，複製做 Startup）— 不用改
- `src/jarvis/engine.py`（barge-in）
- `src/jarvis/mouth.py`（stop_play + streaming）
- `src/jarvis/ear.py`（interrupt 偵測）

---

## Phase 6 — Wake/STT/Response 品質改善（2026-08-27 SK 確認，優先於 Phase 5）

**Objective:** 解決三個實際痛點：① wake 誤觸/叫唔醒 ② STT 慢/錯字多 ③ response 出聲太慢。基於官方文檔（openwakeword `vad_threshold`、faster-whisper CTranslate2 基準）實測診斷。

**診斷結果（2026-08-27）：**
- **Wake**：openwakeword 冇用 `vad_threshold`（官方內置 Silero VAD 過濾）→ YouTube BGM/遊戲聲誤觸。
- **STT**：SenseVoiceSmall 純 CPU（`ear.py` 冇 `device` 設定），RTX 5090 閒置（5% util）→ 慢。
- **TTS**：`mouth.speak` 一次過 `synthesize(整句)` 先播放——Phase 3 講嘅 streaming 未實現 → 出聲慢。

### Step A — Wake 防誤觸（vad_threshold）
- **Files:** Modify: `src/jarvis/wake.py`（`_load_model()` / `run_wake_loop()`）
- **做法:** openwakeword 官方內置 Silero VAD：`Model(... , vad_threshold=0.5)`——非語音噪音（BGM/鍵盤）唔會觸發。
- **驗證:** 開 YouTube BGM 唔應誤觸；正常喊「hey jarvis」應照醒。
- **風險:** 低（官方參數）；若 VAD 太嚴令叫唔醒，調低 vad_threshold（0.3-0.5）或只喺 noise 大時啟用。

### Step B — STT GPU 加速
- **Files:** Modify: `src/jarvis/ear.py`（`_get_sensevoice()` / `_get_fun_asr()`）
- **做法:** FunASR `AutoModel(..., device="cuda:0")`（torch.cuda 可用時），CPU 兜底。
- **驗證:** `transcribe_wav` 耗時 CPU vs GPU 對比（預期 3-10x 快）。
- **風險:** 中——funasr CUDA 相容性要實測；`onnxruntime` 路徑（mouth）不受影響；唔得就 fallback CPU。
- **註:** 若 SenseVoice GPU 版唔順，替代 = faster-whisper int8（CTranslate2，CPU 都快 4x，官方基準 59s→16s batch）。

### Step D1 — Streaming TTS（mouth 逐 chunk 即播）
- **Files:** Modify: `src/jarvis/mouth.py`（`speak()`）
- **做法:** Piper `voice.synthesize` 本身係 generator——逐 chunk `audio_int16_bytes` 邊出邊餵播放器（queue），唔再 `b"".join` 等成句。
- **驗證:** 長句首音節出現時間明顯提早。
- **風險:** 中——chunk 邊界音質/節奏可能略變；播放器要支援 stream（sounddevice OutputStream）。

### Step D2 — 先唸短句確認（感知延遲最低）
- **Files:** Modify: `src/jarvis/shell_app.py`（reply handler）
- **做法:** LLM 回覆一出，先唸「Yes, Sir.」（~0.6s）立即回饋，同時正式 SPEAK 依序播放（queue）。
- **驗證:** 喊話後 ~1s 內有聲（唔使等成段）。
- **風險:** 低——若覺得煩可以加開關（settings `tts_ack`）。

### Step D3 — 縮短「等講完」時間
- **Files:** Modify: `src/jarvis/wake.py`（`_CMD_SILENCE_FRAMES` / `_STT_TRAIL_S`）
- **做法:** `_CMD_SILENCE_FRAMES` 8→5（~400ms 靜音即收）、`_STT_TRAIL_S` 0.5→0.35。每句慳 ~300ms。
- **驗證:** 講完 → STT 開始更快；正常句尾唔會 cut 斷。
- **風險:** 中——太短會喺句中停頓誤判收工。實測後若斷句就還原或微調。

### 驗證總結（Phase 6 完成指標）
1. 開 YouTube BGM 30 秒 → 0 誤觸。
2. `transcribe_wav` GPU vs CPU：快 ≥3x。
3. 喊「hey jarvis 現在幾點」→ 由喊完到有聲 ≤3s（目標 2s）。

### Files likely to change (Phase 6)
- `src/jarvis/wake.py`（vad_threshold + silence/trail）
- `src/jarvis/ear.py`（cuda device）
- `src/jarvis/mouth.py`（streaming chunks）
- `src/jarvis/shell_app.py`（ack stub）
