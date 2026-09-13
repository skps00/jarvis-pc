# Hermes Bridge Auth & Key Rotation

> 2026-08-29 寫。JARVIS → Hermes API（8642）嘅 Bearer 認證同 key rotation 操作說明。

---

## 現狀（2026-08-29）

- **用途**：JARVIS（`jarvis-pc`）call 本地 Hermes API（`http://127.0.0.1:8642`）用 Bearer token。
- **Key 檔案**：`%APPDATA%\Jarvis\hermes_api.key`（`hermes_bridge.py:_API_KEY_PATH`）
- **生成規則**：`load_or_create_api_key()`（hermes_bridge.py:439）——檔案唔存在或 <16 chars → 生成 `jarvis-<token_hex(16)>` 寫入；存在且 ≥16 → 直接讀。
- **套用**：`_api_headers()` / SSE request 都 `Authorization: Bearer <key>`。
- **冇 rotation 機制**——key 一旦生成就永久用，直到人手刪除。

## Key Rotation（手動）

> Hermes API 側（gateway）接受任何合法 Bearer？——依家 JARVIS 側只係「自己帶 key」，冇驗證對方。Rotation 嘅意義：防止 key 洩漏後長期有效。

### 步驟

1. **停 JARVIS 對話**（確保冇 in-flight request）：
   ```powershell
   # 唔使停 sidecar；bridge 每次 call 先讀 key
   ```
2. **刪舊 key**：
   ```powershell
   Remove-Item "$env:APPDATA\Jarvis\hermes_api.key"
   ```
3. **下次 call 自動生成新 key**：JARVIS 再 call Hermes（wake → reply）時 `load_or_create_api_key()` 會自動建新 key。
4. **驗證**：
   ```powershell
   Get-Content "$env:APPDATA\Jarvis\hermes_api.key"
   # 確認 >16 chars，格式 jarvis-xxxxxxxx…
   ```

### 風險

- 刪 key 瞬間到下次 call 之間：冇 key 檔案 → 下次 call 先生成。**冇 race**（load_or_create 係同步單線程讀寫）。
- Hermes 側如果驗證 key（`HERMES_API_KEY` env / config），rotation 後 Hermes 都要同步新 key——**確認 gateway 有冇 set `HERMES_API_KEY`**：
  ```powershell
  # Hermes 側（hermes home / config）有冇指同一 key？
  ```

## 建議（未實作，記低）

- **自動 rotation**：key 每 30 日自動換（cron / sidecar daily thread 檢查 `mtime > 30d` → regenerate）。
- **Hermes 側驗證**：gateway config 設 `HERMES_API_KEY` 同 JARVIS key 一致——雙向驗證，防 local 惡意 process 直接 call 8642。
- **DPAPI 加密 key 檔案**：配合 `secrets DPAPI` 工作項（REMAINING_WORK H 節），key 檔案明文→加密。

## 相關檔案

| 檔案 | 作用 |
|---|---|
| `jarvis-pc/src/jarvis/hermes_bridge.py` | bridge 主體；`_API_KEY_PATH` / `load_or_create_api_key()` / `_api_headers()` |
| `%APPDATA%\Jarvis\hermes_api.key` | Bearer key（明文，唔提交） |
| `%APPDATA%\Jarvis\host.json` | host 路徑外部化（唔關 auth 事，但同目錄） |
