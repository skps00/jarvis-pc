# Plan v2：自我監測「無效指令數字老實化」＋ step-change 趨勢規則 ＋ 全域測試隔離

- 日期：2026-09-22（Hermes 起草；**v2 按 R1 反方 3:7 修訂**）
- 範圍：`src/jarvis/self_monitor.py`、`src/jarvis/self_review.py`、`src/jarvis/settings.py`（只加環境變數覆寫）、`tests/conftest.py`、`tests/test_self_monitor*.py`、`tests/test_self_review.py`、`tests/test_brain.py`
- SK 決定（2026-09-22）：**Q1 = (b)** 老實數字驅動 auto-tune；**Q2 = (ii)** 全域測試隔離
- 狀態：**⏸ 停手（SK 2026-09-22 選「3」＝等新 mic 再做）**。呢份檔保留 R1/R2 全部 blocker 同 review log，新 mic 到時直接由 §0 嘅載重決定重寫 v3，唔使重做 research。

---

## 0. Review log（每輪比分＋實質修改）

| 輪 | 比分 | 結果 | 主要 blocker |
|---|---|---|---|
| R1 | 正方 3 : 反方 7 | 未過 | ①下限拍腦袋(<實測) ②baseline 缺席未定義 ③驗收數同 code 窗口矛盾 ④step finding 冇 metric/summary→指紋印唔出 ⑤哨兵 mock 錯 binding |
| R2 | 正方 2 : 反方 8 | 未過（更差） | **設計前提錯**：①用「尾 N 行」做「每日」數字 → 單位錯（cmd_invalid 係窗口累積 48，floor 20 即時成立）；②serve.log 事件行**冇 timestamp** → 無法分曆日；③窗口由「累積」變「滾動」有 regime cliff；④STEP 10×baseline 自我否決（累積 baseline 升 → 門檻 500 永不可達）；⑤`fp ≤ fires` 不變式與實測矛盾（oww_cmd_pcm:oww_fire = 335:248，1:N）；⑥tuner 兩分支都係死條件：升閘要 `avg_peak ≥ 0.28`，但**264 條歷史最大只有 0.07**；⑦`notable` 含 `new_thr != old_thr` → 每次調門檻都會出語音 alert（同 §3.4 承諾相反）；⑧哨兵 tautology（autouse `hermes_enabled=False` 令路徑唔行）＋ `engine.py:230 except Exception` 會吞 `AssertionError`；⑨`settings.py:15` 係 import 期常數 → conftest 設 env 冇效；⑩4 個現有測試 monkeypatch `SETTINGS_DIR` → precedence 未定 |
| R3/R4 | — | 上限 3–4 輪 | 見下方「待 SK 決定」 |

**R3 未開之前必須先解決**（載重決定）：
1. **per-day 數字點嚟**：唯一可行 = 每次 monitor run 記低**累積計數＋時間戳**落一個細狀態檔（例如 `%APPDATA%\Jarvis\self_monitor_state.json`），log 寫**delta**（= 上次 run 到今次 run）→ 單位才對得住「每日」，floor／baseline／step 才有意義（同時解決 serve.log 事件行無 timestamp 嘅問題）。
2. **tuner 是否本輪做**：現有 mic 下 `avg_peak` 歷史最大 0.07 < 升閘所需 0.28 → **tuner 條件今日根本無法成立／無法驗證**，要等新 mic 才有意義；而且每次調門檻都會觸發 `notable` → 語音 alert（要另定語意）。
3. **測試隔離範圍**：唔可以宣稱「全域」（`memory.py`／`mouth.py`／`hermes_bridge.py` 用 `Path.home()`）；要 patch 呼叫期屬性而唔係 import 期常數；哨兵要放喺唔會被 `except Exception` 吞嘅層；要處理 4 個現有 monkeypatch 測試嘅 precedence。

---

## 1. 目標（一句）

令 JARVIS 每日自檢講得出真相：①「叫醒之後用唔到」（無效指令）有得計；②「突然跳升後維持高位」會自己浮出嚟；③ 測試唔會再打真 Hermes API／寫真檔。

## 2. 背景（全部經 R1「數字核實方」獨立重算；數字已按修訂）

