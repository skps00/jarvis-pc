# HUD App 插件化（HoloMat H1）Implementation Plan

> **狀態：計劃書，未開工。要 SK 明確批准先實作。**
> 來源：Concept Bytes《I Engineer Like Tony Stark! (Introducing the HoloMat)》 https://youtu.be/Yrj8bTTsQ2I
> （SK 2026-09-27：「mark it to jarvis plan, we done it in future」；本檔 = 把 H1 由一句想法變成可執行計畫）

**Goal：** 令 JARVIS HUD 加一件 widget 唔再需要改 `main.js`／重新 build／換版——把 widget 檔掉入一個目錄，HUD 下次載入自動出現。

**Architecture：** 主程序（`hud/main.js`）新增一個 **app registry**：開機掃 `apps` 目錄 → 讀 `app.json` → 把 `app.js` 注入 renderer → renderer 用穩定 API 註冊／掛載。app 跑喺 renderer（**冇 Node 權限**），要嘅能力全部經 preload 嘅白名單 API 提供。

**Tech Stack：** Electron 33（現有）／純 JS（唔加第三方依賴）／`contextBridge` + IPC。

---

## 1. 現狀（2026-10-07 實測）

| 項 | 實況 |
|---|---|
| `hud/main.js` | 825 行，4 個頁面寫死（`renderer/index.html` HUD／`companion.html`／`home.html`／`settings.html`）＋各自 preload |
| apps／plugins 目錄 | **冇** |
| 加一件 widget 成本 | 改 `main.js` → bump version → `npm run dist` → 換版（殺 5 個 JARVIS 進程）→ 人手驗收 |
| 打包方式 | electron-builder **portable exe**；app 內容喺 `app.asar` 入面（**唯讀**，唔可以 runtime 加檔） |
| 前置 | Slice 1 側車修復已落地（0.4.14）；Slice B log 輪替進行中（0.4.15）→ 前置已滿足 |

## 2. 業界做法（research；照 SK「設計前先查」規則）

- **Electron 官方 Security checklist**（https://www.electronjs.org/docs/latest/tutorial/security）：① 唔准為 remote content 開 `nodeIntegration`；② **全部 renderer 開 context isolation**；③ 要嘅能力用 **preload + `contextBridge` 暴露有限 API**；④ 定義 CSP（`script-src 'self'`）。→ 即係 widget **唔可以**直接 `require('fs')`／`shell`，一定要經白名單 API。
- **同類產品取態**：VS Code Extensions／Obsidian plugins／Figma plugins 都係「目錄掃描 + manifest + 有限 API」；三者共同承認嘅 tradeoff 係：**有權寫入 plugins 目錄嘅檔＝可執行代碼**（同管理員同等信任），所以要明文寫出嚟，唔好當佢係沙盒。
- **asar 限制**：打包後 `app.asar` 唯讀 → 插件目錄**必須喺 asar 以外**（`%APPDATA%\Jarvis\apps`），否則「掉檔即用」根本做唔到。

## 3. 設計決定（含替代方案）

### D1. apps 目錄解析順序
`JARVIS_APPS_DIR`（env，測試用）→ `%APPDATA%\Jarvis\apps`（正式）→ `<repo>/hud/apps`（dev）。
> 同 `settings_dir()` 用同一套「呼叫期解析」pattern（2026-10-06 已落地），保持一致、可測。

### D2. 一個 app ＝ 一個目錄
```
%APPDATA%\Jarvis\apps\hw-ring\
  app.json      # { "id":"hw-ring", "name":"負載環", "icon":"◎", "api":["sensors"], "size":[220,160] }
  app.js        # renderer 代碼；export register(Jarvis)
  README.md     # optional 開發說明
```
- 只有 `app.json` 係必需；`app.js` 缺席＝純靜態卡（可接受 v1）。
- **唔引入第三方依賴**（同 REMAINING_WORK 邊界一致）。

### D3. 注入方式（三選一，建議 a）
| 方案 | 做法 | 取捨 |
|---|---|---|
| **a（建議）** | main 讀 `app.js` 文字 → `webContents.executeJavaScript()` 注入 renderer | 最簡單、唔使改 CSP；代碼同 HUD 同一個 context |
| b | 每個 widget 開 sandboxed `<iframe>` + `postMessage` | 隔離最好，但要另寫 bridge（v2 硬化方向） |
| c | preload 動態 `require` widget | ❌ 直接俾 Node 權限，違反 Electron 官方指引 |

### D4. Widget API（v1 白名單，全部經 preload `contextBridge` 暴露）
`Jarvis.register({id, mount(el), unmount?, tick?})`、`Jarvis.sensors()`（CPU/GPU/RAM/NET）、`Jarvis.speak(text)`、`Jarvis.alerts()`、`Jarvis.media()`、`Jarvis.settings(name)`、`Jarvis.log(msg)`。
- **冇** `fs`／`child_process`／`shell`／任意 IPC channel。
- 每個 app 要喺 `app.json` 聲明 `api` 清單；未聲明嘅 API 呼叫會被 preload 擋（fail-loud，寫 log）。

