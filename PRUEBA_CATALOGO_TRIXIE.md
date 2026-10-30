# Prueba del catálogo en Raspberry Pi OS Trixie

Versión: `v2026.10.30-catalogo-pruebas.1`.

Incluye el instalador, la contraseña administrativa elegida localmente y el catálogo
inicial de 12 estacionamientos activos, cero desactivados y Ciudad Mendoza retirado.
No se incluyen nuevos componentes de descarga, importación o activación.
No se modifican MariaDB ni los usuarios de las TPV.

## Actualizar la instalación existente

Cerrar el panel. Abrir una terminal dentro de su carpeta actual (la que contiene
`main.py` y `.venv`). Ejecutar el bloque en esa misma terminal. Si algún comando
falla, detenerse; no usar reset, clean, checkout forzado ni sobrescribir archivos.

```bash
set -e
panel_actual="$PWD"
test -f main.py
test -x .venv/bin/python
git diff --exit-code
git diff --cached --exit-code
resguardo_config="$(mktemp -d "$HOME/panel-config-previa-XXXXXXXX")"
chmod 700 "$resguardo_config"
cp -a Config/config_files "$resguardo_config/"
chmod -R go-rwx "$resguardo_config"
printf 'Configuraciones resguardadas en: %s\n' "$resguardo_config"
git fetch origin tag v2026.10.30-catalogo-pruebas.1
git switch --detach v2026.10.30-catalogo-pruebas.1
.venv/bin/python Tools/preparar_configuracion.py
.venv/bin/python -B -m unittest discover -s tests
bash iniciar_linux.sh
```

La etiqueta deja el código en modo detached HEAD para probar exactamente esa
versión. No modifica la rama main ni la etiqueta estable anterior.
Los cambios locales en archivos de código hacen detener la comprobación inicial;
conservarlos y revisarlos antes de actualizar. Los JSON privados están ignorados
por Git y el preparador no los sobrescribe. Si falta el archivo de usuarios se
solicita una contraseña nueva para Aurelio; si existe, siguen vigentes sus usuarios
y contraseñas, sin añadir ni reemplazar a Aurelio.

**Si ya existe el archivo local de conexiones, no aparecerán automáticamente los
12 registros distribuidos.** Ese es el comportamiento esperado para conservar el
catálogo local. No borrar ni renombrar configuraciones para forzar la carga.

## Probar los 12 registros sin tocar configuraciones existentes

Cerrar el panel. Desde la carpeta de la instalación existente, ejecutar en una
misma terminal. Esta prueba usa el entorno Python existente y crea configuraciones
independientes en otra carpeta; no copia credenciales de la instalación actual.

```bash
set -e
panel_actual="$PWD"
test -f main.py
test -x .venv/bin/python
git fetch origin tag v2026.10.30-catalogo-pruebas.1
prueba_catalogo="$(mktemp -d "$HOME/panel-catalogo-prueba-XXXXXXXX")"
git worktree add --detach "$prueba_catalogo" v2026.10.30-catalogo-pruebas.1
cd "$prueba_catalogo"
"$panel_actual/.venv/bin/python" Tools/preparar_configuracion.py
"$panel_actual/.venv/bin/python" -B -m unittest discover -s tests
"$panel_actual/.venv/bin/python" main.py
```

Elegir y confirmar una contraseña local para Aurelio. Entrar con ese usuario y la
contraseña elegida. En Administración verificar 12 activos, ningún inactivo y que
Ciudad Mendoza no aparezca en el listado. Su identidad queda reservada en
`estacionamientos_eliminados`. Todas las estaciones tendrán actualización automática
y verificación de configuración deshabilitadas. No intentar abrir reportes ni
configurar correo o bases durante esta prueba.

Las pruebas usan datos ficticios y servicios simulados. En esta publicación hay
96 pruebas; las otras tres del espacio de desarrollo corresponden al auxiliar de
activación que deliberadamente no se publica todavía. No se necesita instalar
paquetes ni ejecutar el instalador completo si la versión anterior ya abre bien.
