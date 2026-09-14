const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('secureTokenApp', {
  version: '1.0.0',
  secureMode: true,
  apiBase: 'http://localhost:8001',
  isDesktop: true,
});
