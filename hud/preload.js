// Preload: expose safe IPC bridge to renderer
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvisHud', {
  // 智慧穿透：註冊卡片位置
  setRects: (rects) => { ipcRenderer.send('hud:set-rects', rects); },
  setDragging: (d) => { ipcRenderer.send('hud:dragging', d); },
  setClickable: (clickable) => {
    ipcRenderer.send('hud:set-ignore-mouse', !clickable);
  },
  // 硬體監控數據（每 2 秒）
  onHardware: (cb) => {
    ipcRenderer.on('hud:hw', (_e, data) => cb(data));
  },
  // Jarvis 回覆推送 → 顯示回覆面板
  onReply: (cb) => {
    ipcRenderer.on('hud:reply', (_e, data) => cb(data));
  },
  // 真實統計（wake 次數）
  onStats: (cb) => {
    ipcRenderer.on('hud:stats', (_e, data) => cb(data));
  },
  // 天氣推送
  onWeather: (cb) => {
    ipcRenderer.on('hud:weather', (_e, data) => cb(data));
  },
  // 重置佈局
  onResetLayout: (cb) => {
    ipcRenderer.on('hud:reset-layout', () => cb());
  },
  // 麥克風高頻數據（光環波形）
  onMic: (cb) => {
    ipcRenderer.on('hud:mic', (_e, v) => cb(v));
  },
  // 註冊卡片位置（智慧穿透）
  setRects: (rects) => {
    ipcRenderer.send('hud:set-rects', rects);
  },
  // 拖曳鎖定（拖曳中保持可點）
  setDragging: (d) => {
    ipcRenderer.send('hud:dragging', d);
  },
  // 音樂播放狀態（▶/⏸ 切換）
  onMediaState: (cb) => {
    ipcRenderer.on('hud:media-state', (_e, s) => cb(s));
  },
  // 麥克風輸入（VOICE 卡）
  onMicIn: (cb) => {
    ipcRenderer.on('hud:mic-in', (_e, v) => cb(v));
  },
  // 熱鍵切換互動模式
  onInteractiveChange: (cb) => {
    ipcRenderer.on('hud:interactive', (_e, interactive) => cb(interactive));
  },
});

// ---- HoloMat H1: Jarvis app API (D4 whitelist) ----
const _appRegistry = new Map();
let _layouts = {};
let _tickTimer = null;

function _ensureTickLoop() {
  if (_tickTimer) return;
  _tickTimer = setInterval(() => {
    _appRegistry.forEach((spec) => {
      if (typeof spec.tick !== 'function') return;
      try {
        const r = spec.tick();
        if (r && typeof r.catch === 'function') r.catch(() => {});
      } catch (_) { /* mount isolation */ }
    });
  }, 2000);
}

function _deny(appId, name) {
  const msg = 'api denied: ' + name + ' (not in app.json api)';
  console.warn('[Jarvis]', appId, msg);
  ipcRenderer.send('jarvis:app-error', { id: appId, error: msg });
  return Promise.reject(new Error(msg));
}

function _gate(appId, declared, name) {
  if (name === 'register') return true;
  const list = Array.isArray(declared) ? declared : [];
  return list.indexOf(name) !== -1;
}

function _mountCard(spec, layout) {
  const id = spec && spec.id;
  if (!id) return;
  const root = document.getElementById('jarvis-apps-root');
  if (!root) return;
  let el = document.getElementById('jarvis-app-' + id);
  if (!el) {
    el = document.createElement('div');
    el.id = 'jarvis-app-' + id;
    el.className = 'jarvis-app-card';
    el.setAttribute('data-app-id', id);
    root.appendChild(el);
  }
  if (layout) {
    el.style.left = (layout.x || 0) + 'px';
    el.style.top = (layout.y || 0) + 'px';
    el.style.width = (layout.w || 220) + 'px';
    el.style.height = (layout.h || 160) + 'px';
  }
  const prev = _appRegistry.get(id);
  if (prev && typeof prev.unmount === 'function') {
    try { prev.unmount(); } catch (e) {
      ipcRenderer.send('jarvis:app-error', { id: id, error: 'unmount: ' + (e && e.message ? e.message : e) });
    }
  }
  try {
    if (typeof spec.mount === 'function') spec.mount(el);
  } catch (e) {
    ipcRenderer.send('jarvis:app-error', { id: id, error: 'mount: ' + (e && e.message ? e.message : e) });
    return;
  }
  _appRegistry.set(id, spec);
  _ensureTickLoop();
}

function makeJarvisApi(appId, declared) {
  const id = appId || '?';
  const api = declared || [];
  return {
    register: (spec) => {
      const s = Object.assign({}, spec || {}, { id: (spec && spec.id) || id });
      const layout = _layouts[s.id];
      _mountCard(s, layout);
    },
    sensors: () => {
      if (!_gate(id, api, 'sensors')) return _deny(id, 'sensors');
      return ipcRenderer.invoke('jarvis:sensors');
    },
    speak: (text) => {
      if (!_gate(id, api, 'speak')) return _deny(id, 'speak');
      return ipcRenderer.invoke('jarvis:speak', String(text || ''));
    },
    alerts: () => {
      if (!_gate(id, api, 'alerts')) return _deny(id, 'alerts');
      return ipcRenderer.invoke('jarvis:alerts');
    },
    media: () => {
      if (!_gate(id, api, 'media')) return _deny(id, 'media');
      return ipcRenderer.invoke('jarvis:media');
    },
    settings: (name) => {
      if (!_gate(id, api, 'settings')) return _deny(id, 'settings');
      return ipcRenderer.invoke('jarvis:settings', String(name || ''));
    },
    log: (msg) => {
      if (!_gate(id, api, 'log')) return _deny(id, 'log');
      return ipcRenderer.invoke('jarvis:log', { id: id, msg: String(msg || '') });
    },
  };
}

contextBridge.exposeInMainWorld('Jarvis', makeJarvisApi('_host', [
  'sensors', 'speak', 'alerts', 'media', 'settings', 'log',
]));
contextBridge.exposeInMainWorld('jarvisBind', (appId, declared) => makeJarvisApi(appId, declared));

ipcRenderer.on('jarvis:apps-layout', (_e, layouts) => {
  _layouts = layouts || {};
  Object.keys(_layouts).forEach((id) => {
    const el = document.getElementById('jarvis-app-' + id);
    const L = _layouts[id];
    if (el && L) {
      el.style.left = (L.x || 0) + 'px';
      el.style.top = (L.y || 0) + 'px';
      el.style.width = (L.w || 220) + 'px';
      el.style.height = (L.h || 160) + 'px';
    }
  });
});

ipcRenderer.on('jarvis:apps-clear', () => {
  _appRegistry.forEach((spec, id) => {
    if (spec && typeof spec.unmount === 'function') {
      try { spec.unmount(); } catch (_) {}
    }
    const el = document.getElementById('jarvis-app-' + id);
    if (el && el.parentNode) el.parentNode.removeChild(el);
  });
  _appRegistry.clear();
});