| 事實 | 數值（獨立重算） |
|---|---|
| serve.log（現行）`[ear] raw=` | **48** 宗收音（窗口 09/10 23:41 → 09/22 17:02；檔內有 5,317 個帶日期行，但事件行本身無 timestamp） |
| ↳ `[fail] 聽唔清` | 7 |
| ↳ `[route] unknown` | 40（17:02 快照 41；同 `[hermes] kind=unknown` **1:1 成對**，唔可以當兩個獨立訊號相加） |
| ↳ `[hermes] session=` | 40 次事件 / **31 個 unique** session（會重用，次數 ≠ session 數） |
| 09-01（SK 叫買新 mic）之後語音收音 | **70 宗，100% 無效**（gz 段 22：6 fail + 16 unknown；現行 48：7 + 41） |
| serve.log.bak（08/28→09/10） | 33 宗收音，同樣 **100% 無效**（12 + 21）；搜 `怎樣開 Chrome` = 0 |
| self_monitor.log `fp` | **264/264 行 = 0**（由 08-28 到 09-22 從未非零） |
| `thr` 歷史 | 0.30 → 0.45/0.46 → **0.75（08-31 上限）** → 一路 decay 到 0.35 → **再跳 0.75（09-17）** → decay 到 **0.55（現值）**；24 次 pair 變動，最少 3 次 +0.40 級跳升（唔可能係 +0.05 步進 ⇒ 有外部改 settings） |
| state.db `jarvis-*` session | **248**（16:59 前 247；+1 = 本輪測試親手整出） |
| ↳ title 含 Chrome | **200**；其中 **199** 個第一句 = 完全相同 `怎樣開 Chrome？`（其餘 1 個係 `幫我查點樣開 Chrome`） |
| ↳ 測試污染時間線 | 08-31:103、09-12:49、09-13:29、**09-14:1、09-16:2、09-18:1**、09-22:1（本輪親手）→ **唔係「09-13 後停晒」**，係間歇持續 |
| 09-12 16:36–18:27 簇 | **36 個 session**（gap 10.1s–1250s；全局最大簇係 08-31 12:15–12:25 共 65 個） |

**根因 1（監測講唔到真相）**：`self_monitor.py:32 _FP_DUR_S = 0.6`，fp 只計 `oww_cmd_pcm dur < 0.6s`（:91-94）。全檔 330 條 `oww_cmd_pcm`，`dur<0.6` = **0** → fp 永遠 0。
**根因 2（連鎖）**：`_tune_threshold`（:171-176）升閘要 `fp>=3`（從未發生），因此**長期生效嘅係 :174-175 嘅 decay 分支**（`avg_peak<0.28 and fires==0` → −0.05）→ 門檻一直向下漂。
**根因 3（環境污染）**：`tests/test_brain.py::test_engine_query_with_mocked_llm`（:302-308）只 mock `jarvis.brain._chat`；`engine.execute_utterance` 見 `hermes_enabled=True`＋route∈{query,unknown}（:124/:138）就 `_dispatch_hermes()` → `engine.hermes_chat`（:32 import 綁定、:224 呼叫）＝**真 API**。live `settings.json`：`hermes_enabled: true`。**現場證實**：單跑該測試 → 新增 `jarvis-1fd59b1d`（16:59:28，首句 `怎樣開 Chrome？`）。
**根因 3 的深層**：`settings.py:15 SETTINGS_DIR = Path.home()/…` **唔讀 APPDATA** → R1 實測把 `APPDATA` 指去空 tmp 後 `hermes_enabled` 仍 True。同類盲點：`hermes_bridge.py:71`、`memory.py:10`、`mouth.py:23`。現有 `tests/conftest.py:22-35` autouse `_isolate_appdata` 對 settings 係 **no-op**。
**已確認但本輪唔減誤觸**（反方 flip 要求明文承認）：mic 現況 rms≈0.004、`avg_peak=0.03`、門檻 0.55 → 收音/喚醒側問題照舊；本輪只交付「睇得見」。

---

## 3. 設計

> 只改**監測／報告／測試隔離**；唔改 wake 捕音、唔改 STT、唔改 TTS、唔改 alert 決策。（唯一例外：SK 已批 **Q1=(b)**，即 tuner 會用新指標 —— 設計見 §3.5，並加對稱控制＋上限行為。）

### 3.1 metric 定義（**單位／分母寫死，唔准相加唔同分母嘅數**）

