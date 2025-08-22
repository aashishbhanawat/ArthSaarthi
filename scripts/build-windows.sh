#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Print each command before executing it
set -x

echo "--- Starting Windows Build ---"

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf backend/dist backend/build frontend/dist-electron

# 1. Install Frontend Dependencies
echo "Step 1: Installing frontend dependencies..."
(cd frontend && npm install)

# 2. Build Frontend
echo "Step 2: Building frontend..."
(cd frontend && npm run build)

# 3. Install Backend Dependencies
echo "Step 3: Installing backend dependencies..."
# This assumes the user has a virtual environment named 'venc' in their home directory
# In a more robust setup, this would be handled by a configuration file or a setup script.
source ~/venc/bin/activate
(cd backend && pip install -r requirements-windows.txt)

# 4. Bundle Backend
echo "Step 4: Bundling backend..."
(cd backend && python -m pyinstaller build-backend.spec)

# 5. Package Electron App for Windows
echo "Step 5: Packaging Electron app for Windows..."
# We use the 'dist' script from package.json which runs electron-builder
(cd frontend && npm run dist -- --win)

echo "--- Windows Build Finished ---"
echo "Installer located in frontend/dist-electron/"
