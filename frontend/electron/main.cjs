const { app, BrowserWindow, globalShortcut, Tray, Menu, screen, ipcMain } = require('electron');
const path = require('path');
const http = require('http');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow = null;
let islandWindow = null;
let tray = null;
let isQuitting = false;
let backendProcess = null;
let lastIslandToggle = 0;

const FRONTEND_URL = process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173';
const BACKEND_URL = 'http://localhost:8000';

function checkBackendHealth(callback) {
  let finished = false;
  const done = (result) => {
    if (!finished) {
      finished = true;
      callback(result);
    }
  };

  const req = http.get(`${BACKEND_URL}/health`, (res) => {
    done(res.statusCode === 200);
    res.resume();
  });
  req.on('error', () => done(false));
  req.setTimeout(2500, () => {
    req.destroy();
    done(false);
  });
}

function ensureBackendRunning() {
  checkBackendHealth((running) => {
    if (!running) {
      console.log('[Electron] Backend not detected on :8000. Spawning Python backend daemon...');
      const projectRoot = path.resolve(__dirname, '../../');
      const pythonExe = path.join(projectRoot, 'backend', '.venv', 'Scripts', 'python.exe');
      
      try {
        const logPath = path.join(projectRoot, 'backend_daemon.log');
        let outLog = 'ignore';
        try {
          outLog = fs.openSync(logPath, 'a');
        } catch (e) {
          console.warn('[Electron] Could not open backend_daemon.log exclusively, proceeding with ignore.');
        }
        backendProcess = spawn(pythonExe, ['-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8000'], {
          cwd: projectRoot,
          detached: true,
          stdio: ['ignore', outLog, outLog]
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

const distIndex = path.join(__dirname, '../dist/index.html');
const hasDist = fs.existsSync(distIndex);

function loadWindowContent(targetWindow, queryParam = '') {
  const queryStr = queryParam ? (queryParam.startsWith('?') ? queryParam : `?${queryParam}`) : '';
  const devUrl = `${FRONTEND_URL}${queryStr}`;

  http.get(FRONTEND_URL, (res) => {
    if (res.statusCode === 200) {
      targetWindow.loadURL(devUrl).catch(() => {
        if (hasDist) {
          targetWindow.loadFile(distIndex, { search: queryParam.replace(/^\?/, '') });
        }
      });
    } else {
      if (hasDist) {
        targetWindow.loadFile(distIndex, { search: queryParam.replace(/^\?/, '') });
      } else {
        targetWindow.loadURL(devUrl).catch(() => {});
      }
    }
    res.resume();
  }).on('error', () => {
    if (hasDist) {
      console.log(`[Electron] Dev server offline, loading pre-built bundle from ${distIndex}`);
      targetWindow.loadFile(distIndex, { search: queryParam.replace(/^\?/, '') });
    } else {
      targetWindow.loadURL(devUrl).catch(() => {});
    }
  });
}

function showMainWindow() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.show();
    mainWindow.setAlwaysOnTop(true);
    mainWindow.focus();
    mainWindow.setAlwaysOnTop(false);
  }
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    title: 'NOVA AI - ADA',
    icon: path.join(__dirname, '../src-tauri/icons/icon.ico'),
    backgroundColor: '#020409',
    show: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  loadWindowContent(mainWindow);

  mainWindow.webContents.on('did-finish-load', () => {
    console.log('[Electron] mainWindow did-finish-load! URL:', mainWindow.webContents.getURL());
  });

  mainWindow.webContents.on('console-message', (_event, level, message, line, sourceId) => {
    console.log(`[MainWindow Console] (${level}) ${message} [${sourceId}:${line}]`);
  });

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription) => {
    console.warn(`[Electron] mainWindow failed to load (${errorCode}: ${errorDescription})`);
    if (hasDist && !mainWindow.webContents.getURL().includes('index.html')) {
      console.log('[Electron] mainWindow fallback to pre-built dist/index.html');
      mainWindow.loadFile(distIndex);
    }
  });

  mainWindow.once('ready-to-show', () => {
    showMainWindow();
  });

  // Intercept Alt+Space and shortcuts inside MainWindow before Windows OS swallows them
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.type === 'keyDown') {
      if ((input.alt && (input.code === 'Space' || input.key === ' ')) ||
          (input.control && (input.code === 'Space' || input.key === ' ')) ||
          input.key === 'F2') {
        event.preventDefault();
        toggleIsland();
      }
    }
  });

  setTimeout(() => {
    if (mainWindow && !mainWindow.isDestroyed() && !mainWindow.isVisible()) {
      mainWindow.show();
      mainWindow.focus();
    }
  }, 1200);

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
  const islandWidth = 330;
  const islandHeight = 46;
  const islandX = Math.round((screenWidth - islandWidth) / 2);
  const islandY = 12;

  islandWindow = new BrowserWindow({
    width: islandWidth,
    height: islandHeight,
    x: islandX,
    y: islandY,
    frame: false,
    transparent: true,
    hasShadow: false,
    backgroundColor: '#00000000',
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    focusable: true,
    show: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  islandWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  islandWindow.setAlwaysOnTop(true, 'screen-saver');

  loadWindowContent(islandWindow, 'island=true');

  islandWindow.webContents.on('did-finish-load', () => {
    console.log('[Electron] islandWindow did-finish-load! URL:', islandWindow.webContents.getURL());
  });

  islandWindow.webContents.on('console-message', (_event, level, message, line, sourceId) => {
    console.log(`[IslandWindow Console] (${level}) ${message} [${sourceId}:${line}]`);
  });

  islandWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription) => {
    console.warn(`[Electron] islandWindow failed to load (${errorCode}: ${errorDescription})`);
    if (hasDist && !islandWindow.webContents.getURL().includes('index.html')) {
      console.log('[Electron] islandWindow fallback to pre-built dist/index.html');
      islandWindow.loadFile(distIndex, { search: 'island=true' });
    }
  });

  // Intercept Escape and Alt+Space inside island
  islandWindow.webContents.on('before-input-event', (event, input) => {
    if (input.type === 'keyDown') {
      if (input.key === 'Escape' || (input.alt && (input.code === 'Space' || input.key === ' '))) {
        event.preventDefault();
        islandWindow.webContents.send('shortcut-triggered', 'collapse');
      }
    }
  });

  // Auto-collapse when clicking outside the Island (guarded against focus switch blurs)
  islandWindow.on('blur', () => {
    if (Date.now() - lastIslandToggle < 500) return;
    if (islandWindow && !islandWindow.isDestroyed()) {
      islandWindow.webContents.send('shortcut-triggered', 'collapse');
    }
  });

  islandWindow.once('ready-to-show', () => {
    islandWindow.show();
  });

  setTimeout(() => {
    if (islandWindow && !islandWindow.isDestroyed() && !islandWindow.isVisible()) {
      islandWindow.show();
    }
  }, 1200);
}

