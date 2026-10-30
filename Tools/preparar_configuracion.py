"""Prepara únicamente configuraciones ausentes, sin servicios externos."""
import getpass
import json
import os
from pathlib import Path

if __package__:
    from .catalogo_inicial import configurar_catalogo
else:
    from catalogo_inicial import configurar_catalogo

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVOS = (
    'path_files_settings.json',
    'user_settings.json',
    'database_connection_configuration.json',
    'system_settings.json',
)


def preparar_configuracion(raiz=RAIZ, pedir_clave=getpass.getpass):
    carpeta = Path(raiz) / 'Config' / 'config_files'
    pendientes = {}
    for nombre in ARCHIVOS:
        destino = carpeta / nombre
        if destino.exists():
            continue
        datos = json.loads((carpeta / (nombre + '.example')).read_text(encoding='utf-8'))
        pendientes[nombre] = datos

    nombre_catalogo = 'database_connection_configuration.json'
    if nombre_catalogo in pendientes:
        catalogo = json.loads((Path(raiz) / 'Config/catalogo_inicial.json').read_text(encoding='utf-8'))
        pendientes[nombre_catalogo] = configurar_catalogo(pendientes[nombre_catalogo], catalogo)

    if 'user_settings.json' in pendientes:
        clave = pedir_clave('Contraseña local para el administrador Aurelio: ')
        confirmacion = pedir_clave('Repite la contraseña: ')
        if not clave or clave != confirmacion:
            raise ValueError('La contraseña debe tener contenido y coincidir con su confirmación.')
        usuario = pendientes['user_settings.json']['ussers'][0]
        usuario.update(UserName='Aurelio', Name='Aurelio', Password=clave, Permits='admin')

    creados = []
    for nombre, datos in pendientes.items():
        destino = carpeta / nombre
        try:
            descriptor = os.open(destino, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            # Otra ejecución pudo crear el archivo después de la comprobación.
            continue
        with os.fdopen(descriptor, 'w', encoding='utf-8') as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
            archivo.write('\n')
        creados.append(nombre)
    return creados


def main():
    try:
        creados = preparar_configuracion()
    except (OSError, ValueError, EOFError):
        # No imprimir excepciones que puedan incluir contenido de configuraciones.
        print('No se pudo preparar la configuración. Comprueba los ejemplos, permisos y la confirmación de contraseña.')
        return 1
    print('Configuraciones creadas: ' + (', '.join(creados) if creados else 'ninguna; se conservaron las existentes'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
