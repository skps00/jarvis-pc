# 代碼變更與問題日誌

## [2026-07-28 07:55:00] 操作類型：修改

- **文件路徑**：src/jarvis/brain.py, tests/test_brain.py, code_change_log.md
- **變更摘要**：/review A：close／restart／system_power 硬閘；「關」唔再誤觸「關於／無關／關係」。
- **遇到的問題**：
  - 問題1：open 有閘、close／power 無 → LLM 可無證據關／關機
  - 解決方案：對稱 lexical hard gate
  - 狀態：✅ 已解決
  - 問題2：單字「關」匹配「關於」
  - 解決方案：負向前後看（無／開… + 於／係…）
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 07:50:00] 操作類型：修改

- **文件路徑**：src/jarvis/{shell_app,hands,brain}.py, code_change_log.md
- **變更摘要**：/review AUTO-FIX：busy 時設定重啟聽候保持 pause；join timeout 警告；Prism focus 傳 monitor/role；close 詞加 shut。
- **遇到的問題**：
  - 問題1：存設定重開 wake 會 clear pause，錄音中搶 mic
  - 解決方案：restart 後若 `_busy` 再 set pause
  - 狀態：✅ 已解決
  - 問題2：Prism 路徑漏 role layout
  - 解決方案：`_launch_prism(..., monitor=, role=)`
  - 狀態：✅ 已解決
- **備註**：ASK 待答：close/power hard gate；「關」誤觸「關於」。

## [2026-07-28 07:45:00] 操作類型：修改

- **文件路徑**：src/jarvis/shell_app.py, tests/test_shell_wake_restart.py, code_change_log.md
- **變更摘要**：修設定存檔後聽候可能唔再開（stop 未 join 就 start）；列模型／檢測改背景線程防 Tk 凍；門檻範圍存檔前校驗。
- **遇到的問題**：
  - 問題1：apply_settings → stop_wake → start_wake；舊 thread 仍 alive 時 start 直接 return，聽候變關
  - 解決方案：stop_wake join(timeout)；再 clear event 再開
  - 狀態：✅ 已解決
  - 問題2：list_models／probe 喺 UI 線程，timeout 可卡數十秒（Tk 常見坑）
  - 解決方案：worker thread + root.after 回 UI
  - 狀態：✅ 已解決
- **備註**：審核方法：單元測試 + 探索式邊界 + 網上 desktop/Tk checklist。

## [2026-07-28 07:35:00] 操作類型：修改

- **文件路徑**：src/jarvis/shell_app.py, tests/test_settings.py, code_change_log.md
- **變更摘要**：補完 SettingsWindow（先前 StrReplace 失敗）；Tabs＋隱藏 ASR 雲端欄＋檢測連線；加 preset_from_label／probe 單測。
- **遇到的問題**：
  - 問題1：SettingsWindow 大塊 replace 對唔上舊字串，UI 仍係單頁
  - 解決方案：整段 class 用檔案拼接覆寫；跑 test_settings
  - 狀態：✅ 已解決
- **備註**：對齊：Cherry 檢測／列模型；Hermes Key→model；OpenClaw 分頁；Claude Code／Codex 清晰 model id。

## [2026-07-28 07:25:00] 操作類型：修改

- **文件路徑**：src/jarvis/{settings,shell_app}.py, code_change_log.md
- **變更摘要**：設定頁對齊 Cherry／Hermes／OpenClaw：Notebook 分頁、SenseVoice 隱藏雲端欄、檢測連線、中文 Preset；參考 Claude Code／Codex 模型揀選清晰度。
- **遇到的問題**：
  - 問題1：一長形式難用；SenseVoice 仍見雲端欄
  - 解決方案：Tab＋條件顯示＋probe_connection（UI 07:35 才真正落地）
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 07:20:00] 操作類型：修改

- **文件路徑**：src/jarvis/{settings,ear,brain,shell_app}.py, tests/test_settings.py, .env.example
- **變更摘要**：設定通用化——ASR/LLM 可選 model；API 列模型；Ollama／自訂模型；舊 mimo 欄位相容遷移。
- **遇到的問題**：
  - 問題1：寫死 mimo-v2.5-asr／單一供應商
  - 解決方案：openai_audio + asr_model；LLM preset＋list_models；custom_models
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 07:15:00] 操作類型：新增 | 修改

