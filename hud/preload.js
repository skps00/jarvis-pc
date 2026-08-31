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
