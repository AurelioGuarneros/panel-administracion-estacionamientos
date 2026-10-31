@echo off
echo Instalador del entorno de desarrollo. Para uso normal descarga el instalador Usuarios .exe.
cd /d "%~dp0"
if not exist main.py (
 echo Falta main.py: primero incorpora el codigo del panel.
 exit /b 1
)
py -3.13 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe Tools\preparar_configuracion.py
if errorlevel 1 exit /b 1
echo Entorno preparado. Ejecuta iniciar_windows.bat para revisar interfaces y catalogo.
echo No se ha instalado MariaDB.
