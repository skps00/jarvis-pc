# 多平台內容吸收 Framework（Content Absorption Framework）Implementation Plan

> **For Hermes:** 分析/文件任務（無 jarvis code 改動，唔需要 cursor-agent）。Plan 交付前已過 adversarial review。
> 承接：2026-09-02 Douyin 收藏吸收 PoC（一次性）——SK：「it can for many diff website」→ 抽象成通用 framework（Phase 2 follow-up，HANDOFF 已記）。

**Goal:** 將 2026-09-02 抖音收藏吸收 pipeline（scan → classify → summarize → improve plan → adversarial review → SK 批准 → 落地）抽象成**跨平台可覆用 framework**——任何平台（YouTube / Bilibili / X / Reddit / 抖音…）嘅收藏只需一個 adapter，就行同一條吸收 pipeline。

**Architecture:** 核心 = 一個 skill（`content-absorption`）定義 SOP + 統一 schema + 輸出格式，由 agent 執行（**第一版唔寫 runner code——避免 over-engineer**）；每平台一個 adapter reference 檔（點攞收藏清單、點攞 caption/transcript、cookies/auth、坑）；吸收落點不變（improve-plan gap 表 → adversarial review → SK 逐項批准先改）。

**Tech Stack:** 現有 Hermes tools（browser_exec / yt-dlp / faster-whisper / web_extract / youtube-transcript-api）+ skills。零新依賴。

---

## Context（2026-09-02 實測證據）

- Douyin PoC 完成：199 favorites → 101 AI/coding（51%），已分類存檔
- 分類 schema（實測）：`douyin_favorites_classified.json` = `{all: 199, ai: 101, other: 98}`，每條含 caption/desc
- Scan reference 已有：`douyin-tiktok-content/references/douyin-favorites-browser.md`（browser+CDP cookies、CAPTCHA 處理、scroll container、SK 副螢幕規則）——**已驗證可用**，只係困喺 douyin skill 度
- Improve plan 產出已落地 A1-A4（plan skill 拆解 3 步法、cursor audit、memory consolidate、cursor dispatch 4 段 template）——**吸收機制（gap 表 → review → SK 批准）已被 SK 確認有效**
- 反噪音 filter 已有（營銷 caption → 記錄唔吸收）；bias 修正已有（「已實行」要主動 check 有咩 Hermes 未用嘅）
- 平台能力現況：YouTube transcript（skill 有，yt-dlp cookies 已有）；Bilibili 下載（yt-dlp `-f "bv*+ba/b"` 已實測）；抖音完整 adapter（已有）

## 設計原則

1. **唔寫 runner script**——pipeline 係 agent 用現有 tools 執行，skill 記 SOP 就夠（避免新 code 維護負擔）；除非 SK 之後要自動化（cron 定期 scan）先考慮 script
2. **一個 skill、每平台一個 reference**——`content-absorption`（SOP+schema）+ `references/adapters/<platform>.md`
3. **統一輸出格式**——任何平台 scan 完都出同一 shape：分類 JSON + notes + improve plan gap 表
4. **吸收閘唔變**——SK 逐項批准先改 skill/workflow/memory（今日已確認有效，唔郁）
5. **平台優先序跟 SK 實際使用**——YouTube（BGM+睇片多）> Bilibili > X/Reddit（後補，X API 收費可能 browser-only）

## Task 分解

### Task 1: 定義統一收藏 Schema（理想 shape + 今日落差實測）

**Objective:** 定跨平台統一收藏格式——**明確係 target shape**（adapter 要盡量攞齊），並記錄今日 douyin 數據嘅實際落差（實測：只有 caption string，冇 id/url）。

**Files:**
- Create: skill `content-absorption` 內 `SCHEMA.md`（reference）
- 參考：`douyin_favorites.json`（實測 shape：`{scrollTop, scrollHeight, count, items[]}`，items = **純 string captions，391 條冇 url/id**）

**Step 1:** 喺 SCHEMA.md 定義統一 item shape（target）+ 標明「每個欄位 adapter 要主動攞，攞唔到就留空並記錄」：
```json
{
  "platform": "douyin|youtube|bilibili|x|reddit",
  "id": "原生 ID（adapter 盡量攞；今日 douyin browser path 未攞——記錄為 known gap）",
  "url": "https://...（adapter 盡量攞；有 url 先可以之後深睇單條）",
  "title": "標題（如有）",
  "desc": "caption/description 原文（douyin 已攞）",
  "saved_at": "收藏時間（如有）",
  "category": "ai|other|noise"   // classify 後寫入
}
```
分類 JSON = `{all: [...], ai: [...], other: [...], noise: [...]}`。

