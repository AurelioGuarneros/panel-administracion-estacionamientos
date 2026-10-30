#!/usr/bin/python3
"""Preparación explícita en Raspberry. Nunca descarga correo ni importa respaldos."""
import argparse
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from Models.configuracion_respaldos import leer_perfil, conexion_local
import pymysql


def escribir_exclusivo(ruta, contenido, modo):
    ruta = Path(ruta)
    if ruta.exists():
        if ruta.read_bytes() != contenido:
            raise RuntimeError('Hay un componente previo diferente: se conserva; revisar antes de continuar.')
        if ruta.stat().st_uid != 0 or ruta.stat().st_mode & 0o022:
            raise RuntimeError('Permisos inseguros en componente previo.')
        return
    with os.fdopen(os.open(ruta,os.O_WRONLY|os.O_CREAT|os.O_EXCL,modo),'wb') as f:
        f.write(contenido)


def comprobar(cursor):
    cursor.execute('SELECT VERSION(),@@lower_case_table_names')
    version, minusculas = cursor.fetchone()
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
    if not match or 'MariaDB' not in version or tuple(map(int,match.groups())) < (10,6,1):
        raise RuntimeError('Se requiere MariaDB >= 10.6.1 para activación atómica.')
    if minusculas != 0:
        raise RuntimeError('Se requiere lower_case_table_names=0 para conservar los nombres exactos. No se cambia el servidor.')


def verificar_grants(cursor, perfil):
    for rol in ('importador','lector'):
        usuario=perfil['mariadb'][rol]['user']
        cursor.execute('SHOW GRANTS FOR %s@localhost',(usuario,))
        permitidos=({'CREATE','DROP','INSERT','SELECT','ALTER','INDEX','REFERENCES'} if rol=='importador' else {'SELECT','SHOW VIEW'})
        prefijo='panel_stage_' if rol=='importador' else ''
        esquemas={prefijo+r['database'] for r in perfil['estaciones']}
        vistos={}
        for (grant,) in cursor.fetchall():
            if 'WITH GRANT OPTION' in grant: raise RuntimeError('No se permite delegar privilegios.')
            m=re.match(r'GRANT (.*?) ON (.*?) TO ',grant)
            if not m: raise RuntimeError('Grants no reconocidos.')
            privilegios={p.strip() for p in m[1].split(',')}
            if privilegios=={'USAGE'} and m[2]=='*.*': continue
            esquema=m[2].removesuffix('.*').strip('`').replace('\\','')
            if not privilegios.issubset(permitidos) or esquema not in esquemas or 'WITH GRANT OPTION' in grant:
                raise RuntimeError('Cuenta de recuperación con permisos excesivos.')
            vistos.setdefault(esquema,set()).update(privilegios)
        if any(not permitidos.issubset(vistos.get(esquema,set())) for esquema in esquemas):
            raise RuntimeError('Faltan permisos de recuperación por esquema.')


