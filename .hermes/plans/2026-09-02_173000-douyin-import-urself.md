# Douyin AI/coding 收藏 → Knowledge Import（「import urself」）

> **For Hermes:** 內容分析任務（無 code 改動，唔需要 cursor-agent）。Plan 已過 adversarial review（2026-09-02）。

**Goal:** 深度分析 SK 抖音收藏入面 101 條 AI/coding 內容，提取可執行嘅 Agent/Codex/vibecoding best practices，對比我哋而家 JARVIS/Hermes workflow，產出 gap 分析 + 吸收建議——令 Hermes 吸收 SK 關注嘅社群智慧。

**Architecture:** 本地 caption 分析為主（captions 已含核心訊息），深睇（下載 + ASR）按需——只有 caption 唔足以判斷內容先觸發（YouTube/抖音 video → yt-dlp + faster-whisper，畫面 → Qwen-VL）。

**Tech Stack:** 已存 JSON（`douyin_favorites_classified.json`）、Python 分析、選擇性 yt-dlp/faster-whisper。

---

## Context（2026-09-02 實測）

- 掃描完成：199 收藏 unique，**101 條 AI/coding**（51%），已分類存檔
- 分類：Agent 工具 37 / Agent 架構 21 / 開源項目 9 / 面試職場 6 / vibecoding 6 / 技巧配置 6 / 本地模型 2 / 其他 AI 14
- Captions（抖音 desc）多數已含核心訊息（好多係「教學型」caption，技巧直接寫喺文字度）——唔使逐條睇片
- 已觀察：SK 收藏嘅 practices 同佢現有 workflow 高度重疊（驗收標準、review 流程、多角度 prompt）——分析重點係「重疊確認 + 新 gap 發掘」
- Data 位置：`C:\Users\skps9\AppData\Local\hermes\cache\browser-use\workspace\20260902_113633_f326f8ff\douyin_favorites_classified.json`

## 分析框架

對每條 AI/coding caption 提取：
1. **核心訊息**（呢條教咩技巧/介紹咩工具）
2. **可執行 practice**（轉化成具體行動規則——例如「第一版完成後叫 agent code review」）
3. **工具/資源**（新工具名、開源項目、prompt 模板）

然後群組合成「best practice 模式」，再對比：

| 維度 | 我哋而家（JARVIS/Hermes workflow） | 收藏反映嘅社群 practice | Gap？ |
|---|---|---|---|
| 驗收標準 | SK 已實行（實際運行逐項驗證） | 相同（#13） | 確認 |
| Code review 流程 | pass1/pass2 已有 | 相同（#31）+「三個月後最脆弱位」 | 確認 |
| 多角度決策 | adversarial review 已有 | COO 5 顧問 prompt（#5） | 確認 |
| 記憶/知識庫 | 未有完整 Obsidian 方案 | Obsidian 永久記憶（#34）、知識庫（#40） | **可能 gap** |
| Skill 工作流 | 已有 skills 系統 | 「AI 接力包」（#12）、Browser-BC 操作→Skill（#38） | **可能 gap** |
| 上下文管理 | 部分（session reset 6:00） | 上下文隔離/任務拆解（#17） | 檢查 |
| 新工具 | — | mcp-builder、vercel-deploy-claimable、RuView 等 | 評估 |

## Output（交付物）

1. **收藏內容知識摘要**：101 條 → 主題深度分析（每主題 3-5 個核心 insight）
2. **Best practice 對照表**：收藏反映嘅 practice vs 我哋現狀（上表完整版）
3. **Gap + 吸收建議**：明確列出「值得吸收」嘅項目 + 每個 gap 嘅**具體改動提議**（新增/更新邊個 skill、調整邊個 workflow）
4. **跟進清單**：邊啲工具/項目值得之後試（新工具評估唔係今次 scope）

## 吸收機制（明確定義——唔係「睇完就算」）

「import urself」嘅實際落地 = **對照現有 skills/workflow → 提議具體改動**：

- 分析 output 唔會直接寫入 memory（已 99% 滿）——而係轉成「**改動提議清單**」，例如：
  - 「新增 skill X（由 #34 Obsidian 記憶方案提煉）」
  - 「更新 skill Y（加 #17 上下文隔離 practice）」
  - 「調整 workflow Z」
- 每個提議：改邊度 + 點改 + 值幾多（效益）
- **SK 逐項批準先改**（唔擅自改 memory/skill/code）
- 真正「吸收」= SK 批準嘅提議落地之後

## 反噪音 filter（唔好吸收 hype）

Caption 分析時標記「營銷/噪音」類（月入 X 刀、AI 員工數量、暴富、一夜成名等無可執行內容）——記錄但**唔入 best practice 對照表**，淨係統計數量。

## 深睇上限

- Caption 已含核心訊息嘅：唔深睇
- Caption 唔夠 + 高價值（工具要知實際用法先判斷值唔值）：**最多 5 條**深睇（yt-dlp + faster-whisper）
- 超過 5 條 → 列入「跟進清單」等 SK 決定

## Scope 註明

今次係**一次性 PoC**（101 條分析 + 吸收提議）。SK 之前提嘅「通用多平台內容吸收 framework」係 follow-up——**唔混埋今次**（framework design 另出 plan）。

## 執行步驟

1. **分析 101 條**（本地 Python + 我閱讀）——每條提取核心 → 群組 → 寫分析 notes（`%TEMP%\douyin_import_notes.md`）
2. **深睇觸發**：caption 分析後，如果某條「工具介紹」要知實際用法先判斷值唔值（例如 mcp-builder、Browser-BC）——yt-dlp 下載該條音訊 + faster-whisper 轉錄（有 cookies）
3. **對照表 + gap 分析**（核心輸出）
4. **吸收**：gap 入面「值得即刻做」嘅——出建議（例如新增 skill / 調整 workflow），但**改動要 SK 批準先做**（唔擅自改 memory/skill）
5. 交付報告（Discord 簡潔版 + 完整 notes 檔案）

## Files

| File | 用途 |
|---|---|
| `%TEMP%\douyin_import_notes.md` | 分析 notes（每條核心提取） |
| `%TEMP%\douyin_import_report.md` | 最終報告（摘要 + 對照 + gap） |

## 驗收標準

- [ ] 101 條全部有分析記錄（notes）
- [ ] Best practice 對照表齊（至少 8 個維度）
- [ ] Gap 清單每個有明確建議（做/唔做 + 點做）
- [ ] 冇未批準嘅 memory/skill/code 改動

## Risks

- **R1. Caption 唔夠深**：部分 caption 得標題冇內容——深睇要時間（每條 2-5 分鐘 ASR）——按「值唔值」排序，caption 已夠嘅唔深睇
- **R2. 主觀吸收**：我分析可能 bias（揀啱自己 workflow 嘅）——用「收藏原文為準」+ 每條記錄原文 key phrase
- **R3. Scope creep**：新工具評估（mcp-builder 等）容易變「試玩 session」——今次只記錄「值得之後試」，唔實際試
- **R4. 收藏內容本身質素參差**：部分係廣告/軟廣（「月入 6000 刀」類）——過濾 marketing 噪音，淨係吸收可執行部分
- **Open**: SK 想要幾深嘅「吸收」？——預設：報告 + gap 建議，SK 批準先改 memory/skill

## Acceptance

- 交付物 4 樣齊（摘要/對照/gap/跟進清單）
- 冇擅自改動
- SK 睇完 report 可以拍板「邊啲吸收」
