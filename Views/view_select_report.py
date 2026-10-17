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

    def __init__(self, user_name: str = None, estacionamiento: str = None, reportes: dict = None, admin: bool = False) -> None:
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
        self.query = Queries(estacionamiento=self.estacionamiento)

        if self.query.data_base.connection:
            # Crea la ventana principal
            self.panel_report = tk.Toplevel()

            # Se elimina la funcionalidad del botón de cerrar
            self.panel_report.protocol(
                "WM_DELETE_WINDOW", lambda: self.desconectar())

            # Calcula la posición de la ventana en la pantalla
            pos_x = int(self.panel_report.winfo_screenwidth() / 2)
            pos_y = int(self.panel_report.winfo_screenheight() / 2)

            # Establece la geometría de la ventana con su posición y tamaño
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

            # Inicia el loop principal de la ventana
            self.panel_report.mainloop()

    def interface(self) -> None:
        """Crea la interfaz gráfica para cambiar de conexión y generar reportes."""
        # Crea un Label Frame principal para la sección superior
        seccion_superior = ttk.LabelFrame(self.panel_report, text='')
        seccion_superior.columnconfigure(1, weight=1)
        seccion_superior.propagate(True)
        seccion_superior.grid(row=0, column=0, sticky=tk.NSEW)

        # Crea otro Label Frame para la sección del logo dentro del Label Frame principal
        seccion_logo = ttk.LabelFrame(seccion_superior, text='')
        seccion_logo.grid(row=0, column=0, sticky=tk.NSEW)

        # Crea una etiqueta con la imagen del logo dentro del Label Frame de la sección del logo
        etiqueta_logo = ttk.Label(seccion_logo, image=self.logo_pase)
        etiqueta_logo.grid(row=0, column=0, sticky=tk.NSEW)

        # Crea una etiqueta de bienvenida para mostrar el usuario conectado y el estacionamiento
        etiqueta_bienvenida = ttk.Label(
            seccion_logo,
            text=f'Bienvenido/a: {self.user_name}, estas conectado/a a -> {self.estacionamiento}'
        )
        etiqueta_bienvenida.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # Crea un Label Frame para la sección de los botones de reportes
        seccion_botones = ttk.LabelFrame(
            self.panel_report,
            text='Selecciona el tipo de reporte a generar')
        seccion_botones.grid(row=1, column=0)

        # Crea un Label Frame para los botones de desconectar y salir
        seccion_botones_salir = ttk.LabelFrame(
            seccion_superior,
            text='Salir')
        seccion_botones_salir.grid(row=0, column=3, padx=5, sticky='NW')

        # Crea un botón de desconexión y lo empaqueta en la seccion_botones_salir
        boton_desconectar = tk.Button(
            seccion_botones_salir,
            justify="center",
            text='Desconectar',
            command=self.salir,
            image=self.icono_desconectar
        )
        boton_desconectar.grid(row=0, column=0, padx=5, pady=5)

        # Creación de botones y configuración de su estado según si hay reportes disponibles
        self.boton_general = tk.Button(
            seccion_botones,
            justify="center",
            text='General',
            state='disable',
            command=lambda: {
                # Oculta la ventana actual, abre la ventana correspondiente y muestra la ventana de nuevo
                self.panel_report.withdraw(),
                self.boton_general.config(state="disable"),
                View_Panel_General(
                    user_name=self.user_name,
                    estacionamiento=self.estacionamiento,
                    query=self.query),
                self.panel_report.deiconify(),
                self.boton_general.config(state="normal"),
            })
        self.boton_general.grid(row=0, column=0, padx=5,pady=5, sticky=tk.NSEW)
        if self.reportes['Reporte_General']:
            # Si hay reporte disponible, activa el botón correspondiente
            self.boton_general.config(state="normal")

        self.boton_boletos = tk.Button(
            seccion_botones,
            justify="center",
            text='Boletos/\nIngresos',
            state='disable',
            command=lambda: {
                # Oculta la ventana actual, abre la ventana correspondiente y muestra la ventana de nuevo
                self.panel_report.withdraw(),
                self.boton_boletos.config(state="disable"),
                View_Panel_Boletos_Ingresos(
                    user_name=self.user_name,
                    estacionamiento=self.estacionamiento,
                    query=self.query),
                self.panel_report.deiconify(),
                self.boton_boletos.config(state="normal"),
            })
        self.boton_boletos.grid(row=0, column=1, padx=5,pady=5, sticky=tk.NSEW)
        if self.reportes['Reporte_Boletos_Ingresos']:
            # Si hay reporte disponible, activa el botón correspondiente
            self.boton_boletos.config(state="normal")


        # Creación de botones y configuración de su estado según si hay reportes disponibles
        self.boton_dias = tk.Button(
            seccion_botones,
            text='Diario',
            justify="center",
            state='disable',
            command=lambda: {
                # Oculta la ventana actual, abre la ventana correspondiente y muestra la ventana de nuevo
                self.panel_report.withdraw(),
                self.boton_dias.config(state="disable"),
                View_Panel_Dias(
                    user_name=self.user_name,
                    estacionamiento=self.estacionamiento,
                    query=self.query),
                self.panel_report.deiconify(),
                self.boton_dias.config(state="normal"),
            })
        self.boton_dias.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        if self.reportes['Reporte_Dias']:
            # Si hay reporte disponible, activa el botón correspondiente
            self.boton_dias.config(state="normal")

        self.boton_pensionados = tk.Button(
            seccion_botones,
            justify="center",
            text='Pensionados',
            state='disable',
            command=lambda: {
                # Oculta la ventana actual, abre la ventana correspondiente y muestra la ventana de nuevo
                self.panel_report.withdraw(),
                self.boton_pensionados.config(state="disable"),
                View_Panel_Pensionados(
                    user_name=self.user_name,
                    estacionamiento=self.estacionamiento,
                    query=self.query),
                self.panel_report.deiconify(),
                self.boton_pensionados.config(state="normal"),
            })
        self.boton_pensionados.grid(row=0, column=3, padx=3, pady=5, sticky=tk.NSEW)
        if self.reportes['Reporte_Pensionados']:
            # Si hay reporte disponible, activa el botón correspondiente
            self.boton_pensionados.config(state="normal")

        self.boton_ingresos_pensiones = tk.Button(
            seccion_botones,
            justify="center",
            text='Ingresos\nPensiones',
            state='disable',
            command=lambda: {
                # Oculta la ventana actual, abre la ventana correspondiente y muestra la ventana de nuevo
                self.panel_report.withdraw(),
                self.boton_ingresos_pensiones.config(state="disable"),
                View_Panel_Ingresos_Pensiones(
                    user_name=self.user_name,
                    estacionamiento=self.estacionamiento,
                    query=self.query),
                self.panel_report.deiconify(),
                self.boton_ingresos_pensiones.config(state="normal"),
            })
        self.boton_ingresos_pensiones.grid(row=0, column=4, padx=4, pady=5, sticky=tk.NSEW)
        if self.reportes['Reporte_Ingresos_Pension']:
            # Si hay reporte disponible, activa el botón correspondiente
            self.boton_ingresos_pensiones.config(state="normal")

        self.boton_cambios_sistema = tk.Button(
            seccion_botones,
            justify="center",
            text='Cambios del\nSistema',
            state='disable',
            command=lambda: {
                # Oculta la ventana actual, abre la ventana correspondiente y muestra la ventana de nuevo
                self.panel_report.withdraw(),
                self.boton_cambios_sistema.config(state="disable"),
                View_panel_cambios(
                    user_name=self.user_name,
                    estacionamiento=self.estacionamiento,
                    query=self.query),
                self.panel_report.deiconify(),
                self.boton_cambios_sistema.config(state="normal"),
            })
        self.boton_cambios_sistema.grid(row=0, column=5, padx=4, pady=5, sticky=tk.NSEW)
        if self.reportes['Reporte_Cambios_Sistema']:
            # Si hay reporte disponible, activa el botón correspondiente
            self.boton_cambios_sistema.config(state="normal")


        if self.admin:
            self.boton_admin_usuarios = tk.Button(
                self.panel_report,
                text='Administrar Usuarios',
                command=lambda: {
                    # Se deshabilitan los botones mientras se realiza la conexión
                    self.desactivar(),

                    # Se llama al método conectar del objeto select_controller con la opción seleccionada
                    self.report_controller.view_crud_usuarios(),
                    # Se habilitan de nuevo los botones
                    self.activar(),
                })
            self.boton_admin_usuarios.grid(row=3, column=0, padx=5, pady=5)

    def desactivar(self) -> None:
        """Desactiva los botones de la interface"""
        self.panel_report.withdraw()  # oculta la ventana
        self.boton_admin_usuarios.config(state="disable")

    def activar(self) -> None:
        """Activa los botones de la interface """
        self.panel_report.deiconify()
        self.boton_admin_usuarios.config(state="normal")

    def desconectar(self) -> None:
        """Elimina el panel y detiene la ejecución del hilo donde se ejecuta la ventana"""
        # detener el loop principal
        self.panel_report.quit()
        # Destruye el panel principal
        self.panel_report.destroy()

    def salir(self) -> None:
        """Muestra un cuadro de diálogo para informar al usuario que se está cerrando la aplicación y detiene la ejecución del programa. """
        self.desconectar()
        # Levanta una excepción para salir del programa
        raise SystemExit
