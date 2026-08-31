// Home / Main GUI preload — control center bridge
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('homeApi', {
  openCompanion: () => ipcRenderer.send('home:open-companion'),
  openSettings: () => ipcRenderer.send('home:open-settings'),
  toggleHud: () => ipcRenderer.send('home:toggle-hud'),
  close: () => ipcRenderer.send('home:close'),
  quit: () => ipcRenderer.send('home:quit'),
  relaunch: () => ipcRenderer.send('home:relaunch'),
  onWeather: (cb) => ipcRenderer.on('hud:weather', (_e, d) => cb(d)),
  onHw: (cb) => ipcRenderer.on('hud:hw', (_e, d) => cb(d)),
  onStats: (cb) => ipcRenderer.on('hud:stats', (_e, d) => cb(d)),
  onStatus: (cb) => ipcRenderer.on('home:status', (_e, st) => cb(st)),
  onAppend: (cb) => ipcRenderer.on('home:append', (_e, t) => cb(t)),
  sendText: (t) => ipcRenderer.invoke('home:send-text', t),
  onHudVisible: (cb) => ipcRenderer.on('home:hud-visible', (_e, d) => cb(d)),
});
