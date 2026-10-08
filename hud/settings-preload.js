// Settings window preload — load/save Jarvis settings.json
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('settingsApi', {
  load: () => ipcRenderer.invoke('settings:load'),
  save: (obj) => ipcRenderer.invoke('settings:save', obj),
  scanInputs: () => ipcRenderer.invoke('settings:scan-inputs'),
  scanOutputs: () => ipcRenderer.invoke('settings:scan-outputs'),
  openHermes: () => ipcRenderer.invoke('settings:open-hermes'),
  probeHermes: () => ipcRenderer.invoke('settings:probe-hermes'),
  testAlert: () => ipcRenderer.invoke('settings:test-alert'),
  getAppsLayout: () => ipcRenderer.invoke('apps:get-layout'),
  setAppsLayout: (mode) => ipcRenderer.invoke('apps:set-layout', mode),
  reloadApps: () => ipcRenderer.invoke('apps:reload'),
  close: () => ipcRenderer.send('settings:close'),
});
