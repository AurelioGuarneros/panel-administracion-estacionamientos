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
        Sincroniza la base de datos, descargando y cargando la versión más reciente si es necesario.

        :param name_config (str): Nombre de la configuración de la base de datos.
        :return: None
        """
        try:
            # Obtiene la configuración de la base de datos desde el archivo de configuración
            configuracion = self.config_db.obtener_db_configuracion(
                name_config)

            host = configuracion["host"]
            user = configuracion["user"]
            password = configuracion["password"]
            iv = configuracion["iv"]
            database = configuracion["database"]
            email = configuracion["email"]

            if host != "localhost":
                messagebox.showwarning(
                    "Alerta", f"Ha seleccionado una conexión directa, por lo que no se descargará una base de datos")
                self.connect(host, user, self.tools_instance.descifrar_AES(
                    password, iv), database)
                return

            success_email = self.download_db(email_filter=email)

            if success_email is False:
                messagebox.showwarning(
                    "Error", f"Error al descargar la base de datos más reciente, verifique su conexión a internet e intente nuevamente, en caso de que persista el error contacte con un administrador")
                return

            if success_email is None:
                messagebox.showwarning(
                    "Error", f"No se encontró una base de datos para descargar, contacte a un administrador y verifique el envio de información del estacionamiento")
                return

            date_email, file_path_db = success_email

            if file_path_db is None:
                messagebox.showwarning(
                    "Error", f"Error al descomprimir la base de datos, contacte a un administrador, se conectará a la última versión descargada anteriormente")
                self.connect(host, user, self.tools_instance.descifrar_AES(
                    password, iv), database)
                return

            hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hoy = datetime.strptime(hoy, "%Y-%m-%d %H:%M:%S")

            tiempo_pasado = hoy - date_email
            print(f"Fecha actual: {hoy}")
            print(f"Fecha envio: {date_email}")
            print(f"diferencia de tiempo: {tiempo_pasado}")

            # Calcula la diferencia en días, horas y minutos
            dias_pasados = tiempo_pasado.days
            horas_pasadas, _ = divmod(tiempo_pasado.seconds, 3600)

            if dias_pasados >= 1 and horas_pasadas > 0:
                messagebox.showwarning(
                    "Alerta", f"La base de datos que acaba de descargarse fue enviada en esta fecha [{date_email}], por lo que su información no está actualizada a la fecha actual, contacte con el estacionamiento correspondiente para que envíen la información actualizada o contacte con un administrador por posible error al enviar la información.")

            self.load_db(user, self.tools_instance.descifrar_AES(
                password, iv), database, file_path_db)

            self.connect(host, user, self.tools_instance.descifrar_AES(
                password, iv), database)

        except Exception as e:
            messagebox.showwarning(
                "Error", f"Mostrar el siguiente error a un administrador: {e}")
            print(e)
            traceback.print_exc()
            return False

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

    def load_db(self, user: str, password: str, old_db: str, new_db: str) -> None:
        """
        Carga una base de datos desde un archivo SQL.

        :param user (str): Usuario de la base de datos.
        :param password (str): Contraseña del usuario de la base de datos.
        :param old_db (str): Nombre de la base de datos existente.
        :param new_db (str): Ruta al archivo SQL que contiene la nueva base de datos.
        :return: None
        """
        try:
            if system() == "Windows":
                command = f"cd C:/xampp/mysql/bin && mysql -u {user} -p{password} {old_db} < {new_db}"
            elif system() == "Linux":
                command = f"mysql -u {user} -p{password} {old_db} < {new_db}"
            else:
                raise self.IncompatibilidadSistema(
                    "Incompatibilidad con el sistema operativo")
                
            self.tools_instance.remove_extra_data_from_database(new_db)

            # Ejecutar el comando para cargar la base de datos
            run(command, shell=True)
            print("Base de datos cargada exitosamente.")

            try:
                remove(new_db)
                print("Archivo .sql eliminado exitosamente.")
            except Exception as e:
                print(f"No se pudo eliminar el archivo .sql: {e}")

        except CalledProcessError as error:
            print(f"Error al ejecutar el comando: {error}")
        except self.IncompatibilidadSistema as error:
            print(f"Error: {error}")
        except Exception as error:
            print(f"Error al ejecutar el comando: {error}")

    class IncompatibilidadSistema(Exception):
        """
        Excepción para indicar incompatibilidad con el sistema operativo.
        """
        pass
