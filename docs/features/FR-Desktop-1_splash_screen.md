# Feature Plan: Desktop Splash Screen (FR-Desktop-1)

**Feature ID:** FR-Desktop-1  
**Title:** Splash Screen During Asset Seeding  
**Priority:** P1  
**Category:** Desktop UX

---

## 1. Objective

Improve the first-run user experience for the desktop application by displaying a splash screen with progress indicator during the asset seeding process, instead of the current banner notification approach.

---

## 2. Current Behavior

- App launches and shows login screen immediately
- Asset seeding runs in background
- Banner notification shows seeding progress
- User can interact with app while seeding (may cause issues)

---

## 3. Proposed Behavior

- App launches and shows splash screen
- Splash screen displays:
  - ArthSaarthi logo
  - Progress bar or spinner
  - Status text (e.g., "Loading asset database...")
- After seeding completes, splash transitions to login screen
- If seeding fails, show error with retry option

---

## 4. Technical Design

### 4.1 Electron Main Process

```typescript
// Create splash window
const splashWindow = new BrowserWindow({
  width: 400,
  height: 300,
  frame: false,
  alwaysOnTop: true,
  // ... other options
});

splashWindow.loadFile('splash.html');

// Wait for seeding to complete
ipcMain.on('seeding-complete', () => {
  splashWindow.close();
  mainWindow.show();
});
```

### 4.2 Backend Seeding Status API

Add endpoint to check seeding status:
```
GET /api/v1/system/seeding-status
Response: { "status": "in_progress" | "complete" | "failed", "progress": 45 }
```

### 4.3 Splash Screen UI

Simple HTML/CSS page with:
- Logo centered
- Animated progress indicator
- Status text area

---

## 5. Acceptance Criteria

- [ ] Splash screen appears on app launch
- [ ] Progress indicator reflects actual seeding progress
- [ ] Splash transitions to login after seeding completes
- [ ] Error state shown if seeding fails
- [ ] Works on all platforms (Windows, macOS, Linux)

---

## 6. Dependencies

- Backend seeding status endpoint
- Electron IPC communication
