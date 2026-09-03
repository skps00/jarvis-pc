# Skills 整合審查 Plan（128 skills → 重複/可整合盤點）

> **For Hermes:** 純分析 + 提議 plan（無 code 改動）。合併/刪除動作全部等 SK 逐項批准先做。
> 方法：真證據——逐一讀 SKILL.md frontmatter + body + 比對 trigger/功能，唔靠 description 估。

**Goal:** 盤點 128 個 skills 嘅重複/可整合項，每項有具體建議（合併成邊個、刪邊個、定係唔郁），SK 拍板後先執行。

**Architecture:** 分三類——A 真重複（功能重疊、agent 會揀錯）／B 分層互補（設計上分工，可加 cross-link 但唔合併）／C 唔算重疊（唔郁）。

**Review 後最終範圍（2026-09-02 adversarial review 裁決 6:4 支持有限合併）：**
- ✅ 執行合併：A1 short-video（-2）、A4 llm-loop（-1）、A5 aux-model（-1）→ **128 → 124**
- ⚠️ 輕量 cross-link（唔刪）：A2 windows 群、A3 MC 群
- 唔郁：B 群 + C 群

---

## 審查方法（已做）

1. `os.walk` 掃描全部 128 skills（分類分佈：software-development 31 / productivity 18 / creative 16 / autonomous-ai-agents 13 / ...）
2. 高嫌疑群逐一讀 SKILL.md body（windows 自動化 / short-video / MC mod / voice / HUD / llm-loop / aux-models 等）
3. 用 difflib 比對相似度（字面低但功能重疊——因為各 skill 累積唔同實戰細節）
4. 快速對照 trigger conditions 判斷「同一個任務散落幾個 skill」

---

## A. 真重複（建議合併——agent 而家會揀錯/load 錯）

> **Review 後裁決（2026-09-02 adversarial review）：** 實測 skills index 全個先 ~1,747 tokens，合併慳嘅 context ≈ 260 tokens（微不足道）。真正 benefit = 消除 100% 重疊 + 減 drift。**只合併「100% 重疊、冇獨立 value」嘅組（A1/A4/A5）；多角度實戰筆記組（A2/A3）改做輕量 cross-link，唔刪。**

### A1. Short-video 三胞胎 → 合併成 1 個 ✅ 執行
| Skill | Size | 內容 |
|---|---|---|
| `douyin-tiktok-content` | 6.6KB + favorites browser ref | 最完整：API + ASR + cookies + 收藏 scan reference |
| `short-video-content` | 4.6KB | 同一 trigger（v.douyin.com / tiktok.com link 要讀） |
| `short-video-platform-read` | 2.8KB | 又係同一 trigger（douyin notes 讀取） |

**證據**：三個 trigger 100% 重疊——「user 貼 douyin/tiktok link → 讀內容」。`short-video-content` + `short-video-platform-read` 係早期版本，`douyin-tiktok-content` 已包含晒所有功能 + 更新嘅收藏 scan。

**建議**：保留 `douyin-tiktok-content`（最完整）；刪 `short-video-content` + `short-video-platform-read`（功能已被 cover）。
**風險**：低——但刪前要 diff 確認冇獨特 content（short-video-content 可能有一兩個 douyin-tiktok-content 冇嘅 snippet）。

### A2. Windows 自動化群 → ⚠️ 唔刪——輕量 cross-link + 統一 boundary
> Review 改判：5 個 skill 各有多角度實戰 reference（cua-driver-debugging / wallpaper-engine / game-detection / headless-chrome...），merge 成大檔 = load 更重 + description 57-char cover 唔晒。真正問題係 drift（activity_monitor.py 被 5 個引用）+ boundary 唔清。

| Skill | Size | 定位 |
|---|---|---|
| `windows-desktop-automation` | 8.5KB + activity_monitor.py | computer_use/GUI 自動化 + 活動 gate |
| `windows-background-automation` | 5.3KB + hw_monitor.py | 背景自動化（活動感知 + 截圖） |
| `windows-headless-ops` | 3.8KB | headless Windows ops（無彈窗） |
| `windows-focus-safe-automation` | 5.4KB | 無彈窗無搶焦點自動化 |
| `windows-activity-aware-operations` | 6.8KB | 活動偵測 + 無彈窗原則 |
| `windows-computer-use` | (automation cat) | cua-driver hangs 診斷 |
| `windows-headless-capture` / `windows-screen-capture` | 4.5KB / 2.3KB | 截圖（monitor/region/HTML→PNG） |

