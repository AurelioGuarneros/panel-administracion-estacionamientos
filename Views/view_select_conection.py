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

        # Ventana amplia para conservar el selector a la izquierda y mostrar
        # el contenido de cada función en el panel derecho.
        ancho = min(1180, max(900, self.panel_connect.winfo_screenwidth() - 100))
        alto = min(700, max(560, self.panel_connect.winfo_screenheight() - 120))
        self.panel_connect.geometry(f'{ancho}x{alto}')
        self.panel_connect.minsize(900, 560)
        self.panel_connect.resizable(True, True)
        self.panel_connect.title(f'Selecciona la conexión')

        # Distribución horizontal: selector original a la izquierda y contenido a la derecha.
        self.panel_connect.columnconfigure(0, weight=0, minsize=330)
        self.panel_connect.columnconfigure(1, weight=1)
        self.panel_connect.rowconfigure(0, weight=1)

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
        self.panel_izquierdo = ttk.Frame(self.panel_connect, padding=(4, 4))
        self.panel_izquierdo.grid(row=0, column=0, sticky='nsew')
        self.panel_izquierdo.columnconfigure(0, weight=1)

        self.panel_derecho = ttk.LabelFrame(self.panel_connect, text='Área de trabajo', padding=10)
        self.panel_derecho.grid(row=0, column=1, sticky='nsew', padx=(4, 8), pady=8)
        self.panel_derecho.columnconfigure(0, weight=1)
        self.panel_derecho.rowconfigure(1, weight=1)
        self.titulo_contenido = ttk.Label(self.panel_derecho, text='Bienvenido al Panel de Administración', font=('TkDefaultFont', 12, 'bold'))
        self.titulo_contenido.grid(row=0, column=0, sticky='w', pady=(0, 8))
        self.contenido = ttk.Frame(self.panel_derecho)
        self.contenido.grid(row=1, column=0, sticky='nsew')
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.rowconfigure(0, weight=1)
        self.mostrar_inicio()

        # Se conserva el diseño original de los controles del lado izquierdo.
        seccion_superior = ttk.LabelFrame(self.panel_izquierdo, text='')
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
            self.panel_izquierdo, text='Selecciona la conexión')
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
        seccion_botones = ttk.LabelFrame(self.panel_izquierdo, text='')
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

    def limpiar_contenido(self, titulo):
        vista_estado = getattr(self, 'estado_actualizacion', None)
        if vista_estado is not None and getattr(vista_estado, 'ocupado', False):
            from tkinter import messagebox
            messagebox.showinfo('Actualización en curso',
                                'Espera a que termine la actualización antes de cambiar de función.',
                                parent=self.panel_connect)
            return False
        for widget in self.contenido.winfo_children():
            widget.destroy()
        self.titulo_contenido.configure(text=titulo)
        return True

    def mostrar_inicio(self):
        self.limpiar_contenido('Área de trabajo')
        ttk.Label(
            self.contenido,
            text='Selecciona una opción del lado izquierdo.\n\n'
                 'La información y las herramientas de cada botón aparecerán en esta área.',
            justify='left', wraplength=520
        ).grid(row=0, column=0, sticky='nw', padx=12, pady=12)

    def abrir_administracion(self):
        from tkinter import messagebox
        try:
            if not self.limpiar_contenido('Administrar estacionamientos'):
                return
            self.admin_estacionamientos = self.select_controller.abrir_administracion(
                self.panel_connect,
                lambda: self.actualizar_estacionamientos(propagar_error=True),
                container=self.contenido,
                on_close=self.mostrar_inicio
            )
        except (PermissionError, ValueError, OSError):
            messagebox.showerror('Administración', 'No se pudo abrir la administración.', parent=self.panel_connect)
            self.mostrar_inicio()

    def abrir_estado_actualizacion(self):
        from tkinter import messagebox
        try:
            if not self.limpiar_contenido('Estado de actualización'):
                return
            self.estado_actualizacion = self.select_controller.abrir_estado_actualizacion(
                self.panel_connect,
                container=self.contenido,
                on_close=self.mostrar_inicio
            )
        except (OSError, ValueError):
            messagebox.showerror('Estado de actualización', 'No se pudo leer el catálogo local.', parent=self.panel_connect)
            self.mostrar_inicio()

    def cargar_informacion(self):
        if not self.variable_estacionamiento.get():
            return
        if not self.limpiar_contenido('Cargar información'):
            return
        self.select_controller.conectar(
            self.variable_estacionamiento.get(), self.user_name,
            self.reportes, container=self.contenido
        )

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
