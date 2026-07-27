# 自訓英文 wake「jarvis」（openWakeWord）

預訓練只有 **Hey Jarvis**。要淨講 **Jarvis** 又準又輕 → 自訓一個 ONNX，放下：

`%APPDATA%\Jarvis\wake\jarvis.onnx`

（可多個 `*.onnx`；檔名含 `jarvis` 會自動載入。）

## 最快：Google Colab（約 1 小時）

1. 開官方 notebook：  
   https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb?usp=sharing
2. Target phrase 填：`jarvis`（或 `hey jarvis` 若只要加強）
3. Runtime → GPU → Run all，等訓練完
4. 下載產生嘅 `.onnx`
5. 建立資料夾並放入：

```powershell
New-Item -ItemType Directory -Force "$env:APPDATA\Jarvis\wake"
Copy-Item .\jarvis.onnx "$env:APPDATA\Jarvis\wake\jarvis.onnx"
```

6. 重啟 `JARVIS.vbs`／`python -m jarvis serve`  
   - 有自訂模型時會**自動關** SenseVoice 文字後備（慳 CPU）  
   - 日誌仍應見「聽候：開」

## 驗收

- 講 **Jarvis**（唔使 Hey）→ 開始錄音  
- 嘈雜環境誤觸少過 STT 後備
- 預設 OWW 門檻 **0.58**（再 arm 要掉到 **0.28**）；仍誤觸可再升 `DEFAULT_THRESHOLD`

## 備註

- Windows 本機全套訓練要 WSL2 + GPU，唔建議；用 Colab。  
- 未有自訂檔時：繼續用 hey_jarvis OWW + 英文 STT 後備。
- 自訓完記得重啟 serve；有 `*.onnx` 會關 SenseVoice 文字後備。
