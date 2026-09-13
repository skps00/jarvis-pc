# Settings Field Map — settings.html ↔ settings.json ↔ IPC

> 對應 code：`hud/settings.html`、`hud/settings-preload.js`、`hud/main.js`（`clampSettingsPatch`）
> 目的：加減設定項時，呢張表係「HTML id ↔ settings.json key ↔ 型別 ↔ clamp ↔ IPC」嘅單一對照。
> 更新：2026-08-31（E 文檔項，pass1 #3 skip 補返）

## 0. IPC 流程（settings-preload.js → main.js）

| 方法 | IPC channel | main.js handler | 實作 |
|---|---|---|---|
| `api.load()` | `settings:load` | 538-555 | sidecar `GET http://127.0.0.1:8765/settings`（Bearer = `alerts/mcp_token.txt`）→ fallback 直接讀 settings.json |
| `api.save(obj)` | `settings:save` | 638-664 | `clampSettingsPatch(obj)` → sidecar `POST /settings`（Bearer）→ fallback 直接寫 |
| `api.scanInputs()` | `settings:scan-inputs` | 665 | `scanAudioDevices('input')` |
| `api.scanOutputs()` | `settings:scan-outputs` | 666 | `scanAudioDevices('output')` |
| `api.openHermes()` | `settings:open-hermes` | 680-683 | `shell.openExternal(hermes_base_url)` |
| `api.probeHermes()` | `settings:probe-hermes` | 684-692 | `GET {hermes_base_url}/api/health`（4s timeout） |
| `api.testAlert()` | `settings:test-alert` | 693-701 | `python -c "from jarvis.mouth import speak; speak('Test alert, sir.')"` |
| `api.close()` | `settings:close` | 667-669 | 關 settings window |

**注意（H2 單一 writer）**：save 一律經 sidecar `POST /settings`；直接寫檔只係 sidecar down 時嘅 fallback。
改 settings 唔好喺別處直接寫 settings.json。

## 1. 全部 Field（按 collect() 順序）

`R` = range slider，`C` = checkbox，`S` = select，`N` = number，`P` = password，`T` = text，`TA` = textarea。
Clamp 只列出 main.js `clampSettingsPatch` 有處理嘅；其餘原樣傳。

