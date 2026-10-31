[Setup]
AppId={{646B0B36-5ECC-4D16-9088-AEF0081DDCEB}
AppName=Herramientas de desarrollo del Panel (prueba)
AppVersion=2026.10.30.1
DefaultDirName={localappdata}\Programs\PanelEstacionamientosDesarrollo
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0
OutputDir=..\..\dist\instaladores
OutputBaseFilename=PanelEstacionamientos-Desarrollo-Prueba-Windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[Files]
Source: "..\..\build\herramientas\python.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "..\..\build\herramientas\git.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "preparar_desarrollo.bat"; DestDir: "{app}"
[Icons]
Name: "{userprograms}\Panel de Estacionamientos\Preparar entorno de desarrollo"; Filename: "{app}\preparar_desarrollo.bat"
[Code]
procedure InstalarHerramienta(Archivo, Parametros: String);
var Codigo: Integer;
begin
  if not Exec(ExpandConstant(Archivo), ExpandConstant(Parametros), '', SW_HIDE,
              ewWaitUntilTerminated, Codigo) then
    RaiseException('No se pudo iniciar la instalación de una herramienta.');
  if (Codigo <> 0) and (Codigo <> 3010) then
    RaiseException('La instalación de una herramienta falló. Consulta el registro en LocalAppData.');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    InstalarHerramienta('{tmp}\python.exe', '/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1 InstallLauncherAllUsers=0 /log "{localappdata}\Panel-Python-Instalacion.log"');
    InstalarHerramienta('{tmp}\git.exe', '/CURRENTUSER /VERYSILENT /NORESTART /LOG="{localappdata}\Panel-Git-Instalacion.log"');
  end;
end;
