# Phase 1: Game Session Detection 修復（game ready 誤報 + Steam 自動 cover）

> **For Hermes:** cursor-agent 執行（SK 規則：任何 code 改動經 cursor-agent）。Plan 已過 adversarial review（2026-09-02）。

**Goal:** 修「X is ready, sir.」誤報——前景切換（遊戲↔Discord）唔再觸發；Steam game 自動 cover（RunningAppID）；Minecraft server 唔誤判為 client。

**Architecture:** activity_monitor.py（Hermes scripts，cron 每分鐘一次性 process）由「前景-based 瞬間偵測」改為「running-game session 偵測」（Steam RunningAppID + process/cmdline 多來源），session 跨 tick 靠 file state 保持（latch）；sidecar `shell_app.py` game watch 改為 track game 名變化（由無到有先 alert），唔再靠瞬間 `game_started` flag。

**Tech Stack:** Python（winreg / subprocess / json / ctypes）、Windows registry（HKCU\Software\Valve\Steam\RunningAppID）、Steam appmanifest_*.acf、jarvis-pc sidecar。

---

## Context（2026-09-02 實測證據）

- **Bug root cause**：`activity_monitor.py` 用前景視窗 detect game。SK 玩 Minecraft 切去 Discord（前景唔係 game）→ 寫 `game=None`（`_write_game_event(None)` reset prev）→ 切返 Minecraft → `prev_game(None) != game` → `game_started=True` → sidecar game watch 報「Minecraft is ready, sir.」每次切換都報。
- **Sidecar watch 次要問題**：`shell_app.py:1695-1714` `elif not started: last_seen = None`——activity_monitor 大部分 tick 寫 `game_started=False`，watch 每分鐘 reset，令「一次 game session 只 alert 一次」失效。
- **Server edge case**：SK 開發 MC mod 會開 Minecraft server（java/javaw + 可能含「minecraft」字眼）——唔應該當 client game。
- **多 game 同時 running 係真實場景**（實測）：CS2（Steam RunningAppID=730, cs2.exe running）+ Minecraft（Prism 前景）同時開。
- **Steam 側可行**（實測）：`HKCU\Software\Valve\Steam\RunningAppID` 有值（730=CS2）；Steam library 18 個 appmanifest 讀到真遊戲名（Black Myth: Wukong 等）；foundry-warden 項目實測 RunningAppID 開 game 即 flip、退出歸 0。
- **Minecraft client cmdline 特徵**（實測，Prism）：`org.prismlauncher.EntryPoint` + classpath 含 `minecraft-1.19.2-client.jar`（`-client.jar` 尾）。Server 特徵：`-jar server.jar` / `nogui` / `DedicatedServer` / `paperclip` / `papermc` / fabric-server。

## 設計決定

### 1. running-game 偵測（多來源合併）
```python
def detect_running_games() -> list[str]:
    """Return sorted unique game names currently running (Steam + process + java client)."""
    games = set()
    # (a) Steam RunningAppID → appmanifest name（Steam 開住先有；真實 running，Steam 管理）
    appid = read_steam_running_appid()          # winreg HKCU\Software\Valve\Steam
    if appid:
        name = steam_game_name(appid)           # parse appmanifest_*.acf
        if name: games.add(name)
    # (b) 非 Steam process map（GAME_PROCESSES，不含 java——java 要 cmdline 分辨）
    for proc in running_process_names():        # tasklist / wmic 一次攞
        if proc.lower() in GAME_PROCESSES and GAME_PROCESSES[proc.lower()]:
            games.add(GAME_PROCESSES[proc.lower()])
    # (c) Java client（cmdline 分辨，server 排除）
    for pid, cmdline in java_processes_with_cmdline():
        name = java_client_game(cmdline)        # client jar / EntryPoint → "minecraft"; server → None
        if name: games.add(name)
    return sorted(games)
```

### 2. session game 選擇（前景優先 → 新 running → latch → 單一 fallback）
```python
# game_start_event.json 擴展為 {"game": name|None, "ts": epoch, "running": [names]}
# （向後兼容：只有 "game" key 都讀到）
prev = read_prev_session()                      # 舊 _read_prev_game() 改名但兼容舊格式
prev_running = prev.get("running")              # list | None（首次 tick 為 None）
running = detect_running_games()                # list[str]（Steam + process + java client）
fg_game = detect_game(fg)                       # 前景視窗 detect（沿用，只做優先級）
new_games = [] if prev_running is None else [g for g in running if g not in prev_running]
if fg_game and fg_game in running:
    game = fg_game                              # 1. 前景 game（玩家 active）
elif new_games:
    game = new_games[0]                         # 2. 新開嘅 game（multitasking：舊 game running 都報）
elif prev and prev.get("game") in running:
    game = prev.get("game")                     # 3. latch：上次 session game 仍然 running
elif len(running) == 1:
    game = running[0]                           # 4. 單一 running game 先 fallback（Steam 啱開未有前景）
else:
    game = None                                 # 首次 tick / 多 game 冇新 → 唔亂揀
game_started = bool(game and game != prev.get("game"))  # 由冇到有（或 game 轉變）先 True
_write_game_event(game, running)                # 每次 tick 都寫（含 ts + running 集合）
```

