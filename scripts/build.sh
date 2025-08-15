#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Frontend Build ---
echo "Building frontend assets..."
# The `build` script in frontend/package.json runs `tsc && vite build`
(cd frontend && npm install && npm run build)
echo "Frontend build complete. Output is in frontend/dist/"

# --- Backend Build ---
echo "Building backend executable with PyInstaller..."
# The spec file is configured to place the output in backend/dist/
# We need to ensure dependencies are installed first.
pip install -r backend/requirements.txt
(cd backend && pyinstaller build-backend.spec)
echo "Backend build complete. Output is in backend/dist/"

# --- Application Packaging ---
echo "Packaging cross-platform application with Electron Builder..."
# The `dist` script in frontend/package.json runs `electron-builder`
# It will pick up the configuration from the `build` section in package.json
(cd frontend && npm run dist)
echo "Application packaging complete. Installers are in frontend/dist-electron/"

echo "Build process finished successfully."
