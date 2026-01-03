const { app, BrowserWindow, ipcMain, Menu, Tray, nativeImage } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const portfinder = require('portfinder');
const http = require('http');

let backendProcess;
let mainWindow;
let splashWindow;
let storedBackendPort;
let tray = null;
let isQuitting = false;

app.setName('ArthSaarthi');

// Single instance lock - prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  console.log('Another instance is already running. Quitting...');
  app.quit();
} else {
  app.on('second-instance', () => {
    // Someone tried to run a second instance, focus our window
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

/**
 * Create splash screen window
 */
async function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 400,
    height: 320,
    frame: false,
    resizable: false,
    transparent: false,
    alwaysOnTop: true,
    center: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));

  splashWindow.once('ready-to-show', () => {
    splashWindow.show();
  });

  return splashWindow;
}

/**
 * Make HTTP GET request to backend API
 */
async function makeGetRequest(port, endpoint) {
  return new Promise((resolve) => {
    const options = {
      hostname: '127.0.0.1',
      port: port,
      path: endpoint,
      method: 'GET',
      timeout: 5000,
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve({ error: 'Invalid response' });
        }
      });
    });

    req.on('error', () => {
      resolve({ error: 'Cannot connect to backend' });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ error: 'Request timeout' });
    });

    req.end();
  });
}

/**
 * Make HTTP POST request to backend API
 */
async function makePostRequest(port, endpoint, data = {}) {
  return new Promise((resolve) => {
    const postData = JSON.stringify(data);
    const options = {
      hostname: '127.0.0.1',
      port: port,
      path: endpoint,
      method: 'POST',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve({ success: true });
        }
      });
    });

    req.on('error', () => {
      resolve({ error: 'Cannot connect to backend' });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ error: 'Request timeout' });
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Check seeding status
 */
async function checkSeedingStatus(port) {
  return await makeGetRequest(port, '/api/v1/system/seeding-status');
}

/**
 * Trigger seeding if needed
 */
async function triggerSeedingIfNeeded(port) {
  const status = await checkSeedingStatus(port);

  if (status.status === 'needs_seeding') {
    // Trigger seeding
    await makePostRequest(port, '/api/v1/system/trigger-seeding');
    return true;
  }

  return status.status !== 'complete';
}

/**
 * Wait for seeding to complete with progress updates
 */
async function waitForSeedingComplete(port) {
  const POLL_INTERVAL = 2000; // 2 seconds
  const MAX_WAIT = 600000; // 10 minutes max for seeding
  const startTime = Date.now();

  // Initial message
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('seeding-progress', {
      progress: 5,
      message: 'Checking asset database...',
    });
  }

  // Check if seeding is needed and trigger it
  const needsSeeding = await triggerSeedingIfNeeded(port);

  if (!needsSeeding) {
    // Already complete
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.webContents.send('seeding-progress', {
        progress: 100,
        message: 'Ready!',
      });
    }
    return { success: true };
  }

  // Seeding in progress - poll until complete
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('seeding-progress', {
      progress: 10,
      message: 'Initializing asset database...',
    });
  }

  while (Date.now() - startTime < MAX_WAIT) {
    const status = await checkSeedingStatus(port);

    if (status.status === 'complete') {
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('seeding-progress', {
          progress: 100,
          message: `Ready! (${status.asset_count || 0} assets)`,
        });
      }
      return { success: true };
    }

    if (status.status === 'in_progress') {
      const progress = Math.min(95, 10 + (status.progress || 0) * 0.85);
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('seeding-progress', {
          progress: Math.round(progress),
          message: status.message || `Loading assets... (${status.asset_count || 0} loaded)`,
        });
      }
    }

    if (status.status === 'needs_seeding') {
      // Still waiting for seeding to start
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('seeding-progress', {
          progress: 10,
          message: `Loading asset database... (${status.asset_count || 0} assets loaded)`,
        });
      }
    }

    if (status.status === 'failed') {
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('seeding-error', status.error || 'Seeding failed');
      }
      return { success: false, error: status.error };
    }

    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
  }

  // Timeout - but allow proceeding if some assets loaded
  const finalStatus = await checkSeedingStatus(port);
  if (finalStatus.asset_count >= 100) {
    return { success: true };
  }

  return { success: false, error: 'Seeding timeout' };
}

