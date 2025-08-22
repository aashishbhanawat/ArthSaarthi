#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Main Build Script ---"

# Detect the operating system
OS="$(uname -s)"
case "$OS" in
    Linux*)     ./scripts/build-linux.sh;;
    MINGW*)     ./scripts/build-windows.sh;;
    CYGWIN*)    ./scripts/build-windows.sh;;
    Darwin*)    ./scripts/build-macos.sh;;
    *)          echo "Unsupported OS: $OS"; exit 1;;
esac

echo "--- Main Build Script Finished ---"
