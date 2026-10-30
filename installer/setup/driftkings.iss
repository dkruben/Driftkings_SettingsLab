; Build only through build_tools/build_installer.py. Payload is never conditional.
#if VER < EncodeVer(6, 7, 1)
  #error Inno Setup 6.7.1 or later is required
#endif
#ifndef InputDir
  #error Run build_tools/build_installer.py --artifacts <build> --compile
#endif
#include InputDir + "\metadata.generated.iss"

[Setup]
AppId={code:InstallationId}
AppName=Driftkings
AppVersion={#BuildVersion}
AppPublisher=DriftKingsMods
AppPublisherURL=https://github.com/dkruben/Driftkings_SettingsLab
DefaultDirName={sd}\Games\World_of_Tanks
DisableProgramGroupPage=yes
DisableDirPage=no
AppendDefaultDirName=no
; The game folder always exists; ClientError validates it instead of a generic overwrite prompt.
DirExistsWarning=no
UsePreviousAppDir=no
UsePreviousLanguage=no
UsePreviousGroup=no
UsePreviousUserInfo=no
UsePreviousPrivileges=no
UsePreviousSetupType=no
UsePreviousTasks=no
PrivilegesRequired=lowest
MinVersion=10.0
; Dark custom style matching the Driftkings artwork; branding.generated.iss adds the game background.
WizardStyle=modern dark
WizardBackColor=#15120f
WizardSizePercent=130,130
LicenseFile={#RepoRoot}\licence
InfoBeforeFile={#InputDir}\changelog.generated.txt
OutputDir={#InstallerOutput}
OutputBaseFilename=Driftkings-{#BuildVersion}-WoT-{#GameVersion}-Setup
UninstallFilesDir={app}\mods\configs\driftkings\installer
UninstallDisplayName=Driftkings {#BuildVersion}
CloseApplications=no
RestartApplications=no
Compression=lzma2
SolidCompression=yes

[Dirs]
Name: "{app}\mods\configs\driftkings\sixthsense"; Flags: uninsneveruninstall
Name: "{app}\mods\configs\driftkings\images"; Flags: uninsneveruninstall

; Languages, wizard texts and component names come from installer/setup/messages.json and the mod YAML catalogues.
#include InputDir + "\languages.generated.iss"
#include InputDir + "\branding.generated.iss"
#include InputDir + "\payload.generated.iss"
#include InputDir + "\previews.generated.iss"
#include InputDir + "\components.generated.iss"

[Code]
#include "wizard.iss"
