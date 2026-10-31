$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$setup = (Resolve-Path dist/instaladores/PanelEstacionamientos-Usuarios-Prueba-Windows-x64.exe).Path
$app = Join-Path $env:LOCALAPPDATA 'Programs/PanelEstacionamientos'
$datos = Join-Path $env:LOCALAPPDATA 'PanelEstacionamientos/datos'
$informe = Join-Path (Get-Location) 'dist/instaladores/prueba-windows.json'
function Ejecutar($Archivo, $Argumentos) {
    $p = Start-Process -FilePath $Archivo -ArgumentList $Argumentos -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "$Archivo terminó con código $($p.ExitCode)" }
}
Ejecutar $setup '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="instalacion-prueba.log"'
if (!(Test-Path "$env:APPDATA/Microsoft/Windows/Start Menu/Programs/Panel de Estacionamientos/Panel de Estacionamientos.lnk")) { throw 'Falta acceso directo' }
# Comprobar independencia del PATH de Python/Git; el runner sí tiene herramientas instaladas.
$pathOriginal = $env:PATH
try {
    $env:PATH = "$env:SystemRoot/system32;$env:SystemRoot"
    Ejecutar "$app/PanelEstacionamientos.exe" "--smoke-test `"$informe`""
} finally { $env:PATH = $pathOriginal }
if (!(Test-Path $informe)) { throw 'Falta informe de prueba del ejecutable' }
New-Item -ItemType Directory -Force $datos | Out-Null
$testigo = Join-Path $datos 'conservar-prueba.txt'
Set-Content $testigo 'dato ficticio que debe conservarse'
$hash = (Get-FileHash $testigo).Hash
Ejecutar $setup '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
if ((Get-FileHash $testigo).Hash -ne $hash) { throw 'Reinstalación alteró datos' }
Ejecutar "$app/unins000.exe" '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
if ((Get-FileHash $testigo).Hash -ne $hash) { throw 'Desinstalación alteró datos' }
Ejecutar $setup '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
if ((Get-FileHash $testigo).Hash -ne $hash) { throw 'Nueva instalación alteró datos' }
