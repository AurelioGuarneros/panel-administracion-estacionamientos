"""
Actualizador de respaldos del Panel de Estacionamientos.

Consulta IMAP de solo lectura, descarga validada, restauración temporal y activación local.
"""

import json
import imaplib
import email
import sqlite3
import time
from pathlib import Path

from Config.config_database import DatabaseConfig
from Models.estacionamientos_config import resolver_registro
from activador_respaldos import verificar_integridad
from Models.configuracion_respaldos import leer_perfil, conexion_local, asociacion_autorizada
from Models.sql_respaldo import sql_validado, MAX_ZIP
import hashlib
import re
import os
import tempfile
import contextlib
import ssl
import zipfile




def huella_archivo(ruta):
    huella = hashlib.sha256()
    with Path(ruta).open('rb') as f:
        for bloque in iter(lambda:f.read(1024*1024),b''): huella.update(bloque)
    return huella.hexdigest()


class ActualizadorRespaldos:

    INTERVALO_COMPROBACION = 1800  # 30 minutos

    def __init__(self, config_path=None, directorio=None, perfil=None):
        self.configuracion = DatabaseConfig()
        if config_path is not None:
            self.configuracion.database_config_file = str(config_path)
        self.perfil = perfil if perfil is not None else leer_perfil(obligatorio=False)

        self.directorio = (
            Path.home()
            / ".local"
            / "share"
            / "panel-estacionamientos"
        )

        if directorio is not None:
            self.directorio = Path(directorio)

        self.directorio.mkdir(
            parents=True,
            exist_ok=True
        )

        self.archivo_estado = (
            self.directorio / "actualizaciones.sqlite3"
        )

        self.inicializar_registro()

    def conectar_registro(self):
        return sqlite3.connect(self.archivo_estado)

    def inicializar_registro(self):
        with self.conectar_registro() as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS actualizaciones (
                    estacionamiento TEXT PRIMARY KEY,
                    ultimo_respaldo TEXT,
                    ultima_comprobacion REAL DEFAULT 0,
                    estado TEXT DEFAULT 'Sin actualizar'
                )
            """)

    def inicializar_importaciones(self):
        """Registra únicamente respaldos instalados correctamente."""
        with self.conectar_registro() as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS importaciones (
                    estacionamiento TEXT PRIMARY KEY,
                    uid_importado TEXT NOT NULL,
                    fecha_importacion REAL NOT NULL,
                    archivo TEXT NOT NULL
                )
            """)

    def obtener_ultima_importacion(self, estacionamiento):
        estacionamiento = self.clave_registro(estacionamiento)
        self.inicializar_importaciones()

        with self.conectar_registro() as conexion:
            fila = conexion.execute("""
                SELECT uid_importado, fecha_importacion, archivo
                FROM importaciones
                WHERE estacionamiento = ?
            """, (estacionamiento,)).fetchone()

        if fila is None:
            return None

        return {
            "uid": fila[0],
            "fecha": fila[1],
            "archivo": fila[2]
        }

    def registrar_importacion(self, estacionamiento, uid, archivo, fecha=None):
        """Llamar solamente después de activar y validar la base."""
        estacionamiento = self.clave_registro(estacionamiento)
        self.inicializar_importaciones()

        with self.conectar_registro() as conexion:
            conexion.execute("""
                INSERT INTO importaciones (
                    estacionamiento,
                    uid_importado,
                    fecha_importacion,
                    archivo
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(estacionamiento)
                DO UPDATE SET
                    uid_importado = excluded.uid_importado,
                    fecha_importacion = excluded.fecha_importacion,
                    archivo = excluded.archivo
            """, (
                estacionamiento,
                str(uid),
                fecha if fecha is not None else time.time(),
                str(archivo)
            ))


    def registrar_preparacion(self, estacionamiento, uid, archivo, base_temporal):
        """Registra un respaldo validado en una base temporal."""
        estacionamiento = self.clave_registro(estacionamiento)
        self.inicializar_importaciones()

        with self.conectar_registro() as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS preparaciones (
                    estacionamiento TEXT PRIMARY KEY,
                    uid TEXT NOT NULL,
                    archivo TEXT NOT NULL,
                    base_temporal TEXT NOT NULL,
                    fecha REAL NOT NULL
                )
            """)

            conexion.execute("""
                INSERT INTO preparaciones
                    (estacionamiento, uid, archivo, base_temporal, fecha)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(estacionamiento)
                DO UPDATE SET
                    uid = excluded.uid,
                    archivo = excluded.archivo,
                    base_temporal = excluded.base_temporal,
                    fecha = excluded.fecha
            """, (
                estacionamiento,
                str(uid),
                str(archivo),
                base_temporal,
                time.time()
            ))

    def obtener_ultima_preparacion(self, estacionamiento):
        """Consulta qué UID fue restaurado y validado temporalmente."""
        estacionamiento = self.clave_registro(estacionamiento)
        self.inicializar_importaciones()

        with self.conectar_registro() as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS preparaciones (
                    estacionamiento TEXT PRIMARY KEY,
                    uid TEXT NOT NULL,
                    archivo TEXT NOT NULL,
                    base_temporal TEXT NOT NULL,
                    fecha REAL NOT NULL
                )
            """)

            fila = conexion.execute("""
                SELECT uid, archivo, base_temporal, fecha
                FROM preparaciones
                WHERE estacionamiento = ?
            """, (estacionamiento,)).fetchone()

        if fila is None:
            return None

        return {
            "uid": fila[0],
            "archivo": fila[1],
            "base_temporal": fila[2],
            "fecha": fila[3]
        }

    def listar_estacionamientos(self):
        archivo = self.configuracion.database_config_file

        with open(archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)

        retirados = datos.get('estacionamientos_eliminados', [])
        reservadas = {r['database'].casefold() for r in retirados}
        remitentes = [r.get('email','').strip().casefold() for r in datos['settings'] if r['name_config'] != 'Admin']
        if any(not re.fullmatch(r'[a-z0-9_.+%\-]+@[a-z0-9.\-]+\.[a-z]{2,}',e) for e in remitentes):
            raise ValueError('Remitente inválido en catálogo.')
        if len(remitentes) != len(set(remitentes)):
            raise ValueError('Remitentes duplicados: corrige el catálogo antes de descargar.')
        return [
            {
                "nombre": item["name_config"],
                "database": item["database"],
                "email": item["email"]
            }
            for item in datos["settings"]
            if item["name_config"] != "Admin" and item["database"].casefold() not in reservadas and item.get("activo", True) and (
                (asociacion_autorizada(self.perfil, item) if getattr(self, 'perfil', None) else
                 item.get("actualizacion_automatica", True) and item.get("configuracion_verificada", True))
            )
        ]

    def clave_registro(self, nombre):
        # El historial conserva su clave original aunque cambie el nombre visible.
        with open(self.configuracion.database_config_file, encoding='utf-8') as archivo:
            registro = resolver_registro(json.load(archivo), nombre)
        return registro.get('clave_respaldo', registro['name_config'])

    def obtener_estado(self, estacionamiento):
        estacionamiento = self.clave_registro(estacionamiento)
        with self.conectar_registro() as conexion:
            fila = conexion.execute("""
                SELECT
                    ultimo_respaldo,
                    ultima_comprobacion,
                    estado
                FROM actualizaciones
                WHERE estacionamiento = ?
            """, (estacionamiento,)).fetchone()

        if fila is None:
            return {
                "ultimo_respaldo": None,
                "ultima_comprobacion": None,
                "estado": "Sin actualizar"
            }

        return {
            "ultimo_respaldo": fila[0],
            "ultima_comprobacion": fila[1],
            "estado": fila[2]
        }

    def necesita_comprobacion(self, estacionamiento):
        estado = self.obtener_estado(estacionamiento)

        ultima = estado["ultima_comprobacion"]

        if ultima is None:
            return True

        return (
            time.time() - ultima
            >= self.INTERVALO_COMPROBACION
        )


    def _correo(self):
        perfil = getattr(self, 'perfil', None)
        if not perfil:
            raise ValueError('Configura el perfil local de recuperación antes de consultar el correo.')
        cfg = perfil['imap']
        conexion = imaplib.IMAP4_SSL(cfg['host'], cfg['puerto'], timeout=60, ssl_context=ssl.create_default_context())
        try:
            conexion.login(cfg['usuario'], cfg['password'])
            carpeta = cfg['carpeta']
            if any(c.isspace() or c in '\\"' for c in carpeta):
                carpeta = '"'+carpeta.replace('\\','\\\\').replace('"','\\"')+'"'
            estado, _ = conexion.select(carpeta, readonly=True)
            if estado != 'OK': raise RuntimeError('No se pudo abrir la carpeta de correo.')
            return conexion
        except Exception:
            with contextlib.suppress(Exception): conexion.logout()
            raise

    def consultar_respaldos_correo(self):
        resultados = {}
        for estacion in self.listar_estacionamientos():
            nombre = estacion['nombre']
            try:
                respaldo = self.descargar_respaldo(nombre)
                resultados[nombre] = dict(respaldo, estado='Encontrado')
            except Exception:
                resultados[nombre] = {'estado':'Error al consultar o validar respaldo', 'fecha':None, 'uid':None}
        return resultados

    def registrar_comprobacion(self, estacionamiento, estado):
        """
        Registra una consulta al correo.
        No significa que el respaldo esté instalado.
        """
        estacionamiento = self.clave_registro(estacionamiento)
        with self.conectar_registro() as conexion:
            conexion.execute("""
                INSERT INTO actualizaciones (
                    estacionamiento,
                    ultima_comprobacion,
                    estado
                )
                VALUES (?, ?, ?)
                ON CONFLICT(estacionamiento)
                DO UPDATE SET
                    ultima_comprobacion = excluded.ultima_comprobacion,
                    estado = excluded.estado
            """, (
                estacionamiento,
                time.time(),
                estado
            ))

    def comprobar_todos(self):
        """
        Consulta el correo de los estacionamientos activos
        y registra los resultados.
        Descarga y valida ZIP; no restaura bases de datos.
        """
        resultados = self.consultar_respaldos_correo()

        for nombre, informacion in resultados.items():
            estado = informacion["estado"]

            if estado == "Encontrado":
                estado = "Correo encontrado; pendiente de importar"

            self.registrar_comprobacion(nombre, estado)

        return resultados


    def registrar_evento(self, nombre, fase, estado, respaldo=None):
        clave = self.clave_registro(nombre)
        respaldo = respaldo or {}
        with self.conectar_registro() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS eventos_respaldos (
                id INTEGER PRIMARY KEY, estacionamiento TEXT, fecha REAL, fase TEXT,
                estado TEXT, uid TEXT, buzon TEXT, archivo TEXT, sha256 TEXT, recepcion REAL)""")
            c.execute('INSERT INTO eventos_respaldos VALUES (NULL,?,?,?,?,?,?,?,?,?)',
                      (clave,time.time(),fase,estado,str(respaldo.get('uid','')),
                       respaldo.get('buzon',''),str(respaldo.get('archivo','')),respaldo.get('sha256',''),respaldo.get('recepcion')))
        self.registrar_comprobacion(nombre, estado)

    def descargar_respaldo(self, nombre):
        """Busca por UID descendente; valida remitente, CRC, estructura y SQL sin ejecutar."""
        from email.utils import parseaddr
        estaciones = {e['nombre']:e for e in self.listar_estacionamientos()}
        if nombre not in estaciones: raise ValueError('Estacionamiento no activo o desconocido')
        estacion = estaciones[nombre]
        base = estacion['database']
        if not re.fullmatch(r'db_[A-Za-z0-9_]+',base): raise ValueError('Nombre de base no permitido')
        conexion = None
        try:
            conexion = self._correo()
            estado, datos = conexion.uid('search', None, 'FROM', '"'+estacion['email']+'"')
            if estado != 'OK' or not datos or not datos[0]: raise RuntimeError('No se encontraron correos')
            uids = sorted((u for u in datos[0].split() if u.isdigit()),key=int,reverse=True)
            cfg = self.perfil['imap']
            validez = conexion.response('UIDVALIDITY')[1]
            buzon = hashlib.sha256((cfg['host']+':'+str(cfg['puerto'])+':'+cfg['usuario']+':'+cfg['carpeta']+':'+str(validez)).encode()).hexdigest()
            for uid in uids:
                # RFC822.SIZE permite rechazar mensajes desmesurados antes de traer el cuerpo.
                estado, tam = conexion.uid('fetch', uid, '(RFC822.SIZE)')
                cabecera = b' '.join(x for x in tam if isinstance(x,bytes)) if tam else b''
                tamanos = re.findall(rb'RFC822.SIZE (\d+)',cabecera)
                if estado != 'OK' or not tamanos or int(tamanos[0]) > MAX_ZIP*2:
                    continue
                estado, mensajes = conexion.uid('fetch', uid, '(INTERNALDATE BODY.PEEK[])')
                if estado != 'OK': continue
                contenido = next((x[1] for x in mensajes if isinstance(x,tuple)),None)
                if not contenido: continue
                recibido = next((imaplib.Internaldate2tuple(x[0]) for x in mensajes if isinstance(x,tuple)),None)
                mensaje = email.message_from_bytes(contenido)
                origenes = mensaje.get_all('From', [])
                if len(origenes) != 1 or parseaddr(origenes[0])[1].casefold() != estacion['email'].casefold(): continue
                for parte in mensaje.walk():
                    if not (parte.get_filename() or '').lower().endswith('.zip'): continue
                    datos_zip = parte.get_payload(decode=True)
                    if not datos_zip or len(datos_zip)>MAX_ZIP: continue
                    carpeta = self.directorio / 'respaldos' / base
                    carpeta.mkdir(parents=True,exist_ok=True,mode=0o700)
                    with tempfile.NamedTemporaryFile(dir=carpeta,prefix='.descarga_',delete=False) as tmp:
                        ruta = Path(tmp.name); tmp.write(datos_zip)
                    try:
                        # Prevalidar el SQL completo antes de cualquier conexión MariaDB.
                        for _ in sql_validado(ruta,base): pass
                        sha = hashlib.sha256(datos_zip).hexdigest()
                        destino = carpeta / ('respaldo_uid_'+uid.decode()+'_'+sha[:16]+'.zip')
                        os.replace(ruta,destino)
                        respaldo = {'estacionamiento':nombre,'database':base,'uid':uid.decode(),
                                    'buzon':buzon,'archivo':str(destino),'sha256':sha,
                                    'fecha':mensaje.get('Date',''),'recepcion':time.mktime(recibido) if recibido else None}
                        self.registrar_evento(nombre,'descarga','ZIP y SQL validados',respaldo)
                        return respaldo
                    except (ValueError,UnicodeError, zipfile.BadZipFile, RuntimeError):
                        continue
                    finally:
                        ruta.unlink(missing_ok=True)
            raise RuntimeError('No se encontró respaldo válido en el correo.')
        except Exception:
            with contextlib.suppress(Exception):
                self.registrar_evento(nombre,'descarga','Error de actualización; revisar configuración, correo o temporal')
            raise
        finally:
            if conexion is not None:
                with contextlib.suppress(Exception): conexion.logout()

    def recibo_activacion(self, base):
        """La marca viaja atómicamente con las tablas; no depender solo del SQLite."""
        import pymysql
        if not re.fullmatch(r'db_[A-Za-z0-9_]+',base): raise ValueError('Base inválida.')
        try:
            conexion = pymysql.connect(**conexion_local(self.perfil,'lector',database=base))
            try:
                with conexion.cursor() as c:
                    c.execute('SELECT sha256, UNIX_TIMESTAMP(activado) FROM `_panel_respaldo`')
                    fila = c.fetchone()
                return {'sha256':fila[0],'fecha':float(fila[1])} if fila else None
            finally: conexion.close()
        except pymysql.err.OperationalError:
            return None
        except pymysql.err.ProgrammingError:
            return None

    def _temporal_tiene_tablas(self, base):
        import pymysql
        conexion = pymysql.connect(**conexion_local(self.perfil,'importador'))
        try:
            with conexion.cursor() as c:
                c.execute('SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s',('panel_stage_'+base,))
                return bool(c.fetchone()[0])
        finally: conexion.close()

    def activar_preparacion(self, nombre, uid, archivo, sha256=None):
        import subprocess
        estaciones = {e['nombre']:e for e in self.listar_estacionamientos()}
        base = estaciones[nombre]['database']
        preparado = self.obtener_ultima_preparacion(nombre)
        calculada = huella_archivo(archivo)
        if sha256 and calculada != sha256: raise ValueError('El ZIP cambió después de su descarga.')
        sha256 = sha256 or calculada
        if not preparado or str(preparado['uid']) != str(uid) or preparado['base_temporal'] != 'panel_stage_'+base:
            raise RuntimeError('No existe preparación validada para ese respaldo.')
        proceso = subprocess.run(['sudo','-n','/usr/local/sbin/panel-activar-seguro',base,sha256],
                                 capture_output=True,text=True,timeout=600)
        if proceso.returncode: raise RuntimeError('El auxiliar rechazó la activación. Revisa la instalación o el resguardo local.')
        self.registrar_importacion(nombre,uid,archivo)
        return 'Base activada y verificada'

    def restaurar_temporal(self, nombre, password_importador=None, archivo_exacto=None, sha256=None):
        """Mismo mecanismo temporal; SQL validado por sentencias, sin comandos de shell."""
        import pymysql
        perfil = self.perfil
        estaciones = {e['nombre']:e for e in self.listar_estacionamientos()}
        if nombre not in estaciones: raise ValueError('Estacionamiento no autorizado')
        base = estaciones[nombre]['database']
        if not re.fullmatch(r'db_[A-Za-z0-9_]+',base): raise ValueError('Nombre de base no permitido')
        temporal = 'panel_stage_'+base
        carpeta = (self.directorio/'respaldos'/base).resolve()
        if not archivo_exacto: raise ValueError('Selecciona un respaldo exacto validado.')
        archivo = Path(archivo_exacto).resolve()
        if archivo.parent != carpeta or not archivo.name.startswith('respaldo_uid_'):
            raise ValueError('Respaldo fuera del directorio autorizado.')
        calculada = huella_archivo(archivo)
        if sha256 and sha256 != calculada: raise ValueError('El ZIP cambió después de su descarga.')
        for _ in sql_validado(archivo,base): pass
        conexion = pymysql.connect(**conexion_local(perfil,'importador',autocommit=True))
        try:
            with conexion.cursor() as cursor:
                cursor.execute(f'CREATE DATABASE IF NOT EXISTS `{temporal}`')
                cursor.execute('SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s',(temporal,))
                if cursor.fetchone()[0]: raise RuntimeError('Temporal ocupada: se conserva para revisión.')
                cursor.execute(f'USE `{temporal}`')
                cursor.execute('SET SESSION sql_mode=%s',('NO_AUTO_VALUE_ON_ZERO',))
                cursor.execute('SET SESSION foreign_key_checks=0')
                for sql in sql_validado(archivo,base): cursor.execute(sql)
                cursor.execute('SET SESSION foreign_key_checks=1')
            verificar_integridad(conexion,temporal)
            if huella_archivo(archivo) != calculada: raise ValueError('El ZIP cambió durante la restauración.')
        finally:
            conexion.close()
        return {'estacionamiento':nombre,'base_temporal':temporal,'archivo':str(archivo),'estado':'Restauración temporal correcta'}

    def actualizar_estacion(self, nombre):
        from Models.bloqueo_respaldos import bloqueo
        with bloqueo(self.directorio/'actualizacion.lock'):
            return self._actualizar_estacion(nombre)

    def _actualizar_estacion(self, nombre):
        respaldo = self.descargar_respaldo(nombre)
        base = respaldo['database']
        recibo = self.recibo_activacion(base)
        if recibo and recibo.get('sha256') == respaldo['sha256']:
            # Reconcilia un cierre entre la activación y el registro SQLite sin reimportar.
            self.registrar_importacion(nombre,respaldo['uid'],respaldo['archivo'],fecha=recibo.get('fecha'))
            self.registrar_evento(nombre,'importacion','Ya importado; sin duplicar',respaldo)
            return respaldo
        try:
            temporal = 'panel_stage_'+base
            preparado = self.obtener_ultima_preparacion(nombre)
            if not (preparado and str(preparado['uid']) == respaldo['uid'] and preparado['archivo'] == respaldo['archivo'] and self._temporal_tiene_tablas(base)):
                self.restaurar_temporal(nombre,archivo_exacto=respaldo['archivo'],sha256=respaldo['sha256'])
                self.registrar_preparacion(nombre,respaldo['uid'],respaldo['archivo'],temporal)
            self.activar_preparacion(nombre,respaldo['uid'],respaldo['archivo'],respaldo['sha256'])
            self.registrar_evento(nombre,'importacion','Importado y activado',respaldo)
            return respaldo
        except Exception:
            self.registrar_evento(nombre,'importacion','Error de importación; revisar temporal o auxiliar',respaldo)
            raise

    def ejecutar_todos(self, importar=False):
        resultado = []
        for estacion in self.listar_estacionamientos():
            nombre = estacion['nombre']
            try:
                if importar: self.actualizar_estacion(nombre)
                else: self.descargar_respaldo(nombre)
                resultado.append((nombre,'Importado o ya disponible' if importar else 'Descargado y validado'))
            except Exception:
                with contextlib.suppress(Exception):
                    self.registrar_evento(nombre,'importacion' if importar else 'descarga','Error de actualización; revisar configuración, correo o temporal')
                resultado.append((nombre,'Error; se conservan las bases anteriores'))
        return resultado


if __name__ == "__main__":

    actualizador = ActualizadorRespaldos()

    estacionamientos = (
        actualizador.listar_estacionamientos()
    )

    print("\nACTUALIZADOR DE RESPALDOS")
    print("=" * 45)

    print(
        f"Estacionamientos configurados: "
        f"{len(estacionamientos)}"
    )

    for estacionamiento in estacionamientos:

        nombre = estacionamiento["nombre"]

        estado = actualizador.obtener_estado(nombre)

        print(f"\n{nombre}")
        print(
            f"  Base: {estacionamiento['database']}"
        )
        print(
            f"  Estado: {estado['estado']}"
        )
        print(
            f"  Comprobar: "
            f"{actualizador.necesita_comprobacion(nombre)}"
        )
