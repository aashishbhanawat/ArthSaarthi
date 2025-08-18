const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const portfinder = require('portfinder');
const isDev = require('electron-is-dev');

let backendProcess;
let mainWindow;

function createMainWindow(backendPort) {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
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
    const indexPath = path.join(__dirname, '../dist/index.html');
    mainWindow.loadFile(indexPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  return new Promise((resolve, reject) => {
    portfinder.getPortPromise()
      .then(port => {
        const backendPath = isDev
          ? path.join(__dirname, '../../backend/run_cli.py') // Placeholder for dev
          : path.join(process.resourcesPath, 'arthsaarthi-backend'); // Production path

        const args = isDev ? ['run-dev-server', '--port', port] : ['--port', port];
        const command = isDev ? 'python' : backendPath;

        backendProcess = spawn(command, args, {
          env: { ...process.env, DEPLOYMENT_MODE: 'desktop' },
        });

        backendProcess.stdout.on('data', (data) => {
          console.log(`Backend stdout: ${data}`);
          // Resolve once we get some output, assuming it's ready
          // A more robust solution would be to wait for a specific message
          resolve(port);
        });

        backendProcess.stderr.on('data', (data) => {
          console.error(`Backend stderr: ${data}`);
        });

        backendProcess.on('close', (code) => {
          console.log(`Backend process exited with code ${code}`);
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
    createMainWindow(backendPort);
  } catch (error) {
    console.error('Failed to start backend, quitting app.', error);
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
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
