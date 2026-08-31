# Hermes Bridge Auth — 現狀、風險與 Rotation 指引

> 對應 code：`src/jarvis/hermes_bridge.py`
> 目的：記錄 sidecar → Hermes API（:8642）嘅認證機制、已知風險，以及點樣安全 rotation。
> 更新：2026-08-31（E 文檔項）

## 1. 機制現狀

JARVIS sidecar 透過本機 Hermes API Server（`127.0.0.1:8642`）問 Hermes（同一個 Discord gateway instance）。認證係 **loopback Bearer token**：

1. **Key 位置**：`%APPDATA%\Jarvis\hermes_api.key`（明文，一行）。
2. **Key 生成**（`load_or_create_api_key()`）：
   - 檔案存在且長度 ≥16 → 直接重用。
   - 否則生成 `jarvis-` + `secrets.token_hex(16)`，寫入檔案。
   - 生成係 **lazy**——每次 `_api_headers()` 都會檢查一次（成本極低）。
3. **使用**：所有 API call（`/v1/capabilities`、`/v1/runs`、SSE events、approval POST）都帶
   `Authorization: Bearer <key>`。同一把 key 用晒全部 channel。
4. **驗證**（`_api_auth_ok()`）：probe `/v1/capabilities`；`401` → 判定 key 唔夾 → `_kill_api_port()` 清埠
   再 `ensure_api_server()` 重起 gateway（新 gateway 讀返同一個 key 檔）。
5. **Fallback**：API 唔得時回落 `hermes chat -q` CLI（`_chat_via_cli`，同一 HERMES_HOME）。
6. **防禦**：key 檔只 bind loopback；`hmac.compare_digest` 用於 MCP 8765 嘅 Bearer 比較（constant-time）。
   （Hermes API server 端嘅驗證邏輯喺 Hermes 本體——本檔假設 gateway 讀同一個 key 檔。）

## 2. 風險

| 風險 | 嚴重度 | 說明 |
|---|---|---|
| 冇 expiry／冇自動 rotation | 中 | Key 生成一次永久有效；一旦洩漏（備份、同步、誤貼）無法自然失效 |
| 明文存放 | 低-中 | `%APPDATA%` 係 user-scope，一般 user 先讀到；但任何跑喺同 user 下嘅 process 都可讀 |
| Loopback-only | 低 | 只聽 `127.0.0.1`，網絡層攻擊面細 |
| 刪檔時序 | 低 | 刪 key 檔 + 重啟 gateway 兩步之間，舊 key 仍有效（短暫） |

## 3. Rotation 方法（手動）

因為 key 係 lazy 生成、gateway 讀同一個檔，rotation = 換檔 + 重啟兩邊：

```bash
# 1. 刪舊 key
rm "%APPDATA%\Jarvis\hermes_api.key"

# 2. 重啟 sidecar（Electron 會自動 respawn ~90s）→ 下次 API call 自動生成新 key
#    （或者只 recycle gateway：python -c "from jarvis.hermes_bridge import recycle_api_server; print(recycle_api_server())"）
```

之後 `load_or_create_api_key()` 會生成新 key，`ensure_api_server()` 起返 gateway 讀新 key。

> 注意：如果 gateway 已經行緊（舊 key 喺 memory），刪檔後要 `recycle_api_server()` 或者
> 手動 kill :8642 等佢重起，否則舊 gateway 會繼續用舊 key 拒絕新 key（`_api_auth_ok` 會 detect 401）。

## 4. 建議（未來，未實作）

- **定期 rotation**：cron 每 30 日執行「刪 key → recycle_api_server」，順便記 H_auth log。
- **ACL 收緊**：`icacls "%APPDATA%\Jarvis\hermes_api.key" /inheritance:r /grant:r "%USERNAME%:F"`。
- **rotation 審計**：rotation 事件寫入 `%APPDATA%\Jarvis\autonomy_state.json` 嘅 H_auth events（同一信任分層）。

## 5. 相關

- MCP 8765 嘅 Bearer（`alerts/mcp_token.txt`）係**另一把** key，唔好同 hermes_api.key 混。
- settings.json 入面 `hermes_api.key` 保持明文（AGENTS.md 註明），唔 DPAPI 加密——因為 sidecar
  啟動早期就要用，解密鏈會加 boot 複雜度（已知 tradeoff）。
