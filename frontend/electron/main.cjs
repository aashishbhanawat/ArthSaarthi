const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const portfinder = require('portfinder');
const http = require('http');

let backendProcess;
let mainWindow;
let splashWindow;
let storedBackendPort;

app.setName('ArthSaarthi');

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
    if (BrowserWindow.getAllWindows().length === 0 && storedBackendPort) {
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
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  if (backendProcess) {
    console.log('Terminating backend process...');
    backendProcess.kill();
  }
});
