# Phase 0 — Hermes Voice 煙測（wake + barge-in）

目標：證明「講緊可以插嘴」喺 **Hermes Voice** 已通。  
**主路徑 = 你而家嘅 WSL Hermes**（`~/.hermes`，DeepSeek 等已設好嗰套）。

Windows native Hermes（`%LOCALAPPDATA%\hermes`）**已刪**；唔再裝除非你另要求。

## WSL 主路徑

```bash
# WSL 入面
cd ~/.hermes/hermes-agent
# 已裝可跳過
uv pip install -e ".[voice]" -e ".[wake]"   # 或 pip

hermes chat
# /voice on
# /wake on
```

`~/.hermes/config.yaml` 應有（已幫你 append 過可再核）：

```yaml
wake_word:
  enabled: true
  provider: openwakeword
  phrase: "hey jarvis"
  # WSL 本機 PortAudio 常 devices=0 → 用 Desktop 擷 Windows 真咪：
  capture: client    # 配合 `hermes desktop`；純 CLI 可試 local
  openwakeword:
    model: hey_jarvis

voice:
  barge_in: true
  auto_tts: true

stt:
  provider: local
  local:
    model: base

tts:
  provider: edge
  edge:
    voice: "en-US-AriaNeural"
```

### 真咪（WSL 現實）

好多機 WSL `sounddevice` = **0 devices**（即使裝咗 `portaudio19-dev`）。要真咪：

1. **推薦：** WSL 跑 Hermes backend + **`hermes desktop`**，`wake_word.capture: client`（桌面用 Windows 咪，PCM 餵 WSL；官方 wake-word 文檔）
2. 或者修 WSLg／PulseAudio 令 WSL 見到裝置後先用 `capture: local`

純 `hermes chat` 喺 WSL、又 0 devices → wake／voice 會失敗；唔係 Jarvis 問題。

## 驗收劇本（barge-in）

1. WSL：`hermes chat`（或 desktop + client capture）
2. `/voice on` → `/wake on`
3. 講 **「Hey Jarvis」**
4. 叫講長段 → TTS 播緊插嘴「show me」
5. **必須：** TTS 即停 → 跟新指令

| 項 | 記下 |
|----|------|
| 插嘴→停聲延遲 | 體感 |
| 假觸發／假插嘴 | 次數 |
| 咪路徑 | WSL local／desktop client |

## 通過準則

- barge-in 連續 3 次穩定
- Jarvis `voice_frontend=hermes` 時關 Jarvis OWW（避雙 mic）
- Alerts MCP：`docs/hermes_alerts_mcp.md`（Hands 已封存 `attic/hands_mcp/`）

## 自訓 `jarvis.onnx`

`%APPDATA%\Jarvis\wake\jarvis.onnx` → WSL 路徑如 `/mnt/c/Users/.../AppData/Roaming/Jarvis/wake/jarvis.onnx` 寫入 `openwakeword.model`。見 `docs/hermes_architecture.md`。
