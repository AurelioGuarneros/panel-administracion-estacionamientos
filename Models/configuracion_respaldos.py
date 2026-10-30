"""Perfil de recuperación separado del catálogo y de las configuraciones existentes."""
import json
import os
from pathlib import Path
import re


def ruta_perfil():
    return Path.home() / '.config/panel-estacionamientos/recuperacion.json'


def leer_perfil(ruta=None, obligatorio=True):
    ruta = Path(ruta) if ruta else ruta_perfil()
    if not ruta.exists() and not obligatorio: return None
    if os.name != 'nt' and ruta.stat().st_mode & 0o077:
        raise ValueError('El perfil de recuperación requiere permisos 0600.')
    datos = json.loads(ruta.read_text(encoding='utf-8'))
    if datos.get('version') != 1: raise ValueError('Perfil incompatible.')
    imap = datos['imap']
    if not all(isinstance(imap.get(k),str) and imap[k] for k in ('host','usuario','password','carpeta')):
        raise ValueError('Configuración de correo incompleta.')
    if any(c in imap['host']+imap['carpeta'] for c in '\r\n'):
        raise ValueError('Servidor o carpeta IMAP inválidos.')
    if type(imap.get('puerto')) is not int or not 1 <= imap['puerto'] <= 65535:
        raise ValueError('Puerto IMAP inválido.')
    bd = datos['mariadb']
    if not str(bd['socket']).startswith('/') or not bd['socket'].endswith('.sock'):
        raise ValueError('Socket local inválido.')
    for rol in ('importador','lector'):
        if not re.fullmatch(r'panel_[a-z]+_[0-9a-f]{12}', bd[rol]['user']) or not bd[rol]['password']:
            raise ValueError('Cuenta local de recuperación inválida.')
    bases, correos = set(), set()
    for r in datos['estaciones']:
        if not re.fullmatch(r'db_[A-Za-z0-9_]+',r['database']): raise ValueError('Nombre de base inválido.')
        if r['database'].casefold() in bases or r['email'].casefold() in correos: raise ValueError('Asociación duplicada.')
        bases.add(r['database'].casefold()); correos.add(r['email'].casefold())
    return datos


def conexion_local(perfil, rol, **otros):
    return dict(unix_socket=perfil['mariadb']['socket'], **perfil['mariadb'][rol],
                charset='utf8mb4', local_infile=False, connect_timeout=15,
                read_timeout=300, write_timeout=300, **otros)


def asociacion_autorizada(perfil, registro):
    return any(r['database'] == registro['database'] and
               r['email'].casefold() == registro.get('email','').casefold()
               for r in perfil['estaciones'])
