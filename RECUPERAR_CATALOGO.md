# Recuperar el catálogo local sin perder configuraciones

Versión de prueba: **`v2026.10.30-recuperacion-catalogo.1`**, rama
`instalacion-configuracion-local`. La versión anterior
`v2026.10.30-respaldos-pruebas.1` no contiene esta corrección.

## Causa y operación explícita

La interfaz lee el archivo indicado por `database_config_file` en el mapa local,
normalmente `Config/config_files/database_connection_configuration.json`.
La instalación anterior conservó ese archivo porque ya existía, aunque solo
contenía Admin/db_test y el estacionamiento db_ejemplo. La plantilla distribuida
no se mezcla automáticamente al iniciar el panel ni al actualizar Git.

`Tools/recuperar_catalogo.py` agrega explícitamente los registros ausentes de
`Config/catalogo_inicial.json`. Sin `--aplicar` solo muestra el plan y no escribe.
Con `--aplicar` conserva un respaldo de los bytes originales y sustituye el JSON
atómicamente. Respeta la ruta configurada que usa la interfaz.

- Admin, credenciales, campos privados y registros personalizados se conservan.
- Un registro de ejemplo se retira únicamente si coincide íntegramente con el
  ejemplo distribuido, sin campos añadidos ni valores modificados. Un ejemplo
  personalizado, incluso desactivado, se conserva.
- Los activos locales ya presentes se conservan con sus nombres, alias, ids y
  estados. Un desactivado no se reactiva; una identidad retirada no reaparece.
- Se agrega Ciudad Mendoza a las reservas de retirados; no se agrega como activo.
  Si hay un registro local que contradice esa reserva, se detiene para revisión.
- Se detectan colisiones de nombres, alias, bases, identificadores y remitentes.
  No se resuelven sobrescribiendo datos locales ni fusionando identidades ambiguas.
- Las altas nuevas usan los campos ficticios de conexión de la plantilla; nunca
  copian las credenciales privadas de otro estacionamiento. Los reportes pueden
  usar el perfil local ya configurado, tras ampliar sus asociaciones y permisos.

En la instalación de Jorge que solo contiene los ejemplos intactos, el resultado
esperado es Admin + 12 estacionamientos activos y Ciudad Mendoza retirado.
Si hay personalizaciones, el total puede ser mayor; si hay retiros o desactivados
locales, se respetan y el total activo puede ser menor. No se fuerza siempre 12
ignorando decisiones locales. Repetir la operación no duplica registros ni vuelve
a escribir un archivo que ya coincide.

## Actualizar el código en la Raspberry

Cerrar el panel y cualquier otro proceso de actualización. Desde la carpeta de
la instalación actual, en una misma terminal:

```bash
set -e
test -f main.py
test -x .venv/bin/python
git diff --exit-code
git diff --cached --exit-code
resguardo="$(mktemp -d "$HOME/panel-antes-recuperar-catalogo-XXXXXXXX")"
cp -a Config/config_files "$resguardo/"
if [ -f "$HOME/.config/panel-estacionamientos/recuperacion.json" ]; then
  cp -a "$HOME/.config/panel-estacionamientos/recuperacion.json" "$resguardo/"
fi
chmod -R go-rwx "$resguardo"
printf 'Resguardo privado: %s\n' "$resguardo"
git fetch origin tag v2026.10.30-recuperacion-catalogo.1
git switch --detach v2026.10.30-recuperacion-catalogo.1
.venv/bin/python -B -m unittest discover -s tests
```

La descarga explícita de la etiqueta funciona también si el repositorio se clonó
con `--single-branch`. El código queda en esa versión identificada (detached HEAD),
sin modificar main ni ramas locales.

Si Git detecta modificaciones locales o un comando falla, detenerse sin usar
reset, clean ni cambios forzados. Los cuatro JSON privados no se reemplazan por
Git. No volver a ejecutar el configurador IMAP ni generar contraseñas nuevas.

## Recuperar el catálogo de la interfaz

```bash
.venv/bin/python Tools/recuperar_catalogo.py
.venv/bin/python Tools/recuperar_catalogo.py --aplicar
```

