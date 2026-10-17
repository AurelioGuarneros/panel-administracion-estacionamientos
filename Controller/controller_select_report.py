from Views.view_crud_usuarios_tpv import View_CRUD_usuarios
from Models.queries import Queries


class Controller_Select_Report:
    """
    Controller de la seleccion de reportes.
    """

    def __init__(self, estacionamiento: str = None, user_name: str = None, query: Queries = None) -> None:
        """
        Constructor de la clase.
        Crea la ventana principal, la tabla y los campos de consulta.

        :param estacionamiento (str): Nombre del estacionamiento.
        :param user_name (str): Nombre de usuario.
        :param query (Queries): Objeto de tipo Queries que tiene la conexión a la base de datos.
        :return: None
        """
        self.user_name: str = user_name
        self.estacionamiento: str = estacionamiento
        self.query: Queries = query

    def view_crud_usuarios(self) -> None:
        """
        Abre la vista CRUD de usuarios.

        :return: None
        """
        View_CRUD_usuarios(estacionamiento=self.estacionamiento,
                           user_name=self.user_name, query=self.query)
