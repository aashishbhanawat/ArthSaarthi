# FR: Android Background Daily Portfolio Snapshot (Issue #492)

**Version:** 1.0  
**Date:** 2026-07-26  
**Target Release:** Current iteration  

---

## 1. Overview
Currently, the Android app only takes portfolio snapshots on-demand or while the app is active in the foreground. Since mobile phones are "always-on" devices, we want to replicate the server-mode daily cron snapshot behavior on Android without draining the user's battery or keeping a persistent background service running. This will be achieved using Android's battery-aware `WorkManager`.

---

## 2. Requirements & Implementation Details

### 2.1 Backend Changes (Python / FastAPI)
*   **New API Endpoint:** Create `POST /api/v1/system/snapshots/run-daily`.
    *   **Action:** Call the existing `take_daily_snapshots_for_all(db)` from `app.services.snapshot_service`.
    *   **Response:** Return a JSON payload with the count of portfolios updated and the date of the snapshot.
    *   **Security:** Since this is triggered by the local Android worker, it will naturally be protected because the server only binds to `127.0.0.1`.
*   **No change to `main.py` asyncio loop:** The existing `_desktop_snapshot_loop` stays as-is. It handles in-session snapshots.

### 2.2 Frontend Changes (React / Capacitor)
*   **Settings UI:** Add a toggle in the settings menu: "Enable Daily Background Snapshots (Android Only)".
    *   By default, this should be **enabled**.
*   **Capacitor Plugin Call:** 
    *   When toggled ON, the React app calls a new Capacitor plugin method: `PythonBackend.enableDailySnapshot()`.
    *   When toggled OFF, it calls: `PythonBackend.disableDailySnapshot()`.

### 2.3 Android Layer Changes (Kotlin / WorkManager)
*   **Dependencies:** Add `androidx.work:work-runtime-ktx:2.9.1` (or latest stable 2.x) to `frontend/android/app/build.gradle.kts`.
*   **Worker Class (`SnapshotWorker.kt`):**
    1.  Ensure `BackendService` is running. If not, start it.
    2.  Poll `http://127.0.0.1:<port>/api/v1/auth/status` until the backend is healthy (re-using logic from `PythonBackendPlugin.waitForBackendReady`).
    3.  Make a POST request to `http://127.0.0.1:<port>/api/v1/system/snapshots/run-daily`.
    4.  *(Optional but recommended)* Issue a shutdown signal to the backend if it was started *only* for this worker, to save memory.
*   **Plugin Methods (`PythonBackendPlugin.kt`):**
    *   Implement `enableDailySnapshot()`: Enqueues a `PeriodicWorkRequest` (repeat interval: 24 hours, flex interval: 1 hour) with constraint `NetworkType.CONNECTED`.
    *   Implement `disableDailySnapshot()`: Cancels the specific work request by tag (e.g., `daily_portfolio_snapshot`).
*   **Boot Persistence:** Ensure WorkManager handles reboots naturally. Add `<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />` to `AndroidManifest.xml`.

### 2.4 DB Impact (SQLite)
*   **No schema changes required.** The existing `portfolio_snapshot` table works perfectly.
*   **Security (Encryption):**
    *   Currently, the SQLite DB is stored in the app's internal `filesDir`, which is sandboxed and encrypted by the Android OS (file-based encryption on modern Android).
    *   *No column-level encryption is required for this specific feature*, as we are just automating the execution of an existing process.

### 2.5 Dependencies & Libraries
*   **Android/Kotlin:** `androidx.work:work-runtime-ktx`
*   **Python:** No new libraries needed. The existing environment (`yfinance`, `httpx`, etc.) is fully compatible with Chaquopy.

---

## 3. Testing Plan

### 3.1 Manual Testing
1.  **Worker Registration:** Open the Android app, go to Settings, and verify the background sync toggle is ON. Inspect logs (via Android Studio logcat) to ensure `WorkManager` enqueued the job.
2.  **Toggle Off:** Turn off the toggle. Verify in logs that the WorkManager job was cancelled.
3.  **Forced Execution (App Closed):** 
    *   Close the app entirely.
    *   Use ADB to force the WorkManager job: `adb shell am broadcast -a androidx.work.diagnostics.REQUEST_DIAGNOSTICS` and `adb shell cmd activity idle-maintenance`.
    *   Verify via Logcat that `SnapshotWorker` started, booted the Python backend, triggered the snapshot, and succeeded.
4.  **Network Constraint Test:** Turn off WiFi/Data. Attempt to force the job. Verify it remains in `ENQUEUED` state and does not run. Turn WiFi back on; verify it runs.

### 3.2 Automation Strategy
*   **Backend (Pytest):** 
    *   Write a unit test for the new `POST /api/v1/system/snapshots/run-daily` endpoint (mocking the actual snapshot logic to verify the route and response).
*   **Frontend (Jest/Playwright):** 
    *   *Not applicable* for deep background testing. UI toggle tests can mock the Capacitor plugin call.
*   **E2E:** 
    *   E2E cannot easily test Android WorkManager constraints. Rely on manual ADB testing for the OS-level scheduling.

---

## 4. Documentation Updates

The following files must be updated before the feature branch is merged:

1.  **`README.md` & `docs/user_guide.md`**: Add a note under the Android section explaining the automatic daily snapshot feature and how to disable it in settings to save battery/data if desired.
2.  **`docs/architecture.md` / `code_flow_guide.md`**: Document the flow of `WorkManager -> SnapshotWorker -> BackendService -> API Endpoint`.
3.  **`docs/troubleshooting.md`**: Add a section: "Android Portfolio History not updating" -> Explain battery optimization settings, Doze mode, and checking the toggle in the app settings.
4.  **`docs/workflow_history.md`**: Log the completion of Issue #492.
5.  **`docs/project_handoff_summary.md`**: Update the "Current State" and "Android Features" section to reflect the new background capability.
6.  **`docs/requirements.md`**: Update `FR6.7` (Historical Data) or add a specific line item in the Android section about guaranteed daily data points.

---

## 5. UI/UX Considerations
*   The only visible change is the toggle in the Settings page.
*   **Mobile Friendly:** Ensure the Settings toggle uses a standard native-looking switch (e.g., Ionic/Material toggle) and provides a small helper text explaining that it uses minimal battery and only runs on WiFi/Data.
