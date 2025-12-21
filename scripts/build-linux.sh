#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Print each command before executing it
set -x

echo "--- Starting Linux Build ---"

# Create a clean virtual environment
echo "Creating a clean virtual environment..."
rm -rf ~/venc
python3 -m venv ~/venc

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
source ~/venc/bin/activate
(cd backend && "$VIRTUAL_ENV/bin/pip" install pyinstaller==6.17.0)

(cd backend && "$VIRTUAL_ENV/bin/pip" install -r requirements.txt)

# 4. Bundle Backend
echo "Step 4: Bundling backend..."
(cd backend && "$VIRTUAL_ENV/bin/python" -m PyInstaller build-backend.spec)

# 5. Set Execute Permissions
echo "Step 5: Setting execute permissions on backend..."
chmod +x "$(pwd)/backend/dist/arthsaarthi-backend/arthsaarthi-backend"

# 6. Package Electron App for Linux
echo "Step 6: Packaging Electron app for Linux..."
# We use the 'dist' script from package.json which runs electron-builder
# We set USE_SYSTEM_FPM=true to work around an issue with the pre-built fpm on ARM
(cd frontend && USE_SYSTEM_FPM=true npm run dist -- --linux)

echo "--- Linux Build Finished ---"
echo "Installer located in frontend/dist-electron/"
