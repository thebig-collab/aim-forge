#define MyAppName "AimForge"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "AimForge"
[Setup]
AppId={{F2E63B19-6C0B-4E72-A9F7-8B7C1C0E1A20}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\AimForge
DefaultGroupName=AimForge
OutputDir=installer
OutputBaseFilename=AimForge_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Files]
Source: "dist\AimForge.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\AimForge"; Filename: "{app}\AimForge.exe"
Name: "{autodesktop}\AimForge"; Filename: "{app}\AimForge.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
