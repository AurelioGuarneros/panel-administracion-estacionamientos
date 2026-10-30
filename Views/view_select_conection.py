from Controller.controller_select_conection import Controller_Select_Conection
from Tools.proyect_tools import Tools

import tkinter as tk
from tkinter import ttk
from tkinter import StringVar
from tkinter import PhotoImage

from PIL import ImageTk, Image


class View_Conect:
    """
    Clase de la vista de selección de conexion.

    :param user_name (str): Nombre de usuario.
    :param reportes (dir): Diccionario de reportes disponibles.
    """

    def __init__(self,
                 user_name=None,
                 reportes=None, permiso=None):
        """
        La clase Conect se encarga de crear una ventana para seleccionar una conexión.
        Permite al usuario seleccionar una conexión de una lista desplegable y conectarla mediante un botón.
        La ventana se ajusta al centro de la pantalla y contiene un logo de la empresa.

        :param user_name (str or None): nombre del usuario.
        :param reportes (dict or None): diccionario con los permisos del usuario.

        :raises None: 

        :return:
            - None
        """
        self.permiso = permiso
        self.user_name = user_name
        self.reportes = reportes
        # Crea la ventana principal
        self.panel_connect = tk.Toplevel()

        # se elimina la funcinalidad del boton de cerrar
        self.panel_connect.protocol(
            "WM_DELETE_WINDOW", lambda: self.desconectar())

        # deshabilita los botones de minimizar y maximizar
        # self.panel_connect.attributes('-toolwindow', True)

        # Establece la geometría de la ventana con su posición y tamaño
        self.panel_connect.geometry()
        self.panel_connect.resizable(False, False)
        self.panel_connect.title(f'Selecciona la conexión')

        # Configura la columna principal del panel para que use todo el espacio disponible
        self.panel_connect.columnconfigure(0, weight=1)

        # Crea las instancias de las clases Tools() y Controller_Select_Conection(permiso=permiso)
        self.tools_instance = Tools()
        self.select_controller = Controller_Select_Conection(permiso=permiso)

        # Crea las variables para los iconos e imagenes
        logo = self.tools_instance.read_path_config_file('images', 'logo_pase')
        logo_pase = Image.open(logo)
        # Cambiar tamaño de la imagen
        logo_pase = logo_pase.resize((106, 55), Image.LANCZOS)
        self.logo_pase = ImageTk.PhotoImage(logo_pase)

        icono_desconectar = self.tools_instance.read_path_config_file(
            'images', 'icono_desconectar')
        self.icono_desconectar = PhotoImage(
            file=icono_desconectar).subsample(50)

        self.variable_estacionamiento = StringVar()

        database_list, self.opciones_conexiones = self.select_controller.get_db_list()

        # Se omite la creación automática de bases de datos.
        # Las bases se administrarán desde MariaDB.

        # Llama a la función interface() que configura la interfaz gráfica
        self.interface()

        # El administrador accede al catálogo local antes de cualquier reporte.
        if self.permiso == 'admin':
            self.panel_connect.after_idle(self.abrir_administracion)

        # Inicia el loop principal de la ventana
        self.panel_connect.mainloop()

    def interface(self):
        """
        Crea toda la interface para cambiar de conexion

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # Se crea un Label Frame principal para la sección superior
        seccion_superior = ttk.LabelFrame(self.panel_connect, text='')
        seccion_superior.columnconfigure(1, weight=1)
        seccion_superior.propagate(True)
        seccion_superior.grid(row=0, column=0, sticky=tk.NSEW)

        # Se crea otro Label Frame para la sección del logo dentro del Label Frame principal
        seccion_logo = ttk.LabelFrame(seccion_superior, text='')
        seccion_logo.grid(row=0, column=0, sticky=tk.NSEW)

        # Se crea una etiqueta con la imagen del logo dentro del Label Frame de la sección del logo
        etiqueta_logo = ttk.Label(seccion_logo, image=self.logo_pase)
        etiqueta_logo.grid(row=0, column=0, sticky=tk.NSEW)

        # Crea un LabelFrame para los botones de desconectar y salir
        seccion_botones_salir = ttk.LabelFrame(seccion_superior, text='Salir')
        seccion_botones_salir.grid(row=0, column=3, padx=5, sticky='NW')

        # Crea un botón y lo empaqueta en la seccion_botones_salir
        boton_desconectar = ttk.Button(
            seccion_botones_salir, text='Desconectar', command=self.salir,  image=self.icono_desconectar)
        boton_desconectar.grid(row=0, column=0, padx=5, pady=5)

        # Se crea un Label Frame para la sección de la conexión
        seccion_conecion = ttk.LabelFrame(
            self.panel_connect, text='Selecciona la conexión')
        seccion_conecion.columnconfigure(1, weight=1)
        seccion_conecion.propagate(True)
        seccion_conecion.grid(row=1, column=0)

        # Se definen las opciones de conexión y se crea una ComboBox para seleccionar una opción
        etiqueta_bienvenida = ttk.Label(
            seccion_conecion, text=f'Bienvenido/a: {self.user_name}')
        etiqueta_bienvenida.grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        self.lista_desplegable_opciones = ttk.Combobox(
            seccion_conecion, values=self.opciones_conexiones, textvariable=self.variable_estacionamiento, state='readonly', width=30, height=5)
        self.lista_desplegable_opciones.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.lista_desplegable_opciones.configure(foreground="black")


        # Se crea un Label Frame para la sección de los botones
        seccion_botones = ttk.LabelFrame(self.panel_connect, text='')
        seccion_botones.grid(row=2, column=0)

        # Se crea un botón para conectarse a la opción seleccionada
        self.boton_seleccionar = ttk.Button(seccion_botones, text='Cargar información',
                                            command=self.cargar_informacion)

        self.boton_seleccionar.grid(row=0, column=0, padx=5, pady=5)
        self.estado_catalogo = ttk.Label(seccion_botones, text='')
        self.estado_catalogo.grid(row=1, column=0)
        if self.permiso == 'admin':
            ttk.Button(seccion_botones, text='Administrar estacionamientos', command=self.abrir_administracion).grid(row=2, column=0, pady=5)
            ttk.Label(seccion_botones, text='Administrar estacionamientos usa el archivo local.\nCargar información conecta a MariaDB.').grid(row=3, column=0, padx=5, pady=5)
            ttk.Button(seccion_botones, text='Estado de actualización', command=self.abrir_estado_actualizacion).grid(row=4, column=0, padx=5, pady=5)
        self.actualizar_estacionamientos()

    def actualizar_estacionamientos(self, propagar_error=False):
        anterior = self.variable_estacionamiento.get()
        _, self.opciones_conexiones = self.select_controller.get_db_list(propagar_error=propagar_error)
        self.lista_desplegable_opciones.configure(values=self.opciones_conexiones)
        self.variable_estacionamiento.set(anterior if anterior in self.opciones_conexiones else (self.opciones_conexiones[0] if self.opciones_conexiones else ''))
        self.lista_desplegable_opciones.configure(state='readonly' if self.opciones_conexiones else 'disabled')
        self.boton_seleccionar.configure(state='normal' if self.opciones_conexiones else 'disabled')
        self.estado_catalogo.configure(text='' if self.opciones_conexiones else 'No hay estacionamientos activos.')

    def abrir_administracion(self):
        from tkinter import messagebox
        try:
            ventana = getattr(self, 'admin_estacionamientos', None)
            if ventana is not None and ventana.window.winfo_exists():
                ventana.window.lift()
                return
            self.admin_estacionamientos = self.select_controller.abrir_administracion(self.panel_connect, lambda: self.actualizar_estacionamientos(propagar_error=True))
        except (PermissionError, ValueError, OSError):
            messagebox.showerror('Administración', 'No se pudo abrir la administración.')

    def abrir_estado_actualizacion(self):
        from tkinter import messagebox
        try:
            ventana = getattr(self, 'estado_actualizacion', None)
            if ventana is not None and ventana.window.winfo_exists():
                ventana.refrescar()
                ventana.window.lift()
                return
            self.estado_actualizacion = self.select_controller.abrir_estado_actualizacion(self.panel_connect)
        except (OSError, ValueError):
            messagebox.showerror('Estado de actualización', 'No se pudo leer el catálogo local.', parent=self.panel_connect)

    def cargar_informacion(self):
        if not self.variable_estacionamiento.get():
            return
        self.desactivar()
        try:
            self.select_controller.conectar(self.variable_estacionamiento.get(), self.user_name, self.reportes)
        finally:
            self.activar()





    def salir(self):
        """
        Destruye el panel principal.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # Detiene el loop principal
        self.panel_connect.quit()
        # Destruye el panel principal
        self.panel_connect.destroy()

    def desactivar(self):
        """
        Desactiva los botones de la interface

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.panel_connect.withdraw()  # oculta la ventana
        self.boton_seleccionar.config(state="disable")

    def activar(self):
        """
        Activa los botones de la interface

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.panel_connect.deiconify()
        self.actualizar_estacionamientos()

    def desconectar(self):
        """
        Elimina el panel y detiene la ejecución del hilo donde se ejecuta la ventana

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # detener el loop principal
        self.panel_connect.quit()
        # Destruye el panel principal
        self.panel_connect.destroy()

    def salir(self):
        """
        Muestra un cuadro de diálogo para informar al usuario que se está cerrando la aplicación y detiene la ejecución del programa.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.desconectar()
        raise SystemExit