- **文件路徑**：src/jarvis/{settings,ear,brain,shell_app,wake}.py, tests/test_settings.py, .env.example
- **變更摘要**：Tk 設定頁 + AppData settings.json；ASR SenseVoice｜MiMo 可切；LLM／聽候／錄音／開機自啟可改。
- **遇到的問題**：
  - 問題1：設定散落 .env 同硬編碼常數
  - 解決方案：統一 settings.json（優先於 .env）
  - 狀態：✅ 已解決
- **備註**：第一版唔改 profiles、唔做 TTS。

## [2026-07-28 07:05:00] 操作類型：修改 | 新增

- **文件路徑**：src/jarvis/{autostart,__main__}.py, tests/test_autostart.py, code_change_log.md
- **變更摘要**：修 autostart：legacy .cmd 算已啟用；disable 淨清 .cmd 唔再誤報；status 警告舊腳本；加單測。
- **遇到的問題**：
  - 問題1：開機彈 CMD（Startup JARVIS.cmd + python.exe）
  - 解決方案：改 silent VBS + pythonw；enable 清舊 cmd
  - 狀態：✅ 已解決
  - 問題2：disable 只剩 .cmd 時會講「本來就未開啟」
  - 解決方案：先記 had_vbs/had_cmd 再刪
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 07:00:00] 操作類型：修改

- **文件路徑**：src/jarvis/autostart.py
- **變更摘要**：開機自啟改寫 silent `JARVIS.vbs`（pythonw，WindowStyle=0）；清舊 `JARVIS.cmd`。
- **遇到的問題**：
  - 問題1：重開機 Jarvis 跟住彈 CMD
  - 解決方案：Startup 唔再用 `python.exe` 嘅 `.cmd`；改 VBS + pythonw
  - 狀態：✅ 已解決
- **備註**：跑一次 `python -m jarvis autostart on` 覆寫 Startup。

## [2026-07-28 01:50:00] 操作類型：修改

- **文件路徑**：src/jarvis/{brain,hands,wake}.py, tests/test_brain.py, docs/train_wake_jarvis.md
- **變更摘要**：Backlog4：無開動詞唔再盲改關（要有關提示先翻）；restore.role 硬佈局；wake 門檻 0.55→0.58。
- **遇到的問題**：
  - 問題1：Brain 無開動詞一律改關 → STT 漏「開」會誤關
  - 解決方案：僅有 clear close hint 先 flip；否則 refuse
  - 狀態：✅ 已解決
  - 問題2：多螢幕只移 top-left、唔理 role
  - 解決方案：primary_game 鋪滿；chat／ide／browser 分區
  - 狀態：✅ 已解決
- **備註**：自訓 jarvis.onnx 留明日（docs/train_wake_jarvis.md）。

## [2026-07-28 01:42:00] 操作類型：修改

- **文件路徑**：src/jarvis/shell_app.py, src/jarvis/wake.py
- **變更摘要**：聽候 CD 5s → 2s。
- **遇到的問題**：
  - 問題1：CD 太長
  - 解決方案：WAKE_CD_SECONDS／_POST_RESUME_S＝2
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 01:40:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py
- **變更摘要**：審核開／focus：清 steam 死分支；app_exe／app_lnk 已開改 focus。
- **遇到的問題**：
  - 問題1：steam focus 後仍判斷「已關閉／已取消」
  - 解決方案：刪死碼
  - 狀態：✅ 已解決
  - 問題2：Cursor 等 app_exe 已開會再 launch 一份
  - 解決方案：有 process_names 且在跑 → focus display_name
  - 狀態：✅ 已解決
- **備註**：brain「無開動詞→改關」仍係設計風險（STT 漏「開」會變關）。

## [2026-07-28 01:35:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py, tests/test_hands_mc.py
- **變更摘要**：Steam 已開改 focus 視窗，唔再問「確認關閉」。
- **遇到的問題**：
  - 問題1：開 CS2 已運行 → 彈「已開。確認關閉？」；用戶要 focus
  - 解決方案：`_launch_or_focus_steam` 對齊 shell_app／Chrome
  - 狀態：✅ 已解決
- **備註**：關 CS 仍用「關／閂」動詞走 close_profile。

## [2026-07-28 01:32:00] 操作類型：修改

- **文件路徑**：src/jarvis/shell_app.py, src/jarvis/wake.py
- **變更摘要**：錄音顯示 REC n；指令後顯示聽候 CD n（5s）至就緒。
- **遇到的問題**：
  - 問題1：用戶問 CD
  - 解決方案：大字 CD 倒數對齊 debounce／post-resume
  - 狀態：✅ 已解決
