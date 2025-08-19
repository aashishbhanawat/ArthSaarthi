const { app, BrowserWindow, ipcMain } = require('electron');
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
    const testPath = path.join(__dirname, '../dist/test.html');
    mainWindow.loadFile(testPath);
    mainWindow.webContents.openDevTools();
  }

  mainWindow.setMenu(null);

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
          env: { ...process.env, DEPLOYMENT_MODE: 'desktop' },
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
