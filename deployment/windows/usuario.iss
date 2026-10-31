#define AppVersion "2026.10.30.1"
[Setup]
AppId={{B90698E9-7720-4EA6-9852-154697F99858}
AppName=Panel de Administración de Estacionamientos (prueba)
AppVersion={#AppVersion}
AppPublisher=Panel de Estacionamientos
DefaultDirName={localappdata}\Programs\PanelEstacionamientos
DefaultGroupName=Panel de Estacionamientos
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\..\dist\instaladores
OutputBaseFilename=PanelEstacionamientos-Usuarios-Prueba-Windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
UninstallDisplayIcon={app}\PanelEstacionamientos.exe
AppMutex=Local\PanelEstacionamientosUsuario
CloseApplications=yes
[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; Flags: checkedonce
[Files]
Source: "..\..\dist\PanelEstacionamientos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Panel de Estacionamientos"; Filename: "{app}\PanelEstacionamientos.exe"
Name: "{group}\Carpeta de datos y registros"; Filename: "{localappdata}\PanelEstacionamientos\datos"
Name: "{group}\Desinstalar Panel"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Panel de Estacionamientos"; Filename: "{app}\PanelEstacionamientos.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\PanelEstacionamientos.exe"; Description: "Iniciar el Panel"; Flags: nowait postinstall skipifsilent
; Nunca usar UninstallDelete en la carpeta persistente de datos.
