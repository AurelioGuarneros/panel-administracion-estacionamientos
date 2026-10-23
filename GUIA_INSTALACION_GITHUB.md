# Instalación de prueba desde GitHub — Ubuntu y Raspberry Pi OS

Rama congelada de prueba: `respaldo-panel-20261023`. **No instalar en un equipo que esté controlando una barrera en producción.**

## Instalación en equipo nuevo

Requiere Linux de escritorio (Ubuntu o Raspberry Pi OS Desktop), conexión a Internet, `git` y permisos `sudo`.

```bash
sudo apt-get update
sudo apt-get install -y git
git clone --branch respaldo-panel-20261023 --single-branch https://github.com/AurelioGuarneros/panel-administracion-estacionamientos.git
cd panel-administracion-estacionamientos
bash INSTALAR_DESDE_GITHUB.sh
bash VERIFICAR_INSTALACION.sh
```

El instalador instala paquetes del sistema y dependencias Python en `.venv`, sin importar SQL ni cambiar datos existentes. **No configura MariaDB Server automáticamente**: se debe decidir si el servidor estará en la misma máquina o en otra, crear un usuario de pruebas con permisos mínimos y preparar bases locales separadas. `mariadb-client` sí se instala.

## Configuración privada (no publicar en GitHub)

La aplicación requiere archivos JSON locales en `Config/config_files/` (incluyendo `path_files_settings.json`, configuración de conexiones y correo). GitHub los excluye deliberadamente. El instalador no los inventa ni descarga credenciales. Configurar de forma segura, con permisos `chmod 600`, usando los valores y formato válidos de la instalación existente. Nunca enviar contraseñas por issues ni subir respaldos SQL al repositorio.

Una vez configurado el entorno y restauradas **bases de prueba**, iniciar desde la carpeta del proyecto:

```bash
./iniciar_linux.sh
```

## Reporte de Jorge

Anotar modelo de Raspberry, versión de Raspberry Pi OS, arquitectura (`uname -m`), versión de Python, resultado de `VERIFICAR_INSTALACION.sh`, si abrió la interfaz, selección de estación, consulta de corte, ingresos, exportación y estado de actualizaciones. Adjuntar solo errores sin contraseñas, correos privados ni datos de clientes.

**Estado:** scripts preparados para pruebas, todavía no validados en Raspberry física ni en una instalación limpia de Ubuntu.
