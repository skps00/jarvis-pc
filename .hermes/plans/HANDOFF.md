# HANDOFF — jarvis-pc（狀態區塊 + 逐日 index）

<!-- STATE:BEGIN -->
## 狀態（每次 session 尾／cron **改寫**；新 section 一律加喺本區塊**之下**）

- **目標**：JARVIS ONE（語音／HUD／alerts）穩定收尾 ＋ MC packai（Forge 1.19.2 primary）＋ MayaCraft DJ2 客戶端玩家支援（非 repo 專案）。計畫書：`.hermes/plans/REMAINING_WORK.md`
- **現狀（2026-09-30 19:3x 改寫；全部 Hermes 親核）**
 - **MS DCT 面試：四場全部完成**（Mike 9/28；Elena＋Dhaval 9/29；**Owen 9/30 11:00＝最後一場**，59:58 已轉錄）→ `Documents\MS_DCT_Prep\records\`：`面試-20260930-1100-Owen-逐字稿.md`（48,225 bytes）＋`-情報摘要.md`（10,342 bytes）；今日 focus＝technical knowledge；role 實際＝**70–80% hands on**（SK 原答 remote support 被即場修正）；Owen Lee＝前 Microsoft 香港 DC site operation manager（Mike Wong report 佢）。**冇下一輪；下星期有 conclusion**（10/1、10/2 係其他人面試）。枱面檔＝`面試速查-中英對照.pdf`（7 頁）＋`今日唸稿-20260929.pdf`。
 - **DJ2-Cleanroom（玩家支援；09-30 收線）**：① Actinium 0.0.11 版可連 mayacraft.net（10:28:58 開機→10:30:44 入服、零 mixin 錯誤）② `使用說明.txt` 加【版本選擇：要 FPS 定要光影】（108 行；sha16 `7cef1cc4d2858c46`）③ 裝 **NeoFontRender 0.6.1＋ModularUI 3.2.0-nfr.2**（sha256 對官方 digest；**SmoothFont 已移除** → 根因＝Actinium 接管字體令 SmoothFont 自我停用）④ resource pack 錯版已移除：DJ2 用 `Modernity-f3-3.10.3.zip`（f1 版 pack_format 1 → GUI／格子對唔上）；**文檔／打包交咗另一個 AI，Hermes 只做測試**（16:11–19:10 連續玩、零 crash）⑤ 遊戲 ping 266ms **結案**＝join 後暫態（load 完 51ms；路徑 26ms 實測正常；間歇 +240ms 尖峰只出現喺「SK ↔ 該 host」，SK 部機已排除）。
 - **Git**：jarvis-pc `feature/hermes-alerts-mcp` HEAD `26701c4`；**未 push 95**（vs origin/feature，未 fetch）、**未 merge 151**（vs origin/main）；**未 commit 4 檔**（`hud/main.js`／`hud/settings.html`／`src/jarvis/settings.py`／`src/jarvis/shell_app.py` ＝ Slice 1）。
 - **JARVIS ONE**：09-29 07:3x 親核冇行（要開先問 SK）；⚠️ 一個 app 正常 4 個同名進程，唔好 kill 主進程。
 - **Slice 1（側車重啟循環修復）＝ code 寫好、自驗過、未 commit、未換版**；還原＝`git checkout -- <4 檔>`；patch 存底 `%LOCALAPPDATA%\hermes\backups\jarvis-sidecar-slice1-uncommitted-20260923.patch`。**等 SK 揀驗收窗口 1／2**（窗口 1＝開 HUD 15–20 分鐘；窗口 2＝HUD 關 ≥35 分鐘；打包換版夾喺兩窗之間）。
 - **5090 黑屏 Tier 1**：`OverlayTestMode=5`／`TdrDelay=20`／`TdrDdiDelay=30` 仍在 registry；還原 `mpo_restore.reg`；watchdog cron `4dfef80822b3`（*/5）行緊、無新事件。
 - **CS2 幀時 spike**：未做＝MSAA 4X→2X（只可遊戲內改）、Steam overlay 關 → 之後 A/B 量 frametime（工具／報告 `Documents\PC_Troubleshoot\cs2-perf\`）。LPI：0-15＝V-Cache CCD。
 - **packai（MC 主線）**：HEAD `013e4ac` 已 push；**Slice 1b 4 檔未 commit**＋**真機 A/B 未跑**。
 - **語音／mic 線 HOLD**（等新 mic）；Hermes `compression.micro_compact=true`。
- **唔准郁（硬限制）**
 - 打機／用緊電腦：**零彈窗、零搶焦點**（先讀 `state/sk_activity.json`）；GUI 窗一律第二副螢幕；Chrome 主動開＝`bg_launch.py --minimized`
 - `AGENTS.md` 受保護（要 SK 明確 go）；唔准 `curl|sh`；**HANDOFF 視為可公開 → 唔准入 secrets**
 - packai code **一律經 cursor-agent**；**唔准 `git add -A`**；真 instance 唔准自動部署
 - **語音／mic 線 HOLD**：唔郁 `wake.py`／STT／AEC／聲紋／threshold／mic device
- **未解（等 SK 決）**：① JARVIS Slice 1 驗收窗口 1／2 ② Slice 1 打包換版 ③ **測試隔離 ii 實作**（已批准未開工）④ **packai Slice 1b 真機 A/B** ⑤ Slice 1c／Slice 2 正式 plan ⑥ **dev → main 合併**（PR 定直接 merge）⑦ **反方 reviewer R1 報告未消化**（subagent session `20260927_231610_3d99d0`，11.3k 字：LD1–LD6）⑧ **CS2 為何仍落 LPI 16-31** ⑨ JARVIS 要唔要開返 ⑩ **DJ2 客戶端測試待 SK 眼睇**（字體／GUI／光影三項；文檔＋v1.3 打包已交另一個 AI）
- **下一步（優先序）**：① DJ2 文檔收尾（使用說明兩節 → v1.3 zip）② JARVIS Slice 1 窗口 1 → 打包換版 → 窗口 2 ③ packai Slice 1b 真機 A/B ④ 反方 R1 → 三段式（≥8:2）⑤ CS2 剩兩樣 → A/B ⑥ 測試隔離 ii（plan → review）⑦ dev→main 合併決定
- **歸檔索引**：已完成記錄喺 `plans/archive/HANDOFF-2026-09.md`（主檔曾歸檔一次：09-22 段落搬走）
- **參考段（檔尾）**：陷阱（重溫）／語音·硬體設定（驗證過）
<!-- STATE:END -->
## 2026-09-30 21:0x（Discord；DJ2 客戶端交咗另一個 AI → Hermes 只做測試）

- **SK 決定**：MayaCraft DJ2 客戶端嘅**文檔／打包（使用說明補節、v1.3 zip）交咗另一個 AI 處理** → Hermes **唔做文檔**，只負責**測試**。
- **測試現況（log 實證）**：今日 16:11 起連續玩到 **19:10**（約 3 小時）、**零新 crash report**（最後一個係 10:13:11，喺換版之前）→ 今日改動（NeoFontRender 0.6.1＋ModularUI、移走 SmoothFont、resource pack 改 f3、Actinium 0.0.11）**未見任何回歸**。
- **待 SK 眼睇 3 項**：① 字體有冇變 NeoFontRender（光滑感）② 物品欄 GUI／格子對唔對齊（f3 pack）③ 若行 B 版，光影著唔著。
- `REMAINING_WORK.md` 已加 09-30 sync；STATE 已改寫（commit `532f889`）。
- **ping 最後定位（21:2x Hermes 親核）**：SK 遊戲 session 仍 `Established`（javaw PID 45212→114.34.59.40:5601）。同一部 host：**:443 連續 6 次 27ms 穩定**；**:5601 六次有兩次 235–236ms**（+208ms）→ **懲罰係遊戲端口專屬**（該 host 嘅防護／回源層），ICMP 3/3 25–26ms 零丟包、SK 部機排除。已停止再探測（避免觸發對方 rate limit）。
- **21:5x AFK 實測（SK 截圖）**：靜止一段時間後 ping 回落 **26ms** ＝我實測路徑值 → 高 ping 同「活動量」掛鈎（chunk／封包爆發經遊戲端口排隊），ping 線收結、唔再探測。



## 2026-09-30 12:0x（Discord；SK「done, read it」→ Owen 場面試轉錄）

- **錄影親核**：`Videos\2026-09-30 10-54-45.mp4` 701,449,772 bytes、`ffprobe` **3598.15s = 59:58**；OBS log `2026-09-30 10-52-29.txt`（Recording Start 10:54:46／Stop 11:54:44）；開檔前後 stat 一致（已收檔）。
- **音源**：mic `SteelSeries Sonar - Microphone` ＋ `耳機 (2- Arctis Nova 7)` 混成一條 AAC stereo（唔可分開）→ 16 kHz mono wav 115 MB。
- **兩引擎**：SenseVoice 30 秒分塊（**120 塊／110 有聲／0 錯**，rtf≈0.003）＋ faster-whisper `small` **全檔 3 進程**（**1,529 行**，part0 137／part1 804／part2 588）。
- **出檔（腳本 render，非手抄）**：`MS_DCT_Prep\records\面試-20260930-1100-Owen-逐字稿.md`（48,225 bytes，含誤聽對照表）＋`面試-20260930-1100-Owen-情報摘要.md`（10,342 bytes）。
- **內容**：Owen Lee（前 Microsoft 香港 DC **site operation manager**；Mike Wong report 佢）主持；今日 focus＝**technical knowledge**；自我介紹用英文（08:41→11:29，實測 168 秒＝2:48），其餘廣東話。技術題＝server 著唔返／機櫃電源（DGX 6×PSU）／CPU-RAM-HDD-SSD 症狀／新機上 rack 步驟／駁線種類（「答得最好嘅一條」）／no POST troubleshooting／換 RAM 後仍報 error；判斷題＝現場同 procedure 有出入、換 PDU 會斷兩邊電 → SK 答「先問人、唔對路停低、black and white 記錄」，Owen 評「絕對正確」。
- **修正**：SK 第 1 題把 role 理解成 remote support／跟 case → Owen 用 3 分鐘修正（70–80% hands on、一至五 9–6＋**每季一星期 standby**，after hours 做 first POC）。
- **〔判讀〕**：ASR 把 Owen 叫 SK 嘅 `angel/Angelo` 當成 **Andrew**（whisper [08:11] 聽到 `Andrew`）；「cost me around 15-60 hours per day」應為 **15–16 小時**（兩引擎同聽錯，物理不可能）。
- **未做**：(c) 中文玩家回覆、(b) A/B FPS 量測（SK：b later、interview first、a ignore）。

## 2026-09-30 10:3x（Discord；DJ2-Cleanroom Actinium 版收口）

- **使用說明.txt**：加【版本選擇：要 FPS 定要光影】一節（A 版 Nothirium 組／B 版 Actinium 0.0.11 對照表、切換步驟、兩條紅線、實測記錄、Actinium 已知小問題）＋Actinium 官方下載連結（包 zip 冇跟呢個 jar）→ 108 行、UTF-8 無 BOM、LF、sha16 `7cef1cc4d2858c46`；改前備份 `hermes\backups\dj2-actinium-test1-20260930\使用說明.txt.before-20260930-1034`。
- **快照**：`…dj2-actinium-test1-20260930\版本對照-20260930.md`（2,698 bytes；四次實測＋現況 mod 開停清單；唔跟包出去）。
- **Skill**：`cleanroom-modpack-crash-triage`（software-development）已建＋補 `## When to Use`。
- **GUI／slot 對唔上（SK 2026-09-30 15:1x 貼圖問）＝用錯 resource pack 版本**：DJ2 開住 `Modernity-**f1**-3.10.3.1.zip`（pack_format 1；`options.txt` 有 `incompatibleResourcePacks` 證明遊戲自己 flag 佢唔相容）；作者 Modrinth 元數據 f1-3.10.3.1 = **1.12.2 False**、f3-3.10.3 = **1.12.2 True**。實測：把 1.12.2 格線（x8/y84、18px pitch）疊上兩版 inventory.png → f1 明顯偏（工藝 2×2 位置亦唔同），f3 對正；兩版 GUI 差 3.9% 像素。已下載正確版 `Modernity-f3-3.10.3.zip`（Modrinth、sha512 核對）入 DJ2 resourcepacks（未啟用）；**等 SK 決定要唔要 Hermes 改 options.txt（停 f1／開 f3）**。另一 pack `2.2.0_plain_Jappafied_Modded.zip` 無 GUI 圖、唔關事。
- **錯版已移除（SK 2026-09-30 16:10 叫 Hermes 做）**：`Modernity-f1-3.10.3.1.zip` 由 DJ2 `minecraft\resourcepacks` 移去 `…\hermes\backups\dj2-actinium-test1-20260930\removed-packs\`（可還原）；`options.txt` 已備份（`options.txt.before-20260930-161050`，改後 byte-identical）；SK 自己已切換，現況 `resourcePacks:["2.2.0_plain_Jappafied_Modded.zip","Modernity-f3-3.10.3.zip"]`、`incompatibleResourcePacks:[]`、`guiScale:0`。全 instances 掃描：冇其他 f1 殘留（NovaEngineering 用 f3-3.10.2＋Adjunct／Extra addons）。
- **遊戲 ping 266ms 查證（SK 2026-09-30 16:2x–16:5x）**：MayaCraft 主機＝**台灣台北 114.34.59.40（Chunghwa AS3462）**。**路徑健康**：tracert 11 hop 25ms、ICMP 31/31 25ms 零 spike、單發 TCP 26ms、LAN 1ms、1.1.1.1 2ms、HiNet 168.95.1.1:443 24ms 零 spike、無 VPN（6 個 OpenVPN adapter 全 Disconnected）、Ethernet 5GbE Up。**但 Minecraft 應用層 ping（25 次）中位 93ms、7/25（28%）跳 700–756ms**；同 IP 換 port 一樣跳 → 屬「SK ↔ server」之間 TCP 層間歇延遲（不是 server 對所有人）。**推翻早前「server 端限流」結論**（SK 朋友同為香港但 25ms）。仍在查：ISP 路由（路徑 HKBN 112.118→PCCW→中華）、NIC 三個可疑設定（**節能乙太網路 EEE＝開啟、Selective Suspend＝開啟、流量控制 Rx&Tx 開啟**）、join 後大量 chunk 下載。顯示來源：**Universal Tweaks `UTGuiPlayerTabOverlayMixin`** 讀 `func_178853_c`（=getResponseTime，server keep-alive 量值）→ 真數據非顯示 bug。
- **ping 續查（SK 2026-09-30 17:0x 貼 server-list 圖）**：SK **未入遊戲時 server list 顯示 26ms**（同我 TCP 量度 25–26ms 一致）→ 路徑正常。未入遊戲嘅 idle 期再量（每 0.35s 一次、13 次）：game host min25/med26/**max242**，對照 HiNet 24/24/25 → 「+240ms 間歇懲罰」只發生喺「SK ↔ 呢個 host」。實測上傳 20.6 Mbit/s、下載測試被 CF 403 擋（未量）。**關鍵未解**：in-game 數字係 **server 用 keep-alive 量**、server list 數字係 **client 量** → 要問 SK 朋友 25ms 係喺邊度睇。
- **ping 結案（SK 2026-09-30 17:1x）**：**入到遊戲、load 完之後 tab list ＝ 51ms 綠色**（圖證）→ 之前 266ms 係**join 後大量 chunk／資料下載期間嘅暫態**，唔係故障。結論：路徑 26ms（server list 實測）＋ in-game 51ms 正常；唔需要任何改動。若再見高數字 → 等 2–3 分鐘俾佢載完，仍高先 relog／試 VPN 對比 ISP path。
- **ping 再查（SK 2026-09-30 17:2x：朋友 in-game 都係 25ms、SK 常見 200+）**：排除法完成 —— **SK 部機冇事**（5ms sleep overshoot 1940 樣本 max **0.6ms**、total CPU 5–8%、LAN 1ms、無 cFos/Killer/GameFirst/加速軟件；只有 ms_pacer/ms_l2bridge 標準 binding）。**尖峰只出現喺 game host**：15 次 TCP :5601 有 **4 次連續（約 1.5 秒窗口）236–248ms**，同一時間 HiNet 168.95.1.1 = 24–25ms 零尖峰；114.34.59.0/24 其他 IP 唔通（filtered）。→ 結論：**server 側／該 host 網絡嘅 1–2 秒週期性尖峰**（唔係 SK 網絡）。下一步靠 SK：同時段朋友對比、VPN 換出口測試、必要時出報告畀 server 管理員。
- **SK 揀 B → 已裝 NeoFontRender（2026-09-30 14:45）**：`mods\neofontrender-0.6.1-full.jar`（28,399,167；sha256 `0560eceb…`＝官方 digest）＋`mods\modularui-3.2.0-nfr.2.jar`（2,742,727；sha256 `50babd81…`；NFR 嘅 `mcmod.info` 明寫 `requiredMods: modularui@[3.2.0-nfr.2,)`，本包原本冇 ModularUI）。兩個都無鎖；未重開遊戲（未生效）。還原＝`hermes\backups\dj2-neofontrender-20260930\restore_neofontrender.py`（只刪呢兩個 jar）。⚠️ **SmoothFont-mc1.12.2-2.1.4.jar 唔喺 DJ2 mods**（14:41 仲有、14:44 已冇；唔係 Hermes 刪）→ 其他 instance（Enigmatica 2 Expert Extended）有同一版本可複製返。遊戲內開 NFR 設定＝按 `O`；`/neofontrender info`。
- **SmoothFont 冇效（SK 2026-09-30 問）**：根因＝**Actinium 接管字體**（`mixins.actinium.vintage.json` 嘅 `MixinFontRenderer` 改 `renderStringAtPos`／`renderStringAligned`／`getCharWidth` ＋ Angelica `BatchingFontRenderer`）→ SmoothFont 自行停用（`latest.log` 14:40:08 `Disabled smoothfont functions.(reason:renderChar methods might be replaced.)`）；A 版 run（`2026-09-30-6.log.gz`）**冇**呢行＝A 版 SmoothFont 正常。上游 Actinium issue #1 已記（官方建議關 SmoothFont 或用 optimize-only）。四條路：A 切 A 版／B 改裝 NeoFontRender 0.6.1（Actinium 有內建 compat）／C `-Dactinium.disableFontBatcher=true`（未官方測試）／D `runMode=2`。診斷檔 `hermes\backups\dj2-actinium-test1-20260930\smoothfont-診斷-20260930.md`。
- **現況組合**：Actinium 0.0.11（sha256 `688efc58…`＝官方 digest）＋Chibi 5.33 開；Nothirium／RenderLib／Naughthirium／meldexun EntityCulling `.disabled`；`celeritasextra`／`celeritasdynamiclights`／舊 compat bridge 已移。


## 今日完成（2026-09-30）
- jarvis-pc 當日無新 commit
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 82 個 commit（未 push）

## 今日完成（2026-09-29）
- jarvis-pc 當日無新 commit
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 73 個 commit（未 push）

## 2026-09-29 20:0x（Discord；SK「check video, today interview and new phone call is here」→ 今日 4 段錄影轉錄）

- **4 段錄影全部親核**（`ffprobe` 時長＋檔名時間戳＋OBS log `2026-09-29 07-09-00.txt` 對得上；冇 `obs64` 進程＝已收檔）：
 - `Videos\2026-09-29 10-55-31.mp4`（52:06）＝ **Elena 場**（loop 第 2 場）
 - `Videos\2026-09-29 11-47-39.mp4`（8:51）＝ **兩場之間嘅背景音樂**，零對話（SenseVoice 全文只有歌詞亂碼）→ 唔計
 - `Videos\2026-09-29 11-57-47.mp4`（42:30）＝ **Dhaval 場**（loop 第 3 場）
 - `Videos\2026-09-29 18-31-55.mp4`（53:47）＝ **內線教練電話覆盤**
- **輸出**（`Documents\MS_DCT_Prep\records\`，全部由腳本 render，無手抄）：`面試-20260929-1100-Elena-逐字稿.md`、`面試-20260929-1200-Dhaval-逐字稿.md`、`教練通話-20260929-1831-逐字稿.md`、`面試-20260929-情報摘要.md`、`教練通話-20260929-1831-重點摘要.md`
- **核對**：SenseVoice 30 秒分塊（RTF≈0.002，316 塊／7 塊靜音）；faster-whisper `small` **全檔 3 進程**（1132／426／447 行）逐條主張對照。核對**改正 1 個誤判**：[17:00] 唔係斷線，係 SK mic 被靜音（`you are on mute`）。Dhaval 場 [04:00] whisper 較清 → 今日＝ loop 第 2、3 場。
- **教練通話 actionable（明日用）**：① **唔好再講「用手機影相」**（教練：quick and dirty、唔應該講出口；正確＝場內 provided notebook／trace-lock 記錄／拉多一個人；「十間十間公司都唔准帶手機」，紙都唔准）② **講慢啲、一句一句、每句一個 point** ③ **明日 11:00＝Owen**，佢唔會問刁鑽題；10/1、10/2 仲有其他人面試 → **下星期有 conclusion**。
- **另記**：Elena 場三個 focus area＝ process compliance／safety／operational judgment；Dhaval 場實際係**技術情境題**（唔係原 plan 估嘅 culture），同一條「server 停／冇手機／冇程序」問咗 3 次 → 兩場題型高度重疊。
- jarvis-pc code 冇郁；只 commit HANDOFF。

## 2026-09-29 07:3x（Discord；SK「read hand off + read past session」→ 速查收口 ＋ 補記前一個 session）

- **前一個 session（09-28 11:11 → 09-29 02:49；`@session:default/20260928_111122_7f806f71`）成果之前冇入 HANDOFF，今次補記**：
 - 枱面檔收口成 **7 頁** `MS_DCT_Prep\面試速查-中英對照.pdf`（當時 sha16 `259c39019ac030ec`）＋ `.docx` 同步；版面＝10 秒 checklist → Mike 提醒 → 開場句 → 自我介紹（用 SK 原句、只改語法）→ ✅要／❌唔要 → 背景（四場／同一 set／三位面試官）→ 一個答題 concept ＋ 6 領域 ＋ 電話紀錄問題表 → 3 條反問 → 紅線。**冇一題一頁**（SK 當日指示：講完一題隔一兩行）。
 - 新記錄：`records\天晉-20260928-逐字稿.md`（104 分鐘錄音、SenseVoice 209 塊）＋ `天晉-20260928-重點摘要.md`（兩引擎核對：troubleshooting 六步／security awareness／safety stop-and-ask／衝突英文句）＋ `records\Mike-補課-20260928-2109.md`（3:45 語音：英文要搞返、對 Dhaval 講 `My English is average — if anything isn't clear, please stop me and ask.`、多笑唔好傻笑）＋ `records\內幕-背景-20260928.md`（只留 prep folder）。
 - SK 當日決定：**唔用「交易所斷網」例子**（全文 0 次）→ 例子包改 2 條真事（China Mobile International 換 RAM 對相／交易所項目 hardware decommission＋change control）；犯錯題正名為 China Mobile International（原本誤寫交易所）；自我介紹公司名由 `Chinese Mobile International` 改成官方全名；第 8 條用 `not familiar` 版本；第 14 條揀 `After a break`。
