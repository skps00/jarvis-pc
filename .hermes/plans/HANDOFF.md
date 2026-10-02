# HANDOFF — jarvis-pc（狀態區塊 + 逐日 index）

<!-- STATE:BEGIN -->
## 狀態（每次 session 尾／cron **改寫**；新 section 一律加喺本區塊**之下**）

- **目標**：JARVIS ONE（語音／HUD／alerts）穩定收尾 ＋ MC packai（Forge 1.19.2 primary）＋ MayaCraft DJ2 客戶端玩家支援（非 repo 專案）。計畫書：`.hermes/plans/REMAINING_WORK.md`
- **現狀（2026-09-30 19:3x 改寫；全部 Hermes 親核）**
 - **MS DCT 面試：四場全部完成**（Mike 9/28；Elena＋Dhaval 9/29；**Owen 9/30 11:00＝最後一場**，59:58 已轉錄）→ `Documents\MS_DCT_Prep\records\`：`面試-20260930-1100-Owen-逐字稿.md`（48,225 bytes）＋`-情報摘要.md`（10,342 bytes）；今日 focus＝technical knowledge；role 實際＝**70–80% hands on**（SK 原答 remote support 被即場修正）；Owen Lee＝前 Microsoft 香港 DC site operation manager（Mike Wong report 佢）。**冇下一輪；下星期有 conclusion**（10/1、10/2 係其他人面試）。枱面檔＝`面試速查-中英對照.pdf`（7 頁）＋`今日唸稿-20260929.pdf`。
 - **DJ2-Cleanroom（玩家支援；09-30 收線）**：① Actinium 0.0.11 版可連 mayacraft.net（10:28:58 開機→10:30:44 入服、零 mixin 錯誤）② `使用說明.txt` 加【版本選擇：要 FPS 定要光影】（108 行；sha16 `7cef1cc4d2858c46`）③ 裝 **NeoFontRender 0.6.1＋ModularUI 3.2.0-nfr.2**（sha256 對官方 digest；**SmoothFont 已移除** → 根因＝Actinium 接管字體令 SmoothFont 自我停用）④ resource pack 錯版已移除：DJ2 用 `Modernity-f3-3.10.3.zip`（f1 版 pack_format 1 → GUI／格子對唔上）；**文檔／打包交咗另一個 AI，Hermes 只做測試**（16:11–19:10 連續玩、零 crash）⑤ 遊戲 ping 266ms **結案**＝join 後暫態（load 完 51ms；路徑 26ms 實測正常；間歇 +240ms 尖峰只出現喺「SK ↔ 該 host」，SK 部機已排除）。⑥ **10-01 凌晨：聊天欄紅字根因查到**（Cleanroom 建議系統 → TP `checkPermission`；每次問＝2 行＝本地＋伺服器；修法三選項等 SK 揀）。 ⑦ **10-03 冶煉爐 crash（朋友 client）→ 自家 `dj2-fixes-1.1.1` 兜底**：slot 越界 cancel＋即刻閂 GUI、null tank 唔畫（上游 #4081 Won't Fix）；已裝 SK instance（sha 親核）、**朋友要自己裝**；jar `Documents\MC_Patches\dj2-fixes\dist\`。
 - **Git**：jarvis-pc `feature/hermes-alerts-mcp` HEAD `e69b5c1`；**未 push 100**、**未 merge 156**（截至 10-01 13:2x；其後 docs commit 各 +1）；**未 commit 4 檔**（`hud/main.js`／`hud/settings.html`／`src/jarvis/settings.py`／`src/jarvis/shell_app.py` ＝ Slice 1）。
 - **JARVIS ONE**：10-01 13:2x 親核**行緊**（Electron＋sidecar、8765/8770/8771 LISTEN、`/health` ok）；⚠️ 一個 app 正常 4 個同名進程，唔好 kill 主進程。
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
- **未解（等 SK 決）**：① JARVIS Slice 1 驗收窗口 1／2 ② Slice 1 打包換版 ③ **測試隔離 ii 實作**（已批准未開工）④ **packai Slice 1b 真機 A/B** ⑤ Slice 1c／Slice 2 正式 plan ⑥ **dev → main 合併**（PR 定直接 merge）⑦ **反方 reviewer R1 報告未消化**（subagent session `20260927_231610_3d99d0`，11.3k 字：LD1–LD6）⑧ **CS2 為何仍落 LPI 16-31** ⑨ JARVIS 要唔要開返 ⑩ **DJ2 客戶端測試待 SK 眼睇**（字體／GUI／光影三項；文檔＋v1.3 打包已交另一個 AI）⑪ **DJ2 聊天欄紅字修法**（①改 TP jar 5 bytes｛只減半｝／②自家 client mod 過濾顯示｛要起 1.12.2 build 環境｝／③改 Cleanroom jar｛脆｝） → **SK 揀 ②＋(i) 全清淨**；jar 已 build＋已放入 instance（待 SK 重啟驗收）；⑫ **MayaCraft ping 報告已出**（等 SK send 畀 server admin） ⑬ **DJ2 冶煉爐防呆已上線（1.1.1）、待重開 game 睇 `cleanmix.log` 兩個新 APPLY**；朋友 client 未裝。
- **下一步（優先序）**：① DJ2 自家 mod 驗收：`dj2-wrapfix`（Tinkers GUI crash）＋`dj2-chatfilter`（紅字）→ 重啟後睇 cleanmix.log APPLY ＋ 實測（10-02）② JARVIS Slice 1 窗口 1 → 打包換版 → 窗口 2 ③ packai Slice 1b 真機 A/B ④ 反方 R1 → 三段式（≥8:2）⑤ CS2 剩兩樣 → A/B ⑥ 測試隔離 ii（plan → review）⑦ dev→main 合併決定
- **歸檔索引**：已完成記錄喺 `plans/archive/HANDOFF-2026-09.md`（主檔歸檔 3 次：09-22 段落；2026-10-01 搬 09-23／09-24 段落；**2026-10-03 搬 09-24～09-30 全部段落**，備份 `hermes\backups\HANDOFF.md.bak-20261003-0245`）
- **參考段（檔尾）**：陷阱（重溫）／語音·硬體設定（驗證過）
<!-- STATE:END -->

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


