@echo off
setlocal
title Panel Estacionamientos - Instalacion Windows 11
cd /d "%~dp0"
echo ==================================================
echo  PANEL DE ESTACIONAMIENTOS - PRUEBA WINDOWS 11
echo ==================================================
echo.
echo Esta prueba NO modifica el programa anterior.
echo No configura bases de datos ni contrasenas.
echo.
where py >nul 2>&1
if errorlevel 1 (
 echo FALTA PYTHON: instala Python 3.12 con Python Launcher.
 echo https://www.python.org/downloads/windows/
 pause
 exit /b 1
)
if not exist "requirements.txt" (
 echo ERROR: Ejecuta este archivo dentro de la carpeta del programa.
 pause
 exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALAR_WINDOWS.ps1"
if errorlevel 1 (
 echo.
 echo ERROR EN LA INSTALACION. Toma una foto y enviala.
 pause
 exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFICAR_WINDOWS.ps1"
echo.
echo La preparacion termino. Envia una foto de esta pantalla.
echo Las conexiones y bases de prueba se configuraran despues.
pause
