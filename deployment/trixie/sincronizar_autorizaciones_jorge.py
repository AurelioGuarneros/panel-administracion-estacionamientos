#!/usr/bin/env python3
"""Reconciliación puntual de autorizaciones en Raspberry; no altera bases ni correos.

Solo acepta la discrepancia diagnosticada en noviembre de 2026. Por defecto
hace un diagnóstico sin escrituras. --aplicar requiere confirmación explícita.
"""
import argparse
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pymysql
from Models.configuracion_respaldos import leer_perfil, conexion_local
from Tools.asociaciones_recuperacion import reglas_sudoers
from deployment.trixie.actualizar_autorizaciones import aplicar_cambios
from deployment.trixie.actualizar_autorizaciones import RUTAS, archivo_root
from deployment.trixie.preparar_sistema import comprobar, verificar_grants, conceder_permisos

AGREGAR = {'db_ciudad_mendoza'}
RETIRAR = {'db_amores_1003', 'db_durango_205', 'db_tenayuca_200'}


def preparar(usuario, ruta):
    if os.geteuid() != 0:
        raise ValueError('Se requiere sudo.')
    cuenta = pwd.getpwnam(usuario)
    ruta = Path(ruta)
    if (cuenta.pw_uid == 0 or ruta.is_symlink()
            or ruta.stat().st_uid != cuenta.pw_uid
            or not ruta.resolve().is_relative_to(Path(cuenta.pw_dir).resolve())):
        raise ValueError('Perfil de otro usuario o enlace no permitido.')
    perfil_bytes = ruta.read_bytes()
    perfil = leer_perfil(ruta)
    bases = [e['database'] for e in perfil['estaciones']]
    if len(bases) != len(set(bases)) or len(bases) != 10 or not AGREGAR.issubset(bases):
        raise ValueError('El perfil no coincide con las 10 estaciones esperadas.')
    if RETIRAR.intersection(bases):
        raise ValueError('Una estación retirada aún aparece en el perfil; detener.')
    archivos = {k: archivo_root(p) for k, p in RUTAS.items()}
    instaladas = archivos['bases'].decode().splitlines()
    if len(instaladas) != len(set(instaladas)):
        raise ValueError('Lista instalada duplicada.')
    if set(bases) - set(instaladas) != AGREGAR or set(instaladas) - set(bases) != RETIRAR:
        raise ValueError('Las diferencias ya cambiaron; no aplicar este ajuste puntual.')
    if archivos['helper'] != Path(__file__).with_name('panel-activar-seguro').read_bytes():
        raise ValueError('El auxiliar instalado es distinto.')
    config = json.loads(archivos['config'])
    if config.get('socket') != perfil['mariadb']['socket'] or config.get('lector') != perfil['mariadb']['lector']['user']:
        raise ValueError('Configuración del auxiliar no corresponde al perfil.')
    esperadas = reglas_sudoers(usuario, instaladas).decode().strip().splitlines()
    actuales = archivos['sudoers'].decode().strip().splitlines()
    if len(actuales) != len(esperadas) or set(actuales) != set(esperadas):
        raise ValueError('Sudoers contiene otras reglas; detener.')
    nuevas = reglas_sudoers(usuario, bases)
    with tempfile.NamedTemporaryFile() as f:
        f.write(nuevas)
        f.flush()
        if subprocess.run(['/usr/sbin/visudo', '-cf', f.name], capture_output=True).returncode:
            raise ValueError('Reglas sudoers inválidas.')
    if ruta.read_bytes() != perfil_bytes:
        raise ValueError('Perfil cambió durante diagnóstico.')
    return perfil, bases, instaladas, archivos, nuevas, ruta, perfil_bytes


def ejecutar(usuario, ruta, aplicar=False):
    perfil, bases, instaladas, archivos, nuevas, ruta, perfil_bytes = preparar(usuario, ruta)
    print('Incorporar autorización:', ', '.join(sorted(AGREGAR)))
    print('Retirar autorizaciones:', ', '.join(sorted(RETIRAR)))
    print('Conservar estaciones:', len(bases))
    if not aplicar:
        print('SOLO DIAGNÓSTICO: no se modificaron archivos ni permisos.')
        return
    # Bloquea el actualizador mientras se cambian autorizaciones.
    from Models.bloqueo_respaldos import bloqueo
    lock = Path(pwd.getpwnam(usuario).pw_dir) / '.local/share/panel-estacionamientos/actualizacion.lock'
    if lock.is_symlink() or not lock.is_file():
        raise ValueError('No existe el bloqueo seguro del actualizador.')
    with bloqueo(lock):
        preparar(usuario, ruta)  # Revalidar estado antes de escribir.
        # Exigir permisos completos solo en las estaciones vigentes.
        # Admitir temporalmente las autorizaciones retiradas sin exigir que estén completas.
        conexion = pymysql.connect(
            unix_socket=perfil['mariadb']['socket'],
            user='root', autocommit=True, local_infile=False)
        try:
            with conexion.cursor() as cursor:
                comprobar(cursor)
                verificar_grants(cursor, perfil, adicionales=AGREGAR | RETIRAR)
                for rol in ('importador', 'lector'):
                    prueba = pymysql.connect(**conexion_local(perfil, rol))
                    prueba.close()
                # Primero otorgar Ciudad Mendoza; nunca DROP DATABASE.
                conceder_permisos(cursor, perfil, sorted(AGREGAR))
                # Revocar solo privilegios de los esquemas expresamente retirados.
                imp = perfil['mariadb']['importador']['user']
                lect = perfil['mariadb']['lector']['user']
                for base in sorted(RETIRAR):
                    stage = ('panel_stage_' + base).replace('_', r'\_')
                    lector = base.replace('_', r'\_')
                    cursor.execute(
                        f"REVOKE ALL PRIVILEGES ON `{stage}`.* FROM '{imp}'@'localhost'")
                    cursor.execute(
                        f"REVOKE ALL PRIVILEGES ON `{lector}`.* FROM '{lect}'@'localhost'")
                verificar_grants(cursor, perfil)
            # Escribir configuración instalada con respaldos privados.
            # No cambiar el perfil: ya tiene Ciudad Mendoza.
            cambios = [
                (RUTAS['bases'], archivos['bases'], ('\n'.join(bases) + '\n').encode()),
                (RUTAS['sudoers'], archivos['sudoers'], nuevas),
            ]
            respaldos = aplicar_cambios(cambios)
            print('Autorizaciones sincronizadas. Perfil IMAP y contraseñas intactos.')
            print('Respaldos privados creados:', len(respaldos))
            print('No se eliminaron ni importaron bases de datos.')
        finally:
            conexion.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usuario', required=True)
    parser.add_argument('--perfil', required=True)
    parser.add_argument('--aplicar', action='store_true')
    args = parser.parse_args()
    try:
        ejecutar(args.usuario, args.perfil, args.aplicar)
    except Exception as e:
        print('Operación detenida:', type(e).__name__, str(e)
              if isinstance(e, ValueError) else 'revisar permisos y estado; no repetir a ciegas.')
        raise SystemExit(1)
