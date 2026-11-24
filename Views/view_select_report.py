from Controller.controller_select_report import Controller_Select_Report
from Tools.proyect_tools import Tools
from Models.queries import Queries
from .view_panel_general import View_Panel_General
from .view_panel_pensionados import View_Panel_Pensionados
from .view_panel_boletos_ingresos import View_Panel_Boletos_Ingresos
from .view_panel_dias import View_Panel_Dias
from .view_panel_ingresos_pension import View_Panel_Ingresos_Pensiones
from .view_panel_cambios_sistema import View_panel_cambios

import tkinter as tk
from tkinter import ttk
from tkinter import StringVar

from PIL import ImageTk, Image
from tkinter import PhotoImage


class View_Report:
    """
    Clase de la vista de selección de reportes
    :param user_name (str): Nombre de usuario.
    :param estacionamiento (str): Nombre del estacionamiento.
    :param reportes (dict): Diccionario de reportes disponibles.

    :raises None: 

    :return:
        - None
    """

    def __init__(self, user_name: str = None, estacionamiento: str = None, reportes: dict = None, admin: bool = False, container=None) -> None:
        """
        Constructor de la clase. Crea la ventana principal para la selección de reportes.

        :param user_name (str or None): Nombre de usuario.
        :param estacionamiento (str or None): Nombre del estacionamiento.
        :param reportes (dict or None): Diccionario de reportes disponibles.

        :raises None: 

        :return:
            - None
        """
        self.user_name = user_name
        self.estacionamiento = estacionamiento
        self.reportes = reportes
        self.admin = admin
        self.embebido = container is not None
        self.query = Queries(estacionamiento=self.estacionamiento)

        if self.query.data_base.connection:
            # Crea la ventana principal
            self.panel_report = container if self.embebido else tk.Toplevel()

            # El contenedor embebido pertenece a la ventana de selección.
            if not self.embebido:
                self.panel_report.protocol("WM_DELETE_WINDOW", lambda: self.desconectar())

            if not self.embebido:
                pos_x = int(self.panel_report.winfo_screenwidth() / 2)
                pos_y = int(self.panel_report.winfo_screenheight() / 2)
                self.panel_report.geometry(f"+{pos_x}+{pos_y}")
                self.panel_report.resizable(False, False)
                self.panel_report.title(f'Selección de reporte')

            # Configura la columna principal del panel para que use todo el espacio disponible
            self.panel_report.columnconfigure(0, weight=1)

            # Crea las instancias de las clases Tools() y Controller_Select_Conection()
            self.tools_instance = Tools()
            self.report_controller = Controller_Select_Report(
                estacionamiento=self.estacionamiento,
                user_name=self.user_name,
                query=self.query
            )

            # Crea las variables para los iconos e imágenes
            logo = self.tools_instance.read_path_config_file(
                'images', 'logo_pase')
            logo_pase = Image.open(logo)
            # Cambiar tamaño de la imagen
            logo_pase = logo_pase.resize((106, 55), Image.LANCZOS)
            self.logo_pase = ImageTk.PhotoImage(logo_pase)

            icono_salir = self.tools_instance.read_path_config_file(
                'images', 'icono_salir')
            self.icono_salir = PhotoImage(file=icono_salir).subsample(50)

            icono_desconectar = self.tools_instance.read_path_config_file(
                'images', 'icono_desconectar')
            self.icono_desconectar = PhotoImage(
                file=icono_desconectar).subsample(50)

            self.variable_estacionamiento = StringVar()

            # Llama a la función interface() que configura la interfaz gráfica
            self.interface()

            # El loop principal lo administra la ventana raíz.

    def interface(self) -> None:
        """Muestra las siete funciones dentro del área derecha de la ventana principal."""
        for widget in self.panel_report.winfo_children():
            widget.destroy()
        self.panel_report.columnconfigure(0, weight=1)
        self.panel_report.rowconfigure(1, weight=1)

        encabezado = ttk.Frame(self.panel_report, padding=(8, 6))
        encabezado.grid(row=0, column=0, sticky="ew")
        encabezado.columnconfigure(1, weight=1)
        ttk.Label(encabezado, text=f"Estacionamiento: {self.estacionamiento}",
                  font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(encabezado, text=f"Usuario: {self.user_name}").grid(
            row=1, column=0, sticky="w", pady=(3, 0))

        seccion_botones = ttk.LabelFrame(
            self.panel_report, text="Selecciona la función que deseas abrir", padding=12)
        seccion_botones.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        for columna in range(3):
            seccion_botones.columnconfigure(columna, weight=1, uniform="funciones")
        for fila in range(3):
            seccion_botones.rowconfigure(fila, weight=1)

        funciones = [
            ("General", "Reporte_General", View_Panel_General, 0, 0),
            ("Boletos / Ingresos", "Reporte_Boletos_Ingresos", View_Panel_Boletos_Ingresos, 0, 1),
            ("Diario", "Reporte_Dias", View_Panel_Dias, 0, 2),
            ("Pensiones", "Reporte_Pensionados", View_Panel_Pensionados, 1, 0),
            ("Ingresos Pensiones", "Reporte_Ingresos_Pension", View_Panel_Ingresos_Pensiones, 1, 1),
            ("Cambios del sistema", "Reporte_Cambios_Sistema", View_panel_cambios, 1, 2),
        ]
        self.botones_funciones = []
        for texto, permiso, clase, fila, columna in funciones:
            disponible = bool(self.reportes.get(permiso, False))
            boton = ttk.Button(
                seccion_botones, text=texto,
                command=lambda vista=clase, titulo=texto: self.abrir_funcion(vista, titulo),
                state="normal" if disponible else "disabled")
            boton.grid(row=fila, column=columna, sticky="nsew", padx=6, pady=6, ipady=14)
            self.botones_funciones.append(boton)

        if self.admin:
            boton_usuarios = ttk.Button(
                seccion_botones, text="Administrar Usuarios",
                command=self.abrir_usuarios)
            boton_usuarios.grid(row=2, column=0, columnspan=3,
                                sticky="nsew", padx=6, pady=6, ipady=10)

    def abrir_funcion(self, clase_vista, titulo):
        """Abre la función seleccionada dentro de la misma área de trabajo."""
        if not self.embebido:
            clase_vista(user_name=self.user_name, estacionamiento=self.estacionamiento,
                        query=self.query)
            return
        for widget in self.panel_report.winfo_children():
            widget.destroy()
        clase_vista(user_name=self.user_name, estacionamiento=self.estacionamiento,
                    query=self.query, container=self.panel_report,
                    on_back=self.mostrar_menu)

    def abrir_usuarios(self):
        """Abre la administración de usuarios en el área derecha."""
        if not self.embebido:
            self.report_controller.view_crud_usuarios()
            return
        for widget in self.panel_report.winfo_children():
            widget.destroy()
        from Views.view_crud_usuarios_tpv import View_CRUD_usuarios
        View_CRUD_usuarios(estacionamiento=self.estacionamiento,
                           user_name=self.user_name, query=self.query,
                           container=self.panel_report, on_back=self.mostrar_menu)

    def mostrar_menu(self):
        """Regresa al menú de funciones sin cerrar la conexión al estacionamiento."""
        if not self.embebido:
            return
        for widget in self.panel_report.winfo_children():
            widget.destroy()
        self.interface()

    def desactivar(self) -> None:
        """Desactiva los botones de la interface"""
        self._ocultar_panel()  # oculta la ventana
        if hasattr(self, "boton_admin_usuarios"):
            self.boton_admin_usuarios.config(state="disable")

    def activar(self) -> None:
        """Activa los botones de la interface """
        self._mostrar_panel()
        if hasattr(self, "boton_admin_usuarios"):
            self.boton_admin_usuarios.config(state="normal")

    def _ocultar_panel(self):
        if not self.embebido:
            self.panel_report.withdraw()

    def _mostrar_panel(self):
        if not self.embebido:
            self.panel_report.deiconify()

    def desconectar(self) -> None:
        """Elimina el panel y detiene la ejecución del hilo donde se ejecuta la ventana"""
        if self.embebido:
            for widget in self.panel_report.winfo_children():
                widget.destroy()
            return
        self.panel_report.quit()
        self.panel_report.destroy()

    def salir(self) -> None:
        """Muestra un cuadro de diálogo para informar al usuario que se está cerrando la aplicación y detiene la ejecución del programa. """
        self.desconectar()
        # Levanta una excepción para salir del programa
        raise SystemExit
