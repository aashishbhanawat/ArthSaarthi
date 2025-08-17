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

This plan provides a robust and standard way to convert a web application into a cross-platform desktop application.
