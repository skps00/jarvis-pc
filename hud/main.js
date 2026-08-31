// J.A.R.V.I.S. HUD — Electron main process
// Transparent, frameless, always-on-top, click-through overlay.
const { app, BrowserWindow, ipcMain, globalShortcut, screen, shell, Tray, Menu, nativeImage } = require('electron');

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (homeWin && !homeWin.isDestroyed()) { homeWin.show(); homeWin.focus(); }
    else if (win && !win.isDestroyed()) { win.show(); win.focus(); }
  });
}

// 防止 stdout/stderr 管道断开（EPIPE）导致主进程崩溃（背景启动时 gateway 中断会断管）
for (const s of [process.stdout, process.stderr]) {
  if (s && typeof s.on === 'function') s.on('error', e => { if (e && e.code === 'EPIPE') return; });
}
process.on('uncaughtException', e => {
  if (e && (e.code === 'EPIPE' || e.message === 'write EPIPE')) return;
  try {
    require('fs').appendFileSync(process.env.APPDATA + '\\Jarvis\\hud_error.log', new Date().toISOString() + ' ' + (e && e.stack ? e.stack : String(e)) + '\n');
  } catch (_) {}
});
const { execFile } = require('child_process');
const path = require('path');

let win = null;
let hwTimer = null;
let statsTimer = null;
// ---- 真實天氣（Node 抓取，無 CORS 限制）----
const https = require('https');
let weatherTimer = null;
function fetchJson(url, cb) {
  https.get(url, (res) => {
    let d = '';
    res.on('data', (c) => { d += c; });
    res.on('end', () => {
      try { cb(JSON.parse(d)); } catch (e) { cb(null); }
    });
  }).on('error', () => cb(null));
}
function pollWeather() {
  // IP 定位（ipinfo.io 無 Cloudflare 擋）
  fetchJson('https://ipinfo.io/json', (geo) => {
    if (!geo || !geo.loc) return;
    const [lat, lon] = geo.loc.split(',').map(Number);
    if (!lat || !lon) return;
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&timezone=auto`;
    fetchJson(url, (wx) => {
      if (!wx || !wx.current_weather) return;
      const cw = wx.current_weather;
      const codes = { 0: 'SUNNY', 1: 'MOSTLY CLEAR', 2: 'PARTLY CLOUDY', 3: 'OVERCAST', 45: 'FOG', 51: 'DRIZZLE', 61: 'RAIN', 63: 'RAIN', 71: 'SNOW', 80: 'SHOWERS', 95: 'STORM' };
      const data = {
        temp: Math.round(cw.temperature),
        desc: codes[cw.weathercode] || 'CLOUDY',
        city: geo.city || geo.region || geo.country || 'LOCAL',
      };
      if (win && !win.isDestroyed()) win.webContents.send('hud:weather', data);
      sendHome('hud:weather', data);
    });
  });
}

// ---- 常駐麥克風監聽（驅動光環波形）----
// ⚠️ H1 (2026-08-29): 機路徑抽出——優先 %APPDATA%\Jarvis\host.json（{python, jarvis_pc_dir}），
//   再 env（JARVIS_PYTHON / JARVIS_PC_DIR），最後 fallback 預設值。搬機/升 Python 只改 host.json。
const HOST_JSON = path.join(process.env.APPDATA || '', 'Jarvis', 'host.json');
let hostCfg = {};
try { hostCfg = JSON.parse(require('fs').readFileSync(HOST_JSON, 'utf-8')); } catch (e) {}
const DEFAULT_PY = 'C:\\Users\\skps9\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe';
const DEFAULT_PC = 'C:\\Users\\skps9\\Documents\\Code_Project\\jarvis-pc';
const SIDECAR_PY = hostCfg.python || process.env.JARVIS_PYTHON || DEFAULT_PY;
const JARVIS_PC_DIR = hostCfg.jarvis_pc_dir || process.env.JARVIS_PC_DIR || DEFAULT_PC;
const { spawn } = require('child_process');
let sidecarProc = null;
let sidecarRestartTimes = [];   // recent spawn timestamps → crash-loop rate limit (60s window)
let sidecarHealthFails = 0;
let sidecarHealthTimer = null;
let sidecarStopping = false;    // set by stopSidecar() → suppress exit-handler respawn
let sidecarRespawnTimer = null; // pending 5s exit respawn timer (cleared on stop)
let crashLoopNotified = false;  // notify once per crash-loop episode

function sidecarRunning() {
  // H3 (2026-08-29): HTTP /health (sidecar MCP has a real health endpoint) instead of bare TCP —
  // anything listening on 8765 (stale MCP, wrong process) no longer counts as healthy.
  return new Promise((resolve) => {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 1500);
    fetch('http://127.0.0.1:8765/health', { signal: ctrl.signal })
      .then((r) => { clearTimeout(timer); resolve(r.ok); })
      .catch(() => { clearTimeout(timer); resolve(false); });
  });
}

function spawnSidecar() {
  if (sidecarStopping) return;
  if (sidecarProc && !sidecarProc.killed) return;
  // Crash-loop rate limit: ≥3 spawns in 60s → back off 60s, notify once.
  const now = Date.now();
  sidecarRestartTimes = sidecarRestartTimes.filter((t) => now - t < 60000);
  if (sidecarRestartTimes.length >= 3) {
    // Backoff: rate-limited for 60s. Next health tick (30s) or exit handler retries
    // once timestamps age out — no explicit timer needed.
    if (!crashLoopNotified && typeof tray !== 'undefined' && tray) {
      crashLoopNotified = true;
      tray.displayBalloon({ title: 'JARVIS ONE', content: 'Sidecar crash loop — backing off 60s before retry.' });
    }
    return;
  }
  crashLoopNotified = false;
  const fs = require('fs');
  const logPath = process.env.APPDATA + '\\Jarvis\\serve.log';
  const out = fs.openSync(logPath, 'a');
  const child = spawn(SIDECAR_PY, ['-m', 'jarvis', 'serve'], {
    cwd: JARVIS_PC_DIR,
    windowsHide: true,
    env: { ...process.env, PYTHONPATH: JARVIS_PC_DIR + '\\src', JARVIS_ELECTRON_HOST: '1' },
    stdio: ['ignore', out, out],
  });
  try { fs.closeSync(out); } catch (e) {}  // child dup'd the handle; parent must not leak FDs
  sidecarProc = child;
  sidecarRestartTimes.push(now);
  child.on('exit', (code, signal) => {
    // Identity-check: only clear our own ref (health-kill of a prior child must not wipe the new one).
    if (sidecarProc === child) sidecarProc = null;
    if (sidecarStopping) return;
    if (sidecarRespawnTimer) clearTimeout(sidecarRespawnTimer);
    sidecarRespawnTimer = setTimeout(() => {
      sidecarRespawnTimer = null;
      sidecarRunning().then((up) => { if (!up) spawnSidecar(); });
    }, 5000);
  });
}

function startSidecarHealthCheck() {
  if (sidecarHealthTimer) return;
  // Every 30s: 3 consecutive misses (90s down) → force respawn.
  sidecarHealthTimer = setInterval(() => {
    sidecarRunning().then((up) => {
      if (up) { sidecarHealthFails = 0; return; }
      sidecarHealthFails += 1;
      if (sidecarHealthFails >= 3) {
        sidecarHealthFails = 0;
        if (sidecarProc && !sidecarProc.killed) {
          // Let the exit handler own respawn (5s delay → port released, no bind race).
          try { sidecarProc.kill(); } catch (e) {}
        } else {
          spawnSidecar();
        }
      }
    });
  }, 30000);
}

async function ensureSidecar() {
  startSidecarHealthCheck();
  if (sidecarProc && !sidecarProc.killed) return;
  const up = await sidecarRunning();
  if (up) return; // already running (watchdog/autostart)
  spawnSidecar();
}

function stopSidecar() {
  sidecarStopping = true;
  if (sidecarHealthTimer) { clearInterval(sidecarHealthTimer); sidecarHealthTimer = null; }
  if (sidecarRespawnTimer) { clearTimeout(sidecarRespawnTimer); sidecarRespawnTimer = null; }
  if (sidecarProc && !sidecarProc.killed) {
    try { sidecarProc.kill(); } catch (e) {}
    sidecarProc = null;
  }
}

let micProc = null;
function startMicLoop() {
  // 輸出音訊 loopback（耳機正在播的聲音 → 波形）
  const OUT_LOOP = path.join(process.env.LOCALAPPDATA || '', 'hermes', 'scripts', 'output_loop.py');
  const IN_LOOP = path.join(process.env.LOCALAPPDATA || '', 'hermes', 'scripts', 'mic_loop.py');
  function attachLoop(proc, channel) {
    let buf = '';
    proc.stdout.on('data', (chunk) => {
      buf += chunk.toString('utf8');
      let nl;
      while ((nl = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        const v = parseFloat(line);
        if (!isNaN(v) && win && !win.isDestroyed()) win.webContents.send(channel, v);
      }
    });
  }
  // 輸出（耳機播放中聲音 → 波形）
  const outProc = spawn(PYTHON, [OUT_LOOP], { windowsHide: true, env: { ...process.env, PYTHONPATH: '' }, stdio: ['ignore', 'pipe', 'ignore'] });
  attachLoop(outProc, 'hud:mic');
  outProc.on('exit', () => setTimeout(startMicLoop, 2000));
  // 輸入（麥克風 → VOICE 卡）
  const inProc = spawn(PYTHON, [IN_LOOP], { windowsHide: true, env: { ...process.env, PYTHONPATH: '' }, stdio: ['ignore', 'pipe', 'ignore'] });
  attachLoop(inProc, 'hud:mic-in');
  inProc.on('exit', () => setTimeout(startMicLoop, 2000));
}

// ---- 真實統計：wake 次數（讀 Jarvis log）----
const fs = require('fs');
function pushStats() {
  try {
    const logPath = path.join(process.env.APPDATA || '', 'Jarvis', 'wake_debug.log');
    if (!fs.existsSync(logPath)) return;
    const content = fs.readFileSync(logPath, 'utf8');
    const lines = content.split('\n');
    const wakes = lines.filter(l => l.includes('wake_loop_start')).length;
    const payload = { wakes };
    if (win && !win.isDestroyed()) win.webContents.send('hud:stats', payload);
    sendHome('hud:stats', payload);
  } catch (e) { /* ignore */ }
}

// ---- Jarvis 回覆推送接收器（127.0.0.1:8770/reply）----
const http = require('http');
const replyServer = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/reply') {
    const chunks = [];
    req.on('data', (c) => { chunks.push(c); });
    req.on('end', () => {
      try {
        const body = Buffer.concat(chunks).toString('utf8');
        const data = JSON.parse(body);
        if (win && !win.isDestroyed()) win.webContents.send('hud:reply', data);
        companionAppend(data.caption || data.speak || data.text || data.spoken || JSON.stringify(data));
        homeAppend(data.caption || data.speak || data.text || data.spoken || JSON.stringify(data));
      } catch (e) { /* ignore */ }
      res.writeHead(200); res.end('ok');
    });
  } else {
    res.writeHead(404); res.end();
  }
});

// ---- JARVIS Media Bridge（8771）：HUD 音樂按鈕 → Chrome 擴充指令隊列 ----
const mediaQueue = [];
const mediaBridge = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
  let body = '';
  req.on('data', (c) => { body += c; });
  req.on('end', () => {
    try {
      const pathName = new URL(req.url, 'http://x').pathname;
      if (pathName === '/cmd' && req.method === 'POST') {
        const { cmd } = JSON.parse(body || '{}');
        if (cmd) mediaQueue.push(cmd);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end('{"ok":true}');
      } else if (pathName === '/next-cmd' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ cmd: mediaQueue.shift() || null }));
      } else if (pathName === '/state' && req.method === 'POST') {
        const st = JSON.parse(body || '{}');
        if (st.caption || st.speak) companionAppend(st.caption || st.speak);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end('{"ok":true}');
      } else { res.writeHead(404); res.end('{}'); }
    } catch (e) { res.writeHead(400); res.end('{}'); }
  });
});
if (gotLock) {
  mediaBridge.listen(8771, '127.0.0.1', () => console.log('[HUD] media bridge on 8771'));
  replyServer.listen(8770, '127.0.0.1');
}

// 遊戲中自動隱藏（HUD 只桌面顯示）：每 5 秒查活動狀態
const ACTIVITY_SCRIPT = path.join(process.env.LOCALAPPDATA || '', 'hermes', 'scripts', 'activity_monitor.py');
let actTimer = null;
function checkActivity() {
  execFile(PYTHON, [ACTIVITY_SCRIPT], { windowsHide: true, timeout: 6000, env: { ...process.env, PYTHONPATH: '' } }, (err, stdout) => {
    const alog = path.join(require('os').tmpdir(), 'jarvis_hud_activity.log');
    try {
      // activity 檢查失敗 → 保守：唔郁 HUD 可見性（遊戲中唔會因為 check 失敗而彈 HUD）
      if (err) { require('fs').appendFileSync(alog, new Date().toISOString() + ' ERR:' + err.message + '\n'); return; }
      if (!stdout) { require('fs').appendFileSync(alog, new Date().toISOString() + ' NOOUT\n'); return; }
      const line = stdout.trim().split('\n').pop();
      const data = JSON.parse(line);
      require('fs').appendFileSync(alog, new Date().toISOString() + ' state=' + data.state + ' game=' + data.game + '\n');
      const hidden = data.state === 'playing' || data.fullscreen === true;
      if (win && !win.isDestroyed() && win.isVisible() === hidden) {
        if (hidden) win.hide(); else win.show();
        sendHome('home:hud-visible', { visible: !hidden });
      }
    } catch (e) { /* ignore */ }
  });
}


const HW_MONITOR = path.join(process.env.LOCALAPPDATA || '', 'hermes', 'scripts', 'hw_monitor.py');
const PYTHON = SIDECAR_PY;   // H1: 同 sidecar 用同一 host.json python
const JARVIS_PY = SIDECAR_PY;

const VOICE_STATUS_JSON = process.env.APPDATA + '\\Jarvis\\voice_status.json';
let lastVoiceStatus = '';
function pollVoiceStatus() {
  try {
    const fs = require('fs');
    if (!fs.existsSync(VOICE_STATUS_JSON)) return;
    const raw = fs.readFileSync(VOICE_STATUS_JSON, 'utf-8');
    if (raw === lastVoiceStatus) return;
    lastVoiceStatus = raw;
    const st = JSON.parse(raw);
    // Stale detect (2026-08-29): sidecar writes ISO updated_at; >30s → HUD greys status.
    if (st.updated_at) {
      const t = new Date(st.updated_at).getTime();
      st.stale = !isNaN(t) && (Date.now() - t) > 30000;
    }
    if (companionWin && !companionWin.isDestroyed()) {
      companionWin.webContents.send('companion:status', st);
    }
    sendHome('home:status', st);
  } catch (e) {}
}

let homeWin = null;
let companionWin = null;
let settingsWin = null;
let appQuitting = false;
let lastHomeWeather = null;
let lastHomeHw = null;
let lastHomeStats = null;
let lastHomeStatus = null;

function sendHome(ch, data) {
  if (ch === 'hud:weather') lastHomeWeather = data;
  else if (ch === 'hud:hw') lastHomeHw = data;
  else if (ch === 'hud:stats') lastHomeStats = data;
  else if (ch === 'home:status') lastHomeStatus = data;
  if (homeWin && !homeWin.isDestroyed()) homeWin.webContents.send(ch, data);
}

/** Push cached live payloads after home renderer is ready (first paint / reopen). */
function seedHome() {
  if (!homeWin || homeWin.isDestroyed()) return;
  if (lastHomeWeather) homeWin.webContents.send('hud:weather', lastHomeWeather);
  if (lastHomeHw) homeWin.webContents.send('hud:hw', lastHomeHw);
  if (lastHomeStats) homeWin.webContents.send('hud:stats', lastHomeStats);
  if (lastHomeStatus) homeWin.webContents.send('home:status', lastHomeStatus);
  else {
    try {
      if (fs.existsSync(VOICE_STATUS_JSON)) {
        const raw = fs.readFileSync(VOICE_STATUS_JSON, 'utf-8');
        lastVoiceStatus = raw;
        lastHomeStatus = JSON.parse(raw);
        homeWin.webContents.send('home:status', lastHomeStatus);
      }
    } catch (e) { /* ignore */ }
  }
  if (win && !win.isDestroyed()) {
    homeWin.webContents.send('home:hud-visible', { visible: win.isVisible() });
  }
}

// frameless transparent panel pattern：Companion/Home/Settings 共用（寬高/行為微差，刻意唔抽 helper 保持獨立）
function createHomeWindow() {
  if (homeWin && !homeWin.isDestroyed()) {
    homeWin.show();
    homeWin.focus();
    seedHome();
    return;
  }
  homeWin = new BrowserWindow({
    width: 720, height: 480,
    transparent: true, frame: false, resizable: true,
    alwaysOnTop: false, skipTaskbar: false, show: true,
    backgroundColor: '#00000000',
    webPreferences: { preload: path.join(__dirname, 'home-preload.js'), contextIsolation: true },
  });
  homeWin.loadFile(path.join(__dirname, 'home.html'));
  homeWin.webContents.on('did-finish-load', () => {
    console.log('[home] did-finish-load OK');
    seedHome();
  });
  // Behaviour: X / close hides to tray — app stays resident (will-quit destroys).
  homeWin.on('close', (e) => {
    if (!appQuitting) {
      e.preventDefault();
      homeWin.hide();
    }
  });
  homeWin.on('closed', () => { homeWin = null; });
}

// frameless transparent panel pattern：Companion/Home/Settings 共用（寬高/行為微差，刻意唔抽 helper 保持獨立）
function createCompanionWindow() {
  if (companionWin && !companionWin.isDestroyed()) { companionWin.show(); companionWin.focus(); return; }
  companionWin = new BrowserWindow({
    width: 420, height: 560,
    transparent: true, frame: false, resizable: true,
    alwaysOnTop: false, skipTaskbar: false, show: true,
    webPreferences: { preload: path.join(__dirname, 'companion-preload.js'), contextIsolation: true },
  });
  companionWin.loadFile(path.join(__dirname, 'companion.html'));
  companionWin.webContents.on('did-finish-load', () => console.log('[companion] did-finish-load OK'));
  companionWin.webContents.on('did-fail-load', (_e, code, desc, url) => console.log('[companion] did-fail-load', code, desc, url));
  companionWin.on('closed', () => { companionWin = null; });
}

function createSettingsWindow() {
  if (settingsWin && !settingsWin.isDestroyed()) { settingsWin.show(); settingsWin.focus(); return; }
  settingsWin = new BrowserWindow({
    width: 460, height: 640,
    transparent: true, frame: false, resizable: true,
    alwaysOnTop: false, skipTaskbar: false, show: true,
    webPreferences: { preload: path.join(__dirname, 'settings-preload.js'), contextIsolation: true },
  });
  settingsWin.loadFile(path.join(__dirname, 'settings.html'));
  settingsWin.on('closed', () => { settingsWin = null; });
}

function companionAppend(text) {
  if (companionWin && !companionWin.isDestroyed()) {
    companionWin.webContents.send('companion:append', String(text));
  }
}

function homeAppend(text) {
  if (homeWin && !homeWin.isDestroyed()) homeWin.webContents.send('home:append', String(text));
}

function createWindow() {
  const { workArea } = screen.getPrimaryDisplay();

  win = new BrowserWindow({
    width: workArea.width,
    height: workArea.height,
    x: workArea.x,
    y: workArea.y,
    transparent: true,
    backgroundColor: '#00000000',  // 載入前不閃黑
    frame: false,
    resizable: false,
    movable: false,
    alwaysOnTop: false,      // 不置頂：開其他視窗時被蓋住（不擋），桌面空時可見
    skipTaskbar: true,
    hasShadow: false,
    focusable: false,
    fullscreenable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.setIgnoreMouseEvents(true, { forward: true });
  win.webContents.setZoomFactor(1.0);  // 響應式 vw 設計，不需 zoom
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

// ---- 硬體監控：每 2 秒跑 hw_monitor.py 推給 renderer ----
function pollHardware() {
  execFile(PYTHON, [HW_MONITOR], { windowsHide: true, timeout: 8000, env: { ...process.env, PYTHONPATH: '' } }, (err, stdout) => {
    if (err || !stdout) return;
    try {
      const data = JSON.parse(stdout.trim().split('\n').pop());
      if (win && !win.isDestroyed()) win.webContents.send('hud:hw', data);
      sendHome('hud:hw', data);
    } catch (e) { /* ignore parse noise */ }
  });
}

// ---- IPC ----
ipcMain.on('hud:set-rects', (_e, rects) => { hudRects = rects || []; });
ipcMain.on('hud:dragging', (_e, d) => { hudDragging = !!d; if (hudDragging && win) win.setIgnoreMouseEvents(false); });
ipcMain.on('hud:set-ignore-mouse', (_e, on) => { if (win) win.setIgnoreMouseEvents(on, { forward: true }); });
ipcMain.on('companion:close', () => {
  if (companionWin && !companionWin.isDestroyed()) companionWin.close();
});

ipcMain.on('home:open-companion', () => createCompanionWindow());
ipcMain.on('home:open-settings', () => createSettingsWindow());
ipcMain.on('home:toggle-hud', () => {
  if (!win || win.isDestroyed()) return;
  if (win.isVisible()) win.hide();
  else win.show();
  sendHome('home:hud-visible', { visible: win.isVisible() });
});
// Home 係常駐 app 嘅主畫面：✕ = hide 去 tray（唔 destroy）；真正退出用 tray「退出」
ipcMain.on('home:close', () => {
  if (homeWin && !homeWin.isDestroyed()) homeWin.hide();
});
ipcMain.handle('home:send-text', (_e, text) => new Promise((resolve) => {
  const safe = JSON.stringify(String(text || ''));
  const code = "from jarvis.engine import execute_utterance; r=execute_utterance(" + safe + ", ask_confirm=lambda p: True, repair_asr=False); print('\\n'.join(r.lines))";
  execFile(JARVIS_PY, ['-c', code], {
    windowsHide: true,
    timeout: 120000,
    env: { ...process.env, PYTHONPATH: JARVIS_PC_DIR + '\\src' },
  }, (err, stdout) => {
    if (err) { resolve({ ok: false, error: String(err.message || err) }); return; }
    const lines = (stdout || '').split('\n').map(s => s.trim()).filter(Boolean);
    resolve({ ok: true, lines });
  });
}));
ipcMain.on('home:quit', () => { stopSidecar(); app.quit(); });
ipcMain.on('home:relaunch', () => { stopSidecar(); app.relaunch(); app.quit(); });

// ---- Settings window (Phase 8.2) ----
const SETTINGS_JSON = path.join(process.env.APPDATA || '', 'Jarvis', 'settings.json');

function scanAudioDevices(kind) {
  const chanKey = kind === 'input' ? 'max_input_channels' : 'max_output_channels';
  const snippet = [
    'import sounddevice as sd, json',
    'by_name = {}',
    'for i, d in enumerate(sd.query_devices()):',
    `    if int(d.get("${chanKey}") or 0) <= 0: continue`,
    '    raw = str(d.get("name") or "device %d" % i).strip()',
    '    sr = float(d.get("default_samplerate") or 0)',
    '    by_name.setdefault(raw, []).append((i, sr))',
    'names = []',
    'for name, cands in by_name.items():',
    '    best = cands[0]',
    '    for j, sr in cands[1:]:',
    '        if abs(sr - 44100.0) < abs(best[1] - 44100.0):',
    '            best = (j, sr)',
    '    names.append(name)',
    'print(json.dumps(names, ensure_ascii=False))',
  ].join('\n');
  return new Promise((resolve) => {
    execFile(PYTHON, ['-c', snippet], { windowsHide: true, timeout: 15000, env: { ...process.env, PYTHONPATH: '' } }, (err, stdout) => {
      if (err || !stdout) { resolve([]); return; }
      try {
        const arr = JSON.parse(stdout.trim());
        resolve(Array.isArray(arr) ? arr : []);
      } catch (e) { resolve([]); }
    });
  });
}

ipcMain.handle('settings:load', async () => {
  // H4 (2026-08-29): secrets are DPAPI-encrypted in settings.json — read the decrypted
  // view from the sidecar so settings.html never renders dpapi: blobs. Fallback: direct
  // read (sidecar down) — encrypted fields show as-is, saving still routes via POST.
  try {
    const tokPath = path.join(process.env.APPDATA || '', 'Jarvis', 'alerts', 'mcp_token.txt');
    let tok = '';
    try { tok = fs.readFileSync(tokPath, 'utf-8').trim(); } catch (e) {}
    if (tok) {
      const resp = await fetch('http://127.0.0.1:8765/settings', {
        headers: { 'Authorization': 'Bearer ' + tok },
      });
      if (resp.ok) return await resp.json();
    }
  } catch (e) {}
  try { return JSON.parse(fs.readFileSync(SETTINGS_JSON, 'utf-8')); }
  catch (e) { return {}; }
});
/** Mirror jarvis settings.py _clamp() for fields settings.html edits. */
function clampSettingsPatch(obj) {
  const out = { ...obj };
  if ('wake_threshold' in out) {
    let v = parseFloat(out.wake_threshold);
    if (Number.isNaN(v)) v = 0.50;
    out.wake_threshold = Math.max(0.25, Math.min(0.99, v));
  }
  if ('speaker_threshold' in out) {
    let v = parseFloat(out.speaker_threshold);
    if (Number.isNaN(v)) v = 0.50;
    out.speaker_threshold = Math.max(0.10, Math.min(0.99, v));
  }
  if ('aec_enabled' in out) out.aec_enabled = !!out.aec_enabled;
  if ('speaker_gate' in out) out.speaker_gate = !!out.speaker_gate;
  if ('aec_reference_device' in out) {
    out.aec_reference_device = String(out.aec_reference_device || '').trim();
  }
  const LLM_PRESETS = new Set(['deepseek', 'mimo', 'ollama', 'custom']);
  if ('llm_preset' in out) {
    let p = String(out.llm_preset || 'custom').trim().toLowerCase();
    if (!LLM_PRESETS.has(p)) p = 'custom';
    out.llm_preset = p;
  }
  if ('llm_api_key' in out) out.llm_api_key = String(out.llm_api_key || '').trim();
  if ('llm_base_url' in out) out.llm_base_url = String(out.llm_base_url || '').trim().replace(/\/+$/, '');
  if ('llm_model' in out) out.llm_model = String(out.llm_model || '').trim();
  if ('hermes_enabled' in out) out.hermes_enabled = !!out.hermes_enabled;
  if ('hermes_trusted' in out) out.hermes_trusted = !!out.hermes_trusted;
  if ('hermes_base_url' in out) {
    let u = String(out.hermes_base_url || '').trim().replace(/\/+$/, '');
    if (!u) u = 'http://127.0.0.1:8688';
    out.hermes_base_url = u;
  }
  if ('alert_voice' in out) out.alert_voice = !!out.alert_voice;
  if ('alert_cd_seconds' in out) {
    let v = parseFloat(out.alert_cd_seconds);
    if (Number.isNaN(v)) v = 0;
    out.alert_cd_seconds = Math.max(0, Math.min(120, v));
  }
  if ('alert_tts' in out) {
    let m = String(out.alert_tts || 'hermes').trim().toLowerCase();
    if (!['hermes', 'piper', 'off'].includes(m)) m = 'hermes';
    out.alert_tts = m;
  }
  // Mirror jarvis settings.py _clamp() — keep in sync when adding numeric settings.
  if ('wake_cd_seconds' in out) {
    let v = parseFloat(out.wake_cd_seconds);
    if (Number.isNaN(v)) v = 3.0;
    out.wake_cd_seconds = Math.max(0.5, Math.min(30.0, v));
  }
  if ('record_seconds' in out) {
    let v = parseFloat(out.record_seconds);
    if (Number.isNaN(v)) v = 4.0;
    out.record_seconds = Math.max(1.0, Math.min(10.0, v));
  }
  if ('text_wake' in out) out.text_wake = !!out.text_wake;
  if ('tts_length_scale' in out) {
    let v = parseFloat(out.tts_length_scale);
    if (Number.isNaN(v)) v = 0.85;
    out.tts_length_scale = Math.max(0.3, Math.min(2.0, v));
  }
  if ('tts_volume' in out) {
    let v = parseFloat(out.tts_volume);
    if (Number.isNaN(v)) v = 1.6;
    out.tts_volume = Math.max(0.1, Math.min(3.0, v));
  }
  if ('alerts_mcp_port' in out) {
    let v = parseInt(out.alerts_mcp_port, 10);
    if (Number.isNaN(v)) v = 8765;
    out.alerts_mcp_port = Math.max(1024, Math.min(65535, v));
  }
  if ('alert_gpu_poll_s' in out) {
    let v = parseFloat(out.alert_gpu_poll_s);
    if (Number.isNaN(v)) v = 5.0;
    out.alert_gpu_poll_s = Math.max(1.0, Math.min(120.0, v));
  }
  if ('mage_enabled' in out) out.mage_enabled = !!out.mage_enabled;
  if ('vc_fail_closed' in out) out.vc_fail_closed = !!out.vc_fail_closed;
  return out;
}

ipcMain.handle('settings:save', async (_e, obj) => {
  try {
    const patch = clampSettingsPatch(obj);
    // H2: single-writer via sidecar POST /settings (Bearer token); fallback direct write.
    try {
      const tokPath = path.join(process.env.APPDATA || '', 'Jarvis', 'alerts', 'mcp_token.txt');
      let tok = '';
      try { tok = fs.readFileSync(tokPath, 'utf-8').trim(); } catch (e) {}
      if (!tok) throw new Error('no token');
      const resp = await fetch('http://127.0.0.1:8765/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok },
        body: JSON.stringify(patch),
      });
      if (!resp.ok) throw new Error('sidecar http ' + resp.status);
      return await resp.json();
    } catch (e) {
      // fallback: direct write (old behaviour — sidecar down shouldn't break settings UI)
      let cur = {};
      try { cur = JSON.parse(fs.readFileSync(SETTINGS_JSON, 'utf-8')); } catch (e2) {}
      const merged = { ...cur, ...patch };
      fs.mkdirSync(path.dirname(SETTINGS_JSON), { recursive: true });
      fs.writeFileSync(SETTINGS_JSON, JSON.stringify(merged, null, 2) + '\n', 'utf-8');
      return { ok: true, fallback: true };
    }
  } catch (e) { return { ok: false, error: String(e) }; }
});
ipcMain.handle('settings:scan-inputs', () => scanAudioDevices('input'));
ipcMain.handle('settings:scan-outputs', () => scanAudioDevices('output'));
ipcMain.on('settings:close', () => {
  if (settingsWin && !settingsWin.isDestroyed()) settingsWin.close();
});
function readHermesBaseUrl() {
  try {
    const s = JSON.parse(fs.readFileSync(SETTINGS_JSON, 'utf-8'));
    let u = String(s.hermes_base_url || '').trim().replace(/\/+$/, '');
    if (!u) u = 'http://127.0.0.1:8688';
    return u;
  } catch (e) {
    return 'http://127.0.0.1:8688';
  }
}
ipcMain.handle('settings:open-hermes', () => {
  shell.openExternal(readHermesBaseUrl());
  return { ok: true };
});
ipcMain.handle('settings:probe-hermes', () => new Promise((resolve) => {
  const url = readHermesBaseUrl() + '/api/health';
  const req = http.get(url, { timeout: 4000 }, (res) => {
    res.resume();
    resolve({ ok: res.statusCode >= 200 && res.statusCode < 300 });
  });
  req.on('error', () => resolve({ ok: false }));
  req.on('timeout', () => { req.destroy(); resolve({ ok: false }); });
}));
ipcMain.handle('settings:test-alert', () => new Promise((resolve) => {
  execFile(JARVIS_PY, ['-c', "from jarvis.mouth import speak; speak('Test alert, sir.', blocking=True)"], {
    windowsHide: true,
    timeout: 15000,
    env: { ...process.env, PYTHONPATH: JARVIS_PC_DIR + '\\src' },
  }, (err) => {
    resolve(err ? { ok: false, error: String(err.message || err) } : { ok: true });
  });
}));

// ---- 智慧穿透：main 輪詢滑鼠 vs 卡片位置 ----
let hudRects = [];
let hudDragging = false;
let cursorTimer = null;
function pointInRect(x, y, r) { return x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h; }
function checkCursor() {
  if (hudDragging) return;
  try {
    const p = screen.getCursorScreenPoint();
    const b = win.getBounds();
    const rx = p.x - b.x, ry = p.y - b.y;
    const inside = hudRects.some(r => pointInRect(rx, ry, r));
    const current = !win.getIgnoreMouseEvents();
    if (inside !== current) {
      win.setIgnoreMouseEvents(!inside, { forward: true });
      win.setAlwaysOnTop(inside, 'floating');
    }
  } catch (e) {}
}

// ---- Dock 已移除（2026-08-29）：音樂控制改放 tray menu，media bridge 8771 保留（Chrome 擴充）----
let tray = null;
function createTray() {
  const icon = nativeImage.createEmpty();
  // small blue circle via data URL
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><circle cx="8" cy="8" r="7" fill="#00aaf8"/></svg>';
  tray = new Tray(nativeImage.createFromDataURL('data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64')));
  tray.setToolTip('JARVIS ONE');
  const mediaMenu = Menu.buildFromTemplate([
    { label: '⏮ 上一首', click: () => mediaQueue.push('prev') },
    { label: '⏯ 播放/暫停', click: () => mediaQueue.push('playpause') },
    { label: '⏭ 下一首', click: () => mediaQueue.push('next') },
  ]);
  const menu = Menu.buildFromTemplate([
    { label: '主畫面 / Home', click: () => createHomeWindow() },
    { label: '顯示 HUD', click: () => { if (win && !win.isDestroyed()) { win.show(); sendHome('home:hud-visible', { visible: true }); } } },
    { label: '音樂控制', submenu: mediaMenu },
    { label: '設定', click: () => createSettingsWindow() },
    { label: '顯示 Companion', click: () => createCompanionWindow() },
    { type: 'separator' },
    { label: '重新啟動', click: () => { stopSidecar(); app.relaunch(); app.quit(); } },
    { label: '退出 JARVIS', click: () => { stopSidecar(); app.quit(); } },
  ]);
  tray.setContextMenu(menu);
  tray.on('double-click', () => createHomeWindow());
}

// ---- whenReady ----
if (gotLock) app.whenReady().then(() => {
  globalShortcut.register('CommandOrControl+Alt+H', () => {
    if (!win) return;
    if (win.isVisible()) win.hide(); else win.show();
    sendHome('home:hud-visible', { visible: win.isVisible() });
  });
  globalShortcut.register('CommandOrControl+Alt+U', () => { if (win) win.setIgnoreMouseEvents(!win.getIgnoreMouseEvents(), { forward: true }); });
  globalShortcut.register('CommandOrControl+Alt+R', () => { if (win) win.webContents.send('hud:reset-layout'); });
  createWindow();
  if (process.env.JARVIS_OPEN_HOME === '1') createHomeWindow();
  ensureSidecar();
  createTray();
  // debug entry points: JARVIS_OPEN_COMPANION=1 / JARVIS_OPEN_SETTINGS=1 / JARVIS_OPEN_HOME=1
  if (process.env.JARVIS_OPEN_COMPANION === '1') createCompanionWindow();
  if (process.env.JARVIS_OPEN_SETTINGS === '1') createSettingsWindow();
  if (process.env.JARVIS_OPEN_HOME === '1') createHomeWindow();
  pollHardware();
  hwTimer = setInterval(pollHardware, 3000);
  checkActivity();
  actTimer = setInterval(checkActivity, 5000);
  pushStats();
  statsTimer = setInterval(pushStats, 15000);
  pollWeather();
  weatherTimer = setInterval(pollWeather, 600000);
  cursorTimer = setInterval(checkCursor, 150);
  setInterval(pollVoiceStatus, 2000);
});

app.on('window-all-closed', () => { /* 常駐，不退出 */ });
app.on('will-quit', () => {
  appQuitting = true;
  stopSidecar();
  if (win && !win.isDestroyed()) win.destroy();
  if (homeWin && !homeWin.isDestroyed()) homeWin.destroy();
  if (companionWin && !companionWin.isDestroyed()) companionWin.destroy();
  if (settingsWin && !settingsWin.isDestroyed()) settingsWin.destroy();
});
