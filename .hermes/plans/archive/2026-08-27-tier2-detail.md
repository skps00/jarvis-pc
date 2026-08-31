# Tier 2 詳細 Implementation Plan（Voice call 安全 + 聲紋）

> 主 plan：`JARVIS_MASTER_PLAN.md`。本檔係 Tier 2 嘅逐 Step 詳細方案。
> **前置**：Tier 1 全部完成先開始（見 Tier 1 完成定義）。
> 三個 Step 有依賴：A3（AEC）→ A4（聲紋）——A4 需要 AEC 先濾走喇叭聲，先分到本地聲。

---

## Step A3 — AEC（聲學迴聲消除）

### 目標

wake pipeline 加 AEC——濾走「喇叭出嘅聲」（voice call 對方聲 + 自己 TTS 迴聲），淨音入 openwakeword。一次過解決：① 對方 voice call 聲唔觸發 ② 自己 TTS 唔自觸發 ③ voice call 照叫照醒。

### 架構（新增音訊管道）

```
現在：mic → callback → openwakeword.predict()
改後：mic ─┐
           ├→ AEC（用 speaker reference 濾走喇叭聲）→ openwakeword.predict()
    speaker┘  （WASAPI loopback 攞 reference）
```

### 改動方案

**位置**：`wake.py` `run_wake_loop()`（line 490-505）+ `_callback`（line 380-470）

**Step 3a — 攞 speaker reference（WASAPI loopback）**
- 用 `sounddevice` 開第二條 stream，`WasapiSettings(loopback=True)` 攞喇叭輸出
- reference 同 mic 同步（同 samplerate 16kHz）

**Step 3b — AEC filter**
- Library：**`python-webrtc-audio-processing`**（WebRTC AEC3，業界標準）
- 喺 `_callback` 內：`mic_chunk - AEC(speaker_reference_chunk)` = 淨本地聲
- 淨音先入 `pcm_ring` + `model.predict()`

**Step 3c — 同步問題**
- mic 同 speaker loopback 兩條 stream 要對齊（時間差）——用同一 device 嘅 clock 或者 buffer 對齊
- 呢個係 AEC 最難嘅位，要 spike 驗證

### 測試

```bash
# 1. 裝 library
pip install python-webrtc-audio-processing

# 2. 先做 spike（獨立 script）：
#    開 YouTube 播人聲 → 錄 mic + loopback → 跑 AEC → 聽下淨音係咪冇咗喇叭聲

# 3. 真機測試
python -m jarvis serve
# ① 開 YouTube 播人聲 → 喊「hey jarvis」→ 應該醒（AEC 濾走人聲但保留你聲）
# ② JARVIS 自己 TTS 出聲 → 唔應該自觸發 wake
# ③ 開 Discord voice call → 對方講嘢 → 唔觸發；你喊 → 醒
```

### 驗證標準

- [ ] YouTube 人聲 BGM 下，喊「hey jarvis」醒（本地聲保留）
- [ ] JARVIS 自己 TTS 出聲唔自觸發
- [ ] voice call 對方講嘢唔觸發（待 SK 開 voice call 實測）

### Rollback

還原 `wake.py` + 移除 AEC library。

### 風險

- **高**（Tier 2 最難嘅 step）——同步問題（mic 同 loopback 對齊）係 AEC 最大挑戰。要 spike 先。
- 若 WebRTC AEC3 喺 Python 3.14 裝唔到 → 用 `speexdsp` fallback（效果較弱）。

---

## Step A4 — Speaker Verification（聲紋辨識）

### 目標

wake 觸發後，聲紋比對「係咪 SK 把聲」——屋企其他人（Pepper/Rhodey 場景）講嘢唔觸發。

### ✅ 已實測（2026-08-27）

- `speechbrain` ECAPA-TDNN 喺 Windows + Python 3.14 跑通
- 同人 cosine 0.9142 vs 異人 -0.02~0.20 → **threshold 0.5 完美分人**

### 改動方案

