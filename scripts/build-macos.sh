#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Print each command before executing it
set -x

echo "--- Starting macOS Build ---"

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
# This assumes a virtual environment is active.
# In a CI/CD environment, this should be handled by the setup steps.
(cd backend && pip install -r requirements.txt)

# 4. Bundle Backend
echo "Step 4: Bundling backend..."
(cd backend && pyinstaller build-backend.spec)

# 5. Set Execute Permissions
echo "Step 5: Setting execute permissions on backend..."
chmod +x "$(pwd)/backend/dist/arthsaarthi-backend/arthsaarthi-backend"

# 6. Package Electron App for macOS
echo "Step 6: Packaging Electron app for macOS..."
# We use the 'dist' script from package.json which runs electron-builder
(cd frontend && npm run dist -- --mac)

echo "--- macOS Build Finished ---"
echo "Installer located in frontend/dist-electron/"
