# JARVIS

**Just A Rather Very Intelligent System**

Windows 本機語音管家（builder）：熱鍵／系統匣細窗 → 粵英混 STT → 白名單開戰場。

設計定稿：`%USERPROFILE%\.gstack\projects\jarvis-pc\*-design-*.md`（Status: APPROVED）

## v1 範圍

- 熱鍵：`Ctrl+Alt+J`
- 規則優先：`open/開/launch/…` + 已登錄名稱
- Chrome：`--restore-last-session`（不送鍵）
- Python 系統匣 + 細窗；無 TTS／HUD／Hermes-as-core

## 快速結構

```
config/          # profiles 範例（真實路徑勿提交密鑰）
src/             # 應用程式碼（之後）
tests/           # 測試
```

## 開發

（Hands CLI／STT 接線尚未開始——等「開始實作 v1」。）
