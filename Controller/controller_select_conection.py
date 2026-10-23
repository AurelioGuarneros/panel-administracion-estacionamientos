from Views.view_select_report import View_Report
from Views.view_crud_usuarios_reportes import View_CRUD_usuarios
from Tools.proyect_tools import Tools

from tkinter import messagebox
import json
import tkinter as tk


class Controller_Select_Conection:
    """
    Controlador para seleccionar la conexión a una base de datos.
    """

    def __init__(self) -> None:
        """
        Constructor de la clase. Crea la ventana principal para la selección de la conexión.

        :return: None
        """
        self.tools_instance = Tools()
        self.database_config_file = self.tools_instance.read_path_config_file(
            'config_files', "database_config_file")

    def conectar(self, estacionamiento: str, user_name: str, reportes: dict) -> None:
        """
        Establece la conexión a una base de datos seleccionada por el usuario y muestra la vista de informes.

        :param estacionamiento (str): El nombre de la conexión seleccionada por el usuario.
        :param user_name (str): El nombre de usuario.
        :param reportes (dict): Diccionario con los permisos del usuario.

        :raises TypeError: Si el estacionamiento seleccionado no es válido.

        :return: None
        """
        try:
            # Asigna los valores de estacionamiento, user_name y reportes a las variables correspondientes
            self.estacionamiento: str = estacionamiento
            self.user_name: str = user_name
            self.reportes: dict = reportes

            # Asigna la configuración de conexión correspondiente según el estacionamiento seleccionado
            if self.estacionamiento == 'Seleccione una conexión':
                raise TypeError('Selecciona una conexión.')

            print(f'Conectando a -> {self.estacionamiento}')
            View_Report(user_name=self.user_name, estacionamiento=self.estacionamiento,
                        reportes=self.reportes, admin=True)

        except TypeError as e:
            # Si se produce una excepción TypeError, muestra un mensaje de advertencia
            messagebox.showwarning("Error", f"{e}")
        except Exception as e:
            messagebox.showwarning("Error", f"{e}")

    def get_db_list(self):
        """
        Obtiene la lista de bases de datos disponibles y sus nombres de conexiones desde el archivo de configuración.

        :return: tuple[list, list] or None: Una tupla que contiene dos listas, la primera con las bases de datos y la segunda con los nombres de conexiones, o None si hay un error.
        """
        try:
            with open(self.database_config_file, "r", encoding='utf-8') as f:
                data = json.load(f)

            # Obtiene la lista de las bases de datos seleccionada
            db_list = []
            db_name_conections = []
            for config in data["settings"]:
                if len(config["name_config"]) > 0 and config.get("activo", True):
                    if config["name_config"] == "Admin":
                        pass
                    else:
                        db_name_conections.append(config["name_config"])

                    if config["database"] == "db_test":
                        pass
                    else:
                        db_list.append(config["database"])
            else:
                return db_list, db_name_conections

        except ValueError as e:
            # Si se lanza una excepción ValueError, muestra un mensaje de error
            tk.messagebox.showerror('Error', f'Error: {e}')

    def view_usuarios(self, user_name: str) -> None:
        """
        Abre la vista CRUD de usuarios.

        :param user_name (str): El nombre de usuario.

        :return: None
        """
        View_CRUD_usuarios(user_name=user_name)
