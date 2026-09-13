# Discord Voice Out Implementation Plan

> **For Hermes:** use this plan after SK approval.

**Goal:** SK 喺 Discord 同 Hermes 傾偈時，JARVIS 喺部機用 voice 唸出 Hermes 回覆嘅英文短版（≤20 words）。

**Architecture:** 用現有 jarvis-alerts MCP（8765）嘅 `jarvis_speak` tool——Hermes 每次喺 Discord 覆 SK 後，如果開關開咗，自動 call speak 唸一句英文摘要。零 sidecar code 改動（MCP tool 已有限頻 + playing 拒絕 + SK DM source gate）。

**Tech Stack:** Hermes skill 規則 + Jarvis settings toggle + 現有 `mcp__jarvis_alerts__jarvis_speak`。

---

## 背景

- SK 想要：Discord 打字傾偈 + 部機有 JARVIS 把聲唸回覆。
- 現有基建：`jarvis_speak` MCP tool（限頻 ≤1 req/2s、playing 拒絕、SK DM source 檢查）已經 work（wake 通道用緊）。
- Master plan 原方案 A（Jarvis 讀 Hermes session log）——lag + 要讀 sqlite，唔及 MCP push 直接。
- **無需改 JARVIS sidecar**——呢個係 Hermes 行為層功能。

## 方案設計

### 開關（Jarvis settings）
- 新增 `discord_voice_out`（bool，default **true**——SK 想要呢個功能）：
  - `settings.html` 加 toggle（三處同步：HTML + loadSettings + collect —— §24 陷阱）
  - `main.js` clampSettingsPatch 加 `!!bool`
  - sidecar settings.py dataclass 加 field

### 觸發規則（Hermes skill）
- 新/更新 skill：`jarvis-voice-out`（或者更新 jarvis-companion）：
  - 條件：平台=Discord + 同 SK 自己 DM + Jarvis settings `discord_voice_out=true` + 唔係 playing（jarvis_speak 自己會拒）
  - 動作：Hermes 每次回覆 SK 前，諗一句 **SPEAK 英文短版（≤20 words，JARVIS 英式簡潔）**；回覆送出後 call `jarvis_speak(text=SPEAK)`
  - 回覆本身照常（中文文字 + SPEAK 尾）
  - Gate：技術 troubleshooting 長回覆 → 仍然唸一句短版（「Fixed, sir.」/「Diagnosis done, sir.」）——唔好因為長就唔唸
  - 如果 speak 失敗 → 靜默（唔影響 Discord 回覆）

### 同 voice 通道一致性
- 語音一律英文（契約規則）——SPEAK 內容同 voice 通道一樣要英文
- 唔好重複唸：如果回覆同時觸發其他 TTS（例如 game alert）——jarvis_speak 有限頻 + queue，OK

## Steps

### Task 1: settings 加 `discord_voice_out` toggle
**Files:**
- Modify: `src/jarvis/settings.py`（dataclass + default True）
- Modify: `hud/settings.html`（Advanced section toggle，三處同步）
- Modify: `hud/main.js`（clampSettingsPatch `!!bool`）
- Test: `tests/test_settings.py`（default + roundtrip）

### Task 2: Hermes skill `jarvis-voice-out`
**Files:**
- Create: skill（Discord 回覆 → SPEAK → jarvis_speak 流程）
- 載入規則：Discord 平台 + SK DM 時自動載入

### Task 3: 驗證
- `settings.html` 開關 work（CDP 或 SK 手動）
- SK 喺 Discord 覆一句 → JARVIS 唸英文短版（實測）
- playing 時 call speak → 拒絕（安全 gate 生效）

## Files likely to change
- `src/jarvis/settings.py`、`hud/settings.html`、`hud/main.js`、`tests/test_settings.py`
- 新 skill（Hermes 側）

## Tests / Validation
- settings roundtrip（POST /settings → load 返 True/False）
- 實測：Discord 覆 SK → JARVIS 唸聲（真機）
- 安全：playing 時唔唸（jarvis_speak gate）

## Risks / Open Questions
- **Open Q1**：技術 troubleshooting 對話係咪都唸？（建議：唸，一句短版）——SK 拍板
- **Open Q2**：`discord_voice_out` default true 定 false？（建議 true——你想要呢個功能）
- 每次回覆加一句 SPEAK 生成——model 成本極細（一句）
- jarvis_speak 限頻 2s——連續快速回覆會 drop 部分（可接受，避免 spam）
