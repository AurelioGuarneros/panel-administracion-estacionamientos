@echo off
setlocal
set "PATH=%LocalAppData%\Programs\Python\Python313;%LocalAppData%\Programs\Python\Python313\Scripts;%LocalAppData%\Programs\Git\cmd;%PATH%"
set "DESTINO=%USERPROFILE%\source\panel-administracion-estacionamientos"
if exist "%DESTINO%" goto existente
git clone --branch desarrollo/instaladores-windows https://github.com/AurelioGuarneros/panel-administracion-estacionamientos.git "%DESTINO%"
if errorlevel 1 goto error
:existente
if not exist "%DESTINO%\instalar_windows.bat" goto error
cd /d "%DESTINO%"
call instalar_windows.bat
if errorlevel 1 goto error
echo Entorno preparado en %DESTINO%. Para iniciar, ejecuta iniciar_windows.bat.
pause
exit /b 0
:error
echo No se pudo preparar el entorno. Se conservaron los archivos existentes.
pause
exit /b 1
