# Iron Man 視覺完整化 Implementation Plan

> **For Hermes:** use this plan after SK approval.

**Goal:** HUD 全屏 overlay 加 Iron Man 視覺元素——雷達掃描 + 數據流 + 呼吸光環增強（旋轉環已有），唔遮核心資訊、唔影響穿透/點擊、GPU 效能受控。

**Architecture:** 純前端 CSS/HTML（renderer/index.html + hud-theme.css）——CSS keyframes + 漸變 + 偽元素，唔加 JS 邏輯（避免影響現有 IPC/穿透）。

**Tech Stack:** CSS3 animations / conic-gradient / radial-gradient / opacity 分層。**零新依賴。**

---

## 背景

- renderer/index.html 已有：掃描線（scan 9s）、中央反應爐光環（ring r1/r2/r3 旋轉）、核心呼吸（core-idle box-shadow）、波形 canvas、tick 刻度、頭盔標線。
- Master plan HUD 後續：「Iron Man 視覺完整化（旋轉環/雷達掃描/數據流/呼吸光環——已跳過頭盔弧形冠）」。
- ⚠️ 全屏 overlay：動畫要輕（GPU-friendly：transform/opacity only）、元素唔可以阻擋 click-through（HUD setIgnoreMouseEvents）。
- ⚠️ SK 規則：每次改動後檢查元素重疊（OOB「always check overlap」）。

## 方案設計（4 個元素）

### 1. 雷達掃描（radar sweep）
- 位置：核心光環外圍（core-wrap 後方），圓形 conic-gradient 扇形（`conic-gradient(from 0deg, rgba(0,170,248,0.28), transparent 60deg)`）
- 動畫：`radar 4s linear infinite`（旋轉 360°）
- 性質：`position: absolute; border-radius: 50%; pointer-events: none; opacity: 0.35`

### 2. 數據流（data streams）
- 位置：畫面兩側（left/right 邊緣），垂直幼線 + 流動粒子
- 動畫：`stream-down 6s linear infinite`（background-position / translateY）
- 性質：`pointer-events: none; opacity: 0.25`

### 3. 呼吸光環增強（breathing outer ring）
- 位置：核心外圍加一層 pulse ring（`ring.pulse`——border + box-shadow 呼吸）
- 動畫：`pulse-ring 3s ease-in-out infinite`（scale 1→1.06 + opacity 0.5→0.15）
- 同核心 core-idle 區分（外圈大呼吸，內核細呼吸）

### 4. 旋轉環補強（已有 r1/r2/r3）
- 加一層最外圈「掃描弧」：`ring.r4`——border-top 高亮弧（類似 Iron Man 頭盔掃描），`spin 20s linear infinite`
- 唔郁現有 r1-r3（避免視覺回歸）

## Steps

### Task 1: CSS 加 4 組 keyframes + 元素 class
**Files:**
- Modify: `hud/renderer/index.html`（<style> 加 keyframes + .radar/.stream/.pulse/.r4 class；HTML 加對應 div）

**驗證：**
- `node --check`（無 JS 改動但照跑）
- HTML div 平衡（`<div` == `</div>`）
- headless chrome 載入 renderer/index.html → 0 uncaught + 截圖睇視覺

### Task 2: 元素重疊檢查（SK 規則）
- 用 layout_check.js 或 CDP getBoundingClientRect 量新元素同核心資訊（clock/topbar/core label）交疊
- 新視覺元素全部 `pointer-events: none` + 低 opacity → 唔遮資訊

### Task 3: 效能檢查
- CSS 只用 transform/opacity 動畫（GPU compositor）
- 唔加 JS requestAnimationFrame loop（現有 canvas 已經有）
- 驗證：開 HUD 後 GPU 使用率冇顯著上升（nvidia-smi）

### Task 4: 打包 + 換版（如果 SK 要 exe）
- §21 流程：bump version → npm run dist → taskkill → spawn → 更新 3 個 .lnk
- ⚠️ 打包前確認 build.files 有 renderer/**（已有）

## Files likely to change
- `hud/renderer/index.html`（CSS + HTML）
- 可能 `hud/hud-theme.css`（如共用 theme 加變數）
- 唔改 main.js（無 IPC 改動）

## Tests / Validation
1. `node --check` 無 error（如改 JS）
2. HTML div/script 平衡
3. headless chrome 載入 0 uncaught + 截圖（視覺確認）
4. layout_check.js 重疊檢查（核心資訊冇被遮）
5. GPU 使用率冇明顯上升
6. SK 肉眼驗證（Iron Man 感覺）

## Risks / Tradeoffs
- **效能**：全屏動畫多 → GPU 負擔；用 transform/opacity-only + 低 opacity 控制
- **視覺嘈**：元素太多會「花」——每個元素 opacity ≤0.35，主次分明（核心 1.0 > 光環 0.5 > 雷達 0.35 > 數據流 0.25）
- **遮擋**：全部 pointer-events: none + z-index 低於核心資訊
- **Open Q1**：要唔要「頭盔弧形冠」（master plan 話跳過）？——建議唔加（全屏弧冠會遮頂部資訊）
- **Open Q2**：做完淨 dev 版驗證，定打包 exe 換版？（建議：先 dev 版睇效果，滿意先打包）