/**
 * Check for app updates from GitHub Releases
 */
async function checkForUpdates() {
  const https = require('https');

  return new Promise((resolve) => {
    const options = {
      hostname: 'api.github.com',
      path: '/repos/aashishbhanawat/ArthSaarthi/releases/latest',
      method: 'GET',
      headers: {
        'User-Agent': 'ArthSaarthi-Desktop',
        'Accept': 'application/vnd.github.v3+json',
      },
      timeout: 10000,
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const release = JSON.parse(data);
          const latestVersion = (release.tag_name || '').replace(/^v/, '');
          const currentVersion = app.getVersion();

          // Simple version comparison (works for semver-like versions)
          if (latestVersion && isNewerVersion(latestVersion, currentVersion)) {
            resolve({
              available: true,
              version: latestVersion,
              url: release.html_url,
              name: release.name || `Version ${latestVersion}`,
            });
          } else {
            resolve({ available: false });
          }
        } catch {
          resolve({ available: false, error: 'Failed to parse response' });
        }
      });
    });

    req.on('error', (err) => {
      console.log('Update check failed:', err.message);
      resolve({ available: false, error: err.message });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ available: false, error: 'Request timeout' });
    });

    req.end();
  });
}

/**
 * Compare version strings (returns true if v1 > v2)
 */
function isNewerVersion(v1, v2) {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);

  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const p1 = parts1[i] || 0;
    const p2 = parts2[i] || 0;
    if (p1 > p2) return true;
    if (p1 < p2) return false;
  }
  return false;
}

/**
 * Create system tray icon with context menu
 */
async function createTray() {
  const isDev = (await import('electron-is-dev')).default;

  console.log('[TRAY] createTray() called');
  console.log('[TRAY] Platform:', process.platform);
  console.log('[TRAY] isDev:', isDev);

  // In dev, use the public folder; in production, use extraResources
  let iconPath;
  if (isDev) {
    iconPath = path.join(__dirname, '../public/ArthSaarthi.png');
  } else {
    // In production, the icon is extracted to Resources folder via extraResources
    iconPath = path.join(process.resourcesPath, 'tray-icon.png');
  }

  console.log('[TRAY] Icon path:', iconPath);

  let icon = nativeImage.createFromPath(iconPath);
  console.log('[TRAY] Icon loaded, isEmpty:', icon.isEmpty());
  console.log('[TRAY] Icon size:', icon.getSize());

  if (icon.isEmpty()) {
    console.error('[TRAY] ERROR: Failed to load tray icon from:', iconPath);
    return;
  }

  // Platform-specific icon sizing
  const isMac = process.platform === 'darwin';
  const isLinux = process.platform === 'linux';

  let trayIcon;
  if (isLinux) {
    console.log('[TRAY] Using Linux icon size: 22x22');
    trayIcon = icon.resize({ width: 22, height: 22 });
  } else if (isMac) {
    console.log('[TRAY] Using macOS icon size: 16x16 with template');
    trayIcon = icon.resize({ width: 16, height: 16 });
    trayIcon.setTemplateImage(true);
  } else {
    console.log('[TRAY] Using Windows icon size: 16x16');
    trayIcon = icon.resize({ width: 16, height: 16 });
  }

  console.log('[TRAY] Resized icon size:', trayIcon.getSize());

  try {
    tray = new Tray(trayIcon);
    console.log('[TRAY] Tray created successfully');
  } catch (err) {
    console.error('[TRAY] ERROR creating Tray:', err);
    return;
  }

  tray.setToolTip('ArthSaarthi');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show ArthSaarthi',
      click: () => {
        console.log('[TRAY] Context menu "Show" clicked');
        showMainWindow();
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        console.log('[TRAY] Context menu "Quit" clicked');
        isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);
  console.log('[TRAY] Context menu set');

  // Single click on tray icon shows window
  tray.on('click', () => {
    console.log('[TRAY] Tray icon clicked');
    showMainWindow();
  });

  // Double-click also shows window
  tray.on('double-click', () => {
    console.log('[TRAY] Tray icon double-clicked');
    showMainWindow();
  });

  console.log('[TRAY] All event handlers registered');
}

