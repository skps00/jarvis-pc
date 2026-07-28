# 自訓英文 wake「jarvis」（openWakeWord）

預訓練只有 **Hey Jarvis**。要淨講 **Jarvis** → 自訓 ONNX + **STT 後備**（hybrid）。

`%APPDATA%\Jarvis\wake\jarvis.onnx`

（可多個 `*.onnx`；檔名含 `jarvis` 會自動載入。）

## 聽候點解（hybrid）

1. **OWW**：同時載 **hey_jarvis**（Hey Jarvis）+ 自訓 `jarvis.onnx`（若有）
2. **STT 後備**：咪有聲但 OWW 分數唔夠 → 短錄音 → SenseVoice／cloud ASR 認 `jarvis`／`hey jarvis`／賈維斯
3. 門檻預設約 **0.35**（設定頁可改）

> 唔好開兩個 `jarvis serve`（會搶 mic）。日誌：`聽候中 — Jarvis（hey+custom+STT …）`；除錯：`%APPDATA%\Jarvis\wake_debug.log`

## 最快：Google Colab（約 1 小時）

1. 開官方 notebook：  
   https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb?usp=sharing
2. Target phrase 填：`jarvis`（或 `hey jarvis` 若只要加強）
3. Runtime → **GPU** → Run all，等訓練完
4. 下載產生嘅 `.onnx`（通常喺 notebook 輸出／Files 面板）
5. 安裝到 Jarvis（PowerShell，喺 repo 根目錄）：

```powershell
.\scripts\install_wake_onnx.ps1 -SourcePath $env:USERPROFILE\Downloads\jarvis.onnx
```

或手動：

```powershell
New-Item -ItemType Directory -Force "$env:APPDATA\Jarvis\wake"
Copy-Item .\jarvis.onnx "$env:APPDATA\Jarvis\wake\jarvis.onnx"
```

6. **重啟** serve（關舊 `pythonw`／tray → 再開 `JARVIS.vbs` 或 `python -m jarvis serve`）
   - 日誌應見：`聽候中 — Jarvis（custom+STT …）`
   - 設定頁門檻會套用（預設約 **0.35**）

## Colab 小抄

| 步驟 | 做咩 |
|--|--|
| GPU | Runtime → Change runtime type → T4／任何 GPU |
| Phrase | `jarvis`（細楷，短） |
| 跑完 | 睇有冇 `.onnx` 下載掣／Files |
| 失敗 | Runtime 斷線就再 Run all；唔好用 CPU |

## 驗收

- 講 **Jarvis**（唔使 Hey）→ 開始錄音
- 跟住講帶開動詞指令（例「開 Cursor」）
- 仍遲鈍：設定降門檻（例 0.25）；誤觸多就升（例 0.45）

## 備註

- Windows 本機全套訓練要 WSL2 + GPU，唔建議；用 Colab。
- 想更準：錄自己聲 50–300 段再訓（見社群 openwakeword-training），再覆蓋 onnx。
- 檔名／stem 要含 `jarvis`（例 `jarvis.onnx`、`my_jarvis_v1.onnx`）。
