"""Recuperación explícita del catálogo; sin correo, credenciales nuevas ni MariaDB."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

if __package__ in (None, ''): sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Tools.catalogo_inicial import recuperar_catalogo
from Tools.archivos_configuracion import guardar_con_respaldo


def ruta_catalogo_local(raiz):
    raiz = Path(raiz).resolve()
    ruta = raiz/'Config/config_files/database_connection_configuration.json'
    mapa = raiz/'Config/config_files/path_files_settings.json'
    if mapa.exists():
        valor = json.loads(mapa.read_text(encoding='utf-8'))['path_files'][0]['config_files'][0]['database_config_file']
        ruta = raiz/valor
    if ruta.is_symlink() or raiz not in ruta.resolve().parents:
        raise ValueError('La configuración debe ser un archivo local de esta instalación.')
    return ruta


def plan_recuperacion(raiz):
    raiz = Path(raiz).resolve()
    ruta = ruta_catalogo_local(raiz)
    original = ruta.read_bytes()
    local = json.loads(original)
    catalogo = json.loads((raiz/'Config/catalogo_inicial.json').read_text(encoding='utf-8'))
    plantilla = json.loads((raiz/'Config/config_files/database_connection_configuration.json.example').read_text(encoding='utf-8'))
    datos, resumen = recuperar_catalogo(local, catalogo, plantilla)
    return ruta, original, local, datos, resumen


def ejecutar(raiz, aplicar=False):
    ruta, original, local, datos, resumen = plan_recuperacion(raiz)
    respaldo = None
    if aplicar and datos != local:
        contenido = (json.dumps(datos, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
        respaldo = guardar_con_respaldo(ruta, contenido, original)
    return resumen, respaldo


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aplicar', action='store_true', help='Guardar con respaldo; sin esta opción solo se muestra el plan.')
    args = parser.parse_args()
    try:
        resumen, respaldo = ejecutar(Path(__file__).resolve().parents[1], args.aplicar)
        print('Plan: %d altas, %d reservas de retirados, %d ejemplos sin cambios a retirar, %d identidades conservadas u omitidas.' % tuple(len(resumen[k]) for k in ('agregados','retirados','ejemplos_eliminados','omitidos')))
        if respaldo: print('Catálogo recuperado. Respaldo privado:', respaldo)
        else: print('Sin escrituras.' if not args.aplicar else 'El catálogo ya coincide; se conservó el archivo sin cambios.')
    except (OSError, ValueError, KeyError, TypeError):
        print('Recuperación detenida: revisa ruta, estructura, permisos o conflictos del catálogo. No se muestran datos privados.')
        raise SystemExit(1)
