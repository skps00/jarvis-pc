# Skill 整合 plan **v6** — 語音 3 合 1（`jarvis-voice-assistant` 為 umbrella）

> 2026-09-19。**R1 4:6 → R2 6:4 → R3 7:3 → R4 7:3 → R5 正方 8 : 反方 2（`go=true`，過閘）**
> v6 ＝ v5 ＋ R5 嘅 5 條修正（FC2–FC5）＋ **真做咗倒帶演練**（R5 O2 指我聲稱彩排過還原但冇做）。
> 報告：`.hermes\plans\reviews\2026-09-19_skill-voice-merge-plan-R{1..5}-opposing.md`
> 範圍：只涉 `%LOCALAPPDATA%\hermes\skills\`（實機至今**零改動**）。

## 0. v6 修正（對應 R5）
| R5 指出 | v6 處置 |
|---|---|
| O1 A6 三重數字矛盾（11／10／12）＋skills 樹係**移動靶**（curator 18:15:48 新寫 2 行命中） | A6 改為「**執行時即場重測**」：預期 11–12 行，逐行處置；並寫明 curator 新命中（`hermes-skill-library-governance/references/skill-merge-plan-acceptance.md:14-15`）屬**可接受漂移** |
| O2 §6 聲稱「已彩排過還原」但冇做 | **已真做倒帶演練**（`%TEMP%\rollback_rehearsal.py`）：刪 14 檔 ＋ 還原 `SKILL.md` ⇒ **21/21 檔案 sha1 ＝ 原狀、無多無少 ⇒ ROLLBACK CLEAN = True** |
| O3 第 8 行淨刪會失去語意連繫 | 改為**指向 umbrella**：`related_skills` 內 `windows-voice-pipeline` → `jarvis-voice-assistant`（保留 3 個條目） |
| O4 執行後再跑舊 review 腳本會踩鬼閘 | §6 明文：舊腳本（`voice_merge_rehearsal.py`／`rehearsal_*.py`／`voice_merge_check.py`）係**一次性**，執行後唔准再跑；A4 要對 `%TEMP%` backup 比，唔好對 live 比 |
| O5 未記 `platforms:[windows]` 行為改變 | §4 補：umbrella 由**全平台**變 **只在 Windows 載入** |

## 1. 目標（一句）
3 個語音 skill → **1 個 umbrella**，消除「同一問題 3 個 skill 撞手」，**內容零損失**。

## 2. 現況（實測）
| skill | 檔案數 | 字數（CRLF 保留） | `SKILL.md` | curator |
|---|---|---|---|---|
| `jarvis-voice-assistant`（keeper） | 21 | 150,405 | 62,362 | **curator-managed** |
| `windows-voice-pipeline` | 10 | 57,440 | 28,566 | curator-managed |
| `hermes-voice-windows` | 4 | 14,042 | 7,206 | curator-managed |
| **合計** | **35** | **221,887** | — | — |

## 3. 整合設計（零損失；**只准 4 個檔案共 8 行**改動）
1. keeper＝`jarvis-voice-assistant`（HOLD 段唔郁）
2. 逐字 copy 2 個 `SKILL.md` → `references/windows-voice-pipeline.md`、`references/hermes-voice-windows.md`
3. 搬入附屬檔 14 個：pipeline `references/` 9 檔（撞名者 → `voice-pipeline-aec-implementation.md`）＋ `voice-setup-notes.md` ＋ 2 個 hvow scripts（彩排實測：**11 逐字一致 ＋ 3 有改動**）
4. **允許改動（8 行／4 檔）**：
 - `references/windows-voice-pipeline.md`：`:147` aec 連結改名（`:143` 唔准改）＋ `:36/:112/:187/:193` 裸路徑 → `jarvis-pc/scripts/…`（`:85` 唔准改）＝ 5 行
 - `references/speaker-verification-ecapa.md:32`、`references/unprompted-speech-triage.md:16` ＝ 2 行
 - `software-development/electron-windows-overlay/SKILL.md:11`：`related_skills` 內 `windows-voice-pipeline` → **`jarvis-voice-assistant`**（保留連繫，唔淨刪）＝ 1 行
5. 新 frontmatter（逐字；CRLF）：見附錄 A
6. 新指標節（逐字；插喺 HOLD 段之後、`## Projects` 之前）：見附錄 B
7. 歸檔：`hermes curator archive windows-voice-pipeline`／`hermes curator archive hermes-voice-windows`

## 4. 紅線／已知行為改變
- **唔碰**：HOLD 段原文、`settings.json`、sidecar、`wake.py`／STT／AEC／聲紋；**唔叫 SK 測 mic**；**唔准 `hermes curator pin`**
- ⚠️ **已知行為改變**：① description 改動影響語音任務 routing ② `electron-windows-overlay` 少一個 related skill 但多一個（改指 umbrella）③ **umbrella 由全平台載入變 `platforms:[windows]` 只在 Windows 載入**
- 除 §3.4 嘅 8 行，零文字改動