**位置**：`wake.py`（wake 觸發後、`_trip` 前）+ 新 enrollment script

**Step 4a — Enrollment script（新檔案 `scripts/enroll_voice.py`）**
- 錄 SK 30 秒聲（讀 mic）→ speechbrain 提 embedding → 存 `%APPDATA%/Jarvis/voice_profile.npy`（**加密**）
- 記低 mic device ID（換 mic 偵測用）

**Step 4b — Speaker gate（wake.py）**
- `_trip` 前：攞最近 ~1s 音訊 → speechbrain embedding → cosine 比對 profile
- `>= 0.5` → 係 SK → `_trip`；`< 0.5` → 唔醒
- 每次 wake 多 ~50-100ms（embedding 推論），可接受

**⚠️ 已知 pitfalls（實測）：**
- speechbrain `link_with_strategy` 喺 Windows symlink fail → monkeypatch 用 copy
- model 要 `huggingface_hub.snapshot_download` 落 local（唔好用內建 fetching）

### 測試

```bash
python scripts/enroll_voice.py   # 錄 SK 30 秒
# ① SK 喊「hey jarvis」→ 醒
# ② 播其他人聲喊「hey jarvis」（或用 SAPI 生成異人聲）→ 唔醒
```

### 驗證標準

- [ ] SK 自己喊醒（3/3）
- [ ] 異人聲唔醒（用 SAPI/錄音模擬）
- [ ] 換 mic 後提示重新 enrollment

### Rollback

移除 speaker gate + 刪 profile。

### 風險

- 中。真人聲 vs 合成聲測試有差異——真實使用要 SK 錄聲。
- 換 mic 會跌準確度 → 要重新 enrollment（已設計偵測）。

---

## Step chat_context — 社交場合偵測

### 目標

偵測「SK 而家喺 Discord/WhatsApp 同邊個傾偈」→ JARVIS proactive/speak 喺社交場合靜音。

### 改動方案

**位置**：`activity_monitor.py`（Hermes side）+ JARVIS gate 讀取

**Step 1 — activity_monitor 加 `chat_context` 欄位**
```python
# run() 內，classify 之後
chat = detect_chat_context(fg)   # 新 function
out["chat_context"] = chat

def detect_chat_context(fg):
    proc = (fg.get("process") or "").lower()
    title = fg.get("title") or ""
    if "discord" in proc or "whatsapp" in proc:
        # Discord 標題 = "@對象名 - Discord" 或 "群組名 - Discord"
        name = title.split(" - ")[0].strip()
        is_self = name.startswith("@JARVIS")  # 同 JARVIS 自己
        return {"platform": "discord" if "discord" in proc else "whatsapp",
                "chat": name, "is_self": is_self}
    return None
```

**Step 2 — JARVIS gate 讀取**
- proactive / MCP speak 前讀 `sk_activity.json` 嘅 `chat_context`
- `chat_context` 存在且 `is_self=false` → 靜音（社交場合）

### 驗證標準

- [ ] Discord 同人 DM → `chat_context.is_self=false`
- [ ] Discord 同 JARVIS → `is_self=true`
- [ ] 其他 app → `chat_context=null`

### 風險

- 低。純標題解析。Discord 標題格式可能變（版本更新）——加 fallback（解析唔到就當 `is_self=false` 保守靜音）。

---

## Tier 2 完成定義

1. voice call 對方聲唔觸發 wake（A3 + 實測）
2. JARVIS 自己 TTS 唔自觸發（A3）
3. 屋企異人聲唔觸發（A4）
4. 社交場合 JARVIS 唔 proactive（chat_context）
5. SK 自己喺任何場景都叫得醒

---

## 執行順序

```
A3（AEC，最難，先 spike）→ A4（聲紋，已實測）→ chat_context（最簡單）
```

- **A3 先做**：A4 依賴 AEC 先濾喇叭聲；A3 要 spike 驗證同步
- **chat_context 獨立**：唔依賴 A3/A4，可以隨時做
