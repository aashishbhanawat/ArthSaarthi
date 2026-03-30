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

### Building for Android (Experimental)

The Android build uses **Capacitor.js** (wraps the React frontend into a WebView) and **Chaquopy** (embeds the Python/FastAPI backend on the device). This is experimental.

#### Android Prerequisites

- **Android Studio** with Android SDK (API level 34+)
- **Android NDK** (installed via Android Studio SDK Manager)
- Set `ANDROID_HOME` environment variable:
  ```bash
  export ANDROID_HOME=$HOME/Android/Sdk
  ```
- Node.js 18+ and npm

#### Android Build Steps

```bash
# Using the main build script with --android flag:
./scripts/build.sh --android          # debug APK
./scripts/build.sh --android release  # release APK

# Or directly:
./scripts/build-android.sh            # debug APK
./scripts/build-android.sh release    # release APK
```

#### Android Build Output

After a successful build, the APK can be found at:
- **Debug:** `frontend/android/app/build/outputs/apk/debug/ArthSaarti-debug.apk`
- **Release:** `frontend/android/app/build/outputs/apk/release/ArthSaarti-release.apk`

Install on a connected device:
```bash
adb install frontend/android/app/build/outputs/apk/debug/ArthSaarti-debug.apk
```

#### Android Known Limitations

- **APK size** is large (~100-200 MB) due to the bundled Python interpreter and dependencies.
- **First-run startup** is slower as Chaquopy extracts Python on first launch.
- **PDF import** may not work on Android (some C-extension packages lack Android wheels).
- This is an **experimental** build target — not production-ready.

### Build Outputs

After a successful build, the installers can be found in the `frontend/dist-electron/` directory.

-   **On Windows:** You will find a `.exe` installer.
-   **On macOS:** You will find a `.dmg` file.
-   **On Linux:** You will find an `.AppImage` file and a `.deb` package.
-   **On Android:** See the Android section above for APK location.

