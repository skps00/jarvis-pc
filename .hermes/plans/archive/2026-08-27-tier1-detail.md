# Tier 1 詳細 Implementation Plan（wake / STT / response 品質）

> 主 plan：`JARVIS_MASTER_PLAN.md`。本檔係 Tier 1 嘅**逐 Step 詳細執行方案**——具體到改邊行、改咗啲咩、點測試、點回滾。
> **原則：先睇晒呢個 plan 先開始寫 code。** 每個 Step 獨立、可單獨回滾。

---

## Step A2 — wake rearm 邏輯修復（叫唔醒元兇）🔴 最高優先

### 問題（已實證）

`wake.py` 而家嘅 rearm 邏輯：

```python
# wake.py callback 內（約 line 405-408）
best = _jarvis_score(scores)
if best < _REARM_BELOW:      # _REARM_BELOW = 0.25（line 16）
    armed = True
if armed and best >= threshold:   # threshold = 0.50
    _trip(...)
```

**Bug**：`armed` 要等 OWW 分數**跌到 < 0.25** 先重新武裝。如果環境有持續中等分數（0.25-0.5，例如 YouTube 有人聲、遊戲音效）→ `best` 從未 < 0.25 → `armed` 永遠 False → **叫極都唔醒**。

### 改動方案（加 rearm timeout）

**目標**：`armed` 唔淨靠「跌到好低」，而係「分數 < threshold 持續 N 秒」就重新武裝。

**位置**：`wake.py`
- line 16 附近加一個常量 `_REARM_TIMEOUT_S = 2.0`
- callback 內加一個 `nonlocal` 變數 `below_thr_since`（timestamp）
- 修改 rearm 邏輯

**具體改動（before → after）：**

```python
# BEFORE（現在）
if best < _REARM_BELOW:
    armed = True
if armed and best >= threshold:
    _trip(...)

# AFTER（改動）
if best >= threshold:
    below_thr_since = None
    if armed:
        _trip(...)
else:
    # 分數跌到 threshold 以下——計時，持續 _REARM_TIMEOUT_S 就重新武裝
    if below_thr_since is None:
        below_thr_since = time.time()
    elif time.time() - below_thr_since >= _REARM_TIMEOUT_S:
        armed = True
```

**要加嘅變數**：`below_thr_since` 要喺 callback 嘅 `nonlocal` 清單（同 `armed` 一齊），loop 開始 reset 為 `None`。

### 測試步驟

```bash
# 1. 語法檢查
python -c "import ast; ast.parse(open(r'src/jarvis/wake.py').read())"

# 2. 邏輯單元測試（用 fake scores 模擬）
#    寫個臨時 script：模擬「持續 0.3 分數 3 秒 → 應該 re-arm → 之後 0.6 分數 → 應該 fire」
#    （唔使真 mic，直接 call 邏輯 or 抽離做 test）

# 3. 真機測試
python -m jarvis serve
# 開 YouTube 播有人聲 BGM 30 秒 → 喊「hey jarvis」→ 應該醒（之前會叫唔醒）
```

### 驗證標準

- [ ] BGM 有人聲環境下，喊「hey jarvis」**3 次內醒**（之前會全 fail）
- [ ] 冇 BGM 時，正常喊 3 次全部醒
- [ ] 誤觸率冇明顯上升（BGM 30 秒冇亂醒）

### Rollback

```bash
git checkout src/jarvis/wake.py   # 或者還原 backup
```

### 風險

- 低。純邏輯加 timeout，唔影響 fire 條件（`armed and best >= threshold` 保留）。
- 如果 timeout 太短（例如 1s）可能 re-arm 太快——用 2.0s 保守值，實測微調。

---

## Step A — wake VAD 防誤觸

### 問題

openwakeword 而家冇用 `vad_threshold`（官方內置 Silero VAD）——非語音噪音（鍵盤、BGM、環境聲）會誤觸。

### 改動方案

**位置**：`wake.py` `_load_model()`（line 102-110）

**before：**
```python
return Model(wakeword_models=paths, inference_framework="onnx")
```

**after：**
```python
return Model(wakeword_models=paths, inference_framework="onnx", vad_threshold=0.5)
```

（另一處 fallback `return Model(inference_framework="onnx")` 都加 `vad_threshold=0.5`）

### 測試

```bash
python -m jarvis serve
# ① 開 YouTube 純音樂 30 秒 → 應該 0 誤觸
# ② 敲鍵盤 30 秒 → 應該 0 誤觸
# ③ 正常喊「hey jarvis」→ 應該照醒
```

### 驗證標準

- [ ] 純音樂/鍵盤 30 秒 0 誤觸
- [ ] 正常喊醒（vad_threshold 唔會擋真人聲）
- [ ] ⚠️ 有人聲 BGM 唔保證（VAD 會當語音）——呢個靠 A2 嘅 rearm + 後續 A3/A4 補

### Rollback

移除 `vad_threshold=0.5` 參數即可。

### 風險

- 低。官方參數。若 VAD 太嚴令叫唔醒 → 調低 0.3-0.4。

---

## Step B — STT GPU 加速

### 問題

`ear.py` `_get_sensevoice()` 冇 device 設定——SenseVoice 純 CPU 跑，5090 閒置。

### 改動方案

**位置**：`ear.py` `_get_sensevoice()`（line 88-92）

