# JARVIS Master Plan（jarvis-pc + jarvis-hud 全項目）

> 合併來源（2026-08-27）：`.hermes/plans/2026-08-26_150000-jarvis-bg-voice-latency.md`、`TODOS.md`、`REMINDERS.md`、`docs/train_wake_jarvis.md`、jarvis-hud 現況。
> **原則：** 先查再動 → 測試先行 → 每步驗證；重大改動先出計畫確認（SK 規則）。
> 狀態圖例：✅ 完成 ｜ 🔄 進行中 ｜ ⏳ 排期 ｜ 📌 已確認決定 ｜ 💤 deferred

---

## 🏆 終極願景（SK 2026-08-27 明示）——全方位 AI 協作夥伴

> **「唔應該係管家。佢嘅身份包括但並不限於：幫助我研發、code、俾 idea……一個全方位嘅 AI 協作夥伴。甚至可以根據我面對緊嘅情況去俾我唔同嘅意見。」**

### 身份定義（唔係僕人式管家）

| 管家（✗ 唔啱） | 協作夥伴（✓ 目標） |
|---|---|
| 等指令、執行命令 | 主動參與、俾建議 |
| 你問先答 | 根據你嘅 context 主動俾意見 |
| 只做你講嘅嘢 | 一齊諗、一齊做、互補 |
| 單一角色 | 多面：研發 / code / idea / 日常 / 娛樂 |

**核心特質：proactive（主動）+ collaborative（協作）+ contextual（睇情況俾意見）。**

### 目標形態

```
                SK（用戶）
                 │  自然對話（voice / HUD / Discord / 任何入口）
                 ▼
        ┌─────────────────────────┐
        │  JARVIS（AI 協作夥伴）   │
        │  ─ 理解你而家做緊咩     │  ← context awareness
        │  ─ 主動俾意見/建議      │  ← proactive
        │  ─ 一齊研發/code/諗嘢   │  ← collaborative
        │  ─ 管理手下 agents      │  ← orchestration（仍然需要）
        └───────┬─────────────────┘
                │ 需要時調度
     ┌──────────┼──────────┐
     ▼          ▼          ▼
  Hermes    Claude Code   Codex / OpenCode / Cursor
  （核心推理）  （程式碼工人） （專才）
```

### 協作夥伴嘅關鍵能力（vs 管家）

1. **Context awareness（感知你嘅處境）**——知你開緊咩 app、打緊咩 game、寫緊咩 code、GPU 幾熱：
   - 已有：`sk_activity.json`（foreground/activity）、sensors（NVML）
   - 要做：呢啲 context 要 feed 入 JARVIS，令佢識得「睇情況俾意見」
2. **Proactive（主動）**——唔止等指令：
   - 你 GPU 過熱 → 主動提議
   - 你 code 有 pattern → 主動建議 refactor
   - 你 idle 咗 → 主動問「要唔要幫手」
3. **Multi-agent orchestration（管理手下）**——需要時自動調度 Claude Code/Codex，唔使你理
4. **多入口**——voice / HUD / Discord 都得，一個身份

### 而家已有嘅基建（✅）

| 基建 | 現狀 | 夥伴角色 |
|---|---|---|
| **Hermes（我）** | ✅ 完整 agent | 夥伴大腦：理解、推理、協作 |
| **Context 感知** | ✅ `sk_activity.json` + activity_monitor | 知你喺做咩（要 feed 入 JARVIS） |
| **Sensors** | ✅ NVML GPU 健康 | 知你部機狀態 |
| **delegate/cron/kanban** | ✅ | 需要時調度手下 |
| **Jarvis（voice）** | ✅ wake/STT/TTS | 把聲（voice 入口） |
| **HUD** | ✅ Iron Man overlay | 視覺（HUD 入口） |
| **WeSight** | ✅ 工作區 | 桌面整合 |

### 缺口（要做先成事）

1. **Context → JARVIS 管道**——SK 做緊咩要入 JARVIS 知（foreground/activity/sensors → HUD/voice 顯示 + 俾意見）
2. **前台一體化**——voice + HUD + 管理整合一個入口 → **Phase 8 JARVIS ONE**
3. **MCP 雙向整合**——Hermes ⇄ JARVIS 結構化互通 → **Phase 8 Step 8.5**
4. **Proactive 機制**——點樣「根據情況主動俾意見」而唔係 spam（要 throttle/優先度）

### 關鍵 insight（2026-08-27 實測）

- **協作夥伴大腦已經存在**——Hermes 本身就係（推理/記憶/技能/工具齊）。
- **Context 源已有**——`sk_activity.json` + sensors + gateway，只係要接埋。
- **Jarvis MCP server 已存在**（8765）——加 tools 即打通。
- 所以願景可行性 = **整合 + 加 proactive 層**，唔係由零起樓。

---

## 📦 項目總覽

| 子項目 | 路徑 | 狀態 |
|---|---|---|
| Jarvis 語音助手（serve/wake/STT/TTS） | `jarvis-pc` | ✅ 基礎完成，🔄 品質改善中 |
| JARVIS HUD（Iron Man 視覺 overlay + dock） | `jarvis-hud` | ✅ v0.1 運行中，⏳ 後續增強 |
| Chrome Media Bridge（YouTube 控制） | `jarvis-hud/chrome-extension` | ✅ 運行中（8771） |
| Hermes 整合（bridge API 8642 / SPEAK） | `jarvis-pc/src/jarvis/hermes_bridge.py` | ✅ 完成 |

---

## 🎯 MVP 分層（2026-08-27 14-POV review 加入——防 scope 爆炸）

> **問題**：plan 越寫越長，核心痛點、voice call 安全、長遠願景混埋一齊，導致「寫 plan 幾日，code 一行未寫」。分三層，先做 Tier 1。

### Tier 1 — 核心痛點（🔴 立即做，最細步最大效益）

**SK 即時痛點：wake 唔準 / STT 慢 / response 慢。**

| Step | 內容 |
|---|---|
| A2 | wake rearm 修復（叫唔醒元兇） |
| A | wake VAD 防誤觸 |
| B | STT GPU 加速（5090） |
| D1/D2/D3 | streaming TTS + 短確認 + 縮短等待 |

### Tier 2 — Voice call 安全（🟡 Tier 1 完成後做）

**SK 痛點：同人 voice call 會洩漏 / 對方聲誤觸。**

