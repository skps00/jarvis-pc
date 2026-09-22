# HANDOFF — jarvis-pc（狀態區塊 + 逐日 index）

<!-- STATE:BEGIN -->
## 狀態（每次 session 尾／cron **改寫**；新 section 一律加喺本區塊**之下**）

- **目標**：JARVIS ONE（語音／HUD／alerts）穩定收尾 ＋ MC packai（Forge 1.19.2 primary）設定／答案版面／卡片修復落地。計畫書：`.hermes/plans/REMAINING_WORK.md`
- **現狀（2026-09-22 18:4x 改寫；全部 Hermes 親核）**
 - **Git**：HEAD ＝ `feature/hermes-alerts-mcp` `1a55b19`，**ahead origin 5**（全部 docs commit，未 push）；origin/main 有 `96be515`（PR #12）未入本分支；agent 未 commit 檔 = **0**（`src/`／`tests/`／`hud/` 全部乾淨）
 - **JARVIS ONE**：HUD **0.4.13** 已 build＋部署＋捷徑更新；`hud/main.js`＋`hud/package.json` **已 commit**（`61354de`）；**語音喚醒已關**（`voice_frontend=hermes`，側車重啟生效，8765 `/health` `wake_on=false`，wake_debug 75 秒零增長實證）；**自動調門檻已凍結**（`wake_debug.log` 歸檔 → `avg_peak=None` → thr 定死 0.55，親核 `0.55->0.55`）
 - **兩條監測線停手（等 SK 新 mic）**：① 誤觸／無效指令數字老實化＋step 趨勢（plan `2026-09-22-self-monitor-honest-fp-and-step-trend.md`；R1 3:7、R2 2:8）② 自檢提示靜音（plan `2026-09-22-self-monitor-alert-mute.md`；R1 2:8、R2／R3 仍有 blocker）。**兩份 plan 內含全部 blocker 同反轉條件，重啟唔使重做 research。**
 - **已批准但未做**：**測試隔離 ii**（全域）—— `tests/test_brain.py:302` 條測試冇停 `hermes_enabled` → 會真 call Hermes 開 session（已實錘：198 個同字串 `怎樣開 Chrome？` session；親手跑一次即新增 `jarvis-1fd59b1d`）。SK 2026-09-22 揀「2 ii」。
 - **packai（MC 主線，詳 MC repo HANDOFF）**：Slice 1 已 commit＋push；**Slice 1b code 已改好、自驗綠（compile RC=0／harness 58/58／python 125 檔 1 baseline 紅／NC3 紅→還原→綠），真機 A/B 未跑 → 未 commit**（未 commit 5 檔：`AskReplyScrub.java`／`InternalJargonCheck.java`／`AskReplyScrubCheck.java`＋`tmp-check.gradle`＋`code_change_log.md`）；真 instance jar `af448fa4d939`（09-21 21:41）；沙盒 `0a79ee90c0bd`；MC repo HEAD `013e4ac` 已全部 push
 - **Hermes**：cron `jarvis-session-handoff` 09-22 05:45／08:14 agent 段 timeout（**非 429、零資料損失**）；`jarvis-alert-shadow-report` 08:11 Discord 送訊 timeout
 - **本檔**：402 行（**已過 400 門檻 → 下次開工先歸檔最舊 section 落 `plans/archive/HANDOFF-2026-09.md`**）
- **唔准郁（硬限制）**
 - 打機／用緊電腦：**零彈窗、零搶焦點**（先讀 `state/sk_activity.json`）；GUI 窗一律第二副螢幕；Chrome 主動開＝`bg_launch.py --minimized`
 - `AGENTS.md` 受保護（要 SK 明確 go）；唔准 `curl|sh`；**HANDOFF 視為可公開 → 唔准入 secrets**
 - packai code **一律經 cursor-agent**；**唔准 `git add -A`**；部署只准用 `mc_mod_deploy_jar.py`（真 instance 唔准自動部署）；cursor 派工唔准用 `--no-desktop`
 - **語音／mic 線 HOLD（等 SK 新 mic）**：唔郁 `wake.py`／STT／AEC／聲紋／wake threshold／mic device；唔叫 SK 測 wake
- **未解（等 SK 決）**：① **測試隔離 ii 實作**（已批准，未開工）② **Slice 1b 真機 A/B** ③ Slice 1c plan（源頭措辭／機翻／關聯閘）④ Slice 2 世界生成正式 plan ⑤ 取得途徑缺口修補（advancement `inventory_changed`＋「JSON 冇 ≠ 遊戲冇」措辭）⑥ **dev → main 合併**（PR 定直接 merge）⑦ `jarvis-pc/AGENTS.md` 版本字串仍寫 0.4.10 ⑧ **SK 手動**：Surfshark 加 3 個 exclusion folder
- **下一步（優先序）**：① **測試隔離 ii**（可即做；要 plan → review ≥8:2 → 實作；驗收＝跑測試前後 session 數／檔案 mtime 不變）② **packai Slice 1b 沙盒真機 A/B**（diamond／amethyst／crying_obsidian／brazier＋Tetra，掃 body 0 hit）→ 全過才 commit；需 SK 唔用機（idle）＋DS 空閒 ③ Slice 1c plan → R1 review ④ Slice 2 正式 plan ⑤ 取得途徑缺口（等 SK 拍板）⑥ merge 決定 ⑦ HANDOFF 歸檔
- **歸檔索引**：≤2026-09-11 全部搬 `plans/archive/HANDOFF-2026-09.md`；更舊見 `plans/archive/HANDOFF_2026-08-*.md`
- **參考段（喺檔尾）**：陷阱（重溫）／語音·硬體設定（驗證過）
<!-- STATE:END -->

