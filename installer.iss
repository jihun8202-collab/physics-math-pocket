#define MyAppName "Physics + Math Pocket"
#ifndef MyAppVersion
  #define MyAppVersion "3.5.5.5"
#endif
#ifndef MyAppBuild
  #define MyAppBuild "35505"
#endif
#ifndef MyAppChannel
  #define MyAppChannel "Beta"
#endif
#define MyAppPublisher "Physics + Math Pocket Project"
#define MyAppExeName "PhysicsMathPocket.exe"
#define MyAppCopyright "Copyright © 2026 Physics + Math Pocket Project"

[Setup]
; IMPORTANT: Keep this AppId unchanged in all future releases so Setup upgrades the existing installation.
AppId={{68D9A3E3-1F4A-4772-90A7-77D4BC2B2A56}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\PhysicsMathPocket
UsePreviousAppDir=yes
DefaultGroupName=Physics + Math Pocket
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=release
OutputBaseFilename=PhysicsMathPocket_Setup_{#MyAppVersion}_{#MyAppChannel}_Build{#MyAppBuild}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardImageFile=assets\wizard.bmp
WizardSmallImageFile=assets\wizard_small.bmp
SetupIconFile=assets\physics_pocket.ico
LicenseFile=LICENSE.md
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
VersionInfoVersion={#MyAppVersion}.{#MyAppBuild}
VersionInfoDescription=Physics + Math Pocket 설치/업데이트 프로그램
VersionInfoProductName=Physics + Math Pocket
VersionInfoProductVersion={#MyAppVersion}.{#MyAppBuild}
VersionInfoCopyright={#MyAppCopyright}
MinVersion=10.0.17763

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕 화면에 바로가기 만들기"; GroupDescription: "추가 바로가기:"

[Files]
Source: "dist\PhysicsMathPocket\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README_KO.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "SOURCES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "DESIGN_NOTES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Physics + Math Pocket"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\assets\physics_pocket.ico"; WorkingDir: "{app}"
Name: "{autodesktop}\Physics + Math Pocket"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\assets\physics_pocket.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Physics + Math Pocket 실행"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  DataDir: string;
  StampPath: string;
  NowText: string;
  FirstText: string;
begin
  if CurStep = ssPostInstall then
  begin
    DataDir := ExpandConstant('{localappdata}\PhysicsMathPocket');
    ForceDirectories(DataDir);
    StampPath := DataDir + '\install_state.ini';
    NowText := GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':');
    FirstText := GetIniString('Install', 'FirstInstalledAt', '', StampPath);
    if FirstText = '' then
      SetIniString('Install', 'FirstInstalledAt', NowText, StampPath);
    SetIniString('Install', 'LastUpdatedAt', NowText, StampPath);
    SetIniString('Install', 'Version', '{#MyAppVersion}', StampPath);
    SetIniString('Install', 'Build', '{#MyAppBuild}', StampPath);
  end;
end;
