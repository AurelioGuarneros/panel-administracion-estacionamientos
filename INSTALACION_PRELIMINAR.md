# Instalación preliminar (no validada)
Se conserva Python + Tkinter para Windows y Linux/Raspberry Pi OS.

1. Incorporar el código original **depurado** (sin `.git`, entornos virtuales, respaldos ni configuraciones privadas). Debe incluir `main.py`.
2. Linux o Raspberry Pi OS: instalar paquetes del sistema `python3`, `python3-tk`, `python3-venv` y el cliente de MariaDB/MySQL. Ejecutar `bash instalar_linux.sh` y después `bash iniciar_linux.sh`.
3. Windows: instalar Python 3 con Tcl/Tk y cliente MySQL adecuado; ejecutar `instalar_windows.bat`, luego `iniciar_windows.bat`.
4. Restaurar en cada equipo la configuración local, guardando las contraseñas **fuera del repositorio**.
5. Verificar la lectura IMAP, la importación de respaldos y las consultas contra una base de prueba antes de usarlo en producción.

No se trata aún de instaladores finales ni se garantiza compatibilidad con todas las versiones de Windows/Linux.