## 2026-09-22 18:5x（Discord；Hermes 設定＋非專案事項）
- **Hermes config 改動（已生效於新 session）**：`compression.micro_compact=true`、`micro_compact_every_n_turns=10`（每 10 輪自動摺一輪舊歷史入滾動摘要）＋`compression.threshold=0.35` 批次壓縮保留做保險。備份 `%LOCALAPPDATA%\hermes\config.yaml.bak-20260922-182831-microcompact`；還原＝`hermes config set compression.micro_compact false`。**未重啟 gateway**（SK 選等下個 session）。⚠️ 坑：`hermes config set` 會重寫 config.yaml 並刪走檔尾純註解（今次 38 行，已還原）。
- **依據**：`hermes insights --days 3` ≈ US$5.14（~$1.7/日）；agent.log 顯示本 session 40 分鐘內 4 次 35 萬 token 批次壓縮（context 長期貼住 0.35×1M 上限）→ 開 micro-compaction 比純批次好；唔建議 cadence=1（前綴 35 萬 token，cache 失效成本會放大）。
- **非專案工作（Microsoft 面試準備）**：DCT（HK, Job ID 200049923）4 場 Teams 面試 9/28–9/30；產出在 `C:\Users\skps9\Documents\MS_DCT_Prep\`（`MS-DCT-interview-prep-20260922.pdf` 21 頁、`MS-DCT-cheat-sheet-20260922.pdf` 2 頁＋`.md`／`.html` 源檔）。官方 15 頁 hiring tips 全讀；官方 Code of Conduct 明文「面試期間不得用外部協助」。**待 SK 提供 6 個 STAR 數字**，之後出英文可照背版。
- **今日 jarvis-pc 狀態**：語音喚醒已關、自動調門檻已凍結、HUD 0.4.13 已 commit；兩條監測線停手等新 mic（SK 選 C）。**程式碼零改動**（`src/`／`tests/`／`hud/` 未改）。


- **✅ 自動調門檻已凍結（SK 2026-09-22 18:0x 答「k」）**：唔改 code，做法＝把 `wake_debug.log` **改名歸檔**（`wake_debug.log.bak-20260922_171739-tunerfreeze`，6,586,680 bytes 原封保留）→ 檔唔存在 ⇒ `_parse_wake_debug` 得 `avg_peak=None` ⇒ decay 分支（要求 `avg_peak is not None`）**永遠唔成立** ⇒ 門檻唔再自己漂。
  **親核**：跑 `run_once()` → summary `thr=0.55->0.55`、`settings.json` mtime/size 前後一樣（1790068327／2740）→ 真係冇寫入。
  **還原**：`mv wake_debug.log.bak-20260922_171739-tunerfreeze wake_debug.log`（聽候重開時本來就會生新檔，唔影響）。
  **注意（pre-existing，非本次引入）**：同一 run `notable=True` 係因為 serve.log 尾有 `err=2`，唔係門檻 — 即係「每日一句 self-monitor 英文提示」原本就會發生。

## 2026-09-22 18:3x（Discord；SK 決定「C」＝監測靜音都停手，等新 mic）
- **SK 決定**：自我監測提示靜音**唔做**（選 C）→ 等新 mic 到手一次過處理。今日兩條 monitoring 線（誤觸老實化＋提示靜音）**全部停手**。
- **停手原因（照 SK 規矩 3–4 輪上限）**：R1 2:8／R2 有 blocker／R3 仍有 blocker 未達 8:2。R3 反方**推翻我一個數字**：我報「誤吞真事故 0.00%」係抽樣假綠（抽 3,000／全檔 373,113 → 實際誤吞 **36** 條）。
- **留低嘅可用結論（新 mic 重啟時直接用）**：① 良性 traceback 判定要用「traceback 所屬 log record 含 marker」而唔係固定行距（核實方實測：現檔 30/30 過濾、備份唔誤吞）；② `resp_lat` 條件（`>5s`）係**恆真**假陽性（實測 21 個樣本 min 6.0s／p90 26s）→ 新 mic 後要用真數據重新定基準，唔可以照抄；③ 驗「真靜音」唔可以用 `queue.jsonl`（poller 1 秒 ack）或單靠 ledger（冇 run 標記、多生產者）→ 要正向對照。
- **證據存底**（log 每分鐘長，舊樣本會跌出窗口）：`%LOCALAPPDATA%\Temp\serve_tail2000_snapshot_20260922.txt`、`benign_tb_blocks_snapshot_20260922.txt`。相關 plan：`.hermes\plans\2026-09-22-self-monitor-alert-mute.md`、`2026-09-22-self-monitor-honest-fp-and-step-trend.md`。
- **現時行為（未改任何 code）**：提示仍會响（觸發＝serve.log 尾 2000 行出現 asyncio traceback 同／或 resp_lat>5s）；因為 wake 已關，`resp_lat` 會長期 n/a，實際上只餘 traceback 一種觸發，而且會隨 log 長大而自動跌出窗口（實測約 6 分鐘）。

## 2026-09-22 18:1x（Discord；SK 決定「3＋停語音喚醒」）
- **SK 決定**：① 自我監測老實化／趨勢規則 = **選 3 停手**（等新 mic）；② **停止 JARVIS 語音喚醒**。
- **語音喚醒已關（Hermes 親做親核）**：`settings.json` `voice_frontend: jarvis → hermes`（經 8765 `POST /settings` **單一 writer**；備份 `%APPDATA%\Jarvis\settings.json.bak-20260922_171207`）→ 側車重啟（舊 PID 33076 → 新 27956，**14 秒**起返）。
- **實證**：`/health` `wake_on:false`；`voice_status.json` `wake_on:false` 17:12:26；serve.log 出現 `[warn] 語音前端=Hermes — Jarvis 聽候已禁`；`wake_debug.log` **75 秒零增長**（最後一行 17:12:09）→ 聽候線程真停。alert poller（pythonw）／STT SenseVoice 預載照正常。
- **還原方法**：`POST /settings {"voice_frontend":"jarvis"}`（或改 settings.json）→ 重啟側車（kill 8765 擁有者 PID，Electron 自動 respawn）→ 見 `[ok] 聽候 Jarvis` 即回到原狀。
- **⚠️ 未處理風險（等 SK 一句）**：側車每日 09:00 自檢仍會跑 `_tune_threshold` 嘅 decay 分支（`avg_peak<0.28 and fires==0` → 門檻 −0.05，最低 0.25），而 `notable` 含「門檻有變」→ 可能**每日自動降門檻＋出一次提示音**；新 mic 到時門檻可能已漂到 0.25（＝更易誤觸）。
- **plan 歸檔**：`.hermes/plans/2026-09-22-self-monitor-honest-fp-and-step-trend.md` 已標「SK 選 3 停手」，內含 R1（3:7）／R2（2:8）逐條 blocker ＋ review log → 新 mic 到時可直接沿用，唔使重做。
- **發現 B（實錘）**：`state.db` 有 247 個 `jarvis-*` session，其中 **198 個第一句係完全相同字串 `怎樣開 Chrome？`**（09-12 16:36–18:27 一日 70 個，最短隔 9 秒）；`serve.log`＋備份搜該字串 **0 次** → 冇經麥克風。
- **真兇**：`tests/test_brain.py::test_engine_query_with_mocked_llm`（:302）只 mock `brain._chat`，**冇停 `hermes_enabled`** → `engine.execute_utterance`（:124/:138 route=unknown）行 `_dispatch_hermes()` → 真 Hermes API。**現場證實**：單跑該測試 → 即新增 session `jarvis-1fd59b1d`（`如何開啟 Chrome #6`）。
- 語音側實數：09-01（SK 叫買新 mic）後語音路徑收音 **81** 次（舊備份 33＋現行 48），其中 **73 次（90%）＝亂碼／空白**；09-13 後仍留 22 個垃圾 session。
- Plan 已加 §2.5（發現 B）＋§3.5（測試隔離設計：mock `engine.load_settings`／哨兵測試／可選 conftest 全域隔離）；等 SK 揀 (a)/(b) ＋隔離深度。

