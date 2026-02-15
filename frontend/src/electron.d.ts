// src/electron.d.ts

export interface ElectronAPI {
  executeCommand: (userInput: string) => Promise<{ success: boolean; error?: string }>;
  platform: string;
  versions: {
    node: string;
    chrome: string;
    electron: string;
  };
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
