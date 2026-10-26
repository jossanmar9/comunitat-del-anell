; Instal·lador de Windows de La Comunitat (Inno Setup 6).
; El fa GitHub en publicar una versió (.github/workflows/publica.yml):
;   ISCC /DVersio=2.0 /DOrigen=..\..\dist\LaComunitat paquets\windows\comunitat.iss
; Origen és la carpeta de PyInstaller (LaComunitat.exe i _internal) amb el fitxer «installat»,
; que fa que les partides es guarden a %APPDATA%\LaComunitat.
; Llicència GPL-3.0-or-later.

#ifndef Versio
  #define Versio "0.0"
#endif
#ifndef Origen
  #define Origen "..\..\dist\LaComunitat"
#endif

[Setup]
AppId={{43CBC6F1-BADA-4F99-8A4C-DD9C8F4EFD84}
AppName=La Comunitat
AppVersion={#Versio}
AppVerName=La Comunitat {#Versio}
AppPublisher=La Comunitat
AppPublisherURL=https://jossanmar9.github.io/comunitat-del-anell/
AppSupportURL=https://github.com/jossanmar9/comunitat-del-anell/issues
AppUpdatesURL=https://github.com/jossanmar9/comunitat-del-anell/releases
DefaultDirName={localappdata}\Programs\LaComunitat
DefaultGroupName=La Comunitat
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist
OutputBaseFilename=LaComunitat-{#Versio}-installador
SetupIconFile=..\..\logo.ico
UninstallDisplayIcon={app}\LaComunitat.exe
UninstallDisplayName=La Comunitat
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "ca"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
ca.Nom=La Comunitat
es.Nom=La Comunidad
ca.Manual=Manual d'usuari
es.Manual=Manual de usuario
ca.Dades=Carpeta de dades
es.Dades=Carpeta de datos

[Tasks]
Name: "escriptori"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#Origen}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Dirs]
Name: "{userappdata}\LaComunitat"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{cm:Nom}"; Filename: "{app}\LaComunitat.exe"
Name: "{autodesktop}\{cm:Nom}"; Filename: "{app}\LaComunitat.exe"; Tasks: escriptori
Name: "{group}\{cm:Manual}"; Filename: "{app}\docs\manual-usuari.pdf"; Languages: ca; Check: FileExists(ExpandConstant('{app}\docs\manual-usuari.pdf'))
Name: "{group}\{cm:Manual}"; Filename: "{app}\docs\manual-usuario.pdf"; Languages: es; Check: FileExists(ExpandConstant('{app}\docs\manual-usuario.pdf'))
Name: "{group}\{cm:Dades}"; Filename: "{userappdata}\LaComunitat"

[Run]
Filename: "{app}\LaComunitat.exe"; Description: "{cm:LaunchProgram,{cm:Nom}}"; Flags: nowait postinstall skipifsilent
