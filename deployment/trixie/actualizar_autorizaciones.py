#!/usr/bin/python3
"""Amplía autorizaciones explícitamente; no importa datos ni configura correo."""
import argparse
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
sys.dont_write_bytecode = True
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from Models.configuracion_respaldos import leer_perfil, conexion_local
from Tools.asociaciones_recuperacion import ampliar_asociaciones, reglas_sudoers
from Tools.recuperar_catalogo import ruta_catalogo_local
from Tools.archivos_configuracion import guardar_con_respaldo
from deployment.trixie.preparar_sistema import comprobar, conceder_permisos, verificar_grants
import pymysql

class ErrorPlan(ValueError):
    """Diagnóstico controlado, sin valores privados."""


class ErrorAplicacion(RuntimeError):
    """Estado controlado de la reversión de archivos."""


RUTAS = {'helper':Path('/usr/local/sbin/panel-activar-seguro'),
         'bases':Path('/etc/panel-estacionamientos/bases-autorizadas.txt'),
         'config':Path('/etc/panel-estacionamientos/activacion.json'),
         'sudoers':Path('/etc/sudoers.d/panel-estacionamientos')}


def archivo_root(ruta):
    if ruta.is_symlink() or ruta.stat().st_uid != 0 or ruta.stat().st_mode & 0o022:
        raise ErrorPlan('Componente de activación inseguro; no se modifica.')
    return ruta.read_bytes()


def planificar(usuario, perfil_ruta, catalogo_ruta):
    if os.geteuid() != 0: raise ErrorPlan('Ejecutar mediante sudo para leer las autorizaciones.')
    cuenta = pwd.getpwnam(usuario)
    perfil_ruta = Path(perfil_ruta)
    if cuenta.pw_uid == 0 or perfil_ruta.is_symlink() or not perfil_ruta.resolve().is_relative_to(Path(cuenta.pw_dir).resolve()) or perfil_ruta.stat().st_uid != cuenta.pw_uid:
        raise ErrorPlan('El perfil debe pertenecer al usuario de la instalación.')
    perfil_bytes = perfil_ruta.read_bytes()
    perfil = leer_perfil(perfil_ruta)
    if json.loads(perfil_bytes) != perfil or perfil_ruta.read_bytes() != perfil_bytes:
        raise ErrorPlan('El perfil cambió durante la revisión; vuelve a ejecutar el diagnóstico.')
    catalogo_ruta = Path(catalogo_ruta)
    catalogo_bytes = catalogo_ruta.read_bytes()
    nuevo, agregadas = ampliar_asociaciones(perfil, json.loads(catalogo_bytes))
    archivos = {k:archivo_root(p) for k,p in RUTAS.items()}
    if archivos['helper'] != Path(__file__).with_name('panel-activar-seguro').read_bytes():
        raise ErrorPlan('El auxiliar instalado es diferente; requiere revisión.')
    cfg = json.loads(archivos['config'])
    if cfg['socket'] != perfil['mariadb']['socket'] or cfg['lector'] != perfil['mariadb']['lector']['user']:
        raise ErrorPlan('El perfil no corresponde al auxiliar instalado.')
    anteriores = [r['database'] for r in perfil['estaciones']]
    if len(anteriores) != len(set(anteriores)) or set(archivos['bases'].decode().splitlines()) != set(anteriores):
        raise ErrorPlan('La lista instalada no corresponde al perfil; se conserva.')
    lineas = archivos['sudoers'].decode().strip().splitlines()
    esperadas = reglas_sudoers(usuario,anteriores).decode().strip().splitlines()
    if len(lineas) != len(esperadas) or set(lineas) != set(esperadas):
        raise ErrorPlan('Sudoers contiene reglas distintas; se conserva sin cambios.')
    bases = anteriores + agregadas
    cambios = []
    if agregadas:
        cambios = [(RUTAS['bases'], archivos['bases'], ('\n'.join(bases)+'\n').encode()),
                   (RUTAS['sudoers'], archivos['sudoers'], reglas_sudoers(usuario,bases)),
                   (perfil_ruta, perfil_bytes, (json.dumps(nuevo,ensure_ascii=False,indent=2)+'\n').encode())]
    return {'perfil':perfil, 'nuevo':nuevo, 'agregadas':agregadas, 'cambios':cambios,
            'catalogo':catalogo_ruta, 'catalogo_bytes':catalogo_bytes, 'cuenta':cuenta,
            'dependencias':[(RUTAS['helper'],archivos['helper']),(RUTAS['config'],archivos['config'])]}


