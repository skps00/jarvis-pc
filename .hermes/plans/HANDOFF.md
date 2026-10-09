# HANDOFF — jarvis-pc（狀態區塊 + 逐日 index）

<!-- STATE:BEGIN -->
## 狀態（每次 session 尾／cron **改寫**；新 section 一律加喺本區塊**之下**）

- **目標**：JARVIS ONE（語音／HUD／alerts）穩定收尾 ＋ MC packai（Forge 1.19.2 primary）＋ MayaCraft DJ2 客戶端玩家支援（非 repo 專案）。計畫書：`.hermes/plans/REMAINING_WORK.md`
- **現狀（2026-10-09 04:0x 改寫；全部 Hermes 親核）**
- **10-09 凌晨（SK 睡時 Hermes 自動跑，全部 PASS）**：① packai raw-id A1/A2 真機過（`packai_sandbox` 4/4 OK、玩家 body 0 path-token）② M1 面板驅動 A9 過（ATM8 cards 2／5）③ H1 插件化實作＋真 dev instance CDP 驗過（API 白名單／hw-ring 卡／sensors 對得上 nvidia-smi／**0 重疊**）④ promo M0 定案＝`ddagrab_dl`＋ATM8 原片 105.2s 已錄 ⑤ HEI crash（SK 自己換 4.35.1）Hermes 核實收線。**三者 code 全部未 commit（等 SK go）**。
- **JARVIS ONE＝0.4.16 上線（10-09 04:53；H1 插件化＋hw-ring 卡）**：五進程／`8642/8765/8770/8771` LISTEN／零可見 console 窗／`/health` 200；exe sha256 `29d1be4e…`（SWAP 用官方 `swap_hud_version.ps1`）。alert shadow＋`alert_voice=false`（語音 HOLD）⇒ poller 從未啟動 ⇒ **#9 綁「等新 mic」**（升 enforce 前要重跑三個情境）。
- **Git（jarvis-pc）**：PR #13 已 merge（`aaa9917`）＋部署副本 `hermes\scripts\jarvis_sidecar_health.py` 已更新（fingerprint 一致、冇假警報）。未 commit＝`uv.lock`＋untracked `2026-10-04_agent-vm-3060-plan.md`；**10-09 H1 code 已 commit＋已 push**（`165a149..2c939d3`，10-09 13:5x）。
- **X3D CCD 派工**：主導＝最高權限 Windows 排程 `\JARVIS-GameVCachePin`（Hermes cron 已刪）；還原＝`game_vcache_pin.json` `enabled:false`。**MC heap**：DJ2 真 heap＝8G（G1GC，`relauncher.json`；Prism MaxMemAlloc 從來冇生效），10-06 SK 定案唔改。
- **packai**：Slice 1b 已 push；Modrinth slug＝`pack-ai-assistant`；沙盒 jar 現為 `autotest-dev-0.2.3.jar`（sha256 `140b9c0cab35…`＝raw-id fix＋M1，backup `%TEMP%\deploy_backup_20261009_0325\`）。
- **DJ2-Cleanroom**：`dj2-fixes-1.1.1` 已驗收；**HEI 4.35.0→4.35.1 已由 SK 換入並親測**（Hermes 核 sha `8777b115592519ea…`）；客戶端三項（字體／GUI／光影）**SK 10-09 眼睇 OK**。
- **5090 黑屏 Tier 1** 設定仍在（還原 `mpo_restore.reg`；watchdog cron 無新事件）；**CS2 線已收**（baseline 中位 650 FPS／1% low 235）。**新 session 自動 brief** 已上線（`hooks.pre_llm_call`）。**求職線**：最後階段（panel 下週），內幕只留 `Documents\MS_DCT_Prep\`。**語音／mic 線 HOLD**。
- **唔准郁（硬限制）**：打機／用緊電腦＝零彈窗零搶焦點（先讀 `state/sk_activity.json`）；GUI 窗一律副螢幕、Chrome 主動開＝`bg_launch.py --minimized`；`AGENTS.md` 受保護；唔准 `curl|sh`；**HANDOFF 可公開→唔准入 secrets**；packai code 一律經 cursor-agent；唔准 `git add -A`；真 instance 唔准自動部署；語音／mic 線唔郁（wake／STT／AEC／聲紋／threshold）。
- **未解（等 SK 決）**：① ~~raw-id＋M1~~ **真機驗收已過**（等 go 就 commit code＋artifacts）② CS2 LPI 16-31 ③ cursor 凍線（SK 講「now」）④ TRCC＝唔做 ⑤ ~~HoloMat：H1 已上線 0.4.16~~ → **SK 10-09 眼睇新卡 OK，收工** ⑥ 窗口 2 剩 #11 主觀體驗 ⑦ `web_search` 屬間歇 ⑧ DJ2 郁動掉幀＝Litematica ⑨（**新**）ATM8 答案出現 raw **item tag id** `forge:ingots/steel`（`namespace:tag/path` 唔喺 fail-closed 網前綴）→ 等 SK 揀「擴網」定「人化 tag」；promo A3 像素掃會撳到 ⑩ ✅ MayaCraft HEI 訊息 **SK 已發**（10-09）
- **下一步（優先序）**：① promo：**motion-graphics 版 27 s 已出**（`docs/promo/mg-20261009/promo_mg_27s.mp4`，無旁白＋CC0 古典配樂）→ 剩 **補拍 shot 1／6＋KubeJS demo（要 SK 收機）＋擴到 50 s ＋封面／分發包** ② ✅ 兩 repo 已 push（10-09 13:5x；jarvis-pc 9 commits、packai 1 commit）③ 朋友求職個案（等對方答 5 條）④ CS2／NVIDIA 線已收 ⑤ #9／#5 等新 mic ⑥ 兩 repo push（等 SK 講）
- **歸檔索引**：`plans/archive/HANDOFF-2026-09.md`（最近 2026-10-03 搬 09-24～09-30）
- **參考段（檔尾）**：陷阱（重溫）／語音·硬體設定（驗證過）
<!-- STATE:END -->

## 今日完成（2026-10-09）
### promo（10-09 下午，Discord；SK 全程在線決策）
- 方向改動（SK go）：**取消旁白**（查實 Create 官方 trailer 全片冇旁白＝純遊戲畫面＋古典樂）；吸收 SK 貼嘅 B 站片（BV16Lam6JEgV／Wish_Coder／2:00／7.6 萬 view）motion-graphics 風格——量測 118.5s 只有 13 個硬切＝慢剪，靠深色底＋3D 浮動圖示＋大字逐句＋圖表＋logo 結尾。
- 產出（本機 PIL＋ffmpeg，0 API 成本）：`docs/promo/mg-20261009/promo_mg_27s.mp4`（27.2s）＋`promo_mg_50s.mp4`（50.3s、1920×1080/30fps/H.264/AAC）；版面＝深色底＋圓角窗框放真機畫面（唔遮 mod UI）＋底部大字卡＋標題卡／資訊卡／logo 結尾卡。
- 配樂＝莫扎特《費加洛》序曲 **CC0**（Wikimedia Commons，出處記 `docs/promo/narration-20261009/LICENSES.md`）；音量 −16 LUFS。
- 腳本：`%TEMP%\mg_promo_v3.py`（PIL 合成）＋`build_mg50.sh`（合成→壓片→配樂）；素材切段 `%TEMP%\mg2\s1..s5`（由 `promo_raw_20261009-034259.mp4` 105.2s 抽）。
- SK 新內容要求：加「**mod 讀得到 KubeJS 改過嘅 item／recipe**」→ 已出資訊卡 c3；真機 demo 待補拍（ATM8 沙盒有 KubeJS 1902.6.2＋`AskKubeJsBridgeCheck` harness 為證）。
- 待做：補拍 shot 1（JEI 清單）／shot 6（設定畫面）／KubeJS demo（全部要 SK 收機）＋封面＋分發包。
- 旁白線 park：piper JARVIS 聲（SK 否決）＋edge-tts 14 把聲試聽包（`docs/promo/narration-20261009/audition/`）。
- 成本（Hermes 用量庫估算）：本 session US$0.245／10-09 全日 US$0.248／10-07 起 US$2.02／開機至今 US$47.19。
- mp4 暫未入 git（binary、26MB）；如要入 git 要 SK 講。
- 追加（10-09 19:1x）：SK 要「見到完整操作流程」→ 補拍分鏡 `docs/promo/SHOTLIST-v5-user-journey-2026-10-09.md`（Y＝長按問 hovered 物品／`]`＝開面板，已由 `ClientSetup.java` 核實；ddagrab `draw_mouse` 預設開＝錄到游標；KubeJS demo 首選＝ATM8 刪走 Occultism 銀礦生成 `kubejs/server_scripts/ore_removal.js`）。
- overlay 動態（字幕滑入＋淡出、卡文字漸入、底部流動光）完成 → 重出 50s（3.4MB）；修咗兩個 bug：流動光越界（`x1<x0` 令 render abort）＋字幕滑入第二行被下界切斷（改 bottom-anchored）。

- jarvis-pc 當日 commit 7 個（最新：49edd34 docs(handoff): 10-09 04:53 JARVIS ONE 0.4.16 上線（H1 插件化）＋打包清單坑；）
- 未 commit 檔案 2 個：uv.lock, .hermes/plans/2026-10-04_agent-vm-
- 10-09 13:5x 已 push（`165a149..2c939d3`）；現時 ahead 1（HANDOFF docs commit）

## 2026-10-09 凌晨（Discord；SK 睡覺期間自動跑：packai A1/A2＋M1/A9 真機驗收、H1 實作＋GUI 驗證、promo M0＋原片）

SK 睡前指示：**1＋2＋3**（packai 驗收／HoloMat H1 開工／promo 拍片）＋「u done it all, and update the hand off」。以下全部 Hermes 自己跑、有原始輸出。

- **packai raw-id A1/A2 ＝ PASS（真機，`packai_sandbox`）**：jar `autotest-dev-0.2.3.jar`（sha256 開頭 `140b9c0cab35`＝fix＋M1）部署副本 backup `%TEMP%\deploy_backup_20261009_0325\`。4/4 OK（diamond×2、amethyst_shard×2，`cardsOut=7`）＋負控 `bedrock=NO_SAMPLE`；84s；+175,403 tokens。Hermes 用**獨立較闊** predicate（`x/y` path-like token）掃玩家 body：**0 命中**；原漏 → 「transmutation table rare」／「desert pyramid」／「bathhouse normal」；`check.post_scrub_drop=0`；零搶焦點。證據 `docs/research/artifacts/2026-10-09-rawid-a1a2/`。
- **M1 面板驅動層（A9）＝ PASS（真機，`packai_sandbox_atm8`）**：`question` case 2 條 → `ask-*-none.jsonl`（真走面板）body 1,216／1,456 字＋`cardsOut=2／5`；103s；+168,865 tokens；零搶焦點。證據 `docs/research/artifacts/2026-10-09-m1-a9/`。
- **⚠️ 新發現（未屬 plan v4 §7 範圍）**：ATM8 答案出現 **raw item tag id `forge:ingots/steel`**（2 處）——`namespace:tag/path` 形態唔喺 fail-closed 網 7 個前綴（`chests|gameplay|entities|inject|structures|spawners|blocks`）內 ⇒ 照樣出街（`post_scrub_drop=0`）。同一輪其他 `x/y` 命中全部係正常英文字（`furnace/smelters`／`loot/trade`）。**promo A3 像素掃會撳到** → 建議另開 plan（擴網到 tag 形態 or 人化 tag）。
- **H1 插件化實作完成（cursor）＋Hermes 親核**：Tasks 0–5＋文檔（`hud/apps_registry.js`／`hud/apps/hw-ring/*`／`main.js`／`preload.js`／`settings*.html/js`／`renderer/index.html` 只加 root）。靜態：`node --check` 全綠、11/11 單元測試（3 條新：carousel／free 避位＋負控）、`apps_layout_overlap_check.js` 綠。**真 dev instance＋CDP**（port 9233；9222 被 Hermes Chrome 佔）：API 白名單 7 個 ✓、`#jarvis-apps-root` ✓、**hw-ring 卡真出**（`◎ LOAD9%CPU 9%GPU 6%RAM 37%NET 73↓ 2↑`）✓、`sensors()` 對得上 nvidia-smi（8%／3845MB／41°C vs 7%／3927MiB／41°C）✓。首輪揭**新卡 × `.stats` 重疊** → 已修（`occupied` 避位）＋GUI 覆核 **0 重疊（只剩原有 `weather×greeting`）**。**未做**：Task 6 換版（bump／`npm run dist`／swap exe／`.lnk`）＝等 SK 批。
- **promo M0 ＝ PASS（方法選定）**：裸 `ddagrab` 唔得（`Impossible to convert` d3d11→yuv420p）⇒ **`ddagrab_dl`＝`ddagrab`＋`-vf hwdownload,format=bgra`** 成功（2560×1440@60）；`gdigrab` 必須 `-offset_x 0 -offset_y 0 -video_size 2560x1440`（否則錄 3640×1920 全虛擬桌面）。**坑**：硬 terminate ffmpeg → mp4 `moov atom not found` 壞檔；要 stdin 送 `q` 禮貌收工（+`-movflags +faststart`）。
- **promo ATM8 原片已錄**：`%TEMP%\promo_footage_20261009-034259\promo_raw_*.mp4`（2560×1440、62fps 級、6,223 frames、**105.2s**）＋3 條 case OK（shot2 面板問題 cards 2／shot3 單件 diamond cards 5／shot5 世界生成 cards 4）＋`PROMO_NOTES-draft.md`（分鏡→相對時間碼）；WM_CLOSE 關 game、cases 清走。**未做**：shot 1／6（JEI 捲動／設定畫面＝要 GUI 驅動）＋剪輯（overlay／旁白／SRT／音樂／封面）→ 另 session。
- **HEI crash 線收線**：SK 自己換 `HadEnoughItems_1.12.2-4.35.1.jar`；Hermes 核實 sha256 開頭 `8777b115592519ea`＝**官方原檔**、舊 4.35.0 冇殘留、`javap` 見到 `init(...)` 返嚟 ✓；SK 遊戲內 checked OK。給 MayaCraft AI 嘅短訊息已寫好：`Documents\PC_Troubleshoot\dj2-optimization\交MayaCraft-AI-HEI-更新訊息-20261009.md`（等 SK 發）。
- **未 commit（等 SK go）**：packai code（raw-id fix＋M1）＋`docs/research/artifacts/2026-10-09-*`＋jarvis-pc H1 code。HANDOFF／DJ2 筆記已更新並 commit。
- **JARVIS ONE 0.4.15 → 0.4.16 已上線（2026-10-09 04:53，SK 05:0x 講「3 now」）**：bump＋`npm run dist`（cursor，commit `4951b41`）→ 官方 `swap_hud_version.ps1 -Version 0.4.16`（hidden）：殺 5 進程 → 開新版 → `8765 /health` 200 `{"ok":true}`、`8642/8765/8770/8771` LISTEN、3 個 `JARVIS ONE.lnk` 已指 0.4.16、零可見 console、無 0.4.15 殘留。exe sha256 `29d1be4e7ba87a23213d9155b442041922280a537940a181059a3d4b2dc33154`（72,586,165 B）。
- **⚠️ 換版途中撳到嘅坑（已修＋已寫入 skill）**：0.4.16 首次打包 `hud/package.json` 嘅 `build.files` **漏咗 `apps_registry.js`＋`apps/**`** → `@electron/asar listPackage` 查到 asar 內 0 命中（打包版會冇 H1 功能／甚至 require 失敗）→ 派 cursor 補清單＋重建，Hermes 重驗 asar 見到 `\apps_registry.js`＋`\apps\hw-ring\app.js` 才換版。
- **打包版自我證據（唔使截圖）**：`%APPDATA%\Jarvis\apps_registry.log` 04:53:08 寫住 `[apps] dir=C:\…\Temp\<hash>\resources\app.asar\apps count=1 mode=carousel occupied=7` ＋ `[apps] overlap resolve hw-ring (40,1240) -> (434,1080)` ⇒ 插件載入＋避位修正**喺打包版真跑住**；`hud_error.log`／`app_error.log` 換版後無新錯誤。
- **promo 粗剪**（SK 04:5x「4 go」）：`docs/promo/roughcut-20261009/promo_roughcut_27s.mp4`（1920×1080、27.2s、字幕已燒）＋`roughcut.srt`＋5 張 still＋`PROMO_NOTES.md`（分鏡時間碼＋已知限制：視窗模式錄、shot3 問題含 `minecraft:diamond`、未做旁白／音樂／D2／D7）。
- **SK 決定（10-09）**：raw item tag id（`forge:ingots/steel` 類）＝**ignore**，唔開 plan、唔擴網；commit 兩 repo ✅；H1 換版 ✅ now；promo 粗剪 ✅ go。
- **SK 報完成（10-09 中午，據 SK 口報、Hermes 未親驗）**：① MayaCraft AI HEI 更新訊息 **SK 已發** ② SK 已眼睇 DJ2 客戶端三項（字體／GUI／光影）＋ HUD 0.4.16 `hw-ring` 新卡 ⇒ 兩項收工。
- **測試＋push 兩 repo（10-09 13:5x，SK「1 test it, then push」）**：packai＝compile OK＋**60/60 Java harness**＋Python 125 檔 **1 紅（已知 `check_ask_display_leak.py`＝要真機 log）**；jarvis-pc＝`node --check` OK＋hud 2 個 check PASS＋**pytest 564 passed**＋`eval_gate --lock` 一致＋`--all` 三 suite 綠（HASH `9307fc48192e0e8b` 冇 drift）。secrets 掃描 2 repo 乾淨（唯一命中＝evidence 檔名 `ask-*` 假陽性）。push 成功並已 fetch 覆核：jarvis-pc `165a149..2c939d3`、packai `345836c..edffe69`，兩邊 `main...origin/main` 同步。
- **promo 方向改動（10-09 下午，SK「go」）**：**取消旁白**——查實 Create 官方 trailer（「This is Create. (2022)」）係**純音樂＋文字、零旁白**；再吸收 SK 貼嘅 B 站參考（BV16Lam6JEgV「我合并了1万个mc模组和插件加载器」，實測**118.5 s 只有 13 個硬切**＝靠 motion graphics 唔係快剪）→ 新版面＝深色底＋中間圓角窗框放真機畫面＋底部獨立大字卡（唔遮 UI）＋標題卡／logo 結尾卡＋進度條。產出 **`docs/promo/mg-20261009/promo_mg_27s.mp4`**（1920×1080、27.23 s、H.264＋AAC、配樂＝**CC0 莫扎特《費加洛》序曲**；`LICENSES.md` 已記出處）。工具＝`%TEMP%\mg_promo_v2.py`（PIL 逐格合成）＋`build_mg_promo.sh`；底片用**無字幕** `_base.mp4`（唔用有舊中文燒字嘅 roughcut）。
- **promo 新增內容要求（SK）**：加 **KubeJS** 內容——我們個 mod 讀得到 KubeJS 改過嘅物品／配方（ATM8 沙盒確有 `kubejs-forge-1902.6.2`＋server scripts；harness `AskKubeJsBridgeCheck`；prompt 有 `// file: kubejs` 規則）→ 要補拍一段 demo（**等 SK 收機**，連 shot 1／6）。
- 小坑：沙盒 `logs` 還原在 game 剛退出時會 `FileExistsError`（trace 還原 OK、證據已 collect 走）＝skill 已記錄之 Windows 檔鎖問題。
## 2026-10-08 深夜（Discord；packai raw-id 修復：cursor 實作完成、Hermes 真機 body 親核揭真漏）
- **SK 20:19 派工（cursor-agent 實作 plan v3.1）**：改 3 檔＝`ReplyLang.idToLabel`＋`structureObtainLabel` 改 delegate／`AskReplyScrub` shape-first 人化＋post-humanisation 丟行網／新增 `RawIdScrubFixtureCheck`；`tmp-check.gradle` 由 `research/gen_tmp_check.py` 重生（無手改）。**未 commit、未部署**。回報 `%TEMP%\cursor_packai_rawid_report.md`。
- **Hermes 親核（全部自己跑，唔靠 cursor 自報）**：`compileJava compileTestJava` RC=0；7 個 harness 全綠（含新 `RawIdScrubFixtureCheck`；`-ea` 已開＝assert 真會生效）；`tests/check_*.py` **125 檔 1 紅**＝`check_ask_display_leak.py` RC=2「NO LOG LINES」（要真機 log，同本 diff 無關）。另寫離線 harness（Temp，唔入 repo）餵**真機 10-07 錄落 27 條 body**：已識別 id 全部人化正確、輸出同「只換 id」逐字元一致、model-facing 負控（`Plainify.lootLine`）照留 raw。
- **⚠️ 揭到真漏（實機證據）**：真機 body 有 `掉落表：archaeology/desert_pyramid`，而 scanner 白名單（chests|gameplay|entities|inject|structures|spawners|blocks）冇 `archaeology` ⇒ **該行照樣漏 raw id**；A1「用同一支 scanner 掃＝0」會**假過**（scanner 同網一齊盲）。實測兩包 loot_tables 首段共 **48 個目錄、42 個唔喺白名單**（`actions`／`dispensers`／`trapped_chests`／`shulker_boxes`／`loot_bags`…）。正常部分：`transmutation_table_rare`→「transmutation table rare」、`bathhouse_normal`→「bathhouse normal」。
- **未做（plan 要求、cursor 指令冇寫）**：F1 碰撞消歧（leaf 撞名加 `<parent>`）＋A7 碰撞清單；scanner 冇帶 plan §F3 講嘅 U 形態 pattern。A1／A2／A5 真機驗收要部署 jar＋開遊戲（等 SK）。
- **等 SK 揀修法**：① 補白名單到 census 全集（細 diff，但 `top/`／`box/`／`misc/` 等通用字有誤傷風險）② **玩家側 source-first**＝喺 `AskEngine:1727`／`PackIndex:1318` 出「掉落表：」時就地人化（任何前綴都覆蓋、零 regex 誤傷；model-facing `AcquireAskTool:112` 照留 raw），regex 只做副網 ③ 其他。
- **SK 揀 ② → v4 已實作（cursor-agent 00:08–00:10）**：新增 `Plainify.playerLootLine`（`blocks/` 照 delegate 去 `lootLine`；其餘 `ReplyLang.lootTableObtain(idToLabel(table))`）＋`AskEngine:1727` 改叫佢＋新 `PlayerLootLineCheck`（5 assert）。規格寫入 packai `docs/plans/2026-10-08-gap-panel-raw-id-leak-fix.md` §7 v4。**未 commit、未部署**。
- **Hermes 親核（v4）**：compile RC=0；7 個 harness 綠（含新 check）；python 125 檔 1 紅（已知）。另由**真機 141 條 trace 抽出嘅 20 個真 raw table id** 逐個跑新 function ⇒ **20/20 人化正確、零路徑殘留**（`archaeology/desert_pyramid`→「desert pyramid」、`chests/village/moon/blacksmith`→「blacksmith」、`twilightforest:structures/well`→「well」、`blocks/ritual_brazier`→blocks 原句）；model-facing `lootLine` 負控全部照留 raw。
- **仍已知未覆蓋（明寫）**：模型自己回聲未入白名單嘅前綴（例 `actions/…`）→ regex 網照唔到（plan v4 已記）；A7 碰撞消歧未做（真機 20 個 id 內冇真正撞名）。**下一步＝部署 jar 開遊戲做 A1／A2 真機驗收（要 SK），過咗才 commit code**。

- **M1「面板問答驅動層」實作完成（cursor 01:0x–01:13）＋Hermes 親核**：只改 2 檔＝`AiAssistantScreen.openAndAskQuestion(String)`（dev-only：開面板→預填 `draftInput`→`sendCurrent()`，走同一 ask 路徑；唯一呼叫者 `AutoTestHarness:415`）、`AutoTestHarness`（CaseSpec/parse 加 `question`；`startCase` question 分支唔行 sample；Judge 對 question case 唔再用 item 配對）。**Hermes 自己跑**：`compileJava compileTestJava` RC=0；**全套 60/60 harness 綠**（`--rerun-tasks`，1m2s）；`tests/check_*.py` 125 檔 1 紅（`check_ask_display_leak.py`＝要真機 log，已知 baseline）。jar 已建：`forge/1.19.2/build/libs/autotest-dev-0.2.3.jar`（1,297,942 B、`sha256 140b9c0cab35cd32f320ea07…`）——bytecode 親核含 raw-id fix（`playerLootLine`／`idToLabel`／`humanizeRawIdShapes`）＋M1（`openAndAskQuestion`／`question`）。**未部署、未 commit。**
- **DJ2 crash 查清（SK 要「詳細查」）**：2026-10-09 01:06:27／01:07:57／01:08:09 同一 session 三連發；`NoSuchMethodError mezz.jei...RecipeTransferButton.init(Container, EntityPlayer)` ← `appeng...JEIMissingItem.showError`。根因（javap 打真 jar 核實）：本機 `HadEnoughItems_1.12.2-4.35.0.jar` **只有 `update(...)`、冇 `init(...)`**（4.35.0 commit `c24a85db8` 改名）；`ae2-uel-v0.56.4` 仍呼叫 `init` ⇒ 一 hover AE2 終端「＋」轉移掣即爆。**官方 HEI 4.35.1（2026-10-07）已 revert → `init` 返嚟**（下載 asset 987,667 B、`sha256 8777b115592519ea0b077032…`、javap 親核）；上游 `CleanroomMC/HadEnoughItems#259`（09-25 開／10-01 關）＋`Krutoy242/Enigmatica2Expert-Extended#670`（降 4.34.3 有效）。報告 `Documents\PC_Troubleshoot\dj2-optimization\crash-2026-10-09-AE2-HEI-4.35.0.md`；`DJ2-筆記.md` §0／§5.1／§6／§7 已更新。**未改任何 mod 檔**（等 SK 揀 ① 換 4.35.1／② 降 4.34.3／③ 唔改／④ 通知 pack 作者）。
- **Blocker（等 SK）**：DJ2 崩咗但 **javaw PID 43308（11.85 GB）仲未死**（另 2 個 Prism javaw）⇒ 兩個部署（`packai_sandbox` 4-case、`packai_sandbox_atm8` 拍片）都 REFUSED。SK 揀 a（自己閂）／b（准我 kill，只殺 DJ2 instance）。
- ⚠️ **Temp 檔名撞（Hermes 記）**：派工檔名重用咗 09-14 遺留嘅 `cursor_packai_m1_*` ⇒ 誤覆蓋舊 `m1_instructions.md`／`m1_dispatch.ps1`／`m1_report.md`（全部係 `%TEMP%` scratch，內容喺 session 記錄）；之後一律用 `cursor_packai_promoM1_*` 命名。
## 2026-10-08 晚上（Discord；PR #13 merge 入 main、packai 開工閘真機跑、Modrinth slug 定案）
- **PR #13 收尾（SK「go」）**：cursor-agent 修 review 兩條 warning → 我親驗：full pytest **564 passed**、`eval_gate --lock` 一致（55 檔）、`eval_gate --all` 三 suite 全綠、**負控**（只 revert 兩個 production 檔）新測試必紅（`'OFF'.startswith`）→ 還原即 11/11 綠；commit `2952f6d` push → PR **由 Cursor Approval Agent 自動 merge（`aaa9917`，19:09 HKT）**；覆核：`git merge-base --is-ancestor 2952f6d origin/main` ✅、main 上 `settings_ui.py` 0 個舊常數、watchdog 有 `ProcessEnumError`。
- **部署副本同步**：`hermes\scripts\jarvis_sidecar_health.py` 由 `origin/main` 版本覆蓋（backup `backups/jarvis_sidecar_health.py.bak-20261008-191017`）；跑一次輸出 `OK wake_on=False`＝同 cron monitor 存住嘅 hash 一樣 ⇒ 冇假警報。
- **packai 開工閘真機跑（A9 首次真驗收）**：`packai_sandbox`（現行 10-07 jar）4/4 OK／`cardsOut=5`／body 471–691 字／+159,995 tokens；`packai_sandbox_atm8`（09-20 jar）4/4 OK／`cardsOut=6–8`／body 1049–2225 字／+176,346 tokens；兩邊負控 `NO_SAMPLE`、自家 mod 例外 0。**澄清**：`/ai` 打 chat 唔出卡，出卡要行 AI 面板（＝plan 嘅 M1 薄驅動層）。詳見 packai `docs/promo/PROMO_PLAN-v4-2026-10-08.md` §12。
- **揾到真缺陷（未修）**：gap 面板（「資料有、答案未提」）印 raw id（`chests/…`、`gameplay/…`、`crafting_shaped -> "…"`）→ NFWC 3/4、ATM8 2/4 條中招；等 SK 決定。
- **Modrinth slug**：SK「use ur suggest」→ `pack-ai-assistant`；Modrinth API 實查 HTTP 404（未佔用）；已寫入 plan 4 處＋§11 核實表（commit `ac60a0a`，已 push）。
- **窗口（老實記錄）**：NFWC run 用標題認窗失敗 → 遊戲窗留喺主螢幕約 2 分鐘；ATM8 run 改 **PID 認窗**成功搬副螢幕（`on_target_monitor=true`、`foreground_is_mc=false`）。SK 嘅 DJ2 全程冇被碰（javaw 由 4 返 3、冇 kill 過任何非自己嘅進程）。

## 2026-10-08 下午（Discord；promo plan v4 通過 8:2、NVIDIA 三值核完（唔裝 NPI）、CS2 線收線、packai 版控）

- **promo 宣傳片線收口**：R2＝4:6 → 修 5 條 flip condition（FC1–FC5）→ **R3＝正方 8 : 反方 2 → 達標**（3:7→4:6→8:2，未到停手線）。新檔：`docs/promo/PROMO_PLAN-v4-2026-10-08.md`（26,475 B）＋`docs/plans/reviews/2026-10-08_promo-plan-v{3,4}-round{2,3}.md`；commit `b8608ea`（已 push）。Hermes 親核：R3 引用嘅 sha256 同 v4 一致、ATM8 沙盒 380 jar、`New World (1)`＝19,273,115 B（v3 寫 1.2 MB 係錯）、`docs/PUBLISH.md` CF id 1643097。**未做**：拍片（要 SK 開機）＋開工閘嗰次 2 分鐘 `/ai` 真實測（A9 首條真 trace）。
- **NVIDIA 三值（CS2 profile）已核**：Hermes 背景方式開 NVIDIA App（no-activate；`focus_stolen=true` 但已還原、開前開後前景都係 Discord；完事已閂 App）→ 圖形→程式設定→絕對武力 2 → 讀值：**低延遲模式＝全域-關閉**、**電源管理模式＝全域-慣用的最大效能**、**畫面播放速率上限＝全域-關閉** ⇒ 三個都係建議值 → **唔需要改、NVIDIA Profile Inspector 唔裝**（全唯讀，冇改任何設定）。記錄：`Documents\PC_Troubleshoot\cs2-perf\NVIDIA-SETTINGS-2026-10-08.md`。
- **CS2 線收線（SK 10-08 指示）**：① 動態陰影 A/B **取消**（SK：動態陰影必須「全部」，否則見唔到其他玩家影子）② 「純 CS2 一段（閂 MC）」**唔做**（SK：暫無卡頓）③ 閘 2 **ignore for now**。已寫入 `PLAN-v2.1-2026-10-03.md`（「❌ 已排除」段）。watchdog cron 照留。
- **packai 其他版控**：`AGENTS.md` 守門句加註「`mc-mod-jar-guard` 自 2026-09-15 20:25 paused（SK 09-27 決定維持）」＋`.gitignore` 加 `docs/research/artifacts/_*`（13 個 scratch 檔唔再阻 status）→ commit `355fe25`（已 push）。
- **正合個案（side task）**：Chrome 重開後**補讀到 OfferToday 頁內全文**（之前只讀到摘要）→ 正合有**平台認證**（BRN 70580929）、自己都用短名招聘；佢自己嘅招聘聯絡人＝**陳小姐／Samson Tang（行政人事部部長）**、職位喺旺角 → 同「保捷＋梅先生＋油塘」睇唔到連繫。報告已更新：`Documents\job-check\2026-10-08-正合建築工程-深入核查.md`。
- **等 SK**：① Modrinth 要唔要**新開專案頁**（SK 10-08：「mod c」＝CurseForge＋Modrinth 兩個都要）② packai 拍片／`/ai` 實測要開機配合 ③ 13 個 `_*` scratch 檔已按 SK 指示入 `.gitignore`（如想改入 git 講一聲）。


## 今日完成（2026-10-08）
- jarvis-pc 當日 commit 1 個（最新：9c9e7b3 docs(handoff): 10-08 凌晨 — 朋友求職個案風險調查、CS2 閘 0 baseline（含 Minecr）
- 未 commit 檔案 2 個：uv.lock, .hermes/plans/2026-10-04_agent-vm-
- 領先 remote 4 個 commit（未 push）

## 2026-10-07 深夜 → 10-08 凌晨（Discord；朋友求職個案風險調查、CS2 閘 0 baseline＋設定審計、promo plan v3）
- **朋友求職個案（第三方）風險調查**：3 份檔存本機 `Documents\job-check\`（風險評估／查詢稿／新片分析）。**本檔唔寫公司名同行內細節**（本 repo＝public）。
- **新片＝CS2 6:12＋語音對話（關於見工）**，非遊戲片；ASR 重點：兩位朋友分開見、冇交個人資料、冇簽任何文件 → `job-check\2026-10-07-新片分析-CS2對話.md`。
- **CS2 閘 0 完成（FrameView 4 次 capture，共 ~70 分鐘）**：主 baseline（62.7 分鐘、2,055,058 frames）＝**中位 650 FPS／平均 583／1% low 235／GPU 81%／CPU 15%（最忙 thread 67%，冇飽和）**；遊戲中 <60 FPS 只 0.03% → 判斷＝**GPU 樽頸但未頂**。**⚠️ 全部錄影期間 Minecraft（javaw.exe）同開** → 數字係全機數，要純 CS2 基準就要另錄一段唔開 Minecraft。報告（正本）`Documents\PC_Troubleshoot\cs2-perf\BASELINE-2026-10-07-frameview.md`＋cron 自動報告 `gate0-2026-10-07-2355.md`／`gate0-2026-10-08-0136.md`（數字一致）。
- **⚠️ 教訓（已入報告）**：`cs2_video.txt` 唔等於 live 值（09-27 舊檔寫 MSAA 4×，實際 SK 遊戲內已關）→ 要 SK 截圖／遊戲退出後才核。
- **CS2 設定審計（唯讀）**：MSAA 已關、Steam overlay 已關（SK 確認）；剩低大項＝**動態陰影「全部」**；Windows 側＝HAGS 開／GameDVR 關／MPO 停用／電源高效能／cs2 GPU 偏好高效能／VBS 未見啟用。
- **NVIDIA 驅動 per-app 3D 設定未核**：存於 `nvdrsdb0.bin`（binary）→ 要 NVIDIA Profile Inspector（未裝，待 SK 批）。
- **promo 宣傳片**：計畫 v3 已寫（Round 1 review 比分 3:7 → 已逐條修正：背景 pack 世代、錄影工具、觀眾語言、驗收定義）；`super_minecraft_AI_player\docs\promo\PROMO_PLAN-v3-2026-10-07.md`；**Round 2 review 未跑**。

## 2026-10-07 16:4x（Discord；主線待辦重整 ＋ Unlight side quest 研究存檔）
- **SK 決定**：TRCC「開 game 自動關」＝**唔做**；DJ2 Litematica 掉幀＝**唔追**（SK 遇到先講）。
- **主線待辦**（等 SK 揀）：② PR #13 review＋merge ⑤ cursor 凍線診斷；① CS2 閘 0 等 SK 今晚開 game；③ CS2 調優等閘 0 數據；④ HoloMat 等 SK 答 3 條；⑦ #9／#5 等新 mic。
- **② PR #13 code review 完成**（Hermes 親做）：verdict＝**Request changes**（2 warning：W1 `settings_ui.py` 仍用舊 `SETTINGS_PATH`／`SETTINGS_DIR` 常數 → UI 會指錯目錄；W2 `tools/jarvis_sidecar_health.py` 將「列進程失敗」當 `OFF` → 靜靜蓋住真故障）＋4 suggestion；證據＝live `/health` payload 實測吻合、新測試 19 passed、改動測試 74 passed（1 紅＝環境缺 numpy，main 同樣紅）；報告 `.hermes\plans\2026-10-07_pr13-code-review.md`。**未貼上 GitHub、未改 code**（等 SK）。
- **side quest（Unlight:Revive 自動化）已完成研究、存檔、暫停**：`Documents\side-quest-money\research\2026-10-07-unlight-revive-{automation,feasibility}.md`（SK：「ignore it, back to main quest」；決定性證據＝MIT 工具 `UnlightPlugin/ulr-companion` 用 CDP 連 Steam 客戶端；遊戲＝Phaser 3.87；開 debug port `--remote-debugging-port=59222`）。

## 2026-10-07 16:15（Discord；求職線：兩通教練電話逐字稿＋離職證明 email＋HR 講稿）
- **兩條片＝兩通教練電話**（唔係遊戲片）：`Videos\2026-10-07 10-52-53.mp4`（67 分）＋`2026-10-07 13-09-01.mp4`（64 分）→ 4 個檔：`MS_DCT_Prep\records\教練通話-20261007-1052-{逐字稿,重點摘要}.md`、`教練通話2-20261007-1309-{逐字稿,重點摘要}.md`（SenseVoice 30s chunk＋whisper 窗口交叉核對；人工數目 ASR 兩個引擎都聽錯，SK 親耳定案＝HK$29,000）。
- **離職證明 email 定稿**（寄 Primetech HR Miracle Lau，Cc Dan Pun）：`MS_DCT_Prep\records\離職證明-索取email-20261007.md`；含逐項核對表（在職期 2025-10-02→2026-04-08、Fujitsu Staff no. C88323），全部對真 Gmail＋duty report PDF（PDF 存 `records\入職文件\`）。
- **HR 電話講稿**：`MS_DCT_Prep\records\HR電話講稿-20261007.txt`（人工 29k 英文原句、保密講法、文件清單、掛線後 3 件事）。
- **工具 bug 已修**：skill `local-recording-transcription` 嘅 `whisper_windows.py` 寫死 STEM／WINDOWS（會靜靜跑錯錄音）→ 改成食 `WS_STEM`／`WS_WINDOWS` 環境變數。
- **HANDOFF 只留 pointer**（求職內幕／人事細節一律唔入本檔）。

## 2026-10-07 12:0x（Discord；push 兩 repo、packai Slice 1b 真機驗收通過、CS2 閘 0 watcher）
- **push（SK 一句「go」）**：jarvis-pc `feature/hermes-alerts-mcp` 6 個 commit → origin（`cdb5a1f..fcfb49b`）；packai `main` `013e4ac..815c5cb`。push 前掃 secrets：兩邊 `git diff/show` grep（`sk-…`／`api_key`／`bearer`／`password`／`dpapi:`）＝0 hit。PR #13 已含該 6 個 commit（merge 延後，SK：「future」）。
- **packai Slice 1b 真機 A/B（Hermes 親跑）**：靜態重跑 compile RC=0、harness **58/58**、python 125 檔 1 紅（已知 baseline）、`AskReplyScrub.java` sha 同 09-22 記錄一致；flagged jar `autotest-dev-0.2.3.jar`（sha256 `04eadb7d…f4577`，`javap -c` 證 `proseOrFacts` 真 call `rewriteInternalJargon`）部署沙盒 → harness 3 case（amethyst 17.7s／diamond 17.1s OK、bedrock NO_SAMPLE）＋真 LLM billed 48001＋68481。**生效證據**：`ask-20261007-114346` raw 尾行「脚本索引」vs 玩家 body「脚本资料」；該輪 body 0 jargon、卡 7/7。證據存 `super_minecraft_AI_player\docs\research\artifacts\2026-10-07-slice1b-realmachine\`。
- **捉到坑**：沙盒 `mods/` 同時有 09-19 舊 flagged jar（`autotest-dev-0.2.3.jar`，無新 pass）→ 頭兩輪真機其實跑舊 code（body 冇改寫）。用 `javap` 排除「冇接線」後追到雙 jar；舊 jar 移去 `%TEMP%\packai_stale_jar_20261007\`，並寫入 skill `minecraft-mod-in-game-autotest` §16。
- **CS2 閘 0 watcher**：新 cron `cs2-perf-gate0-watch`（`3f322ccff9a3`，*/5，monitor `hermes\scripts\cs2_watch.py`，deliver origin，continuity）——SK 開 CS2 → 一句提醒；收 game 有新 FrameView CSV → 自動分析＋寫 `PC_Troubleshoot\cs2-perf\gate0-*.md`；其他狀態靜默。
- 沙盒 game 已關（javaw 清零，零搶焦點）；HANDOFF 未解清單重整。

