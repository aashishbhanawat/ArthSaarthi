const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getApiConfig: () => ipcRenderer.invoke('get-api-config'),
});
