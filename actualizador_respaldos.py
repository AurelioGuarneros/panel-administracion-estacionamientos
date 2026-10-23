"""
Actualizador de respaldos del Panel de Estacionamientos.

Primera etapa:
- Identificar los estacionamientos configurados.
- Registrar fechas de actualización.
- Evitar comprobaciones innecesarias.
- No modificar bases de datos.
"""

import json
import imaplib
import email
from email.utils import parsedate_to_datetime
import sqlite3
import time
from pathlib import Path

from Config.config_database import DatabaseConfig
from Tools.proyect_tools import Tools


class ActualizadorRespaldos:

    INTERVALO_COMPROBACION = 1800  # 30 minutos

    def __init__(self):
        self.configuracion = DatabaseConfig()

        self.directorio = (
            Path.home()
            / ".local"
            / "share"
            / "panel-estacionamientos"
        )

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

    def listar_estacionamientos(self):
        archivo = self.configuracion.database_config_file

        with open(archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)

        return [
            {
                "nombre": item["name_config"],
                "database": item["database"],
                "email": item["email"]
            }
            for item in datos["settings"]
            if item["name_config"] != "Admin" and item.get("activo", True)
        ]

    def obtener_estado(self, estacionamiento):
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


    def consultar_respaldos_correo(self):
        """
        Consulta los últimos respaldos de todos los estacionamientos.
        No descarga adjuntos ni modifica bases de datos.
        """

        herramientas = Tools()

        configuracion_correo = (
            self.configuracion.obtener_email_configuracion(
                "reportes.panel@pasesa.com.mx"
            )
        )

        password = herramientas.descifrar_AES(
            configuracion_correo["password"],
            configuracion_correo["iv"]
        )

        resultados = {}

        conexion = imaplib.IMAP4_SSL(
            "pop.pasesa.com.mx", 993
        )

        try:
            conexion.login(
                configuracion_correo["email"],
                password
            )

            conexion.select("INBOX", readonly=True)

            for estacionamiento in self.listar_estacionamientos():

                nombre = estacionamiento["nombre"]
                remitente = estacionamiento["email"]

                estado, datos = conexion.uid(
                    "search",
                    None,
                    "FROM",
                    f'"{remitente}"'
                )

                if estado != "OK" or not datos or not datos[0]:
                    resultados[nombre] = {
                        "estado": "Sin respaldos",
                        "fecha": None,
                        "uid": None
                    }
                    continue

                identificadores = datos[0].split()

                uid = identificadores[-1]

                estado, mensajes = conexion.uid(
                    "fetch",
                    uid,
                    "(BODY.PEEK[HEADER.FIELDS (DATE SUBJECT FROM)])"
                )

                if estado != "OK":
                    resultados[nombre] = {
                        "estado": "Error al consultar",
                        "fecha": None,
                        "uid": None
                    }
                    continue

                cabecera = next(
                    (
                        elemento[1]
                        for elemento in mensajes
                        if isinstance(elemento, tuple)
                    ),
                    None
                )

                if cabecera is None:
                    resultados[nombre] = {
                        "estado": "Sin cabecera",
                        "fecha": None,
                        "uid": None
                    }
                    continue

                mensaje = email.message_from_bytes(cabecera)

                fecha = mensaje.get("Date", "")

                try:
                    fecha = parsedate_to_datetime(
                        fecha
                    ).isoformat()
                except Exception:
                    pass

                resultados[nombre] = {
                    "estado": "Encontrado",
                    "fecha": fecha,
                    "uid": uid.decode()
                }

        finally:
            try:
                conexion.logout()
            except Exception:
                pass

        return resultados



    def registrar_comprobacion(self, estacionamiento, estado):
        """
        Registra una consulta al correo.
        No significa que el respaldo esté instalado.
        """
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
        No descarga ni restaura bases de datos.
        """
        resultados = self.consultar_respaldos_correo()

        for nombre, informacion in resultados.items():
            estado = informacion["estado"]

            if estado == "Encontrado":
                estado = "Correo encontrado; pendiente de importar"

            self.registrar_comprobacion(nombre, estado)

        return resultados


    def descargar_respaldo(self, nombre):
        """
        Descarga el ZIP más reciente de un estacionamiento activo.
        No importa ni modifica bases de datos.
        """
        import tempfile
        import os
        import zipfile
        from email.utils import parseaddr

        estaciones = {
            e["nombre"]: e
            for e in self.listar_estacionamientos()
        }

        if nombre not in estaciones:
            raise ValueError("Estacionamiento no activo o desconocido")

        estacion = estaciones[nombre]
        remitente = estacion["email"].lower()

        configuracion = self.configuracion.obtener_email_configuracion(
            "reportes.panel@pasesa.com.mx"
        )

        password = Tools().descifrar_AES(
            configuracion["password"],
            configuracion["iv"]
        )

        conexion = imaplib.IMAP4_SSL(
            "pop.pasesa.com.mx", 993
        )

        try:
            conexion.login(configuracion["email"], password)
            conexion.select("INBOX", readonly=True)

            estado, datos = conexion.uid(
                "search", None, "FROM", f'"{remitente}"'
            )

            if estado != "OK" or not datos or not datos[0]:
                raise RuntimeError("No se encontraron correos")

            # Revisar los mensajes recientes hasta hallar un ZIP válido.
            for uid in reversed(datos[0].split()[-20:]):
                estado, mensajes = conexion.uid(
                    "fetch", uid, "(BODY.PEEK[])"
                )

                if estado != "OK":
                    continue

                contenido = next(
                    (x[1] for x in mensajes if isinstance(x, tuple)),
                    None
                )

                if not contenido:
                    continue

                mensaje = email.message_from_bytes(contenido)

                origen = parseaddr(mensaje.get("From", ""))[1].lower()

                if origen != remitente:
                    continue

                for parte in mensaje.walk():
                    nombre_archivo = parte.get_filename()

                    if not nombre_archivo:
                        continue

                    if not nombre_archivo.lower().endswith(".zip"):
                        continue

                    datos_zip = parte.get_payload(decode=True)

                    if not datos_zip:
                        continue

                    directorio = (
                        self.directorio
                        / "respaldos"
                        / estacion["database"]
                    )
                    directorio.mkdir(parents=True, exist_ok=True)

                    destino = directorio / (
                        "respaldo_uid_" + uid.decode() + ".zip"
                    )

                    with tempfile.NamedTemporaryFile(
                        dir=directorio,
                        prefix=".descarga_",
                        suffix=".zip",
                        delete=False
                    ) as temporal:
                        ruta_temporal = Path(temporal.name)
                        temporal.write(datos_zip)

                    try:
                        with zipfile.ZipFile(ruta_temporal) as z:
                            archivos = [
                                x for x in z.infolist()
                                if not x.is_dir()
                            ]

                            if (
                                len(archivos) != 1
                                or not archivos[0].filename.lower().endswith(".sql")
                            ):
                                raise ValueError(
                                    "El ZIP debe contener un único SQL"
                                )

                            if z.testzip() is not None:
                                raise ValueError("ZIP dañado")

                        os.replace(ruta_temporal, destino)

                    finally:
                        ruta_temporal.unlink(missing_ok=True)

                    return {
                        "estacionamiento": nombre,
                        "database": estacion["database"],
                        "uid": uid.decode(),
                        "archivo": str(destino),
                        "fecha": mensaje.get("Date", "")
                    }

            raise RuntimeError(
                "No se encontró un ZIP válido entre los últimos 20 correos"
            )

        finally:
            try:
                conexion.logout()
            except Exception:
                pass


    def restaurar_temporal(self, nombre, password_importador):
        """
        Restaura un respaldo en una base temporal.
        No modifica la base definitiva del estacionamiento.
        """
        import os
        import re
        import zipfile
        import subprocess
        import pymysql

        estaciones = {
            e["nombre"]: e
            for e in self.listar_estacionamientos()
        }

        if nombre not in estaciones:
            raise ValueError("Estacionamiento no autorizado")

        estacion = estaciones[nombre]
        base = estacion["database"]

        if not re.fullmatch(r"db_[a-z0-9_]+", base):
            raise ValueError("Nombre de base no permitido")

        temporal = "panel_stage_" + base

        carpeta = self.directorio / "respaldos" / base

        archivos = sorted(
            carpeta.glob("respaldo_uid_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not archivos:
            raise FileNotFoundError("No existe respaldo descargado")

        archivo = archivos[0]

        conexion = pymysql.connect(
            unix_socket="/run/mysqld/mysqld.sock",
            user="importador_panel",
            password=password_importador,
            autocommit=True
        )

        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{temporal}`"
                )

                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA=%s",
                    (temporal,)
                )

                if cursor.fetchone()[0] != 0:
                    raise RuntimeError(
                        "La base temporal contiene tablas. "
                        "No se sobrescribirá."
                    )

        finally:
            conexion.close()

        with zipfile.ZipFile(archivo) as z:
            nombres = [
                x for x in z.namelist()
                if not x.endswith("/")
            ]

            if len(nombres) != 1 or not nombres[0].lower().endswith(".sql"):
                raise ValueError("ZIP con estructura incorrecta")

            entorno = os.environ.copy()
            entorno["MYSQL_PWD"] = password_importador

            proceso = subprocess.Popen(
                [
                    "mariadb",
                    "--protocol=socket",
                    "--default-character-set=utf8mb4",
                    "--abort-source-on-error",
                    "-u", "importador_panel",
                    temporal
                ],
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=entorno
            )

            try:
                with z.open(nombres[0]) as sql:
                    while True:
                        bloque = sql.read(65536)

                        if not bloque:
                            break

                        proceso.stdin.write(bloque)

                proceso.stdin.close()
                errores = proceso.stderr.read().decode(
                    "utf-8", errors="replace"
                )
                codigo_salida = proceso.wait()

            except Exception:
                proceso.kill()
                proceso.wait()
                raise

        if codigo_salida != 0:
            raise RuntimeError(
                f"Error al restaurar {nombre}: {errores[-1000:]}"
            )

        conexion = pymysql.connect(
            unix_socket="/run/mysqld/mysqld.sock",
            user="importador_panel",
            password=password_importador,
            database=temporal
        )

        try:
            with conexion.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tablas = [fila[0] for fila in cursor.fetchall()]
        finally:
            conexion.close()

        obligatorias = {
            "Cortes", "Entradas", "MovimientosPens",
            "MovsUsuarios", "PagosPens",
            "Pensionados", "Usuarios"
        }

        if not obligatorias.issubset(set(tablas)):
            raise RuntimeError(
                "Faltan tablas obligatorias: "
                + str(obligatorias - set(tablas))
            )

        return {
            "estacionamiento": nombre,
            "base_temporal": temporal,
            "tablas": tablas,
            "archivo": str(archivo),
            "estado": "Restauración temporal correcta"
        }


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
