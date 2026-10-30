# Recuperación real de respaldos en Raspberry Pi OS Trixie

Versión de prueba: **`v2026.10.30-respaldos-pruebas.1`**, rama
`instalacion-configuracion-local`. La versión anterior
`v2026.10.30-catalogo-pruebas.1` no contiene este flujo.
La primera descarga e importación real se realiza en la Raspberry de Jorge.

## Qué hace Estado de actualización

Abrir la ventana lee únicamente el registro local. Sus acciones explícitas son:

- **Consultar y descargar ZIP**: consulta el receptor mediante IMAP TLS con
  validación de certificado, sin modificar mensajes; busca los UID de mayor a
  menor hasta hallar un ZIP válido de cada remitente del catálogo. Valida CRC,
  un único SQL, nombres de archivos, tamaño y formato SQL; lo guarda localmente.
- **Importar seleccionado**: descarga el respaldo válido más reciente de la
  estación seleccionada, prepara y valida una base temporal y activa sus tablas.
- **Descargar e importar todos**: ejecuta ese mismo flujo por cada estación activa
  autorizada. Un fallo se registra y permite continuar con la siguiente.

Se reutilizan `ActualizadorRespaldos.restaurar_temporal`, las validaciones de
`activador_respaldos.py` y el auxiliar existente. `panel_mejoras._procesar_estacion`
delega en el mismo flujo. No se instala el antiguo formulario del complemento:
la administración conserva el modelo actual y las reservas de los retirados.
No hay actualización automática al arrancar ni al seleccionar una estación.

## Preparar la Raspberry

Cerrar el panel. Desde la carpeta actual de su instalación:

```bash
set -e
test -f main.py
test -x .venv/bin/python
git diff --exit-code
git diff --cached --exit-code
resguardo_config="$(mktemp -d "$HOME/panel-config-previa-XXXXXXXX")"
cp -a Config/config_files "$resguardo_config/"
chmod -R go-rwx "$resguardo_config"
printf 'Configuraciones conservadas en: %s\n' "$resguardo_config"
git fetch origin tag v2026.10.30-respaldos-pruebas.1
git switch --detach v2026.10.30-respaldos-pruebas.1
sudo apt update
sudo apt install mariadb-server mariadb-client python3-pymysql sudo ca-certificates
sudo systemctl enable --now mariadb
systemctl is-active mariadb
.venv/bin/python -B -m unittest discover -s tests
if [ ! -e "$HOME/.config/panel-estacionamientos/recuperacion.json" ]; then
  .venv/bin/python Tools/configurar_respaldos.py
fi
```

Si todavía no existe el perfil, el configurador solicita servidor IMAP TLS, puerto (993 por defecto), usuario,
contraseña, carpeta (INBOX por defecto) y socket de MariaDB. La contraseña se pide
sin mostrarla ni pasarla por argumentos. Se usa el correo receptor real que
proporcione Aurelio; no existe una cuenta o contraseña predeterminada.

Crea únicamente `~/.config/panel-estacionamientos/recuperacion.json` con permisos
0600, directorio 0700. Si ya existe, se detiene y lo conserva. No modifica los
cuatro JSON del panel. El perfil contiene la configuración del receptor, cuentas
MariaDB aleatorias exclusivas para esta recuperación y las asociaciones exactas
base/remitente de los activos del catálogo local. No crea usuarios del panel ni
usuarios de TPV. No se conecta a servicios durante su creación.

La actualización deja el código en la etiqueta identificada (detached HEAD). No
modifica main, las etiquetas anteriores ni los JSON privados. Si un comando falla,
detenerse sin forzar cambios. La primera comprobación de Git detecta modificaciones
locales en código; no eliminarlas para actualizar.

La cuenta receptora, su servidor y su certificado deben permitir IMAP TLS. No se
admite TLS sin verificar. Para corregir el correo se puede editar este nuevo
perfil privado localmente, manteniendo 0600; no copiarlo a GitHub ni a informes.
Los cambios de base/remitente del catálogo invalidan su asociación en el perfil;
no se habilitan nuevos destinos por editar solo un nombre en el catálogo.

