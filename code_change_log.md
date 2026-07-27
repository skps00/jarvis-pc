# 代碼變更與問題日誌

## [2026-07-27 12:42:00] 操作類型：新增

- **文件路徑**：src/jarvis/{router,hands,engine}.py, tests/test_router.py, REMINDERS.md, README.md
- **變更摘要**：system_power：關機／睡眠 → Always Yes 先確認再執行（shutdown／SetSuspendState）。
- **遇到的問題**：無
- **備註**：選做 Hard checklist 缺口；查詢 LLM 仍延後。dry-run／拒確認唔執行。

## [2026-07-27 12:32:00] 操作類型：修改

- **文件路徑**：src/jarvis/asr_repair.py, tests/test_router.py
- **變更摘要**：browser 粵語誤聽用 regex 包[沙洒耍…]→browser，唔再逐個加字。
- **遇到的問題**：
  - 問題1：ear 輪流出包沙／包洒，逐條 confusion 追唔切
  - 解決方案：`_BROWSER_BAU_SAA` 一次替換
  - 狀態：✅ 已解決
- **備註**：真講英文 browser 先穩；Chrome 更穩。

## [2026-07-27 12:28:00] 操作類型：修改

- **文件路徑**：src/jarvis/{router,asr_repair}.py, tests/test_router.py
- **變更摘要**：修「开个新包耍出嚟」——剝尾助詞出嚟；包耍→browser；保留 force_new。
- **遇到的問題**：
  - 問題1：ear raw=`开个新包耍出嚟。` → 未登錄「包耍出嚟」
  - 解決方案：normalize 剝出嚟／出来；confusion／alias 包耍→browser
  - 狀態：✅ 已解決
- **備註**：推論：用戶講「開個新 browser 出嚟」。

## [2026-07-27 12:22:00] 操作類型：修改

- **文件路徑**：src/jarvis/asr_repair.py, tests/test_router.py
- **變更摘要**：ASR 修 force_new：new window／再開誤聽；`_fix_open_target` 保留 modifier；filler 明確唔食 new。
- **遇到的問題**：
  - 問題1：「開 knew window Chrome」因 chrome substring 提早 usable（無 force_new），跳過 confusion
  - 解決方案：confusions 先於 early-return
  - 狀態：✅ 已解決
- **備註**：對齊 plan「可修 new window／再開」。

## [2026-07-27 12:14:00] 操作類型：修改

- **文件路徑**：src/jarvis/{router,hands,engine}.py, config/profiles*.yaml, tests/test_router.py, README.md
- **變更摘要**：通用 force_new：再開／new／新視窗等；開個＝量詞；Chrome --new-window；跳過已開 focus。
- **遇到的問題**：無
- **備註**：之後 LLM 可對歧義句填 force_new JSON；而家規則先。

## [2026-07-27 12:02:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py
- **變更摘要**：Chrome 已開：改 focus 現有窗（唔再問殺 process）；多窗唔問邊個，focus Z-order 最上層。
- **遇到的問題**：
  - 問題1：「開 browser」Chrome 開住時取消還原，唔 focus
  - 解決方案：對齊設計／MC——已開只 focus；冷開先 --restore-last-session
  - 狀態：✅ 已解決
- **備註**：要揀指定窗＝之後再做；而家手動 Alt+Tab。

## [2026-07-27 11:54:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py
- **變更摘要**：focus 視窗時唔再用無條件 SW_RESTORE（會縮細全螢幕）；只最小化先 restore。
- **遇到的問題**：
  - 問題1：已開 MC 再 focus 令全螢幕變細窗
  - 解決方案：IsIconic 先先 ShowWindow(SW_RESTORE)
  - 狀態：✅ 已解決
- **備註**：重啟 serve。

## [2026-07-27 11:51:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py, tests/test_hands_mc.py
- **變更摘要**：Prism MC 已開：偵測 java 命令列含 instance_id → 唔再 --launch，改 focus 遊戲窗＋字幕說明。
- **遇到的問題**：無
- **備註**：Windows only focus；搶唔到 focus 會提示 Alt+Tab。

## [2026-07-27 11:47:00] 操作類型：修改

- **文件路徑**：src/jarvis/asr_fix.py, tests/test_router.py
- **變更摘要**：把 SenseVoice 對短英文專名誤聽（caa→CS、cura→Cursor）寫入修正／別名表。
- **遇到的問題**：
  - 問題1：使用者講 CS／Cursor，STT 出 caa／cura，以為自己英文差
  - 解決方案：說明係模型問題；加目標詞別名＋開+target 重建
  - 狀態：✅ 已解決
- **備註**：重啟 serve。亦可用粵語名：開特戰／開瀏覽器。