### 3. sk_activity.json 輸出（欄位語義不變，值更穩定）
- `game`：session game（SK 喺 Discord 期間仍 = 上次 game，只要 process 仲 running）
- `game_started`：只喺「無 session → 有 session」或「game 名轉變」嗰個 tick True（其餘 False）
- `state`：不變（前景-based playing/using/idle）
- `_write_game_event()` 更新為寫 `{"game": game, "ts": ...}`（None 時都寫 ts，方便 debug）

### 4. sidecar game watch（shell_app.py）
```python
# 舊：依賴 started flag + reset（每次 False 都 reset → 重複 alert）
# 新：track game 名
last_game = None
while ...:
    data = load_activity() or {}
    game = data.get("game")
    if game and game != last_game:
        last_game = game
        enqueue_alert("game", f"{game_ready_phrase(game)} is ready, sir.")
    elif not game:
        last_game = None
    wait(5.0)
```

## Files

| File | Change |
|---|---|
| `C:\Users\skps9\AppData\Local\hermes\scripts\activity_monitor.py` | 加 Steam helpers、java cmdline helpers、run() game 邏輯重寫 |
| `C:\Users\skps9\Documents\Code_Project\jarvis-pc\src\jarvis\shell_app.py` | `_start_game_alert_watch` 改 track game 名（~1695-1714） |
| `C:\Users\skps9\AppData\Local\hermes\skills\software-development\windows-background-automation\references\sk-machine-facts.md` 或 activity-monitor 相關 skill | 語義註明「game = running session，state = 前景」 |
| New: `C:\Users\skps9\AppData\Local\Temp\game_detect_smoke.py` | 驗證 helper 行為（temp，唔 commit） |

## Tasks（cursor-agent 執行；每個 task commit 或留 working tree 一次過驗證）

### Task 1: activity_monitor.py — Steam helpers
**Objective:** 讀 Steam RunningAppID + parse appmanifest 攞 game 名。

- Modify: `activity_monitor.py`（加喺 Game detection section 附近）
- Code（要加入）：
```python
_STEAM_REG = r"Software\Valve\Steam"
_STEAM_APPS = r"C:\Program Files (x86)\Steam\steamapps"

def read_steam_running_appid():
    """HKCU Software\\Valve\\Steam RunningAppID (REG_DWORD) → int | None."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STEAM_REG) as k:
            v, _ = winreg.QueryValueEx(k, "RunningAppID")
            return int(v) if v else None
    except OSError:
        return None

def steam_game_name(appid):
    """Parse steamapps/appmanifest_<appid>.acf → name (exclude non-games)."""
    import re
    p = os.path.join(_STEAM_APPS, f"appmanifest_{appid}.acf")
    try:
        txt = open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    m = re.search(r'"name"\s+"([^"]+)"', txt)
    t = re.search(r'"type"\s+"([^"]+)"', txt)
    name, typ = (m.group(1) if m else None), (t.group(1) if t else None)
    if not name:
        return None
    if typ and typ not in ("game",):          # application/demo/tool → skip
        return None
    if name.lower() in _STEAM_NON_GAME:        # 已知非遊戲（Wallpaper Engine 等）
        return None
    return name
```
- 加入 module 常數：`_STEAM_NON_GAME = {"wallpaper engine", "3dmark", "steamworks common redistributables"}`（按 SK 實測 appmanifest 18 隻 filter；可再加）
- **驗證**：`python -c "import sys; sys.path.insert(0, r'C:\Users\skps9\AppData\Local\hermes\scripts'); import activity_monitor as a; print(a.read_steam_running_appid()); print(a.steam_game_name(730))"` → 730 + Counter-Strike 2

### Task 2: activity_monitor.py — process + java cmdline helpers
**Objective:** 列出 running game processes（非 java）+ java client 分辨（server 排除）。

