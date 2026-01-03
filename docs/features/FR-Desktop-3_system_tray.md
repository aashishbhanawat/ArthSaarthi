# Feature Plan: System Tray Integration (FR-Desktop-3)

**Feature ID:** FR-Desktop-3  
**Title:** System Tray Integration for Desktop App  
**Priority:** P3  
**Category:** Desktop Enhancements  
**GitHub Issue:** #190

---

## 1. Objective

Allow desktop users to minimize the application to the system tray instead of closing it, keeping the app running in the background without cluttering the taskbar.

---

## 2. User Flow

1. User clicks the window close button (X)
2. App minimizes to system tray instead of quitting
3. Tray icon visible in system tray area
4. Right-click tray icon → Context menu appears
5. Click "Show ArthSaarthi" → Window is restored
6. Click "Quit" → App fully terminates

---

## 3. Technical Design

### 3.1 Electron Tray API Usage

```javascript
const { Tray, Menu, nativeImage } = require('electron');

let tray = null;

function createTray(mainWindow) {
  const icon = nativeImage.createFromPath(iconPath);
  tray = new Tray(icon);
  
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show ArthSaarthi', click: () => mainWindow.show() },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() }
  ]);
  
  tray.setToolTip('ArthSaarthi');
  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => mainWindow.show());
}
```

### 3.2 Window Close Behavior

```javascript
mainWindow.on('close', (event) => {
  if (!app.isQuitting) {
    event.preventDefault();
    mainWindow.hide();
  }
});
```

### 3.3 Changes to main.cjs

| Area | Change |
|------|--------|
| Imports | Add `Tray, Menu, nativeImage` |
| createTray() | New function to initialize tray |
| mainWindow close | Override to hide instead of quit |
| app.on('before-quit') | Set `app.isQuitting = true` |

---

## 4. Platform Considerations

| Platform | Behavior |
|----------|----------|
| **Windows** | Tray in right side of taskbar. Right-click for menu. |
| **macOS** | Menu bar app. Click for menu. |
| **Linux** | Varies by desktop environment. AppIndicator support. |

---

## 5. Acceptance Criteria

- [x] Tray icon appears when app starts
- [x] Closing window minimizes to tray (does not quit)
- [x] Context menu works on tray icon right-click
- [x] "Show ArthSaarthi" restores the window
- [x] "Quit" fully terminates the application
- [x] Works on Windows, macOS, and Linux

---

## 6. Testing Plan

### Manual Testing
- Start app → verify tray icon appears
- Close window → verify app stays in tray
- Right-click tray → verify menu appears
- Click Show → verify window restores
- Click Quit → verify app terminates

---

## 7. Files to Modify

| File | Changes |
|------|---------|
| `frontend/electron/main.cjs` | Add Tray initialization, close handler |

---

## 8. Dependencies

- Electron `Tray` API (built-in)
- Tray icon asset (reuse existing app icon)