## 今日完成（2026-10-07）
- jarvis-pc 當日 commit 6 個（最新：fcfb49b docs(handoff): 2026-10-07 續 — Litematica 掉幀診斷、GC 排除、Tinkers' A）
- 未 commit 檔案 2 個：uv.lock, .hermes/plans/2026-10-04_agent-vm-
- 領先 remote 6 個 commit（未 push）

## 今日完成（2026-10-07 凌晨；接 10-06 session）

- 【#4 Slice B log 輪替】build 0.4.15 完成（BUILD_RC=0、asar 實證有 appendActivityLog、sha256 head a9a3d447…）；舊 100MB log 備份 `backups/jarvis_hud_activity.log.bak-20261007-003020`；**未換版，等 SK**。
- 【cron 清理】刪走重複 Hermes cron `game-vcache-pin`（唔 elevated、priv_err 1300）；真正做嘢＝Windows 排程 `\JARVIS-GameVCachePin`（已核實執行中，javaw×3 pinned 0xffff）。
- 【#11】`detect_sustained_high()` 新增；修死碼：`--days` 預設 7→30（`_CLI_DEFAULT_DAYS`）＋抽 `_build_parser()`＋guard test；pytest **561 passed/0 failed**；真 artifact `days_analyzed=30`；`--fingerprint` → NONE。
- 【#11 pass-2 修完】span 連續性（baseline+recent 全 span 要連續，防斷日後用陳年 baseline）＋抽 `sustained_high_details()` 去重；負控 RED→GREEN；pytest **562 passed/0 failed**。
- 【#12】HoloMat HUD 插件化計畫：`.hermes/plans/2026-10-07_0045-hud-app-plugins-holomat-h1.md`（6 task＋3 個待 SK 決定問題）。
- 【踩到】18:00 提醒 job 冇發到（scheduler 遲過 120s grace → 被移除）；`web_search` backend（keyless Exa）掛。