- **備註**：REC＝錄音；CD＝聽候冷卻。

## [2026-07-28 01:30:00] 操作類型：修改

- **文件路徑**：src/jarvis/shell_app.py
- **變更摘要**：錄音大字倒數 timer（4→1）；日誌每秒一筆；結束隱藏。
- **遇到的問題**：
  - 問題1：用戶想見到錄音 timer
  - 解決方案：獨立大 Label + status／title／tray 同步
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 01:25:00] 操作類型：修改

- **文件路徑**：src/jarvis/wake.py, src/jarvis/shell_app.py
- **變更摘要**：防狂錄：邊沿觸發（分數要跌先再醒）＋恢復後 4s 冷卻＋UI 5s debounce。
- **遇到的問題**：
  - 問題1：醒完又即刻再醒 → 不停錄音
  - 解決方案：armed 要 score<_REARM_BELOW；post-resume cooldown；shell 5s 略過
  - 狀態：✅ 已解決（待再測）
- **備註**：—

## [2026-07-28 01:20:00] 操作類型：修改

- **文件路徑**：src/jarvis/wake.py, src/jarvis/shell_app.py, tests/test_wake.py
- **變更摘要**：聽候打回簡易版：拆 model.reset／連幀／STT；門檻 0.5；_fire 即 pause；忙緊略過要 clear pause。
- **遇到的問題**：
  - 問題1：加嚴＋reset 後完全唔醒
  - 解決方案：OWW 單幀 0.5；唔 reset；唔再開 STT wake；防 pause 死鎖
  - 狀態：✅ 已解決（待再測）
- **備註**：穩優先於減誤觸。

## [2026-07-28 01:15:00] 操作類型：修改

- **文件路徑**：src/jarvis/shell_app.py, src/jarvis/wake.py
- **變更摘要**：修「只醒一次」：listen／submit 必定 finally 清 busy＋pause；恢復時 model.reset。
- **遇到的問題**：
  - 問題1：語音執行中拋錯或中途 return → pause 永遠 set → 聽候死
  - 解決方案：work() 統一 finally busy=False；pause.clear 唔再依賴 _wake_on；OWW reset 後重開 mic
  - 狀態：✅ 已解決（待再測）
- **備註**：日誌應見每次指令後「聽候恢復」。

## [2026-07-28 01:10:00] 操作類型：修改

- **文件路徑**：src/jarvis/wake.py, src/jarvis/shell_app.py, tests/test_wake.py
- **變更摘要**：聽候聽唔到 → 門檻 0.55、連 2 幀、關 VAD、恢復嚴格 STT 後備。
- **遇到的問題**：
  - 問題1：0.68＋VAD＋3 幀太嚴，Hey Jarvis 唔觸
  - 解決方案：降門檻／幀數；移除 vad_threshold；無自訂 onnx 時開短句 STT
  - 狀態：✅ 已解決（待再測）
- **備註**：誤觸同漏聽要夾；仍漏再降至 0.5。

## [2026-07-28 00:20:00] 操作類型：修改

- **文件路徑**：src/jarvis/wake.py, src/jarvis/shell_app.py, tests/test_wake.py
- **變更摘要**：減 Hey Jarvis 誤觸：門檻 0.68、連 3 幀、3s cooldown、關 STT wake、VAD／RMS gate。
- **遇到的問題**：
  - 問題1：hey jarvis 背景誤觸
  - 解決方案：提高 threshold；連續幀確認；預設唔再用 SenseVoice 當 wake；短靜音略過
  - 狀態：✅ 已解決（待用戶再測）
- **備註**：漏聽↑換準；仍漏可略降 `DEFAULT_THRESHOLD`（唔好低過 0.55）。

## [2026-07-28 00:10:00] 操作類型：新增 | 修改

- **文件路徑**：src/jarvis/{wake,hands,shell_app}.py, docs/train_wake_jarvis.md
- **變更摘要**：英文 Jarvis OWW：自訂 onnx 目錄、門檻調低；soft 多螢幕 restore.monitor 移窗。
- **遇到的問題**：
  - 問題1：自訓要 Colab／GPU，本機難一次跑完
  - 解決方案：文件教 Colab；下載後放 `%APPDATA%\\Jarvis\\wake\\jarvis.onnx` 自動載入並關 STT 後備
  - 狀態：✅ 已解決（訓練本身交用戶 Colab）
  - 問題2：多螢幕只記 yaml、唔搬窗
  - 解決方案：focus 後 `_place_hwnd_on_monitor`（primary／secondary）
  - 狀態：✅ 已解決
