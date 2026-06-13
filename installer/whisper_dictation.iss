; Inno Setup 6 script for Whisper Dictation
; Run from the repo root: iscc installer\whisper_dictation.iss
; version.txt must exist in the repo root (created by CI from the git tag).

#define VerFile FileOpen("version.txt")
#define AppVersion FileRead(VerFile)
#expr FileClose(VerFile)

#define AppName "Whisper Dictation"
#define AppPublisher "DramisInfo"
#define AppExeName "whisper-dictation.exe"

[Setup]
AppId={{C7E2A1D4-3F8B-4E90-BCA2-1D456789ABCD}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/DramisInfo/whisper-dictation
AppSupportURL=https://github.com/DramisInfo/whisper-dictation/issues
AppUpdatesURL=https://github.com/DramisInfo/whisper-dictation/releases
DefaultDirName={autopf}\WhisperDictation
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=installer\output
OutputBaseFilename=WhisperDictation-Setup-{#AppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=auto
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\whisper-dictation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\{#AppExeName}"; Parameters: "--unregister-autostart"; Flags: nowait
