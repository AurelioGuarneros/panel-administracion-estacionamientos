# Prueba del panel en Windows 10/11 desde GitHub

**Estado:** preparación de dependencias para pruebas, sin validar aún la aplicación completa en Windows.

1. Instalar **Git para Windows** y **Python 3.11 o 3.12**, con Python Launcher. Abrir PowerShell.
2. Descargar la rama de pruebas:

```powershell
cd $HOME\Documents
git clone --branch respaldo-panel-20261023 --single-branch https://github.com/AurelioGuarneros/panel-administracion-estacionamientos.git
cd panel-administracion-estacionamientos
powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALAR_WINDOWS.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\VERIFICAR_WINDOWS.ps1
```

Si la carpeta ya existe, no repetir `git clone`; abrirla y comprobar que sea la rama de pruebas.

El instalador solo prepara el entorno Python, no instala MariaDB Server, no importa SQL ni incorpora contraseñas. Para pruebas funcionales, preparar un servidor MariaDB separado, los archivos JSON privados que espera la aplicación en `Config/config_files`, y verificar compatibilidad de rutas y del cliente MySQL. El código actual incluye una ruta de cliente de XAMPP para Windows; puede requerir adaptar esa ruta si no se utiliza XAMPP.

Una vez configurado, para intentar iniciar:

```powershell
.\.venv\Scripts\python.exe main.py
```

Registrar cada error en GitHub Issues: https://github.com/AurelioGuarneros/panel-administracion-estacionamientos/issues. Indicar versión Windows, Python, paso, resultado esperado/real y mensaje de error sin datos privados.

**Importante:** usar un equipo de pruebas, no un sistema de estacionamiento en producción.