- **備註**：PR #4 已 merge；本變更在 feature/wake-jarvis-oww-monitor。

## [2026-07-27 23:45:00] 操作類型：修改

- **文件路徑**：src/jarvis/wake.py, src/jarvis/shell_app.py
- **變更摘要**：聽候收窄淨英文 Hey Jarvis／Jarvis；移除賈維斯／加維斯。
- **遇到的問題**：
  - 問題1：用戶只要英文 Jarvis
  - 解決方案：_TEXT_WAKES 只留 jarvis／hey jarvis；UI 文案同步
  - 狀態：✅ 已解決
- **備註**：Hey Jarvis＝OWW；裸 Jarvis＝STT 後備。

## [2026-07-27 23:35:00] 操作類型：修改

- **文件路徑**：src/jarvis/wake.py, tests/test_wake.py
- **變更摘要**：聽候加裸「Jarvis／賈維斯」：OWW Hey Jarvis + 短窗 STT 後備。
- **遇到的問題**：
  - 問題1：openWakeWord 預訓練無淨 Jarvis
  - 解決方案：大聲短窗拷貝 → SenseVoice；命中 jarvis/賈維斯 等同 wake
  - 狀態：✅ 已解決
- **備註**：STT 路徑較慢／食 CPU；Hey Jarvis 仍係最快。

## [2026-07-27 23:10:00] 操作類型：新增 | 修改

- **文件路徑**：src/jarvis/{wake,ear,shell_app,hands,config,memory,app_index,__main__}.py, pyproject.toml, config/profiles.example.yaml, tests/
- **變更摘要**：4 wake word 聽候；2 關閉路徑 caption；1 aliases CLI；3 yaml stt_aliases；5 多窗揀最上並標註。
- **遇到的問題**：
  - 問題1：唔想每次撳「語音」
  - 解決方案：openwakeword `hey_jarvis` 背景聽；命中後 pause → 錄音 4s → 執行
  - 狀態：✅ 已解決
  - 問題2：關 app 唔知行邊條路徑
  - 解決方案：成功訊息附（記住 PID／視窗標題／process_names／Prism java）
  - 狀態：✅ 已解決
- **備註**：`pip install "jarvis-pc[wake]"`；無套件則只留手動語音。多螢幕 layout 仍 soft。force WhatsApp／MC 在 alias 之前跑，避免 learned「沙锅石→WhatsApp」誤開。

## [2026-07-27 19:20:00] 操作類型：修改

- **文件路徑**：src/jarvis/{memory,app_index,asr_repair}.py, tests/test_app_index.py
- **變更摘要**：語音槽位 verb+app_query；成功命中寫入 stt_aliases（學習誤聽）。
- **遇到的問題**：
  - 問題1：大量 app／誤聽唔能靠硬編碼與 hotword 擴表
  - 解決方案：parse_command_slots；alias 先查後 fuzzy；force WhatsApp／近匹配成功後 learn
  - 狀態：✅ 已解決
- **備註**：alias 存 %APPDATA%\\Jarvis\\memory.json；上限 300。

## [2026-07-27 19:12:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py
- **變更摘要**：刪 `_shell_app_focus_needles` 內多餘 WhatsApp 硬編碼（用 display_name 即可）。
- **遇到的問題**：
  - 問題1：focus needles 重複寫 whatsapp
  - 解決方案：只留 display_name
  - 狀態：✅ 已解決
- **備註**：ASR `石`／whatapp 別名仍係專用表（同 Discord／MC 一族）。

## [2026-07-27 19:08:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py, tests/test_hands_mc.py, src/jarvis/asr_repair.py
- **變更摘要**：shell_app 開時若已運行只 focus；新開後 poll 視窗再搶 focus（WhatsApp）。
- **遇到的問題**：
  - 問題1：開 WhatsApp 成功但視窗唔置前
  - 解決方案：`_launch_or_focus_shell_app` + AttachThreadInput 強化 SetForegroundWindow
  - 狀態：✅ 已解決
- **備註**：同分支一併修 `爱锅石` 預設開。

## [2026-07-27 19:05:00] 操作類型：修改

- **文件路徑**：src/jarvis/asr_repair.py, tests/test_router.py
- **變更摘要**：無明確關前綴嘅 `*石`（如 `爱锅石`）改預設開 WhatsApp，唔好當關。
- **遇到的問題**：
  - 問題1：講開 WhatsApp，raw=`爱锅石` → 被修成閂 → 確認取消
  - 解決方案：散/闩/山/沙…先關；其餘短 `*石` 預設開
  - 狀態：✅ 已解決