## 2026-09-22 17:3x（Discord；SK「go」→ 自我監測老實化 plan）
- 親核實錘（SK 報「冇用 JARVIS 但 false active」）：serve.log 窗口 09-10→09-22，`[ear] raw=` **48** 次中，`[fail] 聽唔清` 7 ＋ `[route] unknown`／`[hermes] kind=unknown` 40 → **100% 語音指令無效**（例 `精行还还在。`／`这样大家很公平都会。`／`。`），且真開咗垃圾 session（`[hermes] session=`）。
- 但 `self_monitor.py:33 _FP_DUR_S=0.6` 只計 `oww_cmd_pcm dur<0.6s` → 呢批 `dur=1.8~4.6s` 全唔計，self_monitor.log 連日 `fp=0`；連鎖：`_tune_threshold`（fp≥3 才 +0.05）永遠唔觸發。
- Plan 寫好：`.hermes/plans/2026-09-22-self-monitor-honest-fp-and-step-trend.md`（新 deterministic 訊號 fp_junk/junk_sess、headline fp 合成、step-change 趨勢規則、驗收＋負控＋還原）。**待 SK 揀 (a) 只報數字（暫停 auto-tune，建議）／(b) 照自動調門檻**；R1 反方＋數字核實雙 reviewer 排 18:00 後（非高峰）。
- LHM 開機自動啟動**親證有效**：今日 08:54:22 開機（同日 08:38／08:18／08:08 亦 boot 過）；LHM 進程 08:55:04 起（開機 +35s，零手動）；排程工作 `JARVIS LHM Sensor`（logon trigger、RunLevel Highest）Action＝`LibreHardwareMonitor.exe`。
- LHM 網頁埠 8085 已 listen；`scripts/hw_monitor.py` 讀到 `cpu_temp_c=80.0`（CS2 中）／GPU 59°C 62% 280W／uptime 7.8h → D 項「LHM autostart 等真 reboot」**收貨**（RC：os.LastBootUpTime＋Get-Process StartTime＋hw_monitor JSON）。
- 順手核 JARVIS 本體正常：`JARVIS-ONE-0.4.13.exe` 行緊、8765 `/health` ok（wake_on true）。
- 全程序用 hidden VBS 包（零彈窗）；跑完 kill 殘留 wscript／powershell 並刪 `.out`。
- 仍未開工：`self_review.detect_trend` sustained-high 規則（D 項另一條；code 改動 → 等非高峰＋SK go 才寫 plan）。

- **MC／packai a+b（09-20）**：plan v3.1 過 review（R3 8:2）→ cursor 實作 → Hermes 親驗（compile RC=0／53 檢查綠／python 124 檔 1 已知紅／5 條負控）→ FTB 沙盒 4 輪真機（世界生成三類 ＋ 必答清單）＋ 跨包 UniversIO 7/7；**code 未 commit，等 SK**。詳 `super_minecraft_AI_player/.hermes/plans/HANDOFF.md`。
- **MC a+b（09-20 後續）**：code review 捉到 P0（gap 判定被 marker 自我命中 ⇒ b 對 a no-op），Hermes 親手 RED→修→NC 紅→還原綠→真機一輪；另修 P1×2、留 P1×4 待辦；docs commit `ae70d74`；**code 未 commit**（等 SK 揀 (1) 只 commit 本批 ／ (2) 累積到版本）。
- **MC a+b（09-4x）**：SK 揀 A → 累積批次 commit `f325c4e`（135 檔，唔 push）；commit 前掃 secrets 全清、runtime `logs/` 故意排除（未入 .gitignore，建議下次加）；UniversIO 最終版 jar 覆核 7/7 全綠。
- **11:1x packai 測試範圍**：新增兩個沙盒（Star Technology／ATM8，皆 1.19.2 Forge）＋登記文件 `docs/TEST_SCOPE.md`；jar `b5ffe2761cea`；遊戲內 smoke 待 Gate 轉 idle。