| Step | 內容 |
|---|---|
| A3 | AEC（**優先 WebRTC AEC3**，業界標準） |
| A4 | Speaker verification（聲紋，已實測可行） |
| chat_context | 社交場合偵測（Discord 標題 + voice_call） |

### Tier 3 — 願景（⏳ 長遠，逐步）

**Iron Man 全 AI 夥伴：一個 app + 深度整合 + 擴展 + 自我整合。**

| 項目 | 內容 |
|---|---|
| Phase 8 JARVIS ONE | Electron 一個 app |
| Step 8.5 MCP 整合 | Hermes ⇄ JARVIS 雙向 |
| Mage-VL | streaming 影片理解（「眼」） |
| 自我整合/擴展 | 反編譯接入 + 更多平台/MCP |

**原則**：Tier 1 未完成前，唔好開始 Tier 2/3 嘅 code（避免完美主義陷阱）。每個 Tier 有明確「done 定義」先算完成。

---

## Phase 1 — 語音核心（已完成 ✅）

- [x] `jarvis serve` 背景常駐（tray + companion + hotkey）
- [x] 開機自啟（Startup `JARVIS.vbs`）
- [x] wake「hey jarvis」（openwakeword，threshold 0.50）
- [x] 遊戲中不醒（讀 `sk_activity.json`，`playing` → 靜音）
- [x] STT（SenseVoiceSmall，`yue` 預設）+ asr_repair 補錯
- [x] TTS（Piper jarvis-high.onnx，英文）
- [x] Hermes bridge（API 8642 / SPEAK 機制 / 主文中文+語音英文）

## Phase 2 — barge-in（說話打斷）✅ 已完成

- [x] 音量突增（RMS > -20dB）+ 持續 ≥300ms → 中斷 `mouth.stop_play()`
- [x] Echo Prevention（TTS 播放期間暫停偵測）

## Phase 3 — streaming（🔴 部分完成——TTS streaming 未實現！）

- [x] Hermes bridge SSE streaming（`/v1/runs/{id}/events` 讀 `message.delta`）
- [x] 先唸短句確認「Yes, Sir.」概念已定（Open Questions #3）
- [ ] **Streaming TTS**（`mouth.speak` 仍係一次過 `synthesize(整句)` → 等成句先播放）→ 已列入 Phase 6 D1
- [ ] Streaming STT（可選）→ 已列入 Phase 6 後續

## Phase 4 — 回覆語言 ✅ 已完成

- [x] 主文中文 + `SPEAK: <English>` 英文唸（mouth 僅唸 spoken，CJK 跳過）

---

## Phase 6 — Wake/STT/Response 品質改善（⏳ 已確認未開始，優先於 Phase 8）

> 2026-08-27 SK 確認：① wake 誤觸/叫唔醒 ② STT 慢/錯字多 ③ response 出聲太慢。
> **對 SK 嘅好處：** 把聲變準（少誤觸）、變快（GPU STT）、變爽（streaming + 縮短等待）。

| Step | 內容 | 檔案 | 狀態 |
|---|---|---|---|
| **A** | wake 防誤觸：openwakeword `vad_threshold`（Silero VAD 過濾非語音） | `wake.py` | ✅ 已處理：`vad_threshold=0`（關閉）——實測 0.5 太嚴擋真人聲（叫唔醒）；防誤觸改靠 A2 rearm timeout + threshold（2026-08-27 決定） |
| **A2** 🔴 | **wake rearm 邏輯修復**（2026-08-27 logic review 發現）：`armed` 依賴分數跌 < 0.25 先重新武裝——環境有持續中等分數（0.25-0.5，例如 BGM 有人聲）→ 永遠唔會 rearm → 叫唔醒。**修正：加 rearm timeout**（分數 < threshold 持續 N 秒就重新武裝，唔淨靠跌低） | `wake.py` | ✅ 已實作（2026-08-28）：`_REARM_TIMEOUT_S = 2.0`（wake.py:20）+ callback 內 below_thr_since 機制（wake.py:550-557） |
| **A3** 🔴 | **AEC（聲學迴聲消除）**（2026-08-27 SK 確認 + 網上查證）：wake pipeline 加 AEC——WASAPI loopback 攞喇叭 reference → `speex_echo_cancellation` / WebRTC AEC3 → 淨音入 openwakeword。**解決**：① 對方 voice call 聲唔觸發 wake ② 自己 TTS 迴聲唔自觸發（取代 echo prevention hack）③ SK 喺 voice call 照叫照醒（唔使 hotkey） | `wake.py` + `pyaec`/`pyaudiowpatch` | ✅ 上線（2026-08-28）：`AecChain` 多 reference（Sonar Media=YouTube BGM + Sonar Chat=voice call 對方聲 + Arctis=自己 TTS 迴聲；冇 signal 自動 skip）。`aec_first_apply` 確認 AEC 喺 wake pipeline 跑緊。settings `aec_enabled: true` + `aec_reference_device`。**⚠️ get_chunk bug 已修**（partial buffer 後 queue 空會錯 return None → deadline 邏輯）。**待 SK 實測**：YouTube BGM 30s 0 誤觸 + voice call 中對方聲唔觸發 + 自己叫照醒 |
| **A4** 🔴 | **Speaker Verification（聲紋辨識）**（2026-08-27 SK 補充——Iron Man「完全理解邊個講嘢」）：預先錄 SK 30s 聲（enrollment）→ wake 前 AEC 濾走喇叭 → speaker gate（係咪 SK 把聲）→ 係先醒。**解決**：屋企其他人（Pepper/Rhodey 場景）講嘢唔觸發；只有 SK 叫先醒。Library：`resemblyzer` / `speechbrain` / `pyannote`。**✅ 可行性已實測（2026-08-27）：speechbrain ECAPA-TDNN 喺 Windows+Python 3.14 跑通——同人 cosine 0.9142 vs 異人 -0.02~0.20，threshold 0.5 完美分人。Pitfalls：① speechbrain symlink fail → monkeypatch `link_with_strategy` 用 copy ② model 要 `huggingface_hub.snapshot_download` 落 local** | `wake.py` + enrollment script + `speechbrain` | **🟡 已實作上線（2026-08-27 晚）：** `src/jarvis/speaker_gate.py`（verify_pcm + warm + profile meta）+ `wake.py` gate（OWW + STT path）+ settings `speaker_gate/speaker_threshold` + settings UI + `scripts/verify_voice.py`。serve 已重啟，`spk_gate ready dev=cuda:0 load=1.0s`。**⚠️ 待 SK 真聲驗證**：210 個 wake 樣本係 **Sonar mic**（record script 用 default input），enrollment 用 **Arctis**（wake_mic_device=2）→ cross-mic cosine 得 0.19-0.33，**樣本做唔到 accept 驗證**。下一步：SK 講「hey jarvis」睇 log score 或跑 `verify_voice.py`；唔夠高分就重新 enrollment（Arctis）。threshold 0.5 待真機數據微調。 |
| **B** | STT GPU 加速：FunASR `device="cuda:0"`（5090 閒置中） | `ear.py` | ✅ 已實作（2026-08-28 確認）：`_preferred_device()`（ear.py:28-37）傳 `device="cuda:0"`；serve.log rtf 0.03-0.044（GPU）vs 0.546（CPU fallback 時） |
| **D1** | Streaming TTS：Piper 逐 chunk 即播（唔等成句） | `mouth.py` | ❌ 決定唔做（2026-08-28）：實測 Piper TTS 非 bottleneck（0.266s 一句）——`sd.OutputStream` streaming 反而令 voice out 失效（已 revert）。壓延遲靠 LLM 首 token + STT（bridge 唔好 fallback CLI） |
| **D2** | 先唸短確認「Yes, Sir.」→ 感知延遲最低 | `shell_app.py` | ✅ 已實作（2026-08-28 確認）：`_on_listen_cmd` capture 完成即刻唸（shell_app.py:647-659）；`mouth.interrupt()` 蓋過 ack 防疊聲 |
| **D3** | 縮短等講完：`_CMD_SILENCE_FRAMES` 8→5、`_STT_TRAIL_S` 0.5→0.35 | `wake.py` | ✅ 已實作（2026-08-28 確認）：`_CMD_SILENCE_FRAMES = 5`（wake.py:30）、`_STT_TRAIL_S = 0.35`（wake.py:36） |

