# ⚡ Electron 33+ Production Desktop Architecture (`frameworks/desktop/electron.md`)

> **Standard Identifier**: `FW-DESKTOP-ELECTRON-001`  
> **Framework**: Electron 33+ (Chromium + Node.js Context Isolation & Sandboxed Desktop)  
> **Status**: Active / Production Standard  
> **Governing Rules**: **R-001**, **R-034**, **R-060**, **R-064**, **R-251**, **R-273**  
> **Last Updated**: 2026-11-20  

---

## 1. Core Philosophy & Golden Rule

> **Golden Rule**: *Renderer processes MUST be fully sandboxed with `contextIsolation: true`, `nodeIntegration: false`, and `sandbox: true`. Never expose raw Node.js primitives or arbitrary IPC channels to the webview. Expose exclusively typed, audited, and parameter-validated methods through `contextBridge.exposeInMainWorld()`.*

---

## 2. Secure Process Architecture & Sandboxing

Modern Electron enforces strict process boundary separation between the privileged Main process and unprivileged Renderer processes.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ELECTRON 33+ ARCHITECTURE                       │
├────────────────────────────────────────────────────────────────────────┤
│  PRIVILEGED MAIN PROCESS (Node.js Runtime)                             │
│  • Full Operating System Access (FS, SQLite, OS APIs, System Tray)     │
│  • Window Management (`BrowserWindow`) & Session Lifecycle             │
│  • Validates & Handles IPC via `ipcMain.handle("channel", fn)`         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ IPC Bridge (Typed Structured Clone)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PRELOAD SCRIPT (`contextBridge.exposeInMainWorld`)                    │
│  • Executes before web content in isolated JavaScript context          │
│  • Exposes minimal typed API contract (`window.desktopApi`)            │
│  • Enforces argument sanitization & channel allowlisting               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Safe Window API Bridge
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  SANDBOXED RENDERER PROCESS (Chromium Web Engine)                      │
│  • `contextIsolation: true`, `sandbox: true`, `nodeIntegration: false` │
│  • Modern Web UI (React 19 / Vue 3.5 / Svelte 5 / Next.js SPA)         │
│  • ZERO access to `require("fs")`, `process.env`, or raw sockets      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Production IPC Pipeline & Context Isolation

### 3.1 Hardened Main Window Configuration (`src/main/index.ts`)

```typescript
import { app, BrowserWindow, ipcMain, session } from 'electron';
import * as path from 'path';

let mainWindow: BrowserWindow | null = null;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      nodeIntegrationInWorker: false,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
    },
  });

  // Intercept window open attempts and prevent untrusted external popup windows
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // Only open trusted external URLs in the user's default browser
    if (url.startsWith('https://')) {
      import('electron').then(({ shell }) => shell.openExternal(url));
    }
    return { action: 'deny' };
  });

  // Enforce strict CSP in production
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: asset:;",
        ],
      },
    });
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  mainWindow.loadURL(
    app.isPackaged
      ? `file://${path.join(__dirname, '../renderer/index.html')}`
      : 'http://localhost:5173'
  );
}

app.whenReady().then(createWindow);
```

### 3.2 Secure Preload Bridge (`src/preload/index.ts`)

```typescript
import { contextBridge, ipcRenderer } from 'electron';

export interface ExportDataPayload {
  reportId: string;
  format: 'json' | 'csv';
}

const desktopApi = {
  getAppVersion: (): Promise<string> => ipcRenderer.invoke('app:get-version'),
  exportData: (payload: ExportDataPayload): Promise<{ success: boolean; filePath: string }> => {
    // Validate arguments inside preload before sending over IPC
    if (!payload.reportId || typeof payload.reportId !== 'string') {
      throw new Error('Invalid reportId supplied to exportData');
    }
    if (!['json', 'csv'].includes(payload.format)) {
      throw new Error('Unsupported export format');
    }
    return ipcRenderer.invoke('data:export', payload);
  },
};

// Expose strictly typed API to window object
contextBridge.exposeInMainWorld('desktopApi', desktopApi);

// Type declaration for the Renderer TypeScript scope
export type DesktopApi = typeof desktopApi;
```

### 3.3 Main Process IPC Handler (`src/main/ipc.ts`)

```typescript
import { app, ipcMain, dialog } from 'electron';
import * as fs from 'fs/promises';
import { ExportDataPayload } from '../preload';