def aplicar_cambios(cambios):
    """Activar el perfil al final; ante error se intenta revertir los archivos escritos."""
    escritos, respaldos = [], []
    try:
        for ruta, antes, despues in cambios:
            respaldos.append(guardar_con_respaldo(ruta,despues,antes))
            escritos.append((ruta,antes,despues))
    except Exception:
        fallo = False
        for ruta, antes, despues in reversed(escritos):
            try: guardar_con_respaldo(ruta,antes,despues)
            except Exception: fallo = True
        if fallo: raise ErrorAplicacion('Actualización parcial: conservar los respaldos y revisar autorizaciones antes de continuar.') from None
        raise ErrorAplicacion('No se completó la ampliación; se revirtieron los archivos escritos. Los grants añadidos quedan limitados a esquemas explícitos.') from None
    return respaldos


def actualizar(usuario, perfil_ruta, catalogo_ruta, aplicar=False):
    plan = planificar(usuario,perfil_ruta,catalogo_ruta)
    if not aplicar or not plan['agregadas']: return plan['agregadas'], []
    reglas = next(despues for ruta,_,despues in plan['cambios'] if ruta == RUTAS['sudoers'])
    with tempfile.NamedTemporaryFile() as f:
        f.write(reglas); f.flush()
        if subprocess.run(['/usr/sbin/visudo','-cf',f.name],capture_output=True).returncode:
            raise ErrorPlan('La ampliación de sudoers no es válida.')
    # La GUI debe estar cerrada. Se comparte el bloqueo del actualizador.
    from Models.bloqueo_respaldos import bloqueo
    cuenta = plan['cuenta']
    directorio = Path(cuenta.pw_dir)/'.local/share/panel-estacionamientos'
    home = Path(cuenta.pw_dir)
    for carpeta in (home/'.local',home/'.local/share',directorio):
        if carpeta.is_symlink(): raise ErrorPlan('Directorio de estado enlazado; requiere revisión.')
        if not carpeta.exists():
            carpeta.mkdir(mode=0o700)
            os.chown(carpeta,cuenta.pw_uid,cuenta.pw_gid)
        if carpeta.stat().st_uid != cuenta.pw_uid:
            raise ErrorPlan('El directorio de estado debe pertenecer al usuario.')
    lock = directorio/'actualizacion.lock'
    if not lock.exists():
        fd = os.open(lock,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
        try: os.fchown(fd,cuenta.pw_uid,cuenta.pw_gid)
        finally: os.close(fd)
    if lock.is_symlink() or lock.stat().st_uid != cuenta.pw_uid:
        raise ErrorPlan('Bloqueo de actualización ajeno; requiere revisión.')
    with bloqueo(lock):
        if plan['catalogo'].read_bytes() != plan['catalogo_bytes']:
            raise ErrorPlan('El catálogo cambió; vuelve a revisar la ampliación.')
        for ruta, contenido in plan.get('dependencias',[]):
            if archivo_root(ruta) != contenido: raise ErrorPlan('El auxiliar o su configuración cambió; vuelve a revisar el plan.')
        for ruta,antes,_ in plan['cambios']:
            if ruta.read_bytes() != antes: raise ErrorPlan('La configuración cambió; vuelve a revisar la ampliación.')
        conexion = pymysql.connect(unix_socket=plan['perfil']['mariadb']['socket'],user='root',autocommit=True,local_infile=False)
        try:
            with conexion.cursor() as cursor:
                comprobar(cursor)
                verificar_grants(cursor,plan['perfil'],adicionales=plan['agregadas'])
                # Solo probar las cuentas existentes; no crear usuarios ni alterar contraseñas.
                for rol in ('importador','lector'):
                    prueba = pymysql.connect(**conexion_local(plan['perfil'],rol))
                    prueba.close()
                conceder_permisos(cursor,plan['perfil'],plan['agregadas'])
                verificar_grants(cursor,plan['nuevo'])
            respaldos = aplicar_cambios(plan['cambios'])
        finally: conexion.close()
    return plan['agregadas'], respaldos


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usuario',required=True)
    parser.add_argument('--perfil',required=True)
    parser.add_argument('--catalogo',type=Path)
    parser.add_argument('--aplicar',action='store_true')
    args = parser.parse_args()
    try:
        catalogo = args.catalogo or ruta_catalogo_local(Path(__file__).resolve().parents[2])
        bases, respaldos = actualizar(args.usuario,args.perfil,catalogo,args.aplicar)
        print('Bases a incorporar: '+(', '.join(bases) if bases else 'ninguna; asociaciones ya presentes'))
        if not args.aplicar: print('Solo diagnóstico: sin conexión MariaDB ni escrituras.')
        else: print('Ampliación completada. Respaldos privados: %d. IMAP y contraseñas conservados.' % len(respaldos))
    except (ErrorPlan,ErrorAplicacion) as error:
        print('Ampliación detenida: '+str(error))
        raise SystemExit(1)
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,pymysql.err.MySQLError):
        print('Ampliación detenida. Revisa asociaciones, componentes instalados, permisos y respaldos. No se muestran datos privados.')
        raise SystemExit(1)
