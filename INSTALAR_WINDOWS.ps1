$ErrorActionPreference = "Stop"
Write-Host "=== Panel de Estacionamientos - preparacion Windows ==="
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Instala Python 3.11 o 3.12 desde python.org, con Python Launcher, y vuelve a ejecutar."
}
if (-not (Test-Path "requirements.txt")) { throw "No se encuentra requirements.txt" }
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  py -3 -m venv .venv
}
$python = Join-Path $root ".venv\Scripts\python.exe"
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Fallo al actualizar pip" }
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Fallo al instalar dependencias" }
& $python -m compileall -q main.py Models Config Controller Views Tools actualizador_respaldos.py activador_respaldos.py panel_mejoras.py
if ($LASTEXITCODE -ne 0) { throw "Hay errores de sintaxis" }
Write-Host "Preparacion terminada. Ejecuta .\VERIFICAR_WINDOWS.ps1"
Write-Host "Las configuraciones privadas y MariaDB de prueba se preparan por separado."
