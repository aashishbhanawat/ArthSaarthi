#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Print each command before executing it
set -x

echo "--- Starting Android Build ---"
echo ""
echo "Prerequisites:"
echo "  1. Android SDK installed (API level 34+)"
echo "  2. Android NDK installed"
echo "  3. ANDROID_HOME environment variable set"
echo "  4. Node.js 18+ and npm"
echo "  5. Python 3.10+ (for backend source)"
echo ""

# Verify Android SDK is available
if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    echo "ERROR: ANDROID_HOME or ANDROID_SDK_ROOT not set."
    echo "Please install Android Studio and set ANDROID_HOME to your SDK path."
    echo "Example: export ANDROID_HOME=\$HOME/Android/Sdk"
    exit 1
fi

ANDROID_SDK="${ANDROID_HOME:-$ANDROID_SDK_ROOT}"
echo "Using Android SDK at: $ANDROID_SDK"

# Clean up previous builds
echo "Step 0: Cleaning previous builds..."
rm -rf frontend/dist

# 1. Install Frontend Dependencies (including Capacitor)
echo "Step 1: Installing frontend dependencies..."
(cd frontend && npm install)

# 2. Build Frontend (Vite production build)
echo "Step 2: Building frontend..."
(cd frontend && npm run build)

# 3. Sync Capacitor (copies dist/ to android assets)
echo "Step 3: Syncing Capacitor..."
(cd frontend && npx cap sync android)

# 4. Copy Backend Python source to android project
echo "Step 4: Copying backend Python source..."
ANDROID_PYTHON_DIR="frontend/android/app/src/main/python"
mkdir -p "$ANDROID_PYTHON_DIR"

# Copy the backend app module (the core Python code)
cp -r backend/app "$ANDROID_PYTHON_DIR/"
# Copy alembic config (needed for DB initialization)
cp -r backend/alembic "$ANDROID_PYTHON_DIR/"
cp backend/alembic.ini "$ANDROID_PYTHON_DIR/"

# Ensure the run_server.py entry point exists
if [ ! -f "$ANDROID_PYTHON_DIR/run_server.py" ]; then
    echo "ERROR: run_server.py not found in $ANDROID_PYTHON_DIR"
    echo "This file should have been created during project setup."
    exit 1
fi

echo "Backend Python source copied to $ANDROID_PYTHON_DIR"

# 5. Build Android APK
echo "Step 5: Building Android APK..."
echo ""
echo "Choose build type:"
echo "  debug   — Unsigned debug APK (for testing)"
echo "  release — Release APK (requires signing)"
echo ""

BUILD_TYPE="${1:-debug}"

if [ "$BUILD_TYPE" = "release" ]; then
    echo "Building release APK..."
    (cd frontend/android && ./gradlew assembleRelease)
    APK_PATH="frontend/android/app/build/outputs/apk/release/app-release.apk"
else
    echo "Building debug APK..."
    (cd frontend/android && ./gradlew assembleDebug)
    APK_PATH="frontend/android/app/build/outputs/apk/debug/app-debug.apk"
fi

# 6. Report build output
echo ""
echo "--- Android Build Finished ---"
if [ -f "$APK_PATH" ]; then
    echo "APK located at: $APK_PATH"
    echo ""
    echo "To install on a connected device:"
    echo "  adb install $APK_PATH"
else
    echo "APK file not found at expected location: $APK_PATH"
    echo "Check the Gradle output above for errors."
    exit 1
fi
