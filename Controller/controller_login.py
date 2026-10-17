from Tools.proyect_tools import Tools
from Views.view_select_conection import View_Conect
from Views.view_select_report import View_Report

import tkinter as tk

import json


class ControllerLogin:
    """
    Controlador del login
    """

    def __init__(self):
        """
        Inicializa las variables de usuario y contraseña como nulas.
        Crea una instancia de la clase tools para acceder a sus métodos.
        Obtiene la ruta del archivo de configuración del archivo de ajustes de usuario utilizando el método read_path_config_file.

        :param None:
        :return:
            - None
        """
        self.user: str = None
        self.password: str = None

        # Crear una instancia de la clase "tools" para acceder a sus métodos
        self.tools_instance = Tools()

        # Obtener la ruta del archivo de configuración de ajustes de usuario
        self.user_settings_file: str = self.tools_instance.read_path_config_file(
            'config_files', 'user_settings_file')

    def get_data(self, user: str = None, password: str = None) -> None:
        """
        Obtiene los datos del usuario y tema y los imprime en la consola.

        :param user (str or None): Nombre de usuario para iniciar sesión. Si se deja en blanco, se asigna None.
        :param password (str or None): Contraseña para iniciar sesión. Si se deja en blanco, se asigna None.

        :raises TypeError: Si el campo de usuario o contraseña está vacío.

        :return:
            - None
        """
        try:
            # Asignar los valores de usuario y contraseña a las variables correspondientes
            self.user = user
            self.password = password

            # Si el usuario o la contraseña están vacíos, lanzar una excepción TypeError
            if user == '' or password == '':
                raise TypeError(
                    'El campo Usuario o Contraseña está vacío, no deje campos en blanco.')

            # Obtener los datos del usuario a través del nombre de usuario
            user_data = self.obtener_user_data(UserName=self.user)

            # Comprobar que el usuario existe
            self.comprobar_usuario(user_data)

        # Si se lanza una excepción TypeError, mostrar un mensaje de error en una ventana de diálogo
        except TypeError as e:
            tk.messagebox.showerror('Error', f'Error: {e}')

    def comprobar_usuario(self, user_data: dict = None) -> None:
        """
        Verificar si el usuario y la contraseña proporcionados son correctos y determinar qué permisos tiene el usuario.

        :param user_data (dict or None): Los datos del usuario obtenidos a través del nombre de usuario.

        :raises KeyError: Si el nombre de usuario o la contraseña son incorrectos.
        :raises TypeError: Si el tipo de permiso es desconocido o si se produce un error desconocido.

        :return:
            - None
        """
        try:
            if user_data:
                if self.user == user_data['UserName'] and self.password == user_data['Password']:
                    # Si el nombre de usuario y la contraseña son correctos, determinar qué permisos tiene el usuario.
                    print(f"Dentro!: {user_data['Name']} ")

                    # Si el usuario tiene permisos normales, mostrar la vista de informes.
                    if user_data['Permits'] == 'normal':
                        View_Report(
                            user_name=user_data['Name'],
                            estacionamiento=user_data['DefaultConection'],
                            reportes=user_data['Reportes'])

                    # Si el usuario tiene permisos de administrador, mostrar la vista de conexión.
                    elif user_data['Permits'] == 'admin':
                        View_Conect(
                            user_name=user_data['Name'],
                            reportes=user_data['Reportes'])

                    # Si el tipo de permiso es desconocido, lanzar una excepción TypeError.
                    else:
                        raise TypeError("Tipo de permiso desconocido")
                else:
                    # Si el nombre de usuario o la contraseña son incorrectos, lanzar una excepción KeyError.
                    raise KeyError(
                        "El nombre de usuario o contraseña son incorrectos")

        except KeyError as e:
            # Si se lanza una excepción KeyError, mostrar un mensaje de error en una ventana de diálogo.
            tk.messagebox.showerror('Error', f"Error: {e}")
        except TypeError as e:
            # Si se lanza una excepción TypeError, mostrar un mensaje de error en una ventana de diálogo y sugerir contactar con un administrador.
            tk.messagebox.showerror(
                'Error', f"Error: {e}.\nContactar con un administrador")

    def obtener_user_data(self, UserName: str) -> dict:
        """
        Obtener los datos del usuario a partir de su nombre.

        :param UserName (str): nombre del usuario.
        :return:
           - usuario (dict): un diccionario con los parámetros de los usuarios.

        :raises ValueError: si no se encuentra el usuario especificado.
        """
        try:
            with open(self.user_settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Obtener la configuración seleccionada
            usuario = None
            for user in data["ussers"]:
                if user["UserName"] == UserName:
                    usuario = user
                    break

            if usuario is None:
                raise ValueError("El usuario ingresado no está registrado")

            return usuario

        # Si se lanza una excepción ValueError, mostrar un mensaje de error en una ventana de diálogo
        except ValueError as e:
            tk.messagebox.showerror('Error', f'Error: {e}')