- **備註**：關要講出關動詞／散／闩／山 等。

## [2026-07-27 19:00:00] 操作類型：修改

- **文件路徑**：src/jarvis/asr_repair.py, tests/test_router.py
- **變更摘要**：裸 STT `沙锅石`／`散木石` 強制映射 WhatsApp（多為關）。
- **遇到的問題**：
  - 問題1：語音落 `沙锅石`／`散木石` 無動詞 → unknown
  - 解決方案：擴充 WhatsApp garbled 前綴（散／沙／山…）+ 整句短 `*石` 強制 閂／開
  - 狀態：✅ 已解決
- **備註**：整句 `*石` 預設當關（此誤聽族常見於 close）。

## [2026-07-27 18:06:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py, tests/test_hands_mc.py
- **變更摘要**：關閉 `shell_app` 時加視窗標題→PID fallback，修 WhatsApp「未在運行」誤判。
- **遇到的問題**：
  - 問題1：`close_profile` 已命中 WhatsApp，但 process_names 偵測不到而回「未在運行」
  - 解決方案：若 launch.type=shell_app，先嘗試 enum windows 依 display_name 找 PID，再 `taskkill /PID`
  - 狀態：✅ 已解決
- **備註**：fallback 只在 shell_app 啟用，減少誤殺。

## [2026-07-27 18:00:00] 操作類型：修改

- **文件路徑**：src/jarvis/asr_repair.py, tests/test_router.py
- **變更摘要**：加 WhatsApp 誤聽專修（`what石`／`闩 石`／`山殼石`）到 `開/閂 whatsapp`。
- **遇到的問題**：
  - 問題1：語音 close WhatsApp 落成「闩 石」，被錯配成 superwhisper
  - 解決方案：短目標 + 石/whatsapp token + 開關動詞 → 強制映射 whatsapp
  - 狀態：✅ 已解決
- **備註**：只在短目標情境啟用，減少誤傷。

## [2026-07-27 17:54:00] 操作類型：修改

- **文件路徑**：src/jarvis/asr_repair.py, tests/test_app_index.py
- **變更摘要**：裸 app 名自動補 `開`，修 `raw=whatsapp` 被判 unknown。
- **遇到的問題**：
  - 問題1：語音落 `whatsapp`（無動詞）→ router unknown，Discover 無法進入
  - 解決方案：ASR 新增 `_maybe_prefix_open_for_bare_app`，高分命中即改成 `開 <App>`
  - 狀態：✅ 已解決
- **備註**：避免 query 句/關閉句誤改。

## [2026-07-27 17:50:00] 操作類型：修改

- **文件路徑**：src/jarvis/app_index.py, tests/test_app_index.py
- **變更摘要**：加短查詢防誤命中長句標籤（如 What is new...）。
- **遇到的問題**：
  - 問題1：`開 what石` 被改寫到長句 App 名，路由走 query
  - 解決方案：best match 前加 plausibility gate：短目標禁配長句／多詞標籤
  - 狀態：✅ 已解決
- **備註**：保留 WhatsApp 命中。

## [2026-07-27 17:46:00] 操作類型：修改

- **文件路徑**：src/jarvis/app_index.py, tests/test_app_index.py
- **變更摘要**：加 mixed STT 拉丁骨架匹配，`what石` 可命中 `WhatsApp`。
- **遇到的問題**：
  - 問題1：ASR 輸出 `what石`，混中英字導致 score 低於門檻
  - 解決方案：拼寫分數新增 `latin_skeleton` 比對與近似門檻；補回歸測試
  - 狀態：✅ 已解決
- **備註**：serve 需重啟載入新邏輯。

## [2026-07-27 17:30:00] 操作類型：新增

- **文件路徑**：src/jarvis/app_index.py, src/jarvis/{asr_repair,discover}.py, tests/test_app_index.py, pyproject.toml, requirements.txt
- **變更摘要**：掃本機 app 建名索引；拼寫近匹配 + ToJyutping 粵拼對目標自動改寫。
- **遇到的問題**：
  - 問題1：手寫 whatapp 表唔 scale；粵語 STT 漢字／拼音對英文名難對
  - 解決方案：StartApps／捷徑／profiles 索引；SequenceMatcher + 粵拼（去調）pair score；repair 改寫 開／關 目標
  - 狀態：✅ 已解決
