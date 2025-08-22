# Feature Plan: Native Executable Installers (NFR10)

## 1. Objective

To package the ArthSaarthi application as a single, one-click executable/installer for Windows, macOS, and Linux. This will provide a native desktop experience and eliminate the need for end-users to have Docker or a Python/Node.js environment.

## 2. Technology Stack

*   **Electron:** Will be used to create the main application window, manage the application lifecycle, and orchestrate the backend process.
*   **PyInstaller:** Will be used to bundle the entire Python/FastAPI backend, including the Python interpreter and all dependencies, into a single, self-contained executable.
*   **Electron Builder:** Will be used to package the Electron app, the React frontend assets, and the bundled Python backend into distributable installers (`.exe`, `.dmg`, etc.).

## 3. High-Level Architecture

The final application will consist of three main parts working in concert:

1.  **Electron Main Process (`electron/main.js`):**
    *   This is the application's entry point.
    *   On app start, it will use a library like `portfinder` to find a free network port.
    *   It will then launch the bundled Python backend executable as a child process, passing the selected port as a command-line argument.
    *   It will create a `BrowserWindow` and load the production-built frontend (`frontend/dist/index.html`).
    *   The frontend's base URL for API calls will be dynamically configured to `http://localhost:<port>`.
    *   On app quit, it will gracefully terminate the backend child process.

2.  **Backend Packaging (PyInstaller):**
    *   A PyInstaller build script (`build-backend.spec`) will be created to define the bundling process.
    *   It will bundle the Python interpreter and all dependencies from `requirements.txt`.
    *   The entry point will be a small Python script that starts the Uvicorn server for our FastAPI app. This script will be configured to read the port from the command-line arguments.
    *   The backend will be pre-configured to use `DATABASE_TYPE=sqlite` and `CACHE_TYPE=disk` for these builds.
    *   This process will produce a single backend executable (e.g., `arthsaarthi-backend.exe`).

*   **Conditional Feature Disabling:**
    *   To ensure a true single-user experience, multi-user features will be disabled when the application runs in this mode (`DATABASE_TYPE=sqlite` and `ENVIRONMENT=production`).
    *   **Backend:** The API endpoints for user management (`/api/v1/users/`) will not be registered by the FastAPI application.
    *   **Frontend:** The UI for user management (the "User Management" link in the navigation) will be hidden. This is controlled by a `deployment_mode` flag sent from the backend to the frontend upon login.

3.  **Frontend & Final Packaging (Electron Builder):**
    *   The `electron-builder` configuration will be added to `frontend/package.json`.
    *   It will be configured to include the frontend build output (`dist/`) and the backend executable (from the PyInstaller step) as an "extra resource". This ensures the backend executable is shipped inside the final application package.

## 4. Implementation Plan

1.  Add `electron`, `electron-builder`, `electron-is-dev`, and `portfinder` as dev dependencies to `frontend/package.json`.
2.  Add `pyinstaller` to the backend's development requirements (`backend/requirements.in`).
3.  Create a new `electron/` directory at the project root to house the Electron main process code (`main.js`) and a `preload.js` for secure communication between the main and renderer processes.
4.  Implement the logic in `main.js` to manage the backend child process and create the browser window.
5.  Create a PyInstaller spec file for the backend.
6.  Update the build scripts (`scripts/build-*.sh`) to orchestrate the full, multi-step build process.
7.  Update the GitHub Actions `release.yml` workflow to use more descriptive artifact names.

---

## 5. Debugging and Lessons Learned

Building a packaged Electron application that bundles a Python backend is a complex process with many potential points of failure. This section documents the debugging journey for this feature.

### 5.1. `fpm` on ARM Architecture

*   **Problem:** The `electron-builder` tool failed to build the `.deb` package on the ARM-based Raspberry Pi. The error was `cannot execute binary file: Exec format error`.
*   **Root Cause:** `electron-builder` downloads a pre-built `fpm` (a tool for creating packages) that is compiled for x86 architectures, which is incompatible with ARM.
*   **Solution:** The build script was modified to set the `USE_SYSTEM_FPM=true` environment variable when running `electron-builder`. This forces it to use the `fpm` installed on the system (via `sudo gem install fpm`), which will be the correct architecture.