**完成指標：** ① BGM 30s 0 誤觸（⚠️ 限「純音樂/環境聲」；**有人聲 BGM 唔保證**——VAD 會當語音，另測）② STT GPU ≥3x 快 ③ 喊完→有聲 ≤3s。④（A2）BGM 有人聲環境下叫「hey jarvis」仍然醒。

### Phase 6 後續（💤 deferred）
- **自訓 wake「jarvis」**（`docs/train_wake_jarvis.md`）：淨講 Jarvis 就醒；自己聲 1000+ 混 Kokoro TTS 訓練（預訓練只有 Hey Jarvis）
- **Discord 回覆 voice out**（2026-08-27 討論）：方案 A = Jarvis 讀 Hermes session log 見新回覆即 speak；零衝突。B = Hermes plugin push。C = Jarvis 直連 Discord ❌（token 衝突）

---

## Phase 7 — Alert / 感應器平台（⏳ 依序）

> 來源：`TODOS.md`。Sensor platform design APPROVED（NVML GPU 健康已 ship）。

| 項目 | 內容 | 依賴 | 狀態 |
|---|---|---|---|
| **GPU-Z failover backend** | `GpuzBackend`（CSV/SHM）做 HWiNFO 後備 | HWiNFO SHM 先落地 | 💤 deferred |
| **HWiNFO SHM backend** | CPU 溫度/功耗/風扇 + 5090 hotspot | NVML + speak-path 穩定 | 💤 deferred |
| **Minecraft ready alert** | 偵測 Prism/MC ready → stub「Minecraft is ready.」 | hermes alert_tts 穩定 | 💤 deferred |
| **Hermes push/notify** | AlertStore 入隊後主動 push（sub-second） | speak-path harden | 💤 deferred |
| **screen/UIA「what did they say?」** | 短 ping 後可追問內容（UIA/OCR） | Alerts HTTP MCP 穩定 | 💤 deferred |
| **remote Hermes → Windows alerts MCP** | VPN/SSH tunnel 支援（唔開 public port） | 本地 HTTP MCP 穩定 | 💤 deferred |

---

## Phase 5 — GUI 重做 Iron Man 風格（⚠️ 將由 Phase 8 取代/合併）

> **2026-08-27 修正：** Phase 8（JARVIS ONE）已決定用 **Electron** 做殼——Phase 5 嘅「pywebview」方向被取代。本 Phase 內容合併入 Phase 8 Step 8.2（companion/settings → Electron Iron Man HTML）。**唔再獨立執行。**

**保留嘅原始目標**（由 Phase 8.2 承接）：
- companion/settings 由 tkinter → Iron Man HTML（#00aaf8、透明、科技感）
- tray 保留（Phase 8 會變單一 tray）

---

## HUD — JARVIS HUD（jarvis-hud）（✅ v0.1 運行中 / 🔄 將被 Phase 8 整合）

### 已實現（✅）
- Transparent/frameless/always-on-top/click-through overlay（Iron Man 視覺）
- 空心圓環 + Jarvis 字樣 + 波形核心（已定案，非實心球）
- 數據密集控制中心 + 頭盔標線 + App Dock
- 主色桌布藍 **#00aaf8**、卡片可拖曳
- **Dock**：滑鼠滑到底部感應區彈出、貼螢幕底、遊戲中自動隱藏、平時隱藏不擋畫面、獨立 BrowserWindow 置頂
- **Media Bridge**（8771）：HUD 音樂按鈕 → Chrome 擴充控制 YouTube（content.js 輪詢 8771）
- **Reply Server**（8770）：Jarvis 回覆推送顯示（`POST /reply` → `ok`）
- 遊戲偵測（`activity_monitor.py`）→ dock 強制隱藏

### 後續（⏳）
- [ ] 元素重疊檢查（SK 規則：每次改動後「always check overlap problem」）
- [ ] Iron Man 視覺完整化（旋轉環/雷達掃描/數據流/呼吸光環——已跳過頭盔弧形冠）
- [ ] HUD ↔ Phase 5 GUI 視覺語言統一（Phase 5 用同款 HTML）

---

## ⚠️ 已知問題 / 注意事項

- **TTS streaming 未實現**（Phase 3 標完成但 mouth.speak 仍整段合成）→ Phase 6 D1
- **jarvis serve 唔係成日跑**（2026-08-27 檢查：冇 serve process，得 alert poller + MCP wrappers；SK 話暫時唔使理）
- **SenseVoice 純 CPU**（5090 閒置）→ Phase 6 B
- **wake 冇 VAD 過濾**（BGM/遊戲聲誤觸）→ Phase 6 A
- **HUD 8770/8771 正常**（POST /reply → ok；Media Bridge listen）
- **Windows 工作列自動隱藏**：HUD/dock 定位要考慮 work area = 全屏 1440px

