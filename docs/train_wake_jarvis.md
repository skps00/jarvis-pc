# 自訓英文 wake「jarvis」（最準路徑）

目標：淨講 **Jarvis** 就醒。預訓練只有 **Hey Jarvis**。

模型路徑：`%APPDATA%\Jarvis\wake\jarvis.onnx`

---

## 最準做法（推薦）：自己聲 1000+ + TTS trainer

官方 Simple Colab = 淨合成音 → 對你咪／口音弱（已驗證分數≈0）。  
**要準：大量自己聲 + Kokoro TTS 混訓**（真實聲通常加權更高）。

### Step A — 本機錄音（目標 1000）

1. **先關** Jarvis serve（搶咪會錄空）
2. Repo 根目錄：

```powershell
.\scripts\record_jarvis_wake.ps1 -Target 1000
```

或：

```powershell
python scripts\record_jarvis_wake.py --target 1000 --seconds 2.0
```

3. 每次 **Enter** → 倒數 → 講 **「Jarvis」**（自然、短）
4. 鍵：`r` 重錄上一段｜`p` 回放｜`s` 進度｜`q` 離開
5. 輸出目錄：

`%APPDATA%\Jarvis\wake_recordings\my_real_samples\`  
檔名：`jarvis_0001.wav` …（16 kHz mono，同 CoreWorx `my_real_samples/`）

**錄音提示：** 快慢、大細聲、遠近、轉頭；可分幾日錄，腳本會接續編號。

### Step B — 訓練（CoreWorxLab + Docker + NVIDIA GPU）

需要：NVIDIA GPU、Docker + NVIDIA Container Toolkit、約 20GB 碟。

```powershell
git clone https://github.com/CoreWorxLab/openwakeword-training.git
cd openwakeword-training
```

把錄音資料夾放進／複製成 repo 內 `my_real_samples\`（內容係你啲 `jarvis_*.wav`）。

```powershell
docker compose build trainer
docker compose run --rm trainer ./setup-data.sh
docker compose run --rm trainer python train.py --wake-word "jarvis" --data-dir /app/data
```

訓練可能 **數小時**。完成後取：

`my_custom_model/jarvis.onnx`（或同等路徑下嘅 `.onnx`）

> 無本地 GPU：可用有 GPU 嘅雲機跑同一 Docker；唔建議再靠官方 Simple Colab 淨 TTS。

### Step C — 安裝到 Jarvis

```powershell
cd C:\Users\skps9\Documents\Code_Project\jarvis-pc
.\scripts\install_wake_onnx.ps1 -SourcePath .\path\to\jarvis.onnx
```

重啟 serve（關 tray → 再開 `JARVIS.vbs`／`pythonw -m jarvis serve`）。

### Step D — 驗收

- 淨講 **Jarvis** → 自動錄音
- 跟住 **「開 Cursor」**（要有開動詞）
- **Hey Jarvis** 仍應可用（內建 hey_jarvis）
- 誤觸多 → 設定升門檻（0.45–0.55）；太鈍 → 降（0.3）
- 除錯：`%APPDATA%\Jarvis\wake_debug.log`／`wake_status.txt`

---

## 聽候點解（而家 main）

1. **推薦**：Hermes Voice `hey_jarvis`／自訓 onnx + `voice.barge_in`（見 `docs/hermes_voice_smoke.md`）；Jarvis `voice_frontend=hermes`
2. **Jarvis OWW 後備**：設定語音前端=Jarvis → `hey_jarvis` + 自訂 `jarvis.onnx`（若有）
3. **STT 後備**：OWW 唔夠分時短窗 ASR（淨 Jarvis 過渡用；有強 onnx 後可少靠）
4. 唔好開兩個 wake（Hermes + Jarvis）搶 mic；亦唔好開兩個 `jarvis serve`

### 掛自訓 onnx 去 Hermes

模型：`%APPDATA%\Jarvis\wake\jarvis.onnx`  
喺 Hermes `config.yaml` 將 `wake_word.openwakeword.model`（或文檔嘅 `model_path`）改成該檔**絕對路徑**（例 `C:/Users/.../AppData/Roaming/Jarvis/wake/jarvis.onnx`）。欄位名跟 Hermes 版本。

---

## 備註

- 檔名／stem 要含 `jarvis`（例 `jarvis.onnx`）
- 負樣本唔好用同音近義（官方／CoreWorx：用 hello／alexa 等明顯唔同句）
- 第一次可先 300 段試跑；**1000+ 通常更準、更穩**
- SOUL／個性：Hermes profile 或 SOUL.md 寫「Jarvis」短英管家口吻；Jarvis Piper 只讀英文 SPEAK／alert
