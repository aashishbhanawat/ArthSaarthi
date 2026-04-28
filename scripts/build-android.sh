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
echo "  4. Node.js 20+ and npm (required by Vite 7.x and Capacitor CLI)"
echo "  5. Python 3.13 (for backend source, with Rust support)"
echo ""

# Verify Node.js version
NODE_MAJOR=$(node -v 2>/dev/null | sed 's/v\([0-9]*\).*/\1/')
if [ -z "$NODE_MAJOR" ] || [ "$NODE_MAJOR" -lt 20 ]; then
    echo "ERROR: Node.js 20+ required. Found $(node -v). Please install/upgrade Node.js."
    exit 1
fi

# Smarter ANDROID_HOME detection
if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    for path in "$HOME/android-sdk" "$HOME/Android/Sdk" "/home/homeserver/android-sdk" "/usr/lib/android-sdk"; do
        if [ -d "$path" ]; then
            export ANDROID_HOME="$path"
            echo "Auto-detected ANDROID_HOME at: $ANDROID_HOME"
            break
        fi
    done
fi

if [ -z "$ANDROID_HOME" ]; then
    echo "ERROR: ANDROID_HOME not set. If using sudo, try: sudo -E bash ./scripts/build-android.sh"
    exit 1
fi

# Ensure Python 3.13 is available for Chaquopy build
BUILD_TOOLS_DIR="frontend/android/build-tools"
PYTHON_313_DIR="$BUILD_TOOLS_DIR/python3.13"
PYTHON_BIN="$PYTHON_313_DIR/bin/python3"

if ! command -v python3.13 > /dev/null 2>&1 && [ ! -f "$PYTHON_BIN" ]; then
    echo "Step 0: Setting up portable Python 3.13..."
    mkdir -p "$BUILD_TOOLS_DIR"
    TARBALL="cpython-3.13.12+20260320-aarch64-unknown-linux-gnu-install_only.tar.gz"
    URL="https://github.com/astral-sh/python-build-standalone/releases/download/20260320/$TARBALL"

    if [ ! -f "$BUILD_TOOLS_DIR/$TARBALL" ]; then
        curl -L "$URL" -o "$BUILD_TOOLS_DIR/$TARBALL"
    fi
    mkdir -p "$PYTHON_313_DIR"
    tar -xf "$BUILD_TOOLS_DIR/$TARBALL" -C "$PYTHON_313_DIR" --strip-components=1
fi

# Determine which Python to use for build-time tasks
if command -v python3.13 > /dev/null 2>&1; then
    PYTHON_BUILD_CMD="python3.13"
else
    # Use absolute path for our portable python
    PYTHON_BUILD_CMD=$(readlink -f "$PYTHON_BIN")
fi
echo "Using build-time Python: $PYTHON_BUILD_CMD"

# Step 0.5: Download pydantic-core wheel (AArch64)
WHEELS_DIR="frontend/android/app/libs/python-wheels"
mkdir -p "$WHEELS_DIR"

# Clean up any broken/small wheels from previous attempts
find "$WHEELS_DIR" -name "pydantic_core*" -size -100k -delete

ANDROID_WHEEL="pydantic_core-2.23.4-cp313-cp313-android_26_aarch64.whl"
if [ ! -f "$WHEELS_DIR/$ANDROID_WHEEL" ]; then
    echo "Step 0.5: Downloading pydantic-core wheel via pip..."
    # Use the portable python to download the correct wheel from PyPI
    "$PYTHON_BUILD_CMD" -m pip download pydantic-core==2.23.4 \
        --only-binary :all: \
        --platform manylinux_2_17_aarch64 \
        --dest "$WHEELS_DIR"

    # Patch wheel for Android compatibility
    ORIGINAL_WHEEL=$(ls "$WHEELS_DIR"/pydantic_core-2.23.4-cp313-cp313-manylinux*.whl | head -n 1)
    if [ -f "$ORIGINAL_WHEEL" ]; then
        echo "Patching wheel for Android..."
        ANDROID_WHEEL_TAG="cp313-cp313-android_26_aarch64"
        "$PYTHON_BUILD_CMD" scripts/patch_wheel.py "$ORIGINAL_WHEEL" "$WHEELS_DIR/$ANDROID_WHEEL" "$ANDROID_WHEEL_TAG"
        rm "$ORIGINAL_WHEEL"
        echo "Patched wheel created at: $WHEELS_DIR/$ANDROID_WHEEL"
    fi
fi

# Clean up previous builds
echo "Step 1: Cleaning previous builds..."
rm -rf frontend/dist

# 2. Install Frontend Dependencies
echo "Step 2: Installing frontend dependencies..."
(cd frontend && npm install)

# 3. Build Frontend
echo "Step 3: Building frontend..."
(cd frontend && npm run build)

# 4. Sync Capacitor
echo "Step 4: Syncing Capacitor..."
(cd frontend && npx cap sync android)

# 5. Copy Backend Python source
echo "Step 5: Copying backend Python source..."
ANDROID_PYTHON_DIR="frontend/android/app/src/main/python"
mkdir -p "$ANDROID_PYTHON_DIR"
cp -r backend/app "$ANDROID_PYTHON_DIR/"
cp -r backend/alembic "$ANDROID_PYTHON_DIR/"
cp backend/alembic.ini "$ANDROID_PYTHON_DIR/"

# 6. Generate Gradle wrapper if missing
if [ ! -f "frontend/android/gradlew" ]; then
    echo "Step 6: Generating Gradle wrapper..."
    GRADLE_BIN=""
    if command -v gradle > /dev/null 2>&1; then GRADLE_BIN="gradle"
    else
        for path in "/usr/bin/gradle" "/usr/local/bin/gradle"; do
            if [ -x "$path" ]; then GRADLE_BIN="$path"; break; fi
        done
    fi
    if [ -z "$GRADLE_BIN" ]; then echo "ERROR: gradle not found"; exit 1; fi
    (cd frontend/android && "$GRADLE_BIN" wrapper --gradle-version 8.9)
    chmod +x frontend/android/gradlew
fi

# 7. Build Android APK
echo "Step 7: Building Android APK..."
(cd frontend/android && ./gradlew assembleDebug -PbuildPython="$PYTHON_BUILD_CMD")

APK_PATH="frontend/android/app/build/outputs/apk/debug/ArthSaarti-debug.apk"
echo ""
echo "--- Android Build Finished ---"
if [ -f "$APK_PATH" ]; then
    echo "APK located at: $APK_PATH"
else
    echo "APK file not found at expected location: $APK_PATH"
    exit 1
fi
