from Views.view_agregar_usuario_reportes import View_agregar_usuarios
from Views.view_modificar_usuario_reportes import View_modificar_usuarios
from Tools.proyect_tools import Tools

from tkinter import messagebox as mb

import json


class Controller_CRUD_usuarios:
    """
    Controlador para realizar operaciones CRUD en usuarios.

    :param user_name (str): Nombre de usuario actual.
    """

    def __init__(self, user_name: str = None):
        """
        Constructor de la clase.

        :param user_name (str): Nombre de usuario actual.
        """
        self.user_name = user_name

        self.tools_instance = Tools()
        self.user_settings_file = self.tools_instance.read_path_config_file(
            'config_files',
            'user_settings_file')

        # Obtiene la configuración seleccionada
        with open(self.user_settings_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        # Lista de usuarios
        self.user_list = [[user[k] for k in user.keys() if k != "Reportes"] +
                          list(user['Reportes'].values()) for user in self.data['ussers']]

    def ver_usuarios(self) -> list:
        """
        Obtiene los datos de todos los usuarios.

        :return:
            - usuarios (list): Lista de usuarios, cada uno representado como una lista de valores.
        """
        usuarios = self.user_list
        return usuarios

    def obtener_usuario(self, user_name: str) -> dict:
        """
        Obtiene los detalles de un usuario por su nombre de usuario.

        :param user_name (str): Nombre de usuario a buscar.

        :return:
            - usuario (dict): Un diccionario con los detalles del usuario.
        """
        usuario = None
        for user in self.data["ussers"]:
            if user["UserName"] == user_name:
                usuario = user
                break

        if usuario is None:
            mb.showerror(
                "Error", "No hay un registro de un usuario con ese nombre de usuario")

        return usuario

    def eliminar_usuarios(self, user_name: str) -> None:
        """
        Elimina un usuario por su nombre de usuario.

        :param user_name (str): Nombre de usuario a eliminar.
        """
        for user in self.data['ussers']:
            if user['UserName'] == user_name:
                self.data['ussers'].remove(user)
                break
        else:
            mb.showerror(
                "Error", "No hay un registro de un usuario con ese nombre de usuario")

        # Guardar los cambios en el archivo JSON
        with open(self.user_settings_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

        self.actualizar_JSON()

    def agregar_usuarios(self) -> None:
        """
        Abre una ventana para agregar un nuevo usuario.
        """
        nuevo_usuario = View_agregar_usuarios(user_name=self.user_name)
        self.actualizar_JSON()

    def modificar_usuarios(self, user_name: str) -> None:
        """
        Abre una ventana para modificar un usuario existente.

        :param user_name (str): Nombre de usuario a modificar.
        """
        usuario = self.obtener_usuario(user_name)
        nuevo_usuario = View_modificar_usuarios(
            user_name=self.user_name,
            user_update=usuario)
        self.actualizar_JSON()

    def actualizar_JSON(self) -> None:
        """
        Actualiza la información del archivo JSON después de realizar cambios.
        """
        with open(self.user_settings_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.user_list = [[user[k] for k in user.keys() if k != "Reportes"] +
                          list(user['Reportes'].values()) for user in self.data['ussers']]

    def comprobar_usuario(self, usuario_nombre: str) -> bool:
        """
        Comprueba si un usuario con un nombre de usuario dado existe en la lista de usuarios.

        :param usuario_nombre (str): Nombre de usuario a comprobar.

        :return:
            - exists (bool): True si el usuario existe, False en caso contrario.
        """
        exists = any(user['UserName'] ==
                     usuario_nombre for user in self.data['ussers'])
        if not exists:
            mb.showerror(
                "Error", "No existe un usuario con ese nombre de usuario")
        return exists
