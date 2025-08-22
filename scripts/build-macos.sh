#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Print each command before executing it
set -x

echo "--- Starting macOS Build ---"

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
(cd backend && "$VIRTUAL_ENV/bin/pip" install -r requirements.txt)
(cd backend && "$VIRTUAL_ENV/bin/pip" install PyInstaller)

# 4. Bundle Backend
echo "Step 4: Bundling backend..."
(cd backend && "$VIRTUAL_ENV/bin/python" -m PyInstaller build-backend.spec)

# 5. Set Execute Permissions
echo "Step 5: Setting execute permissions on backend..."
chmod +x "$(pwd)/backend/dist/arthsaarthi-backend/arthsaarthi-backend"

# 6. Package Electron App for macOS
echo "Step 6: Packaging Electron app for macOS..."
(cd frontend && npm run dist -- --mac)

echo "--- macOS Build Finished ---"
echo "Installer located in frontend/dist-electron/"