## [2026-07-27 11:43:00] 操作類型：新增／修改

- **文件路徑**：src/jarvis/{asr_fix,ear,engine,shell_app}.py, config/profiles*.yaml, tests/test_router.py
- **變更摘要**：語音準度：ASR 修正／模糊匹配白名單指令、錄音改 4 秒、hotword／postprocess、CS 誤聽「开线」。
- **遇到的問題**：
  - 問題1：SenseVoice 出「測試开线嘅」等嘈音，指令唔準
  - 解決方案：asr_fix + 稍長錄音 + profile hotwords（引擎支援先）
  - 狀態：✅ 已解決（模型本身仍有上限；講短句最穩）
- **備註**：重啟 serve。講「開 CS」「開 Cursor」短指令。

## [2026-07-27 11:40:00] 操作類型：修改

- **文件路徑**：src/jarvis/router.py, tests/test_router.py
- **變更摘要**：ASR 正規化：簡體動詞（开／打开…）→ 繁體；剝句尾句號。
- **遇到的問題**：
  - 問題1：SenseVoice 出「开 cs 。」router 認唔到「開」
  - 解決方案：normalize_utterance 做簡→繁＋去標點
  - 狀態：✅ 已解決
- **備註**：重啟 serve 後生效。

## [2026-07-27 11:05:00] 操作類型：修改

- **文件路徑**：src/jarvis/shell_app.py
- **變更摘要**：加狀態列／視窗標題／系統匣提示：就緒、錄音倒數、辨識中、執行中；錄音時匣圖變紅。
- **遇到的問題**：
  - 問題1：使用者唔知 JARVIS 係咪運行／係咪錄音
  - 解決方案：明顯 status label + 倒數 + tray 藍／紅
  - 狀態：✅ 已解決
- **備註**：需重啟 serve。

## [2026-07-27 11:03:00] 操作類型：修改

- **文件路徑**：src/jarvis/ear.py, pyproject.toml
- **變更摘要**：補裝 torchaudio；Ear 錯誤改顯示真正缺嘅模組。
- **遇到的問題**：
  - 問題1：撳語音顯示「SenseVoice 未裝」，實為缺 torchaudio（ImportError 被籠統包住）
  - 解決方案：pip install torchaudio；改錯誤文案；extras 加入 torchaudio
  - 狀態：✅ 已解決
- **備註**：需重啟 `python -m jarvis serve`。

## [2026-07-27 11:01:00] 操作類型：修改

- **文件路徑**：pyproject.toml（ear extras）
- **變更摘要**：本機安裝 `[ear]`（funasr／sounddevice／numpy）並補裝 PyTorch CPU；ear extras 加入 torch。
- **遇到的問題**：
  - 問題1：funasr 安裝後缺 torch，無法跑 SenseVoice
  - 解決方案：`pip install torch`（CPU wheel）；寫入 optional-deps
  - 狀態：✅ 已解決
- **備註**：首次 `listen` 會再下載 SenseVoiceSmall 模型。

## [2026-07-27 10:17:00] 操作類型：新增／修改

- **文件路徑**：src/jarvis/{autostart,ear,discover,persist,engine,hands,router,__main__,shell_app}.py, pyproject.toml, tests/test_router.py, README.md, REMINDERS.md
- **變更摘要**：完成使用者 1234：驗收通過；開機自啟；SenseVoice Ear 骨架；Discover&Confirm＋查詢字幕 stub。
- **遇到的問題**：
  - 問題1：四項範圍大
  - 解決方案：順序實作；Ear 用 optional `[ear]`；query 暫不接 LLM
  - 狀態：✅ 已解決（LLM 內容回答仍待）
- **備註**：`python -m jarvis autostart on`；語音需 `pip install -e ".[ear]"`。

## [2026-07-27 10:09:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py
- **變更摘要**：Chrome 還原：已開住時可確認後 taskkill 全部再 `--restore-last-session`；字幕提示多窗需「結束 Google Chrome」一次關晒。
- **遇到的問題**：
  - 問題1：使用者兩個 Chrome 窗，還原後只開一個
  - 解決方案：Chrome session 只會還原「上次寫入嘅窗」；開住／背景會令 Jarvis 略過還原。改為可強制結束再還原＋關閉教學提示。Jarvis 無法憑空發明 Chrome 沒存嘅第二窗。
  - 狀態：✅ 已解決（行為＋說明；多窗仍取決於 Chrome 有冇存齊）
- **備註**：設計禁止 SendKeys；唔做 Ctrl+Shift+T。

## [2026-07-27 09:51:00] 操作類型：修改