## 今日完成（2026-09-22）
- jarvis-pc 當日無新 commit
- 未 commit 檔案 3 個：.hermes/plans/HANDOFF.md, hud/main.js, hud/package.json

## 今日完成（2026-09-21）
- jarvis-pc 當日無新 commit
- 未 commit 檔案 3 個：.hermes/plans/HANDOFF.md, hud/main.js, hud/package.json

## 今日完成（2026-09-20）
- jarvis-pc 當日 commit 6 個（最新：be003f4 docs(handoff): packai 測試範圍擴充（Star Technology／ATM8 沙盒））
- 未 commit 檔案 2 個：hud/main.js, hud/package.json

## 2026-09-20 06:5x（Discord；SK「read hand off」→ drift 複核）
- 讀齊兩份 HANDOFF（jarvis-pc＋MC）＋逐項對 live 核（git／mtime／sha256／cron output／instance jar）；零新 code 改動。
- 捉到 4 處過時，已修入 STATE：① jarvis-pc STATE 停留 09-17（09-17 12:00 HOLD 已過期、MC 摘要滯後）② 本檔 09-19 skill 段未 commit ③ MC STATE 未寫 73 檔未 commit 規模 ④ cron handoff 今日 05:45 FAILED(429) 零寫入。
- 親核數字：jarvis-pc HEAD `c0a6a42`（feature branch ahead 41）；真 instance jar `06b5b129a114`（09-18 07:12）；MC tree 73 檔未 commit（+4,484／−1,305）。
- SK 09-20 06:5x：「read hand off / check last session / update hand off first」 → 已讀上一個 session（09-19 08:03–09-20 01:05，3,830 msgs），本檔已更新；下一步序（a 維度／生態群系／礦物分佈｜ b 必答清單｜ c 細試點） **等 SK 覆**。
- 親核：上一個 session 嘅遊戲內測試係喺 `packai_sandbox_ftb` 沙盒跑（jar `e0fbecc77085`）；真 instance jar 仍 `06b5b129a114`——jar 內方法名核實：真 instance **冇** `routeLinesForItem`／`mergeJarRoutes`，沙盒有。


## 2026-09-19 session（Discord；Hermes skill 庫 renew ＋ 語音 skill 3合1）