沿用窗口：**現有欄位一律維持尾 2000 行**（唔改語意、零回歸）。新欄位用**第二個較大窗口**（wake_debug 尾 40,000 行；serve.log 尾 40,000 行＝現行全檔），並在 summary 加 `win=` 標明窗口行數。

| 欄位 | 定義 | 分母 | 來源 |
|---|---|---|---|
| `fires`（舊，不變） | `oww_fire` 數 | 尾 2000 行 | wake_debug |
| `fp`（**舊語意不變**） | `oww_cmd_pcm dur<0.6s` 數；**保證 `fp ≤ fires`** | wake event | wake_debug |
| `cmd_invalid`（新，headline） | `[route] unknown` ＋ `[fail] 聽唔清` | **utterance** | serve.log（大窗口） |
| `cmd_route_unk`（新） | `[route] unknown`（唯一來源；`[hermes] kind=unknown` 只做 cross-check，**唔加**） | utterance | serve.log |
| `cmd_novoice`（新） | `[fail] 聽唔清（太短／淨語氣詞）` | utterance | serve.log |
| `junk_sess`（新） | `[hermes] session=` 的 **unique id 數**（唔用次數） | unique session | serve.log |
| `disp`（新） | `dispatch_on_command` 數（交叉核對用） | wake event | wake_debug |
| `win=`（新） | 新欄位所用窗口行數（審計用） | — | 兩檔 |

- **唔再用 `fp` 做合成 headline**（R1 blocker ①）：`fp` 保持 per-wake-event 定義；「無效指令」係 `cmd_invalid`，單位寫明 utterance。summary 兩個數同時出現，SK 一眼睇到兩個分母。
- 唔加中文字落 summary（`_RE_KV` 只食 `[\d.]+|n/a|on|off`）；欄位名只用 `\w`。

### 3.2 step-change 規則（修正版）

`self_review.detect_step(days, metric)`：
1. **baseline** = 前最多 7 日**有值**（非 None）日嘅中位數；樣本數 < 3 → 走「baseline_insufficient」分支。
2. **條件**：最近 **2 個連續曆日**（重用 `_consecutive_days`）兩日都 ≥ `max(10 × baseline, floor_abs[metric])`。
3. `floor_abs` **由實測分佈導出**（唔可以拍腦袋；寫入 code 常數＋註釋講點嚟）：由 self_monitor.log 舊值 + 本輪實測估算，初值
   - `cmd_invalid`: **20**（現時典型 ≈ 4/日，即 5×典型）
   - `fp`: **5**（歷史全 0 → 5 已係明確異常）
   - `stt_miss` / `stt_rtf` / `err`: **10 / 1.0 / 30**
   - 每個都在 plan → code 註釋寫明「實測典型值 → 設 N 倍」推導。
4. **baseline_insufficient**（新欄位歷史無值）：用 `floor_abs` 判，finding 加 `baseline_insufficient: true`、`confidence 0.5`（唔用 0.8）。
5. **唔可以拋錯**：median 空集合／parse 失敗 → 回 `False`（唔 raise）；`main()` 包 try/except：出錯 → `print("ERROR")` ＋ **exit 2**（fail-visible，唔可以同上次 fingerprint 相同而靜音）。
6. **穩定 fingerprint**：finding 必須含**穩定、無日期**嘅 `metric` 同 `summary`（例：`summary = "cmd_invalid >= 10x baseline on 2 consecutive days"`），`id = STEP-<metric>`（**唔含日期**），令同一狀況持續時 fingerprint **唔會每日變**（唔會每日叫醒 agent）；`expires` 照 `_EXPIRES_DAYS=7`。
7. **去重／優先序**：同一 metric 同一 run 最多出一條 finding —— 若 STEP 命中就唔再出 TREND（`also_trend: true` flag 記錄）；`build_review()["trends"]` 同步加 step 結果。
8. 舊「連續 3 日單調退化」規則**唔改**。

### 3.3 新欄位同時入 `_TREND_METRICS` / `_LOWER_IS_BETTER`

加 `cmd_invalid`（已由 §3.2 嘅優先序保證唔會同 STEP 雙出）。

### 3.4 alert 副作用（R1 補漏）

`notable` 條件維持用舊 `fp`（唔用新指標）→ **唔會**令 alert 由「偶爾」變「每日一則」；另加一個測試斷言：同一狀況連續兩日跑 `run_once()`，`notable` 唔會由 false 變 true 再變（並在 §4 加 alert_policy 輸出快照測試）。若將來要令 `cmd_invalid` 出 alert，另開 task。