**做法（唔刪）：**
1. **統一 boundary**：喺每個 skill 開頭加「Related：呢組仲有 X/Y/Z，揀邊個取決於……」（例如：GUI 操作→desktop-automation；純 headless 截圖→headless-ops；cua-driver 壞→computer-use）
2. **減 drift**：activity_monitor.py 只喺一個 skill 保持 canonical（windows-desktop-automation），其他引用改 link 指向
3. 唔 merge、唔刪——保留各自實戰 reference
**風險**：低（只加 pointer，唔郁內容）

### A3. MC mod 四胞胎（super_minecraft_AI_player）→ ⚠️ 唔刪——輕量 cross-link
> Review 改判：四胞胎字面相似度低（0.05-0.12）但功能重疊——係「同一 project 多角度實戰筆記」（各自有 reference：deepseek-function-calling / jei-category-priority-debug / llm-api-repro / deepseek-tool-loop-debugging）。合併成大檔 = load 更重；**真正 fix = boundary 分明 + cross-link**，令 agent 揀到啱嗰本而唔使讀晒四本。

| Skill | Size | 內容 |
|---|---|---|
| `minecraft-llm-assistant-mod` | 6.5KB | trigger = super_minecraft_AI_player 任務 |
| `minecraft-modpack-ai-development` | 12.7KB + 3 refs | build/smoke/Ask engine + deepseek 坑 |
| `pack-ai-mod-development` | 10.9KB + 1 ref | 改 AskEngine/AskToolLoop + cursor-agent |
| `pack-ai-deepseek-llm` | 4.4KB | deepseek thinking mode 坑 |

**做法（唔刪）：**
1. 每個 skill 開頭加「Related/boundary」：`minecraft-modpack-ai-development` = 總覽+build/smoke；`pack-ai-mod-development` = code 改動細節；`pack-ai-deepseek-llm` = DeepSeek LLM 坑；`minecraft-llm-assistant-mod` = LLM/問答功能。揀邊本取決於任務類型。
2. 重複內容（deepseek tool loop 出現喺 3 本）——喺其中一本留 canonical，其他 link 指向。
3. 唔 merge、唔刪（MC 係 SK 最高優先 project，保守）
**風險**：低

### A4. LLM tool-loop 雙胞胎 → 合併成 1 個 ✅ 執行
| Skill | Size | 內容 |
|---|---|---|
| `llm-tool-calling-reliability` | 4.4KB + ref | LLM tool loop 診斷（no calls/wrong args/loops） |
| `llm-tool-loop-integration` | 3.8KB + ref | 同一主題（app 用 tools multi-round loop） |

**證據**：trigger 幾乎一樣（「LLM agent 有 tools schema 但 model 唔 call / call 錯 / loop」）。兩個都有 deepseek thinking mode reference（一份喺 autonomous-ai-agents，一份喺 software-development——分類都散咗）。

**建議**：保留 `llm-tool-calling-reliability`（喺 software-development，同 MC/deepseek 坑近）；`llm-tool-loop-integration` 內容 merge 入去，刪。
**風險**：低。

### A5. Hermes aux-model 雙胞胎 → 合併成 1 個 ✅ 執行
| Skill | Size | 內容 |
|---|---|---|
| `hermes-aux-model-setup` | 3.8KB | aux config（vision/video/compression） |
| `hermes-aux-models` | 4.5KB | 同一主題（trigger「No LLM provider configured for task」） |

**證據**：標題一樣「Hermes Auxiliary Model Setup」，body 都講 `auxiliary.*` config provider auto fix。兩個都有 deepseek-vision.md reference。重複。

**建議**：保留 `hermes-aux-models`（較新、有 video/compression/skills_hub 覆蓋）；`hermes-aux-model-setup` merge 入去，刪。
**風險**：低。

---

## B. 分層互補（唔合併，但可加 cross-link 防揀錯）

