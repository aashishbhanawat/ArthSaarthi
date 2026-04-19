# Android Native App: Optimization & Permissions

To ensure reliable operation of the ArthSaarthi backend on Android, the following settings and permissions are required or recommended.

## 1. Background Execution & Battery Optimization

### 1.1. Foreground Service
The `BackendService` should run as a **Foreground Service** to prevent the Android system from killing the Python backend when the app is in the background.
- **Requirement**: Call `startForeground()` from `BackendService.kt`.
- **Requirement**: A persistent notification must be displayed to the user.
- **Permission**: `android.permission.FOREGROUND_SERVICE` (already in manifest).
- **Android 14+**: Requires `android.permission.FOREGROUND_SERVICE_SPECIAL_USE` or a more specific type like `DATA_SYNC` if applicable.

### 1.2. Battery Optimization (Whitelisting)
By default, Android's "Doze" mode and App Standby will throttle background tasks.
- **Recommendation**: The app should request the user to disable battery optimization for ArthSaarthi.
- **Permission**: `android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`.
- **Action**: Direct the user to the "Battery Optimization" settings page if `isIgnoringBatteryOptimizations()` is false.

### 1.3. WakeLock
If the backend is performing critical background work (like the daily snapshot loop), a `WakeLock` may be needed to keep the CPU awake.

## 2. Permissions

### 2.1. Internet
- `android.permission.INTERNET`: Required for loopback communication with the frontend and fetching market prices. (Already present).

### 2.2. Notifications
- `android.permission.POST_NOTIFICATIONS`: Required on Android 13+ to show the foreground service notification.

## 3. Storage & Data Persistence

### 3.1. Internal Storage
The app uses `filesDir` (internal storage) for the SQLite database. This is private to the app and automatically backed up by Android (if `allowBackup="true"`).

### 3.2. Lifecycle Management
The `BackendService` is started in `onStartCommand` and should be stopped in `onDestroy`. Using `START_STICKY` ensures the service attempts to restart if killed by the system.

## 4. Troubleshooting
The unauthenticated `/api/v1/system/logs` endpoint is critical for remote debugging on Android devices where logcat access may be restricted.
