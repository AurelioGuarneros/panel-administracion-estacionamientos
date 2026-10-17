import json
import tkinter as tk
import pymysql
from subprocess import run, CalledProcessError
from platform import system
from threading import Thread
from time import sleep

from Tools.proyect_tools import Tools

class DatabaseConfig:
    """
    Clase que representa la configuración de la base de datos.

    :param tools_instance (tools): Instancia de la clase tools.
    :param database_config_file (str): Ruta del archivo de configuración de la base de datos.
    """

    def __init__(self):
        """
        Inicializa una instancia de la clase DatabaseConfig.
        """
        self.tools_instance = Tools()
        self.database_config_file = self.tools_instance.read_path_config_file(
            'config_files', "database_config_file")
        self.system_config_file = self.tools_instance.read_path_config_file(
            'config_files', "system_settings_file")

    def guardar_db_configuracion(self, name_config: str, host: str, user: str, password: str, database: str, email: str) -> None:
        """
        Guarda la configuración de la base de datos en un archivo JSON.

        :param name_config (str): Nombre de la configuración.
        :param host (str): Dirección del servidor de la base de datos.
        :param user (str): Nombre de usuario para acceder a la base de datos.
        :param password (str): Contraseña para acceder a la base de datos.
        :param database (str): Nombre de la base de datos a la que conectarse.
        :param email (str): Dirección de correo electrónico.
        :raises FileNotFoundError: Si no se encuentra el archivo de configuración.
        """
        # Cifra la contraseña y obtén el vector de inicialización
        result = self.tools_instance.cifrar_AES(str(password))
        if result:
            new_password, iv_text = result
        else:
            # Manejar el caso en que cifrar_AES devuelve False
            print("Error al cifrar la contraseña.")
            return

        # Crea un diccionario con los parámetros de la conexión
        configuracion = {
            "name_config": name_config,
            "host": host,
            "user": user,
            "password": new_password,
            "iv": iv_text,
            "database": database,
            "email": email
        }

        try:
            # Intenta abrir el archivo de configuración existente
            with open(self.database_config_file, "r", encoding='utf-8') as f:
                settings = json.load(f)
        except FileNotFoundError:
            settings = {"settings": []}

        # Agrega la nueva configuración al diccionario de configuraciones
        settings['settings'].append(configuracion)

        # Guarda el diccionario de configuraciones en el archivo JSON
        with open(self.database_config_file, "w", encoding='utf-8') as f:
            json.dump(settings, f, indent=4)

    def obtener_db_configuracion(self, name_config: str) -> dict:
        """
        Obtiene la configuración de la base de datos a partir de su nombre.

        :param name_config (str): Nombre de la configuración.
        :return: Un diccionario con los parámetros de la conexión a la base de datos.
        :raises ValueError: Si no se encuentra la configuración especificada.
        """
        try:
            with open(self.database_config_file, "r", encoding='utf-8') as f:
                data = json.load(f)

            # Obtiene la configuración seleccionada
            configuracion = None
            for config in data["settings"]:
                if config["name_config"] == name_config:
                    configuracion = config
                    break

            if configuracion is None:
                raise ValueError(
                    "No se encontró la configuración especificada.")

            return configuracion

        except ValueError as e:
            # Si se lanza una excepción TypeError, muestra un mensaje de error en una ventana de diálogo
            tk.messagebox.showerror('Error', f'Error: {e}')

    def create_databases(self, databases: list) -> None:
        """
        Crea bases de datos.

        :param databases (list): Lista de nombres de bases de datos a crear.
        """
        try:
            if system() == "Windows":
                self.start_mysql_windows(1)

            data_config = self.obtener_db_configuracion("Admin")
            config = {
                "host": data_config["host"],
                "user": data_config["user"],
                "password": self.tools_instance.descifrar_AES(
                    data_config["password"],
                    data_config["iv"])
            }
            # Crea una conexión a la base de datos MySQL
            conexion = pymysql.connect(**config)

            # Crea un objeto cursor para ejecutar comandos SQL
            cursor = conexion.cursor()

            for database in databases:

                # Sentencia SQL para crear la base de datos
                create_database_sql = f"CREATE DATABASE IF NOT EXISTS {database};"

                # Ejecuta la sentencia SQL
                cursor.execute(create_database_sql)

                # Confirma la transacción
                conexion.commit()

                print(f"Base de datos [{database}] creada exitosamente.")

            # Cierra el cursor y la conexión
            if cursor:
                cursor.close()
            conexion.close()

        except pymysql.err.OperationalError as e:
            print(f"Error: {e}")
            tk.messagebox.showerror('Error', f'Error: {e}')
            return
        except Exception as e:
            tk.messagebox.showerror('Error', f'Error: {e}')
            print(e)
            return

    def guardar_email_configuracion(self, email: str, password: str) -> None:
        """
        Guarda la configuración de correo en un archivo JSON.

        :param email (str): Dirección de correo electrónico.
        :param password (str): Contraseña para el correo electrónico.
        """
        # Cifra la contraseña y obtén el vector de inicialización
        result = self.tools_instance.cifrar_AES(str(password))
        if result:
            new_password, iv_text = result
        else:
            # Manejar el caso en que cifrar_AES devuelve False
            print("Error al cifrar la contraseña.")
            return

        # Crea un diccionario con los parámetros de la conexión
        configuracion = {
            "email": email,
            "password": new_password,
            "iv": iv_text
        }

        try:
            # Intenta abrir el archivo de configuración existente
            with open(self.system_config_file, "r", encoding='utf-8') as f:
                system_config = json.load(f)
        except FileNotFoundError:
            system_config = {"system_config": []}

        # Agrega la nueva configuración al diccionario de configuraciones
        system_config['system_config'].append(configuracion)

        # Guarda el diccionario de configuraciones en el archivo JSON
        with open(self.system_config_file, "w", encoding='utf-8') as f:
            json.dump(system_config, f, indent=4)

    def obtener_email_configuracion(self, email: str) -> dict:
        """
        Obtiene la configuración de correo a partir de una dirección de correo electrónico.

        :param email (str): Dirección de correo electrónico.
        :return: Un diccionario con los parámetros de la conexión de correo.
        :raises ValueError: Si no se encuentra la configuración especificada.
        """
        try:
            with open(self.system_config_file, "r", encoding='utf-8') as f:
                data = json.load(f)

            # Obtiene la configuración seleccionada
            configuracion = None
            for config in data["system_config"]:
                if config["email"] == email:
                    configuracion = config
                    break

            if configuracion is None:
                raise ValueError(
                    "No se encontró la configuración especificada.")

            return configuracion

        except ValueError as e:
            # Si se lanza una excepción TypeError, muestra un mensaje de error en una ventana de diálogo
            tk.messagebox.showerror('Error', f'Error: {e}')

    def start_mysql_windows(self, time_seconds: int = 0) -> None:
        """
        Inicia el servidor MySQL en Windows en un hilo separado.

        Esta función inicia el servidor MySQL en Windows utilizando el comando 'mysqld' y ejecuta este proceso en un hilo separado.
        También permite especificar un tiempo de espera antes de continuar.

        :param time_seconds (int, optional): El tiempo en segundos que se debe esperar antes de continuar. Por defecto es 0.
        :return: None
        """
        def start():
            try:
                # Comando para iniciar el servidor MySQL
                command = f"cd C:/xampp/mysql/bin && mysqld"
                run(command, shell=True)

            except CalledProcessError as error:
                print(f"Error al ejecutar el comando: {error}")

            except Exception as error:
                print(f"Error al ejecutar el comando: {error}")

        # Crea un nuevo hilo para ejecutar la función 'start'
        thread = Thread(target=start)
        thread.start()

        # Espera el tiempo especificado antes de continuar
        sleep(time_seconds)