---

## Phase 8 — JARVIS ONE：一個 app 整合（🔴 大方向，2026-08-27 SK 拍板）

> **執行計畫已寫**：`.hermes/plans/PHASE8_JARVIS_ONE.md`（2026-08-28）——8.1 一個入口 → 8.5 MCP 整合，每步驗證 + 風險。建議次序：8.1 → 8.5 → 8.3 → 8.2/8.4。

> **SK 決定：** jarvis + HUD 最終要係**一個 app、一個 tray、一個啟動入口**（唔係兩個獨立 project）。語言技術交俾 agent 決定：**Electron 為主 + Python sidecar**。

### 目標架構

```
┌───────────────────────────────────────────────┐
│  JARVIS ONE（Electron app — 單一入口）        │
│                                               │
│  Electron main process                       │
│   ├─ Tray（唯一入口：開關/顯示/設定/退出）    │
│   ├─ HUD overlay（透明 Iron Man，遊戲自動隱藏）│
│   ├─ Companion 視窗（聊天/狀態）              │
│   ├─ Settings 視窗（Iron Man HTML）           │
│   ├─ Dock（底部感應區彈出）                   │
│   ├─ Media Bridge（8771）＋ Reply Server（8770）│
│   └──┬─ IPC（stdio JSON-RPC / localhost）────┐│
│  Python voice sidecar（Electron spawn）      ││
│   ├─ wake（openwakeword + VAD + 遊戲中不醒） ││
│   ├─ STT（SenseVoice GPU）                   ││
│   ├─ TTS（Piper streaming）                  ││
│   ├─ Hermes bridge（8642 / SPEAK）           ││
│   └─ alerts / sensor poller                  ││
└──────────────────────────────────────────────┘
```

### 遷移階段（每步驗證）

| Step | 內容 | 驗證 |
|---|---|---|
| **8.1 一個入口** | Electron 起 app 時 spawn Python sidecar（**先 spawn 現有 jarvis serve 包裝**，8.3 先真正 sidecar 化）；tray 管晒（開 HUD/設定/退出 = 一齊退出） | 一個 tray 一個 process tree；退出 tray → sidecar 一齊收；全程無 console 閃出 | ✅ 完成（2026-08-28）：jarvis-hud main.js 加 Tray（顯示 HUD/Dock/退出）+ `ensureSidecar()`（8765 偵測 → spawn `python.exe -m jarvis serve`，JARVIS_ELECTRON_HOST=1）+ `stopSidecar()`（退出一齊收）+ Ctrl+Alt+D 加 `dockForceHidden` check；shell_app `start_tray` 喺 JARVIS_ELECTRON_HOST=1 時 skip pystray（防雙 tray）。驗證：HUD 8770/8771 + serve 8765 全 listening，Electron spawn serve 成功 |
| **8.2 視窗搬遷** | companion/settings 由 tkinter → Electron 內嵌 Iron Man HTML（同 HUD 語言）；on-demand 顯示 | 無 tkinter 視窗，全部 Electron；唔撳唔彈 |
| **8.3 語音 sidecar 化** | wake/STT/TTS/hermes_bridge 由 sidecar 提供；Electron 經 IPC call | 喊「hey jarvis」→ HUD 顯示 + 語音回應（全背景） |
| **8.4 HUD 融合** | HUD overlay + companion 共用一個 renderer 體系；dock/遊戲隱藏保留 | Iron Man 視覺統一 |
| **8.5 MCP 整合** | JARVIS 做 MCP server，註冊入 Hermes `mcp_servers`；工具注入全平台 | `hermes` 內 call `mcp_jarvis_speak` 成功；Discord 傾偈可叫 Jarvis 唸嘢 |

### 決策紀錄（2026-08-27）

- **語言**：Electron（main/UI）+ Python（voice sidecar）——HUD overlay 需要 Electron 嘅透明/frameless/穿透；語音用 Python 生態（openwakeword/funasr/piper）
- **IPC**：stdin/stdout JSON-RPC（簡單、唔開 port）或 localhost HTTP（sidecar 已有 HTTP 經驗）——實測後定
- **單一 tray**：取代而家 jarvis tray + HUD 各自窗口
- **現有 jarvis serve 保留**：sidecar 化期間唔會拆走，逐步遷移

### 🔴 背景執行鐵則（SK 2026-08-27 強調）

**JARVIS ONE 所有嘢必須 background 執行——零彈窗、零搶焦點：**
- Electron 用 `show: false` / frameless / transparent；視窗只喺用戶明確叫先顯示（HUD overlay 例外——透明穿透，唔算「彈窗」）
- Python sidecar 用 `pythonw` / CREATE_NO_WINDOW / windowsHide——任何子進程唔可以出 console
- Tray 係唯一可見 UI；Companion/Settings 係 on-demand 視窗（用戶撳先開）
- 遊戲中（`sk_activity.json` state=playing）→ HUD/dock 自動隱藏 + wake 靜音（現有規則保留）
- 一切 spawn 都用隱藏旗標：`Start-Process -WindowStyle Hidden`、`subprocess.CREATE_NO_WINDOW`、Electron `windowsHide: true`

### 🔴 深度整合 Hermes（SK 2026-08-27 強調）——MCP 雙向

**JARVIS ↔ Hermes 唔止 API bridge——要做 MCP 層面雙向整合：**

```
Hermes Agent（Discord/CLI/cron 都用到）
   │ ▲
   │ │ MCP client（Hermes 內置）
   │ │
   ▼ │
JARVIS ONE = MCP server（stdio 或 HTTP）
   ├─ mcp_jarvis_speak(text)          → 叫 Jarvis 用語音唸（背景，唔彈窗）
   ├─ mcp_jarvis_wake_status()         → 查 wake 狀態/裝置
   ├─ mcp_jarvis_alert(phrase)         → 推 alert 入 Jarvis 唸（比 poll 快）
   ├─ mcp_jarvis_sensors()             → 讀 GPU/CPU 感應器（NVML/HWiNFO）
   ├─ mcp_jarvis_set_tts(text)         → 設定 TTS 參數（voice/speed）
   └─ ...（按需擴展）
```