### 3.5 tuner（SK Q1=(b)：用老實數字，但修好單調陷阱）

`_tune_threshold` 改為**對稱控制**，輸入改為新指標（舊 `fp` 唔再用作升閘依據）：
- **升閘**：`cmd_invalid >= 3` **且** `avg_peak >= _PEAK_LOW`（=0.28；即「確實聽得到、但收到嘅指令無效」）→ `min(_THR_MAX, cur + 0.05)`
- **降閘**：`cmd_invalid == 0` **且** `fires >= 1`（有叫醒但零無效）→ `max(_THR_MIN, cur − 0.05)`
- **其他**：hold（唔再靠 `fires == 0` 才准降 → 修好「單調升到 0.75 卡死」）
- **卡上限行為**：已到 `_THR_MAX` 而 `cmd_invalid` 仍 ≥3 → 唔再升，改為**出一條 finding**（`THR-SATURATED`）提示「門檻到頂但無效指令持續」→ 交 SK/後續處理（唔好靜靜卡住）。
- 監測：新 `tuner=` 欄位記 old→new（同舊 `thr=` 語意一致，數值可能唔同）。
- **必附**：動手前 `%APPDATA%\Jarvis\settings.json` 備份 `settings.json.bak-<ts>`（還原＝覆蓋該檔；驗證＝`thr=` 回到動手前值）。

### 3.6 全域測試隔離（SK Q2=(ii)）

1. `src/jarvis/settings.py`：加環境變數覆寫（例如 `JARVIS_SETTINGS_DIR`）→ 默認行為完全不變（唔設＝現狀）。
2. `tests/conftest.py`（autouse, session）：
   - 設 `JARVIS_SETTINGS_DIR` 指向 tmp（寫一份安全 settings：`hermes_enabled=False`、`wake_threshold` 中性值）；
   - **哨兵**：`mock.patch("jarvis.engine.hermes_chat", side_effect=AssertionError("test 唔准打真 Hermes"))` ＋ 同時 patch `jarvis.hermes_bridge.chat`（雙保險）；
   - `mock.patch("jarvis.engine.load_settings", ...)`（`hermes_enabled=False`）作默認；
   - 令 `self_monitor`／`self_review`／`stt_stats` 讀嘅 log 目錄指向 tmp（唔讀真 log）；
   - 保留現有 `_isolate_appdata`（唔刪）。
3. `tests/test_brain.py`：該條測試補上 `hermes_enabled=False`（唔靠 conftest 兜底亦要自我完整）。
4. **防回歸測試**：故意漏 mock → 必紅（要有實測輸出貼落 review）；再加一條斷言「engine query/unknown 路徑走 conftest 默認時，`hermes_chat` 未被呼叫」。

### 3.7 需要 SK 知道嘅一句

`settings.py` 加 env 覆寫屬「改產品 code」（細、默認無行為變化）。如 SK 唔想動 settings.py，替代方案係 conftest 直接 patch `jarvis.settings.SETTINGS_DIR`／`load_settings`（效果一樣、但覆蓋面較窄，`Path.home()` 盲點仍在 `memory.py`／`mouth.py`／`hermes_bridge.py`）。**默認採前者**。

---

## 4. 驗收標準（逐條 Hermes 親手跑；數字全部係**窗口實數**，唔准用全檔數扮窗口數）

1. `env -u PYTHONPATH python -m py_compile src/jarvis/*.py` → RC=0。
2. 單元測試：`tests/test_self_monitor.py`（新欄位 parse／`fp ≤ fires` 不變式／`cmd_invalid = cmd_route_unk + cmd_novoice`／窗口行數 `win=`）；`tests/test_self_review.py`（step 命中、baseline 缺樣本走 floor＋低 confidence、單日 spike 唔算、缺日唔算、median 空集合唔 raise、STEP 優先於 TREND、**fingerprint 持續同一狀況時唔變**、**同一狀況第二日唔出新 finding**）；tuner（升／降／hold／上限飽和出 finding）。
3. **負控（用真 log 片段做 fixture，兩條）**：
   - (i) 把 `[route] unknown` 改成 `[route] open_profile` → `cmd_invalid` 必須跌（唔可以用「刪走 route 行」作弊）；
   - (ii) 只留 `[fail] 聽唔清` → 只有 `cmd_novoice` 上升、`cmd_route_unk` 唔動。
   - (iii) baseline=0 ＋ 只有一日爆升 → **唔出** finding；兩日 → 出。
