$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$setup = (Resolve-Path dist/instaladores/PanelEstacionamientos-Usuarios-Prueba-Windows-x64.exe).Path
$app = Join-Path $env:LOCALAPPDATA 'Programs/PanelEstacionamientos'
$datos = Join-Path $env:LOCALAPPDATA 'PanelEstacionamientos/datos'
$informe = Join-Path (Get-Location) 'dist/instaladores/prueba-windows.json'
function Ejecutar($Archivo, $Argumentos) {
    $p = Start-Process -FilePath $Archivo -ArgumentList $Argumentos -PassThru
    if (!$p.WaitForExit(180000)) {
        Stop-Process -Id $p.Id -Force
        throw 'El proceso excedió tres minutos'
    }
    $p.Refresh()
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
$config = New-Item -ItemType Directory -Force (Join-Path $datos 'Config/config_files')
Get-ChildItem Config/config_files/*.example | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $config.FullName ($_.Name -replace '\.example$', ''))
}
$originales = @{}
Get-ChildItem $datos -Recurse -File | ForEach-Object { $originales[$_.FullName] = (Get-FileHash $_.FullName).Hash }
function ComprobarDatos {
    foreach ($ruta in $originales.Keys) {
        if (!(Test-Path $ruta) -or (Get-FileHash $ruta).Hash -ne $originales[$ruta]) { throw 'Instalación o desinstalación alteró datos/configuraciones' }
    }
}
Ejecutar $setup '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
ComprobarDatos
Ejecutar "$app/unins000.exe" '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
ComprobarDatos
Ejecutar $setup '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
ComprobarDatos