**雙向整合：**
- **Hermes → JARVIS**：JARVIS 作為 MCP server 註冊入 Hermes `mcp_servers` config → 工具自動注入所有平台（Discord 傾偈時 Hermes 可以直接叫 Jarvis 唸嘢、讀感應器）
- **JARVIS → Hermes**：現有 Hermes bridge（API 8642 / SPEAK）保留——Jarvis 收 wake 後 call Hermes 攞回覆
- **結果**：你喺 Discord 同我傾偈，我可以叫 Jarvis 喺部機度 background 唸一句；你喊「hey jarvis」，佢 call 我攞答案——**一個 loop 兩邊互通**

**實作註記（Hermes native MCP）**：
- MCP server 用 stdio（`command: pythonw`，jarvis 起 mcp server）或 HTTP（jarvis 已有 HTTP 經驗）
- 工具命名自動 `mcp_jarvis_*`，全平台注入
- env 過濾：MCP subprocess 只繼承安全 baseline——JARVIS 需要嘅 key 要喺 `env` 明確加
- Hermes 內置 MCP client 要 `pip install mcp`（若未裝）

### 🔴 MCP 安全 & 可靠性（2026-08-27 review 補充）

- **權限**：`mcp_jarvis_speak` / `mcp_jarvis_alert` 會喺部機出聲——**唔應該畀任何對話無限量 call**。要加限頻（rate limit，例如每 tool ≤1 req/2s）同埋只限受信任來源（SK 自己嘅 DM；group/頻道 call 前要確認）。
- **單點故障 fallback**：JARVIS 做 MCP server，死咗 → Hermes 啲 `mcp_jarvis_*` 全失效。要 graceful：MCP tool 失敗時 Hermes 照正常回覆（fallback 到文字），唔好因為 Jarvis 死而整個 conversation 壞。
- **遊戲中 guard**：`mcp_jarvis_speak` 喺 state=playing 時應該拒絕或靜音（唔好喺打機時突然唸嘢嚇人）——沿用背景執行鐵則。

### 🔴 來源/對象過濾（SK 2026-08-27 強調——「我會用 Discord/WhatsApp 同其他人傾偈」）

**JARVIS 嘅語音輸出 / proactive 意見，只可以喺「同 SK 自己」嘅場合出聲——同其他人嘅對話一律靜音：**

- **DM vs group/他人對話**：Hermes 喺 Discord/WhatsApp 見到 SK 同其他人傾偈（group chat、他人 DM）→ **唔觸發** voice out / proactive 提醒 / speak tool。只限 SK 自己嘅 DM（現時 Home channel / SK 個人 DM）。
- **訊息來源**：`mcp_jarvis_speak` 嘅呼叫來源要帶 context（platform + chat）——Hermes 側要檢查係咪 SK 本人對話先允許。
- **WhatsApp 場景**：SK 用 WhatsApp 同人傾偈緊 → Jarvis 唔會因為「Hermes 見到訊息」而突然出聲。
- **「Watch out」原則**：寧願唔出聲，都唔好喺錯嘅場合出聲（瘀事 + 洩漏 JARVIS 存在）。

**✅ 實作可行性（2026-08-27 確認）：`chat_context` 偵測** — **✅ Code 完成（2026-08-28）：**

`activity_monitor.py` 已加 `chat_context` + `voice_call`（Discord/WhatsApp 標題抽 `@對象`/群組 → `is_self`；pycaw render session ACTIVE ≥5s → `voice_call`）。JARVIS gate 已加（`shell_app._start_voice_call_gate` 5s loop → voice_call 中 mute ack/alerts + pause wake；reply 照出 = SK 主動）。**⚠️ 待實測**：SK 開 voice call 時 check `sk_activity.json.voice_call` 會唔會變 true。

Discord/WhatsApp 視窗標題顯示 active chat（例如 `@JARVIS - Discord`、`@阿強 - Discord`、`CS2 戰隊 - Discord`）——**Windows 已經知你同邊個傾偈**。

做法（小改動）：
1. `activity_monitor.py` 擴展：foreground 係 Discord/WhatsApp → 抽標題 `@對象名`/群組名 → 寫入 `sk_activity.json` 新欄位 `chat_context: {platform, chat, is_self}`
2. JARVIS gate：`is_self=true`（同 JARVIS DM）→ 出聲；其他 → 靜音；非 Discord/WhatsApp foreground → 冇傾偈，正常
3. Hermes proactive 同 MCP speak 都讀呢個 gate

**預期效果**：
- 你喺 Discord 同人傾 → 標題唔係 `@JARVIS` → JARVIS 靜音 ✅
- 你喺 WhatsApp 傾 → 靜音 ✅
- 你睇 code / 打機 → 冇 chat context → 正常 ✅

### 🔴 Voice Chat 偵測（SK 2026-08-27 補充——「我指 voice chat」）

**⚠️ 最重要場景：** 你 Discord/WhatsApp **語音通話**中。呢個唔係社交禮儀問題——係**音訊安全**問題：

**兩個核心風險（SK 2026-08-27 點出）：**
1. **對方會唔會聽到 JARVIS 把聲？** → **會！** JARVIS 出聲（Piper → speaker）→ 聲波入 mic → 傳入 voice call → 對方聽到。
2. **JARVIS 會唔會因為對方把聲而起來？** → **會！** 對方講嘢（voice call → speaker）→ JARVIS wake mic 收到 → openwakeword 誤觸（「hey guys」≈「hey jarvis」）→ 仲會回應 → 對方聽到兩把聲。
   - ⚠️ 現有 code 嘅 Echo Prevention 只防 JARVIS 自己 TTS 迴聲——**唔防對方把聲觸發 wake**！

**✅ 解決方案（2026-08-27 實測確認）：pycaw AudioSession State——一個 signal 解決兩個問題**

```
Discord/WhatsApp render session ACTIVE（持續 ≥5s）
  = 對方有聲出緊 = voice call 進行中
  → ① 暫停 JARVIS 出聲（防洩漏俾對方）
  → ② 暫停 wake 偵測（防對方把聲誤觸）
```

**實測結果**：
- ✅ pycaw 裝好（Python 3.14 環境），可以列 Discord 嘅 audio sessions
- ✅ 而家 Discord 2 個 sessions 都 Inactive（冇 voice call，正常）
- Discord RPC pipe 確認唔存在（Discord 冇開 RPC）——唔用 RPC
- 打字 notification 聲 < 5s——加「持續 ≥5s」過濾，唔會誤判

