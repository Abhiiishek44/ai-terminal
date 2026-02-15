// electron/preload.cjs

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Execute terminal command
  executeCommand: (userInput) => ipcRenderer.invoke('execute-command', userInput),
  
  // Platform info
  platform: process.platform,
  
  // Node process info
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron,
  },
});

console.log('Preload script loaded successfully');
