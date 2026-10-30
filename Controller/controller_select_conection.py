from Views.view_select_report import View_Report
from Views.view_crud_usuarios_reportes import View_CRUD_usuarios
from Tools.proyect_tools import Tools

from tkinter import messagebox
from Models.estacionamientos_config import EstacionamientosConfig, exigir_admin


class Controller_Select_Conection:
    """
    Controlador para seleccionar la conexión a una base de datos.
    """

    def __init__(self, permiso=None, config_path=None) -> None:
        """
        Constructor de la clase. Crea la ventana principal para la selección de la conexión.

        :return: None
        """
        self.permiso = permiso
        if config_path is None:
            config_path = Tools().read_path_config_file('config_files', 'database_config_file')
        self.config = EstacionamientosConfig(config_path, permiso)

    def abrir_administracion(self, parent, on_change):
        exigir_admin(self.permiso)
        from Views.view_admin_estacionamientos import ViewAdminEstacionamientos
        return ViewAdminEstacionamientos(parent, self.config, on_change, self.permiso)

    def abrir_estado_actualizacion(self, parent, ruta_sqlite=None):
        exigir_admin(self.permiso)
        from Models.estado_actualizaciones import EstadoActualizaciones
        from Views.view_estado_actualizaciones import ViewEstadoActualizaciones
        return ViewEstadoActualizaciones(parent, EstadoActualizaciones(self.config, ruta_sqlite))

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
            if self.estacionamiento not in [r['name_config'] for r in self.config.activos()]:
                raise TypeError('Selecciona una conexión.')

            print(f'Conectando a -> {self.estacionamiento}')
            View_Report(user_name=self.user_name, estacionamiento=self.estacionamiento,
                        reportes=self.reportes, admin=True)

        except TypeError as e:
            # Si se produce una excepción TypeError, muestra un mensaje de advertencia
            messagebox.showwarning("Error", f"{e}")
        except Exception as e:
            messagebox.showwarning("Error", f"{e}")

    def get_db_list(self, propagar_error=False):
        """
        Obtiene la lista de bases de datos disponibles y sus nombres de conexiones desde el archivo de configuración.

        :return: tuple[list, list] or None: Una tupla que contiene dos listas, la primera con las bases de datos y la segunda con los nombres de conexiones, o None si hay un error.
        """
        try:
            registros = [r for r in self.config.activos() if r['database'] != 'db_test']
            return ([r['database'] for r in registros if r['database'] != 'db_test'],
                    [r['name_config'] for r in registros])
        except (OSError, ValueError):
            if propagar_error:
                raise
            messagebox.showerror('Error', 'No se pudo leer la configuración de estacionamientos.')
            return [], []

    def view_usuarios(self, user_name: str) -> None:
        """
        Abre la vista CRUD de usuarios.

        :param user_name (str): El nombre de usuario.

        :return: None
        """
        View_CRUD_usuarios(user_name=user_name)