**before：**
```python
_sensevoice = AutoModel(
    model="iic/SenseVoiceSmall",
    trust_remote_code=True,
    disable_update=True,
)
```

**after：**
```python
import torch
device = "cuda:0" if torch.cuda.is_available() else "cpu"
_sensevoice = AutoModel(
    model="iic/SenseVoiceSmall",
    trust_remote_code=True,
    disable_update=True,
    device=device,
)
```

（`_get_fun_asr()` 都照樣加 `device=device`）

### 測試

```bash
# 實測 CPU vs GPU 耗時
python -c "from jarvis.ear import transcribe_wav; import time; t=time.time(); print(transcribe_wav('test.wav')); print(f'{time.time()-t:.2f}s')"
```

### 驗證標準

- [ ] GPU 版 STT 快 ≥3x（對比 CPU）
- [ ] 辨識結果同 CPU 版一致（冇因 GPU 而錯字變多）
- [ ] 若 funasr CUDA 相容性有問題 → fallback CPU（改動本身有 `torch.cuda.is_available()` guard）

### Rollback

移除 `device=device` 參數。

### 風險

- 中。funasr CUDA build 相容性要實測（已知 torch 2.13.0+cu132 + 5090 detect 到）。若 fail，替代 = faster-whisper int8（CTranslate2）。

---

## Step D1 — Streaming TTS（mouth 逐 chunk 即播）

### 問題

`mouth.py` `speak()` 而家一次過合成成句先播放（line 247-248）：

```python
chunks = list(voice.synthesize(text, syn_config=syn))
audio = b"".join(c.audio_int16_bytes for c in chunks)   # 等成句先有聲
```

### 改動方案

**位置**：`mouth.py` `_play()`（line 238-258）

Piper `voice.synthesize` 本身係 generator——逐 chunk 合成即播，唔 `b"".join` 等成句。

**方向（詳細實作時再定，但要遵循）：**
1. 用 `sounddevice.OutputStream`（streaming 播放）取代 `_play_once` 嘅整段播放
2. 逐個 `chunk.audio_int16_bytes` 餵入 OutputStream
3. `_play_lock` 保留（防同時播兩段）

**測試**：長句首音節出現時間，對比 before/after（用 time.time 計「開始合成到第一個 chunk 有聲」）。

### 驗證標準

- [ ] 長句（>20 字）首音節延遲明顯縮短（預期減 1-2s）
- [ ] 音質/節奏冇明顯變差（chunk 邊界）
- [ ] `_play_lock` 仍然有效（冇同時播兩段）

### Rollback

還原 `mouth.py` 到整段合成版本。

### 風險

- 中。chunk 邊界音質/節奏可能略變；OutputStream 要處理 buffer 大小。實測音質，若差就保留整段合成（此 Step 係優化唔係必需）。

---

## Step D2 — 先唸短確認「Yes, Sir.」

### 問題

LLM 回覆要等成段出先有聲，感知延遲高。

### 改動方案

**位置**：`shell_app.py` `_drain_queue` result handler（line ~1050-1069）

**方向：**
1. 收到 result（Hermes 回覆）→ 先唸「Yes, Sir.」（~0.6s）立即回饋
2. 同時正式 SPEAK 用 queue 依序播（配合 D1 streaming）
3. 加 settings 開關 `tts_ack`（預設 on，覺得煩可以關）

### 驗證標準

- [ ] 喊完 → ~1s 內有聲（「Yes, Sir.」），唔使等成段
- [ ] 正式回覆照常唸（英文）
- [ ] `tts_ack=false` 時唔唸確認句

### Rollback

移除 ack 呼叫。

### 風險

- 低。若覺得煩可關。同 D1 有依賴（D1 做完 streaming 先唸 ack 更順，但可獨立做）。

---

## Step D3 — 縮短「等講完」時間

### 問題

`wake.py` 而家等 640ms 靜音先收工，每句慳唔到。

### 改動方案

**位置**：`wake.py` 常量（line 22-26）

```python
_CMD_SILENCE_FRAMES = 8   → 5   # ~640ms → ~400ms 靜音即收
_STT_TRAIL_S = 0.5        → 0.35
```

### 測試

```bash
python -m jarvis serve
# ① 講「hey jarvis 開 Cursor」→ 句尾唔會被 cut
# ② 講長句中間停頓 → 唔會誤判收工
```

### 驗證標準

- [ ] 每句慳 ~300ms（講完 → STT 開始更快）
- [ ] 正常句尾唔會 cut 斷
- [ ] 句中停頓唔會誤判收工

### Rollback

還原兩個常量。

### 風險

- 中。太短會喺句中停頓誤判收工。實測後若斷句就還原或微調（6 frames / 0.4s）。

---

## Tier 1 完成定義（全部通過先算完成）

1. BGM 純音樂 30s → 0 誤觸
2. BGM 有人聲 → 喊「hey jarvis」3 次內醒（A2 修復驗證）
3. STT GPU ≥3x 快
4. 喊完 → 有聲 ≤3s（D1+D2+D3 合計）

---

## 執行順序建議

```
A2 → A → D3 → B → D1 → D2
```

- **A2 最先**：最高優先（叫唔醒）、最細、獨立可回滾
- **A、D3**：都係 `wake.py` 細改，可以一齊做（但分開測試，方便定位）
- **B**：`ear.py` 獨立，隨時做
- **D1 → D2**：D1（streaming）係 D2（ack）嘅基礎，先 D1 後 D2
