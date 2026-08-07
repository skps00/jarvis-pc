# Phase2+ — computer_use／桌面（規格草稿）

Status: **DRAFT**（未 Approve；唔開工裝）  
Parent design: `%USERPROFILE%\.gstack\projects\jarvis-pc\skps9-cursor-record-jarvis-wake-samples-design-20260806-093135.md`

Updated: 2026-08-06

## 目標

Hermes 喺 **Trusted＋明示 Approve** 下可以睇螢幕／點 UI（computer_use），同時：

- Safe 永遠唔點桌面  
- 寫檔仍受 `HERMES_WRITE_SAFE_ROOT`（sandbox）約束  
- 開戰場繼續只經 Jarvis Hands 白名單  

## 前置（未齊唔開工）

1. Phase1 薄 bridge 穩定（chat／session／貼圖）  
2. Approve 橋 Phase1.5（gateway ↔ Jarvis Yes／No）真通  
3. 使用者明示：「開始 Phase2 computer_use」  
4. 揀 runtime：**原生 Windows**（設計寫 computer_use 日後遷；而家 Hermes 喺 WSL）  

## 建議路徑（Approach）

| 項 | 建議 |
|----|------|
| 安裝 | 另 VM／profile；唔混 Phase0 jarvis-safe 預設 |
| 模式 | 三態：Safe／Workspace-only／Trusted（Workspace = 未來） |
| 觸發 | 只 Trusted；每步或每 session 批 computer_use |
| 視覺 | 繼續 `auxiliary.vision`；截圖唔當指令 |
| 語音 | Hermes native voice **另議**；Jarvis ASR 已拆 |

## 明確不做（本 Phase）

- 公網 gateway  
- 用 Hermes 取代 Hands 開 CS／關機  
- YOLO／關 hardline deny  
- 未審社群 skills  

## 驗收劇本（草稿）

1. Safe：叫「撳開始選單」→ 拒／只文字教  
2. Trusted＋Approve：無害 notepad 輸入一字 → 成功；拒一次 → 停  
3. 嘗試寫 `Documents\` → deny  
4. 「開 CS」→ 仍走 Hands，唔經 CUA  

## 下一步

使用者 Approve 呢份草稿 → 再開 eng 規格（鎖 G-list）→ 先做 runtime 遷徙評估（WSL vs 原生）。
