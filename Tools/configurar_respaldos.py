"""Configuración interactiva local; no conecta a correo ni a MariaDB."""
import getpass
import json
import os
from pathlib import Path
import secrets
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Models.configuracion_respaldos import ruta_perfil, leer_perfil
from Tools.catalogo_inicial import validar_catalogo


def configurar(raiz=None, destino=None, entrada=input, clave=getpass.getpass):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parents[1]
    destino = Path(destino) if destino else ruta_perfil()
    if destino.exists(): raise FileExistsError('El perfil ya existe; se conserva sin cambios.')
    datos = json.loads((raiz / 'Config/config_files/database_connection_configuration.json').read_text(encoding='utf-8'))
    estaciones = [r for r in datos['settings'] if r['name_config'] != 'Admin']
    # Aplicar las mismas reglas de identidad pública sin copiar conexiones privadas.
    publico = {'version':1,'settings':[], 'estacionamientos_eliminados':[]}
    for r in estaciones:
        publico['settings'].append({k:r.get(k, True if k=='activo' else r['database'] if k=='id' else '')
                                   for k in ('id','name_config','database','email','activo')})
    for r in datos.get('estacionamientos_eliminados',[]):
        publico['estacionamientos_eliminados'].append({k:r.get(k,r['database'] if k=='id' else '')
                                                       for k in ('id','name_config','database')})
    validar_catalogo(publico)
    estaciones = [r for r in publico['settings'] if r['activo']]
    host = entrada('Servidor IMAP TLS: ').strip()
    puerto = int(entrada('Puerto IMAP [993]: ').strip() or '993')
    usuario = entrada('Usuario del correo receptor: ').strip()
    password = clave('Contraseña del correo receptor: ')
    carpeta = entrada('Carpeta IMAP [INBOX]: ').strip() or 'INBOX'
    socket = entrada('Socket MariaDB [/run/mysqld/mysqld.sock]: ').strip() or '/run/mysqld/mysqld.sock'
    sufijo = secrets.token_hex(6)
    perfil = {'version':1,'imap':{'host':host,'puerto':puerto,'usuario':usuario,'password':password,'carpeta':carpeta},
              'mariadb':{'socket':socket,
                         'importador':{'user':'panel_imp_'+sufijo,'password':secrets.token_hex(32)},
                         'lector':{'user':'panel_lect_'+sufijo,'password':secrets.token_hex(32)}},
              'estaciones':estaciones}
    destino.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with os.fdopen(os.open(destino, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600),'w',encoding='utf-8') as f:
        json.dump(perfil,f,ensure_ascii=False,indent=2)
    try: leer_perfil(destino)
    except Exception:
        destino.unlink()
        raise
    return destino


if __name__ == '__main__':
    try:
        print('Perfil local creado:', configurar())
        print('No se modificó el catálogo ni se conectó a servicios. Sigue la preparación Trixie.')
    except (OSError,ValueError,KeyError,EOFError):
        print('No se creó el perfil. Revisa permisos, datos y si ya existe una configuración; no se sobrescribe.')
        raise SystemExit(1)