Comprobar MariaDB y preparar el auxiliar:

```bash
set -e
sudo /usr/bin/python3 deployment/trixie/preparar_sistema.py \
  --usuario "$USER" \
  --perfil "$HOME/.config/panel-estacionamientos/recuperacion.json"
sudo /usr/bin/python3 deployment/trixie/preparar_sistema.py \
  --usuario "$USER" \
  --perfil "$HOME/.config/panel-estacionamientos/recuperacion.json" \
  --instalar
sudo visudo -cf /etc/sudoers.d/panel-estacionamientos
bash iniciar_linux.sh
```

La primera invocación solo comprueba acceso administrativo por socket, versión
MariaDB y sensibilidad a mayúsculas. La segunda crea cuentas dedicadas, concede
permisos, verifica sus grants y acceso, instala el auxiliar root y sudoers.
Se necesita sudo únicamente para esta preparación. Durante las actualizaciones
se usa `sudo -n`, restringido por base y huella hexadecimal; no se solicita la
contraseña del sistema.

Requiere MariaDB >= 10.6.1, tablas InnoDB y `lower_case_table_names=0`.
**No cambia esa variable ni convierte los nombres de bases**. Se conserva
`db_PUNTO_SANTA_ROSA_PV` exactamente. Las referencias de origen en el SQL pueden
variar en mayúsculas: se validan y se dirigen a la temporal con el nombre del
catálogo. Las tablas conocidas se reconocen sin distinguir mayúsculas y se crean
con los nombres que usan los reportes.

Si existe un auxiliar, sudoers o configuración de activación diferente, la
preparación se detiene sin sobrescribirlos. Enviar el mensaje de error para
revisarlo; no borrar configuraciones ni ampliar permisos para forzar la instalación.
No se modifica una cuenta MariaDB existente para cambiarle su contraseña.

## Primera recuperación real

1. Entrar con Aurelio y abrir **Estado de actualización**.
2. Pulsar **Consultar y descargar ZIP** para localizar y validar los respaldos.
3. Pulsar **Descargar e importar todos**. No se exige una prueba manual con bases
   ficticias; esta acción opera con el correo real en la Raspberry.
4. Esperar el resultado por estación. **Importado y activado** o **Ya importado;
   sin duplicar** acredita el resultado del flujo, no una garantía sobre mensajes
   que hayan llegado después de la consulta. La recepción usa INTERNALDATE del
   servidor, no la cabecera Date del remitente.
5. Cerrar la ventana, seleccionar un estacionamiento y abrir sus reportes. Para
   las asociaciones del perfil se utiliza la cuenta local lectora por socket,
   sin reescribir las conexiones existentes del catálogo.

La importación usa una cuenta que solo puede crear, modificar e insertar en sus
esquemas `panel_stage_<base>` explícitos. No tiene FILE, SUPER, EXECUTE, TRIGGER,
permisos globales ni acceso de escritura a bases definitivas. Los reportes usan
otra cuenta con SELECT y SHOW VIEW únicamente en sus bases locales autorizadas.
Los guiones bajos se escapan en GRANT para evitar comodines. El preparador revisa
los grants efectivos y rechaza privilegios adicionales.

## Validación y conservación de datos

No se envía el adjunto a un intérprete de comandos o a un cliente SQL interactivo.
El importador procesa un subconjunto de mysqldump: CREATE TABLE InnoDB de las
siete tablas requeridas (y Cambios opcional), DROP de esas tablas e INSERT VALUES
con literales. Se reconocen cabeceras, USE/CREATE DATABASE de la base esperada,
SET de dump y LOCK sin ejecutarlos. La sesión se prepara con instrucciones del
programa. Se rechazan scripts de shell, SOURCE, DELIMITER, LOAD DATA, rutinas,
triggers, vistas, funciones arbitrarias, otros esquemas y motores externos.
No se deben ampliar privilegios para aceptar un SQL rechazado.

Límites actuales: ZIP 256 MiB, correo 512 MiB, SQL descomprimido 2 GiB y sentencia
32 MiB. Un formato distinto o un límite excedido se rechaza conservando la base
anterior. Se busca un respaldo anterior que pase las validaciones del archivo.
La comprobación de relaciones y datos se realiza tras restaurar la temporal.