### D5. 出錯唔可以拖死 HUD
單個 app 讀唔到／語法錯／mount throw → 只跳過該 app ＋ 寫 `%APPDATA%\Jarvis\app_error.log`（帶 app id），HUD 照行。

### D6. 版面模式（SK 2026-10-08：兩者都要，可切換）
- 預設 **carousel**（一條固定 band，app 自動排隊，零重疊）。
- `app.json` 可寫 `x`／`y`（自由擺位）；HUD 設定有 **「自動排列 / 自由擺位」** 單選（存 settings，即時生效，唔使重啟）。
- 自由擺位下仍要**重疊檢查**（SK 硬要求）：新 app 撞位 → 自動讓位（落／右搵空位）＋寫 log；**唔准靜默重疊**。

### D7. 螢幕（SK 2026-10-08：v1 主螢幕 only，v2 兩邊）
- v1：`app.json` `monitor` 只認 `"primary"`（唔寫＝primary）；其他值 → log 一行跳過。
- v2：多螢幕（要處理副螢幕 1080×1920 **直向** 同橫向 HUD layout 嘅衝突＋DPI）。

### D8. 熱重載（研究見 §8；建議：v1 手動 reload ＋ dev-only watcher）
- **默認（生產）**：加／改 app 之後重啟 HUD，或者撳設定面板一粒 **「重新載入 apps」**。
- **dev-only watcher**（`JARVIS_APPS_WATCH=1`，業界一致做法＝只喺 dev 開）：`fs.watch(apps 目錄)` → **debounce ~700 ms** → 舊 instance `unmount()` → 重讀 `app.js` → `executeJavaScript` 重注入 → `register()`。
- **fail-loud**：unmount 冇做／重掛 throw → 寫 `app_error.log`（app id ＋ 原因），唔准靜默。
- 明文：熱重載**唔係沙盒**；widget 自己有責任 `unmount()` 清 listener／interval，否則只會不斷疊。

## 4. Tasks（bite-sized；每步都要可驗）

**Task 0：寫一份最小 app 做樣板**
- Create: `hud/apps/hw-ring/{app.json,app.js,README.md}`（用現有 `hw_monitor.py` 數據）
- 驗證：檔案存在 + `node --check hud/apps/hw-ring/app.js`

**Task 1：main 側 registry（掃目錄 + 讀 manifest）**
- Modify: `hud/main.js`（新區塊，唔好掂現有 4 頁邏輯）；另加 D6 版面模式切換 ＋ D8「重新載入 apps」掣（v1 要做，唔靠重啟）
- 新增 `resolveAppsDir()`（D1 順序）、`loadAppManifests()`（讀 `app.json`，壞 JSON → 跳過 + log）
- 驗證：`node --check hud/main.js`；起 dev instance（`JARVIS_OPEN_HOME=1`）→ console 印出掃到幾個 app

**Task 2：注入管道（D3-a）**
- Modify: `hud/main.js`（`did-finish-load` 之後注入清單內嘅 `app.js`）
- 驗證：dev instance 內 CDP `Runtime.evaluate("Object.keys(window.Jarvis||{})")` 見到 API

**Task 3：preload 白名單 API（D4）**
- Modify: `hud/preload.js`（加 `contextBridge.exposeInMainWorld('Jarvis', {...})`），IPC handler 集中一個檔尾區塊
- 驗證：CDP 叫 `Jarvis.sensors()` 回真數字（同 `nvidia-smi` 對得上）

**Task 4：renderer 掛載點 + carousel**
- Modify: `renderer/index.html`（加一個空 container + 由 registry 生成嘅 app 卡；**唔改**現有元素）
- 驗證：dev instance 見到 hw-ring 卡；`layout_check.js` 量重疊 = 0（SK 要求每次改動後檢查元素重疊）

**Task 5：錯誤隔離 + log（D5）**
- Modify: `hud/main.js`（`try/catch` + `app_error.log`）
- 驗證：故意放一個壞 `app.json` → HUD 照起、log 有一行、其他 app 照掛

