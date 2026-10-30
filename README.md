# Panel de Administración de Estacionamientos

Desarrollo de recuperación para Jorge en la rama `instalacion-configuracion-local`.

Incluye alta, modificación, desactivación, reactivación y eliminación del catálogo,
consulta del estado local de actualización, consultas y reportes existentes.
Eliminar del catálogo requiere confirmar el nombre y conserva las bases históricas,
los archivos de respaldo y los usuarios. Los nombres y bases retirados quedan reservados.

## Comportamiento de esta versión

«Cargar información» consulta la base configurada; si hay un perfil de recuperación
para esa estación, usa su base MariaDB local con permisos de lectura.
«Estado de actualización» abre el registro local y ofrece acciones explícitas para
consultar el receptor, descargar ZIP validados e importar una estación o todas.
La apertura de ventanas no consulta servicios ni inicia importaciones.
No ejecutar `instalar_mejoras_panel.py`: se conserva la administración vigente y
el procesamiento de respaldos se comparte con el actualizador existente.

## Descarga para Jorge

```bash
git clone --branch instalacion-configuracion-local --single-branch https://github.com/AurelioGuarneros/panel-administracion-estacionamientos.git
cd panel-administracion-estacionamientos
```

En Raspberry Pi OS Trixie de escritorio se requiere Python 3, soporte Tkinter,
venv y acceso a una instancia MariaDB ya preparada. La validación de esta entrega
se realizó en Linux con Python 3.12; la ejecución nativa en Trixie queda para Jorge.
No se incluyen bases de datos ni se crean desde el instalador.

```bash
sudo apt update
sudo apt install python3-venv python3-tk
bash instalar_linux.sh
```

Los reportes que convierten Excel a PDF usan LibreOffice en Linux; requieren
instalarlo por separado. La recuperación requiere MariaDB local y su cliente para generar resguardos
antes de reemplazar bases. La preparación se describe al final de esta guía.

## Configuración local

Los instaladores crean los cuatro archivos `Config/config_files/*.json` faltantes
usando sus ejemplos y conservan íntegros los existentes. Cuando falta
`user_settings.json`, solicitan una contraseña local y su confirmación para
**Aurelio**, con permisos de Administrador. No existe una contraseña administrativa
predeterminada; la plantilla tiene la contraseña vacía y no permite ingresar así.
La contraseña no se muestra al escribirla ni se pasa como argumento de comandos.
Si ya existe el archivo de usuarios, no se solicita contraseña ni se cambian usuarios.

Para completar configuraciones en una instalación ya preparada, ejecutar desde
la carpeta del panel `.venv/bin/python Tools/preparar_configuracion.py` en Linux
o `.venv\Scripts\python.exe Tools\preparar_configuracion.py` en Windows.
Las conexiones y el correo conservan marcadores ficticios: deben configurarse
localmente antes de usarlos. Esta preparación no conecta con MariaDB ni con correo.

Configurar localmente:

- `user_settings.json`: usuarios del panel, permisos y reportes. Contraseña de acceso
  en texto legible, según el comportamiento existente.
- `database_connection_configuration.json`: conexiones a bases ya existentes.
  Los campos `password` e `iv` usan el cifrado AES ya implementado en
  `Tools.proyect_tools.Tools.cifrar_AES`; no colocar texto legible en esos campos.
  La cuenta debe tener los permisos requeridos por las funciones que se prueben.
- `path_files_settings.json`: mapa de rutas relativas; el ejemplo es utilizable.
- `system_settings.json`: configuración de correo de las funciones anteriores.
  La recuperación nueva usa un perfil privado separado; no requiere editar este JSON.

La contraseña administrativa se elige en cada instalación y permanece en el archivo
local excluido de Git. Se conserva el almacenamiento en texto legible del mecanismo
de autenticación existente. No modificar los usuarios existentes de cajeros.
El alta de un estacionamiento hereda la conexión de una plantilla existente; no crea
la base ni habilita automáticamente su actualización.

```bash
bash iniciar_linux.sh
```

La primera recuperación real se ejecuta en la Raspberry de Jorge. Las pantallas de gestión de
usuarios TPV existentes pueden modificar usuarios cuando se usan sus operaciones;
eliminación del catálogo de estacionamientos es una operación distinta.

## Verificación

```bash
.venv/bin/python -B -m unittest discover -s tests
```

Las pruebas utilizan datos ficticios y dobles de servicios. No validan acceso a los
buzones, funcionamiento con bases reales ni ejecución física en Raspberry Pi.
Consultar `PREPARACION_RASPBERRY_TRIXIE.md` para recuperación y alcance.

## Catálogo de una instalación nueva

El instalador incorpora `Config/catalogo_inicial.json` únicamente cuando falta el
archivo local de conexiones. Incluye los estacionamientos validados y referencias
retiradas, sin credenciales. Conserva sus estados y deja deshabilitada la
actualización hasta verificar la configuración local. No mezcla catálogos existentes.
Consultar [la prueba del catálogo en Raspberry](PRUEBA_CATALOGO_TRIXIE.md)
para actualizar conservando configuraciones o probar el catálogo en una carpeta aislada.
La etiqueta `v2026.10.30-catalogo-pruebas.1` solo contiene la prueba del catálogo.
El desarrollo actual añade el flujo de recuperación descrito a continuación.

## Recuperación de respaldos en Trixie

El desarrollo actual permite configurar un receptor IMAP TLS y recuperar respaldos
desde «Estado de actualización», mediante descarga validada, restauración temporal
y el auxiliar de activación. No consulta servicios al abrir la ventana.
Seguir [la preparación y primera recuperación real](RECUPERACION_INSTALACION_NUEVA.md)
en la Raspberry de destino. El perfil es local y no cambia los JSON existentes.
