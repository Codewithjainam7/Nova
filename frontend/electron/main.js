const { app, BrowserWindow, globalShortcut, Tray, Menu, screen, ipcMain } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow = null;
let islandWindow = null;
let tray = null;
let isQuitting = false;
let backendProcess = null;

const FRONTEND_URL = process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173';
const BACKEND_URL = 'http://localhost:8000';

function checkBackendHealth(callback) {
  const req = http.get(`${BACKEND_URL}/health`, (res) => {
    callback(res.statusCode === 200);
  });
  req.on('error', () => callback(false));
  req.setTimeout(1500, () => {
    req.destroy();
    callback(false);
  });
}

function ensureBackendRunning() {
  checkBackendHealth((running) => {
    if (!running) {
      console.log('[Electron] Backend not detected on :8000. Spawning Python backend daemon...');
      const projectRoot = path.resolve(__dirname, '../../');
      const pythonExe = path.join(projectRoot, 'backend', '.venv', 'Scripts', 'python.exe');
      
      try {
        backendProcess = spawn(pythonExe, ['-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8000'], {
          cwd: projectRoot,
          detached: true,
          stdio: 'ignore'
        });
        backendProcess.unref();
        console.log('[Electron] Backend daemon spawned with PID:', backendProcess.pid);
      } catch (err) {
        console.error('[Electron] Failed to auto-spawn backend:', err);
      }
    } else {
      console.log('[Electron] Backend engine is active on port 8000.');
    }
  });
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    title: 'NOVA AI - ADA',
    icon: path.join(__dirname, '../src-tauri/icons/icon.ico'),
    backgroundColor: '#030508',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadURL(FRONTEND_URL);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

function createIslandWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth } = primaryDisplay.workAreaSize;
  const islandWidth = 380;
  const islandHeight = 80;
  const islandX = Math.round((screenWidth - islandWidth) / 2);
  const islandY = 16;

  islandWindow = new BrowserWindow({
    width: islandWidth,
    height: islandHeight,
    x: islandX,
    y: islandY,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    focusable: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  islandWindow.loadURL(`${FRONTEND_URL}/?island=true`);

  // Keep always on top across all workspaces
  islandWindow.setAlwaysOnTop(true, 'screen-saver');
}

function createTray() {
  const iconPath = path.join(__dirname, '../src-tauri/icons/icon.ico');
  tray = new Tray(iconPath);
  tray.setToolTip('ADA - Autonomous Digital Assistant');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open NOVA AI',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: 'Toggle Dynamic Island (Alt+Space)',
      click: () => {
        toggleIsland();
      }
    },
    { type: 'separator' },
    {
      label: 'Organize Downloads Folder',
      click: () => {
        triggerOrganizeDownloads();
      }
    },
    { type: 'separator' },
    {
      label: 'Quit ADA',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    }
  });
}

function toggleIsland() {
  if (!islandWindow) return;
  if (islandWindow.isVisible()) {
    islandWindow.hide();
  } else {
    islandWindow.show();
    islandWindow.focus();
  }
}

function triggerOrganizeDownloads() {
  const postData = JSON.stringify({ content: 'organize my downloads folder' });
  const req = http.request(
    `${BACKEND_URL}/chat`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    },
    (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        console.log('[Tray] Organized Downloads response:', data);
      });
    }
  );
  req.on('error', (e) => console.error('[Tray] Failed to request organize downloads:', e));
  req.write(postData);
  req.end();
}

function registerShortcuts() {
  // Global hotkey: Alt+Space toggles Dynamic Island
  globalShortcut.register('Alt+Space', () => {
    toggleIsland();
  });

  // Global hotkey: Ctrl+Shift+Space toggles Main Window
  globalShortcut.register('CommandOrControl+Shift+Space', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    }
  });
}

// IPC listeners
ipcMain.on('island-set-visible', (_event, visible) => {
  if (!islandWindow) return;
  if (visible) {
    islandWindow.show();
  } else {
    islandWindow.hide();
  }
});

ipcMain.on('island-expand', (_event, expanded) => {
  if (!islandWindow) return;
  const currentBounds = islandWindow.getBounds();
  islandWindow.setSize(currentBounds.width, expanded ? 140 : 80);
});

ipcMain.on('island-toggle', () => {
  toggleIsland();
});

ipcMain.on('main-show', () => {
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
  }
});

ipcMain.on('main-hide', () => {
  if (mainWindow) {
    mainWindow.hide();
  }
});

// App Lifecycle
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    ensureBackendRunning();
    createMainWindow();
    createIslandWindow();
    createTray();
    registerShortcuts();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow();
        createIslandWindow();
      }
    });
  });

  app.on('will-quit', () => {
    globalShortcut.unregisterAll();
  });
}