- **④ 語音 skill 3合1＝已執行＋驗收通過（SK `go`；Hermes 親手做）**：`jarvis-voice-assistant` 為 umbrella，吸收 `windows-voice-pipeline`＋`hermes-voice-windows`；兩者已用 **`hermes curator archive`** 歸檔（`skills\.archive\`）。**7 項實測驗收全中**：A1 `software-development 31→30`／`autonomous-ai-agents 13→12`／curator managed 124→122／`list-archived 1→3`；A2 14 個搬入檔＝**11 sha1 逐字一致＋3 有改動**；A3 總量 221,887→**222,982**（Δ＝+274 fm／+746 指標節／+75 七行）；A4 HOLD 段 identical；A5 `references/*.md`＝31；A6 舊名命中 12 行（逐行處置；`electron-windows-overlay:11` 已改指 umbrella）。備份：`%TEMP%\skill_voice_merge_backup_20260919_195843`（36 檔＋`MANIFEST.json`）；**還原 3 步已倒帶演練＝CLEAN（21/21 sha1 一致）**。plan：`.hermes\plans\2026-09-19-skill-voice-merge-plan.md`；review 5 份 `plans\reviews\2026-09-19_skill-voice-merge-plan-R{1..5}-opposing.md`（**4:6→6:4→7:3→7:3→8:2**）。
- **③ skill 庫 renew 其餘 3 項（Hermes 自己 ③ 清單）**：① 修真死路徑：`hermes-voice-windows` 內 `~/.hermes/AGENTS.md` → `$HERMES_HOME/...`（其餘 6 條經親驗為文檔／陷阱記錄＝誤報）② git 分支雙胞胎合併 → keeper `long-lived-branch-merge`（吸收政策表／invariant／診斷指令／非專家報告法），`git-branch-integration` 已原生歸檔 ③ `minecraft-modpack-ai-development` **100,306 → 56,212 字**（4 大段逐字搬 `references/`，sha1 驗證零損失）。
- **流程教訓（可重用）**：① audit 報告必須逐項親驗（今次第 1、5 項都係誤報）② **整合前先喺 `%TEMP%` 彩排 dry-run**（今次彩排揭發 2 個 bug：HOLD 抽段法錯、A6 用「合併前」值）③ 歸檔**一律用 `hermes curator archive`**——raw `mv` 會令 disk／snapshot／usage／live index 四層狀態唔一致（已修 `git-branch-integration`）。


## 2026-09-16/17 夜間（已核對，零新工作）

- 09-16 21:03–23:46 語音 session ×5（api_server）全部 ASR 亂碼（「系啊唔系…」「马叫维斯」等）→ 照 **mic HOLD**、零動作、零彈窗；00:22 SK 熄機；09-17 07:43 gateway 起返後 cron 補跑（session-handoff／daily-self-review 皆 ok）。核對：JARVIS 本體零 code 改動、零 commit、零 deploy。

## 2026-09-16 session（JARVIS HUD 0.4.13 ＋ Hermes watchdog v3）

- **HUD sidecar bug 修好**：`spawnSidecar()` 撞 ENOENT 唔清 `sidecarProc`（Node 只 emit `'error'`、**唔 emit** `'exit'`）→ 永久 early-return，sidecar 永遠拉唔返（今朝 8765 死嘅直接原因之一）。修：`on('error')` identity-check 清 ref ＋共用 5s respawn timer；早退／health check 加 `exitCode === null` 分支。A/B 實測（`%TEMP%\hud_sidecar_ab_test.py`）：舊 code 1 次嘗試後永久靜；新 code 11s 內 3 次後退避 60s；interpreter 中途出現 → **唔重啟 app** 之下 `8765 /health` 自動返 200。Build `JARVIS-ONE-0.4.13.exe`（`BUILD_EXIT=0`）＋換版＋3 個 `.lnk` 更新；8642/8765/8770/8771 正常、0 閃窗。**版本軌跡 0.4.11 → 0.4.12（predicate 寫錯，實測退化 1 次 vs 3 次）→ 0.4.13（`child.pid === undefined`，已驗證）**；反方 review 亦捉到 plan 敘事錯（07:47 係 SK 重啟部機、真窗口 47m43s、第三條 launch path）。plan `docs/plans/2026-09-16-hud-sidecar-spawn-failure-respawn.md`。**hud/main.js 未 commit**（等 SK 真機驗收）
- **Hermes watchdog v3 上線**：pre-flight（`Test-Interpreter`）＋ bounded 自癒（`uv python install <ver> --reinstall` **＋** `uv venv --allow-existing`，兩件 artifact 都要修）＋ interpreter 壞就**唔 call launch VBS**（唔會再彈 WSH 80070002）＋ login 路徑改經新 guard VBS ＋ 拉完核實 `/health` 才寫 `result: success|failed`（reporter v2 只對 success 講「已自動復活」）。cursor 實作 → 我獨立沙盒驗收**捉到 3 個真 bug**（PS 5.1 `Start-Process -ArgumentList @(...)` array 甩引號 → interpreter 永遠當壞；`-RedirectStandard*`+`.Trim()` 炸 `[Object[]]`；guard probe 同款 → 會永遠 SKIP 唔開 gateway）→ micro-fix 輪修好 → 沙盒 6 項全綠（含 0 閃窗；flash 偵測器有正控 3 次）＋ guard 兩向測試。真機 tick：PID 6764 不變、8642 200、events 無新增、0 flash、log 出 `ENSURE_GUARD`。備份 `.bak-20260916_093243`。plan `docs/plans/2026-09-16-hermes-gateway-watchdog-hardening.md`
- **真根因（要 SK 落手）**：Surfshark 防毒誤判 `Drop.Win64.UserProfileSelfRun.710`（09-14 13:52 隔離 `venv\Scripts\python.exe`）→ **未加 exclusion 之前仍有機會再刪**：`hermes-agent\venv`／`AppData\Local\Python`／`AppData\Roaming\uv\python`
- **零彈窗新法（SK 投訴過「why it keep popup」）**：`%TEMP%\run_hidden.vbs`（`wscript` → `sh.Run("cmd /c (...) > log", 0, True)`）＝整條鏈共用一個 hidden console，孫進程繼承 → cursor 派工／npm build／powershell 檢查 **0 閃窗**（已寫入 skill `cursor-cli-integration`）。HUD overlay 反覆彈出＝3 個 dev instance ＋多次重啟嘅正常副作用，唔係 bug。

## 今日完成（2026-09-16）

- Hermes gateway 停機恢復（07:41-07:57）：uv CPython 3.11 缺 `python.exe` 致 trampoline 失效（報 80070002）、crash loop；`uv python install 3.11 --reinstall` + `uv venv --allow-existing` 補回 trampoline，`hermes gateway start` 恢復，crash loop 停止；見 `code_change_log.md`。



## 2026-09-16 session（KubeJS 取得途徑線：停手 → 收窄）

- SK 問「can AI know how to craft this item?」（满溢神恩项链）→ 我報「3 條途徑」**錯**：`goety_ritual.js:1` 簽名 `GoetyRitualRecipe(craftType, ingredients, activation_item, output)` → 第 3 個 arg 係**祭品（消耗）**；真產出係 gateway pearl。`weapon_infusion.js:14` 同類。
- 真相：满溢項鍊唯一取得途徑＝**充能**（`server_scripts/curios/entity_death.js:21-27`：戴住「空」項鍊打死 4 王之一 → 變身）；空項鍊嚟自 `chestloot_2.json`（loot 索引已覆蓋）。AI 答「查唔到」係錯（路徑存在）。
- **一般化方案停手**（照 SK 3–4 輪規矩）：逐輪比分 R1 3:7／2:8、R2 5:5、R3 4:6／3:7 → 停手報告 `2026-09-15_kubejs-acquisition-path-facts-v3-stop.md`（含卡死點：map-key 來源側／方向過濾擋唔到 peer 洩漏／4 王名要 entity 名解析）。
- **研究（SK 指示 search online）**：JEI／EMI 需 per-mod plugin 才有自訂配方（本包 231 jar：47 個有 JEI plugin、**只有 2 個有 EMI plugin**）；JER 未裝；EMI Loot 已裝；**事件式轉換冇任何 viewer 覆蓋** → 只有腳本／tooltip。
- 工具落地：`tools/kubejs_mechanism_audit.py` ＋ `docs/kubejs-mechanism-coverage.{md,json}`（13 pack：863 原始 → **402 清洗後候選機制**、21 種自訂 recipe class、86 個事件家族）；`tools/kubejs_inventory_probe.py`。commit `e874d9f`／`9828a01`。
- 窄版 v4 → R1 **正方 2 : 反方 8**／**3 : 反方 7** → 拆 **plan α**（peer 行洩漏：真 trace 67 個 peer entry 有 **64 個垃圾**）＋**plan β（v4.1）**；commit `149e628`；R2 review 派咗（SK 關機中斷）。
- 更正我兩個錯：① 「唔需要改 answer layer」**錯**（新 edge 喺 `AskEngine:472-504` 冇 branch 會直接被丟）② 王名 zh_cn 係「暗夜巫妖」唔係「暗夜巫師」。
- B11 已 build＋部署（jar `97d279f7`）；115 check 全綠；我嘅負對照 2 個紅→綠。


## 2026-09-15 session（packai 主線）— Settings C 批／D 批／卡片線

- **C-0 落地**（`1b207174…`）：`renderScreen` 兩分支次序（正常＝自繪→widgets→tips 最後；fallback＝widgets→「畫面太細」→tips，plan 字面反而錯）＋ `mouseClicked` 先交 vanilla（`if (super.mouseClicked(...)) return true;`）＋ scroll 觸發 rebuild 時**保 draft**；新閘 `check_settings_render_order.py`（其後升級 allowlist＋自帶注入負對照）；其餘 3 個 screen 只加註釋（零行為）。
- **C-1 落地**（`ca6b2b36…`）：`llm.traceKeepDays`（預設 3、日清喺檔案數修剪**之前**）／`llm.askMaxToolRounds`（3、**欄位注入** `AskLoopState.maxLlmRounds`）／`llm.dailyTokenLimit`（`config/packai-usage.json`、`synchronized` 單一 writer、64 KiB 上限、缺失 usage 用估算入帳）；新檔 `logic/DailyTokenUsage.java`＋harness；新閘 `check_settings_c1.py`；負對照 2 個皆紅。
- **D 批落地**（`57e59a06…`）：**一行「模型」**＋picker 兩節（雲端／本機；`Target`＋`Row`、header 唔可揀、空節唔顯示、強制 fetch 兩個後端＋CAS pending）；**tag 單一來源** `PackAiConfig.effectiveModelTagKey()`（停用／本機／雲端／雲端・未設 key）；描述板 `Font.split` 3 行 wrap＋**Shift 全文**（1.19.2 `Screen.renderTooltip` 唔會斷行，必須先 split）；`DESC_DOCK_H 36→56`＋可見行數 ≥4 斷言；`boxX = r.x + labelW + 4`；`hiddenInUi`（保留 registry 令 reset／setters 閘唔爆）；新閘 `check_settings_model_picker.py`＋harness `ModelPickerRowsCheck`。
- **卡片線實錘**（SK 20:25–20:30 三次真機 ask，讀 `latest.log`＋trace）：`infinity_sword` 0 卡＝**正確**；`infinity_sword_organ` 4 卡＝3 正確＋1 張**tag 樣本顯示錯**（卡面 grid 兩個樣本都唔係焦點）；`tetra:modular_sword` 1 任務卡＋3 張**設計性抑制**（`toolParts path=strip`）。
- **三次診斷翻轉（全部有 file:line 否證）**：① 以為錯卡＝attribution 錯 → 否證（`recipes/common.js:171` 器官真係合法材料，focus 真喺 `#kubejs:organ`）② 以為改卡樣本可行 → 否證（`RecipeCard` 冇 ingredient provenance、格仔由 JEI drawable 畫）③ 以為正文講隱藏卡＝卡側問題 → 否證（嗰句嚟自 lang `packai.reply.tool_build` #23 提示詞）。
- **真 bug（反方搵到）**：`RecipeEmbed.placeEmissionCardsByRef:778-825` 插卡用**顯示清單 index**（唔係 refId）→ 顯示側一剷卡即**錯位**＝SK 講嘅「張冠李戴」→ **B11 為唯一修法**。
- **B11 落地**（jar `97d279f7` 已部署）：`AskToolEnv.offerEmission` 喺 refId 之前剷框架卡（純核心 `ModularFrameCards.shouldDropFrameCard` 同顯示側共用）、`AskLoopState` 新欄＋雙 bind＋兩處 auto-emit 跳過、全剷時工具明示「已隱藏」；115 check 全綠；我嘅負對照 ①拿掉過濾→紅 ②移到 refId 後→紅（`order pred=20 ref=19 add=23`）
- **B9／B10 落地**（log-only，jar `b288f80e…` 未部署）：`AskCardsDebug.visibleEmissionRefIds`（**剔唔重編**）＋ `render.cards.final.role` 統一 `promptRole()`；harness 加 2 條子斷言；負對照紅→綠、114 check 全綠。
- **B11**：plan §14 v2 過 review **正方 8 : 反方 2**（前置修：S2 次序、S1 範圍）→ **已派 cursor（跑緊）**。
- **我嘅失誤（已寫入 skill／plan）**：① 比分方向寫反（SK 兩次糾正 → 定「**正方 : 反方**」，正方寫前）② 誤報 tag 未實作（只 grep 中文字面，忽略 lang-key 間接）③ 卡 bug 三次錯判因果（上列）。

## 2026-09-15 session — alert enforce 驗收清單補送（cron FAILED）

- 09-15 03:45：一次性 cron `4695c33b8bdf`（alert-enforce 三情境驗收清單，09-13 排）**FAILED**＝`RuntimeError: Non-streaming API call timed out after 600s`，清單冇自動送。
- 09-15 05:2x：shadow 樣本已滿 48h（`shadow_heartbeat.jsonl` 最早 09-12 18:16，count 4018 行）；`--hours 48` 報告 decisions hold=7（全 gaming）／speak=0／digest=0／drop=0；gaming 落差 v1_true=312／v2_true=468／v1_only=11／v2_only=167。
- 09-15 05:2x：手動補出三情境驗收清單（打機→hold／通話→hold／idle→speak，各核 `shadow_ledger` decision）。SK 未開始驗收、未上 enforce；`alert_policy_mode` 仍＝`shadow`。
- SK 指示「check and update handoff first」（DeepSeek 模型唔穩定，隨時斷線）。零 config／code 改動、零 test alert、零 commit。

## 今日完成（2026-09-14）

- 09-14 02:2x–02:5x：packai jar `a4e689de` 部署＋真機 smoke 4/4；fix commits `8d25433`／`9f9baaf`（**未 push**）。
- 09-14 02:41：SK 要求「Tetra/Tinker 類模組化工具每次只答 1 件」→ plan **K3 `modularToolSingleItem`**（預設 ON）。
- 09-14 02:53：開 plan `docs/plans/2026-09-14-packai-reply-layout-plan.md`（`eadc008`）；SK 三張截圖列為驗收案例。
- 09-14 02:57／03:08：兩輪反方 review（read-only subagent）**R1 7:3、R2 7:3** → 依契約停手問 SK；hole 全吸收。
- 09-14 03:03–03:16：plan v2→v3（`75bdf86`／`94b3767`）；SK 提議經 JEI 拎 output → R5 改 `JeiRecipeCards.fromVanillaCrafting`。
- 09-14 03:46：SK 要「log 齊送出／檢查／模型回覆」→ S0 由 3 個 log 欄升級為**全鏈路審計 trace**（v4，`7ba52a7`）。
- 09-14 05:13：SK 定 trace 路徑＝`<instance>/packai/trace/`＋`index.jsonl`（似 KubeJS 自成一格）→ `7954e84`。
- 09-14 05:14：派 **Task S**（cursor-agent）實作 trace（零行為改動）；05:30 實況＝`AskTrace.java`×2＋`AskTraceCheck` 已寫、11 檔改動、報告 0 byte → **未 build／未驗**。
- 09-14 05:4x（cron 核實）：jarvis-pc tree clean／cron 9 個全 ok／8765 `/health` ok／`shadow` 模式；MC 前景 playing（全程零 GUI 動作）。
- 09-14 15:39：免費模型 upstage/solar-pro4:free 驗證 Through——HANDOFF agent 正常運作（Nous）。step-3.7-flash:free 曾 429 於 15:30/31。

## 逐日 index（一行一件；blocker 例外可 2 行）

- 2026-09-13 16:0x：T5 #2 輪 20 題 → `check_ask_display_leak` rc=0（4 條新答案零 `role=`／零 `PURPOSE`）＝T0 修復真機確認。
- 2026-09-13 16:2x：JEI 張冠李戴修好 — 根因 `JeiInfoFacts.sameItem():413` 只比 path 唔比 namespace；改全 id＋新 `shouldAttachForFocus`；Java check＋雙樹 md5＋4 條 python 全過。
- 2026-09-13 16:3x：Tetra 結構分流（`[TOOL_BUILD]` → 「怎麼來」）＋兩輪 review 修復；99 PASS／3 既有 stale FAIL、兩個 Java harness OK、build OK、雙樹對稱 OK。
- 2026-09-13 19:0x–20:0x：review 三輪（R1/R2/R3 全部 FIX-FIRST）→ 修 D1–J：多選組成／offline 三出口／措辭／token 統一／`role=` 廣義／footer 結構性渲染。
- 2026-09-14 02:2x：部署 `a4e689de`（MC 熄自動；舊 `551136fb` 備份落 `dist/_smoke_backups/`）；jar 開檔驗新 symbols＋3 語言 label keys 齊。
- 2026-09-14 02:3x：**真機 smoke 4/4 過**：組成喺「怎麼來」（唔喺「怎麼用」）、多選兩件都帶組成、4 條答案零 raw token、`toolCards emission=4 cardsOut=4`；`check_ask_display_leak` rc=0。
- 2026-09-14 02:5x：**已 commit（未 push）** `8d25433` fix(jei) 全 id 歸屬；`9f9baaf` fix(ask) 洩漏＋組成段位＋來源行標籤翻譯。


- 2026-09-13 15:0x：**T0 修復部署**（真實洩漏：答案【來源】行寫 `role=output／input`＋`PURPOSE`）——根因 `PLAYER_UNSAFE_MARKERS` 只過濾 FACT fallback、模型正文路徑冇剝；改 `AskReplyScrub.scrubInternalFieldEcho`＋`ReplySources` 髒 footer 換 canonical＋6 lang；我獨立 Java harness 實測真機字串通過；jar `551136fb` 部署（三邊 sha256 一致、舊 `450c3a76` 已備份）。
- 2026-09-13 15:0x：**Tetra 計劃** R1 4:6→R2 4:6→R3 6:4 未達 8:2 → 依契約停手報 SK；SK 揀 **a（結構性分流）**；已派 cursor 將 `[TOOL_BUILD]` 由 `AskService:449-452` prepend 抽出、改掛 `AskEngine:508-518` `sectionHowToGet` 之下（兩樹）。
- 2026-09-13 15:0x：**FTB 任務線 plan**（SK 要求新增）R1 3:7→R2 5:5／7:3→R3 7:3／8:2 **達標**；SK 決定 **HOLD**（只留 plan，將來做）。
- 2026-09-13 15:0x：**ASR（Fun-ASR-Nano）**：模型 08-07 已完整下載（2.0GB）；離線載入 15.2s、每條 0.6–1.2s、A/B 樣本唔夠判 → SK 決定**全線 hold 等新 mic**（同 wake／聲紋／AEC 一齊）。
- 2026-09-13 15:0x：契約更新 —— `AGENTS.md` 加「SK 叫→顯示／JARVIS 主動→`--minimized`」（第 115 行；主契約＋源頭 copy md5 `7230bf0b`）。

- 2026-09-13 13:3x–14:0x（Discord session，SK 逐項拍板）：T5 **jar 已 build＋部署**（`gradlew jar` 16s；新 `450c3a76`＝build/libs＝instance mods＝dist 三邊一致；舊 `17ebc474` 備份 `dist/_smoke_backups/packai-0.2.1+mc1.19.2-forge.jar.bak-20260913_133727`）
- 2026-09-13 14:0x：`check_jar_contains_fix.py` **OK**（T2 fail-closed symbols＋lang keys）＋K30–K34 harness **綠**（`AskToolLoopCheck`／`AskReplyScrubCheck OK`）
- 2026-09-13 14:0x：修 **pre-existing 過時 assert**（`"output"`→`"OUTPUT"`；兩樹 md5 `e18f6747`；baseline worktree `7317763` 證實執之前已壞）＋ cursor read-only 一致性分析 **VERDICT SHIP／零 FINDING**（**未 commit**，等 SK）
- 2026-09-13 14:0x：全量 python checks **101 檔 / 4 FAIL**＝baseline 3（worktree 對照證實）＋`check_ask_display_leak.py`（等真機 log）
- 2026-09-13 13:4x：`AGENTS.md` 加新條款（第 115 行）「**SK 叫→顯示；JARVIS 主動→`bg_launch.py --minimized`**」；主契約＋源頭 copy md5 `7230bf0b`；備份 `.bak-20260913-133850`
- 2026-09-13 13:4x：**兩 repo 已 push**（jarvis-pc `14b2cc3`／packai `4886346`，ahead=0）；一次性 cron `4695c33b8bdf`（09-15 03:15 alert enforce 驗收清單）
- 2026-09-13 13:4x：SK 定「**滑鼠有動＝打機**」（已入 memory；alert gaming 判定用）
- 2026-09-13 14:0x：ASR 計劃 `docs/plans/2026-09-13-asr-fun-asr-nano-plan.md`（`ear.py` 早有 `transcribe_fun_asr`）；**Fun-ASR-Nano 08-07 已完整下載**（ModelScope 2.0GB）→ T1 取消
- 2026-09-13 14:1x：ASR 離線實測（CPU）：載入 **15.2s**、每 2s clip **0.6–1.2s**（無 08-07「似凍」）；A/B 用 5 條 wake 碎片兩邊都垃圾 → 唔可判高低
- 2026-09-13 14:2x：**ASR T2 錄音 HOLD**（SK 明示：等新 mic 先做，同 wake／聲紋／AEC 一齊排）；packai test fix 已 commit `f0ac745`（未 push）

> 歸檔：**2026-09-13 及之前**嘅完整 session 記錄已搬去 `plans/archive/HANDOFF-2026-09.md`（要史前文就 grep 嗰邊）。


## 陷阱（重溫）

- **Settings 單一 writer**：改 settings 用 sidecar `POST /settings`（Bearer = `%APPDATA%\Jarvis\alerts\mcp_token.txt`），唔好直接寫 settings.json
- **dpapi:** 值唔好當明文讀；settings.json 已加密
- **jarvis serve** 由 Electron spawn（JARVIS_ELECTRON_HOST=1 headless）；唔好手動起第二個
- **⚠️ onnxruntime 1.28 bug（2026-08-31 實測）**：openwakeword 0.6.0 喺 onnxruntime 1.28 上模型輸出全 0 → wake 死（best 卡 0.001）。pyproject 已 pin `<1.28`；**唔好升級 onnxruntime**。wake_debug `best` 一直 0.001 + 冇 `oww_predict_err` = 呢個坑
- **Arctis headset 休眠**：rms=0.000 持續 = mic 斷連（headset 休眠）——戴返/喚醒先叫到；`mic_signal_ok=false` 喺 voice_status 顯示
- **Qwen2.5-VL server**：用 jarvis-pc env python 跑（`env -u PYTHONPATH`）；transformers video decode 壞咗 → server 內建 pyav 抽幀（16 幀 640p）；model 要 `torch_dtype=torch.bfloat16`（auto 會 OOM）
- **Mage-VL**：`check_imports` monkeypatch 已喺 mage_engine.py 內建；單幀理解
- Python：`C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe`，跑 jarvis 用 `env -u PYTHONPATH`
- 換版流程：bump version → `npm run dist` → kill JARVIS（單斜線 taskkill）→ 開新 exe → 更新 3 個 .lnk
- 語音一律英文；GUI 操作前讀 sk_activity.json（playing/using 禁彈窗）
- **Code Review 兩次**（契約規則）：pass1 刪重複/拆函數/補註釋/降耦合；pass2 三個月後脆弱位

## 語音/硬體設定（驗證過）

- wake_mic = 「麥克風 (2- Arctis Nova 7)」44.1k；TTS 輸出 = G27Q 螢幕喇叭；AEC reference = Sonar Media + Sonar Chat（唔用 Arctis loopback）
- ⚠️ Arctis 週期性 rms=0.000（headset 休眠/斷連）——叫唔醒先睇 wake_debug.log
- mic 細（avg ~0.05）→ AGC 上線；wake_threshold 0.75（self-monitor 自動調出嚟）

### Game Session Detection Phase 1（2026-09-02 session）
- 修「X is ready, sir.」誤報（前景切換 + Minecraft server 誤判）——process-based detection（Steam RunningAppID + tasklist + wmic java cmdline client/server split）+ session latch + running-set-growth alert
- activity_monitor.py（hermes scripts）已應用（backup .py.bak）；shell_app.py commit `ea38b22`；sidecar 已重啟生效
- 4 輪 independent review（11 findings 全修，final pass）；plan: `.hermes/plans/2026-09-02_135000-game-session-detection-phase1.md`
- 已知：`test_stt_stats::test_missing_logs` golden fail = baseline 環境問題（serve.log 有 repair 記錄）——要修 run_once fallback 或 test isolation
- 待做：SK 實測場景 A-E（開 game/切 Discord/關 game）；Phase 2 = 通用 app detection framework（SK 願景：唔止 game）
