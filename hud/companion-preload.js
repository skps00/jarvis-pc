// Companion window preload — reply transcript bridge
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('companion', {
  append: (cb) => ipcRenderer.on('companion:append', (_e, t) => cb(t)),
  onStatus: (cb) => ipcRenderer.on('companion:status', (_e, st) => cb(st)),
  close: () => ipcRenderer.send('companion:close'),
});
