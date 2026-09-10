#define AppVersion "0.1.0"

[Setup]
AppId={{764FD56A-0E5A-45CD-87FD-FD6E13FDEDC2}
AppName=PalmCue
AppVersion={#AppVersion}
AppPublisher=PalmCue
AppPublisherURL=https://github.com/jad-fahmi/palmcue
DefaultDirName={localappdata}\Programs\PalmCue
DefaultGroupName=PalmCue
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=PalmCue-Setup-{#AppVersion}-windows-x64
SetupIconFile=..\build\palmcue.ico
UninstallDisplayIcon={app}\PalmCue.exe
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\PalmCue\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PalmCue"; Filename: "{app}\PalmCue.exe"
Name: "{autodesktop}\PalmCue"; Filename: "{app}\PalmCue.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PalmCue.exe"; Description: "Launch PalmCue"; Flags: nowait postinstall skipifsilent
