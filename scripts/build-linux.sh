#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Starting Linux Build ---"

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf backend/dist frontend/dist-electron

# 1. Install Frontend Dependencies
echo "Step 1: Installing frontend dependencies..."
(cd frontend && npm install)

# 2. Build Frontend
echo "Step 2: Building frontend..."
(cd frontend && npm run build)

# 3. Install Backend Dependencies
echo "Step 3: Installing backend dependencies..."
source ~/venc/bin/activate
(cd backend && pip install -r requirements.txt)

# 4. Bundle Backend
echo "Step 4: Bundling backend..."
(cd backend && pyinstaller build-backend.spec)

# 5. Set Execute Permissions
echo "Step 5: Setting execute permissions on backend..."
chmod +x backend/dist/arthsaarthi-backend/arthsaarthi-backend

# 6. Package Electron App for Linux
echo "Step 6: Packaging Electron app for Linux..."
# We use the 'dist' script from package.json which runs electron-builder
(cd frontend && USE_SYSTEM_FPM=true npm run dist -- --linux)

echo "--- Linux Build Finished ---"
echo "Installer located in frontend/dist-electron/"