## 5. 驗收標準（v6）
| # | 判準 |
|---|---|
| A1 | `skills_list()` **120 → 118**；`software-development 31 → 30`；`autonomous-ai-agents 13 → 12` |
| A2 | 14 個搬入檔 ＝ **11 sha1 逐字一致 ＋ 3 有改動**（各出 `diff` 只顯示指定行） |
| A3 | 總量（CRLF 保留 predicate）＝ **222,982 字**（彩排實測；Δ＝+274／+746／+75） |
| A4 | HOLD 段（由 `## ⛔` 到下一個 `\n## `）`diff` ＝ 空（**對 `%TEMP%` backup 比，唔好對 live 比**；彩排實測 822 字 identical） |
| A5 | `skill_view('jarvis-voice-assistant')` 列出 **31** 個 `references/*.md` |
| A6 | **執行時即場重測**：`grep` 只喺 `skills/` 樹，排除 `.usage.json`／`.curator_backups/`／`.archive/`／ledger，並排除 `^name: (windows-voice-pipeline\|hermes-voice-windows)$` ⇒ 預期 **11–12 行**（curator 新命中屬可接受漂移）；逐行處置：umbrella 4 行（新指標節自引）／umbrella 3 行原有（`:52`／`:128`／`:136`）／umbrella 1 行搬入（`references/jarvis-hud-design.md:11`）／governance 1–2 行（curator 寫）／`windows-desktop-automation:139`／`electron-windows-overlay:11`（已改指 umbrella） |
| A7 | `hermes curator status`：`managed/active 124 → 122`、`archived 0 → 0`；`list-archived` **1 → 3** |

## 6. 還原（3 步；**已真做倒帶演練 = ROLLBACK CLEAN**）
1. umbrella `SKILL.md` 由 `%TEMP%\skill_voice_merge_backup_<ts>\` 還原（`rollback_rehearsal.py` 已驗：21/21 sha1 一致）
2. 刪 14 個搬入檔（已驗：刪完無多無少）
3. `hermes curator restore windows-voice-pipeline`／`hermes curator restore hermes-voice-windows`＋還原 `electron-windows-overlay/SKILL.md` 嗰行
- ⚠️ 舊腳本（`voice_merge_rehearsal.py`／`rehearsal_*.py`／`voice_merge_check.py`）**一次性**，執行後唔准再跑（會 FileNotFoundError 或恆真鬼閘）

## 7. 殘餘風險
curator 會唔會重建返？（三個都 curator-managed）→ 緩解：指標節「已吸收」行＋ledger；驗證：執行後 `status`／`list-archived` 一致、下個語音 session 後再查

## 8. 成本／流程
約 20 分鐘、零 code、零 GUI；SK `go` → 備份 → 做 → 出 §5 實測輸出 ＋ §6 還原指令 → 更新 HANDOFF

---

## 附錄 A：新 frontmatter（逐字）
```markdown
---
name: jarvis-voice-assistant
description: "Debug JARVIS + Hermes voice/HUD on Windows (wake/STT/TTS)."
version: 1.0.0
platforms: [windows]
metadata:
  hermes:
    tags: [jarvis, voice, wake-word, stt, tts, hud, windows, aec, speaker-verification]
    related_skills: [jarvis-companion, hermes-aux-models, desktop-activity-awareness, windows-desktop-automation]
---
```

## 附錄 B：新指標節（逐字）
```markdown
## 語音線整合（2026-09-19：已吸收 2 個 skill）

- 本 skill 已吸收 `windows-voice-pipeline`（Windows 語音管線：wake/STT/TTS/Jarvis 鏈路）同
  `hermes-voice-windows`（Hermes 側語音安裝／設定／驗證）——兩個原名已由 `hermes curator archive` 歸檔。
- 原文**逐字保留**（零損失）：
  - `references/windows-voice-pipeline.md`（其 `references/` 9 檔已搬入本 skill）
  - `references/hermes-voice-windows.md`（＋`references/voice-setup-notes.md`、`scripts/verify_voice_stack.py`、`scripts/voice_test_tts.py`）
- ⚠️ 兩份原文內嘅 `scripts/…` 裸路徑**指 jarvis-pc repo**（`C:\Users\skps9\Documents\Code_Project\jarvis-pc\scripts\`），
  唔係本 skill 嘅 `scripts/` → 已喺文中改寫成 `jarvis-pc/scripts/…` 防影子化（3 個檔案共 7 行）。
- 撞名：`references/aec-implementation.md` 兩份**內容唔同** → pipeline 版改名
  `references/voice-pipeline-aec-implementation.md`（零損失）。
```
