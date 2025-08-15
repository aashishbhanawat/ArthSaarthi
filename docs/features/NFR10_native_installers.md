# Feature: Native Executable Installers (NFR10)

## 1. Objective

To package the ArthSaarthi application as a single, one-click executable/installer for Windows, macOS, and Linux. This will provide a native desktop experience and eliminate the need for end-users to have Docker or a Python/Node.js environment.

## 2. Technology Stack

*   **Electron:** Used to create the main application window, manage the application lifecycle, and orchestrate the backend process.
*   **PyInstaller:** Used to bundle the entire Python/FastAPI backend, including the Python interpreter and all dependencies, into a single, self-contained executable.
*   **Electron Builder:** Used to package the Electron app, the React frontend assets, and the bundled Python backend into distributable installers (`.exe`, `.dmg`, etc.).

## 3. High-Level Architecture

The final application consists of three main parts working in concert:

1.  **Electron Main Process (`electron/main.js`):**
    *   This is the application's entry point.
    *   On app start, it uses `portfinder` to find a free network port.
    *   It then launches the bundled Python backend executable as a child process, passing the selected port as a command-line argument.
    *   It creates a `BrowserWindow` and loads the production-built frontend (`frontend/dist/index.html`).
    *   The frontend's base URL for API calls is dynamically configured to `http://localhost:<port>`.
    *   On app quit, it gracefully terminates the backend child process.

2.  **Backend Packaging (PyInstaller):**
    *   A PyInstaller build script (`backend/build-backend.spec`) defines the bundling process.
    *   It bundles the Python interpreter and all dependencies.
    *   The entry point is a small Python script (`backend/run_pyinstaller.py`) that starts the Uvicorn server for our FastAPI app, configured to read the port from command-line arguments.
    *   The backend is pre-configured to use `DATABASE_TYPE=sqlite` and `CACHE_TYPE=disk`.
    *   This process produces a single backend executable.

*   **Conditional Feature Disabling:**
    *   To ensure a true single-user experience, multi-user features are disabled when the application runs in this mode (`DATABASE_TYPE=sqlite` and `ENVIRONMENT=production`).
    *   **Backend:** The API endpoints for user management (`/api/v1/users/`) are not registered by the FastAPI application.
    *   **Frontend:** The UI for user management (the "User Management" link in the navigation) is hidden, controlled by a `deployment_mode` flag sent from the backend.

3.  **Frontend & Final Packaging (Electron Builder):**
    *   The `electron-builder` configuration is added to `frontend/package.json`.
    *   It's configured to include the frontend build output (`dist/`) and the backend executable as an "extra resource".

## 4. Build Process

A new build script `scripts/build-desktop.sh` orchestrates the entire process:
1.  The backend is bundled into an executable using PyInstaller.
2.  The frontend is built using Vite.
3.  The backend executable is copied into the frontend's build output.
4.  Electron Builder packages everything into a distributable installer.