### DJ2 / Minecraft（10-07 03:00–04:52，Hermes 親核）
- 【FPS 郁動掉幀＝Litematica】你 01:45 裝 litematica、02:15 載入 `1.12 Huge Sci-fi Base - Alternative 2.litematic`、02:20:30 log `Creating 24 render threads`；config `render_range.mode="ALL"`（渲染全層）。→ 下一步：遊戲內 **M,R** 關渲染驗證（未做）。
- 【已排除 GC（實測）】`jstat`：338 次 young GC 總 10.568 s ÷ 玩咗 95 min = **0.19%**；heap 8G/G1GC（relauncher.json `-Xmx8G -Xms8G`，無指定 GC）。
- 【Tinkers' Addons／Mending Moss 機制（jar bytecode 實證）】Amelioration 冷卻 = 地獄 10000、露天日光 12500、其他 15000（+0–998 ms 隨機），每次修「等級」點、上限 L5；Mending Moss `DELAY=150 ticks`、每 1 XP 修 `2+等級`、上限 L10、**爆咗唔修**、只吸 mainhand/offhand 嘅 XP。Tome recipe = 3× `tconstruct:materials` **meta 19（＝Mending Moss）**＋書（meta 18 才係苔蘚球，已更正）。
## 今日完成（2026-10-06）
- jarvis-pc 當日 commit 3 個（最新：34109fe docs(handoff): STATE git line without churning sha）
- 未 commit 檔案 2 個：uv.lock, .hermes/plans/2026-10-04_agent-vm-
- 領先 remote 6 個 commit（未 push）
- 【#1 測試隔離 ii 完成】隔離實錘：真 settings.json／voice_status.json mtime 零變、state.db 767→767；pytest 550 passed/0 failed；eval_gate --all 綠 HASH 9307fc48192e0e8b；未 commit（等 SK）
- 【#1 脆弱位已修（SK：即刻修）】F1 settings cache 加 path key（負控實證：暫時還原 F1 → F3 test 即紅 `assert 0.31 == 0.42`；還原後綠）／F2 conftest 每 test 重設 pristine settings／F3 新增負控 test；全量 pytest 551 passed/0 failed、eval_gate --all 綠 HASH 9307fc48192e0e8b。

