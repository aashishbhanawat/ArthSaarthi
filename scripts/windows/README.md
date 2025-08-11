# Building the Windows Installer

This directory contains the necessary script to create a Windows `.exe` installer for the Personal Portfolio Management System.

## Prerequisites

1.  A **Windows build machine**.
2.  **Node.js** and **Python** installed on the machine.
3.  **Inno Setup** installed. You can download it from [jrsoftware.org](https://www.jrsoftware.org/isinfo.php).

## Build Steps

The build process is two steps:

### Step 1: Build the Core Application Executable

First, you need to build the standalone `pms_app.exe` file. This is done by running the main build script from the root of the project.

Open a command prompt or PowerShell window in the project's root directory and run:
```bash
./scripts/build_packaged_app.sh
```
This script will:
1.  Build the frontend assets.
2.  Run PyInstaller to package the backend and frontend together.
3.  The final executable will be located at `backend/dist/pms_app.exe`.

### Step 2: Compile the Installer

After the `pms_app.exe` has been created, you can build the final setup file.

1.  **Launch Inno Setup.**
2.  Open the script file `create_installer.iss` from this directory.
3.  You may need to update the `SetupIconFile` path in the script if you have a custom icon.
4.  From the Inno Setup menu, select **Build -> Compile**.

Alternatively, you can run the Inno Setup command-line compiler (`iscc.exe`) on the script:
```
iscc.exe create_installer.iss
```

The final installer, `pms_setup.exe`, will be created in the `scripts/windows/installers/` directory.