export function registerIpcHandlers(): void {
  ipcMain.handle('app:get-version', () => {
    return app.getVersion();
  });

  ipcMain.handle('data:export', async (event, payload: ExportDataPayload) => {
    // Defense-in-depth: Re-validate payload inside main handler
    if (!payload || !payload.reportId) {
      throw new Error('Malformed payload');
    }

    const { canceled, filePath } = await dialog.showSaveDialog({
      title: 'Save Report Export',
      defaultPath: `report-${payload.reportId}.${payload.format}`,
      filters: [{ name: 'Export Files', extensions: [payload.format] }],
    });

    if (canceled || !filePath) {
      return { success: false, filePath: '' };
    }

    const dummyReport = JSON.stringify({ id: payload.reportId, generatedAt: new Date().toISOString() });
    await fs.writeFile(filePath, dummyReport, 'utf-8');

    return { success: true, filePath };
  });
}
```

---

## 4. Native OS Integration & Window Lifecycle

Electron desktop applications must integrate with the host OS lifecycle cleanly:

1. **Platform-Specific Window Close**:
   On macOS (`darwin`), closing a window typically hides the window while keeping the app alive in the Dock, whereas on Windows/Linux closing the last window quits the application:
   ```typescript
   app.on('window-all-closed', () => {
     if (process.platform !== 'darwin') {
       app.quit();
     }
   });

   app.on('activate', () => {
     if (BrowserWindow.getAllWindows().length === 0) {
       createWindow();
     }
   });
   ```
2. **Single Instance Lock**:
   Prevent multiple conflicting instances of the desktop application from running concurrently:
   ```typescript
   const gotTheLock = app.requestSingleInstanceLock();
   if (!gotTheLock) {
     app.quit();
   } else {
     app.on('second-instance', () => {
       if (mainWindow) {
         if (mainWindow.isMinimized()) mainWindow.restore();
         mainWindow.focus();
       }
     });
   }
   ```

---

## 5. Security Hardening & Performance Optimization

1. **Disable Dangerous Chromium Flags**:
   Never enable flags that disable site isolation or web security:
   ```typescript
   app.commandLine.appendSwitch('disable-features', 'OutOfBlinkCors');
   ```
2. **Prevent Navigation to Remote / Untrusted URLs**:
   ```typescript
   mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
     const parsedUrl = new URL(navigationUrl);
     if (parsedUrl.origin !== 'http://localhost:5173' && parsedUrl.protocol !== 'file:') {
       event.preventDefault();
     }
   });
   ```
3. **Memory Management & Garbage Collection**:
   - Explicitly nullify closed window references (`mainWindow = null;`).
   - Remove IPC event listeners on component unmount to prevent retained renderer closures.
4. **Auto-Updater Verification**:
   When using `electron-updater`, enforce code signing with valid certificates (Apple Developer ID for macOS, EV Code Signing Certificate for Windows) and verify SHA-512 release digests before applying updates.

---

## 6. Common Pitfalls & Anti-Patterns

- ❌ **Enabling `nodeIntegration: true`**: Exposing Node.js APIs directly in the renderer allows any remote script or malicious npm package to execute arbitrary OS shell commands.
- ❌ **Disabling `contextIsolation`**: Disabling isolation allows malicious renderer scripts to prototype-pollute the JavaScript execution environment and bypass security checks.
- ❌ **Exposing Raw `ipcRenderer`**: Exposing `ipcRenderer.send` or `ipcRenderer.on` directly on `window` allows unvalidated arbitrary messages to be broadcast to the main process.
- ❌ **Using Synchronous IPC**: Calling `ipcRenderer.sendSync()` freezes the entire UI renderer thread while waiting for the main process to respond. Always use `ipcRenderer.invoke()` with `ipcMain.handle()`.

---

## 7. Verification Checklist

- [ ] `contextIsolation: true`, `nodeIntegration: false`, and `sandbox: true` are configured on all `BrowserWindow` instances.
- [ ] Minimal, typed API contracts exposed via `contextBridge.exposeInMainWorld()`.
- [ ] Strict Content Security Policy injected via `session.webRequest.onHeadersReceived()`.
- [ ] Navigation and new window creation intercepted via `setWindowOpenHandler` and `will-navigate`.
- [ ] `app.requestSingleInstanceLock()` prevents duplicate processes.
- [ ] No synchronous IPC (`sendSync`) used anywhere in the codebase.
- [ ] Packaging builds pass cleanly with `electron-builder` or `@electron-forge/cli`.