- Modify: `activity_monitor.py`
- Code（要加入）：
```python
import subprocess  # 已有?（確認頂部 import）

def running_process_names():
    """tasklist /FO CSV → set of lowercase process names (一次 call)。"""
    try:
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
                             text=True, encoding="mbcs", errors="replace", timeout=15,
                             creationflags=0x08000000).stdout
    except Exception:
        return set()
    names = set()
    for line in out.splitlines():
        parts = line.split('","')
        if len(parts) >= 2:
            names.add(parts[0].strip('"').lower())
    return names

def java_processes_with_cmdline():
    """[(pid, cmdline)] for java/javaw.exe (wmic 一次攞 Name+CommandLine)。"""
    try:
        out = subprocess.run(
            ["wmic", "process", "where", "name like '%java%'", "get", "ProcessId,Name,CommandLine", "/format:csv"],
            capture_output=True, text=True, encoding="mbcs", errors="replace", timeout=20,
            creationflags=0x08000000).stdout
    except Exception:
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split(",")
        if len(parts) >= 4 and parts[1]:
            try:
                rows.append((int(parts[1]), ",".join(parts[3:])))
            except ValueError:
                pass
    return rows

def java_client_game(cmdline):
    """Minecraft client vs server 分辨。client → 'minecraft'；server/其他 java → None。"""
    cl = (cmdline or "").lower()
    if "-client.jar" in cl or "net.minecraft.client.main" in cl or "org.prismlauncher.entrypoint" in cl:
        return "minecraft"
    return None  # server.jar / nogui / dedicatedserver / paperclip 一律唔當 game
```
- **注意**：`wmic` 喺新 Windows 可能 deprecated——若 wmic fail，fallback `powershell Get-CimInstance`（見 Pitfalls）；Phase 1 先 wmic（實測 work）＋ fallback 留 comment。
- **驗證**：`python -c "... print(a.java_client_game('...org.prismlauncher.EntryPoint...'))"` → minecraft；`print(a.java_client_game('java -jar server.jar nogui'))` → None；`print(a.running_process_names() & {'cs2.exe','javaw.exe','discord.exe'})`

### Task 3: activity_monitor.py — run() game session 邏輯
**Objective:** run() 用 session game 邏輯（前景→latch→fallback），`game_started` 由冇到有。

- Modify: `activity_monitor.py` `run()`（約 line 425-454）＋ `_read_prev_game`/`_write_game_event`（line 333-349）
- `_read_prev_game()` 改：讀新格式 `{"game": x, "ts": ..., "running": [...]}`，兼容舊 `{"game": x}`——回 dict `{"game":..., "running":...|None}`（舊格式 running=None）
- `_write_game_event(game, running)` 改：寫 `{"game": game, "ts": time.time(), "running": list(running)}`
- `run()` 中間（line 432-439 附近）改為 session 選擇邏輯（見「設計決定 §2」）
- **`state` 邏輯不變**（`classify()` 照舊：前景 game → playing）
- **驗證**：smoke script（Task 5）＋ 實測場景清單

### Task 4: shell_app.py — game watch track game 名
**Objective:** sidecar watch 唔靠瞬間 flag。

- Modify: `jarvis-pc/src/jarvis/shell_app.py` `_start_game_alert_watch`（約 line 1692-1714）
- 新邏輯：
```python
def _watch() -> None:
    from jarvis.activity import load_activity
    last_game = None
    while not self._game_watch_stop.is_set():
        try:
            data = load_activity() or {}
            game = data.get("game")
            if game and game != last_game:
                last_game = game
                self._enqueue_alert("game", f"{game_ready_phrase(game)} is ready, sir.",
                                    app="game", log_prefix="game alert")
            elif not game:
                last_game = None
        except Exception:
            pass
        self._game_watch_stop.wait(timeout=5.0)
```
- **驗證**：`env -u PYTHONPATH python -m py_compile src/jarvis/shell_app.py` + `env -u PYTHONPATH python -m jarvis.eval_gate --lock`

### Task 5: Smoke 驗證 script（temp）
**Objective:** 用真實本機狀態驗證 helper。

- Create: `C:\Users\skps9\AppData\Local\Temp\game_detect_smoke.py`（用 env -u PYTHONPATH python 跑）
- 內容：print read_steam_running_appid()、steam_game_name(730)、running_process_names() 交 game map、java_client_game 正反例、detect_running_games() 結果
- **期望輸出（SK 而家開 CS2 + Minecraft）**：`detect_running_games()` 含 counter-strike 2 + minecraft
- **多 game case**：模擬 run() 揀 game——`fg_game=None, prev_running=[minecraft], prev_game=minecraft, running=[cs2, minecraft]` → game 應該 cs2（新 running 優先）；`prev_running=None`（首次）＋ running=[a,b] → game=None（唔亂揀）；`running=[a]` → a
- 跑：`env -u PYTHONPATH "C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe" "C:\Users\skps9\AppData\Local\Temp\game_detect_smoke.py"`