**Task 6：文檔 + 換版**
- Modify: `hud/apps/README.md`（點寫一個 app）、skill `jarvis-hud-electron-editing-pitfalls`（加一節：換版後 apps 目錄唔受影響／診斷法）
- 換版：bump `0.4.15` → `0.4.16` → `npm run dist` → `swap_hud_version.ps1 -Version 0.4.16`
- 驗證：真 exe 見到 app 卡；`%APPDATA%\Jarvis\apps\` 掉入第二個 app → 重啟 HUD 即出現

## 5. Tests / Validation

- `node --check` 所有改過嘅 JS。
- dev instance + CDP（skill §15；WS URL 每次重新 fetch）驗 DOM 同 API 回值。
- **負控**：壞 manifest、語法錯 app.js、`app.js` 讀唔到 → HUD 三次都要照起（呢個係 D5 嘅驗收）。
- `layout_check.js` 重疊 = 0。
- 真 exe 換版後：5 個 JARVIS 進程 + `8765/8770/8771/8642` LISTEN + `/health` 200（用 python urllib，唔用 curl）。

## 6. Risks／Tradeoffs／Open Questions

1. **安全（最大）**：任何寫得入 `apps\` 目錄嘅檔＝可執行代碼（同 Obsidian／VS Code 同級信任模型）。v1 接受，但要明文寫低；v2 可換 iframe 沙盒（D3-b）。
2. **executeJavaScript 唔受 CSP 限制**：方便但等於繞過一層保護；如果將來 HUD 會載 remote content，就要改用 D3-b。
3. **效能**：HUD 已經係全屏透明 overlay；widget 要用 transform/opacity-only、`pointer-events:none`（SK 2026-09-01 規則：**視覺一定要綁真數據，唔准純裝飾**）。
4. **已定（SK 2026-10-08 答）**（原文三條待決如下，答案見後）：
   - 原問：carousel（照影片）定自由擺位（x/y 由 `app.json`）？→ **兩者都要，用戶可切換**（SK：「both, user can switch it」）＝ D6。
   - 原問：HUD 主螢幕 only，抑或可以指定副螢幕？→ **v1 只主螢幕，「兩邊都要」做 v2**（SK：「both, we can done it in v2」）＝ D7。
   - 原問：v1 要唔要熱重載？→ 先答「**how other work?**」＝ 業界研究（§8）＋ D8 建議。
5. **範圍控制**：唔改現有 4 頁、唔加第三方依賴、唔抄影片 UI（REMAINING_WORK 邊界）。

## 7. Non-goals（v1 唔做）

- 唔做 app 市集／下載／更新機制。
- 唔做權限 UI（只用 `app.json` 聲明 + 擋）。
- 唔做跨機同步。
- 唔改動 voice／mic 線（HOLD 中）。


---

## 8. 業界研究：插件「熱重載」點做（SK 2026-10-08「how other work?」；Hermes 同日查，附一手來源）

| 產品 | 做法 | 出處 |
|---|---|---|
| **Obsidian** | Plugin lifecycle＝`onload()`／`onunload()`；官方明文：disable 時**必須喺 `onunload()` 釋放資源**，否則 app 會變不穩定。第三方 `pjeby/hot-reload`（**972★、ISC、未封存、2026-07 仍有更新**）＝ **watch `main.js`／`styles.css` → debounce ~0.75 s → disable → enable**，**只對**含 `.git` 或 `.hotreload` marker 嘅 plugin 目錄生效（＝dev-only gate）。手動路：`app.plugins.disablePlugin(id)` → `enablePlugin(id)`。 | docs.obsidian.md「Anatomy of a plugin」；github.com/pjeby/hot-reload；forum.obsidian.md/t/12185 |
| **VS Code** | 擴展**冇** hot reload：改完要人手 `Developer: Reload Window`／重啟 Extension Host；社群要求自動化嘅 feature request **2023 開到今日仍然 open**（作者試過 chokidar，結論＝reload 只能人手觸發）。 | github.com/microsoft/vscode#190917（open） |
| **Electron（一般 app）** | 內建**冇** hot reload；dev-only 用 `electron-reload`／`electron-reloader`（**586★、MIT、未封存、2026-10-07 仍有 push**；renderer 改＝reload 頁、main 改＝重啟 app）；現代做法＝`electron-vite`（Vite HMR）。 | geeksforgeeks「Hot Reload in ElectronJS」；github.com/sindresorhus/electron-reloader |
| **Chrome extension** | `chrome.runtime.reload()`（等同人手撳「重新載入」）。 | Chrome extension docs |

**三個共識（借得嘅）**：
1. **gate 落 dev**：Obsidian 要 `.hotreload`／`.git`；Electron reloader 要 `NODE_ENV=development` ⇒ 生產版唔會偷偷熱重載。
2. **重載 ≠ 只重新執行**：要 `onunload()` 清乾淨，否則疊 listener（同 `Jarvis.register({mount, unmount, tick})` 吻合）。
3. **debounce 寫檔**：0.7–1 秒，避免寫到一半就掛。

→ **建議**：v1 手動 reload（＋一粒掣）＋ dev-only watcher（`JARVIS_APPS_WATCH=1`）；**唔做**生產版自動熱重載（成本高、風險＝疊 listener，換來只係開發方便）。
