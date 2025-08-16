const { app, BrowserWindow, ipcMain } = require('electron');
const isDev = require('electron-is-dev');
const path = require('path');
const { spawn } = require('child_process');
const portfinder = require('portfinder');

let mainWindow;
let backendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const startUrl = isDev
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, '../frontend/dist/index.html')}`;

  mainWindow.loadURL(startUrl);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  portfinder.getPort((err, port) => {
    if (err) {
      console.error('Could not find a free port.', err);
      app.quit();
      return;
    }

    const backendExecutable = path.join(
      __dirname,
      '..',
      'backend_dist', // This will be the output directory for PyInstaller
      'main' // The name of the executable
    );

    // Add .exe for windows
    const executable = process.platform === 'win32' ? `${backendExecutable}.exe` : backendExecutable;

    backendProcess = spawn(executable, ['--port', port]);

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });

    // Pass the port to the frontend
    ipcMain.handle('get-api-port', () => port);
  });
}

app.on('ready', () => {
  if (!isDev) {
    startBackend();
  }
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