### 5.2. `EACCES: Permission Denied` Error

*   **Problem:** After being packaged, the application would fail to launch the backend, throwing an `EACCES` error.
*   **Root Cause:** This was a misleading error. The initial thought was a file permission issue, but the real problem was that the application was trying to execute a *directory* instead of the backend executable file *inside* that directory.
*   **Solution:** The path in `frontend/electron/main.cjs` that points to the backend executable was corrected to include the final filename (e.g., `.../resources/arthsaarthi-backend/arthsaarthi-backend`).

### 5.3. Missing Python Modules (`ModuleNotFoundError`)

*   **Problem:** The backend would crash with `ModuleNotFoundError: No module named 'passlib.handlers.bcrypt'`.
*   **Root Cause:** PyInstaller's static analysis cannot always detect dependencies that are loaded dynamically (as "plugins"). The `passlib` library loads its hashing algorithms this way.
*   **Solution:** The `backend/build-backend.spec` file was updated to explicitly include the missing module in the `hiddenimports` array.

### 5.4. Missing Python Shared Library (`libpython`)

*   **Problem:** On the Raspberry Pi, the bundled application failed with a `Failed to load Python shared library` error.
*   **Root Cause:** This appears to be a bug or limitation in PyInstaller where it fails to correctly locate and package the necessary `libpython.so` file on certain Linux distributions or architectures.
*   **Solution (Workaround):** The user discovered a workaround. The `backend/build-backend.spec` file was modified to manually include the specific path to the `libpython3.11.so.1.0` file in the `datas` section, ensuring it gets included in the final package.

### 5.5. Blank Window on Launch

*   **Problem:** The application would launch, but the window would be completely blank.
*   **Root Cause:** The application was using `BrowserRouter` from `react-router-dom`. This component relies on the browser's History API, which does not function correctly when the application is loaded from the local filesystem (`file://...`) as it is in Electron.
*   **Solution:** `BrowserRouter` was replaced with `HashRouter` in `frontend/src/main.tsx`. `HashRouter` uses the URL hash (`#`) for routing and works correctly in a file-based environment.

### 5.6. Backend Configuration (Database and Cache)

*   **Problem:** The packaged application was still trying to connect to the PostgreSQL database and Redis cache, causing it to crash on startup.
*   **Root Cause:** This was a subtle and complex issue related to Python's import-time vs. run-time behavior. The database connection was being initialized by SQLAlchemy the moment its module was imported, which was *before* the application's main logic had a chance to change the configuration settings for desktop mode.
*   **Solution:** The final fix was to modify the `backend/run_cli.py` script. When `DEPLOYMENT_MODE` is `desktop`, the script now forcefully re-initializes the database engine and session with the correct SQLite settings *after* the initial imports are complete but *before* the web server is started. This ensures the application uses the correct database and cache for the desktop environment.
*   **Secondary Cause (Hypothesis):** It is also suspected that PyInstaller was using a cached version of the backend code, which prevented several attempted fixes from being applied. The build scripts were updated to delete the `backend/build` directory to prevent this from happening in the future.

### 5.7. Asset Seeding Race Condition

*   **Problem:** On the very first launch of the native application on a new machine, the application would crash. The logs revealed a `sqlite3.OperationalError: no such table: assets`.
*   **Root Cause:** The application's first-run logic in `run_cli.py` was attempting to seed the asset master data immediately after creating the database file. However, the `seed_assets_command` was being called before the database schema (i.e., the `assets` table and others) had been created by the `create_all` call. This created a race condition where the seeder would try to write to a table that didn't exist yet.
*   **Solution:** The startup logic in `run_cli.py` was modified to be more robust. It now ensures that the database tables are created using `create_all` on the first run. It also now calls the `seed_assets_command` on *every* application launch, ensuring the asset data is always up-to-date, which mirrors the production server's behavior.

This plan provides a robust and standard way to convert a web application into a cross-platform desktop application.
