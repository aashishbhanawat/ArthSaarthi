#!/bin/bash

# This script creates a distributable .dmg file for the macOS application.
# It should be run after `build_packaged_app.sh` has been executed on a macOS machine.

# --- Configuration ---
APP_NAME="pms_app"
APP_BUNDLE="$APP_NAME.app"
DMG_NAME="Personal_Portfolio_Management_System.dmg"
VOL_NAME="Personal Portfolio Management System"
SOURCE_DIR="backend/dist"
TEMP_DMG="temp_${DMG_NAME}"
FINAL_DMG_PATH="installers/${DMG_NAME}"

# --- Helper Functions ---
function print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

function print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
    exit 1
}

# --- Main Process ---
print_info "Starting DMG creation process..."

# Check if the .app bundle exists
if [ ! -d "$SOURCE_DIR/$APP_BUNDLE" ]; then
    print_error "Application bundle not found at $SOURCE_DIR/$APP_BUNDLE"
    print_error "Please run the build_packaged_app.sh script first on a Mac."
    exit 1
fi

# Create installers directory if it doesn't exist
mkdir -p installers

# Create a temporary read-write disk image
print_info "Creating temporary disk image..."
hdiutil create -srcfolder "$SOURCE_DIR/$APP_BUNDLE" -volname "$VOL_NAME" -fs HFS+ -format UDRW "$TEMP_DMG"

# Mount the temporary image
print_info "Mounting temporary disk image..."
MOUNT_DIR=$(hdiutil attach "$TEMP_DMG" -noverify -nobrowse -mountpoint "/Volumes/$VOL_NAME" | awk '/\/Volumes\// {print $3}')

# Create a symbolic link to the Applications folder
print_info "Adding symbolic link to /Applications..."
ln -s /Applications "$MOUNT_DIR/Applications"

# Unmount the disk image
print_info "Unmounting disk image..."
hdiutil detach "$MOUNT_DIR"

# Convert the temporary image to a compressed, read-only final image
print_info "Converting to compressed, read-only DMG..."
hdiutil convert "$TEMP_DMG" -format UDZO -o "$FINAL_DMG_PATH"

# Clean up temporary file
rm "$TEMP_DMG"

print_info "DMG creation complete: $FINAL_DMG_PATH"
