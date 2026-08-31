# Tier 3 詳細 Implementation Plan（JARVIS ONE 願景）

> 主 plan：`JARVIS_MASTER_PLAN.md`。本檔係 Tier 3 嘅詳細方案。
> **前置**：Tier 1 + Tier 2 完成先開始。
> ⚠️ Tier 3 係願景層——部分要先 spike（Mage-VL 試跑、IPC 選型），詳細 plan 標明「待 spike」位，唔會假設已驗證。

---

## Step 8.5 — MCP 雙向整合（Jarvis 做 MCP server）

### 目標

擴展 Jarvis 現有 MCP server（`mcp_alerts_http.py`，FastMCP @ 8765），加 `speak`/`sensors` 等 tools，令 Hermes 可以叫 Jarvis 唸嘢、讀感應器。

### ✅ 已有基建（實測確認）

- Jarvis 已有 MCP server：`mcp_alerts_http.py` `build_mcp()`（FastMCP，4 個 tools：peek_alert/ack_alert/list_alerts/alert_stats）
- Hermes config 已註冊 `mcp_servers.jarvis-alerts`（HTTP 8765 + Bearer token）
- Hermes `mcp` SDK 已裝；Jarvis python 有 `mcp` 套件

### 改動方案

**位置**：`mcp_alerts_http.py`（加 tools）+ Hermes config（加權限）

**Step 1 — 加 `speak` tool**
```python
@mcp.tool()
def speak(text: str, source_chat: str = "") -> dict:
    """叫 Jarvis 用語音唸（英文，背景，唔彈窗）。source_chat 用嚟做來源過濾。"""
    # 檢查來源過濾（source_chat 要係 SK 自己 DM）
    # 檢查 voice_call / playing 狀態（靜音）
    from jarvis.mouth import speak as tts_speak
    ok = tts_speak(text, force=True)
    return {"ok": ok}
```

**Step 2 — 加 `sensors` tool**
```python
@mcp.tool()
def sensors() -> dict:
    """讀 GPU/CPU 感應器（NVML）。"""
    # 讀 NVML GPU 健康（現有 sensor 邏輯）
    return {"gpu": {...}, "cpu": {...}}
```

**Step 3 — 加 `wake_status` / `set_tts`（按需）**

### 測試

```bash
# 起 jarvis serve（MCP server 跟 serve 起）
# Hermes 側 call mcp_jarvis_speak("test") → 應該唸
```

### 驗證標準

- [ ] Hermes（Discord）call `mcp_jarvis_speak` → Jarvis 唸
- [ ] `source_chat` 非 SK DM → 拒絕（來源過濾）
- [ ] Jarvis 死咗 → Hermes fallback 文字（唔壞 conversation）

### 風險

- 低。基建已存在，只係加 tools。安全層（限頻/來源過濾/遊戲中 guard）要一齊做。

---

## Phase 8 — JARVIS ONE（Electron 一個 app）

### 目標

jarvis-pc（Python）+ jarvis-hud（Electron）合併做一個 app、一個 tray、一個入口。

### 架構（已定方向，細節待 spike）

```
Electron main（jarvis-hud 擴展）
  ├─ Tray（單一入口）
  ├─ HUD overlay / Companion / Settings / Dock（Iron Man HTML）
  └─ spawn Python sidecar（jarvis serve 包裝）
        ├─ wake/STT/TTS/hermes_bridge
        └─ IPC（stdin JSON-RPC 或 localhost HTTP ← 待 spike 選型）
```

### 遷移步驟（每步獨立驗證 + 回滾）

| Step | 內容 | 驗證 | 風險 |
|---|---|---|---|
| 8.1 | Electron spawn sidecar + tray 管晒 | 一個 tray 一個 process tree；退出一齊收；無 console | 低 |
| 8.2 | companion/settings tkinter → Electron HTML | 無 tkinter 視窗 | 中 |
| 8.3 | 語音 sidecar 化 + IPC | 喊醒 → HUD 顯示 + 語音 | 高（IPC 待定） |
| 8.4 | HUD + companion 統一 renderer | Iron Man 視覺統一 | 中 |
| 8.5 | MCP 整合（見上） | 雙向互通 | 低 |

### 待 spike 確認（開始前必須先做）