El auxiliar verifica tablas, InnoDB, relaciones, ausencia de referencias externas,
triggers, vistas y filas huérfanas. Para reemplazar una base existente también
rechaza regresiones de cantidad de filas o últimas entradas. Genera un dump
previo en `/var/backups/panel-estacionamientos` (solo root) y mueve las tablas
anteriores a `panel_anterior_<base>_<fecha>`; no elimina esos resguardos.
La activación usa un RENAME TABLE múltiple atómico; si falla la validación
posterior se intenta el renombrado inverso. Una pérdida de conexión durante esa
reversión requiere revisión del resguardo y la marca antes de continuar.

La tabla interna `_panel_respaldo`, creada por el auxiliar, viaja atómicamente con
las tablas y conserva SHA-256 y fecha. Permite reconocer un respaldo ya activado,
aunque el proceso haya terminado antes de registrar el éxito en SQLite. No se
reimporta un ZIP idéntico por un UID diferente. La huella y el CRC comprueban
integridad y duplicación; no son una firma de autenticidad del remitente.

Una temporal ocupada sin preparación coincidente se conserva y detiene únicamente
esa estación. Debe revisarse antes de reintentar; el programa no borra una temporal
que no puede identificar con seguridad. Las estaciones inactivas y retiradas se
excluyen, aunque queden registros históricos. Los cambios del catálogo local no
se sobrescriben ni se mezclan con el inicial.

## Registro y diagnóstico

ZIP: `~/.local/share/panel-estacionamientos/respaldos/<base>/`.
Registro: `~/.local/share/panel-estacionamientos/actualizaciones.sqlite3`.
La tabla `eventos_respaldos` conserva estación, fecha de operación, fase, resultado,
UID, identidad del buzón, archivo, SHA-256 y recepción si está disponible.
`importaciones` conserva el último éxito y `preparaciones` identifica temporales
validadas. Los mensajes de error de la interfaz son controlados y no incluyen
credenciales ni fragmentos de SQL.

Los JSON privados, perfiles, ZIP, SQL y SQLite están excluidos de Git. No adjuntar
esos archivos a incidencias. Para soporte basta el nombre de estación y la fase
que falló; conservar el archivo y los resguardos en la Raspberry.

La ejecución física inicial queda pendiente en la Raspberry de Jorge; en el
equipo de desarrollo solo se ejecutan pruebas automáticas con servicios simulados.
No se conectó al correo ni se importaron bases reales en esa computadora.

## Windows

Esta entrega habilita recuperación en Linux/Trixie. Windows necesita transporte
local host/puerto, exclusión entre procesos y un servicio de activación con ACL que
reemplace sudo. Debe reutilizar el mismo importador, validación, marcas y registro;
no ejecutar el helper Linux como si fuera portable. Las instalaciones Windows
sin perfil de recuperación conservan sus conexiones existentes.

Referencias técnicas: [RENAME TABLE de MariaDB](https://mariadb.com/docs/server/reference/sql-statements/data-definition/rename-table)
y [comandos del cliente MariaDB](https://mariadb.com/docs/server/clients-and-utilities/mariadb-client/mariadb-command-line-client).

## Verificación de esta entrega

Las 126 pruebas automáticas incluyen catálogo, conservación de configuraciones,
rechazo de SQL ajeno al formato admitido, importación temporal, exclusión de
inactivos/retirados, deduplicación y reversión de activación. Se ejecutaron con
conexiones reales a IMAP, MariaDB y sockets bloqueadas.

La compatibilidad Trixie se revisó por dependencias y sintaxis, más la validación
de sudoers mediante visudo. Se verificó la disponibilidad de MariaDB en ARM y de
PyMySQL en los repositorios Debian Trixie. No sustituye la primera ejecución física
del auxiliar en la Raspberry, que comprueba la versión y la configuración efectivas.
Fuentes: [MariaDB en Trixie](https://packages.debian.org/trixie/mariadb-server) y
[PyMySQL en Trixie](https://sources.debian.org/src/python-pymysql/).