- **備註**：依賴 ToJyutping；索引 TTL 5 分鐘。

## [2026-07-27 17:22:00] 操作類型：修改

- **文件路徑**：src/jarvis/{asr_repair,discover}.py, tests/test_discover.py
- **變更摘要**：whatapp→whatsapp；Discover 名稱近音／少字母仍可命中。
- **遇到的問題**：
  - 問題1：raw=`开 whatapp`，score=0，Discover 無候選
  - 解決方案：ASR confusion + SequenceMatcher ≥0.86 當近匹配
  - 狀態：✅ 已解決
- **備註**：重啟 serve。

## [2026-07-27 17:20:00] 操作類型：修改

- **文件路徑**：src/jarvis/{discover,hands,persist}.py, tests/test_discover.py, REMINDERS.md, README.md
- **變更摘要**：Discover 加 Desktop／Local Programs／Get-StartApps（含 Store）；shell_app 啟動並可寫入 profiles。
- **遇到的問題**：
  - 問題1：開 WhatsApp 未登錄且 Start Menu 無 .lnk → 0 候選
  - 解決方案：Get-StartApps + shell:AppsFolder\\AppID；Desktop／Local\\Programs 一齊掃
  - 狀態：✅ 已解決
- **備註**：StartApps 列表 cache 5 分鐘。

## [2026-07-27 17:12:00] 操作類型：修改


- **文件路徑**：src/jarvis/{memory,hands}.py, tests/test_hands_mc.py
- **變更摘要**：開 app 時記 PID 入 memory；關／重開優先 taskkill 嗰啲 PID。
- **遇到的問題**：
  - 問題1：無 process_names／lnk 慢啟動時關唔到
  - 解決方案：launch 前後 snapshot image PIDs；profile_pids 持久化；close 先殺記住
  - 狀態：✅ 已解決
- **備註**：browser／prism 仍用原規則；Steam 關時清 pid 紀錄。

## [2026-07-27 17:10:00] 操作類型：修改


- **文件路徑**：src/jarvis/{asr_repair,brain,engine}.py, tests/test_router.py
- **變更摘要**：關 Discord 誤聽唔再開；Latin confusion 用詞界，避 discordrd。
- **遇到的問題**：
  - 問題1：講 close Discord，raw=`|-] dico`，Brain 開咗 Discord
  - 解決方案：ASR force close；brain 無開動詞禁 open／改關；engine 擋；disco⊂discord 詞界
  - 狀態：✅ 已解決
- **備註**：開 Discord 要講「開」。serve 要重載先食新碼。

## [2026-07-27 17:00:00] 操作類型：修改

- **文件路徑**：src/jarvis/{hands,persist}.py, config/profiles.yaml
- **變更摘要**：app_lnk 關閉時解析 .lnk→exe 名；Discover 寫入 process_names；Discord 補 Discord.exe。
- **遇到的問題**：
  - 問題1：閂 Discord 路由啱但「未設 process_names」
  - 解決方案：_resolve_lnk_target；persist 寫 process_names
  - 狀態：✅ 已解決
- **備註**：重啟 serve。

