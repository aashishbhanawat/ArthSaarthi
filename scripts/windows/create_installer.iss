; Inno Setup Script for Personal Portfolio Management System
; This script requires Inno Setup to be installed on the build machine.
; It should be run after the `pms_app.exe` has been built by `build_packaged_app.sh` on Windows.

[Setup]
; Unique AppId for this application
AppId={{F4B6F6A0-9F8E-4B8A-B8E3-1B0A3F2A9F1C}
AppName=Personal Portfolio Management System
AppVersion=1.0.0
AppPublisher=Your Name/Company
DefaultDirName={autopf}\Personal Portfolio Management System
DefaultGroupName=Personal Portfolio Management System
AllowNoIcons=yes
OutputDir=.\installers
OutputBaseFilename=pms_setup
SetupIconFile=path\to\your\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; This assumes the script is run from the project root, and the executable is in 'backend/dist/'.
Source: "backend\dist\pms_app.exe"; DestDir: "{app}"; Flags: ignoreversion
; TODO: Add other necessary files here if any (e.g., README, license file)
; Source: "docs\user_guide.md"; DestDir: "{app}";

[Icons]
Name: "{group}\Personal Portfolio Management System"; Filename: "{app}\pms_app.exe"
Name: "{group}\{cm:ProgramOnTheWeb,Your Website}"; Filename: "https://your.website.com"
Name: "{autodesktop}\Personal Portfolio Management System"; Filename: "{app}\pms_app.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\pms_app.exe"; Description: "{cm:LaunchProgram,Personal Portfolio Management System}"; Flags: nowait postinstall skipifsilent
