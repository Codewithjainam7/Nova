const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  setIslandVisible: (visible) => ipcRenderer.send('island-set-visible', visible),
  setIslandExpanded: (expanded) => ipcRenderer.send('island-expand', expanded),
  showMainWindow: () => ipcRenderer.send('main-show'),
  hideMainWindow: () => ipcRenderer.send('main-hide'),
  toggleIsland: () => ipcRenderer.send('island-toggle'),
  onShortcutTriggered: (callback) => ipcRenderer.on('shortcut-triggered', (_event, value) => callback(value))
});