## 2026-10-06 01:45–02:15（Discord；DJ2 heap 疑雲查清＋pack 配方普查；SK 叫停 hand off）
- SK 貼 MC F3（`Mem 82% 6744/8192MB`／`Allocated 100% 8192MB`／`Off-Heap +606MB`）＋工作管理員（Zulu PID 44660＝10,456MB）問「what???」。
- 親核（jcmd PID 44660）：`UseG1GC`、Max/MinHeapSize 8G、committed 8G、used ≈6.8G（87%）；process WS 10.26GB、peak 24.29GB、code cache 68MB、119 threads → **兩個數字都真**：F3＝Java heap 上限；工作管理員＝成個進程實體記憶體（唔係漏記憶體）。
- 發現：Prism `MaxMemAlloc=12288` 只到 wrapper，真 heap 由 Cleanroom `relauncher.json` `args` 決定＝**8G**（同 memory 舊條目一致，但呢次係第一次量到真值）。
- 普查（SK「use on pack AI」→ 我讀成做 10-05 嗰兩件：①靜態配方普查 ②SOP 收 skill）：**①做完**（數字見 STATE）；**②未開**。全程只讀檔（無開 GUI／無改 config／無 commit）。
- 中途自我更正一次：v1 把 `advancements/recipes/**` 當配方 → 收緊規則重跑＋bsdtar 交叉核對。
- SK 叫 **stop → hand off**；意圖未確認（記入 STATE 未解 ⑯）。