Revisar primero el plan. En el caso de Jorge debería indicar 12 altas, una reserva
de retirado y un ejemplo intacto a retirar. El comando informa dónde guardó el
respaldo privado. Este termina en `.respaldo`, tiene permisos 0600 en Linux y no
se incluye en Git. Se preservan propietario, permisos y atributos del archivo
reemplazado. Si falla el reemplazo atómico, permanece el archivo original y su
respaldo. Si otro proceso cambia el archivo durante la revisión, se detiene.

Esta operación no modifica IMAP, el perfil de recuperación, MariaDB ni el auxiliar.
No ejecutar una importación todavía: recuperar el listado no amplía permisos.

## Revisar y ampliar autorizaciones existentes

El perfil `~/.config/panel-estacionamientos/recuperacion.json` puede contener solo
la asociación db_ejemplo, porque se generó desde el catálogo incompleto.
El auxiliar también puede tener una lista y sudoers limitados a esa base.
La operación siguiente compara los tres elementos antes de aplicar cambios:

```bash
sudo /usr/bin/python3 deployment/trixie/actualizar_autorizaciones.py \
  --usuario "$USER" \
  --perfil "$HOME/.config/panel-estacionamientos/recuperacion.json"
```

Sin `--aplicar` no conecta a MariaDB ni escribe archivos. Muestra las bases nuevas
que faltan en el perfil y verifica que las autorizaciones instaladas correspondan
al mismo perfil y usuario. Si el auxiliar o sus reglas difieren, se detiene con
un diagnóstico controlado. No sustituye un auxiliar distinto ni reglas ajenas.
Las asociaciones de base/remitente conflictivas requieren revisión; no se cambian
silenciosamente las existentes.

Después de revisar que las nuevas bases corresponden a los activos recuperados:

```bash
sudo /usr/bin/python3 deployment/trixie/actualizar_autorizaciones.py \
  --usuario "$USER" \
  --perfil "$HOME/.config/panel-estacionamientos/recuperacion.json" \
  --aplicar
sudo visudo -cf /etc/sudoers.d/panel-estacionamientos
bash iniciar_linux.sh
```

Este paso sí consulta MariaDB local y amplía grants en la Raspberry. No descarga
ni restaura respaldos, no crea o elimina bases y no crea cuentas ni cambia
contraseñas. Reutiliza el otorgamiento de permisos del instalador existente:

- Importador: permisos de restauración solo sobre cada `panel_stage_<base>` nuevo.
- Lector: SELECT y SHOW VIEW sobre las bases locales nuevas, con nombres exactos.
- Sudoers: comandos limitados a cada base explícita y una huella de 64 hexadecimales.
- Sin privilegios globales, FILE, SUPER, EXECUTE, TRIGGER ni GRANT OPTION.

Se conservan los valores completos de IMAP, las cuentas, las contraseñas y el
socket. Solo se agregan asociaciones activas ausentes. Las asociaciones previas,
incluida db_ejemplo si estaba autorizada, se mantienen para no revocar permisos
existentes ni alterar sus datos. No aparecen en la interfaz si ya no están en el
catálogo, y el actualizador sigue excluyendo los registros inactivos y retirados.
No se añaden nuevas autorizaciones para Ciudad Mendoza o estaciones desactivadas.

Se respalda cada archivo modificado: lista de bases, sudoers y perfil. Los archivos
se reemplazan atómicamente y el perfil se activa al final. Se utiliza el bloqueo
compartido con el actualizador. Si falla una escritura, se intenta revertir los
archivos escritos; los respaldos permanecen. Los grants de MySQL/MariaDB no forman
una transacción con los archivos: si hubo un fallo posterior, pueden quedar grants
nuevos, siempre limitados a los esquemas del plan. Un reintento acepta únicamente
esos grants planificados. Si también falla la reversión de archivos, detenerse y
revisar los respaldos antes de continuar; no ejecutar restauraciones en ese estado.

## Comprobación final

En Administración deben verse los estacionamientos recuperados y no Ciudad
Mendoza. En el caso sin personalizaciones se esperan los 12 activos originales.
Con el catálogo y las autorizaciones ya coherentes, la recuperación real se hace
con las acciones de Estado de actualización según
[la guía de respaldos](RECUPERACION_INSTALACION_NUEVA.md).

Las pruebas de esta corrección usan archivos temporales y MariaDB/IMAP simulados.
No se ejecutan restauraciones, no se conecta al correo y no se cambian bases o
configuraciones reales del equipo de desarrollo.
