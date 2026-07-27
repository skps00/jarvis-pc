# Reminders（給未來的自己／Agent）

## ✅ 現況 A — 打字優先

熱鍵／細窗／CLI 打字 → router → Hands。Chrome 多窗靠「結束 Google Chrome」存 session。

```powershell
python -m jarvis serve
python -m jarvis -c "開 Cursor"
python -m jarvis autostart on    # 開機自啟
```

---

## ✅ B — 本機 SenseVoice（Ear）已接骨架

```powershell
python -m pip install -e ".[ear]"   # 首次會下載模型，較大
python -m jarvis listen 3
# 或 serve 視窗撳「語音」
```

語言預設 `yue`。未裝依賴會字幕提示。

---

## ✅ v1.1 — Discover & Confirm（已接）

未知 `open xxx` → 搜尋：

- Start Menu `.lnk`
- Desktop `.lnk`
- `%LOCALAPPDATA%\Programs` exe
- `Get-StartApps`（含 Store／UWP，例如 WhatsApp）
- Steam／Prism

Yes → 啟動並寫入 `profiles.yaml`（`shell_app` 用 `shell:AppsFolder\AppID`）。

開／關目標會對本機 app 索引做 **拼寫近匹配 + 粵拼（ToJyutping）** 自動改寫（例如 whatapp→WhatsApp、漢字／jyutping→中文名）。

查詢句見下方「查詢小 LLM」。

---

## ✅ 電源 — 關機／睡眠（Always Yes）

```
關機 / shutdown
睡眠 / sleep
```

細窗或 CLI 會問確認；拒＝唔執行。

---

## ✅ 查詢小 LLM + 歧義 JSON

```powershell
copy .env.example .env
# 填 JARVIS_LLM_API_KEY=（預設 DeepSeek；換 BASE_URL／MODEL 可用 GLM）
```

- `幫我查…`／`怎樣…` → 小模型短答字幕（唔開 app）
- 規則 refuse／unknown 且像開場 → LLM JSON → registry 再解析 → Hands
- 無 key：開場仍用規則；查詢只 stub 字幕

---

（完成後把本項移去「已完成」或刪除。）
