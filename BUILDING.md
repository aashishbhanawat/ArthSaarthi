# Building ArthSaarthi from Source

This guide provides instructions for building the native desktop installers for ArthSaarthi on different platforms.

## Prerequisites

- Python 3.10+ and `pip`
- Node.js 18+ and `npm`
- (For Linux) A C compiler and Python development headers might be needed for some dependencies, though the goal is to minimize this. `sudo apt-get install build-essential python3-dev`
- (For Windows) A C++ compiler might be needed. The "Desktop development with C++" workload from the Visual Studio Installer is recommended.

## Build Process

The entire build process is orchestrated by a single script. This script will handle all steps, including installing dependencies, building the frontend, bundling the backend, and packaging the final application.

To build the application, run the following command from the root of the project:

```bash
./scripts/build.sh
```

### What the Build Script Does

1.  **Installs Frontend Dependencies:** Runs `npm install` in the `frontend/` directory.
2.  **Builds Frontend Assets:** Runs `npm run build` to compile the React/TypeScript frontend into static HTML, CSS, and JavaScript files located in `frontend/dist/`.
3.  **Installs Backend Dependencies:** Runs `pip install -r backend/requirements.txt` to install all Python dependencies.
4.  **Bundles Backend Executable:** Runs `pyinstaller` in the `backend/` directory using the `build-backend.spec` file. This creates a self-contained executable of the Python backend, located in `backend/dist/`.
5.  **Packages the Electron Application:** Runs `electron-builder` in the `frontend/` directory. This is the final step that takes the Electron shell, the built frontend assets, and the backend executable, and packages them into a distributable installer for your current operating system.

### Build Outputs

After the script finishes successfully, the installers can be found in the `frontend/dist-electron/` directory.

-   **On Windows:** You will find a `.exe` installer.
-   **On macOS:** You will find a `.dmg` file.
-   **On Linux:** You will find an `.AppImage` file or a `.deb`/`.rpm` package, depending on the `electron-builder` configuration.
