# Phase 2: 通用 App Session Detection Framework（唔止 game）

> 起草：2026-09-03（Hermes JARVIS 線）。承接 `2026-09-02_135000-game-session-detection-phase1.md`（✅）。
> 執行：cursor-agent（SK 規則：任何 code 改動經 cursor-agent）。Plan 過 adversarial review 先可實作。

**Goal（一句話）:** 將 activity_monitor.py 嘅「game-only 偵測」抽象做「通用 app session 偵測」——任何已註冊 app（game／chat／dev／media）都可以被 track 成 running session、輸出落 sk_activity.json、按 policy 觸發 ready alert；**遊戲行為 100% 不變**（向後兼容）。

---

## Context（現狀證據）

- activity_monitor.py（618 行，`%LOCALAPPDATA%\hermes\scripts\`，cron 每分鐘一次性）而家已有：前景 state（playing/using/idle）、**game running-session**（Steam RunningAppID + process map + java client cmdline 分辨、latch、flap guard）、chat_context（Discord/WhatsApp 前景 title）、voice_call、fullscreen。
- 消費者（唔可以整壞）：
  1. Hermes 活動 Gate：讀 `state`（playing/using/idle）——GUI 操作前 gating
  2. jarvis sidecar `shell_app._start_game_alert_watch`：讀 `game` + 變化 → 「X is ready, sir.」
  3. sk_activity.json 其他欄位（fullscreen/chat_context/voice_call）→ HUD／其他
- Phase 1 已留低嘅 hints：R4「若 SK 想『背景 game 都報 ready』，Phase 2 加」；D2「generic 任何 game 都 alert（唔限 MC）」；SK 原話「唔止 game」。
- 現有 hardcode 位（要 generalize 嘅對象）：
  - `GAME_PROCESSES` map + `GAME_TITLE_KEYWORDS`（game-only）
  - `CHAT_APP_MARKERS`（chat-only，前景 title based）
  - `detect_running_games()` 只出 game
  - `detect_game(fg)` 只認 game 前景
- ⚠️ 唔好 over-engineer：消費者實際只需要 (a) 前景 state（已有）(b) running session 集合 (c) session 開始信號。registry 要 declarative + 細。

## Scope 決定（2026-09-03 adversarial review 修訂——反方 8:2 縮 scope）

> 原 scope 被 review 砍咗三樣：watch 泛化（sidecar restart 必然 false-ready）、dev/media registry entries（零消費者 = 寫入死 data）、game_start_event.json apps 鏡像（事實錯誤——sidecar 讀 sk_activity.json，唔讀嗰個檔）。核心 registry refactor 照做。

**做：**
1. **Declarative game registry**：`APP_DEFS` 收編 GAME_PROCESSES + GAME_TITLE_KEYWORDS（**保留異質語義，唔 normalize**——title-kw 名 `cs2` 同 canonical 名 `counter-strike 2` 唔可以夾埋，否則 latch string 比較會靜默變）。**今期唔收編 CHAT_APP_MARKERS**（detect_chat_context 有 is_self/title-parse 語義 + detect_voice_call 第三份硬 code 喺 scope 外——郁佢風險 > 收益）。設計上支援 category/kind，但今期只有 game category 使用。
2. **通用偵測結構**：`detect_running_apps() → {"game": [names]}`（結構留定擴充）+ `detect_running_games()` 做 wrapper（caller 零改動）。Steam/java client/title-confirm 全部保留原邏輯。
3. **sk_activity.json 加 `apps`**：`[{"name", "category"}]`（running games 快照，今期 = game only）＋保留 `game`／`game_started`／`state` 全部欄位（**語義不變**）。**唔加** game_start_event.json 鏡像（無消費者）。

**唔做（Non-goals——review 確認）：**
- ❌ **sidecar watch 泛化**（原 Task 5 砍走）——而家 watch 係 started-flag + freshness gate；改 last-seen 式喺 sidecar restart 會必然誤報 ready（restart 後 last-seen 空 + activity file 永遠 fresh）。等有真 consumer（例如 SK 要 Cursor ready alert）先以「per-app started/ts 信號 + restart-prime」重新設計。
- ❌ dev/media registry entries——apps 欄位今日冇 consumer；加 cursor 落 registry 而家 = 死 data。等 HUD 顯示或 ready-alert 需求出現先加。
- ❌ 唔郁 CHAT_APP_MARKERS／detect_voice_call／classify／state 邏輯
- ❌ per-app usage 統計／dashboard、WMI event-driven（Phase 3）、config UI、新 dependency（全部照舊 YAGNI）

**Step 0（新增，郁 activity_monitor 前必做）**：跑 Phase 1 SK 實測場景 A-E 做 baseline——activity_monitor.py 零 automated coverage（唔喺 repo、eval_gate 唔 cover、HUD 每 5s exec 同一檔），改之前必須有「改前行為」實測記錄。A-E 需要 SK 配合（開/關 game、切前景）；SK 冇時間就最少 smoke matrix（8-scenario，Phase 1 用過）先做。

## 設計

### 1. APP_DEFS（取代三張表）
```python
# name 全部 lowercase（沿用現狀 normalize）
APP_DEFS = [
  # process/exe 直接命中 → name/category/alert
  {"proc": "cs2.exe",         "name": "counter-strike 2", "category": "game",  "alert": True},
  {"proc": "minecraft.exe",   "name": "minecraft",        "category": "game",  "alert": True},
  {"proc": "discord.exe",     "name": "discord",          "category": "chat",  "alert": False},
  {"proc": "Cursor.exe",      "name": "cursor",           "category": "dev",   "alert": False},
  {"proc": "Code.exe",        "name": "vscode",           "category": "dev",   "alert": False},
  # java/特殊 → detector function（game：java_client_game 分辨 client/server）
  {"kind": "java_client",     "name": "minecraft",        "category": "game",  "alert": True},
  # steam → 動態（RunningAppID + appmanifest 名）category=game alert=True
  {"kind": "steam",           "name": None,               "category": "game",  "alert": True},
  # title keyword fallback（前景 title 命中）→ 沿用 game title keywords
  {"kind": "title",           "name": "minecraft",        "category": "game",  "alert": True, "kw": "minecraft"},
]
# 索引：_PROC_INDEX = {proc.lower(): def}、_TITLE_KW = [(kw, def)]、_KIND_FNS = {...}
```
- `category == "game"` 嘅 def 先會被當前景 `playing`（classify 不變：state 只睇 category=game？見 §4）
- Steam：讀 RunningAppID → appmanifest name → 動態 def `{"name": <名>, "category": "game", "alert": True}`（filter 沿用 `_STEAM_NON_GAME`）

### 2. 偵測重構（向後兼容）
```python
def detect_running_apps() -> dict[str, list[str]]:
    """{category: sorted names} 而家 running 嘅已註冊 apps（今期只有 game category）。"""
    running = defaultdict(list)
    # (a) steam → game
    # (b) process map 全部 APP_DEFS（game + chat + dev + media）
    # (c) java client → game
    # 輸出同一 app 唔重複
    return dict(running)

