# Panel de Administración de Estacionamientos

Versión de pruebas para Jorge en la rama `raspberry-trixie`.

Incluye alta, modificación, desactivación, reactivación y eliminación del catálogo,
consulta del estado local de actualización, consultas y reportes existentes.
Eliminar del catálogo requiere confirmar el nombre y conserva las bases históricas,
los archivos de respaldo y los usuarios. Los nombres y bases retirados quedan reservados.

## Comportamiento de esta versión

«Cargar información» conecta a la base MariaDB configurada. No descarga respaldos.
«Estado de actualización» lee el registro SQLite local, si existe; no abre correo ni
MariaDB. Una instalación nueva puede mostrar «Sin fecha registrada».
Los módulos de correo y actualización se conservan, pero el actualizador automático
no está conectado a la interfaz. No ejecutar `instalar_mejoras_panel.py` ni activar
el complemento `panel_mejoras.py` durante estas pruebas.

## Descarga para Jorge

```bash
git clone --branch raspberry-trixie --single-branch https://github.com/AurelioGuarneros/panel-administracion-estacionamientos.git
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
instalarlo por separado. El cliente MariaDB solo se necesita para operaciones
manuales de importación, fuera del flujo de estas pruebas.

## Configuración local

Los cuatro archivos `Config/config_files/*.json.example` contienen rutas o datos
ficticios. Copiarlos sin `.example` solamente si el destino no existe. No sobrescribir
una configuración previa. Los marcadores de contraseña no permiten iniciar sesión.

Configurar localmente:

- `user_settings.json`: usuarios del panel, permisos y reportes. Contraseña de acceso
  en texto legible, según el comportamiento existente.
- `database_connection_configuration.json`: conexiones a bases ya existentes.
  Los campos `password` e `iv` usan el cifrado AES ya implementado en
  `Tools.proyect_tools.Tools.cifrar_AES`; no colocar texto legible en esos campos.
  La cuenta debe tener los permisos requeridos por las funciones que se prueben.
- `path_files_settings.json`: mapa de rutas relativas; el ejemplo es utilizable.
- `system_settings.json`: plantilla de correo. Esta versión de la interfaz no la
  utiliza para actualizar bases; no introducir credenciales de correo para estas pruebas.

Las credenciales administrativas se entregan por un canal privado. Configurar los
usuarios nuevos de cada instalación sin modificar los usuarios existentes de cajeros.
El alta de un estacionamiento hereda la conexión de una plantilla existente; no crea
la base ni habilita automáticamente su actualización.

```bash
bash iniciar_linux.sh
```

Probar con bases de consulta de pruebas ya preparadas. Las pantallas de gestión de
usuarios TPV existentes pueden modificar usuarios cuando se usan sus operaciones;
eliminación del catálogo de estacionamientos es una operación distinta.

## Verificación

```bash
.venv/bin/python -B -m unittest discover -s tests
```

Las pruebas utilizan datos ficticios y dobles de servicios. No validan acceso a los
buzones, funcionamiento con bases reales ni ejecución física en Raspberry Pi.
Consultar `PREPARACION_RASPBERRY_TRIXIE.md` para recuperación y alcance.