| # | HTML id | settings key | UI | Default | Clamp（main.js） | 備註 |
|---|---|---|---|---|---|---|
| 1 | wake_threshold | wake_threshold | R 0.25-0.75 | 0.50 | [0.25, 0.99] | slider；顯示值 wakeThresholdVal |
| 2 | wake_mic_device | wake_mic_device | T | "" | — | device picker 可 scan；例「麥克風 (2- Arctis Nova 7)」 |
| 3 | tts_output_device | tts_output_device | T | "" | — | device picker 可 scan |
| 4 | aec_enabled | aec_enabled | C | false | !!bool | |
| 5 | aec_reference_device | aec_reference_device | T | "" | trim | 例「SteelSeries Sonar - Media」 |
| 6 | speaker_gate | speaker_gate | C | true（load 用 `!== false`） | !!bool | 聲紋 gate |
| 7 | asr_provider | asr_provider | S | sensevoice | — | sensevoice / fun_asr / openai_audio |
| 8 | voice_frontend | voice_frontend | S | hermes | — | jarvis / hermes |
| 9 | llm_preset | llm_preset | S | deepseek | LLM_PRESETS（deepseek/mimo/ollama/custom） | |
| 10 | llm_api_key | llm_api_key | P | "" | trim | **dpapi 加密**（settings.json 存 `dpapi:`） |
| 11 | llm_base_url | llm_base_url | T | "" | trim + strip 尾 `/` | |
| 12 | llm_model | llm_model | T | "" | trim | |
| 13 | custom_models | custom_models | TA（readonly） | [] | — | load 時 join `\n`、collect 時 split |
| 14 | hermes_enabled | hermes_enabled | C | false | !!bool | |
| 15 | hermes_trusted | hermes_trusted | C | false | !!bool | |
| 16 | hermes_base_url | hermes_base_url | T | http://127.0.0.1:8688 | trim + 空值 → default | |
| 17 | alert_voice | alert_voice | C | true（`!== false`） | !!bool | |
| 18 | alert_cd_seconds | alert_cd_seconds | N 0-120 | 0 | [0, 120] | |
| 19 | alert_tts | alert_tts | S | hermes | hermes/piper/off | |
| 20 | asr_api_key | asr_api_key | P | "" | — | dpapi 加密 |
| 21 | asr_base_url | asr_base_url | T | "" | — | |
| 22 | asr_model | asr_model | T | "" | — | |
| 23 | wake_cd_seconds | wake_cd_seconds | N 0.5-30 | 3 | [0.5, 30] | |
| 24 | record_seconds | record_seconds | N 1-10 | 4 | [1, 10] | |
| 25 | text_wake | text_wake | C | false | !!bool | |
| 26 | stt_preload | stt_preload | C | false | !!bool | SenseVoice 預載（慳 RAM） |
| 27 | speaker_threshold | speaker_threshold | R 0.10-0.99 | 0.50 | [0.10, 0.99] | 顯示值 speakerThresholdVal |
| 28 | hotkey | hotkey | T | "" | — | |
| 29 | tts_enabled | tts_enabled | C | true（`!== false`） | !!bool | |
| 30 | tts_ack | tts_ack | C | true（`!== false`） | !!bool | |
| 31 | tts_length_scale | tts_length_scale | N 0.3-2.0 | 0.85 | [0.3, 2.0] | |
| 32 | tts_volume | tts_volume | N 0.1-3.0 | 1.6 | [0.1, 3.0] | |
| 33 | alert_discord | alert_discord | C | true（`!== false`） | !!bool | |
| 34 | alert_cursor | alert_cursor | C | true（`!== false`） | !!bool | |
| 35 | alert_cursor_hooks | alert_cursor_hooks | C | true（`!== false`） | !!bool | |
| 36 | alert_cursor_toast | alert_cursor_toast | C | true（`!== false`） | !!bool | |
| 37 | alert_cursor_uia | alert_cursor_uia | C | true（`!== false`） | !!bool | |
| 38 | alert_cursor_watch | alert_cursor_watch | C | false | !!bool | |
| 39 | alert_whatsapp | alert_whatsapp | C | true（`!== false`） | !!bool | |
| 40 | alert_always | alert_always | C | true（`!== false`） | !!bool | |
| 41 | alert_extra | alert_extra | T | "" | — | 逗號分隔 app 名 |
| 42 | alerts_mcp_port | alerts_mcp_port | N 1024-65535 | 8765 | [1024, 65535] | |
| 43 | alerts_mcp_token | alerts_mcp_token | P | "" | — | **明文**（MCP 8765 Bearer，唔 dpapi） |
| 44 | alert_gpu_health | alert_gpu_health | C | true（`!== false`） | !!bool | |
| 45 | alert_gpu_poll_s | alert_gpu_poll_s | N 1-120 | 5 | [1, 120] | |
| 46 | mage_enabled | mage_enabled | C | false | !!bool | Mage-VL 眼（9.5GB VRAM，lazy） |
| 47 | mage_prompt_default | mage_prompt_default | T | "" | — | |
| 48 | vc_fail_closed | vc_fail_closed | C | false | !!bool | F3：pycaw 失效 → fail-closed mute |

**唯讀 UI（唔 collect，load 時由 JS 產生）**：
- `alertAppsSummary`（#34/#39/#41 嘅人話摘要，`buildAlertAppsSummary()`）
- `custom_models`（見 #13）
- `hermesStatus` / `alertTestStatus` / `inputScanHint` / `outputScanHint`（狀態提示）

## 2. Secrets 處理

| Key | 儲存方式 | 原因 |
|---|---|---|
| llm_api_key / asr_api_key | `dpapi:` 加密（sidecar load 解密/save 加密） | H4：settings.html 唔會 render dpapi blob |
| alerts_mcp_token / hermes_api.key | 明文 | MCP/API 早期就要用，解密鏈增加 boot 複雜度 |

## 3. 加新設定項嘅 checklist

1. `settings.py` dataclass + `_clamp()`（sidecar 端）。
2. `settings.html`：加 HTML field + `loadSettings()` 讀 + `collect()` 寫。
3. `main.js` `clampSettingsPatch`：mirror `settings.py _clamp()`（兩邊要同步，註解已標明）。
4. 有需要 → `shell_app` `_start_settings_apply_watch` 加 live-apply。
5. 更新呢張表。