**Gate 規則：**
```
voice_call_active = true（render ACTIVE ≥5s + 社交 app foreground）
  → 完全靜音 🔇：JARVIS 唔出聲（防洩漏）+ wake 暫停（防誤觸）
voice_call_active = false + 你喺 Discord/WhatsApp 打字 → 正常 ✅（打字唔 mute）
voice_call_active = false + 其他 foreground → 正常 ✅
```

**實作**：`activity_monitor.py` 加 `voice_call: true/false`（pycaw session ACTIVE 持續 ≥5s + 社交 app foreground）；JARVIS gate 讀呢個（speak mute + wake pause）。

**例外**：game 入面嘅 Discord overlay voice（Discord 唔係 foreground）——用 `state=playing` cover（遊戲中靜音）。

**🔧 Voice call 期間點叫 JARVIS 做嘢？（SK 2026-08-27 問——「可能有嘢要叫你做」）**

~~方案：Hotkey push-to-talk~~ → **SK 否決 hotkey**。上網查業界做法 → **正路係 AEC（Acoustic Echo Cancellation）**。

**業界做法（2026-08-27 網上查證）：**
- **Amazon Echo / Google Home**：AEC——以喇叭輸出做 reference，從 mic 訊號減走喇叭出嘅聲。對方 voice call 聲（由喇叭出）→ AEC 濾走 → 唔觸發 wake；用戶本地講嘢 → 照醒。
- **手機 assistant**：靠 OS telephony state（Windows 冇呢樣嘢）。
- **WebRTC（Zoom/Meet）**：AEC 標準做法。

**✅ 方案：JARVIS wake pipeline 加 AEC**

```
reference = 喇叭輸出（WASAPI loopback capture）
mic - AEC(reference) = 淨返「本地聲」（SK 自己講嘢）
```

**一次過解決三個問題：**
1. **對方 voice call 聲 → 濾走 → 唔觸發 wake**（唔使 detect voice call！）
2. **JARVIS 自己 TTS 迴聲 → 濾走 → 唔自觸發**（順便取代現有 echo prevention hack）
3. **SK 喺 voice call 照叫 JARVIS → 本地聲照醒**（唔使 hotkey！）

**現成 library（實測可用）：**
- **`python-webrtc-audio-processing`（⭐215）——WebRTC AEC3（業界標準：Zoom/Meet 都用）← 優先**
- `speexdsp`（PyPI）——SpeexDSP 內置 AEC（舊版，效果較弱，做 fallback）
- `pyaec`（⭐427）——adaptive filter AEC

**實作**：`wake.py` 加 AEC 層——WASAPI loopback 攞 speaker reference → `speex_echo_cancellation` / WebRTC AEC3 → 淨音入 openwakeword。Phase 6 新增 Step A3。

**待驗證**：AEC 效果要實測（對方聲濾得乾唔乾淨、本地聲會唔會受影響）。

**🎬 Iron Man 式解決方案（SK 2026-08-27 問——「Iron Man 點解決？」）**

**Iron Man 核心：私人音訊通道（earpiece）**——JARVIS 永遠經 Tony 耳仔出聲（頭盔/耳機），所以「洩漏俾對方」根本唔存在。三層防護：

| 層 | Iron Man 做法 | 對應方案 |
|---|---|---|
| **1. 私人音訊** | JARVIS 經 earpiece 出聲（得 Tony 聽到） | **JARVIS 預設輸出 = 耳機（Arctis Nova 7）**——物理隔離，漏音極少，唔入 mic |
| **2. 指向性 mic** | 套裝 mic 淨聽 Tony | **AEC + mic 選擇**——濾走喇叭聲 |
| **3. 社交感知** | JARVIS 知道 Tony 同緊邊個 | **chat_context**（Discord 標題 + voice_call detect） |

**實作方向**：mouth.py 輸出 device 預設 = Arctis Nova 7（耳機），唔出喇叭；加上 AEC（Step A3）+ chat_context = 完整 Iron Man 三層。

**🎬 Iron Man 進階——「JARVIS 完全理解邊個講嘢」（SK 2026-08-27 補充）**

**電影事實**：Tony 喺屋企（冇戴頭盔），Pepper/Rhodey 喺度——JARVIS 分辨到邊個講緊嘢：Pepper 講嘢唔當指令、Rhodey 講嘢唔亂回應、Tony 叫「JARVIS」先醒。**JARVIS 唔係「聽到聲就醒」——佢識分人。**

**技術對應：Speaker Verification（聲紋辨識）**

```
Step 1：錄低 SK 30 秒聲（enrollment）→ 建立聲紋
Step 2：每次 wake 前：
  AEC 濾走喇叭聲（遠端）→ 剩本地聲
  → speaker verification：「係咪 SK 把聲？」
  → 係 → 醒 ✅ ｜ 其他人（Pepper/Rhodey 喺屋企）→ 唔醒 🔇
```

**Library**：`resemblyzer`（輕量）/ `speechbrain ECAPA-TDNN`（準）/ `pyannote`（diarization）

**四層完整 Iron Man：**
| 層 | Iron Man | 技術 |
|---|---|---|
| 1. 私人音訊 | earpiece | 耳機輸出（Arctis Nova 7） |
| 2. 指向性 | 套裝 mic 淨聽 Tony | AEC 濾喇叭聲（Step A3） |
| 3. 聲源分辨 | 知 Pepper/Rhodey 把聲 | **Speaker verification**（Step A4） |
| 4. 社交感知 | 知 Tony 同邊個 | chat_context |

**實作**：Phase 6 新增 Step A4——enrollment script（錄 SK 聲）+ wake 前 speaker gate（唔係 SK 聲唔醒）。

**⚠️ A4 注意（SK 2026-08-27 問——「換 mic 有冇影響？」）**：
- 換 mic 後聲紋相似度會跌（唔同 frequency response）——但唔會完全失效（ECAPA 有 channel robustness）
- **最穩陣：換 mic 後重新 enrollment**（錄 30 秒）
- **自動偵測**：enrollment 時記低 mic device ID——detect 到 mic 唔同 → 提示重新 enrollment

### 🔄 自我迭代功能（SK 2026-08-27 問——「識唔識得自我迭代？」）

