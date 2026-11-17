const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  setIslandVisible: (visible) => ipcRenderer.send('island-set-visible', visible),
  setIslandExpanded: (expanded, height) => ipcRenderer.send('island-expand', expanded, height),
  setIslandPinned: (pinned) => ipcRenderer.send('island-pin', pinned),
  resetIslandPosition: () => ipcRenderer.send('island-reset-position'),
  moveIsland: (dx, dy) => ipcRenderer.send('island-move', dx, dy),
  showMainWindow: () => ipcRenderer.send('main-show'),
  hideMainWindow: () => ipcRenderer.send('main-hide'),
  toggleIsland: () => ipcRenderer.send('island-toggle'),
  onShortcutTriggered: (callback) => {
    const handler = (_event, value) => {
      try {
        callback(value);
      } catch (e) {}
    };
    ipcRenderer.on('shortcut-triggered', handler);
    return () => {
      try {
        ipcRenderer.removeListener('shortcut-triggered', handler);
      } catch (e) {}
    };
  }
});
