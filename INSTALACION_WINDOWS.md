# Instaladores Windows de prueba

Estado: desarrollo, sin publicación en Releases. Base: `v2026.10.30-recuperacion-catalogo.1` (commit `bf5c7ac`). Windows 10/11 x64; ARM64 y Windows de 32 bits no validados.

## Descargar e instalar

1. Abre https://github.com/AurelioGuarneros/panel-administracion-estacionamientos/actions/workflows/instaladores-windows.yml y selecciona una ejecución correcta de la rama `desarrollo/instaladores-windows`.
2. En **Artifacts**, descarga `instaladores-windows-prueba-x64` (GitHub puede pedir iniciar sesión). Extrae el ZIP.
3. Ejecuta **`PanelEstacionamientos-Usuarios-Prueba-Windows-x64.exe`**. Incluye Python y las bibliotecas; no necesita instalar Python, Git ni abrir una terminal. El equipo puede estar sin conexión durante la instalación y el primer inicio.
4. Elige los accesos directos y abre el panel. Para una instalación nueva, responde **No** a importar configuración y crea y confirma la contraseña local del usuario **Aurelio**. Cancelar no crea la configuración de usuarios.
5. Entra con **Aurelio** y tu contraseña. Comprueba los 12 estacionamientos activos y Ciudad Mendoza como retirado. No se instala MariaDB ni se consulta correo al abrir el catálogo.

El instalador de prueba no está firmado digitalmente con un certificado del proyecto. Windows puede mostrar su aviso habitual para ejecutables sin firma. Comprueba la procedencia y el archivo `SHA256SUMS.txt` antes de ejecutarlo.

## Datos, actualización y recuperación

- Programa: `%LOCALAPPDATA%\Programs\PanelEstacionamientos`.
- Datos persistentes: `%LOCALAPPDATA%\PanelEstacionamientos\datos`.
- Configuraciones: `datos\Config\config_files`. No se distribuyen archivos de configuración locales ni credenciales reales: solo ejemplos públicos y el catálogo público.
- Errores: `datos\logs\errores.log`, con rotación de 1 MiB. Guarda tipo de error y ubicación del código, sin mensajes de excepción ni variables que puedan contener credenciales. Errores de Tk y de hilos también se registran.
- Instalación: Inno Setup crea su registro en `%TEMP%`; para indicar un destino concreto, el administrador de pruebas puede usar `/LOG="ruta"`.

Cierra el panel y ejecuta el nuevo instalador para actualizar. El AppId y la carpeta de datos se mantienen. El instalador solo administra los archivos del programa; no borra datos al desinstalar. Haz una copia de la carpeta persistente antes de probar una actualización. No copies configuraciones privadas al repositorio.

Si ya tienes una instalación desde código, selecciona **Sí** en el primer inicio y elige la carpeta que contiene `Config`. Se copian las cuatro configuraciones y se conserva una copia literal en `datos\configuracion-importada-original`. El mapa de rutas de la copia se adapta al paquete. No se modifica ni se borra ningún archivo del origen. No se importan automáticamente bases, reportes ni respaldos: permanecen intactos en su ubicación anterior; guarda una copia de ellos y conserva esa instalación. Si ya existe configuración en el destino, no se importa encima ni se reemplaza con el catálogo inicial. Para catálogos antiguos incompletos, la recuperación del catálogo sigue siendo una operación explícita con las herramientas existentes, nunca una sustitución automática durante una actualización.

Las credenciales existentes conservan su formato compatible con el programa actual. El archivo local de usuarios requiere protección mediante los permisos de la cuenta Windows; no compartas la carpeta de datos.

## Herramientas de desarrollo separadas

**`PanelEstacionamientos-Desarrollo-Prueba-Windows-x64.exe`** incluye los instaladores oficiales fijados de Python 3.13.9 y Git 2.51.0. Instala para el usuario actual y genera un acceso directo **Preparar entorno de desarrollo**. Ese acceso clona la rama de desarrollo en `%USERPROFILE%\source\panel-administracion-estacionamientos` y prepara `.venv`; requiere internet para clonar e instalar bibliotecas. Si la carpeta ya existe, conserva el código y no hace `pull`, `reset` ni cambia ramas. Los errores de herramientas se guardan en `%LOCALAPPDATA%\Panel-Python-Instalacion.log` y `Panel-Git-Instalacion.log`.