def preparar(usuario, perfil_ruta, instalar=False):
    if os.geteuid() != 0: raise RuntimeError('Ejecutar con sudo solo durante la preparación.')
    cuenta = pwd.getpwnam(usuario)
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*',usuario) or cuenta.pw_uid == 0: raise ValueError('Usuario Linux inválido.')
    perfil_ruta = Path(perfil_ruta).resolve()
    if not perfil_ruta.is_relative_to(Path(cuenta.pw_dir).resolve()) or perfil_ruta.stat().st_uid != cuenta.pw_uid:
        raise ValueError('El perfil debe pertenecer al usuario y estar en su carpeta personal.')
    perfil = leer_perfil(perfil_ruta)
    for comando in ('mariadb','mariadb-dump','visudo','sudo'):
        if not shutil.which(comando): raise RuntimeError('Falta una dependencia del sistema.')
    helper = Path(__file__).with_name('panel-activar-seguro').read_bytes()
    compile(helper,'panel-activar-seguro','exec')
    conexion = pymysql.connect(unix_socket=perfil['mariadb']['socket'],user='root',autocommit=True,local_infile=False)
    try:
        with conexion.cursor() as cursor:
            comprobar(cursor)
            if not instalar:
                print('MariaDB local accesible, versión y mayúsculas compatibles. No se realizaron cambios.')
                return
            cfg = Path('/etc/panel-estacionamientos')
            cfg.mkdir(mode=0o755,exist_ok=True)
            if cfg.stat().st_uid != 0 or cfg.stat().st_mode & 0o022:
                raise RuntimeError('Directorio de activación inseguro.')
            estado = Path('/var/lib/panel-estacionamientos')
            estado.mkdir(mode=0o755,exist_ok=True)
            if estado.stat().st_uid != 0 or estado.stat().st_mode & 0o022:
                raise RuntimeError('Directorio de registro inseguro.')
            (estado/'activaciones').mkdir(mode=0o755,exist_ok=True)
            Path('/var/backups/panel-estacionamientos').mkdir(mode=0o700,parents=True,exist_ok=True)
            bases = [r['database'] for r in perfil['estaciones']]
            if not bases: raise ValueError('No hay estaciones autorizadas.')
            contenido_allow = ('\n'.join(bases)+'\n').encode()
            config_helper = (json.dumps({'socket':perfil['mariadb']['socket'],'lector':perfil['mariadb']['lector']['user']},sort_keys=True)+'\n').encode()
            reglas = ('\n'.join(usuario+' ALL=(root) NOPASSWD: /usr/local/sbin/panel-activar-seguro '+'^'+base+' [0-9a-f]{64}$' for base in bases)+'\n').encode()
            # El único argumento variable es la huella; el helper exige exactamente 64 hexadecimales.
            import tempfile
            with tempfile.NamedTemporaryFile() as f:
                f.write(reglas);f.flush()
                if subprocess.run(['/usr/sbin/visudo','-cf',f.name],capture_output=True).returncode:
                    raise RuntimeError('Reglas sudoers inválidas.')
            previstos = [('/usr/local/sbin/panel-activar-seguro',helper,0o755),
                         (cfg/'bases-autorizadas.txt',contenido_allow,0o644),
                         (cfg/'activacion.json',config_helper,0o644),
                         ('/etc/sudoers.d/panel-estacionamientos',reglas,0o440)]
            for ruta,contenido,modo in previstos:
                if Path(ruta).exists() and Path(ruta).read_bytes()!=contenido:
                    raise RuntimeError('Existe una instalación anterior distinta. Se conserva sin sobrescribir.')
            for rol in ('importador','lector'):
                cred = perfil['mariadb'][rol]
                cursor.execute('CREATE USER IF NOT EXISTS %s@localhost IDENTIFIED BY %s',(cred['user'],cred['password']))
            for base in bases:
                # '_' es comodín en GRANT incluso con backticks: escapar cada uno.
                temporal = ('panel_stage_'+base).replace('_',r'\_')
                lector = base.replace('_',r'\_')
                imp = perfil['mariadb']['importador']['user']
                lect = perfil['mariadb']['lector']['user']
                cursor.execute(f"GRANT CREATE, DROP, INSERT, SELECT, ALTER, INDEX, REFERENCES ON `{temporal}`.* TO '{imp}'@'localhost'")
                cursor.execute(f"GRANT SELECT, SHOW VIEW ON `{lector}`.* TO '{lect}'@'localhost'")
            verificar_grants(cursor,perfil)
            for rol in ('importador','lector'):
                prueba = pymysql.connect(**conexion_local(perfil,rol))
                prueba.close()
            for ruta,contenido,modo in previstos: escribir_exclusivo(ruta,contenido,modo)
            if subprocess.run(['/usr/sbin/visudo','-cf','/etc/sudoers.d/panel-estacionamientos'],capture_output=True).returncode:
                raise RuntimeError('No se pudo verificar sudoers.')
            print('Auxiliar, cuentas y permisos preparados. No se descargó ni importó ningún respaldo.')
    finally:
        conexion.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--usuario',required=True)
    parser.add_argument('--perfil',required=True)
    parser.add_argument('--instalar',action='store_true')
    args = parser.parse_args()
    try: preparar(args.usuario,args.perfil,args.instalar)
    except Exception:
        print('Preparación detenida. Revisa servicio MariaDB, dependencias, perfil y componentes previos. No se muestran secretos.')
        raise SystemExit(1)