**已經有嘅（✅）：**
- **Skills**：agent 做完任務發現 workflow → 存做 skill → 下次重用（今次 session 已 update 多個）
- **Memory**：用戶偏好/環境事實 → 跨 session 記得
- **Curator**：Hermes 自動管理 skills 生命周期
- **Session search**：跨 session 回顧
- **自我修復**：Gateway watchdog（今日已裝）——detect 異常 → 自動 restart

**想做嘅（⏳ JARVIS 層）：自我監控/調參**
```
JARVIS 定期自我檢查：
  ① wake 誤觸率（幾耐誤觸一次）→ 自動調 threshold
  ② STT 準確度（用戶更正率）→ 自動調 model/hotwords
  ③ response 延遲（喊完→有聲幾耐）→ 自動調參數
  ④ 結果寫入 log → 下次 session 睇到 → 持續改進
```

**實作**：Phase 6 後續加「自我監控」——JARVIS 每週統計自己表現 → 調整參數 → 寫入 plan/log。

**🔒 自我迭代安全（SK 2026-08-27 問——「點樣確保唔會崩潰？」）**

**七層防護（self-improvement safety）：**

| # | 機制 | 做法 |
|---|---|---|
| 1. **改前 backup** | 改任何參數/config 前自動備份——改壞即還原 |
| 2. **改後 self-test** | 每次調整後跑測試（wake ×5 + BGM 30s）——fail 自動 rollback |
| 3. **參數 clamp** | 自動調參有硬性上下限（threshold 0.35-0.75 等）——唔會調到癱瘓 |
| 4. **單一變數** | 每次只改一個參數——知邊個改動導致問題 |
| 5. **人機確認** | 細調整自動；大改動（換 model/改 code）要 SK 確認 |
| 6. **Circuit breaker** | 連續 3 次調整令性能下降 → 停止自動調整 + 報警（唔會自殘） |
| 7. **核心不可改** | wake loop / audio pipeline 核心邏輯唔俾自我修改——只可調 config 層面 |

**流程：**
```
① 統計本週表現 → ② 提出調整方案 → ③ backup → ④ 應用（單一變數+clamp）
→ ⑤ self-test（pass → log / fail → rollback + 報警）
→ ⑥ 連續 3 fail → circuit breaker 停 + 通知 SK
```

**已有基礎**：Watchdog（gateway 自我修復）、backup 習慣、SK「先確認後執行」規則。

### 🔒 安全 / 隱私 / 法務（2026-08-27 14-POV review 補充）

**呢啲喺之前 review 漏咗，但好重要：**

| # | 風險 | 處理 |
|---|---|---|
| 1 | **聲紋 = biometric 數據**（敏感，受 PDPO 規管） | enrollment 聲紋要**加密存儲**，SK 可隨時刪除；唔上傳雲 |
| 2 | **Mage-VL 實時睇畫面 = 潛在屏幕監控** | 畫面理解要**明確邊界**：只睇 SK 要求睇嘅嘢（影片/指定視窗），唔係全天候錄屏；畫面數據唔留底 |
| 3 | **反編譯合法性** | 只反編譯 SK 有合法授權/用途嘅程式；見到 EULA 禁止 reverse engineering 要提 SK |
| 4 | **MCP token 明文** | config 入面嘅 Bearer token 唔可以喺 log/截圖/skill 度出現（[REDACTED] 原則） |
| 5 | **影片下載 ToS** | yt-dlp 下載要注意 YouTube ToS（已有 cookies = 有帳號，用家自己承擔） |

### 🔒 可靠性缺口（2026-08-27 14-POV review 補充）

- **JARVIS 本身冇 watchdog**——gateway 有 watchdog（今日裝），但 JARVIS serve / sidecar 死咗冇人理。要加 JARVIS 層 watchdog（或由 Phase 8 嘅 Electron main process 監察 sidecar 生死，死咗 restart）。
- **冇 git/versioning**——jarvis-pc / jarvis-hud 改 code 前要確認有 git repo（或者至少 backup）——改壞咗可以 rollback。
- **GPU 資源競爭**——Mage-VL + SenseVoice + 打機同時跑，要定**優先級**：`state=playing` 時 GPU 大模型（Mage-VL/STT）降級或延遲，唔好搶 game 嘅 VRAM。

### 🔌 擴展連接（SK 2026-08-27 問——「點樣連接更加多嘅嘢？」）

**五個層面：**

| 層 | 方法 | 例子 | 難度 |
|---|---|---|---|
| **1. 平台** | Hermes gateway 加 platform | Telegram / WhatsApp / Slack / Signal（SK 用 WhatsApp！） | 🟢 config 加幾行 |
| **2. MCP 工具** | `mcp_servers` config 加 server | filesystem、GitHub、Notion、Gmail、Slack、Airtable | 🟢 config + API key |
| **3. Agents** | 更多 CLI agents delegate | Cursor（有限制）、其他 | 🟡 有 skill |
| **4. 硬件/IoT** | 智能家居 | Philips Hue（`openhue` skill 已有）、ESP32 自訂 | 🟡 要硬件 |
| **5. 事件** | Hermes webhook 平台 | GitHub/CI/監控事件 → 自動通知 | 🟢 已支援 |

**優先建議（低 hanging fruit）：**
1. **Telegram/WhatsApp platform**——手機直接同 JARVIS 傾（你已經用 WhatsApp）
2. **MCP servers**（filesystem/github/notion）——我直接讀寫你啲嘢
3. **Philips Hue**——語音控制燈（skill 已有）
4. **Webhook**——GitHub/CI 事件自動通知

**原則**：每加一個連接都要有「背景執行 + 來源過濾」——例如 WhatsApp 連接都要遵守 voice call 靜音、唔好喺 social 場合亂出聲。

### 🛠️ 自我整合第三方程式（SK 2026-08-27 要求——「識得反編譯某些程式，然後自行聯接入去」）

**目標**：JARVIS/Hermes 見到新程式識得自己研究 + 接入，唔使 SK 教。

**✅ 已驗證能力（2026-08-27 WeSight 實例）：**
```
① 反編譯：npx @electron/asar extract app.asar → main.js（9.7 萬行）
② 理解：搵到 `gateway run --replace`（殺 gateway 元兇）+ taskboard stdio bug
③ 接入：改 wesight.sqlite config + gateway-port.json → WeSight 唔再殺 gateway
```

**工具矩陣：**

