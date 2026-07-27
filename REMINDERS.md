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

未知 `open xxx` → 搜尋開始功能表／Steam／Prism → Yes 則啟動並寫入 `profiles.yaml`。

查詢句（幫我查／怎樣／what is…）→ 只字幕（LLM 稍後）。

---

## ✅ 電源 — 關機／睡眠（Always Yes）

```
關機 / shutdown
睡眠 / sleep
```

細窗或 CLI 會問確認；拒＝唔執行。

---

## ⏳ 之後 — 查詢小 LLM

接上小模型 JSON；而家 query 只字幕唔答內容。

---

（完成後把本項移去「已完成」或刪除。）