/**
 * Helper to show and focus the main window
 */
function showMainWindow() {
  console.log('[SHOW] showMainWindow() called');
  console.log('[SHOW] mainWindow exists:', !!mainWindow);

  if (mainWindow) {
    console.log('[SHOW] Window state - isMinimized:', mainWindow.isMinimized(),
      'isVisible:', mainWindow.isVisible(),
      'isDestroyed:', mainWindow.isDestroyed());

    if (mainWindow.isDestroyed()) {
      console.log('[SHOW] Window is destroyed, cannot show');
      return;
    }

    if (mainWindow.isMinimized()) {
      console.log('[SHOW] Restoring minimized window');
      mainWindow.restore();
    }

    console.log('[SHOW] Calling mainWindow.show()');
    mainWindow.show();

    console.log('[SHOW] Calling mainWindow.focus()');
    mainWindow.focus();

    // On macOS, bring app to foreground
    if (process.platform === 'darwin') {
      console.log('[SHOW] macOS: showing dock');
      app.dock.show();
    }

    console.log('[SHOW] Done - window should be visible');
  } else {
    console.log('[SHOW] ERROR: mainWindow is null/undefined!');
  }
}

async function createMainWindow(backendPort) {
  const isDev = (await import('electron-is-dev')).default;

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  ipcMain.removeHandler('get-api-config');
  ipcMain.handle('get-api-config', () => ({
    host: '127.0.0.1',
    port: backendPort,
  }));

  ipcMain.removeHandler('open-user-guide');
  ipcMain.handle('open-user-guide', async (event, sectionId) => {
    const { shell } = require('electron');
    let guidePath;
    if (isDev) {
      guidePath = path.join(__dirname, '../../docs/user_guide/index.html');
    } else {
      guidePath = path.join(process.resourcesPath, 'user_guide', 'index.html');
    }
    const url = `file://${guidePath}${sectionId ? '#' + sectionId : ''}`;
    shell.openExternal(url);
  });

  // Update notification handlers
  ipcMain.removeHandler('check-for-updates');
  ipcMain.handle('check-for-updates', async () => {
    return await checkForUpdates();
  });

  ipcMain.removeHandler('open-release-page');
  ipcMain.handle('open-release-page', async (event, url) => {
    const { shell } = require('electron');
    shell.openExternal(url);
  });

  ipcMain.removeHandler('get-app-version');
  ipcMain.handle('get-app-version', () => {
    return app.getVersion();
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    const indexPath = path.join(__dirname, '../dist/index.html');
    mainWindow.loadFile(indexPath);
  }

  const menuTemplate = [
    {
      label: 'File',
      submenu: [{ role: 'quit' }]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'User Guide',
          click: async () => {
            const isDev = (await import('electron-is-dev')).default;
            const { shell } = require('electron');
            if (isDev) {
              const guidePath = path.join(__dirname, '../../docs/user_guide/index.html');
              shell.openPath(guidePath);
            } else {
              const guidePath = path.join(process.resourcesPath, 'user_guide', 'index.html');
              shell.openPath(guidePath);
            }
          }
        },
        { type: 'separator' },
        {
          label: 'About ArthSaarthi',
          click: () => {
            const { dialog } = require('electron');
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About ArthSaarthi',
              message: 'ArthSaarthi - Personal Portfolio Management',
              detail: 'Version 1.0.0\n\nA comprehensive wealth tracking and portfolio management application.'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);

  // Minimize to tray on close instead of quitting
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  return mainWindow;
}

async function startBackend() {
  const isDev = (await import('electron-is-dev')).default;
  return new Promise((resolve, reject) => {
    portfinder.getPortPromise()
      .then(port => {
        const backendPath = isDev
          ? path.join(__dirname, '../../backend/run_cli.py')
          : path.join(process.resourcesPath, 'arthsaarthi-backend', 'arthsaarthi-backend');

        console.log(`Attempting to start backend at: ${backendPath}`);

        const args = isDev ? ['run-dev-server', '--port', port] : ['run-dev-server', '--port', port];
        const command = isDev ? 'python' : backendPath;

        backendProcess = spawn(command, args, {
          env: {
            ...process.env,
            DEPLOYMENT_MODE: 'desktop',
            DATABASE_TYPE: 'sqlite',
            CACHE_TYPE: 'disk',
            DEBUG: 'false',
          },
        });

        let resolved = false;
        const handleData = (data) => {
          const message = data.toString();
          console.log(`Backend output: ${message}`);
          if (!resolved && message.includes('Uvicorn running on')) {
            console.log('Backend is ready. Resolving startBackend promise.');
            resolved = true;
            resolve(port);
          }
        };

        backendProcess.stdout.on('data', handleData);
        backendProcess.stderr.on('data', handleData);

        backendProcess.on('close', (code) => {
          console.log(`Backend process exited with code ${code}`);
        });

        backendProcess.on('error', (err) => {
          console.error('Failed to start backend process.', err);
          reject(err);
        });
      })
      .catch(err => {
        console.error('Failed to find a free port for the backend:', err);
        reject(err);
      });
  });
}

async function transitionToMain() {
  if (mainWindow) {
    mainWindow.show();
  }

  if (splashWindow && !splashWindow.isDestroyed()) {
    setTimeout(() => {
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close();
        splashWindow = null;
      }
    }, 500);
  }
}

app.whenReady().then(async () => {
  try {
    // Show splash screen first
    await createSplashWindow();

    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.webContents.send('seeding-progress', {
        progress: 0,
        message: 'Starting backend...',
      });
    }

    const backendPort = await startBackend();
    storedBackendPort = backendPort;
    console.log(`Backend started on port ${backendPort}`);

    // Create main window (hidden)
    await createMainWindow(backendPort);

    // Create system tray icon
    await createTray();

    // Small delay for backend to be fully ready
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Wait for seeding to complete (this blocks until seeding is done)
    const result = await waitForSeedingComplete(backendPort);

    if (!result.success) {
      console.error('Seeding failed:', result.error);
      // Still transition but log the error
    }

    // Brief pause to show "Ready!" message
    await new Promise(resolve => setTimeout(resolve, 800));

    // Transition to main window
    await transitionToMain();

  } catch (error) {
    console.error('Failed to start app:', error);
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.webContents.send('seeding-error', error.message || 'Failed to start application');
    }
  }

  app.on('activate', async () => {
    console.log('[ACTIVATE] Dock icon clicked');
    console.log('[ACTIVATE] mainWindow exists:', !!mainWindow);
    console.log('[ACTIVATE] getAllWindows count:', BrowserWindow.getAllWindows().length);

    if (mainWindow && !mainWindow.isDestroyed()) {
      // Window exists but may be hidden - show it
      console.log('[ACTIVATE] Showing existing window');
      showMainWindow();
    } else if (BrowserWindow.getAllWindows().length === 0 && storedBackendPort) {
      // No windows exist - create new one
      console.log('[ACTIVATE] Creating new window');
      await createMainWindow(storedBackendPort);
      mainWindow.show();
    }
  });
});

ipcMain.on('retry-seeding', async () => {
  if (storedBackendPort) {
    // Reset seeding state and retry
    await makePostRequest(storedBackendPort, '/api/v1/system/seeding-reset');
    const result = await waitForSeedingComplete(storedBackendPort);
    if (result.success) {
      await transitionToMain();
    }
  }
});

ipcMain.on('splash-ready', () => {
  console.log('Splash screen is ready');
});

app.on('window-all-closed', () => {
  // Don't quit when all windows are closed - we're minimized to tray
  // Windows will quit when isQuitting is set
  if (process.platform === 'darwin') {
    // On macOS, don't quit - standard behavior
  }
});

// Set isQuitting flag before quitting so window close handler knows to really close
app.on('before-quit', () => {
  isQuitting = true;
});

app.on('will-quit', () => {
  if (backendProcess) {
    console.log('Terminating backend process...');
    backendProcess.kill();
  }
});
