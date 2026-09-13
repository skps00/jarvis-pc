# ASR 修復計畫 — 本地 Fun-ASR-Nano（SK 2026-09-13 定案：③ 本地）

> 背景：sensevoice 對**短句粵語**系統性弱。09-11 全日 6 句 garble（serve.log `[ear] raw=` 實錘，例：
> `啊，我系金三衣人啊好利。`／`为来就系高通。`／`就是这样一个船。`），同日英文句轉得準 → 唔係環境噪音。
> SK 2026-09-13 揀 **③ 本地 Fun-ASR-Nano**（② MiMo 雲端已停服務，用唔到）。
> 規則遵守：安裝／試新 model 前已做 online review（見 §2），未經 SK 批准唔會改 live settings。

---

## 1. 現況（本機實查，唔係推測）

| 項 | 事實 |
|---|---|
| **code path 已存在** | `src/jarvis/ear.py:119 _get_fun_asr()`／`:262 transcribe_fun_asr()`／`:408 transcribe_path()` 已接好；model id `FunAudioLLM/Fun-ASR-Nano-2512`（fallback `iic/Fun-ASR-Nano-2512`） |
| **settings** | `settings.py:20 ASR_FUN_ASR = "fun_asr"`；`:68` 預設 `sensevoice`；`:195-200` clamp 已接受 `fun_asr` |
| **UI 已有選項** | `hud/settings.html:211` `<option value="fun_asr">` |
| **現行 live 值** | `%APPDATA%\Jarvis\settings.json` → `asr_provider: "sensevoice"` |
| **歷史** | 2026-08-07 試過：卡喺首次 `AutoModel` 下載／load（`指令音頻 3.2s` 後 busy）→ 當日加咗 **120s timeout ＋ sticky fail ＋ 自動回退 SenseVoice**，之後 SK 改返 sensevoice 就冇再試 |
| **從未驗過** | 準確度（短句粵語）完全未做過 A/B → 所以今次重點係**量化**，唔係重新開發 |
| **環境** | python 3.14.2｜funasr **1.3.29**（官方要求 ≥1.3.26 ✅ 唔使升級）｜torch 2.13.0+cu132｜模型未下載（HF cache 冇）｜C: 剩 251GB |

## 2. Online review（已做，2026-09-13）

- **來源**：官方 repo `github.com/FunAudioLLM/Fun-ASR`（通義實驗室／Tongyi Lab）、HF `FunAudioLLM/Fun-ASR-Nano-2512`、HF `Fun-ASR-Nano-GGUF`、funasr.com 官方 benchmark。
- **能力**：Fun-ASR-Nano-2512＝8 億參數（SenseVoice SAN-M encoder ＋ adaptor ＋ **Qwen3-0.6B** LLM decoder）；官方明寫中文支援 **7 大方言（含粵語）** ＋ 26 種地域口音；訓練數據數千萬小時。
- **同系另一 checkpoint**：Fun-ASR-MLT-Nano-2512（31 語言，含粵語）— 如 Nano 粵語唔夠好可試。
- **官方數字**：184 條中文測試 CER 8.30%（GGUF q8 CPU 單機）vs whisper.cpp 22–31%；量化 q4/q5/q8 三者 CER 差 ≤0.1%。
- **Windows 支援**：官方「已校驗 Windows llama.cpp/GGUF 包」（即係有零 Python 路線，見 §6 替代方案）。
- **風險未解**：官方 benchmark 係**普通話長音頻**；**短句粵語冇公開數字** → 必須用 SK 自己嘅聲做實測（§3 T2）。

## 3. 執行計畫（分階段，每階段獨立可停）

### T1 — 預先下載模型（低風險，唔改任何 live 行為）
- 背景進程、**CPU**、`torch.set_num_threads(4)`，唔搶 GPU（SK 打機中）。
- 用 `funasr.AutoModel(model="FunAudioLLM/Fun-ASR-Nano-2512", trust_remote_code=True, disable_update=True)` 觸發下載（HF hub 先行，失敗試 ModelScope `iic/...`）。
- 產出：下載 log ＋ 模型大小／sha256 清單。
- **唔會**改 settings、唔會載入 sidecar 進程。

### T2 — 真聲 A/B（關鍵驗收）
- SK 講 **5 句短粵語指令**（例如「開 Chrome」／「而家幾點」／「Minecraft 有咩新」），每句錄一次。
- 同一批 wav 分別過：① SenseVoice（現行）② Fun-ASR-Nano → 逐句對照表（原文／兩個轉寫／人判對錯）。
- 加現成樣本：`%APPDATA%\Jarvis\wake_recordings\my_real_samples\*.wav`（短句，做 sanity check）。
- **PASS 標準**：Fun-ASR 正確句數 **≥** SenseVoice ＋ 至少 2 句 garble 修好；而且延遲唔可以爆（目標：短句 ≤3s 出字）。

### T3 — 開關（要 SK 明確 go）
- 用 sidecar `POST /settings`（單一 writer，Bearer token）改 `asr_provider: "fun_asr"`；**唔好**手改 json。
- 生效方式：`ear._get_fun_asr()` 係 lazy load，下一次語音就用新 provider；唔使重啟 sidecar。
- **回滾**：同一個 endpoint 改返 `sensevoice`（一個欄位，秒級）。