| 群 | Skills | 判斷 |
|---|---|---|
| B1. Email | `email-inbox-triage`（決策層）+ `himalaya`/`google-workspace`（connector 層） | 設計上分層——triage 寫明「connector skills own provider commands」。**唔郁**，但確認 description 已講清楚分工 |
| B2. PDF/doc | `pdf`（結構操作）+ `nano-pdf`（NL 編輯）+ `ocr-and-documents`（掃描文字） | 分工清楚（nano-pdf 開頭已 link pdf + ocr）。**唔郁** |
| B3. Session | `hermes-session-recall`（查歷史內容）+ `session-librarian`（整理/改名/歸檔） | 功能唔同（一個 recall 一個 librarian）。**唔郁** |
| B4. Voice | `hermes-voice-windows`（Hermes voice setup）+ `windows-voice-pipeline`（Jarvis+Hermes debug）+ `jarvis-voice-assistant`（JARVIS 專案總覽） | 有分層但 aec-implementation.md 出現喺 2 個度（重複 reference）。**可選**：uniq reference（一個 keep、另一個 link） |
| B5. HUD | `cinematic-hud-overlay`（設計/美學）+ `electron-windows-overlay`（Electron 技術）+ `jarvis-hud-electron-editing-pitfalls`（jarvis 專案） | 三層分明（general design → electron class → jarvis specific）。**唔郁** |

---

## C. 唔算重疊（唔郁——已確認分工）

- `windows-hardware-monitoring`（硬體監控——同 automation 群唔同，keep）
- `windows-computer-use`（cua-driver 診斷——專注問題修復，唔係 general automation，keep）
- `windows-app-launch-focus`（app launch/focus 技術——特定領域，keep 或併入 umbrella A2 可選）
- `email`、`github`、`research`、`productivity` 其他——各自獨立

---

## 執行步驟（SK 批准後）

1. **A1 short-video merge**：diff `short-video-content` + `short-video-platform-read` vs `douyin-tiktok-content`（已做初步——冇獨特內容）→ 補任何漏咗嘅 snippet → 刪 2 個
2. **A4 llm-loop merge**：diff `llm-tool-loop-integration` vs `llm-tool-calling-reliability` → merge 獨特內容 + reference → 刪 1 個
3. **A5 aux-model merge**：diff `hermes-aux-model-setup` vs `hermes-aux-models` → merge → 刪 1 個
4. **A2 windows cross-link**：5 個 skill 開頭加 Related/boundary pointer（GUI→desktop-automation；headless→headless-ops；cua-driver 壞→computer-use）；activity_monitor.py canonical 指向 desktop-automation
5. **A3 MC cross-link**：4 個 skill 開頭加 Related/boundary（總覽 vs code 改動 vs deepseek 坑 vs LLM 功能）
6. Update memory（如有 skill 名稱 reference——已 grep 冇）
7. 驗收

## 驗收標準

- [ ] A1/A4/A5 已 merge（umbrella skill 包含被刪 skill 所有獨特內容 + reference 保留）
- [ ] 128 → 124（減 4：short-video-content / short-video-platform-read / llm-tool-loop-integration / hermes-aux-model-setup）
- [ ] A2/A3 每個 skill 有 Related/boundary pointer（grep 驗證）
- [ ] 冇 lose 任何獨特 reference/script（merge 前 diff 清單做證據）
- [ ] 冇 SK 未批准嘅刪除

## Risks

- R1. **Merge 唔齊 lose 累積坑**（最大風險）：每個 skill 係多次實戰累積——merge 前 diff 逐項對，唔好淨係睇 size
- R2. **Description 太短 cover 唔晒 trigger**：umbrella description 得 57-60 chars——要揀最重要 trigger，其他放 body
- R3. **其他 AGENTS.md/memory/session 引用舊 skill 名**：grep 全部 reference 先刪
- R4. **A2 windows 群 drift 已存在**（activity-monitor.md vs game-session-detection.md 兩份）——merge 時要決定邊份係 source of truth
- R5. **MC 群風險最高**（SK 最高優先 project）——merge 完要真任務驗證先刪

## Open Questions（SK 拍板）

1. **批准範圍**：A1/A4/A5 merge（減 4）+ A2/A3 cross-link 一齊做？定淨係 merge 低風險三組先？
2. **刪除定保留**：skill 冇 archive 機制；可以直接刪（merge 內容已保留）或者移到 `skills/_deprecated/` 保留 30 日再刪？——預設：直接刪（merge 內容已保留，冇需要留屍）
3. **B4 voice reference 重複**（aec-implementation.md ×2）要唔要 uniq？——預設：低優先，下次郁 voice 先一齊做
