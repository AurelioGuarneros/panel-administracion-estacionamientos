$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Primero ejecuta INSTALAR_WINDOWS.ps1" }
& .\.venv\Scripts\python.exe -c "import tkinter, pymysql, PIL, tkcalendar, ttkthemes, xlsxwriter, openpyxl, Crypto, dateutil, requests; print('Dependencias Python: OK')"
if ($LASTEXITCODE -ne 0) { throw "Fallo en importaciones" }
foreach ($name in @("path_files_settings.json", "database_connection_configuration.json", "system_settings.json")) {
  $file = Join-Path "Config\config_files" $name
  if (Test-Path $file) { Write-Host "PRESENTE: $name" } else { Write-Host "PENDIENTE configuracion privada: $name" }
}
Write-Host "No se ha comprobado aun la conexion a correo o bases de datos."