**Step 2:** SCHEMA.md 加「欄位覆蓋矩陣」——今日 douyin 實際覆蓋（desc ✅ / url ❌ / id ❌）vs target，令每次 scan 完可以 check「今次有冇比上次齊」。

**Step 3:** 驗收：SCHEMA.md 有 shape 定義 + 覆蓋矩陣 + douyin 真實 item 做 example；唔 claim「今日已做到 target」。

### Task 2: 抽 `content-absorption` skill（framework 核心）

**Objective:** 新 skill 定義完整吸收 SOP（今日 douyin 流程通用化），成為「任何平台收藏 → 吸收」嘅操作手冊。

**Files:**
- Create: skill `content-absorption`（category: media 或 productivity）——SKILL.md

**SKILL.md 內容大綱：**
1. **Trigger**：SK 話「scan 我 <平台> 收藏/吸收內容」／定期內容吸收
2. **Pipeline（7 步）**：
   - P1 揀 adapter（`references/adapters/<platform>.md`；未有 → 先 research 平台能力再寫 adapter，照 AGENTS.md research-first + review 規則）
   - P2 Scan：攞收藏清單（每平台方法唔同）→ 寫 `*_favorites.json`
   - P3 Classify：keyword filter（平台無關 keyword 集 + 平台相關補充）→ `*_classified.json`（統一 schema）
   - P4 Summarize：讀一批 → 濃縮 notes（**上下文隔離規則**，唔好 print 晒 captions 入 prompt——今日 context compact ×2 教訓）
   - P5 Improve plan：社群 practice vs 我哋現狀 gap 對照表 → 分級提議（即刻做/評估先/記錄）
   - P6 Review：plan 交付前 `adversarial-decision-review` 三階段；review 用真證據驗證聲稱（grep/ls/跑 command）
   - P7 SK 逐項批准先落地（改 skill/workflow/memory）
3. **反噪音 filter**（營銷 caption 名單 + 規則）
4. **bias 修正**（防自我確認：主動 check「收藏有咩 Hermes 未用嘅」）
5. **Gotchas**（browser-exec stdout 脆弱 / cookies 3 日過期 / CAPTCHA = SK 手動一次 / 唔好直接 import 入 memory）
6. 引用：adapters 目錄、今日 improve-plan 案例

**Step 3:** 驗收：SKILL.md 有完整 7 步 SOP + schema pointer；一個未見過平台嘅 agent 跟住可以做 scan→plan。

### Task 3: 遷移 douyin adapter 入新 skill

**Objective:** 今日 douyin reference 由 `douyin-tiktok-content` 抽入 `content-absorption/references/adapters/douyin.md`（唔刪舊——原 skill 繼續 serve「SK 貼單條 link 要讀」case；新 reference 專注「scan 成個收藏」）。

**Files:**
- Create: `content-absorption/references/adapters/douyin.md`（由 douyin-favorites-browser.md 內容整理，加 schema mapping）
- 保留：`douyin-tiktok-content` skill 原封不動（兩個 skill 互相 link）

**Step 4:** 驗收：新 adapter 有完整 scan 步驟（URL、cookies、CAPTCHA、scroll、extract、SK 副螢幕規則）；內容同實測 reference 一致（diff 抽查）。

### Task 5: YouTube adapter（第二平台 PoC——證明 framework 跨平台）

**Objective:** 寫 YouTube 收藏（liked / playlists / subscriptions）adapter + 實測一次，驗證 framework 唔係 douyin-only。**前置：YouTube cookies 可行性 check（實測 cookies.txt 而家 0 個 youtube entries）。**

**Files:**
- Create: `content-absorption/references/adapters/youtube.md`
- （實測產物入 workspace，唔 commit）

**Step 5:** **可行性 check（先做，Ask first）**：查 `cookies.txt` 有冇 youtube.com domain entries——實測 2026-09-02 係 **0**（cookie 檔只 cover douyin）。冇就要揀：
- (a) SK 用「Get cookies.txt LOCALLY」export YouTube cookies 追加落同一檔（~1 分鐘，SK 手動）
- (b) 行 browser path（youtube.com/playlist?list=LL）——又要登入/CAPTCHA dance
- 揀完先繼續；SK 唔想 export → YouTube PoC 降級為「adapter 寫好但標 untested」，framework 由 douyin 證明