### Task 6: 文件更新
- `windows-background-automation` skill 或 activity-monitor 相關 reference：註明新語義（`game` = running session、`state` = 前景 active、Steam RunningAppID 來源、java client/server 分辨）
- 本 plan 完成後更新 `jarvis-pc\.hermes\plans\REMAINING_WORK.md`（如有）

## 實測驗收（cursor-agent 完成 code 後，由 Hermes 執行）

1. `env -u PYTHONPATH python -m py_compile src/jarvis/*.py`（sidecar 全數）
2. Smoke script 輸出符合預期
3. **場景 A（核心 bug）**：SK 開 Minecraft 前景 → 等 1-2 tick（sk_activity.json game=minecraft）→ 切 Discord → 確認 sk_activity.json `game` **仍然 minecraft**（latch）→ 切返 Minecraft → 確認 **冇** game alert 再觸發（serve.log 唔加「game alert」行）
4. **場景 B（新 session）**：關 Minecraft → 1-2 tick 後 `game=None` → 再開 Minecraft → serve.log 出現一次「game alert: Minecraft is ready」
5. **場景 C（server）**：開 Minecraft server（server.jar/nogui）→ `game` 唔應該 = minecraft（除非 client 都開住）；冇「ready」alert
6. **場景 D（Steam）**：開 Steam game（前景）→ RunningAppID 反映 + `game` = Steam 遊戲名
7. **場景 E（multitasking：新 game 背景開）**：Minecraft 開住（背景 running）→ 開 CS2（Steam，未 focus，SK 喺 Discord）→ 1-2 tick 內 `game` = counter-strike 2（新 running 優先）→ serve.log 一次「game alert: Counter-Strike 2 is ready」；之後切去 CS2 前景 → game 保持 cs2 唔再報
8. `env -u PYTHONPATH python -m jarvis.eval_gate --all`（shell_app 改動後全套）

## Risks / Open Questions

- **R1. RunningAppID 殘留/Steam 關閉**：RunningAppID 只在 Steam running 時可信；Steam 關咗讀唔到（process layer 照 cover 非 Steam）。Steam game 喺 Steam 關閉時 running（少見）→ 靠 process map（GAME_PROCESSES 冇 Black Myth 等）→ miss；Phase 2 可加「appmanifest installdir → exe 存在性」驗證。
- **R2. wmic deprecated**：Windows 新版本 wmic 可能移除 → 要 fallback（Task 2 comment 留）。實測 2026-09-02 wmic work。
- **R3. 非 game Steam app（Wallpaper Engine/3DMark）**：RunningAppID 會 flip 俾佢哋 → `_STEAM_NON_GAME` filter（Task 1）。list 唔會全——加 config/常數管理。
- **R4. 兩個 game 同時 running 揀邊個**：前景優先＋latch；CS2 背景 + Minecraft 前景 → minecraft（實測場景）✓。若 SK 想「背景 game 都報 ready」，Phase 2 加。
- **R5. activity_monitor 每分鐘 tick**：game 開咗後最多 1 分鐘先 alert（現狀一致，冇 regression）。
- **R6. detect_running_games() 每 tick 成本**：tasklist + wmic 兩個 subprocess（~1-2s/分鐘）——可接受；未來 WMI Win32_ProcessStartTrace event-driven 可替代（Phase 3）。
- **Open**: steam_game_name filter 清單要唔要 user-config？Phase 1 先 hardcode 常數（YAGNI）。

## Acceptance Criteria

- [ ] 場景 A：前景切換唔再觸發「ready」
- [ ] 場景 B：真正新 session 先報一次
- [ ] 場景 C：Minecraft server 唔誤報
- [ ] 場景 D：Steam game 自動 cover
- [ ] eval_gate --lock / --all 過
- [ ] 文件語義已更新

---

## Status: ✅ 完成（2026-09-02）

- activity_monitor.py（hermes scripts）：process-based detection + Steam RunningAppID + session latch + flap guard + first-run prime——已應用（backup .py.bak）
- shell_app.py：watch 改 game_started 信號 alert——已 commit `ea38b22`
- **4 輪 adversarial code review**：11 findings 全部修復，final pass（security 0 / logic 0）
- 驗證：smoke（CS2+Minecraft 正確 detect）、8-scenario matrix、eval_gate regression+stress 過（golden 1 fail = `test_stt_stats` baseline 環境問題，與本改動無關）
- 剩餘：sidecar 重啟後 game watch 新邏輯先生效；SK 實測場景 A-E