### T4 — 真機驗收（用數字講話）
- 用 `serve.log` `[ear] raw=` 對比：**09-11 基線 = 6 句 garble／日**；目標 ≤1 句／日。
- 順手補：`stt_stats` 已有 repair_log 統計可做旁證。

## 4. 風險評估（第一規則：風險 → 最壞情況 → 還原）

| 風險 | 最壞情況 | 還原 |
|---|---|---|
| 模型下載 3GB 級 | 佔 disk（**C: 剩 251GB**，可接受）；下載中斷 = 半套 cache → 重下 | 刪 HF cache 目錄 |
| 首次 load 慢／卡（08-07 老問題） | sidecar 停喺「聽候」busy（有 120s timeout ＋ 自動回 SenseVoice，唔會死） | 改返 `sensevoice`；T1 預下載正正係為咗消除呢個風險 |
| funasr 1.3.29 對新 checkpoint 唔支援 | 載入失敗 → sticky fail → 自動 SenseVoice（**Fail-closed，唔會靜默出錯**） | 唔使做嘢（自動退）／必要時升 funasr（要另批） |
| VRAM／RAM 佔用 | 打機時多佔 ~2–3GB VRAM（lazy load，冇用時 0） | 設定關 `fun_asr`；或 `gpu_policy` 強制 CPU |
| 準確度反而差 | 語音指令更差 | T2 唔 PASS 就**唔開**（T3 唔執行），成本 = 一個下載 |

## 5. 唔做（範圍界線）
- 唔升級 funasr／torch（1.3.29 已足夠）。
- 唔改 wake／AEC／聲紋（等 SK 新 mic）。
- 唔動 `asr_repair` 邏輯（今次只換 ASR model）。
- 唔上 GGUF／CPU 路線（見 §6），除非 T2 顯示 GPU 路線有問題。

## 6. 替代方案（記錄備查，未選）
- **FunASR llama.cpp / GGUF**：encoder f16 470MB ＋ `qwen3-0.6b` q4km 484MB／q8 805MB，**零 Python、單一 binary**（whisper.cpp 式），官方有 Windows 校驗包。優點：唔使 torch、CPU 都跑到 8.3% CER。缺點：要另寫 adapter（現有 ear.py 係 funasr Python API）、串流／即時性要再驗。
- 若 T2 顯示「GPU ＋ funasr」路線唔掂（例如 VRAM 或載入時間問題）→ 轉 GGUF 路線。

## 7. 待 SK 決定
1. **T1 可即做？**（純下載，唔改 live 行為）→ ✅ **唔使做：模型早於 2026-08-07 已完整下載**
2. **T2 時段**：需要 SK 講 5 句短粵語（1 分鐘內完成）

---

## 8. 實測記錄（2026-09-13 14:0x，真跑）

### 8.1 T1 改為「已存在」— 證據
- `~/.cache/modelscope/models/FunAudioLLM--Fun-ASR-Nano-2512/snapshots/master/`：`model.pt` **2,127,426,538 bytes**（08-07 23:26）、`config.yaml`、`configuration.json`、`Qwen3-0.6B/`（tokenizer 全套）、`multilingual.tiktoken`；**冇** `.incomplete`／`.part` 殘留 → 完整。
- 注意：`~/.cache/modelscope/hub/models` 係另一個 layout（只有 piper）→ 之前「冇下載」嘅判斷係睇錯路徑。**唔使再下載，撤回 §3 T1 嘅 3GB 下載步驟。**

### 8.2 離線載入＋推理（CPU、4 threads、唔用 GPU）
| 項 | 實測 |
|---|---|
| Fun-ASR-Nano 載入（CPU） | **15.2s**（ckpt `All keys matched successfully`）→ **冇再現 08-07「似凍住」**（當時係下載卡住，唔係模型問題） |
| 每條 2 秒音檔推理 | Fun-ASR **0.60–1.17s**（rtf 0.19–0.59）；SenseVoice 0.14–0.39s |
| 記憶體 | 全程無 crash（CPU 模式） |

### 8.3 A/B 結果（現成 wake 練習樣本 5 條，2.0s each）
| clip | SenseVoice | Fun-ASR-Nano |
|---|---|---|
| 0001 | `proph .` | `dramas` |
| 0002 | `dvis .` | `DRIVERS` |
| 0003 | `dras .` | `dramas` |
| 0004 | `travis .` | `dramas` |
| 0005 | `ds .` | `DROVE US` |

**判讀（老實講）**：兩邊都出垃圾，**唔可以由此判高低** —— 呢 5 條係 wake 練習用嘅 2 秒碎片（好可能係「hey jarvis」被 VAD 截到尾音），唔係完整指令；兩個 model 都聽到類似「…travis/dramas（≈ jarvis）」嘅音，即係**音素對得上、但專名唔識**（正常，訓練集冇 SK 個名）→ 正式 pipeline 有 `_hotword_string()` 補 hotwords（CS2／Cursor／Jarvis 等）。
**結論：要判短句粵語準確度，必須用真指令句（T2）。**

### 8.4 T2 待做
- SK 講 5 句短粵語指令（例：「開 Chrome」／「而家幾點」／「Minecraft 有咩新」），同一批 wav 過兩個 model 對比。
- 錄音方式：由 Hermes 開錄音 script（`jarvis.ear.record_wav`）→ SK 照講；或等 SK 下次正常用語音時自動存 wav。

