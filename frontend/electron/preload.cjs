const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getApiConfig: () => ipcRenderer.invoke('get-api-config'),
  openUserGuide: (sectionId) => ipcRenderer.invoke('open-user-guide', sectionId),
  // Update notification API
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  openReleasePage: (url) => ipcRenderer.invoke('open-release-page', url),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
});

// Splash screen specific API
contextBridge.exposeInMainWorld('splashAPI', {
  onSeedingProgress: (callback) => ipcRenderer.on('seeding-progress', (event, data) => callback(data)),
  onSeedingError: (callback) => ipcRenderer.on('seeding-error', (event, error) => callback(error)),
  splashReady: () => ipcRenderer.send('splash-ready'),
  retrySeeding: () => ipcRenderer.send('retry-seeding'),
});