## 今日完成（2026-10-05）
- jarvis-pc 當日 commit 3 個（最新：6391b00 docs(handoff): X3D isolation verified end-to-end (auto-restore）
- 未 commit 檔案 2 個：uv.lock, .hermes/plans/2026-10-04_agent-vm-
- 領先 remote 3 個 commit（未 push）

## 2026-10-05 03:05–03:30（Discord；handoff 收尾核實）
- 自動還原**實測有效**：MC 關閉後下一個 tick 將 51 個被隔離進程逐個還原 32 LPI（log 有 `RESTORE ... -> all 32 LPIs`；state `games_running=False, isolated=0, pinned=0`）。
- 最高權限 loop 健在：heartbeat 03:21:29、`elevated=true`、`debug_priv=True priv_err=0`、`games=False iso=0 changed=0 skip=[]`；task `JARVIS-GameVCachePin` 存在（`schtasks /query` 已核）。
- 隔離名單（遊戲運行時實測）＝51 個：Chrome 26／steamwebhelper 8／Wallpaper Engine 7／Discord 6／SteelSeries 3／Steam 1；dwm／audio／Defender／svchost／python 硬性排除。
- TRCC.exe 最終結論：**綁唔到**（另加 `p.info['name']` 讀唔到嘅 fallback 後再試仍無效）→ 唔再花時間，改為建議 SK 打機時關咗佢。
- 未做：① SK 用 FrameView 錄「隔離前後」對 1% low ② heap 12G→18G（方案 A，等 SK 話）③ 「開 game 自動關 TRCC」小工具（等 SK 話）。

## 2026-10-05 02:30–03:05（Discord；X3D 隔離＋最高權限 task；TRCC 例外）
- 隔離上線：遊戲 pin CCD0（LPI 0-15）；50–52 個噪音進程（Discord／Chrome／Steam／Wallpaper Engine／SteelSeries）pin CCD1（16-31）；dwm／audio／Defender／svchost／python 硬性唔郁；遊戲全關自動還原。
- 最高權限：`install_game_pin_task.cmd` → scheduled task `JARVIS-GameVCachePin`（同 user、RunLevel Highest、AtLogOn、`pythonw game_vcache_pin.py --loop 10`，heartbeat `state\game_vcache_pin_loop.json`）；undo＝`uninstall_game_pin_task.cmd`；Hermes cron `game-vcache-pin` 保留做 watchdog。
- 坑（已入 skill x3d-vcache-ccd-pinning）：PS `RestartInterval` 會令 task XML 註冊失敗；ctypes `GetCurrentProcess` 要設 restype 否則 OpenProcessToken 回 err 6；SeDebugPrivilege 要明確開。
- **例外**：TRCC.exe（Thermaltake RGB）即使 elevated＋SeDebugPrivilege 都改唔到 affinity（AccessDenied）→ 建議打機時關咗佢（純 RGB 控制）。
- 未做：SK 用 FrameView 對「隔離前後」1% low；heap 12G→18G（方案 A，等 SK 話）。

## 2026-10-05 01:45–02:15（Discord；MC 卡 → 追到 X3D CCD 派工問題，已修＋已自動化）
- 症狀：SK「MC 好卡／fps 由 900+ 跌到 300+」；實測 GPU 只 8–15%（唔關顯卡）→ 遊戲係 CPU 單線程樽頸。
- 量法：Java 48MB pointer-chase ＋ `start /affinity`（低優先權、無 console 窗）→ **V-Cache 96MB CCD = LPI 0-15（17.5 ns/hop）**；32MB CCD = LPI 16-31（91.6 ns，5.2x 慢）。打機時全部嘢（連 game）實測落 LPI 16-31。
- 修法：game process affinity 綁 `0x0000FFFF`（live 綁，唔使重開 game）。FrameView per-frame CSV 實測（02:02–02:09 vs 02:09 之後）：**avg 318→406 fps、1% low 41.6→108.7、0.1% low 10.4→42、最差 frame 1702 ms→152 ms**；同一個 CSV 見到遊戲用量由 `CPUCoreUtil[16-31]` 搬去 `[0-15]`。
- 部署：`hermes\scripts\game_vcache_pin.py` ＋ `hermes\config\game_vcache_pin.json` ＋ cron `game-vcache-pin`（`* * * * *`、`no_agent`、deliver=local；log `hermes\logs\game_vcache_pin.log`）。還原＝config `"enabled": false` 或停 cron `2fd47bb47bd3`。
- 新 skill：`x3d-vcache-ccd-pinning`（量法／修法／坑：VBS 下 CPUID＋GLPIEx 誤報「2×96MB」、PresentMon 非 admin 靜靜 RC=1、FrameView `Documents\FrameView\` CSV 點讀）。
- 未做：SK 體感覆核；CS2 用同一 pin 做 A/B（併入 `cs2-perf` 閘 5）；1% low 仲偏低（下一步查 heap 貼 93%、Defender 咬 1 核、chunk 重建風暴 84 次/session）。

## 2026-10-04 11:35–11:5x（Discord；SK「read hand off + make it auto」→ 新 session 自動讀 handoff 已上線）
- **做咗（SK 揀「both」）**：
  - `%LOCALAPPDATA%\hermes\agent-hooks\session_brief.py`（純 stdlib，0.08–0.31 s）：讀 HANDOFF STATE 區塊＋近 3 日 section 標題＋jarvis-pc／packai git（branch／HEAD／未 push／未 commit 頭 5 個）＋`sk_activity.json`＋DS 時段 → 以 `{"context": ...}` 注入（Hermes 只會 append 去 user message，唔會動 system prompt／cache）。每個 `session_id` 只注入一次（`state\session_brief_seen.json`，原子寫）；log `logs\session_brief.log`（256 KB 自動輪替）；platform 白名單 discord／cli／tui／desktop／telegram（cron、api_server（JARVIS 語音線）唔注入）；有 `parent_session_id`＝子 session 唔注入。
  - `config.yaml` 加 `hooks: pre_llm_call`（timeout 15；**command 要明寫 interpreter**，Windows `Popen` 唔會自動找）＋ allowlist 已批（`shell-hooks-allowlist.json`）；備份 `backups\config.yaml.bak-20261004-114002`。
  - home `AGENTS.md` 加「### 開 session 自動讀（SK 2026-10-04）」（備份 `backups\AGENTS.md.bak-20261004-114426`）。
- **實測（Hermes 親跑）**：`hermes hooks doctor` 全綠（exec／allowlist／mtime／synthetic JSON 0.079 s）；`hermes hooks test pre_llm_call` → exit=0、0.08–0.31 s、parsed wire shape 有 `context`。負控：HANDOFF＋repo 都唔存在 → 照出（`(no repo)`、無 STATE、366 字）✓；state 檔損壞 → 照注入 ✓；無 `session_id`／壞 JSON → `{}` ✓；`platform=cron` → NOOP ✓；第二次同 session → NOOP（dedupe）✓；brief 約 6.7–6.9 KB。
- **實測捉到兩個真 bug（已修）**：① `_run` 用 `.strip()` 食咗 `git status --porcelain` 第一行前導空格 → 第一個檔名被切（`code_change_log.md`→`ode_change_log.md`）→ 改 `.rstrip()`；② Hermes wire shape 只有 `session_id／tool_name／tool_input／cwd／extra` — `platform`／`parent_session_id` 喺 `extra` 內 → 原版會永遠 NOOP，靠 `hermes hooks test` 捉到。
- **生效**：hook 只喺 gateway 啟動時註冊 → 隱藏 helper `agent-hooks\gw_restart_hook.cmd`（＋180 s、restart 後自驗 `gateway status`、失敗 fallback 用 Startup `Hermes_Gateway.vbs` 重開）於 11:48:44 跑；log `logs\gw_restart_run3.log`。
- **坑（新）**：用 write_file 寫 `.cmd` 係 **LF** 行尾 → cmd.exe 會誤讀註釋行（`'m' 不是內部或外部命令`）→ `.cmd` 一律 CRLF＋ASCII。
- jarvis-pc：本次 commit＝docs(HANDOFF) 一個。


## 今日完成（2026-10-04）
- jarvis-pc 當日無新 commit
- 未 commit 檔案 1 個：uv.lock
- 領先 remote 121 個 commit（未 push）
- 修 `douyin_fav_persistent_scan.py`：scan 模式冇 navigate→誤報 LOGIN_REQUIRED；另加 `__main__` teardown 自動清 automation Chrome（實測 671 items、`killed_leftover_chrome:[6]`、之後 0 殘留）。
- Hermes 新 session 自動 brief：gateway 11:48:51 註冊 shell hook、11:49:30 首個 INJECT（4625 字、每 session 一次）；重啟乾淨（`Previous gateway exited cleanly`）。
- Nous Portal OAuth 11:56 重新登入成功（credential 返嚟）；但 `upstage/solar-pro4:free` 免費期結束（HTTP 404）→ 兩個 cron agent（`jarvis-session-handoff`／`jarvis-daily-self-review`）改 `meituan/longcat-2.5-preview:free`（實測 tool call OK）；jobs.json 備份 `backups\cron-jobs.json.bak-20261004-120204`。

## 2026-10-03 20:3x–20:5x（JARVIS Slice 1b ＋ Slice 2 —— 已實作、已實測、已 commit）
- **Slice 1 code commit `2a9e8f6`**（0.4.14 五檔）；**Slice 1b／Slice 2 commit `44211b8`**；cron `jarvis-sidecar-health` 已 resume（20:53 next）。
- **Slice 1b**：新增 module-level 純函數 `shell_app.probe_control_http()` —— 判準改成 HTTP 200 ＋ body `{ok:true, service:'jarvis'}`（唔再單靠 TCP connect）；`_probe_control_http` thread 改用佢；失敗照寫 `hud_error.log`、照樣**唔自動重試**。Test `tests/test_control_http_probe.py`（5 case）。
- **Slice 2**：canonical source `tools/jarvis_sidecar_health.py`（**部署＝copy 去 `%LOCALAPPDATA%\hermes\scripts\jarvis_sidecar_health.py`**；舊檔備份 `.bak-20261003-2048`）。指紋：`OK wake_on=<bool>` ／ `OFF`（HUD＋serve 都冇）／ `DOWN <reason> t=<桶>`（`<5m`/`5-30m`/`30m-2h`/`2-6h`/`>6h`）／ `WARN state_io`；state 檔 `%LOCALAPPDATA%\hermes\state\jarvis_sidecar_health_state.json` 原子寫；stdout 永遠一行。Test `tests/test_sidecar_health_monitor.py`（9 case）。
- **實測（Hermes 親跑 live script）**：UP ×2 同字串且唔留 state ✓｜冒牌 server（`service: not-jarvis` 佔 8765）→ **`DOWN BadPayload t=<5m>`**（⚠️ 上一版會誤報 `OK wake_on=None` —— **Hermes 上輪實測捉到，已修**）✓｜桶跨級 5-30m／30m-2h／2-6h／>6h 全 PASS ✓｜state 損毀 → `WARN state_io` ✓｜零進程（HUD＋serve 都冇）→ `OFF` ✓｜殺 dummy 後 2 秒 8765 回歸、輸出回 `OK wake_on=False` ✓。
- **CI gate**：`eval_gate --lock` 一致（55 test files）、`--all` RC=0（golden＋regression 18＋stress 68 全綠）。
- **未做**：窗口 2 **#8**（bogus python spawn 負控 —— 要搬 `host.json` ＋ 開 dev instance，HUD 會閃，等 SK 唔喺機前）；#11 SK 主觀體驗；Slice B（88 MB `jarvis_hud_activity.log` 輪替）。

## 2026-10-03 19:5x–20:2x（JARVIS Slice 1「窗口 1」驗收 —— 0.4.14 已上線，**通過**）
- **換版（SK 揀窗口 1 = now，佢當時 AFK）**：`hud/package.json` 0.4.13→**0.4.14**；`npm run dist` 經 VBS hidden wrapper（BUILD_RC=0、零閃窗）；`swap_hud_version.ps1 -Version 0.4.14`（SWAP_RC=0）→ 殺 5 個舊進程 → 新 exe 19:59:12 → 8765 `/health` 200 ＋ 8642/8765/8770/8771 LISTENING → **3 個 .lnk 全指 0.4.14**。exe 72,581,418 B、sha256 頭 24 `043cf548f456cc5b4f0b8b53`；**asar 內容核對**：`service === 'jarvis'`／`FROZEN at 8765`／`startSidecarHealthCheck` 齊（＝跑緊新代碼）。
- **窗口 1 結果（全部 Hermes 親跑，48 樣本／12 分鐘）**：① 循環消失——`/health` 48/48 = 200、JARVIS 進程恆 5、`download models from model hub` 恆 310（**零重啟**）、`serve.log` 只 +8 行 ② `alert_voice=false` 仍健康 ③ `alert_voice=true` → kill → **8.7 秒** 8765 起返 ④ `alert_tts=piper`＋voice true → **8.7 秒** ⑤（#6）exit-path kill → **4–6 秒** respawn ⑥（#7）負控：dummy 答 `{"ok":true,"service":"not-jarvis"}` ⇒ **Electron 5 秒內 spawn 新 sidecar**；答正確 payload ⇒ **零 churn**；移除 dummy 後 **67 秒**真 sidecar 接手 ⑦（#10）`GET /settings` 回**解密值**、無 `fallback` ⑧（U1）spawn→LISTEN **4–8.7 秒**。報告：`plans\2026-10-03_slice1-窗口1-驗收報告.md`。
- **未做（唔准當已驗）**：#8 spawn 失敗負控（要搬 `host.json`，屬窗口 2）、#9 monitor 桶化（**Slice 2 未寫**）、#11 SK 主觀體驗、Slice B（88 MB log 輪替）。
- **未 commit**：`hud/main.js`／`hud/settings.html`／`src/jarvis/settings.py`／`src/jarvis/shell_app.py` ＋ `hud/package.json`（0.4.14）——等 SK 批（patch 已存 `backups\jarvis-sidecar-slice1-20261003.patch`）。

## 2026-10-03 19:3x–20:0x（Discord；DJ2 驗收通過 ＋ CS2 三段式 ＋ Slice 1 換版備料）
- **DJ2 冶煉爐防呆驗收通過（Hermes 親核）**：11:36 重開 game → `cleanmix.log` 四個 APPLY（新嘅 `TileHeatingStructureMixin` 11:36:53、`GuiUtilMixin` 12:51:20）；`mods` 只剩 `dj2-fixes-1.1.1.jar`；之後玩到 19:33（8 個鐘）零 crash report（上一個 01:07＝裝之前）；紅字 filter 亦 APPLY 且今日 0 次。SK 講朋友「好似冇再爆」→ 暫唔派 jar。
- **CS2 線（SK 指示消化反方 R1）**：R1 原文由 session DB 抽出存檔 `Documents\PC_Troubleshoot\cs2-perf\REVIEW-R1-反方-2026-09-27.md`（11,293 字，未改寫）；Hermes **自己重算** R1／數字核實方關鍵值全部對得上：`nvlddmkm#153` 30 日 **79**、`Display#4101` **5**（09-11×2／09-24×3）、`Kernel-Power#41` **×1 @09-24 16:58:47**、`CPMINCORES` AC/DC **0x64**、`CPMAXCORES` 0x64／`CPCONCURRENCY` 0x61、GameConfigStore children **115／cs2 = 0**、DXCache **73 檔 279.1MB**（10-03 17:35）。→ 寫 `cs2-perf\PLAN-v2-2026-10-03.md`（六閘：先 baseline→淨化→顯示→注入／AV→driver→CPU pin→BIOS）＋ 派中立裁判 subagent（`deleg_ae9225ef`，背景跑）。
- **JARVIS Slice 1 換版備料（Hermes 靜態自驗）**：`node --check hud/main.js` PASS、`py_compile src/jarvis/*.py` PASS、關鍵函數 39 處仍在、四檔 diff **86+/23−**；patch 存 `%LOCALAPPDATA%\hermes\backups\jarvis-sidecar-slice1-20261003.patch`（8,586 B）；rollback exe `JARVIS-ONE-0.4.13.exe` 保留；RUNBOOK `.hermes\plans\2026-10-03_slice1-換版-RUNBOOK.md`（含窗口 1／2 逐項、負控鐵律、還原表）。**等 SK 答：①窗口 1 幾時 ②Q3 常開面接受定加 gate ③Q2 OFF 語意。**

## 今日完成（2026-10-03）
- jarvis-pc 當日 commit 1 個（最新：65f1997 docs(handoff): DJ2 smeltery crash guard shipped (dj2-fixes 1.1）
- 未 commit 檔案 5 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 115 個 commit（未 push）

## 2026-10-03 02:0x–02:4x（Discord；DJ2 冶煉爐 crash（朋友 client）→ 自家防呆 mixin）
- **根因（實錘）**：冶煉爐多格結構失效（SK 意圖在爐內熔自己取資源，死時 TombManyGraves 在爐內生成墓碑）＋有人開住爐 GUI → 客戶端 tile `itemTemperatures` 長度 0、`liquids` null → ①`TileHeatingStructure.java:144` AIOOBE（slot 26）斷線 ②`GuiUtil.java:163` NPE。上游 #4081（Bug/Won't Fix/1.12，只裝 TiCon+Mantle 就重現）。
- **交付 `dj2-fixes-1.1.1.jar`**（10,190B、sha16 `cac074b63861b1ef`）：① `TileHeatingStructureMixin`（slot 越界→cancel **＋即閂 GUI**）② `GuiUtilMixin`（null tank→唔畫）。機械核對（javap 真 jar descriptor ↔ 自家 annotation）PASS；jar 無 stub 洩漏；SRG 名另喺 234 個真 mod jar 交叉命中。
- **部署完成（親核）**：01:55:25 SWAPPED → mods 只剩 `dj2-fixes-1.1.1.jar`，sha256 同 dist 一致（`cac074b63861b1ef…`）；舊 1.0.1 已清；還原＝刪 `dj2-fixes-*.jar`。
- **朋友那邊（`DJ2-Cleanroom-Client-v1.3-shader`，user `admin`）要自己裝同一個 jar（crash 系他部機爆）；jar 在 `Documents\MC_Patches\dj2-fixes\dist\`。
- **待驗**：重開 game 後 `logs\cleanmix.log` 要有兩個新 `APPLY dj2fixes.mixins.json:TileHeatingStructureMixin|GuiUtilMixin`；`dj2fixes-guard.log` 要有 `guard hit`。
- **順帶（未跟進，SK 講 ignore）**：mods 有 `auto_respawn-1.12.2-1.0.jar` → 佢熔自己→死→自動重生連續 80 分鐘，每次死生成墓碑 → 反覆弄散結構；如要根治可調重生點。


## 2026-10-03 00:5x–01:5x（Discord；side task：雨夜便利店街角 3D 微縮模型）
- 交付 `Documents\Code_Project\diorama-konbini-rain\`（雙擊 `index.html` 即開、離線、無 UI）：three.js r128 內嵌；1064 mesh／24,266 tris／76 程序化貼圖；三煇二 toon + 反轉外殼輪廓 + ACES/bloom。
- 內容：便利店（玻璃可見店內：貨架、飲品雪櫃牆、收銀柱、關東煮、雜誌架、ATM）＋街角（販賣機×3、單車×3、電線桿、馬路標線、護欄、小巷、鄰棟、紅綠燈）＋12 種動效（降雨／滴水／水波紋／自動門開合／招牌閃爛／地面倒影）。
- 驗收：headless Chrome `file://` 實跑多角度截圖（`shots/p1–p4`），頁面錯誤面板空＝0 JS error；自動門用 `?t=3` vs `?t=10.5` 兩張對比實証。未 commit（該資料夾不在 git repo）。
- 註（10-03 02:4x 已做）：主檔歸檔 09-24～09-30 段落 → `plans\archive\HANDOFF-2026-09.md`（備份 `hermes\backups\HANDOFF.md.bak-20261003-0245`）。

## 2026-10-02 11:0x–11:3x（Discord；DJ2 Tinkers GUI crash → 自家 client mod 修正，待 SK 重啟驗收）
- **根因實錘**：`StackOverflowError: Rendering screen`；crash report `Screen name`＝`GuiToolStation`／`GuiToolForge`（同一基地座標 x≈-122.7 z≈169.3）。TConstruct `CustomFontRenderer.func_78280_d`＝vanilla 式遞歸，NFR `MixinFontRenderer`（@Inject HEAD cancellable）攔 `func_78259_e`（sizeStringToWidth）回 0 → `s1 == str` → 自呼 1015 層爆 stack。5 次：10-01 18:07、10-02 03:54:15／03:54:33、10:57:51、11:02:53（11:00 重啟後新 session）。
- **`[fix] cjkLineBreak=false` 已試＝無效**（重啟後照爆、stack 一模一樣；`sizeToWidth`／`graphemeBoundaries` 0 次）→ **已還原 `true`**（config sha16 `4ac4635638c81402`＝改前原值）。
- **交付（C）**：`Documents\MC_Patches\dj2-wrapfix\`（PLAN.md／stubs／src／res／build.py／test\WrapGuardTest.java／swap_when_closed.py）。
  - **v0.1.0 實測唔夠**：mod 有 apply、handler 有行（stack 見 `redirect$zej000$dj2wrapfix$guaranteeProgress`、`dj2wrapfix-stall.log` 4 條），但 **12:06:04／12:08:47 照爆** → v0.1 只處理「量度 ≤0」，NFR 回「正數但過細」一樣令下一輪唔縮短。
  - **v0.2.0（現行）**：① 量度 ≤0 或 `|format(head)| ≥ i` → 自家貪心量度（`func_78263_a`）；② 保證 `|format(head)| < i`；③ 嵌套 >200 層硬返回。離線 harness 已重現舊 bug（無限遞歸）＋驗證新版收斂（maxDepth ≤17）。
  - **觸發字串（實錄）**：`\uE7E3\uE7BD\uE768§o§r\n你的工具在耐久度較少時會變得更持久。`（wrapWidth 128／GuiToolForge）。
  - **實機結果（12:30 session，v0.2.0）**：`cleanmix.log` 12:28:44 `APPLY dj2wrapfix.mixins.json:CustomFontRendererMixin … -> CustomFontRenderer` ✓；**冇新 crash**（最新仍係 12:08:47）→ **crash 修好** ✓。但 SK 螢幕截圖顯示 tooltip 斷行有個孤字行（「你」／「的工具會更持久…」）→ log 實錘：`measured=18 -> 22`（我哋 v0.2 嘅 advancePastInvisible 推過頭）。
  - **v0.3.0（現行）**：加門檻 —— 只有「頭段完全冇可見字 **而且** 唔係以換行結尾」才推過一個可見字；其餘保持原量度。harness case B（真字串 measured=18）已驗：完整句一行、0 孤字行 ✓。jar `dist\dj2-wrapfix-0.3.0.jar`（6,782 bytes、sha16 `5f36d20f5dc742f9`、bytecode 檢查全 OK）。
  - **合併成一個（SK 12:4x 指示「combine it to one」）**：→ **`dj2-fixes-1.0.0.jar`**（7,752 bytes、sha16 `1969d6a52a9625ec`；package `com.skps9.dj2fixes`；plugin `DJ2FixesPlugin`；config `dj2fixes.mixins.json` client=`[GuiNewChatMixin, CustomFontRendererMixin]`）。新專案 `Documents\MC_Patches\dj2-fixes\`；舊兩個專案保留（歷史＋備份）。離線 harness 10 case 全 OK（wrap 5＋chat filter 5）；jar／bytecode 檢查全過。部署：`deploy_when_closed.py` 等 MC 一關 → 刪 `dj2-chatfilter-0.1.0.jar`＋`dj2-wrapfix-*.jar` → 放 `dj2-fixes-1.0.0.jar`。**待 SK 關 MC → 自動換 → 開返驗收**（cleanmix APPLY、tooltip 斷行、紅字）。還原＝刪 `mods\dj2-fixes-1.0.0.jar`。
- **順帶**：dj2-chatfilter 喺 11:00 session 已載入（early loader ✓）、`single player mode` 紅字 0 次。
- 診斷全文：`Documents\PC_Troubleshoot\dj2-optimization\REPORT.md`。
- **總整理（SK 指示「put everything about DJ2 into file」）**：`Documents\PC_Troubleshoot\dj2-optimization\DJ2-筆記.md`（16.5KB；速覽表／自家 mod／7 個修好嘅問題逐項／技術事實＋SRG 表／效能 P1-P3／未解／檔案索引／時間線）；REPORT.md 頂部已加 pointer。
- **對方（MayaCraft AI）回覆 2026-10-02**：揀 **B**（網頁＋重打包 v1.3，manifest 版本欄 `2.23.4-v1.3-shader`）；三樣全納（`dj2-fixes-1.0.0.jar`／字體釘 0.6.1／Modernity f3）；佢哋另會改紅字 FAQ、記憶體 FAQ、JVM 頁 ZGC 註明、資源包 f3、包內 `使用說明.txt` 同步。**佢捉到我 3 個錯（我開 zip 重驗，全部佢對）**：無光影版 `.disabled`=7（四件組喺無光影版屬 manifest 條目 221＋4＝225）／佢哋用 **HEI 取代 JEI**／`Fugue／Flare／ZenUtils／StellarCore` 官方已有 → 報告頂部已加「■ 勘誤」＋附錄 C 已改。**SK 2026-10-02 決定：交 jar ＋ 源碼（b）** → 交件夾 `Documents\PC_Troubleshoot\dj2-optimization\handover-dj2-fixes-1.0.0\`（`dj2-fixes-1.0.0.jar` 7,752B sha256 `1969d6a5…2095`；`dj2-fixes-1.0.0-source.zip` 17,621B sha256 `30c91aca…b074d`（12 檔，已剔除本機部署腳本）；`README.txt`；`交件訊息（貼畀對方）.md`）——**未發出，等 SK 自己 send**。
- **更新報告（交對方 AI）**：`Documents\PC_Troubleshoot\dj2-optimization\交MayaCraft-AI-DJ2更新報告-20261002.md`（214 行；§0 兩個 zip 對比＋■ 勘誤＋本地額外加嘅 mod（含 sha256）＋記憶體冇 leak；附錄 A 全部問題（11 crash report＋8 類）、附錄 B／B6／B7 社群＋中文留言（MC百科 88 短評＋模組頁留言）、附錄 C 加咗嘅 mod 清單）；知識總表 `DJ2-筆記.md`、原始報告 `REPORT.md`。

## 今日完成（2026-10-02）
- **21:3x 卡頓釐清＋隔離計畫**：SK 澄清「**只有新機（5090）卡，舊機（3060）唔卡**」→ 排除純伺服器側（雖然實測 mayacraft 主機 443/5601 都有間歇 235–241 ms 尖峰、Google/Cloudflare 乾淨 = 佢條線本身冇問題）。實時 per-process 量度（PowerShell GPU/CPU counter）：**cs2 = 56.6% GPU／11.4% CPU**、javaw(MC) = 4.9% GPU／3.4% CPU → 雙開真係爭 GPU。計畫：① 閂 CS2 測 ② maxFps 260→141 ③ 停字體 mod ④ Actinium↔Nothirium ⑤ 重開 MPO ⑥ DDU。待 SK 答「舊機 vs 新機軟件分別」。
- **21:1x 5090 卡頓研究（SK：「3060 時同時開 CS+MC 唔覺卡」）**：本地實測＝HAGS 關、MPO 關（OverlayTestMode=5）、ReBAR 開（BAR1 32GB）、PCIe Gen5 x16、高效能電源、GPU 無 throttle（55°C／380W／2887MHz）✓；MC `options.txt` maxFps=260＋VSync 關＋G-Sync 未開。**官方來源**：NVIDIA 581.42 release notes Open Issues **無** 5090 卡頓項（只有 CS2 低解析度文字變形）；§5.4 官方明寫「多螢幕＋視窗模式＋硬體加速播片 → driver 會關 G-SYNC」、「螢幕 refresh 唔同（即使唔用 G-Sync）會卡」；§5.2 WO 20H1+ MPO 令視窗 app 可行 G-Sync（我哋已停 MPO → 視窗 MC 大機會無 VRR）。上游 GitHub #880＝5090 presentation 凍結 3–5s。Steam：5090+9950X3D 用戶由 Balanced 改 High Performance profile 即唔卡。機制推論（C 級）：MC 1.12.2 單執行緒 → 5090 輕場景 600–1000 FPS 令主執行緒飽和、重場景掉到 75–190 → 「換強卡反而卡」。**建議待 SK 決定**：maxFps 260→141、開 G-Sync、NVIDIA profile 改高效能、打 DJ2 時閂 CS2。
- **20:2x v1.0.1（外觀修正）**：SK 報「Tinkers tooltip 開得返，但太多空位」＋截圖 → 查到成因（**實錘**）：`logs/latest.log` 有 40 條 `wrap measure fixed: wrapWidth=139/140/141 measured=0 -> 8 text=\uE7E3\uE7BD\uE768§o§r\n你的工具…` → 我哋把「隱形前綴＋換行」切成獨立一行 → 多出一行空白。離線重現（harness case A）：修前 4 行（2 行空白）→ 修後 3 行（1 行空白）✓；改法＝頭段以 `\n` 結尾時斷點擺喺換行「之前」（TConstruct flag 會吞咗個換行；`f <= i` 恆成立所以一樣收斂），收斂保險改用 `f < i + skip`。build `dj2-fixes-1.0.1.jar`（7,801B、sha256 `fd04d82185cced76fda2…`、無 stub 洩漏、12 個離線 case 全過）→ 背景 watcher `proc_88c88b1667f5` 等 MC 關 → 自動換（mods 只留一個 jar）。**1.0.0 已交件（功能一樣、只差一行空白）→ 待 SK 決定要唔要補發 1.0.1 交件包。**
- jarvis-pc 當日無新 commit
- 未 commit 檔案 5 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 113 個 commit（未 push）

## 2026-10-01 19:2x（Discord；抖音「搵新收藏」— 被驗證碼擋，掃描工具已升級 headless）

- **做咗**：grep 09-13／09-20／09-27 掃描＋vault，抽出 SK 問「同 Strata 片類似」嘅 4 條收藏並全部 ASR 實讀＋上游核實：`58953`（Qwen3.8 27B→5.9GB = PrismML Bonsai 2 ternary；長鏈 agent 只剩 ~75%）、`6932`（4G 跑 70B = MoE offload 宣傳版）、`4302`（8G 跑 35B 快 Ollama 2–4× 真相 = llama.cpp CPU-offload，傳播數字打折）、`3967`（新聞匯總，只記錄）。寫入 `Hermes_Vault\03_收藏吸收\` 4 檔 ＋ MOC 3 行；`PENDING_PROPOSALS.md` 加「本地 MoE offload 引擎試用對比（llama.cpp --n-cpu-moe／KTransformers 19.5K★ vs Strata 8 日新）⏳ 等 SK」。
- **新工具（已入 skill）**：`douyin-tiktok-content/scripts/douyin_fav_headless_scan.py` — headless=new Chrome ＋ CDP(websockets) 靜默掃收藏，SK `using`／打機中都跑得（零窗口零搶焦點）；stdout `title_is_captcha`＋`body_len` 即判 CAPTCHA。SKILL.md＋`references/douyin-favorites-browser.md` 已更新（headless 首選、可見 browser 只做 fallback）。
- **⚠️ Blocker**：今次掃唔到新收藏 — 抖音出「验证码中间页」滑塊（`douyin_scan_20261001/shot_fav.png` 實錘）。根因＝**cookies 09-27 export 已過期（壽命 2–3 日）**。待 SK 二選一：(a) 重新 export `~/.config/yt-dlp/cookies.txt`（之後全 headless 零干擾）；(b) 開可見 browser 喺副螢幕、SK drag 一次拼圖（等佢唔打機時）。
- **片源核實**：YouTube `JD8_r5UDylc`（Tech-Practice）= **贊助廣告**（片頭推 agieverywhere.com hosted API）＋Strata demo；標題「200t/s」係創作者 headline 非獨立測試。Strata（`Niko1221/Strata`）3,699★ MIT、2026-09-24 上線（8 日大）、最新 0.1.31、主作者 1 人（260 commits）＋9 貢獻者、65 open issues、release 只有 `strata-windows-x64.zip`（源碼可自建）。官方 bench（5070 12GB）：Q2_0 93／IQ2_XS 79／IQ3_S 53 t/s；社群（#307）4090 IQ2_XS 106／IQ3_XXS 98 t/s。



## 2026-10-01 18:2x（Discord；DJ2 新 crash 查證——NFR×TiCon，唔關 chat filter 事）

- SK 報「game just crashed」（**觸發畫面 = TiCon 工具站 GUI**，SK 18:4x 確認）→ 親核 `crash-reports/crash-2026-10-01_18.07.28-client.txt`（187.6KB）：`java.lang.StackOverflowError: Rendering screen`，stack = `slimeknights.tconstruct.library.client.CustomFontRenderer.wrapFormattedStringToWidth` **自我遞歸 184 層** ↔ `FontRenderer.sizeStringToWidth` 嘅 NFR hook（`handler$zpj000$neofontrende$sfr$onSizeStringToWidth` → `StructuredTextRuntime.currentEngine` → `NeofontrenderConfig.brilliantTextBindings`）。
- **唔關 chat filter**：crash report 0 次提及 `dj2chatfilter`（該 session 喺 18:04 放 jar 之前開；18:08 新 session 才有載入）。
- **chat filter 初步驗收中**：`cleanmix.log` 有 `APPLY dj2chatfilter.mixins.json:GuiNewChatMixin from mod dj2chatfilter -> net.minecraft.client.gui.GuiNewChat`；新 session（18:08–18:11）`[CHAT]` 只有 1 行（JourneyMap），`single player mode` **0 次**（正對照成立）。待 SK 按 T 再確認。
- **NFR 背景**：Revo Font 0.6.1（`neofontrender`，作者 AndreaFrederica；issue tracker `github.com/AndreaFrederica/NeoFontRender/issues`）；config `config/neofontrender.toml`（`engine = "cosmic"`、`[compat.tinkersantique] enabled = true`）＋ `config/neofontrender-mixins.toml`（逐 mixin 開關，`MixinFontRenderer = true`）。可能修法：① 關 tinkersantique compat ② engine 改 sfr／vanilla ③ 關 MixinFontRenderer ④ 報 upstream。等 SK 揀。 **上游實況（Hermes 親查 GitHub API 2026-10-01）**：NFR 0.6.1（2026-09-29 發佈）已經係最新 release；issue tracker 活躍但**冇一條 Tinkers 相關**（近期：#75 游戏崩溃／#74 VintageFix+JourneyMap／#72 Resume Game crash／#68 Cleanroom modlist menu／#66 Cleanroom Command Suggestion）→ 呢單未有人報；TiCon 側 config 亦冇字體開關。**下一步（待 SK go）：試 `[compat.tinkersantique] enabled = false`（改前備份 neofontrender.toml）。**


## 2026-10-01 18:2x（Discord；DJ2 聊天欄紅字 — 自家 client mod 已 build，待 SK 重啟驗收）

- **做法（SK 揀 ② 自家 client mod ＋ (i) 全清淨）**：Mixin 攔 `GuiNewChat.func_146227_a`（＝`printChatMessage`，SRG 名由官方 mcp_stable-39-1.12 methods.csv 親核；`[CHAT]` log 喺 `printChatMessageWithOptionalDeletion` 內 ⇒ 攔最外層＝畫面＋log 一齊清）。
- **交付**：`Documents\MC_Patches\dj2-chatfilter\`（PLAN.md／src／stubs／res／build.py）→ `dist\dj2-chatfilter-0.1.0.jar`（**2,948 bytes、sha16 `fb41fe1f118396c2`**）已放入 DJ2 `minecraft\mods\`。
- **實作坑（實測）**：① 一定要用 Cleanroom 自帶 **JDK 25**（`~/.cleanroom/java/zulu25…`）——Cleanroom／MixinBooter 的 class file 係 v69，JDK 17 讀唔到；② javac 要 `-encoding UTF-8`（否則 Big5 判 CJK 註釋做 unmappable）；③ stub 類**必須**分開 output dir，否則會被掃入 jar（build.py 已有 assert 防呆）；④ 註冊用 `FMLCorePlugin`＋`MixinConfigs`（形狀跟 Fugue／EMT）＋ `IEarlyMixinLoader`。
- **驗收（待 SK）**：重啟 game → 按 T 5 次 → ① 聊天欄零紅字 ② `latest.log` `grep -c "single player mode"` = 0 ③ `cleanmix.log` 有 APPLY 行 ④ 正對照（其他聊天訊息照出）。**還原＝刪 `mods\dj2-chatfilter-0.1.0.jar`**。
- **✅ 已驗收（2026-10-01 18:4x）**：SK 回報「red text is gone」；Hermes 親核重啟後 session（18:08 起）`latest.log` 含 `single player mode` = **0 行**（同期只有 1 行 `[CHAT]`＝JourneyMap 提示，證明其他聊天訊息照出、冇誤攔）。


## 今日完成（2026-10-01）
- jarvis-pc 當日 commit 1 個（最新：e69b5c1 docs(handoff): 10-01 DJ2 chat-spam root cause (Cleanroom chat ）
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 100 個 commit（未 push）

## 2026-10-01 14:0x（Discord；MayaCraft 延遲量測報告 —— 交 server 管理員）

- SK 報遊戲內 tab ping 235ms、AFK 都仍然 200+（截圖 4 格綠）。Hermes 親量：ICMP 20 包（1000 bytes）**25–26ms、零丟包**；Minecraft status ping（客戶端量，同 server list 同尺）20 次有 **16 次 26ms**；但 **TCP 連線有 15–20% 樣本 234–258ms —— 同一主機 `:443` 同 `:5601` 都有**；對照 HiNet 24ms／Cloudflare 2ms 正常（tracert 11 跳、尾站 25ms）。
- 交付 `Documents\PC_Troubleshoot\maya-ping\2026-10-01-MayaCraft延遲量測-報告.pdf`（2 頁、sha16 `6711e29d14b73437`；md 同步；raw 樣本喺 `raw\`）。問題交去請 admin 查伺服器前面嘅 TCP 層（ICMP 例外）＋ TPS／GC／NIC。**未解 ⑫ 等 SK send 後回報。**
- **SK 2026-10-01 13:5x：佢自己就係 MayaCraft 其中一個 admin**（唔使 send 文件出去）→ 追加兩個實驗：① **同時段**量（45s）ICMP 45 包 24–25ms／零丟包 vs TCP 31/136＝**23% 變 235ms**，慢嘅每一刻 ICMP 都係 24–25ms；② **慢嘅比例同連接速率無關**（1/s＝32%、10/s＝24%、1/s＝20%、4/s＝32%）＝**時間性週期**（每幾秒一段 ~1s），唔係 per-source rate limit。⇒ 指向伺服器側 TCP 處理／排隊，非線路，亦非 SK 部機。
- **SK 13:5x 補充：佢唔係 owner、冇 SSH** —— server 係台灣朋友嘅（對方用 AI 管）。⇒ 交付改成**診斷請求訊息** `Documents\PC_Troubleshoot\maya-ping\給server管理員-診斷請求.md`（A 主機 VM／CPU steal＋PSI、B TCP 掉包／backlog／限速、C 網卡、D 反方向＋第三方 probe 腳本），SK 直接 paste 畀對方。**未解 ⑫ 等對方回 A–D 輸出。**
- **SK 13:5x 再補：server 環境＝Unraid 實體機（家用）＋裏面一個 VM 跑 MC**。⇒ 診斷訊息改成 Unraid 版 `給server管理員-診斷請求.md`（A 先答 3 條：.40 係 host 定 VM／:443 係邊個服務／LAN 對照；B host：steal、docker stats、NIC EEE/drop、br0＋conntrack、dmesg、iptables/nft、virsh dumpxml、mover/mdstat；C guest：PSI、nstat（ListenDrops／SynRetrans／BacklogDrop）；D probe 腳本）。- **SK 14:0x 定調：唔准叫對方跑腳本，只可以叫佢「試」**（對方用 AI 管 server、唔想畀一堆指令）。⇒ 交付改成 `Documents\PC_Troubleshoot\maya-ping\給伺服器主人-測試請求.md`（6 條隨手試：①佢自己入遊戲睇 tab 幾多 ②LAN 另一部機對照 ③停其他 Docker／VM 10 分鐘 ④睇 mover／parity ⑤重啟 VM/host ⑥換 LAN 線／熄 EEE ＋問 .40 係 host 定 VM、:443 係咩服務）；舊嘅指令版搬去 `raw\診斷清單-備用（唔會發出去）.md` 留底。
- **SK 14:0x 再補：對方「用 AI 管 server」＝一部 Hermes**（唔係人）⇒ 訊息改用 agent handoff 格式（目標／我量到嘅事實／請你測試優先／可選唯讀檢查／紅線：未經老闆同意唔好停服務或改設定／問 .40 係 host 定 VM＋:443 服務），檔名不變（覆蓋）。
- **SK 14:0x：「no ip」** ⇒ 訊息內**所有 IP 位址抽走**（只留端口號 5601／443；玩家寫「香港玩家 SK」、伺服器寫「你部 server／Minecraft 端口 5601」）。⚠️ 待 SK 確認意思：唔想訊息出 IP，定係指「VM 冇 public IP（經 host／router 轉發）」。
- 判讀更新：慢值穩定 235ms ＝ +210ms ≈ **一次 TCP 重傳**（Linux min RTO 200ms）⇒ 懷疑間歇性丟 TCP 包，ICMP 例外；:443 都中 ⇒ 指向 host／bridge／NIC／CPE，唔係 guest 程式。
## 2026-10-01 13:2x（Discord；SK「read hand off」→ drift 複核，零新工作）

- 兩份 HANDOFF 都讀完（jarvis-pc STATE＋近 3 日、MC repo STATE）；MC 線自 09-22 冇動（HEAD `013e4ac` 同 `origin/main` 一致；Slice 1b code 4 檔仍 dirty）。
- **捉到 4 處過時句（全部已改）**：① HEAD 寫 `26701c4`、實為 `e69b5c1` ② 未 push 寫 95、實為 100（親核 `git ls-remote`，remote tip `be003f46` 係 HEAD 祖先）③ 未 merge 寫 151、實為 156 ④ 「JARVIS 冇行」係 09-29 舊況，實況 10-01 13:2x 行緊。
- SK 部機現況：`sk_activity.json` = `using`（前景 Prism Launcher）→ 今次零 GUI 操作。

## 2026-10-01 01:4x–3:1x（Discord；DJ2 聊天欄紅字「single player mode」根因）

- **症狀**：開有聊天輸入嘅畫面（T／JourneyMap 全螢幕／睡覺畫面）聊天欄出紅字。SK 實測：按 T ＝ **2 行**、打「/」＝ **4 行**。
- **字串唯一出處（javap 親核）**：`toolprogression-1.12.2-1.6.12.jar` 嘅 `ToolProgressionCommand.func_184882_a`（checkPermission）——非單機就 `sendMessage` 紅字＋return false（訊息寫錯位：應該喺執行度，唔應該喺權限檢查）。
- **邊個問呢個 check**：真 runtime jar（obf `minecraft-1.12.2.jar` ＋ tsrg 映射）掃出全部 caller 只有 `net/minecraft/command/CommandHandler` 三個方法：`executeCommand`／`getTabCompletions`／`getPossibleCommands`。
- **觸發者（Cleanroom 自己）**：`com/cleanroommc/client/chat/suggestion/SuggestionUpdater` refresh 時 ①`ClientCommandHandler.autoComplete` → `getTabCompletions`（逐條指令掃，客戶端印 1 行）②砌 `CPacketTabComplete` 送去伺服器（`brz.a`）→ mayacraft 都有 TP → 伺服器再掃（第 2 行）⇒ **每次「問」＝ 2 行**（1 本地＋1 伺服器），解釋到 T=2／「/」=4。
- **pack 自己嘅 fix 為何冇效**：EMT（`endermodpacktweaks-0.5.11.jar`）本來有 `ToolProgressionCommandMixin` 專吞呢句，但佢用 MCP 名（`checkPermission`／`ICommandSender;sendMessage`）＋`remap=false`，runtime 係 SRG 名（`func_184882_a`／`func_145747_a`），而 `mixins.endermodpacktweaks.refmap.json` 係 0 mapping → 注入點搵唔到、靜靜唔 apply（CleanMix 冇 APPLY 行）→ 開 `[01] Enable Tool Progression Tweaks` 都冇用。
- **唔可以攞走 TP jar**：mayacraft 有裝 Tool Progression 並強制 client 亦要有（1.12.2-1.6.12）→ 停 client jar 會連唔到線（錯誤：`Requires version 1.12.2-1.6.12 but mod is not found on client`）。
- **修法三選（等 SK 揀）**：① 改 TP jar 5 bytes（腳本＋README 已喺 `Documents\MC_Patches\dj2-tp-silence\`；**只減半**）② 自家 client mod 顯示前攔（兩邊清零；要起 1.12.2 build 環境，估 1–2h）③ 改 Cleanroom jar 令佢唔再問（清零但脆：relauncher manifest 有 sha1、且失去指令建議）。
- **②可行性已核**：Cleanroom jar 內建 `zone/rong/mixinbooter/ILateMixinLoader`（EMT 就係用佢）；本機有 JDK17＋ASM 9.10.1＋cleanmix 0.7.2＋mixinextras 0.5.5；**欠** 1.12.2 編譯用 MC SRG jar。
- **未做／現況**：`DJ2-Cleanroom-TEST` 副本已唔在磁碟（要重做測試先再複製）；SK 02:54 實測打緊 CS2（fullscreen）→ 全程零 GUI 操作、**未改任何 jar**。

## 2026-09-30 21:0x（Discord；DJ2 客戶端交咗另一個 AI → Hermes 只做測試）

- **SK 決定**：MayaCraft DJ2 客戶端嘅**文檔／打包（使用說明補節、v1.3 zip）交咗另一個 AI 處理** → Hermes **唔做文檔**，只負責**測試**。
- **測試現況（log 實證）**：今日 16:11 起連續玩到 **19:10**（約 3 小時）、**零新 crash report**（最後一個係 10:13:11，喺換版之前）→ 今日改動（NeoFontRender 0.6.1＋ModularUI、移走 SmoothFont、resource pack 改 f3、Actinium 0.0.11）**未見任何回歸**。
- **待 SK 眼睇 3 項**：① 字體有冇變 NeoFontRender（光滑感）② 物品欄 GUI／格子對唔對齊（f3 pack）③ 若行 B 版，光影著唔著。
- `REMAINING_WORK.md` 已加 09-30 sync；STATE 已改寫（commit `532f889`）。
- **ping 最後定位（21:2x Hermes 親核）**：SK 遊戲 session 仍 `Established`（javaw PID 45212→mayacraft 主機:5601）。同一部 host：**:443 連續 6 次 27ms 穩定**；**:5601 六次有兩次 235–236ms**（+208ms）→ **懲罰係遊戲端口專屬**（該 host 嘅防護／回源層），ICMP 3/3 25–26ms 零丟包、SK 部機排除。已停止再探測（避免觸發對方 rate limit）。
- **21:5x AFK 實測（SK 截圖）**：靜止一段時間後 ping 回落 **26ms** ＝我實測路徑值 → 高 ping 同「活動量」掛鈎（chunk／封包爆發經遊戲端口排隊），ping 線收結、唔再探測。



## 2026-09-30 12:0x（Discord；SK「done, read it」→ 面試錄音轉錄收尾）

- **錄影親核**：`Videos\2026-09-30 10-54-45.mp4` 701,449,772 bytes、`ffprobe` **3598.15s = 59:58**；OBS log `2026-09-30 10-52-29.txt`（Recording Start 10:54:46／Stop 11:54:44）；開檔前後 stat 一致（已收檔）。
- **音源**：mic ＋ 耳機混成一條 AAC stereo（唔可分開）→ 16 kHz mono wav 115 MB。
- **兩引擎**：SenseVoice 30 秒分塊（**120 塊／110 有聲／0 錯**，rtf≈0.003）＋ faster-whisper `small` 全檔 3 進程（**1,529 行**）。
- **出檔（腳本 render，非手抄）**：逐字稿＋情報摘要 → 本機 `Documents\MS_DCT_Prep\records\`（48,225／10,342 bytes）。**內容含面試官身分／評語 ⇒ 依規則唔入可公開文件**。
- **未做**：(c) 中文玩家回覆、(b) A/B FPS 量測（SK：b later、interview first、a ignore）。
## 2026-09-30 10:3x（Discord；DJ2-Cleanroom Actinium 版收口）

- **使用說明.txt**：加【版本選擇：要 FPS 定要光影】一節（A 版 Nothirium 組／B 版 Actinium 0.0.11 對照表、切換步驟、兩條紅線、實測記錄、Actinium 已知小問題）＋Actinium 官方下載連結（包 zip 冇跟呢個 jar）→ 108 行、UTF-8 無 BOM、LF、sha16 `7cef1cc4d2858c46`；改前備份 `hermes\backups\dj2-actinium-test1-20260930\使用說明.txt.before-20260930-1034`。
- **快照**：`…dj2-actinium-test1-20260930\版本對照-20260930.md`（2,698 bytes；四次實測＋現況 mod 開停清單；唔跟包出去）。
- **Skill**：`cleanroom-modpack-crash-triage`（software-development）已建＋補 `## When to Use`。
- **GUI／slot 對唔上（SK 2026-09-30 15:1x 貼圖問）＝用錯 resource pack 版本**：DJ2 開住 `Modernity-**f1**-3.10.3.1.zip`（pack_format 1；`options.txt` 有 `incompatibleResourcePacks` 證明遊戲自己 flag 佢唔相容）；作者 Modrinth 元數據 f1-3.10.3.1 = **1.12.2 False**、f3-3.10.3 = **1.12.2 True**。實測：把 1.12.2 格線（x8/y84、18px pitch）疊上兩版 inventory.png → f1 明顯偏（工藝 2×2 位置亦唔同），f3 對正；兩版 GUI 差 3.9% 像素。已下載正確版 `Modernity-f3-3.10.3.zip`（Modrinth、sha512 核對）入 DJ2 resourcepacks（未啟用）；**等 SK 決定要唔要 Hermes 改 options.txt（停 f1／開 f3）**。另一 pack `2.2.0_plain_Jappafied_Modded.zip` 無 GUI 圖、唔關事。
- **錯版已移除（SK 2026-09-30 16:10 叫 Hermes 做）**：`Modernity-f1-3.10.3.1.zip` 由 DJ2 `minecraft\resourcepacks` 移去 `…\hermes\backups\dj2-actinium-test1-20260930\removed-packs\`（可還原）；`options.txt` 已備份（`options.txt.before-20260930-161050`，改後 byte-identical）；SK 自己已切換，現況 `resourcePacks:["2.2.0_plain_Jappafied_Modded.zip","Modernity-f3-3.10.3.zip"]`、`incompatibleResourcePacks:[]`、`guiScale:0`。全 instances 掃描：冇其他 f1 殘留（NovaEngineering 用 f3-3.10.2＋Adjunct／Extra addons）。
- **遊戲 ping 266ms 查證（SK 2026-09-30 16:2x–16:5x）**：MayaCraft 主機＝**台灣台北 mayacraft 主機（Chunghwa AS3462）**。**路徑健康**：tracert 11 hop 25ms、ICMP 31/31 25ms 零 spike、單發 TCP 26ms、LAN 1ms、1.1.1.1 2ms、HiNet 168.95.1.1:443 24ms 零 spike、無 VPN（6 個 OpenVPN adapter 全 Disconnected）、Ethernet 5GbE Up。**但 Minecraft 應用層 ping（25 次）中位 93ms、7/25（28%）跳 700–756ms**；同 IP 換 port 一樣跳 → 屬「SK ↔ server」之間 TCP 層間歇延遲（不是 server 對所有人）。**推翻早前「server 端限流」結論**（SK 朋友同為香港但 25ms）。仍在查：ISP 路由（路徑 HKBN 112.118→PCCW→中華）、NIC 三個可疑設定（**節能乙太網路 EEE＝開啟、Selective Suspend＝開啟、流量控制 Rx&Tx 開啟**）、join 後大量 chunk 下載。顯示來源：**Universal Tweaks `UTGuiPlayerTabOverlayMixin`** 讀 `func_178853_c`（=getResponseTime，server keep-alive 量值）→ 真數據非顯示 bug。
- **ping 續查（SK 2026-09-30 17:0x 貼 server-list 圖）**：SK **未入遊戲時 server list 顯示 26ms**（同我 TCP 量度 25–26ms 一致）→ 路徑正常。未入遊戲嘅 idle 期再量（每 0.35s 一次、13 次）：game host min25/med26/**max242**，對照 HiNet 24/24/25 → 「+240ms 間歇懲罰」只發生喺「SK ↔ 呢個 host」。實測上傳 20.6 Mbit/s、下載測試被 CF 403 擋（未量）。**關鍵未解**：in-game 數字係 **server 用 keep-alive 量**、server list 數字係 **client 量** → 要問 SK 朋友 25ms 係喺邊度睇。
- **ping 結案（SK 2026-09-30 17:1x）**：**入到遊戲、load 完之後 tab list ＝ 51ms 綠色**（圖證）→ 之前 266ms 係**join 後大量 chunk／資料下載期間嘅暫態**，唔係故障。結論：路徑 26ms（server list 實測）＋ in-game 51ms 正常；唔需要任何改動。若再見高數字 → 等 2–3 分鐘俾佢載完，仍高先 relog／試 VPN 對比 ISP path。
- **ping 再查（SK 2026-09-30 17:2x：朋友 in-game 都係 25ms、SK 常見 200+）**：排除法完成 —— **SK 部機冇事**（5ms sleep overshoot 1940 樣本 max **0.6ms**、total CPU 5–8%、LAN 1ms、無 cFos/Killer/GameFirst/加速軟件；只有 ms_pacer/ms_l2bridge 標準 binding）。**尖峰只出現喺 game host**：15 次 TCP :5601 有 **4 次連續（約 1.5 秒窗口）236–248ms**，同一時間 HiNet 168.95.1.1 = 24–25ms 零尖峰；114.34.59.0/24 其他 IP 唔通（filtered）。→ 結論：**server 側／該 host 網絡嘅 1–2 秒週期性尖峰**（唔係 SK 網絡）。下一步靠 SK：同時段朋友對比、VPN 換出口測試、必要時出報告畀 server 管理員。
- **SK 揀 B → 已裝 NeoFontRender（2026-09-30 14:45）**：`mods\neofontrender-0.6.1-full.jar`（28,399,167；sha256 `0560eceb…`＝官方 digest）＋`mods\modularui-3.2.0-nfr.2.jar`（2,742,727；sha256 `50babd81…`；NFR 嘅 `mcmod.info` 明寫 `requiredMods: modularui@[3.2.0-nfr.2,)`，本包原本冇 ModularUI）。兩個都無鎖；未重開遊戲（未生效）。還原＝`hermes\backups\dj2-neofontrender-20260930\restore_neofontrender.py`（只刪呢兩個 jar）。⚠️ **SmoothFont-mc1.12.2-2.1.4.jar 唔喺 DJ2 mods**（14:41 仲有、14:44 已冇；唔係 Hermes 刪）→ 其他 instance（Enigmatica 2 Expert Extended）有同一版本可複製返。遊戲內開 NFR 設定＝按 `O`；`/neofontrender info`。
- **SmoothFont 冇效（SK 2026-09-30 問）**：根因＝**Actinium 接管字體**（`mixins.actinium.vintage.json` 嘅 `MixinFontRenderer` 改 `renderStringAtPos`／`renderStringAligned`／`getCharWidth` ＋ Angelica `BatchingFontRenderer`）→ SmoothFont 自行停用（`latest.log` 14:40:08 `Disabled smoothfont functions.(reason:renderChar methods might be replaced.)`）；A 版 run（`2026-09-30-6.log.gz`）**冇**呢行＝A 版 SmoothFont 正常。上游 Actinium issue #1 已記（官方建議關 SmoothFont 或用 optimize-only）。四條路：A 切 A 版／B 改裝 NeoFontRender 0.6.1（Actinium 有內建 compat）／C `-Dactinium.disableFontBatcher=true`（未官方測試）／D `runMode=2`。診斷檔 `hermes\backups\dj2-actinium-test1-20260930\smoothfont-診斷-20260930.md`。
- **現況組合**：Actinium 0.0.11（sha256 `688efc58…`＝官方 digest）＋Chibi 5.33 開；Nothirium／RenderLib／Naughthirium／meldexun EntityCulling `.disabled`；`celeritasextra`／`celeritasdynamiclights`／舊 compat bridge 已移。


## 陷阱（重溫）

- **JARVIS ONE 進程數唔等於開咗幾多個 app**：一個 app 正常有 **4 個同名進程**（主進程／GPU／network service／renderer）＋ portable 外層 exe；Task Manager「詳細資料」每個進程一行（2026-09-25 查證）。**唔好 kill 主進程**。

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


