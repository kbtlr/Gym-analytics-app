const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

let backend = null;

function startBackend() {
  if (!app.isPackaged) return; // in dev, run `npm run start:backend` yourself

  const exe = path.join(process.resourcesPath, "backend", "gym-backend.exe");
  backend = spawn(exe, [], {
    cwd: app.getPath("userData"), // writable location for any DB/instance files
    windowsHide: true
  });
  backend.on("error", (err) => console.error("Backend failed to start:", err));
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    autoHideMenuBar: true,
    backgroundColor: "#0f1115",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  mainWindow.webContents.session.clearCache().catch(() => {});
  mainWindow.webContents.session.clearStorageData().catch(() => {});

  if (!app.isPackaged) mainWindow.webContents.openDevTools();
  mainWindow.loadFile(path.join(__dirname, "..", "core.html"));
}

app.whenReady().then(() => {
  startBackend();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("will-quit", () => {
  if (backend) backend.kill();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});