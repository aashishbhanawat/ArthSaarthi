# Building ArthSaarthi from Source

This guide provides instructions for building the native desktop installers for ArthSaarthi on different platforms.

## Prerequisites

- Python 3.10+ and `pip`
- Node.js 18+ and `npm`

### Platform-Specific Prerequisites

- **Linux**:
  - A C compiler and Python development headers might be needed for some dependencies. On Debian/Ubuntu, you can install them with: `sudo apt-get install build-essential python3-dev`
- **Windows**:
  - A C++ compiler might be needed. The "Desktop development with C++" workload from the Visual Studio Installer is recommended.
- **macOS**:
  - Xcode Command Line Tools are required. You can install them by running `xcode-select --install`.

## Build Process

The build process is orchestrated by platform-specific scripts located in the `scripts/` directory. There is also a main `build.sh` script that attempts to detect your operating system and run the appropriate script.

### Using the Main Build Script

To build the application, you can run the following command from the root of the project:

```bash
./scripts/build.sh
```

This script will detect your OS and execute the corresponding build script (`build-linux.sh`, `build-windows.sh`, or `build-macos.sh`).

### Using Platform-Specific Scripts

Alternatively, you can run the platform-specific scripts directly. This is useful if the main build script fails to detect your OS correctly or if you want more control over the build process.

- **For Linux:**
  ```bash
  ./scripts/build-linux.sh
  ```
- **For Windows:**
  ```bash
  ./scripts/build-windows.sh
  ```
- **For macOS:**
  ```bash
  ./scripts/build-macos.sh
  ```

### Cross-Compiling

It is possible to build installers for different platforms from a single host machine, but it requires additional setup:

- **Building for Windows on Linux/macOS**: Requires `wine` to be installed and configured.
- **Building for macOS on Linux/Windows**: This is more complex and requires a macOS runner or a virtual machine. It is not officially supported by this project at the moment.

### Build Outputs

After a successful build, the installers can be found in the `frontend/dist-electron/` directory.

-   **On Windows:** You will find a `.exe` installer.
-   **On macOS:** You will find a `.dmg` file.
-   **On Linux:** You will find an `.AppImage` file and a `.deb` package.