4. 真 log 跑一次 `python -m jarvis.self_monitor`：`cmd_invalid` 等於**當時窗口**實測值（跑嘅時候即場再數一次做對照，唔用 plan 嘅數）；`python -m jarvis.self_review --fingerprint` 有 step 命中就必需印出**含 `STEP-` 嘅穩定字串**，冇命中就明文寫「冇命中＋原因」。**指紋跑兩次（相隔 ≥1 分鐘）要相同**。
5. `python -m jarvis.eval_gate --lock` 一致 ＋ `--suite golden` 全綠；**並且**：跑之前後對比 `state.db` session 數、`%APPDATA%\Jarvis\voice_status.json` mtime、`settings.json` mtime → **三者都不變**（測試隔離實證）。
6. 全量 `pytest tests/` 跑一次（唔止 golden）＋結果貼落 review。
7. alert 快照：`_shape_self_monitor` 對新 summary 輸出快照測試（確保唔會變成每日一則）。
8. 還原演練（實做）：覆蓋 `settings.json.bak-<ts>` → `thr=` 回到動手前值；`git revert <sha>` → 新寫一行逐欄同動手前最後一行比對（除 timestamp/vram 等易變欄）。

## 5. 風險／最壞情況／還原（AGENTS 第一規則）

- **影響面**：3 個 module（self_monitor、self_review、settings）＋ conftest＋測試；行為影響＝報告內容、tuner 決策（SK 已批）、測試不再外呼。
- **最壞情況**：① 門檻被升到 0.75（JARVIS 更聾）→ 已由 §3.5 對稱控制 ＋ 上限飽和出 finding 緩解；且**動手前備份 settings.json**，一步可還原。② 新 finding 太敏感日日嘈 → 由穩定 fingerprint ＋ 去重 ＋ floor 由實測導出緩解。③ conftest 全域隔離搞壞其他測試 → 先跑全量 `pytest tests/` 做 baseline（記下現有紅項），改完全量對比。
- **還原（指名）**：
  1. code：單一 commit；`git revert <sha>`。
  2. **狀態**：`%APPDATA%\Jarvis\settings.json`（tuner 唯一會寫嘅真檔）→ 動手前 copy 成 `settings.json.bak-<ts>`；還原＝copy 返；驗證＝`grep wake_threshold` 回到動手前值 ＋ 跑一次 `self_monitor` 見 `thr` 不再變。
  3. log：`self_monitor.log` 只 append（唔改舊行）；舊行可以照 parse（新欄位缺席 → 走 baseline_insufficient 分支）。
- **唔准郁**：wake 捕音／STT／AEC／聲紋／mic 設定、alert_policy 決策、`_THR_MIN/_THR_MAX` 數值、`AGENTS.md`。（wake_threshold 只經 §3.5 邏輯改，且已獲 SK 批。）

## 6. 交付步驟

1. plan v2 → **R2 review（反方＋數字核實，兩條獨立 reviewer）**；未過 8:2 就再修（上限 3–4 輪）
2. `requesting-code-review` 準備 → cursor-agent 實作（**唔准 `--no-desktop`**）
3. Hermes 自驗 §4 逐條（親手，唔信自述）
4. Code review 兩輪（pass1 重構／pass2 三個月後脆弱位）→ 修完再 review
5. HANDOFF（當日 section 一行）＋ commit（唔 push）

## 7. 明確唔喺本輪做

- 真正減少誤觸（收音／喚醒／新 mic／headset 休眠偵測）→ 等新 mic 後另開（**本輪承認：唔會減少誤觸次數**）。
- 「亂碼」語意判斷（LLM 分類）→ 唔做（SK 要 deterministic）。
- 舊 log 回溯重算／改寫歷史數字 → 唔做。
- `scripts/jarvis_self_monitor.py`（08-28 舊 copy，疑似死碼）→ 唔郁，另立 task。
- `Path.home()` 盲點嘅其他 3 個檔案（`memory.py`／`mouth.py`／`hermes_bridge.py`）→ 本輪只處理 settings 一個；其餘記錄待辦。
