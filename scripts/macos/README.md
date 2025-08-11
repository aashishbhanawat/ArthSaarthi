# Building the macOS Installer (DMG)

This directory contains the necessary script to create a macOS Disk Image (`.dmg`) file for the Personal Portfolio Management System.

## Prerequisites

1.  A **macOS build machine**.
2.  **Node.js** and **Python** installed on the machine (can be installed with Homebrew).

## Build Steps

The build process is two steps:

### Step 1: Build the Core Application Bundle

First, you need to build the standalone `pms_app.app` bundle. This is done by running the main build script from the root of the project.

Open a Terminal window in the project's root directory and run:
```bash
./scripts/build_packaged_app.sh
```
This script will:
1.  Build the frontend assets.
2.  Run PyInstaller to package the backend and frontend together.
3.  The final application bundle will be located at `backend/dist/pms_app.app`.

### Step 2: Create the DMG

After the `pms_app.app` bundle has been created, you can create the final disk image.

From the project's root directory, run the `create_dmg.sh` script:
```bash
./scripts/macos/create_dmg.sh
```

This script will:
1.  Create a temporary disk image.
2.  Copy the `pms_app.app` bundle into it.
3.  Add a symbolic link to the `/Applications` folder to encourage a drag-and-drop installation.
4.  Convert the image to a compressed, read-only format.

The final installer, `Personal_Portfolio_Management_System.dmg`, will be created in the `installers/` directory at the root of the project.
