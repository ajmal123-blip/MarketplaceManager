#define MyAppName "FBauto Bot 33"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "FBauto Bot 33"
#define MyAppExeName "FBauto Bot 33.exe"

[Setup]
AppId={{FBauto-Bot-33-0.1.0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FBauto Bot 33
DefaultGroupName=FBauto Bot 33
OutputDir=installer
OutputBaseFilename=FBauto_Bot_33_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
Uninstallable=yes
WizardStyle=modern

[Files]
Source: "dist\FBauto Bot 33\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FBauto Bot 33"; Filename: "{app}\FBauto Bot 33.exe"
Name: "{autodesktop}\FBauto Bot 33"; Filename: "{app}\FBauto Bot 33.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\FBauto Bot 33.exe"; Description: "Launch FBauto Bot 33"; Flags: nowait postinstall skipifsilent