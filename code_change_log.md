# 代碼變更與問題日誌

## [2026-07-26] 操作類型：新增

- **文件路徑**：README.md, .gitignore, .env.example, config/profiles.example.yaml, src/jarvis/*, tests/.gitkeep, code_change_log.md
- **變更摘要**：建立 `jarvis-pc` repo 最小骨架（無業務邏輯）。
- **遇到的問題**：
  - 問題1：`create_project` MCP 因 Windows 無 `/bin/sh` 導致 git init 失敗；改用 PowerShell `git init`。
  - 解決方案：手動建目錄與 git。
  - 狀態：✅ 已解決
  - 問題2：`move_agent_to_root` 在空 repo（無 HEAD）失敗。
  - 解決方案：先做初始 commit 再 move。
  - 狀態：✅ 已解決（若仍失敗則手動開資料夾）
- **備註**：對應 gstack 設計 APPROVED。