- **09-29 07:3x 親核／動作**：速查 PDF 修好一個殘留引號 bug（`（天晉 [32:30]）；" "「…` 合併成一行）→ 重出 **7 頁、sha16 `363bfce7dd00d9f0`、0 冒號、0 殘留引號**；`.docx` 同步重出；改前備份 `hermes\backups\dct-prep-20260929-0730\`（md／pdf／docx）。
- **JARVIS 冇行**：07:3x 親核 —— 冇 JARVIS／Electron 進程、8765／8770／8771 唔 listen（只有 Hermes API 8642）→ 冇主動開（SK 用緊機）。
- Git 實況：HEAD `22943c9`（`feature/hermes-alerts-mcp`）、未 push **73**、未 merge **129**、未 commit **5** 檔。
- **08:0x SK go（揀「C 中間版」）**：自我介紹由 15 句 **328 字**砍成 **13 句 284 字**（≈2:35 慢講／2:11 正常）；刪走嘅只有 `walk-in users`／`vibe`／`stuff like that` ＋ 連接詞／重複字（第 8／10／12 條字眼跟 SK 原文）；**13 條中譯全部重寫**。速查重出 **7 頁、sha16 `58d744646acec43f`、0 全形冒號、0 殘留引號**（Word `.docx` 同步）；親眼睇 p2／p3（無重疊、無孤兒標題、中譯對齊）。改前 md 存底 `hermes\backups\dct-prep-20260929-0730\…pre-intro-trim`。
- **08:1x SK 答「a」＝揀 A**：第 6 條 `the next project — China Mobile International` → **`the next project at China Mobile International`**（`that under China` 唔通 —— that 後面要動詞；中譯跟改為「（China Mobile International）」）。順手修兩個殘留數字：封面 `18 題` → **13 條問題**、答題 concept 標題 `唔使背 23 條` → **13 條**（對齊電話問題表實際 13 行）。最終速查 **7 頁、sha16 `58d744646acec43f`、284 字、0 全形冒號、0 殘留引號**（Word 同步）；親眼看過 p1（封面）／p2（自我介紹：每句中譯齊、無重疊、無截字）。改前 md 存底 `…pre-optionA`。
- **09:0x SK「start thinking of how to answer the question」→ 今日唸稿**：寫 `_src\今日唸稿-20260929.md`（14 條題、逐題「問 → 答」、英文＋同行〔中譯〕、每條實測 28–57 秒；取代 9/28 舊唸稿）→ 出 **5 頁** `今日唸稿-20260929.pdf`（sha16 `953bf80767ec5323`、0 全形冒號、rc=0、md_leftovers=0；親眼看過 p1／p2 無重疊無截字）。覆蓋 ── 偏好題（**改寫：唔再講 panic**，Mike 話最傷）、換件題、安全題、方案比較題、犯錯題（四步）、跨 team 題、DC 日常、學習題（加「AI 收集但自己真機核實」）、衝突題、先鋒題、Troubleshooting＋換記憶體真例子、網絡題、反問 3 條、開場 checklist。⚠️ 界線已寫入檔尾：換件／安全／方案比較／先鋒＝「我會咁做」框架，唔好講成做過；犯錯題同換記憶體例子＝真事。
- **09:2x Copilot 自我介紹稿核對＋吸收（SK 交 `from copilot`）**：4 點建議 → **採用 3、唔採用 1**。
 - 採用 ── ① `I wasn't familiar with the environment` → **`I had to learn the environment quickly`**（正面化）② 刪 `AI coding`（留住 Linux／scripting／Java）③ 時態 `it is my own decision` → **`it was`**；④ 順手 `fully recharged` → **`After a short break, I'm ready for the next step`**（避 burnout 聯想）。
 - **唔採用 ── Copilot 寫 `the HKEX project` 簡寫**（撞 Mike 教練規則「唔好講 CMI／HKEX 簡寫」＋速查紅線）。
 - **SK 指示 09-29 ── 名一律出全名**：HKMU → **Hong Kong Metropolitan University**、HKEX → **Hong Kong Exchange**、CMI → **China Mobile International**；開場句 → `I'm Chan Ka Hei — you can call me Andrew.`
 - 數字核實（Hermes 親量）── Copilot 建議版實際 **258 字 ≈2:21 慢講**（佢claim 2 分鐘）；佢個「90 秒後備版」實際 **101 字 ≈55 秒**。吸收後現稿 **281 字 ≈2:33 慢講／2:10 正常**。
 - 出檔 ── 速查 **7 頁、sha16 `23cff8f95973df3d`、0 全形冒號、0 殘留引號**（PDF＋Word 同步）；親眼看過 p2（自我介紹：全名／正面化／時態全部改好、無重疊無截字）。改前 md 存底 `hermes\backups\dct-prep-20260929-0730\…pre-copilot-absorb`。
