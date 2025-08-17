# Building the Application

This document provides instructions for setting up the build environment on different operating systems.

## Prerequisites

The following tools are required to build the native desktop application:

- **Node.js and npm:** For frontend dependencies and building the Electron app.
- **Python:** For the backend and PyInstaller.
- **A bash-like shell:** To run the build script (`.sh`).

## Windows

1.  **Node.js (which includes npm):**
    *   Go to the official Node.js website: [https://nodejs.org/en/download/](https://nodejs.org/en/download/)
    *   Download and run the Windows Installer (`.msi`).

2.  **Python:**
    *   Go to the official Python website: [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
    *   Download and run the installer.
    *   **Important:** On the first page of the installer, make sure to check the box that says **"Add Python to PATH"**.

3.  **Git for Windows (provides Git Bash):**
    *   The build script is a shell script (`.sh`), so you need a bash-like environment to run it on Windows. The easiest way is to install Git for Windows, which includes "Git Bash".
    *   Go to [https://git-scm.com/download/win](https://git-scm.com/download/win) and download the installer.
    *   When installing, you can accept the default options.

4.  **Install Python Packages:**
    *   After the steps above are complete, open **Git Bash** (not Command Prompt or PowerShell).
    *   Run the following command to install PyInstaller and other necessary Python packages:
        ```bash
        pip install -r backend/requirements.in
        pip install -r backend/requirements-dev.in
        ```

## macOS

1.  **Homebrew:**
    *   If you don't have it, Homebrew is the easiest way to install development tools on macOS. Open your **Terminal** and run the command found on the Homebrew homepage: [https://brew.sh/](https://brew.sh/)

2.  **Node.js and Python:**
    *   Open your **Terminal** and run the following commands to install the latest versions:
        ```bash
        brew install node
        brew install python
        ```

3.  **Install Python Packages:**
    *   Open your **Terminal** and run the following command to install PyInstaller and other necessary Python packages:
        ```bash
        pip3 install -r backend/requirements.in
        pip3 install -r backend/requirements-dev.in
        ```

## Building

After installing the prerequisites, you can build the native application by running the following command from the project root:

```bash
./scripts/build-desktop.sh
```

The installer will be located in the `frontend/release` directory.
