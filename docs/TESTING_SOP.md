# JARVIS 測試 SOP（2026-08-28 更新）

> 測試次序按重要度。每項有：準備 → 步驟 → 預期 → 出問題點睇。
> Log 位置：`%APPDATA%\Jarvis\wake_debug.log`（wake）、`serve.log`（serve）、`self_monitor.log`（統計）

---

## T1. Wake 叫醒（最核心）⭐

**準備**：戴住 Arctis（headset 有電）；YouTube BGM 開唔開都得
**步驟**：
1. 對 mic 講「**hey jarvis**」（正常音量）
2. 預期：Companion 狀態燈變「● 處理中」+ 聽到「**Yes, Sir.**」回應
**預期**：叫醒成功率 >80%（以前 0.31-0.35 邊緣，AGC 後應該升）
**出問題**：
- 冇反應 → `tail -20 %APPDATA%\Jarvis\wake_debug.log`：
  - `rms=0.000` = mic 斷/休眠（Arctis 問題，唔係 JARVIS）
  - `agc_gain=8.0` + `rms=0.0xx` = AGC 幫緊手但 OWW 分數唔夠（睇 `peak_best`——如果 0.20-0.29 差一線 → threshold 降 0.25）
  - 冇 `wake_heartbeat` = serve 死咗 → 睇 `/health` + watchdog

## T2. BGM 誤觸（AEC 效果）

**準備**：YouTube BGM 開住（Sonar Media channel）
**步驟**：
1. 唔好講嘢，等 30 秒
2. 預期：**0 次誤觸**（JARVIS 唔會突然出聲）
**出問題**：誤觸 → 睇 wake_debug `peak_best`——如果 BGM 期間 >0.30 → AEC 未濾乾淨（可能要加 reference 或者降 threshold）

## T3. Voice call 場景

**準備**：Discord/WhatsApp voice call 開住（對方出聲）
**步驟**：
1. 對方講嘢 → 預期：JARVIS **唔醒**（voice_call gate + AEC）
2. 你叫「hey jarvis」→ 預期：**照醒**（AEC on 時唔 pause wake）
3. JARVIS 回覆 → 預期：對方**聽唔到** JARVIS（ack/alerts muted）
**出問題**：對方聲觸發醒 → 睇 `sk_activity.json` 嘅 `voice_call` 有冇 true（要活動監控 detect 到）

## T4. GUI（tray → Companion / Settings）

**準備**：無
**步驟**：
1. 系統 tray 搵 JARVIS 藍色圓點 icon → 撳右鍵
2. 預期 menu：顯示 HUD / 顯示 Companion / 顯示 Dock / 設定 / 退出
3. 開「顯示 Companion」→ Iron Man 面板（狀態燈 + 回覆記錄）
4. 開「設定」→ 基本欄位 + 三個進階 section（LLM / Hermes / 提醒）
5. 改 threshold（例如 0.35→0.30）→ 儲存 → `wake_debug.log` 下次 `wake_loop_start thr=` 應該係 0.30（mtime cache 已修，唔使重啟）
6. 撳「播放測試音」→ 螢幕喇叭出聲

## T5. Minecraft ready alert

**準備**：冇開 MC
**步驟**：
1. 開 Minecraft（入到主選單/世界）
2. 預期：JARVIS 講「**Minecraft is ready, sir.**」一次
**出問題**：冇聲 → 睇 `sk_activity.json` `game_started` 有冇 true + serve.log 有冇 alert log

## T6. Mage-VL 睇圖（眼）

**準備**：無（model 已喺 cache）
**步驟**：
```powershell
cd C:\Users\skps9\Documents\Code_Project\jarvis-pc
python scripts\mage_vision.py C:\Users\skps9\Documents\Code_Project\jarvis-pc\examples\dog.jpg "What is in this image?"
```
**預期**：load ~8s + 一句描述
**語音版**：settings 開 `mage_enabled: true` → 講「睇圖 C:\path\image.png」→ JARVIS 描述
**注意**：首次 load ~8s + VRAM +9.5GB（唔好打緊機嗰陣用）

---

## 快速診斷 cheat sheet

| 症狀 | 睇咩 |
|---|---|
| 叫唔醒 | `wake_debug.log` rms / agc_gain / peak_best |
| 誤觸 | `wake_debug.log` 有冇 oww_fire（無 command） |
| 冇聲回覆 | `serve.log` TTS fallback / `mouth` device |
| serve 死 | `/health`（urllib）或 `Get-NetTCPConnection -LocalPort 8765` |
| 狀態燈唔郁 | `%APPDATA%\Jarvis\voice_status.json` |
| 全部唔 work | `self_monitor.log` 統計 + 重啟 HUD（tray 退出 → 再開） |