- **文件路徑**：src/jarvis/router.py, config/profiles.yaml, config/profiles.example.yaml, tests/test_router.py
- **變更摘要**：審計同類型路由缺口；補設計已列／語音助理常見動詞、STT 錯字、Chrome／戰場還原別名，並剝句首 please／唔該。
- **遇到的問題**：
  - 問題1：「Chrome 還原」同類句（唔該開、lanuch、resume Chrome、restore tabs、還原上次戰場…）多數未知動詞
  - 解決方案：擴充 open_verbs／restore_phrases／aliases；resume／restore 限 browser；戰場 phrase 仍優先
  - 狀態：✅ 已解決
- **備註**：故意不加「繼續」當通用動詞（太寬）。需重啟 serve。

## [2026-07-27 08:51:00] 操作類型：修改

- **文件路徑**：config/profiles.example.yaml, config/profiles.yaml, tests/test_router.py
- **變更摘要**：支援「Chrome 還原」——把 還原／恢復／restore 當 open 動詞，且 verb_kind_limits 限 browser_session。
- **遇到的問題**：
  - 問題1：使用者輸入「Chrome 還原」被判「未識別開啟動詞」
  - 解決方案：倒裝動詞匹配；戰場還原仍由 restore_phrases 優先攔截
  - 狀態：✅ 已解決
- **備註**：需重啟 `python -m jarvis serve` 才載入新 profiles。

## [2026-07-27 08:38:00] 操作類型：修改

- **文件路徑**：REMINDERS.md, README.md
- **變更摘要**：鎖定 STT 路線 A（打字）先、之後 B（本機 SenseVoice）；Google Cloud STT 因信用卡不支援棄用。
- **遇到的問題**：
  - 問題1：GCP 不支援使用者信用卡，無法開 Speech-to-Text billing
  - 解決方案：不做 Google STT；先打字保底，語音改 SenseVoice
  - 狀態：✅ 已解決（產品決策）
- **備註**：未實作 Ear／SenseVoice；Discover & Confirm 仍為 v1.1。

## [2026-07-27] 操作類型：修改

- **文件路徑**：src/jarvis/shell_app.py, README.md
- **變更摘要**：Ctrl+Alt+J 改為切換顯示／隱藏（toggle）。
- **遇到的問題**：無
- **備註**：—


## [2026-07-27] 操作類型：新增

- **文件路徑**：src/jarvis/{config,memory,hands,router,__main__,__init__}.py, tests/test_router.py, requirements.txt, pyproject.toml, README.md
- **變更摘要**：實作 v1 第一步——profiles 載入、Hands 啟動（Steam／Prism／exe／Chrome restore）、本地 verb+name router、CLI。
- **遇到的問題**：
  - 問題1：Windows console 中文亂碼
  - 解決方案：CLI `stdout.reconfigure(encoding=utf-8)`
  - 狀態：✅ 已解決
- **備註**：Discover & Confirm 仍為 v1.1。下一步：熱鍵 Ctrl+Alt+J＋系統匣／細窗；再接 STT。

## [2026-07-27] 操作類型：新增

- **文件路徑**：REMINDERS.md
- **變更摘要**：鎖定 Discover & Confirm 為 v1.1 後做，並留下提醒。
- **遇到的問題**：無
- **備註**：使用者要求 remind。

## [2026-07-27] 操作類型：新增

- **文件路徑**：config/profiles.yaml
- **變更摘要**：依本機路徑填入 CS2／Prism NFWC／Cursor／Chrome（gitignored）。
- **遇到的問題**：
  - 問題1：無
  - 解決方案：—
  - 狀態：✅ 已解決
- **備註**：
  - Prism portable：`...\PrismLauncher-Windows-MSVC-Portable-8.0\...\prismlauncher.exe`
  - 預設 MC 實例：`No_Flesh_Within_Chest-1.0.2-DIM`
  - Steam：`C:\Program Files (x86)\Steam\steam.exe`（CS2 用 app_id 730）

## [2026-07-26] 操作類型：新增

- **文件路徑**：README.md, .gitignore, .env.example, config/profiles.example.yaml, src/jarvis/*, tests/.gitkeep, code_change_log.md
- **變更摘要**：建立 `jarvis-pc` repo 最小骨架（無業務邏輯）。
- **遇到的問題**：
  - 問題1：`create_project` MCP 因 Windows 無 `/bin/sh` 導致 git init 失敗；改用 PowerShell `git init`。
  - 解決方案：手動建目錄與 git。
  - 狀態：✅ 已解決
  - 問題2：`move_agent_to_root` 在空 repo（無 HEAD）失敗。
  - 解決方案：先做初始 commit 再 move。
  - 狀態：✅ 已解決
- **備註**：對應 gstack 設計 APPROVED。