1. **IPC 選型**：stdio JSON-RPC vs localhost HTTP——實測邊個穩 + 易做（sidecar 已有 HTTP 經驗，傾向 HTTP）
2. **Electron spawn pythonw hidden**——確認 windowsHide 生效、無 console 閃
3. **單一 tray**——現有 jarvis tray（tkinter）+ HUD 窗口點整合

### 風險

- **高**（大工程）。要分 5 個細 step，每步可回滾。Phase 6 嘅 wake 改動喺 sidecar 化時一次過用（避免做兩次）。

---

## Mage-VL — streaming 影片理解（JARVIS 嘅「眼」）

### 目標

本地跑 Microsoft Mage-VL（4B）做 streaming 影片理解，取代「抽幀+vision」。

### 待 spike（未驗證，唔好假設）

1. **下載**：`huggingface_hub.snapshot_download("microsoft/Mage-VL")`——size 待查（4B model，可能 8-16GB）
2. **跑得起**：RTX 5090 32GB 跑 4B——應該得，但要實測 VRAM + 速度
3. **streaming 輸入**：Mage-VL 食影片流/幀？定係要 preprocess？——讀官方 docs/README
4. **整合**：Mage-VL 做獨立 service（MCP tool `mcp_jarvis_vision`）定係 Hermes 直接 call？

### 詳細 plan（spike 之後先寫）

- [ ] spike：下載 + 跑一段 30 秒影片 → 確認理解品質 + 速度 + VRAM
- [ ] spike 通過後，先定「眼」嘅接口（MCP tool？JARVIS sidecar module？）
- [ ] 再寫詳細整合 plan

### 風險

- 高。新 model（2026-08 出），生態未成熟，可能踩坑。**先 spike，唔好一嚟就整合。**

---

## 自我整合第三方程式（反編譯 + 接入）

### 目標

JARVIS 見到新程式識得自己 research + 接入。

### SOP（已定，見主 plan）——詳細化

```
① 偵測程式類型（file header / process 分析）
② 上網查（官方 docs → GitHub issues → 論壇 → 影片）——「有眼有耳」
③ 有官方 API/MCP/plugin → 用官方方式
④ 冇 → 反編譯（asar / pycdc / ILSpy / Ghidra）
⑤ 理解架構 → 揀接入方式（MCP server / config / computer_use）
⑥ 測試 → 寫入 skill
```

### 工具安裝清單（要用先裝）

| 工具 | 用途 | 安裝 |
|---|---|---|
| @electron/asar | Electron 解包 | ✅ 已用過（npx） |
| uncompyle6/pycdc | Python bytecode | 要用先裝 |
| ILSpy | .NET | 要用先裝 |
| Ghidra | 原生 exe | 要用先裝（大） |

### 風險

- 法務：只反編譯有合法授權嘅程式；EULA 禁止 reverse engineering 要提 SK。
- 唔會預先裝晒所有工具——用到邊個裝邊個（避免 bloat）。

---

## 擴展連接（平台 / MCP / IoT / webhook）

### 詳細 plan（按需觸發）

| 項目 | 詳細做法 | 觸發條件 |
|---|---|---|
| Telegram/WhatsApp | `hermes gateway setup` 加 platform + config | SK 想用手機同 JARVIS 傾 |
| MCP servers | `mcp_servers` config 加 filesystem/github/notion | SK 想接入某服務 |
| Philips Hue | `openhue` skill + bridge IP + token | SK 有 Hue 燈想控制 |
| Webhook | `hermes webhook subscribe` | 外部事件通知 |

**原則**：每個連接遵守「背景執行 + 來源過濾 + voice call 靜音」。

---

## Tier 3 完成定義

1. JARVIS ONE 一個 app、一個 tray、背景執行
2. MCP 雙向整合（Hermes ⇄ Jarvis）
3. Mage-VL「眼」跑得順（spike 通過後）
4. 自我整合 SOP 行得通（下次新程式直接套用）
5. 擴展連接按需生效

---

## 執行順序建議

```
8.5 MCP 整合（最細，基建已有）→ Phase 8 JARVIS ONE（分 8.1-8.4 細步）
→ Mage-VL spike（獨立，可並行）→ 自我整合/擴展（按需）
```

**關鍵：8.5 同 Mage-VL spike 可以獨立提前做（唔依賴 Phase 8）。Phase 8 係最大工程，要分細步逐個回滾。**