- **09:4x SK 決定用 A（Copilot 完整版）**：自我介紹由我哋 13 句版**整段換成 Copilot 9 段版**（263 字、17 句、≈2:23 慢講／2:01 正常）；名一律全名（HKMU→Hong Kong Metropolitan University、HKEX→Hong Kong Exchange）。SK 指「句子與句子之間缺乏連接」係講**我哋自己嗰版**（唔係 Copilot）。
 - 17 句中譯全部重寫；另加兩條提示 —— ① 第 1 段同「開場句」重複（開場講咗名就由第 2 段開始）② Copilot 版冇 `my own decision`，被追問「自己走定被裁」時補 `It was my own decision. The shifts were fine — it was the commute.`
 - 出檔 ── 速查 **7 頁、sha16 `23cff8f95973df3d`、0 全形冒號、0 殘留引號**（PDF＋Word 同步）；親眼看過 p2（Copilot 版 9 段連中譯、無重疊無截字）。改前 md 存底 `…pre-copilot-A`。
 - 備用 ── 我另備一個「加連接詞版」（11 段 274 字 ≈2:30 慢講，例 `There I… and that is where…`／`Later…, where I…`），SK 未要。
- **09:5x review 後 SK 只准改兩樣（「just review」→ 逐條裁決）**：① 離職段加返 `it was my own decision` ＋「three to four hours a day」② 抽象句 `the clear focus on operational quality` 換返具體 `you can see whether it has been done properly`。
 - **SK 明確唔改** —— ② 公司關係（佢認為寫咗 `project` 就冇問題）③ 職銜（同 CV 一樣）⑤ Level 2／incident 例子（「no time」→ 用返唸稿第 5、11 題嘅真例子）⑥ 美式／英式拼寫（「I just speak it, so I don't care」）。
 - 現稿 **275 字 ≈2:30 慢講／2:06 正常**；速查 **7 頁、sha16 `23cff8f95973df3d`、0 全形冒號、0 殘留引號**（PDF＋Word 同步）；親眼看過 p2（無重疊／無截字）。改前 md 存底 `…pre-review-fixes`。

