# HANDOFF — jarvis-pc（狀態區塊 + 逐日 index）

<!-- STATE:BEGIN -->
## 狀態（每次 session 尾／cron **改寫**；新 section 一律加喺本區塊**之下**）

- **目標**：JARVIS ONE（語音／HUD／alerts）穩定收尾 ＋ MC packai（Forge 1.19.2 primary）設定／答案版面／卡片修復落地。計畫書：`.hermes/plans/REMAINING_WORK.md`
- **現狀（2026-09-22 19:0x 改寫；全部 Hermes 親核）**
 - **Git**：HEAD ＝ `feature/hermes-alerts-mcp` `358c2bc`，**ahead origin 8**（全部 docs commit，未 push）；origin/main `96be515`（PR #12）未入本分支；未 commit 檔 = **0**，`src/`／`tests/`／`hud/` 乾淨；**今日程式碼零改動**
 - **JARVIS ONE**：HUD **0.4.13** 已 build＋部署＋捷徑更新（`61354de`）；**語音喚醒已關**（`voice_frontend=hermes`，8765 `/health` `wake_on=false`）→ 還原＝`POST /settings voice_frontend=jarvis`＋重啟側車；**自動調門檻已凍結**（`wake_debug.log` 改名歸檔 → thr 定死 0.55）→ 還原＝改返名
 - **監測線**：誤觸老實化＋提示靜音**兩條都停手**（SK 2026-09-22 選 C，等新 mic）；R1–R3 全部 blocker／反轉條件已存兩份 plan，重啟唔使重做 research
 - **packai（MC 主線，詳 MC repo HANDOFF）**：Slice 1 已 commit＋push；**Slice 1b code 自驗綠但真機 A/B 未跑 → 未 commit**（5 檔未 commit）；MC repo HEAD `013e4ac` 已全部 push
 - **Hermes 設定**：`compression.micro_compact=true`＋`micro_compact_every_n_turns=10`（**新 session 生效**；備份 `config.yaml.bak-20260922-182831-microcompact`；還原＝`hermes config set compression.micro_compact false`）
 - **本檔**：只留未做嘅事（已完成任務已全部歸檔）
- **唔准郁（硬限制）**
 - 打機／用緊電腦：**零彈窗、零搶焦點**（先讀 `state/sk_activity.json`）；GUI 窗一律第二副螢幕；Chrome 主動開＝`bg_launch.py --minimized`
 - `AGENTS.md` 受保護（要 SK 明確 go）；唔准 `curl|sh`；**HANDOFF 視為可公開 → 唔准入 secrets**
 - packai code **一律經 cursor-agent**；**唔准 `git add -A`**；部署只准用 `mc_mod_deploy_jar.py`（真 instance 唔准自動部署）
 - **語音／mic 線 HOLD（等 SK 新 mic）**：唔郁 `wake.py`／STT／AEC／聲紋／wake threshold／mic device；唔叫 SK 測 wake
- **未解（等 SK 決）**：① **測試隔離 ii 實作**（已批准，未開工）② **Slice 1b 真機 A/B** ③ Slice 1c plan（源頭措辭／機翻／關聯閘）④ Slice 2 世界生成正式 plan ⑤ 取得途徑缺口修補 ⑥ **dev → main 合併**（PR 定直接 merge）⑦ `jarvis-pc/AGENTS.md` 版本字串仍寫 0.4.10 ⑧ **SK 手動**：Surfshark 加 3 個 exclusion folder ⑨ **非專案**：MS DCT 面試 6 個 STAR 數字（覆咗即出英文可照背版）
- **下一步（優先序）**：① **測試隔離 ii**（plan → review ≥8:2 → 實作；驗收＝跑測試前後 session 數／mtime 不變）② **packai Slice 1b 沙盒真機 A/B**（需 SK idle ＋ DS 空閒時段）③ Slice 1c plan → R1 review ④ Slice 2 正式 plan ⑤ 取得途徑缺口（等 SK 拍板）⑥ merge 決定
- **歸檔索引**：**已完成記錄全部喺 `plans/archive/HANDOFF-2026-09.md`（54 段，已按完成日期新→舊重排＋頂部有日期索引）**；更舊（2026-08）見 `plans/archive/HANDOFF_2026-08-*.md`
- **參考段（檔尾）**：陷阱（重溫）／語音·硬體設定（驗證過）

<!-- STATE:END -->

## 今日完成（2026-09-23）
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
