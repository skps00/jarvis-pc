# HANDOFF — jarvis-pc（狀態區塊 + 逐日 index）

<!-- STATE:BEGIN -->
## 狀態（每次 session 尾／cron **改寫**；新 section 一律加喺本區塊**之下**）

- **目標**：JARVIS ONE（語音／HUD／alerts）穩定收尾 ＋ MC packai（Forge 1.19.2 primary）設定／答案版面／卡片修復落地。計畫書：`.hermes/plans/REMAINING_WORK.md`
- **現狀（2026-09-25 01:1x 改寫；全部 Hermes 親核）**
 - **Git**：HEAD ＝ `ffb1b45`（分支 `feature/hermes-alerts-mcp`）；**未 push 43 個**（比 `origin/同名分支`）、**未 merge 入 main 99 個**（比 `origin/main`）；**未 commit 4 個 code 檔**（Slice 1）。呢三個數會跟下一個 commit 自己變。
 - **JARVIS ONE**：HUD **0.4.13** 行緊（今日 **17:00** 開機自動起，16:58 黑屏重開之後）；8765 `/health` ＝ `ok:true, wake_on:false`；側車 `python -m jarvis serve`（PID 36084）**重啟循環冇再現**（未 commit 嘅 Slice 1 改動已生效）。
 - ⚠️ **一個 app 正常有 4 個同名「JARVIS ONE」進程**（主 9192／GPU 10168／網絡 33088／renderer 35880；portable 解壓到 `%TEMP%`，外層係 `JARVIS-ONE-0.4.13.exe`）→ 唔係重複開 app，**唔好 kill 主進程**（會連 HUD＋側車一齊死）。
 - **Slice 1（側車重啟循環修復）＝ code 寫好、自驗過、未 commit、未換版**：4 檔＝`src/jarvis/shell_app.py`／`hud/main.js`／`src/jarvis/settings.py`／`hud/settings.html`。還原＝`git checkout -- <4 檔>`；patch 存底 `%LOCALAPPDATA%\hermes\backups\jarvis-sidecar-slice1-uncommitted-20260923.patch`。**等 SK 揀驗收窗口**（窗口 1＝開 HUD 15–20 分鐘，驗 #1–#4／#6／#7／#10＋U1／U2；窗口 2＝HUD 關 ≥35 分鐘，驗 #8／#9＋`OFF` 情境）；打包換版（`swap_hud_version.ps1`）夾喺兩窗之間。
 - **5090 黑屏**：今日 **16:37 系統停止回應 → 16:49–16:51 nvlddmkm 153×54＋dwm 崩潰 → 16:58 重開**（同 09-04／09-11 同類）。watchdog cron `4dfef80822b3`（*/5、no_agent）行緊、之後無新事件。**Tier 1 修正未套用**（01:0x 親核：`OverlayTestMode`／`TdrDelay` 機碼唔存在）→ SK double-click `Desktop\5090-tier1-fix.reg`＋重啟即完成（還原 `mpo_restore.reg`）。驅動結論：**591.86**（次選 610.88），避開 595.x／616.5x-616.8x／617.14；另有 NVIDIA GPU UEFI 固件工具 v2.0＋主板 BIOS（1.A50 落後）。報告 `Documents\PC_Troubleshoot\5090黑屏-研究與行動計畫.md`。
 - **MS DCT 面試（Mike 9/28・Elena 9/29 11:00・Dhaval 9/29 12:00・Owen 9/30）**：單一 PDF `Documents\MS_DCT_Prep\Microsoft面試-DCT.pdf` ＝ **14 頁**（**重點筆記版**：重點／自我介紹／筆記；sha256 頭 16 `636d585d71e3b6d5`，09-26 19:3x；舊 18 頁版備份見 backups）＝ **39 條問題，每點有細字中文對照**；自我介紹＝**列點版（19 點，≈2.1 分鐘）**。09-26 19:4x 已吸收 **Copilot 第 6 份**（新增 `Why should we hire you?`／§1「慢少少」／離職題收口句）。**事實核實已收口（09-25 18:3x；09-26 已大瘦身做重點筆記版）**：CMI 事件由「電源故障」改正為真事（換 RAM 拆線、復原插錯一個位、靠影相自己發現、零影響）、主管（supervisor）同 OM 分清、CMI 新項目／新場素材已入自我介紹＋good fit。**P3「撒真數字」SK 決定唔加 → 該項關閉**。
 - **Side task 已完成**：SK 朋友 Timmy（IVE 測量學高級文憑 2026）求職包 `Documents\Timmy_QS_Job_Search\`（9 頁 PDF＋md：49 條 JobsDB 即時空缺＋CV 逐項改法＋QS 面試準備）。
 - **packai（MC 主線）**：MC repo HEAD `013e4ac` 已 push；**Slice 1b 4 檔未 commit**＋**真機 A/B 未跑**。
 - **語音／mic 線 HOLD**（等新 mic）；Hermes `compression.micro_compact=true`（09-22 生效）。
- **唔准郁（硬限制）**
 - 打機／用緊電腦：**零彈窗、零搶焦點**（先讀 `state/sk_activity.json`）；GUI 窗一律第二副螢幕；Chrome 主動開＝`bg_launch.py --minimized`
 - `AGENTS.md` 受保護（要 SK 明確 go）；唔准 `curl|sh`；**HANDOFF 視為可公開 → 唔准入 secrets**
 - packai code **一律經 cursor-agent**；**唔准 `git add -A`**；部署只准用 `mc_mod_deploy_jar.py`（真 instance 唔准自動部署）
 - **語音／mic 線 HOLD**：唔郁 `wake.py`／STT／AEC／聲紋／threshold／mic device；唔叫 SK 測 wake
- **未解（等 SK 決）**：① ~~DCT 三樣待答~~ **已解決（09-25 18:3x）**：HKEX 開錯單＝真；急件 ticket＝另一單（OM 叫開單＋持續檢查）；保養次序分歧＝冇（保留通用答法）；CMI 細節＝換 RAM 插錯線；「new center」＝CMI 新項目／新場 ② **5090 Tier 1 套用**＋驅動／固件／BIOS 決定 ③ **JARVIS Slice 1 驗收窗口 1／2** ④ Slice 1 打包換版 ⑤ **測試隔離 ii 實作**（已批准未開工）⑥ **packai Slice 1b 真機 A/B** ⑦ Slice 1c／Slice 2 正式 plan ⑧ **dev → main 合併**（PR 定直接 merge）
- **下一步（優先序）**：① 5090 Tier 1（打機完 double-click＋重啟，2 分鐘）② DCT 補 STAR／CMI／new center 細節（版面已定：問題＋答案都列點、答案有中文對照）③ JARVIS Slice 1 窗口 → 打包換版 → 窗口 2 ④ 測試隔離 ii（plan → review ≥8:2）⑤ packai Slice 1b 真機 A/B（需 SK idle＋DS 空閒）⑥ dev→main 合併決定
- **歸檔索引**：已完成記錄全部喺 `plans/archive/HANDOFF-2026-09.md`（＋`HANDOFF_2026-08-*.md`）
- **參考段（檔尾）**：陷阱（重溫）／語音·硬體設定（驗證過）
<!-- STATE:END -->

## 今日完成（2026-09-27）
- Hermes 記憶上限：`memory.memory_char_limit` 4,000 → **10,000**（config 備份 `hermes\backups\memlimit-20260927-113744\`；`hermes config set` 刪走嘅檔尾註解已還原，diff 除 key 外只此一項）。MEMORY **60 → 52 條**（合併重複：路徑／git／packai 資料真相／查證／玩家文字／內容規則；零刪規則，3,993 字）；USER 仍 1,847/2,000。
- 系統＋流程審計（SK 要求，based on 抖音吸收）：`%LOCALAPPDATA%\hermes\media_import\2026-09-27-system-workflow-audit.md`——**4 週吸收 plan 只有 09-07 落地**；根因＝content-absorption P5 只 grep vault（已吸收內容），**冇 grep 舊 improve-plan**（未決提案）＋冇有效期；vault 230 note 有 0 次調動（README 自訂 2–3 週標準已到期）；＋6 件系統積壓（memory 99%、state.db 755MB、119 commit 未 merge、4 個死 cron、vault／AI_Studio 冇 git、5090 .reg 未裝）。
- HoloMat 影片（`youtu.be/Yrj8bTTsQ2I`）吸收：HUD 插件化／app carousel **記入 REMAINING_WORK「Content 吸收——HoloMat」H1**（SK：將來做）。
- jarvis-pc 當日無新 commit
- 未 commit 檔案 4 個：hud/main.js, hud/settings.html, src/jarvis/settings.py
- 領先 remote 63 個 commit（未 push）

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
## 2026-09-22 23:1x（Discord；收工前 handoff：STAR 卡改真實資料＋CV 30% 誠信修正）
- **SK 提供 6 條真實數字（口答）**：HKEX 換件「幾次（唔記得）」；CMI＝**電源故障、睇 log、幾日搞好、當時冇 SOP**；圖書館 30%＝**AI 生成、冇量度基礎**（唔可引用）；HKEX 曾幫團隊**定位網絡問題**（無量化）；上手＝**1 星期（有清楚 SOP）**；HKEX 因專案結束、CMI 因 12 小時工時＋3–4 小時車程而離職。
- **交付**：`STAR卡-6張-英文.md` 全 7 張改用真實資料（**刪除 30%**；卡 6 改「假設式」因無真實事件）＋附錄 CV 誠信核對；guide 加 **§21**、修正 §11／§18 → 準備包 **44→43 頁**、速查卡 **2 頁**；速查卡紅線改成「30% 係估算、唔好引用」。
- **待辦（9/23）**：① SK 改 CV 30%（＋自查 FYP 60%／Unreal 40%）② **模擬 panel 開波**（Mike Q1 已出，等 SK 答）③ 補記憶。
## 2026-09-22 22:3x（Discord；MS 面試：Gmail 實錘 9/9 面試官＝Mike Wong＋英文 30 秒口語稿）
- **Gmail 實錘（只讀）**：① 9/9 screen invite 明寫面試官＝**Mike Wong**（9:00–9:30，30 分鐘）→ 証實 9/9「阿 Mi」＝Mike Wong＝舊老闆＝hiring manager＝9/28 第一場（同一人，100% 確定）；② 4 封 invite（9/28 11:30／9/29 11:00／9/29 12:00／9/30 11:00）只有面試官**顯示名**，**冇 email alias** → OSINT 查人工具冇輸入可用（已回覆 SK）。
- **交付**：`MS_DCT_Prep\英文口語稿-30秒版.md`（14 條、每條 22–35 秒、出聲練習用，含開場／收場／後備句）→ guide 加 **§20**，準備包 **39→44 頁**、cheat sheet 保持 **2 頁**（0 空洞頁）。**未 commit** MS_DCT_Prep（非 git repo）。
## 2026-09-22 21:4x（Discord；MS 面試：9/9 首次面試轉錄分析 → 新增卡 7＋統一講法）
- **做法**：轉錄 `Videos\2026-09-09 08-59-28.mp4`（26 分鐘）——**同 hiring manager 嘅 phone screening**（通話由影片 01:30 開始）。同 pipeline：ffmpeg → SenseVoice 逐 30 秒（52 段、0 錯誤）；`asr_chunks.py` 加 `ASR_SRC` 參數（原本 hardcode 舊 wav，已修）。
- **情報**：招聘藍圖＝replacement headcount／1 位 → 佢篩 CV → 首面（9/9）→ 帶期望薪金見大 manager → **panel（幾個 manager、可能外國、問 skill／knowledge／competence）** → HR email 結果＋**發 competence／culture 準備材料**；佢明講**主要用英文**。**評分第一標準＝主動性／ownership**（原話「好多嘢你自己 own」「資源公司有，ownership 在你」）。佢自介「阿 Mi」＋自稱 hiring manager → **極可能＝Mike W.（舊老闆）**。
- **交付**：`MS_DCT_Prep\` 新增 `首次面試-20260909-逐字稿.md`／`分析.md`；guide 加 **§19**＋**§18 加卡 7（主動性）**＋3 句統一講法（離職原因／證書／主動性）→ 準備包 **39 頁**、速查卡 **2 頁**（0 空洞頁）。
## 2026-09-22 21:1x（Discord；MS 面試：模擬題＋示範答案、6 張英文 STAR 卡）
- **交付**：`Documents\MS_DCT_Prep\` 新增 `模擬題與示範答案.md`（四場 × 2 條，英文照背＋中文思路＋後備句）＋`STAR卡-6張-英文.md`（6 張 60–90 秒、含反思句、選卡對照表、待補數字清單）；已併入準備包 **§17／§18**（guide 26→**35 頁**，cheat sheet 保持 **2 頁**；0 孤兒標題、無 <500 字頁）。
- **順手發現（要 SK 留意）**：① CV 顯示圖書館（2023/8–2025/8）同 HKEX（2025/3–7）**時間重疊** → 面試官可能問「同時做兩份？」要預備答案；② 通話提到「表現唔差」嘅候選人＝**MU 同科畢業四年**（HK Metropolitan University）＝同你同校同科 → 有同質競爭者。
## 2026-09-22 20:5x（Discord；MS 面試：舊老闆通話轉錄 → 「逐個面試官會問咩」）
- **做法**：SK 叫 check `Videos\2026-09-18 18-26-51.mp4`（5.95GB、CS2 遊戲中講電話）→ ffmpeg 抽 16k mono 音軌 → 本機 **SenseVoiceSmall（粵語）逐 30 秒切塊**轉錄（109 段、RTF 0.02）＋whisper-small 交叉核對（兩者一致）。**零上傳**。
- **情報（通話 00:00–02:30 原話，兩個引擎互相印證）**：**Elena Yeh（台灣・唯一女・PM）→ 問 Safety＋「點 handle」情境**；**Owen Lee（佢老細、啱啱由 PM 升上去）→ technical：日常作業＋重大 change → 答 Safety／SOP／compliance／冇 spec 要 document＋trace back**；**Dhaval Desai（印度・PM）→ culture 抽象題（用生活例子、唔會問敏感題）**；Mike W.＝打電話嗰位（可能出題人）。另：薪金約 **29k**、grade 2/3（開價 28–29k）、team 12 人、年尾開 2 位。
- **交付**：`Documents\MS_DCT_Prep\`（逐字稿 md 40,778B＋情報摘要＋§16.0；guide **26 頁**、cheat sheet **2 頁**，0 孤兒標題、無空洞頁）。⚠️ 原以為通話由影片 2:00 開始 → 最關鍵情報喺 **00:00–02:30**，已補轉錄。
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


## 2026-09-23 15:0x

- 鍵盤輸入延遲根因**已確認**（兩個獨立原因）：① Surfshark 9/22 09:01 自動更新後 AntivirusService 卡死（服務 Stopped 但進程食 100% 一核）→ 已卸載（重啟後無服務/驅動/進程）；② Microsoft GameInput（9/20 裝、裝咗一套 XInput DLL）→ MSI 已卸載 + 內建 GameInputSvc 已 Disabled。
- 另做：USB 選擇性暫停關（AC/DC 實測 0x0）+ 鍵盤/Razer 6 個介面取消省電（Enable=False）+ TRCC 已 kill（45% 一核，來源＝影片背景／HWiNFO 輪詢）。以上皆有還原腳本於 `%LOCALAPPDATA%\hermes\backups\`。
- **新發現（重大）**：`jarvis serve` 每 ~90 秒被 Electron kill+respawn → 每次重載 1.2GB 模型（serve.log 見 294 次 download 週期；實測 14:34:26→14:35:56→14:37:29→14:38:58）→ 週期性 CPU/IO 尖峰 = SK 打機鍵盤延遲主因。關 JARVIS ONE 後 serve.log 100 秒 +0 bytes；SK 確認打字順返。
- 根因：`hud/main.js:157-179` health check 30s × 3 miss = 90s 就 kill，而 serve 啟動 >90s（每次走網絡檢查 20 個模型檔）。業界做法已搜（K8s startupProbe / AWS grace period / sokuji 90s handshake）。
- Plan：`.hermes/plans/2026-09-23_1500-jarvis-sidecar-restart-loop-fix.md`（3 改動：startup grace period / 模型本地快取 / log 輪替；7 項驗收標準）。**JARVIS ONE 現時保持關閉（HUD/提醒暫停）直到修好換版。**
- → ✅ 狀態更新（2026-09-24 09:4x 親核）：JARVIS ONE 已開返（08:38 開機自動行，側車同一 PID、8765 /health 200）；未 commit 嘅 Slice 1 已令重啟循環消失。
