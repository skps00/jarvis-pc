# Cursor 指令（草稿；等 review 過 8:2 才派）

## 任務
改 `C:\Users\skps9\Documents\Code_Project\jarvis-pc` 一個檔 ＋ 加測試：修 `src/jarvis/self_monitor.py` 兩個假陽性源頭。

## 只准改
1. `src/jarvis/self_monitor.py`
2. `tests/` 新增一個測試檔（＋ `tests/fixtures/` 新增 3 個真 bytes fixture）
3. `src/jarvis/eval_gate.py` 嘅 golden 清單加新測試檔名

## 唔准改
`wake.py`／`alert_policy.py`／`scripts/hermes_alert_speak_once.py`／`settings.py`／`alert_store.py`／`hud/`；唔好跑 formatter 或改其他檔嘅格式。

## 改法（照抄，唔准自由發揮）
### A. err 良性過濾（`self_monitor.py` serve-err 計數段，現約 :124-138）
```python
_BENIGN_TB_MARKERS = ("ProactorBasePipeTransport", "_call_connection_lost")
_BENIGN_TB_CTX = 40  # lines each side; strip-join before matching
```
- 遇 `Traceback` 行：取 `lines[max(0,i-40):i+40]`，**`"".join(l.strip() for l in ctx)`** 後 substring 找 marker；命中 → 唔計 `err`，改 `benign_tb += 1`。
- 其他一切（真 exception／`UnicodeDecodeError`／`stream_err`）照計。
- 註釋要寫：*Windows asyncio proactor 連線關閉 noise；2026-09-22 量得 serve.log 30/30 屬此類；strip-join 係必要（loguru 會 80 欄硬換行）。*

### B. summary 加欄位
- 喺 `err=` 後面加 `benign_tb=<int>`（數字型；`_RE_KV` 已食）。

### C. `resp_lat` 門檻（`self_monitor.py` notable 段，現約 :299）
- `latency > 5.0` → `latency > 30.0`
- 註釋：*2026-09-22 實測 21 個樣本 min 6.0s / p90 26s；舊門檻 5.0s < 最小值 ⇒ 恆真。*

## 測試（`tests/test_self_monitor_benign_tb.py` 或現有 self_monitor 測試檔）
1. fixture 1 = 由真 `%APPDATA%\Jarvis\serve.log` 抽一段良性 traceback（原樣，~30 行）
2. fixture 2 = 同一段以 70 欄硬換行
3. fixture 3 = 由 `serve.log.bak-20260910.gz` 抽 3 條真事故 traceback block
4. 斷言：f1 → `err=0, benign_tb=1`；f2 → `err=0, benign_tb=1`；f3 → `err=3`
5. negative control：monkeypatch `_BENIGN_TB_MARKERS = ()` → f1 變 `err=1`；`resp_lat=8.0s` fixture → `notable=True`
6. 真 sample fixture 唔准用合成字串取代。

## 驗收（改完自己跑，貼輸出）
```
cd C:/Users/skps9/Documents/Code_Project/jarvis-pc
env -u PYTHONPATH "C:/Users/skps9/AppData/Local/Python/pythoncore-3.14-64/python.exe" -m py_compile src/jarvis/self_monitor.py
env -u PYTHONPATH "C:/Users/skps9/AppData/Local/Python/pythoncore-3.14-64/python.exe" -m pytest tests/test_self_monitor_benign_tb.py -q
env -u PYTHONPATH "C:/Users/skps9/AppData/Local/Python/pythoncore-3.14-64/python.exe" -m jarvis.eval_gate --lock
```
唔准 `git commit`／`git add`（Hermes 自己驗完才 commit）。