**Step 6:** Research YouTube liked/playlist 清單攞法（yt-dlp `--cookies` + `https://www.youtube.com/playlist?list=LL`；`youtube-transcript-api` 單條 transcript）→ 寫 adapter。

**Step 7:** 實測（如 Step 5 揀咗可做）：scan SK 嘅 YouTube liked/playlist 一批 → 分類 → 出統一 schema JSON（≥10 條真數據）——PoC 只驗 scan+classify，唔需要完整 improve plan。

**Step 8:** 驗收：YouTube adapter 出到 `youtube_favorites.json`（≥10 條真數據，唔係 dummy）；classify 出到統一 schema；無新依賴裝錯。

### Task 6: Bilibili adapter（可選，時間夠先做）

**Objective:** 寫 Bilibili 收藏 adapter（yt-dlp 下載坑已有）。

**Files:**
- Create: `content-absorption/references/adapters/bilibili.md`

**Step 8:** 驗收：adapter 有收藏清單 + 標題/desc 攞法 + yt-dlp format 坑（`-f "bv*+ba/b"`）；未實測（等 SK 有 Bilibili 收藏先）。

### Task 7: 文檔 + 收尾

**Objective:** framework 完成狀態入 HANDOFF/REMAINING_WORK，今日 PoC notes 歸檔。

**Files:**
- Modify: `.hermes/plans/HANDOFF.md`（新增 framework 完成 section）
- Modify: `.hermes/plans/REMAINING_WORK.md`（如有）

**Step 9:** 驗收：HANDOFF 記低 framework 存在 + 點用；skill list 見到 `content-absorption`。

## 驗收標準（SK 規則——全部實際運行驗證）

- [ ] `content-absorption` skill 存在，含 7 步 SOP + SCHEMA.md + adapters/（douyin + youtube 至少）
- [ ] YouTube PoC 實測：scan → classify 出到統一 schema JSON（≥10 條真數據，唔係 dummy）
- [ ] douyin adapter 由實測 reference 遷移，內容一致
- [ ] 冇 SK 未批准嘅 skill/workflow 改動（Task 1-7 產出係新 skill + reference，冇郁現有 skill/memory）
- [ ] 零新 runtime 依賴（用現有 yt-dlp/transcript-api/browser）

## Risks / Tradeoffs

- **R1 過度抽象**：framework 變「為抽象而抽象」——對沖：第一版只做 douyin(已有)+youtube(實測) 兩個 adapter，第二個平台出到先算 framework 成立；唔寫 runner code
- **R2 YouTube cookies 而家冇（實測 0 entries）**：yt-dlp liked list 一定要 cookies——SK 要 export 或行 browser path；兩樣都唔想做 → YouTube PoC 降級 untested（framework 仍由 douyin 證明，YAGNI）
- **R3 今日 douyin data 冇 url/id（實測）**：schema 係 target 唔係現況——adapter 寫法要主動攞 url，攞唔到記錄 known gap（唔 silent drop）；咁先令「深睇單條」成為可能
- **R4 平台 API 改動**：adapter 係 living doc，坑已入 skill；改動時 research-first
- **R5 Scope creep（X/Reddit/自動化 cron）**：全部後補，YAGNI——今次唔做
- **R6 Skill 重疊**：media/ 已有 douyin-tiktok-content（單條 link 閱讀）+ youtube-content（transcript 轉格式）——`content-absorption` 專注「成個收藏 scan → 吸收 pipeline」，SKILL.md 開頭寫明同其他 skill 嘅界線，避免 agent 揀錯

## Open Questions（執行前 SK 拍板）

1. **YouTube 數據源揀邊個**：liked videos（list=LL，反映 SK 口味）vs 特定 playlist vs subscriptions？——預設：liked（同 douyin 收藏對應）
2. **YouTube cookies 點處理**：SK 用 extension export YouTube cookies 追加（推薦，~1 分鐘）vs browser path vs 今次跳過 YouTube PoC？——**實測而家 cookies.txt 冇 youtube entries**
3. **實測深度**：YouTube PoC 淨 scan+classify（快）定行埋 summarize→improve plan（慢但完整示範）？——預設：scan+classify 就夠證明 framework；完整 pipeline 等 SK 下次叫
4. **Skill category**：media（同 douyin/youtube-content 一齊）vs productivity？——預設 media
