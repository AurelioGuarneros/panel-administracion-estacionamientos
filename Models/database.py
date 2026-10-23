from Config.config_database import DatabaseConfig
from Controller.controller_email import ReciveEmail

import pymysql
import re
from pymysql import err
from tkinter import messagebox
from Tools.proyect_tools import Tools
from datetime import datetime
from subprocess import run, CalledProcessError
from platform import system
import traceback
from os import remove

email_principal = "reportes.panel@pasesa.com.mx"


class database_connection:
    """
    Esta clase permite la conexión a una base de datos MySQL específica.
    Incluye métodos para conectarse a la base de datos, cerrar la conexión y ejecutar consultas en la base de datos.

    :param estacionamiento (str): Nombre del estacionamiento.
    """

    def __init__(self, estacionamiento: str) -> None:
        """
        Inicializa una instancia de la clase `database_connection`.

        :param estacionamiento (str): Nombre del estacionamiento.
        :return: None
        """
        self.estacionamiento = estacionamiento

        # Instancia de la clase DatabaseConfig
        self.config_db = DatabaseConfig()
        self.tools_instance = Tools()

        # Inicializa el objeto de conexión a la base de datos
        self.connection = None

        # Inicializa el objeto del cursor de la conexión
        self.cursor = None

        self.synchronize(name_config=self.estacionamiento)

    def synchronize(self, name_config: str) -> None:
        """
        Conecta con la base de datos configurada.
        La actualización de respaldos se realizará por separado.
        """
        try:
            configuracion = self.config_db.obtener_db_configuracion(
                name_config
            )

            host = configuracion["host"]
            user = configuracion["user"]
            password = self.tools_instance.descifrar_AES(
                configuracion["password"],
                configuracion["iv"]
            )
            database = configuracion["database"]

            print(f"Conectando a {name_config}")
            print(f"Base de datos: {database}")

            self.connect(host, user, password, database)

            if self.connection is None:
                print("No se pudo establecer la conexión.")
            else:
                print("Conexión establecida correctamente.")

        except Exception as error:
            print(f"Error de conexión: {error}")
            traceback.print_exc()

    def connect(self, host: str, user: str, password: str, database: str) -> None:
        """
        Establece una conexión a la base de datos.

        :param host (str): Dirección del host de la base de datos.
        :param user (str): Usuario de la base de datos.
        :param password (str): Contraseña del usuario de la base de datos.
        :param database (str): Nombre de la base de datos.
        :return: None
        """
        try:
            # Realiza la conexión a la base de datos
            self.connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )

        except pymysql.err.OperationalError as e:
            # Manejo de errores en la conexión
            messagebox.showwarning(
                "Error", f"Error al conectarse a la base de datos: {e}")
            return None
        except Exception as e:
            messagebox.showwarning("Error", f"Error: {e}")
            return None

    def close_connection(self) -> None:
        """ Cierra la conexión con la base de datos."""
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str):
        """
        Ejecuta una consulta en la base de datos.

        :param query (str): La consulta SQL a ejecutar.
        :return: result (tuple): Una Tupla con los resultados de la consulta.
        """
        try:
            if self.connection:
                # Crea un objeto cursor para ejecutar la consulta
                self.cursor = self.connection.cursor()

                print(query + '\n')

                # Se ejecuta la consulta
                self.cursor.execute(query)

                # Obtiene los resultados de la consulta
                result = self.cursor.fetchall()

                # Confirma los cambios en la base de datos
                self.connection.commit()

                # Cierra el cursor
                self.cursor.close()

                # Retorna los resultados de la consulta
                return result

        except err.OperationalError as e:
            # Manejo de errores de conexión perdida
            if "10054" in str(e):
                messagebox.showwarning(
                    "Error", "Se ha perdido la conexión con el servidor.\nEl programa se cerrará, posterior a eso inicie nuevamente sesión\n\nEn caso de que el error persista contacte a un administrador.")
                raise SystemExit

        except err.ProgrammingError as error:
            # Manejo de errores de tabla inexistente
            error_message = str(error)
            match = re.search(r"\((\d+),", error_message)
            error_number = int(match.group(1))
            if error_number == 1146:
                print(error)
                messagebox.showwarning(
                    "Error", f"Error: La tabla no existe.\nEs probable que la conexión actual no cuente con la tabla a la que intenta acceder, en caso contrario contacte con un administrador.")
                return

        except Exception as e:
            # Manejo de otros errores
            messagebox.showwarning(
                "Error", f"Error al realizar la consulta, por favor contacte con un administrador y muestre el siguiente error:\nError: {str(e)} ")
            return

    def download_db(self, email_filter: str):
        """
        Descarga una base de datos.

        :param email_filter (str): Filtro de dirección de correo electrónico.
        :return: tuple or None or bool: Una tupla que contiene la fecha formateada del último correo con archivo adjunto descargado y la ruta al archivo descargado. Retorna None si no se encuentra ningún correo o False si ocurre un error.
        """
        # Obtener la información de configuración de correo electrónico desde el objeto config_db
        email_info = self.config_db.obtener_email_configuracion(
            email_principal)

        # Obtener las credenciales de correo y IV de la información obtenida
        email = email_info["email"]
        password = email_info["password"]
        iv = email_info["iv"]

        # Crear una instancia de ReciveEmail
        email_receiver = ReciveEmail(
            username=email,
            password=self.tools_instance.descifrar_AES(password, iv))

        # Recibir el último correo con el filtro especificado
        success_email = email_receiver.recive_last_mail(
            email_filter=email_filter)

        return success_email

    def load_db(self, user: str, password: str, old_db: str, new_db: str) -> bool:
        """
        Importa un archivo SQL en la base indicada.

        Devuelve True si MariaDB finaliza correctamente.
        Devuelve False si ocurre algún error.

        IMPORTANTE:
        Esta función no debe utilizarse directamente sobre
        bases de datos de producción. Primero se debe
        restaurar y validar en una base temporal.
        """
        import os
        import subprocess
        from pathlib import Path

        archivo_sql = Path(new_db)

        if not archivo_sql.is_file():
            print(f"ERROR: No existe el archivo SQL: {archivo_sql}")
            return False

        if not old_db or not old_db.replace("_", "").isalnum():
            print("ERROR: Nombre de base de datos no válido.")
            return False

        if system() == "Windows":
            ejecutable = "C:/xampp/mysql/bin/mysql.exe"
        elif system() == "Linux":
            ejecutable = "mysql"
        else:
            print("ERROR: Sistema operativo incompatible.")
            return False

        # La contraseña no aparece en la línea de comandos.
        entorno = os.environ.copy()
        entorno["MYSQL_PWD"] = password

        comando = [
            ejecutable,
            "--default-character-set=utf8mb4",
            "-u", user,
            old_db
        ]

        try:
            with archivo_sql.open("rb") as entrada:
                resultado = subprocess.run(
                    comando,
                    stdin=entrada,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    env=entorno,
                    check=False
                )

            if resultado.returncode != 0:
                error = resultado.stderr.decode(
                    "utf-8", errors="replace"
                )
                print("ERROR: MariaDB rechazó la importación.")
                print(error.strip())
                return False

            print("Importación finalizada correctamente.")
            print("Archivo SQL conservado:", archivo_sql)
            return True

        except Exception as error:
            print(f"ERROR durante la importación: {error}")
            return False

    class IncompatibilidadSistema(Exception):
        """
        Excepción para indicar incompatibilidad con el sistema operativo.
        """
        pass
