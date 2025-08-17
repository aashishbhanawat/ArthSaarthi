const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getApiPort: () => ipcRenderer.invoke('get-api-port'),
});