function createTray() {
  const iconPath = path.join(__dirname, '../src-tauri/icons/icon.ico');
  tray = new Tray(iconPath);
  tray.setToolTip('ADA - Autonomous Digital Assistant');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open NOVA AI Dashboard (Ctrl+Shift+Space)',
      click: () => {
        showMainWindow();
      }
    },
    {
      label: 'Toggle Dynamic Island (Alt+Space / F2)',
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
    if (mainWindow && !mainWindow.isDestroyed()) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        showMainWindow();
      }
    }
  });
}

function toggleIsland() {
  if (!islandWindow || islandWindow.isDestroyed()) return;
  lastIslandToggle = Date.now();
  islandWindow.show();
  islandWindow.focus();
  islandWindow.webContents.send('shortcut-triggered', 'toggle');
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
  globalShortcut.unregisterAll();

  // Multi-layer reliable hotkeys for Dynamic Island
  const islandKeys = [
    'Alt+Space',
    'CommandOrControl+Space',
    'CommandOrControl+Alt+Space',
    'Alt+I',
    'F2'
  ];

  islandKeys.forEach((key) => {
    try {
      const reg = globalShortcut.register(key, () => {
        console.log(`[Shortcut] Triggered: ${key}`);
        toggleIsland();
      });
      console.log(`[Shortcut] Registered ${key}:`, reg);
    } catch (err) {
      console.warn(`[Shortcut] Failed to register ${key}:`, err);
    }
  });

  // Toggle Main Dashboard Window
  const mainKeys = [
    'CommandOrControl+Shift+Space',
    'Alt+D',
    'F9'
  ];

  mainKeys.forEach((key) => {
    try {
      const reg = globalShortcut.register(key, () => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          if (mainWindow.isVisible()) {
            mainWindow.hide();
          } else {
            showMainWindow();
          }
        }
      });
      console.log(`[Shortcut] Registered ${key}:`, reg);
    } catch (err) {
      console.warn(`[Shortcut] Failed to register ${key}:`, err);
    }
  });
}

// IPC listeners
ipcMain.on('island-set-visible', (_event, visible) => {
  if (!islandWindow || islandWindow.isDestroyed()) return;
  if (visible) {
    islandWindow.show();
  } else {
    islandWindow.hide();
  }
});

let collapseTimeout = null;

ipcMain.on('island-expand', (_event, expanded, customHeight) => {
  if (!islandWindow || islandWindow.isDestroyed()) return;
  const primaryDisplay = screen.getPrimaryDisplay();
  const screenWidth = primaryDisplay.workAreaSize.width;

  if (collapseTimeout) {
    clearTimeout(collapseTimeout);
    collapseTimeout = null;
  }

  if (expanded) {
    const targetWidth = 500;
    const targetHeight = Math.max(customHeight || 280, 280);
    const targetX = Math.round((screenWidth - targetWidth) / 2);
    islandWindow.setBounds({ x: targetX, y: 10, width: targetWidth, height: targetHeight });
  } else {
    collapseTimeout = setTimeout(() => {
      if (islandWindow && !islandWindow.isDestroyed()) {
        const targetWidth = 330;
        const targetHeight = 48;
        const targetX = Math.round((screenWidth - targetWidth) / 2);
        islandWindow.setBounds({ x: targetX, y: 10, width: targetWidth, height: targetHeight });
      }
    }, 280);
  }
});

ipcMain.on('island-toggle', () => {
  toggleIsland();
});

ipcMain.on('main-show', () => {
  showMainWindow();
});

ipcMain.on('main-hide', () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.hide();
  }
});

// App Lifecycle
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    showMainWindow();
    if (islandWindow && !islandWindow.isDestroyed()) {
      toggleIsland();
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
