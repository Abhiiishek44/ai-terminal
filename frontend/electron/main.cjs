// electron/main.cjs

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function configureLinuxRuntime() {
  if (process.platform !== 'linux') {
    return;
  }

  // Keep Chromium's noisy Linux backend logs out of dev terminal output.
  app.commandLine.appendSwitch('log-level', '3');
  app.commandLine.appendSwitch('disable-logging');

  // Prevent VAAPI/GPU initialization errors on systems without proper drivers.
  app.disableHardwareAcceleration();
  app.commandLine.appendSwitch('disable-gpu');
  app.commandLine.appendSwitch('disable-software-rasterizer');
  app.commandLine.appendSwitch('disable-accelerated-video-decode');
  app.commandLine.appendSwitch('use-gl', 'swiftshader');

  if (!process.env.LIBVA_DRIVER_NAME) {
    process.env.LIBVA_DRIVER_NAME = 'dummy';
  }

  // Reduce Chromium media backend issues commonly seen on Linux desktop setups.
  app.commandLine.appendSwitch(
    'disable-features',
    'VaapiVideoDecoder,VaapiVideoEncoder,UseChromeOSDirectVideoDecoder,UseChromeOSDirectVideoEncoder,UseOzonePlatform,WebRtcPipeWireCapturer,AcceleratedVideoDecodeLinuxGL'
  );

  // Avoid some portal/systemd DBus interactions that can fail in dev sessions.
  if (!process.env.GTK_USE_PORTAL) {
    process.env.GTK_USE_PORTAL = '0';
  }
  if (!process.env.ELECTRON_OZONE_PLATFORM_HINT) {
    process.env.ELECTRON_OZONE_PLATFORM_HINT = 'x11';
  }
}

configureLinuxRuntime();

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
    },
    autoHideMenuBar: true,
    backgroundColor: '#000000',
    titleBarStyle: 'default',
  });

  // Load the app
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    mainWindow.loadURL('http://localhost:5174');
    // Open DevTools in development
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle events
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for terminal operations
ipcMain.handle('execute-command', async (event, userInput) => {
  try {
    // This will be handled by the React app calling the backend API
    return { success: true };
  } catch (error) {
    console.error('Error in IPC handler:', error);
    return { success: false, error: error.message };
  }
});

// Handle app errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (error) => {
  console.error('Unhandled Rejection:', error);
});
