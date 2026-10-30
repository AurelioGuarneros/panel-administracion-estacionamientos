@echo off
cd /d "%~dp0"
if not exist main.py (
 echo Falta main.py: primero incorpora el codigo del panel.
 exit /b 1
)
py -3 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe Tools\preparar_configuracion.py
if errorlevel 1 exit /b 1
echo Dependencias Python instaladas. Configura MySQL/MariaDB y las credenciales locales.