## [2026-07-27 16:50:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py, tests/test_hands_mc.py
- **變更摘要**：修 Prism／MC 關閉——用 JSON 攞 java PID（舊 `` `t `` 格式永遠空）。
- **遇到的問題**：
  - 問題1：close_profile 路由啱但「未在運行」；cmdline 有 MATCH、pids=[]
  - 解決方案：`_java_processes` ConvertTo-Json → pid+cmdline
  - 狀態：✅ 已解決
- **備註**：ASR 已到 close；而家殺 process。

## [2026-07-27 16:48:00] 操作類型：修改

- **文件路徑**：src/jarvis/{asr_repair,ear}.py, tests/test_router.py
- **變更摘要**：閂誤聽族（散／s／san…）+ MC → 強制關；無明確開動詞唔准 fuzzy 成開；hotwords 加關／閂。
- **遇到的問題**：
  - 問題1：散／s／打 mycraft 一律模糊成開 minecraft
  - 解決方案：`_force_close_mc`；mc 句無 open verb 只配 close templates；ear hotword
  - 狀態：✅ 已解決
- **備註**：講「關 MC」最穩；serve 已需重啟。

## [2026-07-27 16:44:00] 操作類型：修改

- **文件路徑**：src/jarvis/asr_repair.py, tests/test_router.py
- **變更摘要**：SenseVoice 閂→冂、minecraft→macraft 誤聽表；冂當關閉提示禁修成開。
- **遇到的問題**：
  - 問題1：raw=`冂 macraft` 仍模糊→開 minecraft
  - 解決方案：confusion 冂→閂、macraft→minecraft；_CLOSE_HINT 含冂
  - 狀態：✅ 已解決
- **備註**：重啟 serve 后再試（或 Ctrl+Alt+J 用已殺舊進程後新開嗰條）。

## [2026-07-27 16:42:00] 操作類型：修改

- **文件路徑**：JARVIS.vbs, JARVIS.bat
- **變更摘要**：釘死 pythoncore-3.14 pythonw；殺晒舊／錯 Python 嘅 serve 進程。
- **遇到的問題**：
  - 問題1：修完「閂」仍見模糊→開——兩條舊 serve（含 WindowsApps pythonw）跑緊舊碼
  - 解決方案：Stop-Process；VBS 用絕對路徑 pythonw
  - 狀態：✅ 已解決
- **備註**：再開後試「閂 my craft」。

## [2026-07-27 16:35:00] 操作類型：修改

- **文件路徑**：src/jarvis/{router,asr_repair,hands,engine}.py, tests/test_router.py
- **變更摘要**：粵語「閂」＝關；mycraft→MC；fuzzy 唔再把閂修成開；Prism MC 可關（殺對應 java）。
- **遇到的問題**：
  - 問題1：raw=`閂 mycraft` → 模糊成`開 minecraft`只 focus
  - 解決方案：閂入 close_verbs；close 偏向 fuzzy；MC close 按 instance_id 殺 java
  - 狀態：✅ 已解決
- **備註**：重啟 serve。

## [2026-07-27 13:52:00] 操作類型：修改

- **文件路徑**：src/jarvis/{router,hands,engine,asr_repair}.py, tests/test_router.py, README.md
- **變更摘要**：restart／重開 CS＝確認後關再開；整句 reboot／重啟電腦＝系統重啟。
- **遇到的問題**：無
- **備註**：`重啟 CS`≠`重啟電腦`。

## [2026-07-27 13:48:00] 操作類型：修改

- **文件路徑**：src/jarvis/{router,hands,engine,asr_repair,asr_fix}.py, config/profiles*.yaml, tests/test_router.py, README.md
- **變更摘要**：支援「關 CS」／close — Always Yes 後依 process_names 關閉；asr_fix 改 shim 免再誤修成開。
- **遇到的問題**：
  - 問題1：關 CS 被舊 asr_fix 模糊成開 CS
  - 解決方案：close_profile 算 usable；asr_fix→asr_repair
  - 狀態：✅ 已解決
- **備註**：關機仍優先於「關」；未設 process_names 會拒絕。

## [2026-07-27 13:45:00] 操作類型：修改

- **文件路徑**：src/jarvis/hands.py, config/profiles*.yaml, tests/test_hands_mc.py, README.md
- **變更摘要**：Steam 遊戲已開再講「開」→ Always Yes 關閉（toggle）；cs2 設 process_names。
- **遇到的問題**：
  - 問題1：CS 已開再「開 cs」又 steam:// 啟動一次
  - 解決方案：偵測 process → 確認後 taskkill；force_new 仍再開
  - 狀態：✅ 已解決
- **備註**：要關先確認；拒＝唔殺。

## [2026-07-27 13:20:00] 操作類型：修改

- **文件路徑**：JARVIS.vbs, JARVIS.bat
- **變更摘要**：無黑窗啟動——VBS 用 pythonw WindowStyle=0；bat 只呼叫 wscript。
- **遇到的問題**：無
- **備註**：雙擊 JARVIS.vbs 最乾淨；bat 仍可能閃一下。

## [2026-07-27 13:18:00] 操作類型：修改

- **文件路徑**：JARVIS.bat
- **變更摘要**：bat 改純 ASCII＋CRLF；去掉中文 echo（UTF-8 令 cmd 拆爛指令）。
- **遇到的問題**：
  - 問題1：雙擊出現 `'cho'`／`'arvis'` 不是命令
  - 解決方案：唔用中文；UTF-8 無 BOM
  - 狀態：✅ 已解決
- **備註**：再雙擊 JARVIS.bat。

## [2026-07-27 13:16:00] 操作類型：新增

- **文件路徑**：JARVIS.bat, README.md
- **變更摘要**：雙擊開 JARVIS Shell（`python -m jarvis serve`）。
- **遇到的問題**：無
- **備註**：用 `%~dp0` 定位專案根；失敗會 pause。

## [2026-07-27 12:52:00] 操作類型：新增

- **文件路徑**：src/jarvis/brain.py, src/jarvis/engine.py, tests/test_brain.py, .env.example, README.md, REMINDERS.md
- **變更摘要**：查詢小 LLM＋歧義 JSON（OpenAI-compat／預設 DeepSeek）；Hands 只信 registry 再解析。
- **遇到的問題**：無
- **備註**：無 key 時 query／歧義降級；明確開場唔過 LLM。

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

## [2026-07-28 15:30:01] 操作類型：修改
- **文件路徑**：src/jarvis/wake.py, src/jarvis/shell_app.py, src/jarvis/settings.py, tests/test_wake.py, docs/train_wake_jarvis.md, code_change_log.md
- **變更摘要**：hybrid 聽候：有自訓 jarvis.onnx 只載 custom OWW；加短窗 STT 後備認「Jarvis」；UI／預設門檻改 Jarvis 導向
- **遇到的問題**：
  - 問題1：Colab simple onnx 分數近 0，淨講 Jarvis 唔醒；有 onnx 時又關咗 STT 後備
  - 解決方案：custom-only OWW + RMS 觸發短窗 SenseVoice／cloud ASR + text_is_wake；thr 預設 0.35
  - 狀態：✅ 已解決
- **備註**：之後可用自己聲重訓加強 onnx；STT 後備保證今日可用

## [2026-07-28 15:38:38] 操作類型：修改
- **文件路徑**：src/jarvis/wake.py, tests/test_wake.py, code_change_log.md
- **變更摘要**：修 hybrid：恢復 hey_jarvis+custom 雙載；加強 STT 後備；清雙 serve 搶咪
- **遇到的問題**：
  - 問題1：custom-only 令 Hey Jarvis 完全失效；自訓分數近 0；雙 pythonw serve 搶 mic
  - 解決方案：paths 永遠 bundled+custom；STT 窗加長／降 RMS；殺重複 serve 只留一個
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 15:42:39] 操作類型：修改
- **文件路徑**：src/jarvis/wake.py, code_change_log.md
- **變更摘要**：STT 後備改用 mic ring buffer（唔再講完先錄）；修正晚錄導致 ASR 垃圾字
- **遇到的問題**：
  - 問題1：wake_debug 顯示 stt_pending 有跑但 text=office/dras/he 等，OWW≈0；用戶以為 log 壞
  - 解決方案：保留最近 ~2s PCM，觸發時直接轉 wav 轉錄；說明 log 路徑正常
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 15:51:58] 操作類型：修改
- **文件路徑**：src/jarvis/wake.py, tests/test_wake.py, code_change_log.md
- **變更摘要**：STT 認 SenseVoice 把 Jarvis 聽成 daws/draaws/drivers；寫 wake_status.txt 人可讀；降 STT 誤觸
- **遇到的問題**：
  - 問題1：用戶以為 log 唔 work；實際 oww_fire 有中但 STT ok=False（draaws/daws）
  - 解決方案：fuzzy text_is_wake；wake_status.txt 一行狀態；STT 提高 RMS
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 15:55:50] 操作類型：修改
- **文件路徑**：src/jarvis/wake.py, code_change_log.md
- **變更摘要**：修 wake 搶咪 race：OWW 命中後先關 InputStream 再 on_detect／錄音
- **遇到的問題**：
  - 問題1：oww_fire 有中但用戶覺 Jarvis 唔 work——on_detect 喺 mic stream 未關就開錄音
  - 解決方案：fire_pending；stream 關閉 + 短 delay 先 dispatch
  - 狀態：✅ 已解決
- **備註**：—

## [2026-07-28 16:08:35] 操作類型：修改
- **文件路徑**：src/jarvis/wake.py, code_change_log.md
- **變更摘要**：淨 Jarvis：STT 後備先 en 再 yue；自訓 onnx 分數近 0 時唔阻 STT；放寬短英文命中
- **遇到的問題**：
  - 問題1：Hey Jarvis(OWW) 得；淨 Jarvis 時 SenseVoice yue 出中文亂碼，fuzzy 唔中；custom onnx≈0.001
  - 解決方案：wake STT 雙語序 en→yue；短 ASCII 近似 jarvis 用 edit distance
  - 狀態：✅ 已解決
- **備註**：長期仍應自己聲重訓 onnx