| 程式類型 | 工具 | 接入方式 |
|---|---|---|
| Electron app | asar 解包（✅ 用過） | 讀 source + 改 config / MCP |
| Python | pyc decompile（uncompyle6/pycdc） | 讀 bytecode → 理解邏輯 |
| .NET | ILSpy / dnSpy | 反編譯 C# → 理解 + hook |
| 原生 exe | Ghidra（免費） | 靜態分析 → 理解入口/API |
| 網頁/JS | beautify + 直接讀 | 抓 API → 自己 call |
| 有 API 嘅 | 抓 API → 包裝 | **MCP server**（最正規） |

**接入流程（自我整合 SOP）：**
```
① 上網查（先查再動——SK 原則，確保「有眼有耳」）：
   - 官方文件（docs / API reference / README）
   - GitHub source + Issues（有冇已知 bug / 官方建議）
   - 論壇（Reddit / Stack Overflow / 社群 Discord）
   - 用家建議（blog / reviews / 教學）
   - 影片（YouTube tutorial / demo）
② 有官方 API / MCP / plugin？→ 用官方方式接入（最穩陣）
③ 官方資訊唔夠 → 先反編譯/解包理解架構（fallback，唔係第一步）
④ 揀接入方式（MCP server / config 修改 / computer_use / plugin）
⑤ 測試 → 驗證 → 寫入 skill（下次同類程式直接套用）
```

**「有眼有耳」原則（SK 2026-08-27 要求）：**
- **眼**：睇官方 docs、source、API 文檔
- **耳**：聽社群意見、論壇討論、用家反饋（唔好淨係信官方宣傳）
- **多源驗證**：至少查 2-3 個來源先動手——唔靠單一來源（官方 docs 可能過時、論壇可能誤導）
- **影片都睇**：YouTube demo/tutorial 有時比文字文件快理解實際用法
- **反編譯係最後手段**：先睇有冇公開資訊（source/API/docs），冇先 decompile

**🎬 影片理解能力（SK 2026-08-27 確認——唔止 YouTube，所有影片）：**

**任何來源嘅影片都可以處理：**
```
來源：YouTube / Bilibili / Twitch / Vimeo / Twitter(X) / Reddit / 抖音 / TikTok / 本地檔案（mp4/mkv/avi/mov）/ 任何 URL
  → yt-dlp（1000+ 網站）+ ffmpeg
  → 抽音訊 → faster-whisper ASR（本地 GPU，含廣東話）→ 完整文字 ✅
  → 抽關鍵幀 → vision 分析 → 畫面理解 🟡
  → 有字幕 → 直讀
```

**工具（全部已有）**：yt-dlp（有 cookies）、ffmpeg、faster-whisper（本地）、vision。

**能力**：語音內容 100% 完整；畫面大概理解（抽幀）；總結/提取重點/答問題。

**🧠 Mage-VL（SK 2026-08-27 查證——「mage_v1」= Microsoft Mage-VL）——JARVIS 嘅「眼」進階：**

- **Microsoft Mage-VL**：codec-native streaming 多模態 foundation model（4B）——影片理解，唔係逐幀 decode，而係跟 video codec 結構即時 streaming 理解
- HF：`microsoft/Mage-VL`（downloads 49.8 萬，Apache 2.0，2026-08-10 更新）
- **RTX 5090（32GB）完全跑得起 4B model**
- 用途：JARVIS「眼」終極版——真正 streaming 睇影片/實時畫面，取代/增強「抽幀+vision」
- 待驗證：本地跑 Mage-VL 做 streaming 影片理解（Phase 8 後續/獨立 spike）

**安全原則**：只整合 SK 明確想接入嘅程式；反編譯只為理解（唔會改壞原程式——用 backup + config 層面修改）。

**待驗證**：SK 下次開 voice call 時實測 pycaw session 會唔會變 ACTIVE（預期會）——開通話時 check 一次。

**實作方向**：MCP speak tool 接收 `source_chat` 參數；Hermes 側（agent 層）喺非 SK DM 場合唔 call；Jarvis 側 double-check（例如只聽 SK 自己嘅 voice wake，唔會因為 Discord/WhatsApp 訊息而講嘢）。

### 依賴

- Phase 6（品質改善）先做——sidecar 搬遷時一次過用新 wake/STT/TTS
- HUD 後續（overlap check 等）併入 Electron 統一 renderer 時處理
- 8.5 MCP 整合依賴 Hermes `mcp_servers` config + `pip install mcp`（MCP SDK）

---

## 🎯 Current Sprint（而家做緊咩——2026-08-27 起）

> **Tier 分層（見「MVP 分層」）：先 Tier 1，未完成唔開始 Tier 2/3。**

**而家第一步（Tier 1）：**
1. **A2 wake rearm 修復**（叫唔醒元兇——最細、最高優先）
2. **A wake VAD 防誤觸**
3. **B STT GPU 加速**
4. **D1/D2/D3** streaming TTS + 短確認 + 縮短等待

**Tier 1 完成定義**：① BGM 30s 0 誤觸 ② STT GPU ≥3x 快 ③ 喊完→有聲 ≤3s。

**之後：Tier 2（voice call 安全）→ Tier 3（願景）。**

---

## Files likely to change（全項目索引）

| 檔案 | 相關 Phase |
|---|---|
| `jarvis-pc/src/jarvis/wake.py` | Phase 6 A/D3 |
| `jarvis-pc/src/jarvis/ear.py` | Phase 6 B |
| `jarvis-pc/src/jarvis/mouth.py` | Phase 6 D1 |
| `jarvis-pc/src/jarvis/shell_app.py` | Phase 6 D2 + Phase 5/8.2 |
| `jarvis-pc/src/jarvis/settings_ui.py` | Phase 5/8.2 |
| `jarvis-pc/src/jarvis/engine.py` | Phase 2（已完成） |
| `jarvis-pc/src/jarvis/hermes_bridge.py` | Phase 3（SSE 完成） |
| `jarvis-pc/src/jarvis/mcp_alerts_http.py` | **Phase 8.5 MCP 整合（核心！）** |
| `jarvis-pc/src/jarvis/alert_store.py` | Phase 7（alerts） |
| `jarvis-hud/main.js` | HUD 後續 + Phase 8 |
| `jarvis-hud/renderer/index.html` | HUD 視覺 |
| `jarvis-hud/chrome-extension/*` | Media Bridge |
| `%LOCALAPPDATA%/hermes/config.yaml` | Phase 8.5（`mcp_servers` 註冊） |
