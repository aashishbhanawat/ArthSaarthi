const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const portfinder = require('portfinder');

let backendProcess;
let mainWindow;

async function createMainWindow(backendPort) {
  const isDev = (await import('electron-is-dev')).default;

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      // It's recommended to turn off nodeIntegration and enable contextIsolation for security
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Expose the backend port to the renderer process via IPC
  // Remove existing handler if any (prevents error on window recreation)
  ipcMain.removeHandler('get-api-config');
  ipcMain.handle('get-api-config', () => ({
    host: '127.0.0.1',
    port: backendPort,
  }));

  if (isDev) {
    // In development, load the Vite dev server
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load the built frontend
    const indexPath = path.join(__dirname, '../dist/index.html');
    mainWindow.loadFile(indexPath);
  }

  // Create application menu
  const menuTemplate = [
    {
      label: 'File',
      submenu: [
        { role: 'quit' }
      ]
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
          click: () => {
            const { shell } = require('electron');
            shell.openExternal('https://aashishbhanawat.github.io/ArthSaarthi/');
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
}

async function startBackend() {
  const isDev = (await import('electron-is-dev')).default;
  return new Promise((resolve, reject) => {
    portfinder.getPortPromise()
      .then(port => {
        const backendPath = isDev
          ? path.join(__dirname, '../../backend/run_cli.py') // Placeholder for dev
          : path.join(process.resourcesPath, 'arthsaarthi-backend', 'arthsaarthi-backend'); // Production path

        console.log(`Attempting to start backend at: ${backendPath}`);

        const args = isDev ? ['run-dev-server', '--port', port] : ['run-dev-server', '--port', port];
        const command = isDev ? 'python' : backendPath;

        backendProcess = spawn(command, args, {
          env: {
            ...process.env,
            DEPLOYMENT_MODE: 'desktop',
            DATABASE_TYPE: 'sqlite',
            CACHE_TYPE: 'disk',
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

app.whenReady().then(async () => {
  try {
    const backendPort = await startBackend();
    console.log(`Backend started on port ${backendPort}`);
    await createMainWindow(backendPort);
  } catch (error) {
    console.error('Failed to start backend, quitting app.', error);
    app.quit();
  }

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  // Gracefully terminate the backend process
  if (backendProcess) {
    console.log('Terminating backend process...');
    backendProcess.kill();
  }
});