Desinstalar este auxiliar no elimina Python, Git ni el repositorio, porque pueden ser usados por otros proyectos. Cada herramienta tiene su propia entrada de desinstalación. Un fallo parcial puede dejar una herramienta ya instalada: consulta los registros y sus entradas en Aplicaciones.

`instalar_windows.bat` queda destinado a desarrollo; requiere Python 3.13. El instalador de usuarios finales no lo ejecuta.

## Compilar desde Linux mediante GitHub Actions

El flujo `.github/workflows/instaladores-windows.yml` se ejecuta automáticamente al subir commits a la rama de desarrollo. No crea Releases, tags ni modifica main. También puede solicitarse con **Run workflow**, si el flujo ya está registrado en la rama predeterminada. Para esta etapa basta subir a la rama de desarrollo.

Desde Linux con GitHub CLI autenticado:

```bash
git push origin desarrollo/instaladores-windows
gh run list --workflow instaladores-windows.yml --branch desarrollo/instaladores-windows
gh run download NUMERO_DE_EJECUCION --name instaladores-windows-prueba-x64 --dir instaladores-prueba
```

La compilación ocurre en `windows-2022`, con CPython 3.13.9 x64, pip 25.2, Inno Setup 6.4.3 y versiones fijadas en `deployment/windows/requirements-build.txt`. `panel.spec` incluye únicamente los cinco recursos gráficos conocidos, ejemplos de configuración, catálogo y bibliotecas; nunca empaqueta carpetas locales completas. Los instaladores oficiales de herramientas se descargan por URL versionada y se verifican mediante Authenticode y editor esperado.

El artefacto contiene ambos `.exe`, sumas SHA-256, versiones instaladas, identificación del commit, imagen del ejecutor y manifiesto de herramientas. Permanece 30 días. Las dependencias y los insumos están fijados; no se promete identidad binaria byte a byte (metadatos PE e imagen de Actions pueden variar). Para repetir una compilación conserva el commit y sus manifiestos. La compilación requiere internet; el instalador de usuarios resultante es autónomo.

Para compilar directamente en Windows: instala Python e Inno Setup de las versiones indicadas, abre PowerShell en una copia limpia del repositorio y ejecuta `deployment\windows\compilar.ps1`. Las pruebas del instalador se ejecutan con `deployment\windows\verificar_instalador.ps1` y deben hacerse en una cuenta de pruebas, porque instalan/desinstalan el paquete.

## Alcance y validación

Se conservan las vistas, controladores, reportes y funciones existentes. El cambio de rutas solo se activa en el ejecutable empaquetado. La exportación a PDF mediante Excel conserva su dependencia externa de Microsoft Excel; no se incluye Office. Las operaciones que usan bases de datos necesitan un servidor configurado posteriormente. El auxiliar privilegiado de restauración automática de Raspberry Pi continúa siendo específico de Linux; esta etapa no instala ni adapta servicios MariaDB de Windows.

Linux permite validar lógica, catálogo, importación y conservación de configuraciones. Actions verifica el ejecutable Windows, construcción real del login, imágenes, temas, calendario, apertura de catálogo sin red, edición, instalación silenciosa, accesos directos, reinstalación y desinstalación con conservación de datos. La prueba del ejecutable restringe PATH para excluir Python/Git; el runner tiene herramientas preinstaladas y no equivale a una máquina limpia.

La suite Windows excluye explícitamente `test_auxiliar_empaquetado` y `test_recuperar_catalogo`, que importan infraestructura privilegiada de Linux; ambos se ejecutan en Linux. Las aserciones de modos POSIX se omiten en Windows, donde se usan DACL.

La aceptación final necesita Windows 10 y 11 limpios: doble clic, asistente gráfico, contraseña y cancelación, login incorrecto/correcto, edición y retiro de estacionamientos, cierre y reapertura, actualización con configuraciones modificadas, desinstalación/reinstalación, funcionamiento sin internet, instalación del auxiliar de desarrollo y comprobación de errores. Ver resultados de esta entrega en `PRUEBAS_INSTALADORES_WINDOWS.md`.