## 今日完成（2026-09-28）
- jarvis-pc 當日 commit 1 個（最新：6d8e50c docs(handoff): number-verification pass on CS2 spike (L3 mis-r）
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 68 個 commit（未 push）

- 09-28 06:5x 重開機後覆核（SK「read hand off」）：HUD 0.4.13 自動起＋`/health` ok；Tier 1 registry 四個值仍在；git 實況 ＝ 未 push **68**／未 merge **124**（STATE 舊寫 43／99 已改）；反方 R1 報告喺 subagent session 搵返（11.3k 字）
- 09-28 16:0x 面試資料收口 —— 單一檔 `MS_DCT_Prep\面試一份-中英對照.pdf`（**18 頁**＝Part 1 面試中速查（10 秒 checklist／開場／要唔要表／8 條核心答案／反問／紅線／流程）＋Part 2 完整答案（自我介紹／Elena 安全／Dhaval 文化／Owen 技術／尖問題／技術速記）；sha16 `35669005fae65a22`）。過時段（§1 重點、Mike 場已問紀錄、已用反問、舊 19 頁版）歸 `archive\20260928-*`；教練通話逐字稿／情報摘要／重點筆記（PDF 3 頁）另存。面試日檔案變動已備份 `backups\*.20260928-16??.bak`。
- 09-28 12:1x–13:4x 讀 Mike 場錄影（`Videos\2026-09-28 11-25-07.mp4`，48:59）→ 本機 ASR（SenseVoice 98 塊＋whisper 三窗口核對）→ 交付 `第二輪面試-20260928-逐字稿.md`（41 KB）＋`…-情報摘要.md`＋表情影格圖；當時 pack 14→16 頁（sha16 `08b654c28583f58e`；備份 `backups\*.20260928-1320.bak`）：新增偏好題／學習法／先鋒題答案、proxy 一句、每場針對性反問、9/28 流程情報、⏱30–45 秒紀律、微笑 0/10 實測
- 09-28 14:3x–15:1x 教練通話（`Videos\2026-09-28 14-31-29.mp4`，28:44；Mike 打嚟）→ 本機 ASR（58 塊＋whisper 三窗口核對）→ 交付 `MS_DCT_Prep\教練通話-20260928-1431-逐字稿.md`＋`…-情報摘要.md`＋**`Copilot-註記-20260928.md`（SK 要貼去 Copilot 嘅稿）**；內容含內幕（只留 prep folder，HANDOFF 唔記細節）；下步＝按評分點出即用稿（troubleshooting／換件安全／network 字眼／conflict／accountability）

## 2026-09-27 23:1x–23:5x（Discord；CS2 幀時 spike——「數字核實方」獨立 reviewer 15 項核完）
- **MPO Tier 1 已覆核生效**：本機 **23:07:17** 重開機；`OverlayTestMode=5`／`TdrDelay=20`／`TdrDdiDelay=30`／`HwSchMode=2` 全部 Hermes 親讀 registry 確認（23:4x）。watchdog `4dfef80822b3` 之後無新事件。
- **數字核實（15 項，全唯讀親跑）＝可重現 6／對唔上 7／未能驗 2**。報告 `Documents\PC_Troubleshoot\cs2-perf\NUMBERCHECK-2026-09-27.md`（每項定義＋命令＋原始輸出；原始輸出在 `%TEMP%\verify_*_out.txt`、`%TEMP%\vcache3_run*.txt`）。
- **更正 ①（推翻舊結論）**：「兩邊都冇 96MB L3 平台期」**重現唔到**。`probe_vcache2.ps1` 自帶 verdict：`CPU 0 = 41.5ns／157cyc「L3-resident => V-Cache CCD」`、`CPU 16 = 96.2ns／538cyc「DRAM-bound」`；probe_vcache3 重跑 3 次一致（CPU0 到 96MB 仍 267cyc、128MB 才跳 313–406cyc；CPU16 由 16MB 起 75–105ns 平線）。⚠️ cycles 欄係 WMI 時脈推算（同一核 3,360–5,590MHz）→ 誤差 ±40%，**只用 ns 落結論** → 建議獨立再跑一次才當定論。
- **更正 ②**：`L3 = 192MB` 係**已知誤報**，成因指向 VBS（本機 `VirtualizationBasedSecurityStatus=running`、HVCI=0）；真值 **128MB ＝ 2×32＋64 V-Cache**（本機 Win32_CacheMemory L1 1280KB／L2 16MB／L3 128MB 同 AMD 官方 spec 完全一致）。來源：memtest86+ issue #401、InstLatX64（HotHardware 引）、Tom's Hardware 同串實測「開 VBS→2×96MB」。
- **更正 ③**：副螢幕**唔係內顯推**。三個獨立來源都指兩隻 mon 都喺 5090：`QueryDisplayConfig` 兩條 active path 同一個 adapter LUID；`EnumDisplayDevices` 兩個貼桌面 DISPLAY 都 `VEN_10DE`；兩個 monitor device 嘅 `DEVPKEY_Device_Parent = PCI\VEN_10DE&DEV_2B85`（無任何 monitor 掛 `VEN_1002`）。真值：G27Q 2560x1440@143.97 ＋ AOC 27G2G4 **直立 1080x1920@144**；AMD iGPU 冇 active mode（`EnumDisplaySettingsEx` FAILED）。⚠️ `Win32_VideoController` 對 AMD 報「1920x1080@144」係無接螢幕嘅 adapter 欄位，唔可以當證據。
- **其他數字更正**：`CPMINCORES/CPMAXCORES/CPCONCURRENCY` **唔係查唔到**——`powercfg /qh` 查到（**100%／100%／97%**＝明示停咗 core parking）；`Children` = **115 個 subkey**（唔係 0，ValueCount=0）；`AmdPPM`（amdppm.sys，Running）存在；steamwebhelper **8**（唔係 16）；**GPU-Z／AweSun 冇行**、AnyDesk 2 行緊、HWINFO 1 行緊；DXCache 現值 **275.6MB／39 檔**（全部 `.nvph`）。
- **CL38（SK 報，快問快答）**：DDR5-6000 CL38 = **12.67ns**（CL30=10.00／CL36=12.00／CL40=13.33）；同 28.5ms 差 **225 萬倍** → 確認 CL 唔係 28.5ms spike 成因（成因維持 GPU 掉驅動：7 日內 `nvlddmkm 153 × 54`）。SPD 只報 `PartNumber=UD5-6000`（無型號）、WMI 讀唔到時序 → CL38 未能獨立核；`ConfiguredClockSpeed=6000` ✓ EXPO 生效。
- **未能驗 2 項**：① LPI 0-15／16-31 = 294%／876%（CS2 冇行；我 idle 量 4 次：132/218、140/312、55/411、80/299）② cs2 有冇注入 `gameoverlayrenderer64.dll`（cs2 冇行）。
- **未回收**：反方 reviewer R1（LD1–LD6 逐條存活/死）未返 → 三段式（反方→正方→中立裁判）未出。

## 今日完成（2026-09-27）
- Hermes 記憶上限：`memory.memory_char_limit` 4,000 → **10,000**（config 備份 `hermes\backups\memlimit-20260927-113744\`；`hermes config set` 刪走嘅檔尾註解已還原，diff 除 key 外只此一項）。MEMORY **60 → 52 條**（合併重複：路徑／git／packai 資料真相／查證／玩家文字／內容規則；零刪規則，3,993 字）；USER 1,847 字（上限已加至 4,000）。
- 系統＋流程審計（SK 要求，based on 抖音吸收）：`%LOCALAPPDATA%\hermes\media_import\2026-09-27-system-workflow-audit.md`——**4 週吸收 plan 只有 09-07 落地**；根因＝content-absorption P5 只 grep vault（已吸收內容），**冇 grep 舊 improve-plan**（未決提案）＋冇有效期；vault 230 note 有 0 次調動（README 自訂 2–3 週標準已到期）；＋6 件系統積壓（memory 99%、state.db 755MB、119 commit 未 merge、4 個死 cron、vault／AI_Studio 冇 git、5090 .reg 未裝）。
- HoloMat 影片（`youtu.be/Yrj8bTTsQ2I`）吸收：HUD 插件化／app carousel **記入 REMAINING_WORK「Content 吸收——HoloMat」H1**（SK：將來做）。
- SK 決定（C 組）：**C2 唔做大手術**（實測 VACUUM 只省 2.9 MB、jarvis-* 只 1.8 MB；已做 wal_checkpoint，WAL 7.9→0 MB）；**C4** 刪 3 個死 cron（bglaunch-idle-test／sidequest-xianyu／packai-slice1），`mc-mod-jar-guard` 留 paused；**C5 iii ✅** vault＋AI_Studio 加 git ＋ **私有 repo `skps00/hermes-vault`／`skps00/ai-studio`** ＋ 每日 auto commit（cron `2fb53e441e91` `docs_autocommit.py`，已實測 push 成功）；**C6 暫時唔做**（5090 `.reg` 未套用）；**C7 ✅** 新 cron `808f043e8746` `vault-surface-weekly`（週六 10:00，推 3 條相關筆記＋記 `vault_usage.log`，4 週後決定 vault 去留）；**C3** 等 SK 做 Slice 1 實測先（未 merge，119 commit 留分支）。
- Hermes 記憶：`memory_char_limit` 4,000 → **10,000**、`user_char_limit` 2,000 → **4,000**（config 備份 `backups\memlimit-20260927-113744\`；兩次 `hermes config set` 後都已還原檔尾註解，337 行）。
- A 組：`content-absorption` P5 加「未決提案 loop」（grep 舊 plan＋單一清單＋有效期 7 日／4 週＋EXPIRED）＋新建 `media_import\PENDING_PROPOSALS.md`（15 待決／6 已落地）。
- C7 煙霧測試 ✅（11:57 手動觸發 `vault-surface-weekly`）：job 正常跑（113s）、推咗 3 條相關筆記（`7465` vault/備份、`1426` 工具可靠性、`95587` token 成本）、`media_import\vault_usage.log` 已寫入 3 行（Hermes 親核 log＋3 個 note 檔都存在）；下次自動 2026-10-03 10:00。
- jarvis-pc 當日無新 commit
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 63 個 commit（未 push）
- **CS2 幀時 spike 調查（Discord，22:0x–22:3x）**：實測你部機 fps_max=1000、G-Sync 停用、無邊框、HAGS 開、MPO **未停用**、DXCache **11GB**、只有 Steam overlay 注入 cs2；Valve 官方 FAQ（help.steampowered 418E-7A04-B0DA-9032）明講「幀率高於刷新率→輕微卡頓」＋官方建議 G-Sync+V-Sync+Reflex；SK 選 450+ FPS 路線。新工具 `Documents\PC_Troubleshoot\cs2-perf\`（`cs2_ccd_pin.ps1`／`probe_clock.ps1`／`probe_vcache3.ps1`／README）。**未解**：CS2（LPI 16-31）memory latency 異常（4MB 就上 229 cyc、16MB 上 512 cyc，兩邊都冇 9950X3D 應有嘅 96MB L3 平台期；方法論已用 L2/L3 台階驗證）→ **CPU Sets pin 唔做**（證實唔到 V-Cache CCD ＋ Game Mode／anti-cheat 衝突風險）。**已做**：DXCache 清 10.31GB（C 碟 305→315GB 可用）。**未做**：MPO/TDR（需 SK double-click `Desktop\5090-tier1-fix.reg`＋重啟，Hermes 冇 admin）、Steam overlay 關（SK 3 個掣）、MSAA 4x→2x（只可遊戲內改，`cs2_video.txt` 已證實係 2026-02 過時檔）。

## 2026-09-26 19:4x（Discord；**Copilot 第 6 份提醒核對 → 加 3 樣**，PDF 仍 14 頁）
- **核對結果**：Copilot 8 個提醒 **同現稿零衝突**（5 條已覆蓋 —— 技術題唔好估／Safety 行先／HKEX 故事／ownership 主動句／錯事要 growth，全部有原文位）。用佢個機率表逐條掃 —— 10 條高機率題我哋有 9 條，**唯一缺 `Why should we hire you?`**。
- **加 3 樣（SK `go` 2026-09-26）**：① §3.1 尾新增 `Why should we hire you?`（4 點、≈105 詞／≈40 秒；唔重複 `good fit` 嗰條講法）② §1「講嘢方式」加「**慢少少**」—— 每點之間停半秒、唔好一分鐘衝完 ③ 離職題加收口句 `And the work was never the reason I left — the distance was.`（拆 Copilot 講嗰個疑慮「微軟辛苦你會唔會又走」）＋§3.5「點解離開」row 加追問補句。
- **親核（Hermes 親跑）**：`build_pdf.py` rc=0、**14 頁**、`md_leftovers=0`、問題 **38 → 39**、**全形冒號 0／半形 11（全部時間碼）**、8 條新字串全部在 PDF、render p2（慢少少）＋p6（新題喺框外、4 點喺框內）親眼睇過（無重疊、無孤兒標題）。sha256 頭 16 ＝ `636d585d71e3b6d5`。備份 `hermes\backups\dct-prep-20260926-193819\`（改前 md／pdf／build_pdf.py）。
- **未變**：Copilot「唔好黑 SELL 前公司」嘅做法同現稿一致（車程只講一次、唔埋怨）；佢建議「所有題拉返 Safety」唔做全稿改寫（怕變成口號堆砌，Elena／Owen 兩場已覆蓋）。

## 2026-09-26 10:2x（Discord；**DCT 稿大瘦身：18 頁 → 14 頁「重點筆記」** ＋ 9/9 第一輪轉錄）
- **第一輪（9/9）轉錄落地**（本機 SenseVoiceSmall 30s 分塊 ＋ faster-whisper small 交叉核，**零上傳**）：`MS_DCT_Prep\第一輪面試-20260909-逐字稿.md`（53 段，26:04）＋`第一輪面試-20260909-情報摘要.md`。**內容**：電話篩選、hiring manager 親見；問咗 5 條（自我介紹／DC 日常／**WSA（跨中心調動＋24h＋standby 要幾鐘內返，佢講明「must」）**／同事唔得閒情境題／考證書 challenge）；佢親口講 panel＝幾個唔同部門甚至唔同國家 manager、得一個位、HR 俾 competency＋文化 material、**要預備普通話**；佢主動俾嘅重點＝**主動性／own 自己**（主動搵資料問人；資源係公司畀、**ownership 喺員工**、要 upgrade 自己）、**DC 工作重複（365 日一樣）→ 分別在於點 optimize**、微軟 insist growth。
- **SK 指示（同一 session）**：唔要百科 —— **只要「重點＋筆記＋自我介紹」**；刪術語表／09-22 通話補充／普通話玩笑／對手情報／LinkedIn 提示／「點用」句／官方文化附錄（改**濃縮重點**）／面試日 checklist；技術速記**改 point form**。
- **實際改動**：`MS_DCT_面試一份.md` 62,876 → 48,041 bytes（9 個 h2 → 3 個）；結構＝§1 重點（場次表／佢哋睇重咩／文化濃縮／唔好提及／卡住點算／講嘢方式）＋§2 自我介紹（段落照讀）＋§3 筆記（3.1–3.4 逐場問答＋3.5 尖問題＋3.6 反問＋3.7 技術速記 point form）。**新增 1 條答案**：「份工重複，你點保持成長」（manager 9/9 親口提過）。順手修 markdown 坑（`**標題**` 後要空行，否則 bullet 被吸成段落）＋CSS 微調。
- **第三輪修改（SK 再指示）**：① **自我介紹由段落改成「超詳細列點版」**（19 點：開場／學歷＋圖書館／PrimeTech→HKEX／CMI／離職／現況＋收句，每點英文句＋細字中文、段落標時間），另加「替代開場句」2 句（避免 4 場一字不改）② 開場句 `Sure — thanks for making the time.` 依據＝SK 9/9 第一輪自己講嘅「多謝你抽時間嚟見我」（逐字稿 01:30），非新發明。
- **第四輪修改（SK 再指示）**：SK 指出**「：」講唔出口** → **全份 PDF 嘅全形冒號清零**（改「 —— 」當停頓；cover 都改埋）；保留英文句內嘅半形 `:`（佢係英文標點，讀出嚟就係停頓）。連帶修：`**標籤** ——` 前後空格、`1. 學歷＋第一份工（圖書館…）` 標題內冒號、`第三（…另一角度 —— 靠記錄，唔靠記憶）`。
- **第五輪（SK「fix it」）**：連**英文句內嘅半形 `:` 都清埋**（23 個 → `—`）；連帶修 37 行「兩個長破折號太近」嘅讀感（前面嗰個改逗號）；**PDF 內冒號只剩時間碼**（11:30 等 11 個，唔改）。
- **親核（第五輪後）**：14 頁、`md_leftovers=0`、PDF 內**全形冒號 = 0、半形 = 11（全部時間）**、38 條問題全在、render p4 親眼睇過（英句＋中文對照讀得順）；sha256 頭 16 ＝ `e7de8172b3415f95`。
- ⚠️ **Markdown 坑（今日中兩次）**：`**純標題**` 落一行直接跟 `- ` bullet → python-markdown **唔會 render 成清單**，會變「文字＋- 」一大段 → **標題後必須加空行**。已寫入本檔備忘（下次改 PDF 稿先掃一次）。
- **第二輪修改（SK 再指示）**：① **官方文化改中英對照**（英文原句＋細字中文，唔要附錄）② SK 確認 **9/9 電話篩選嘅「阿 Mi」＝9/28 場 Mike（佢舊老闆）** → §1 表＋新增「Mike 場特別注意」：**同一個人已聽過你 5 條答案 → 同一口徑、加深度、唔加新事實** ③ CSS：blockquote 改可斷頁（每點唔斷）→ 頁數由 18 收返 **14**。
- **親核**：`build_pdf.py` rc=0、**14 頁**、`md_leftovers=0`、**38 條問題（35 問答＋3 反問）全部在 PDF**、中文對照 **162 條**、自我介紹 19 點、render p1／p2／p3／p4／p14 親眼睇過（無重疊、無孤兒標題）；sha256 頭 16 ＝ `e7de8172b3415f95`。備份 `hermes\backups\dct-prep-20260926-102452\`（改前 md／pdf／build_pdf.py）。
- ✅ **已解決**：阿 Mi＝Mike（SK 2026-09-26 親口確認）；`第一輪面試-20260909-情報摘要.md` 已同步更新。


## 今日完成（2026-09-26）
- jarvis-pc 當日無新 commit
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 57 個 commit（未 push）

## 2026-09-25 18:3x（Discord；DCT 稿事實核實收口 ＋ 鍵盤 Win/Alt 診斷）
- **DCT 事實核實（SK 親口逐條答）**：① HKEX 開錯單＋重複單＝真（主答案）② mistake 第二／第三選擇由「電源故障／插錯電源線」**改正為真事**：換 RAM → 拆晒線拉機出嚟 → 復原插錯一個位 → 靠拔線前影相自己發現 → 零影響 → **主管（supervisor，唔係 OM）**就喺旁邊即刻上報 ③ **另一單**：OM 叫開單＋持續檢查系統 → 獨立成 Owen 場新題「忙緊時收到急件 ticket」，兩者唔可以混 ④ Copilot「保養次序分歧」唔存在（SK 從未做保養）→ 保留通用答法 ⑤ 換件過程冇同同事分歧 ⑥「new center」＝ CMI 新項目／新場 → 入自我介紹＋good fit（同時剪 17 個贅字，自我介紹淨 +6 詞）。
- **SK 規則（已入稿尾附錄）**：情境題可以用通用答法 **cover**，但**唔可以講成真實發生過**；真係冇就照實講。
- **收口**：P3「每條答案撒真數字」SK **決定唔加** → 關閉。PDF **16 頁／39 題／133 點**、sha `c284982b039e7323`（`md_leftovers=0`、問題標題全喺框外、`power fault` 0 命中）。備份 `hermes\backups\dct-prep-20260925-181225\`。
- **未做（等 SK 叫）**：面試前自己出聲練（1.5–2 分鐘自我介紹＋四場題）；模擬 panel 我提過、未叫。
- **Hermes session 寫入失敗（SK 見到『No reply … session storage could not be written』，09-25 18:37）**：錯誤 `run_agent: Session DB append_message failed: … returned NULL without setting an exception` → `reason=session_persistence_failed`（該 turn 中止，user 訊息已為 retry 保存）。**一次性**（全 log 1 次）、**DB 冇壞**（5 個 db integrity_check=ok）、磁碟 309 GB free、`hermes doctor` exit 0（4 項無關警告）、Surfshark 冇隔離、Windows event 18:00–19:00 冇磁碟錯。**上游已知未修**：PR `#85065`／issue `#85079`（contended WAL append 嘅 retry）closed 未 merge、`#98020` salvage 仍 open → 唔存在「升級就冇事」。風險因素：`state.db` **750 MB**（83,839 msgs／714 sessions，FTS 索引）＋當時打緊 CS2。**等 SK 決定**：A 備份→刪舊／jarvis-* session→VACUUM（停 gateway、唔可以打機時做）／B 只 `wal_checkpoint(TRUNCATE)`／C 唔做。
- **鍵盤診斷（順手）**：SK 報 Win/Alt 互換 → Windows 側零 remap（Scancode Map 唔存在、冇 PowerToys/AutoHotkey），真兇＝鍵盤切咗 Mac 模式（`VID_258A&PID_010C`＝AULA F75 同族，USB 自報 "Gaming Keyboard"）→ **Fn+W** 切返 Windows；SK 已修好。已寫入 skill `windows-desktop-automation`。
- **MS 文化資料（SK 要求）**：PDF 加「附錄：Microsoft 文化參考（官方 A 級來源）」—— 四條文化屬性（careers Culture FY26 原文）、三條價值（about/values＋Code Book 原句）、Code Book 金句（know-it-all → learn-it-all、`I don't know — yet`）、Model·Coach·Care、2025–26 CEO blog 三大優先（Security／Quality／AI transformation，SFI／QEI）、CO+I DCT 招聘原文（daily safety briefings／EHS／THA／PPE／near-miss／embodies our culture）、中英對照表、8 個來源。**16 → 18 頁**，sha `4d646fc0ece25e4c`（39 題／133 點仍在）。
- **Skill 更新**：`job-interview-prep` §7h-bis／§7r 加「同一時段 ≠ 同一件事（按角色＋名詞分開）」＋「thin fact 升級要守長度預算」；

## 2026-09-25 10:3x（Discord；SK「go」→ **P1＋P2＋P3 已入稿**，PDF 15 頁）
- 入稿內容：① `Why Microsoft?` 補官方 mission＋200+ data centre＋一個標準 ② `Why DCT — not software?`＋`good fit` 補成長點 ③ 離職／intro 嘅「kept learning」講具體（Linux／scripting／Java side project）④ 薪金句去「我知個 range」→ `I'd rather not guess a range` ⑤ **§4.4 加 3 題**（integrity／同事唔跟程序（附舊老闆「攞份文件出嚟講返個 point」原話）／跨背景同事）⑥ **§4.5 加 2 題**（窗口就完但未做完＝壓力題／用非技術語言解釋 RAID）⑦ §4.6 反問 +2 條＋新增「開場連接句」3 句 ⑧ §3 加 Elena 普通話玩笑＋面試前睇 4 位面試官 LinkedIn＋1 條針對性反問 ⑨ §7 加官方 AI 用法（備試 OK、面試中靠自己）⑩ 去重（`ten minutes`／`rely on`／`improvise on live hardware`）。
- **排版 bug 修好**：markdown 會將緊接 `>` 區塊嘅 `- **問題**` 吸成 blockquote 內嘅巢狀清單（問題標題變咗框內小圓點）→ **問題行前面補一個空行** 就正常；已修 5 處，並用 pymupdf 逐條核 **38 條問題全部喺框外**。
- 親核：`md_leftovers=0`、**15 頁**、38 條問題／128 點／128 條中文對照；sha256 頭 16 ＝ `1821e005a4bb0150`。
- 未做：P3「每條答案撒一個真數字」要 SK 核實數字先做；三個 mistake 版本、幽默句、安全負面清單照原樣（誠實優先）。
- 評審檔：`MS_DCT_Prep\答案評審-多角度-20260925.md`（6 視角＋P1/P2/P3 出處）。

## 2026-09-25 10:0x（Discord；SK「ok, also review it in diff pov」→ **多角度評審（未改稿）**）
- 交付：`MS_DCT_Prep\答案評審-多角度-20260925.md` —— 用 **6 個視角**（A 成長／B 反方面試官／C 官方準則／D 舊老闆 insider／E 表達／F 一致性）逐條評 31 條答案，附建議＋優先序。
- **P1（5 項，等 SK go）**：① Why Microsoft 公司半邊補官方 mission／200+ DC（對齊 §5「50/50」口徑）② `Why DCT — not software` 補成長句（同 SK 指出嘅同一病）③ 離職題「kept learning」講具體（進修＋自己動手＋主動求職）④ **§4.4 加「integrity／誠信」題**（官方 Integrity＋舊老闆「信字」）⑤ §3／§7 加「Elena 場可用普通話開玩笑」＋「面試前睇 4 位面試官背景、準備 1 條反問」。
- **P2（6 項）**：good fit 補成長半句／§4.5 加「非技術語言解釋」＋「壓力題」／§4.4 加「跨背景同事」／換走重複用語／反問加 2 條。**P3（3 項）**：PPE 情境、開場連接句、每條撒真數字（要 SK 核數）。
- 未改稿；HANDOFF 只記評審結果。


## 2026-09-25 09:5x（Discord；SK 審稿：「幾年後」答案唔夠好 → 重寫成**成長版**）
- SK 原話：「that answer is not good enough — MS request us to keep growing, then why I stay in shift?」→ 舊答案（可靠／考 A+Server+／**唔離開實體基建**）聽落似**原地踏步**，同微軟官方 **growth mindset／learn-it-all** 文化撞。
- 重寫：**112 詞 ≈42 秒**、5 點 —— ① 先可靠（baseline）② **reliability 係 floor 唔係 ceiling**：一兩年後學**上一層**（senior 技術員工作／change＋規劃／facility＋網絡點配合）③ 考 A+、Server+ 再上④ **成長唔等於離開機房**（要深、要上一級）⑤ 長遠做**帶新人上手**嗰個。
- 順手修：「長做」題加「**一路學一路升；原地踏步唔啱我**」（Standing still isn't for me）。
- 親核：pymupdf 掃新句全在、`md_leftovers=0`、**13 頁**；英文詞數 112（≈42 秒，符合 Mike 場 30–45 秒）。sha256 頭 16 ＝ `51f3bba4f9d351e8`。
- 未做：其餘答案未用同一角度（成長口徑）逐條掃；SK 未答想唔想。


## 2026-09-25 08:3x（Discord；SK 更正 → §4.1 自我介紹**還原**成原本段落版）
- **做錯再修**：我 08:2x 見 SK 提「point form」→ 將**自我介紹答案**改成 5 點列點（commit `9218903`）；SK 即更正原話：「**I mean question part 改成 point form / self-intro still normal**」→ 我**做多咗，已還原**。
- 還原做法：由備份 `hermes\backups\dct-prep-20260925-082719\MS_DCT_面試一份.md` copy 返（一次過覆蓋我 3 處改動：§4.1 5 點列點／附錄 09-25 修正行／「點用」句）→ 重跑 `build_pdf.py`。
- 親核（pymupdf 親跑）：PDF **10 頁**、`md_leftovers=0`、**抽出文字同改前 PDF（`pdf-before-pointform-intro.pdf`）逐字相同**（sha 唔同只係 PDF 內嵌時間）；sha256 頭 16 ＝ `e2651f8fc5d1a163`（636,698 bytes、08:30）；問題列點＋中文對照抽樣仍在。
- 現行版面（＝SK 想要）：**問題＝列點＋中英對照**；**自我介紹＝原本段落版（327 詞 ≈2 分鐘）**；其餘 27 條答案段落、30–60 秒。

## 2026-09-25 08:3x（同場再更正；**§4.2–§4.5 答案全部改列點**，supersedes 上一段尾句）
- SK 最終原話：「**no, I mean the question's answer use point form**」→ 要嘅係**每條問題嘅答案**列點；**自我介紹唔改**（維持段落）。
- 改動：§4.2–§4.5 **28 條答案＋mistake 題第二／第三選擇**，由段落改成 **blockquote 內列點（共 97 點）**；**內容零刪減**（詞級 diff：2114→2068 詞，差異全部係標籤字，例「At HKEX」→「What happened at HKEX」）。問題維持列點＋中英對照。
- 頁數控制：改完最初 **11 頁** → CSS 壓（blockquote 內 list margin 1.5pt／0.7pt、`hr` 12→9pt、blockquote 10.8pt/1.6→10.45pt/1.52）→ **10 頁**（維持原本預算）。
- 親核：pymupdf 掃 29 條問題全在、自我介紹仍段落、`md_leftovers=0`、render p2／p4／p6 睇過（sub-bullet 對齊、無重疊、無孤兒標題）；sha256 頭 16 ＝ `c19ec9621dad8965`（719,813 bytes、10 頁）。

## 2026-09-25 08:4x（Discord；DCT 答案加**中英對照**（SK 選 A）＋**轉錄 09-22 兩通舊老闆通話**）
- **PDF（SK 選 A）**：答案 97 點每點下面加**細字中文對照**（`.zh` span、9pt/1.26 灰）；CSS 再收緊（`hr` 7.5pt、blockquote padding 3.5/9pt、h3 6.5pt）→ **12 頁**、`md_leftovers=0`、末頁 1,478 字（無空洞頁）。親核：**97 條中文全部在 PDF 內**、29 條問題仍在、自我介紹仍段落、render p4 睇過（中文字細一級、唔搶眼）。sha256 頭 16 ＝ `01f9720fe2a8c611`。
- **轉錄（SK 指定）**：`Videos\2026-09-22 19-00-38.mp4`（23:22）＋`19-55-18.mp4`（19:32）→ ffmpeg 16k mono → **SenseVoiceSmall 逐 30s**（47＋40 段、0 錯誤）→ **faster-whisper small 交叉核**（14:30–20:30／06:30–10:30；whisper 用 `language=yue` 會回空 → 要 `language=None`，已記入 skill 待 patch）。**零上傳**；temp `seg_*.wav` 已清。
- **交付**：`MS_DCT_Prep\舊老闆通話-20260922-情報摘要.md`（A–J 段：安排／心態／面試官風格／**安全情境示範**／回答方式／準備策略／三大評分原則／**對手情報**／文化待遇／**6 條建議改動**）＋2 份逐字稿。
- **最重要情報**：① 安全情境＝**先帶所有人離場 → 報 facility（唔係 manager）→ 等 → 負責人確認先入返去**；② **唔清楚就要問清，唔准 take assumption**；③ 見 server 燈要**記住邊部**（天花板／地下都有 label）；④ 對手 3 個都好「淡定＋presentable」→ SK 要靠**幽默＋好奇心＋speak up** 拉分；⑤ 最終二選一由 manager 揀；⑥ **HR email SK 未覆，要補**。
- **未改稿**：上述 6 條改動**未寫入** `MS_DCT_面試一份.md`／PDF，等 SK 一句 go。

## 2026-09-25 09:0x（Discord；SK「go」→ **09-22 通話情報寫入稿**，PDF 13 頁）
- SK 補一句：文化情報要**做研究**（佢之前傳過嘅 link ＝ `careers.microsoft.com/v2/global/en/hiring-tips.html`）。用官方來源核實（**A 級**）：`microsoft.com/en-us/about/values`（Respect／Integrity／Accountability）、官方 **Trust Code** PDF（文化五項：Growth Mindset／Customer Obsessed／One Microsoft／Diverse & Inclusive／Making a Difference）、`news.microsoft.com/codebook`、careers「How we hire」（「We look for respect, integrity, accountability, and growth mindset」＋2–4 場、每場最多一小時、要具體例子）＋官方 Interview tips 欄目（**Do your research／Know our competencies／Accelerate our culture／Be yourself／Demonstrate your thinking and curiosity／Be specific**）。
- **改咗 6 樣**：① §4.3 新增響警號情境題（5 點＋舊老闆紅框示範）② §4.5 新增 server 紅燈題（記住機櫃／位置，唔掃全場）③ §3 加面試官風格（Smile is important）＋對手情報＋二選一機制＋HR email（**SK 09-25 已覆**）④ §5 加 3 行（文化／升職加薪／警號指引）⑤ §7 加 4 條（傾偈式有次序／speak up／好奇心（官方都寫）／唔准斷估救命句）⑥ §4.6 加一句 clarify 英文句。
- 親核（pymupdf 親跑）：31 條問題＋105 條中文對照全在、`md_leftovers=0`、**13 頁**、無空洞頁（末頁 1,591 字）；render p5／p6 睇過（新題列點對齊、紅框提示正常、無重疊）。sha256 頭 16 ＝ `ab7e8a440ff8c3d1`；**09:4x 再加改動（HR email 已覆）→ `53dd9144c6d4d127`**。
- 備份：`hermes\backups\dct-prep-20260925-082719\`（另有 `pdf-before-zh-gloss.pdf`／`pdf-before-pointform-intro.pdf`）。

## 今日完成（2026-09-25）
- jarvis-pc 當日 commit 6 個（最新：3bfaacd docs(handoff): session close - STATE rewrite (DCT pack 10p, Sl）
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 44 個 commit（未 push）

## 2026-09-25 00:0x（Discord；SK 指示 §4 問題改「列點＋中英對照」，PDF 仍 9 頁）
- SK 指示：§4 **問題部分**改成**列點（point form）＋中英對照**，答案唔動。實作：29 條問題由 `### 英文問句` 改成 `- **English?**｜中文`（中文我逐條寫，非機器直譯）＋§4.6 兩條反問同樣處理＋頂部「點用」加一句說明。
- 親核：pymupdf 掃 **29／29 條英文問句**＋**28 條中文對照**全部在（1 條因換行要用 flat 比對）；`md_leftovers=0`、**9 頁**、無 <1000 字頁；render p3／p6 睇過（列點＋答案引用框排版乾淨、無重疊、頁碼 9/9）。
- CSS（為收返 9 頁）：body 10.15pt/1.45、`ul,ol` margin 2/3pt、`li` 1.2pt。試過 `li{break-after:avoid}` 令 p2 出現大片空白 → **已撤回**。
- 備份／還原：同一份 `%LOCALAPPDATA%\hermes\backups\dct-prep-20260924-233903\`（內有改前 md）。PDF sha256 頭 16 ＝ `d280ef2d3d42eab4`（627KB、9 頁）。
- **01:0x SK 交朋友 CV（side task，非 JARVIS）**：Cheung Hei Ming（Timmy）＝2026 IVE 測量學高級文憑（QS stream）＋2024 Yau Lee 實習 → 交付 `Documents\Timmy_QS_Job_Search\`（md＋**5 頁 PDF**＋build_pdf.py＋朋友 CV 副本）。內容：**49 條 JobsDB 即時空缺直連**（AQS 25／見習 8／相鄰職位 15）＋**實測 5 個 post 嘅入職要求**（Techoy／Wise Trend **收 HD**；RLB／中國建築／太古地產**要 Degree**）＋A 級薪酬基準（HKTE：AQS $19–25k）＋CV 6 項修改＋3–5 年路線（top-up degree → HKIS APC；CIC 監工 T1/T2；EMSD 技術員訓練計劃，職學津貼最高 $120,800）。pymupdf 核：5 頁、49 條 unique link、8 個 section 齊、無 <1000 字空洞頁、render 頭／尾頁睇過。
- ⚠️ **browser_exec 三個坑（今次血淚）**：① 程式碼**含中文** → harness stdin UTF-8 解碼失敗（`UnicodeDecodeError 0xa4`）→ 輸出變 `null`；② `js()` 回傳**含 CJK 嘅大字符串**（>~1.5k）→ 同樣輸出 `null`，要 `document.body.innerText.replace(/[^ -~]+/g,' ')` 再 `slice()` 分段；③ `time.sleep()` 同「導航期間 body=null」一樣會斷輸出 → 要 poll `document.body.innerText.length`。JobsDB 可正常抓（無 bot wall）。
- 未變：Copilot 3 個 STAR 故事真偽、CMI cable 事件細節、「new center」解釋 仍待 SK。
- **01:0x SK 問「點解有兩個 JARVIS ONE？」** → 親查 process 清單：**正常**（35732 portable 外層／9192 主進程／10168 GPU／33088 network／35880 renderer，同一個 app）。寫入 STATE 陷阱位，避免下次再誤會。
- **02:0x 追加（同一 side task）**：SK 要「CV 同面試改善建議，先做 research」。已 research（JobsDB《Fresh Grad CV 懶人包》2026-02、HKIS 官網學生會員／認可學歷／QSD APC 卷一範圍、Currie & Brown 早期職位「what we look for」、英國 HBF QS 能力面試框架、apcguide／Robert Half 題庫 C 級）→ 同一份 PDF 加 **§7 CV 逐項改法（13 行前後對照表，含 `[填：數字]` 佔位、唔准作數）**＋**§8 面試準備（形式／3 條必答稿／10 條技術題／STAR 4 個故事／反問／當日 checklist）**；§7→§9 重編，來源分 A/B/C 級。PDF **9 頁**（最後一頁 306 字＝來源清單尾，已濃縮；唔夠位收返 8 頁，老實同 SK 講）。
- **00:3x SK 問「Copilot 個 intro 好啲？」** → 核對後**採用佢嘅骨架**（每份工＋一句得著）、**保留我哋嘅事實同長度**：§4.1 改寫（加「thanks for making the time」開場；HKEX 加「work to someone else's standard, stay accurate under pressure」；CMI 加「hands-on…that's the part I enjoyed most」）。字數 167→168 ＝**講嘅時間一樣（≈60 秒）**，標示改「55–65 秒」。棄用 Copilot 版其餘全部：篇幅 ~330 字（≈2 分鐘，爆我哋 30–60 秒定案）、「took some time to reassess my career goals」（含糊帶過離職，同「老實講自己辭職＋車程」衝突）、「Thank you／I would love the opportunity」（hard sell 收尾）。PDF 9 頁、sha256 頭 16 ＝ `2029d0c14cd9fc4e`。
- **00:5x SK 補：舊老闆講 intro 要 1.5–2 分鐘**（＋「thanks is polite」）→ **撤回上面「唔要長版」嘅判斷**：§4.1 擴寫成 **327 字 ≈ 1.9–2.2 分鐘**（Copilot 骨架＋我哋事實：自己辭職／車程／零 hard sell 收尾「That's what brought me here」），5 段之間加 `>` 分隔（原本 markdown 併成一大塊）。⚠️ 我哋三份逐字稿（9/9 電話、9/18 舊老闆通話）**冇錄到長度呢句** → 依 SK 口述當 A 級證據；**其餘 27 條仍 30–60 秒，等 SK 答係「開場」定「每題」**。PDF **10 頁**（+1 頁；p2 底有空白＝intro 整塊唔斷頁，方便照讀）、sha256 頭 16 ＝ `a69d59df2507e058`。

## 2026-09-24 23:5x（Discord；Copilot 第 5 份 Cheat Sheet → 核對＋吸收 5 條，單一 PDF 收返 9 頁）
- 核對 SK 傳嘅 Copilot Cheat Sheet（存 `MS_DCT_Prep\from_copilot\Cheat_Sheet_copilot_20260924.pdf`）：同 9 頁定案重疊約 6 成，佢係 keyword 骨頭、冇完整句子。
- 吸收 5 條：① **新增 `Why are you a good fit for this role?`**（三格＝圖書館客服／HKEX SOP＋合規／CMI 日常 DC 運維）入 §4.2 Mike 場；② §4.3 安全題加**負面清單**（唔理／等等睇／自己搞掂晒）；③ §4.5 server down 加**硬件指示燈＋讀 log**；④ §4.5 change 失敗加**停後續 change＋評估影響**；⑤ §7 加 **20 個關鍵詞**（四組，明寫「放句入面、唔好背口號」）＋`Validation Check`＝post-execution check、`Change Management`＝PCN 對照。
- 棄用（附錄記低）：靠公司名／規模做賣點（同平實版衝突）、「唔好提車程」、口號式堆砌；檔尾新增**附錄：Copilot 材料核對記錄**（5 條，含 09-22／23／24 前四份）。
- PDF 重建（Hermes 親跑 `build_pdf.py`；hermes venv python 有 markdown＋pymupdf）：10 頁 → **收返 9 頁**（附錄由表格改 bullet＋CSS 邊距微調 10.5/1.5→10.3/1.46）；`md_leftovers=0`、無 <1000 字空洞頁、頁碼 9/9。順手修 3 處「list 前冇空行 → markdown 冇 render 成 bullet」（§1 唔好提及／§7 checklist／軟技巧）。
- 親核：pymupdf 掃 6 條新字串全在（good fit／I don't wait and see／hardware indicators／hold any further changes／Validation Check／附錄）；render p4/p6/p9 睇過無重疊、無亂碼、無半截。
- 備份：`%LOCALAPPDATA%\hermes\backups\dct-prep-20260924-233903\`（3.7M，含改前 md）。還原＝由該資料夾 copy 返 `MS_DCT_面試一份.md`＋`build_pdf.py` 再重建。
- 未變：Copilot 3 個 STAR 故事（HKEX asset／急件／保養次序）仍等 SK 確認真偽；CMI cable 事件細節、「new center」解釋仍待 SK。

## 2026-09-24 14:0x（Discord；SK 交 Copilot《Final Interview Guide》13 頁 → 核對＋吸收 2 題）
- **核對**：Copilot 第三份材料（`MS_DCT_Prep\from_copilot\Final_Interview_Guide_copilot_20260924.txt`，13 頁 quick-memory 版）同我哋三份 PDF **重疊約 85%**，但冇官方術語／9-18 內線／薪金定案／紅線／軟技巧。
- **吸收（已改 2 個 .md）**：30 秒稿 **§3.7 反饋題**、**§4.7 change 失敗題**；照讀稿同步 2 題；guide **附錄 C 加 RCA** ＋ §20 mirror 同步 ＋ 新增 **附錄 D-2**（採用／棄用逐條記錄；同時修走附錄 C 舊「47 頁」字串）。
- **棄用（附錄 D-2 記低）**：generic 面試官分工（**已冇 phone screen 階段**）、含糊離職講法（同「自己辭職＋3-4 小時車程」定案衝突）、hard-sell 收尾句、「每題 1–2 分鐘」（我哋定 30–60 秒）。
- **未證實（等 SK 一句）**：Copilot 三個 STAR 故事（HKEX 資產資料對唔上／急件壓力／保養次序分歧）**未經 SK 確認**，按官方誠實要求**未寫入**任何檔。
- **備份**：`%LOCALAPPDATA%\hermes\backups\dct-prep-20260924-140028\`（14 檔：3 md＋3 pdf＋build_pdf.py 等）。
- **14:2x Copilot 第 4 份（`message.txt` 12 題框架版）**：吸收 1 題（`Walk me through a server deployment.` → 30 秒稿 §4.8＋照讀稿）；guide 新增 **附錄 D-3**；⛔ 棄用「千萬唔好講車程太遠」（同 SK 09-23 親口定案衝突，且 9/28 面試官 Mike＝舊老闆知實情）。
- **SK 答 3 個故事**：`1` HKEX 入錯 asset serial → **冇**（真事係 **CMI 一件同 cable 有關**嘅事，細節待答）；`2` CMI 急件具體個案 → **冇**，但「**仍然收過緊急工單**」＋提及「that was a new center」（待 SK 解釋係咩意思）；`3` 同同事為保養／檢查次序分歧 → **有**（細節待答）。
- **PDF 已重建（Hermes 親跑 headless Chrome；SK 已離開獨佔全螢幕）**：準備包 **59 頁**（56→59：新增附錄 D-2／D-3＋2 題）、照讀稿 **10 頁**、速查卡 **2 頁**（守住 2 頁預算）；pymupdf 核過新內容全部在 PDF 內、`md_leftovers=0`、無 <500 字空洞頁。
- **14:3x SK 指示「全部整理成一份減少頁數」** → 3 份 PDF（59＋10＋2＝71 頁）合併成 **`Microsoft面試-DCT.pdf` 10 頁**（新源檔 `MS_DCT_面試一份.md`；build_pdf.py 重寫成單檔；舊 13 個檔（3 PDF＋研究 md＋逐字稿）搬去 `MS_DCT_Prep\archive\`，**冇刪**）。新檔 7 節＝時間表＋紅線／術語 14 條／逐場情報／照讀答案（4 場＋收場）／尖問題（含薪金 28,000）／技術速記／當日＋軟技巧。Hermes 親核：頁數 10、`md_leftovers=0`、無 <1000 字空洞頁、pymupdf 掃關鍵字（28,000／NDT／LOTO／RCA／4.8 deployment／3.7 feedback／4.7 change fails）全部在；已 render 頁 3 睇過排版正常。備份 `dct-prep-20260924-142614`。
- **16:1x SK 指示（精簡紅線）**：刪走「3 條紅線」整段＋兩處保密提醒（🔒「通水」／「唔好爆我」）→ 改成 4 行「**唔好提及**」清單（30% 數字／前公司壞話／薪金底線／你點知問題）；§3 尾改中性用法句。PDF 仍 **9 頁**，全文已無「保密／通水／紅線／出題」字眼（pymupdf 核）。
- **16:0x SK 指示「只要 45–55 秒完整版 intro」** → §4.1 刪走短版自我介紹，只留完整版（含「輪班冇問題、只係車程」定案句）；全文已無「完整版」引用。PDF 仍 **9 頁**（末頁 1250 字）。備份 `dct-prep-20260924-*`。
- **14:4x 最後修訂**：三個 mistake 版本改成獨立標題＋獨立引言塊（原本被 markdown 併成一塊，難分）＋收緊行距／頁邊 → **單一 PDF 9 頁**（最後一頁 1747 字、無空洞頁）；Hermes 親眼 render 核過 3 頁排版（無重疊／斷字）。
- **14:39 SK 再澄清**：CMI 嗰條線係**電源線（power cord）** → 第二選擇改成「CMI 電源故障 → 維修期間插錯電源線 → 自己即刻發現、修正＋再確認、同主管講、零影響」；第三條（SOP／log 版）標明係同一次故障嘅另一角度。PDF **10 頁**（末頁 1992 字），pymupdf 掃過 6 條關鍵字全在。
- **14:37 SK 補第 2 件真事**：CMI＝「故障由線引起 → 維修期間**插錯線** → 自己即刻發現 → 修正＋自己再確認＋同主管講、零影響」→ 寫入 mistake 題做**第二選擇**（CMI log 版降做第三）。PDF 仍 **10 頁**（末頁 1992 字），pymupdf 掃過新字串在。
- **14:34 SK 補真事細節 → 寫入 mistake 題**：① **HKEX 開錯 ticket／重複開單（兩樣都發生過）**，自己發現、即時同主管講、開返正確單＋取消錯單、零影響 → 已做 **§4.4 主答案**；② CMI「睇 log 太耐」版保留做**第二選擇**。PDF 重建：**10 頁**（CSS 微調拉返一頁，末頁 1636 字、無空洞頁）。
- **待做**：等 SK 補 2 件真事嘅細節（CMI cable 事件／同事次序分歧）＋解釋「new center」；有咗就寫入照讀稿 mistake 題同文化題，再重建 PDF。

## 2026-09-24 17:0x（Discord；SK 報黑屏重開 → 查事件紀錄）
- **事實（唯讀查 Windows 事件紀錄）**：9/24 08:37 開機 → **16:37:16 系統停止回應**（Event 6008 記錄「上次關機非正常」）→ **16:49:24–16:51:18 nvlddmkm event 153 ×54**（XML：`\Device\Video3`／`Error occurred on GPUID: 100`）＋ **Display 4101 ×3**（驅動停止回應後回復）＋ **16:51:05 dwm.exe 崩潰**（WER `AppCrash_dwm.exe`＋`Kernel_141_*`×2＋`Kernel_144_*`＋`Kernel_1b8_*`）→ SK 硬關機 → 16:58:44 重開（Event 41）。
- **背景歷史**：同類 epi 09-04（nvlddmkm ×1）、09-11（4101×2／nvlddmkm×24）、09-24（最嚴重）。**無 WHEA 硬件錯誤**；顯卡 idle 44°C／80W、PCIe Gen5 x16、無 retired pages。
- **環境**：NVIDIA driver **581.42**（2025-09-30 WHQL）、HAGS=2（開）、MPO 未關、TDR 全預設；背景跑 Wallpaper Engine（webwallpaper64 ×8）、Discord ×6、Razer×10、SteelSeries×11、MSI Center×6、HWiNFO（kernel driver）、TRCC。MSI LEDKeeper2 今日亦崩潰 2 次（12:31）。
- **已做（SK 批 ②）**：`hermes\scripts\gpu_incident_watch.py`（no_agent，睇 nvlddmkm／4101／41／6008／dwm 崩潰）＋ cron **`4dfef80822b3`**（`*/5 * * * *`，deliver origin，zero-LLM）；自測：baseline 60 條（54×153＋3×4101＋dwm＋41＋6008）入 `state\gpu_incidents.jsonl`，第二次跑靜默。§電源線 SK 已自行檢查過（排除）。
- **17:2x 驅動研究（SK 要「best version」）**：社群共識（C 級）＝出事區間 **580.97+**（SK 581.42 中招）、**591.44** 有報告修好、**610.88** 多處被指穩定、**595.71** 有 5090 專項分析（0.95V cap）；616.56／616.64 有新問題、617.14 只出 2 日。另有 PSU transient 說（SK 已是 1600W ATX3.1 Titanium → 較低可能）。未做任何 driver 動作。**⚠️ 17:5x 修正（第二輪研究）**：**撤回 595.71 首選** —— 595.71 係 595.59 召回後應急版，本身有電壓 cap（<3GHz、最多 -16%）＋**Event 153／黑屏／Kernel-Power 41 重災**；改推 **591.86**（NVIDIA 官方當時叫 rollback 嘅版本＋Reddit 聚合「2026 best balance」，含 CS2 字體扭曲修正）→ 次選 **610.88**；**避開 595.x／616.56-616.86／617.14**。
- **18:0x SK「go」→ 交付 2 件**：① `Desktop\5090-tier1-fix.reg`（MPO off＋TdrDelay 20／TdrDdiDelay 30；等 SK double-click＋重啟）；② 證據包 `Documents\PC_Troubleshoot\5090-證據包.pdf`（4 頁）＋`evidence\`（事件 CSV 30 日、dxdiag、nvidia-smi、watchdog jsonl）。**watchdog 警報路徑實測通過**（模擬新事件 → 正確印出 60 條分組＋GPU 狀態；測試後已還原 state／log）。追加 `Desktop\5090-收集崩潰dump（管理員）.ps1`（WER／LiveKernelReports／Minidump → evidence\admin-dumps，需右鍵管理員執行）。實測：**WER 資料夾 ACL 擋非管理員**、**Windows 已清走全部 .dmp**（LiveKernelReports 0）。
- **17:5x SK 傳單據相（城市科技/City Computer, Shop 69）**：條款**冇寫年期**，只寫「所有貨品原廠保養」＋「五年自攜免費檢查」＋散件 7 天一換一（已過）→ 年期跟原廠（Gigabyte 出貨地區）；要問鋪頭 3 條問題（地區／年期／收唔收代送）。報告 §4.3。
- **17:4x SK 更正：香港買嘅 5090 係水貨** → Gigabyte HK／AORUS 官方條款唔適用；保養年期限於**賣家／代理（Rivia）**寫喺單或盒貼紙（一般 1 年店保）→ 若 1 年＝2026-12 到期。等 SK 睇單；如要送修要備證據包（事件匯出＋WER dump＋錄影）。
- **17:3x SK 報購買日＝2025-12**（卡 2025-01 出廠＝倉底舊貨）→ 3 年保到 **2028-12**、有註冊則 4 年到 2029-12；NVIDIA UEFI 固件工具（修 2025-03 前出貨／Event 0x141）**更值得做**。
- **17:3x SK 質疑「4 年保」→ 已更正（寫入報告 §4）**：Gigabyte **HK 官網標準＝3 年**；4 年係 AORUS 2026 全球延長保固（**要先喺購買後 30 日內註冊**，型號表有 GV-N5090GAMING OC-32GD）；HK 代理 **Rivia** 以盒上保養雷射貼紙為準。等 SK 講購買日＋有無註冊。
- **17:5x 第三輪研究（SK：多平台、唔可以再買 5090）**：報告 `C:\Users\skps9\Documents\PC_Troubleshoot\5090黑屏-研究與行動計畫.md`。**關鍵**：SK 卡 VBIOS＝**98.02.2E.00.D4（2025-01 出廠）**，同款 GV-N5090GAMING OC-32GD 卡主有**完全相同症狀**帖；**NVIDIA GPU UEFI Firmware Tool v2.0** 正修 `Event 0x141` 黑屏（SK WER 就係 Kernel_141）；主板 MSI X870E CARBON BIOS 1.A50（2025-06，落後）；驅動無單一最好（591.86 兩極／595.x 召回＋電壓 cap／616.x 新問題）。行動分 4 級：Tier1 今日（MPO＋TdrDelay＋電源模式＋功耗 95%）、Tier2 固件（NVIDIA UEFI／Gigabyte VBIOS／主板 BIOS／PCIe Gen4）、Tier3 驅動（596.49→610.88）、Tier4 硬件／DP 線／PCH 溫度。
- **MPO 準備好但未生效**：`Desktop\mpo_off.reg`／`mpo_restore.reg` 已寫（HKLM\SOFTWARE\Microsoft\Windows\Dwm\OverlayTestMode=5）；Hermes shell **非 admin** → 要 SK double-click（UAC）。
- **未做（等 SK 批）**：① 檢查 12V-2x6 顯卡電源線（SK 自己關機做）② driver clean install／更新 ③ 關 MPO（OverlayTestMode=5）④ 關 HAGS ⑤ watchdog cron（no_agent）記下次事發前後 60 秒 context。**零改動**，全部唯讀。

## 今日完成（2026-09-24）
- jarvis-pc 當日 commit 1 個（最新：ef9b85e docs(handoff): Slice 1 code written (uncommitted) + self-verif）
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 36 個 commit（未 push）

## 2026-09-24 09:4x（Discord；read handoff：drift 複核，零新工作）
- **STATE 改寫**（原本停喺 09-22 19:0x）：git 三個數分清（未 push 36／未 merge 入 main 92／未 commit 4 檔）、Slice 1 驗收窗口待 SK、packai Slice 1b 未 commit。
- **舊句修正**：09-23 15:0x「JARVIS ONE 保持關閉」→ 已開返（08:38 開機自動行）；舊「未解 ⑨ STAR 數字待補」→ SK 09-22 已提供、3 份 PDF 09-23 11:34 完成。
- **親核證據**：`git rev-list --count origin/同名分支..HEAD`=36、`origin/main..HEAD`=92；8765 `/health` 200 `wake_on=false`；serve.log 今日只一次 model 載入；MC 三檔 sha16 同記錄一致。

## 2026-09-24 00:3x（Discord；session handoff：Slice 1 code 寫好、未 commit 未驗收）
- **做咗**：plan v4（`f7f754e`）→ 經 **cursor-agent** 實作 Slice 1（**4 個檔未 commit**）：`shell_app.py`（新增 `_ensure_control_http` 無條件起 HTTP server ＋ 5 秒 self-probe ＋ 失敗老實寫 `hud_error.log`、唔自動重試；`_ensure_alerts_mcp` 只 gate poller）｜`hud/main.js`（health 改為要 `body.ok===true && service==='jarvis'`；`clampSettingsPatch` 鎖 8765）｜`src/jarvis/settings.py`（clamp 鎖 8765）｜`hud/settings.html`（欄位 readonly ＋ 鎖定提示）。
- **自驗（Hermes 親跑，非照抄 agent）**：`node --check`＋`py_compile` OK；50 個相關測試全過（settings/shell_app/mcp_alerts_http/alert_piper_gate）；`eval_gate --lock` RC=0；diff 逐行對計劃一致。
- **未 commit**（按規矩：驗收通過才 commit）；**patch 存底** `%LOCALAPPDATA%\hermes\backups\jarvis-sidecar-slice1-uncommitted-20260923.patch`（`git apply --check --reverse` 驗證吻合）；還原＝`git checkout -- hud/main.js hud/settings.html src/jarvis/settings.py src/jarvis/shell_app.py`（HEAD `f37b4f4`）。
- **下次做（等 SK 揀窗口）**：① 窗口 1（開 HUD 15–20 分鐘）：行為驗證（`alert_voice=false` spawn serve → 8765 LISTEN）＋驗收 #1–#4／#6／#7／#10 ＋ U1／U2 量測；② 打包換版（skill `scripts\swap_hud_version.ps1`）；③ 窗口 2（HUD 關）：Slice 2 monitor 桶化＋`OFF` 語意＋#8／#9；④ 全套 532 測試 ＋ `eval_gate --all`。
- **SK 未反對＝照建議行嘅 3 條**：`OFF` 語意（HUD 關住唔通知）／`/settings` 解密面常開接受／MCP 工具（含 `jarvis_speak`）恢復可用。
- **披露＋待辦**：① review subagent 曾喺 20:39 寫入 skill `jarvis-hud-electron-editing-pitfalls\\SKILL.md`（超出我唯讀指示，內容同 plan v4 一致、已核）；② skill `cursor-cli-integration` 已補「長 instructions 唔可以當 CLI 參數傳（命令列太長→偽成功 exit 0）」坑；③ `settings.py` 凍結後留低無害多餘 try/except → 下次落 cursor 順手清。

## 今日完成（2026-09-23）
- **側車重啟循環修復：plan v1→v4**（R1 2:8 → R2 4:6 → R3 3:7 → **中立裁判 4:6 裁 `v3_adequate=true`**）；4 條必修（起 server 後 self-probe／凍結 port 8765／驗收 #3#4 加「改值→kill→確認仍 LISTEN」／monitor 加 `OFF` 語意）已入 v4，拆 Slice 1／2。⚠️ **此條寫於 23:0x（當時 code 未改）；23:2x 之後已實作 Slice 1 code，見上一個 section。** 檔 `.hermes\plans\2026-09-23_1500-jarvis-sidecar-restart-loop-fix.md`；commit `3e8bfe8`(v2)→`250b033`(v3)→`f7f754e`(v4)。
- **plan 產出嘅新發現**：① 8765 唔止 health，仲係 Electron 設定視窗嘅讀寫口 → `alert_voice=false` 期間加密欄位顯示成 `dpapi:` 亂碼＋儲存繞過單一 writer；② port 硬編碼**共 6 處**（`main.js:90/573/674`、`hermes\config.yaml:254`、`jarvis_sidecar_health.py:15`、`swap_hud_version.ps1`）→ 裁定**凍結 8765**；③ 更正舊記錄：cron `6a98a79be95f` **只報告、唔會自動救** sidecar；④ 換版真工具＝skill 內 `scripts\swap_hud_version.ps1`（71 行，唔喺 repo）。
- **等 SK 拍板**：驗收窗口 ×2（窗口 1 開 HUD 15–20 分鐘、窗口 2 HUD 關 ≥35 分鐘）＋ 3 條小決定（`OFF` 語意／`/settings` 解密面常開／MCP 工具恢復可用）。
- jarvis-pc 當日 commit 1 個（最新：9b907f9 docs(handoff): STAR 卡改真實資料＋CV 30% 誠信修正（§21））
- 領先 remote 15 個 commit（未 push）

- 本機清理（SK 選 A）：刪註冊表空關聯 `HKCU\...\FileExts\.bak-20260916_093251`（無 UserChoice、未綁 Store）；Startup 舊備份 `Hermes_Gateway.vbs.bak-20260916_093251` 移去 `%LOCALAPPDATA%\hermes\backups\`（sha256 6a4fbd74537f 一致）。還原＝`reg import backups\reg\HKCU-FileExts-.bak-20260916_093251-20260923.reg` ＋ 移返 Startup。開機啟動不受影響。
- 面試準備（Copilot 題庫整合）：SK 提供 Copilot 16 題 → 改寫成 30 秒口語併入 `MS_DCT_Prep\英文口語稿-30秒版.md`（未覆蓋嘅 10 條新題：1.5–1.9／2.4–2.5／3.4–3.6／4.5–4.6）＋guide §20 同步＋cheat sheet 加「8 題必背＋Safety>SOP>Compliance>Technical」；重建 PDF（guide **47 頁**、速查卡 **2 頁**，0 markdown leftovers）。原始版存 `Copilot題庫-16題-原始版-20260923.md`。⚠️ 未照抄兩處：薪金（用舊老闆版 28–29k，唔跟 Copilot 唔講數字）＋`a mistake` 題需 SK 確認真實素材。
- 情報落地（SK 更正）：**面試官出題自己都用 Copilot**（SK 9/23 由老闆轉述）——同舊老闆 9/18 逐字稿 12:30 原話一致（「我哋冇 sample…in-time 會搵 Copilot 幫手做嘢」）→ guide 新增 **§16.4**、30 秒稿頂加註（題目覆蓋以 Copilot 16 題為主線，答案結構用 Safety>SOP>Compliance／STAR(R)）；重建 PDF（guide 頁數見下、速查卡 2 頁）。
- 面試準備修正（SK 答）：**CMI 電源故障事實＝先上報、之後自己查一輪** → 「太遲上報」版作廢，3.4 mistake 題改「自己查太耐／冇邊查邊交證據」版（+ 純假設式 fallback）；重建 PDF（guide 47 頁、速查卡 2 頁）。**薪金題 SK 傾向 B（唔講數字）但未定** → 我建議「B 開場 + 報 28–29k」混合版（檔內現行 1.8），等 SK 一句確認。
- 面試準備（SK 要求）：**所有縮寫要詳細中英對照**（面試係全球公司）→ 新增 `MS_DCT_Prep\術語中英對照表.md`（A 職位流程／B 安全合規／C 硬件機房／D 我哋文件用字；每條＝全寫＋中文＋一句人話＋可直接講嘅英文句）＋併入 guide **附錄 C**（guide 47→**52 頁**；速查卡保持 **2 頁**，加了指向一行）。⚠️ **NDT／PCN 全寫未經確認 → 明確標示唔亂填**。
- 面試材料整理（SK 指示「直接更新兩份 PDF、唔好整咁多檔案」）：PDF 統一成 **兩份**（`Microsoft面試準備包-DCT.pdf` 52 頁、`Microsoft面試速查卡-DCT.pdf` 2 頁，**去日期**）→ 刪舊 4 個 PDF（含重複抄本）＋今日兩個散檔（內容已內嵌 §20／附錄 C）＋html／預覽圖中間產物，共 21 檔（32→13）；`build_pdf.py` 中間 HTML 改寫去 `%TEMP%`。內容已驗證（附錄 C／§16.4／mistake 新版 全在 PDF 內）。
- 面試軟技巧（SK 舊老闆評語：加 joke／笑容／興趣）：我**親手抽 9/9 錄影 9 幀（2:00–26:00）睇表情 → 笑容 0/9、多數望螢幕唔係鏡頭**；已寫入準備包新增 **§22（笑容／幽默／興趣）**＋速查卡新增「😊 3 件事」；PDF＝準備包 **55 頁**、速查卡 **2 頁**（CSS 微調 font 8.5pt/line 1.28 保住 2 頁）。
- 面試決定（SK 授權）：**薪金題定案＝講 28,000 單一數字**（SK 原本想 26–27k，我列舊老闆內線依據：grade 2 約 29k 幾、第一級 23–24k、HR 控制數 → 佢採用建議）。已寫入兩份 PDF（準備包 55 頁、速查卡 2 頁）。「砌機」句改 `I've built my own PCs before`（SK 確認：砌過機，但唔係 5090 嗰部）。下一步＝模擬 panel（我扮 Mike/Elena/Owen 逐題問）。
- 面試風格修正（SK 轉述：示範句 "hard sell"）：§1.1 自我介紹改**平實版**（講做過咩、唔講口號）＋新增「避免 hard sell」對照表（❌ 自我形容 → ✅ 具體事實），並寫入 guide §16.1 第 7 點（老闆原話「唔使黑 sell 自己」）。PDF＝準備包 **56 頁**、速查卡 2 頁。
- 照讀稿（SK：「簡單啲，直接整份稿畀我照住讀」）：新增 `照讀稿-DCT.md` → 第三份 PDF **`Microsoft面試照讀稿-DCT.pdf`（7 頁，大字 13pt、平實版、25 題、含幽默句／救命句）**；build_pdf.py 加 READ_CSS。三份 PDF 定案：準備包 56 頁（全資料）／照讀稿 7 頁（照讀）／速查卡 2 頁（考前 10 分鐘）。
- Copilot 第二輪回覆（`Documents\interview.txt`）核對：**採用**自我介紹階段結構（壓成 45–55 秒完整版）、新題 `Tell me about the HKEX project`、萬用救命句；**棄用**薪金（又係唔講數字，與定案 28,000 衝突）、mistake（與事實不符）、Why Microsoft（hard sell 措辭）→ 準備包新增 **附錄 D** 記錄判斷。PDF：照讀稿 8 頁、準備包 56 頁、速查卡 2 頁。
- 事實修正（SK 澄清）：離開 CMI **唔係合約完結，係 SK 自己辭職**（12 小時班＋來回 3–4 小時車程不可持續）→ 全文改（照讀稿新增 `Why did you leave your last job?` 題、自我介紹結尾／長做題／hard sell 對照表／速查卡尖問題行／guide §17 示範＋附錄 D 加事實修正）；Copilot 嘅 "contract finished" 措辭已標示為與事實不符。PDF：照讀稿 9 頁、準備包 56 頁、速查卡 2 頁。
- 系統診斷（SK：鍵盤打字隨機延遲，打機時更明顯）：實測發現 **TRCC.exe（Thermalright）即時 49% 一核**（已退出）、**Surfshark.AntivirusService 即時 100% 一核**（服務狀態 Stopped 但進程係孤兒；有自我保護 kill 唔到）；`jarvis serve` 亦 100% 一核（待查）。已將兩個 Surfshark 服務設 **Disabled+Stopped**（還原：`%LOCALAPPDATA%\hermes\backups\restore_surfshark_services.ps1`，記錄 surfshark_services_2026-09-23.txt）；⚠️ 孤兒進程要**重啟電腦**才清得走。USB 選擇性暫停＋鍵鼠「允許關閉省電」仍未改（待 SK）。
- 鍵盤隨機延遲：查出**時間線主因 = Microsoft GameInput**（`C:\Program Files\Microsoft GameInput` 建立 2026-09-20，SK 話該日前後才開始；有 4 個進程 = Redist+本體兩份），網上多來源（r/FortniteBR、r/EASportsFC、r/Minecraft）指 GameInput 服務衝突造成輸入延遲。已 UAC elevated **Stop+Disable `GameInputRedistService`／`GameInputSvc`**（驗證 alive=0，可還原：`%LOCALAPPDATA%\hermes\backups\restore_gameinput_services.ps1`，記錄 gameinput_services_2026-09-23.txt）。另 Chrome Remote Desktop `chromoting` 服務 9/22 裝（Running，未動）。剩餘 CPU 食客：TRCC 51%（由排程 `TRCCAppStartup` 啟動）、Discord 33%、`jarvis serve` ~32%。
- 鍵盤延遲續：已 elevated 關 **USB 選擇性暫停**（AC/DC=0）＋對鍵盤 VID_258A／Razer VID_1532 全部介面 ＋ RZVIRTUAL 取消「允許關閉省電」（True→False，14 項驗證）；並 **kill TRCC.exe** 做對照測試（省 51% 一核；散熱器 LCD 會熄，重開 `C:\Program Files\TRCCCAP\TRCC.exe`）。還原：`backups\restore_usb_power_2026-09-23.ps1`（記錄 usb_power_2026-09-23.txt）。SK 反饋：停 GameInput 後「still, but better」。剩餘：SteelSeriesSonar 12%、Discord、`jarvis serve` 29%。

- **MC／packai a+b（09-20）**：plan v3.1 過 review（R3 8:2）→ cursor 實作 → Hermes 親驗（compile RC=0／53 檢查綠／python 124 檔 1 已知紅／5 條負控）→ FTB 沙盒 4 輪真機（世界生成三類 ＋ 必答清單）＋ 跨包 UniversIO 7/7；**code 未 commit，等 SK**。詳 `super_minecraft_AI_player/.hermes/plans/HANDOFF.md`。
- **MC a+b（09-20 後續）**：code review 捉到 P0（gap 判定被 marker 自我命中 ⇒ b 對 a no-op），Hermes 親手 RED→修→NC 紅→還原綠→真機一輪；另修 P1×2、留 P1×4 待辦；docs commit `ae70d74`；**code 未 commit**（等 SK 揀 (1) 只 commit 本批 ／ (2) 累積到版本）。
- **MC a+b（09-4x）**：SK 揀 A → 累積批次 commit `f325c4e`（135 檔，唔 push）；commit 前掃 secrets 全清、runtime `logs/` 故意排除（未入 .gitignore，建議下次加）；UniversIO 最終版 jar 覆核 7/7 全綠。
- **11:1x packai 測試範圍**：新增兩個沙盒（Star Technology／ATM8，皆 1.19.2 Forge）＋登記文件 `docs/TEST_SCOPE.md`；jar `b5ffe2761cea`；遊戲內 smoke 待 Gate 轉 idle。
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


