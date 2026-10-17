from Views.view_agregar_usuario_tpv import View_agregar_usuarios
from Views.view_modificar_usuario_tpv import View_modificar_usuarios
from Models.queries import Queries


class Controller_CRUD_usuarios:
    """
    Controlador para la gestión de usuarios.

    Args:
        estacionamiento (str): Nombre del estacionamiento.
        user_name (str): Nombre de usuario.
        query (Queries): Objeto de tipo Queries que tiene la conexión a la base de datos.
    """

    def __init__(self, estacionamiento: str = None, user_name: str = None, query: Queries = None) -> None:
        """
        Constructor de la clase.
        Crea la ventana principal, la tabla y los campos de consulta.

        :param estacionamiento (str): Nombre del estacionamiento.
        :param user_name (str): Nombre de usuario.
        :param query (Queries): Objeto de tipo Queries que tiene la conexión a la base de datos.

        :raises None:

        :return:
            - None
        """
        self.user_name = user_name
        self.estacionamiento = estacionamiento
        self.query = query

    def consultar_usuario(self, id: int) -> dict:
        """
        Consulta la información de un usuario por su ID.

        :param id (int): ID del usuario a consultar.

        :return:
            - registros (dict): Información del usuario consultado.
        """
        registros = self.query.consultar_usuario(id)
        return registros

    def ver_usuarios(self) -> list:
        """
        Obtiene la lista de usuarios.

        :return:
            - registros (list): Lista de usuarios.
        """
        registros = self.query.ver_usuarios()
        return registros

    def eliminar_usuarios(self, id: int) -> None:
        """
        Elimina un usuario por su ID.

        :param id (int): ID del usuario a eliminar.
        """
        self.query.eliminar_usuario(id)

    def agregar_usuarios(self) -> None:
        """
        Abre una ventana para agregar un nuevo usuario.
        """
        nuevo_usuario = View_agregar_usuarios(
            user_name=self.user_name,
            estacionamiento=self.estacionamiento,
            query=self.query)

    def modificar_usuarios(self, id: int) -> None:
        """
        Abre una ventana para modificar un usuario existente.

        :param id (int): ID del usuario a modificar.
        """
        usuario_informacion = self.consultar_usuario(id=id)
        modificar_usuario = View_modificar_usuarios(
            user_name=self.user_name,
            estacionamiento=self.estacionamiento,
            query=self.query,
            usuario_informacion=usuario_informacion,
            id=id)