def detect_running_games() -> list[str]:
    return sorted(detect_running_apps().get("game", []))   # ← 現有 caller 照用
```
- **flap guard**：而家以 `not running`（game list 空）做 debounce——改為「全 apps 空」？⚠️ 見 Risk R2（debounce 語義要小心：如果 discord 長開，`apps` 永遠非空 → flap guard 冇意義）。**決定：flap guard 只對 game category 生效（保持現狀）**；其他 category 無 latch 需要（佢哋唔觸發 alert，淨係資訊性）。

### 3. 輸出 schema（加欄位，唔郁舊）
- `sk_activity.json`：
```json
{
  "state": "playing|using|idle",          // 不變（前景）
  "game": "minecraft" | null,             // 不變（session game；latch 邏輯照舊）
  "game_started": true|false,             // 不變
  "apps": [{"name": "discord", "category": "chat"}, ...],   // NEW：running apps（全 category，每 tick 快照）
  "foreground": {...}, "chat_context": {...}, ...           // 不變
}
```
- `game_start_event.json`：唔郁（只係 activity_monitor 自己 latch 用；sidecar 讀 sk_activity.json）

### 4. state 分類（§ Scope：唔郁）——澄清
- `classify()` 照舊：前景 process/title 命中 **category=game** 嘅 def → playing；其他全部 app 前景 = using（同今日 Discord/VS Code 前景 = using 一致）。即係話 registry 引入 category 之後，**只有 game category 影響 state**——chat/dev/media 前景都係 using。呢個係刻意決定（零行為改變）；未來若 SK 想要「dev 前景 = 另一 state」另議。

### 5. sidecar alert watch（shell_app.py）——❌ 砍走（review）
- **今期完全唔郁 shell_app.py**。現有 game watch（started-flag + 120s freshness + last_alerted_game reset）原封不動——佢冇 false-ready bug，郁佢先有。
- 日後要做（等 consumer）：per-app started/ts 信號（而家只有 game 有 game_started）+ restart-prime 邏輯（首次觀察唔 alert，學 activity_monitor first-run prime），先至可以安全泛化。

### 6. Files
| File | Change |
|---|---|
| `%LOCALAPPDATA%\hermes\scripts\activity_monitor.py` | APP_DEFS registry（取代 GAME_PROCESSES + GAME_TITLE_KEYWORDS 兩張 game 表；CHAT_APP_MARKERS 唔郁）；detect_running_apps()；run() 加 apps 輸出；flap guard 邏輯維持現狀 |
| `jarvis-pc\src\jarvis\shell_app.py` | **唔郁**（review：watch 泛化有 false-ready 風險） |
| `%LOCALAPPDATA%\hermes\scripts\activity_monitor.py.bak` | 改前 backup（恆例） |
| skill `desktop-activity-awareness` + `windows-desktop-automation`（內有 158 行舊副本）+ 主契約 `AGENTS.md:101`（引用 GAME_PROCESSES 位置） | 語義更新（apps 欄位、registry 位置、GAME_PROCESSES → APP_DEFS 引用）——**6 處 grep 命中全部要對** |

## Tasks（cursor-agent 執行；每個 task 有驗證）

- **Task 1**：activity_monitor.py 建 `APP_DEFS`（game category only，逐項對應而家 GAME_PROCESSES 21 項 + GAME_TITLE_KEYWORDS 17 項，**name 保持原值——title-kw `cs2` 同 proc-map `counter-strike 2` 唔合併**；java.exe/javaw.exe None-confirm 語義保留）+ `_PROC_INDEX`/`_TITLE_KW` 索引。刪 GAME_PROCESSES/GAME_TITLE_KEYWORDS 兩張舊表，`_GAME_PROCESSES_LOWER` 改指新 index。**CHAT_APP_MARKERS 唔郁**。
- **Task 2**：`detect_running_apps() → {"game": [...]}` + `detect_running_games()` 改 wrapper。驗證：smoke（python -c 直接 call：cs2 開住 → detect_running_apps()["game"] 含 counter-strike 2；detect_running_games() 輸出同改前一致）。
- **Task 3**：run() 加 `apps` 輸出（`[{"name","category"}]`，game only）；**唔加** game_start_event.json 鏡像；flap guard 條件維持現狀。
- **Task 4**：smoke script（temp）——8 場景 matrix 對照 Phase 1 嘅 A-E（零 regression）+ 新增：**apps 欄位出現且只有 game category**；開 Discord/Cursor **唔影響** game/game_started/apps（唔喺 registry，natural 唔出現）。
- **Task 5**：~~shell_app.py alert watch~~ **刪（review）**——eval_gate --lock/--all 照跑（證明 shell_app 冇被郁到）。
- **Task 6**：所有引用 GAME_PROCESSES/GAME_TITLE_KEYWORDS 嘅文件同步（grep 6 處：desktop-activity-awareness skill、windows-desktop-automation skill scripts 舊副本、主契約 AGENTS.md:101）+ REMAINING_WORK 標記。

## 實測驗收（Hermes 執行）
1. `python -m py_compile activity_monitor.py` + `python activity_monitor.py`（一次性 print 睇 apps 欄位）
2. 場景 A-E（Phase 1 全數重跑——**零 regression**）
3. 場景 F：開 Discord（唔開 game）→ state=using、冇 game alert（apps 唔含 discord——今期唔 track chat）
4. 場景 G：Minecraft 開 → 照舊一次「Minecraft is ready」；CS2 + Minecraft 同時 → Phase 1 行為一致
6. `env -u PYTHONPATH python -m jarvis.eval_gate --all` 全綠

## Risks / Open Questions（2026-09-03 review 更新）
- **R1（steam 動態名）**：steam game 名動態 → 冇辦法預先喺 APP_DEFS 標 alert——設計上 steam kind = game + alert True（現狀）。OK。
- **R2（flap guard 語義）**：如果 apps 含常駐 discord，guard「全空先 debounce」會失效——今期 apps = game only，guard 條件維持現狀（`not running` = game list 空）。registry 擴充到 chat/dev 前要再諗。
- **R3（registry drift）**：GAME_PROCESSES 今日係手維護；APP_DEFS 一樣。加 app = 加一行。接受（YAGNI user-config）。
- **R4（title keyword 遷移）**：GAME_TITLE_KEYWORDS 遷移做 entries 時**唔可以 normalize 名**（title-kw 回傳 `cs2`，process map 係 `counter-strike 2`——兩者今日已並存於 detect_game/detect_running_games，語義保留）；次序/去重要測（smoke 場景）。
- **R5（新，review）**：registry index bug／dup def → runtime exception → activity_watch cron 靜默 fail（check=False）→ sk_activity.json stale → GUI gate block／voice_call 卡死。防：改完即刻 `python activity_monitor.py` 手動行一次（print 模式）＋睇 exit code；唔好淨靠 cron。
- **Open Q1（flip condition）**：SK 係咪近期要非-game app 可見度（HUD 顯示用緊咩／Cursor ready alert）？要 → 開 Task 5 watch 泛化（用 per-app signal + prime 設計）+ dev entries；唔要 → 今期 registry 收編已經夠。

## Acceptance Criteria
- [ ] sk_activity.json 有 `apps` 欄位且舊欄位全部不變
- [ ] Phase 1 場景 A-E 零 regression（含 flap guard、latch、server 排除）
- [ ] 開 Discord/Cursor 唔觸發 ready alert（今期唔 track，natural 唔出現喺 apps）
- [ ] Minecraft/CS2 ready alert 行為同今日完全一致
- [ ] shell_app.py 零改動（git diff 確認）
- [ ] eval_gate --lock / --all 全綠
- [ ] 6 處 GAME_PROCESSES 文件引用已同步

## Status: ✅ Task 1-4 完成（2026-09-03）＋ Task 6 文件同步完成

- activity_monitor.py：APP_DEFS registry（21 proc + 17 title-kw，語義保留唔合併）→ `_PROC_INDEX`/`_TITLE_KW`；`detect_running_apps()` + `detect_running_games()` wrapper；run() 加 `apps` 輸出（game only）
- 驗證：py_compile OK；**parity 16/16 PASS**（old vs new：detect_running_games live + 7 synthetic detect_game + 7 classify 全一致）；one-shot 同 baseline 一致（state/game/game_started/voice_call 不變，apps 新欄位正確）；`--update` 路徑 sk_activity.json 加 apps 正常
- backup：`activity_monitor.py.bak-20260903_163254`；shell_app.py 零改動（review 決定）；eval_gate 唔需要跑（jarvis repo 無 code 改動）
- Task 6：主契約 AGENTS.md×2、desktop-activity-awareness SKILL.md、windows-desktop-automation references/activity-monitor.md、skill scripts 舊副本 deprecation header 已同步；歷史 snapshot（diagnostics-2026-09-02 / merged-* / game-session-detection-2026-09.md）刻意保留原狀
- 剩餘：SK 實測場景 A-H（等 SK 玩緊 game 時自然觀察）；Open Q1 flip condition 未觸發（SK 暫冇要求非-game alert/HUD 顯示）
