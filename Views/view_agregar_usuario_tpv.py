from Tools.proyect_tools import Tools
from Models.queries import Queries

from tkinter import messagebox as mb
import tkinter as tk
from tkinter import ttk
from tkinter import StringVar

from PIL import ImageTk, Image
from tkinter import PhotoImage

from datetime import datetime


class View_agregar_usuarios:

    def __init__(self, estacionamiento=None, user_name=None, query: Queries = None):

        self.estacionamiento = estacionamiento
        self.user_name = user_name
        self.query = query

        # Crea la ventana principal
        self.panel_crud = tk.Toplevel()

        # Se elimina la funcionalidad del botón de cerrar
        self.panel_crud.protocol(
            "WM_DELETE_WINDOW", lambda: self.desconectar())

        # Deshabilita los botones de minimizar y maximizar
        # self.panel_crud.attributes('-toolwindow', True)

        self.panel_crud.title(f'Agregar usuarios')

        # Configura la columna principal del panel para que use todo el espacio disponible
        self.panel_crud.columnconfigure(0, weight=1)

        # Crea las instancias de las clases Tools() y Controller_Select_Conection()
        self.tools_instance = Tools()

        # Crea las variables para los iconos e imágenes
        logo = self.tools_instance.read_path_config_file('images', 'logo_pase')
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

        self.usuario_nombre = tk.StringVar()
        self.usuario_nombre_completo = tk.StringVar()
        self.usuario_contraseña = tk.StringVar()
        self.usuario_telefono = tk.StringVar()
        self.usuario_telefono_emergencia = tk.StringVar()
        self.usuario_sucursal = tk.StringVar()

        self.registros = None

        # Llama a la función interface() que configura la interfaz gráfica
        self.interface()

        # # Calcula la posición de la ventana en la pantalla
        # pos_x = int(self.seccion_tabla.winfo_screenwidth() / 2)
        # pos_y = int(self.seccion_tabla.winfo_screenheight() / 2)

        # # Establece la geometría de la ventana con su posición y tamaño
        # self.panel_crud.geometry(f"+{pos_x}+{pos_y}")
        self.panel_crud.resizable(False, False)

        # Inicia el loop principal de la ventana
        self.panel_crud.mainloop()

    def interface(self):
        """
        Crea toda la interface para cambiar de conexion

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # Se crea un Label Frame principal para la sección superior
        seccion_superior = ttk.LabelFrame(self.panel_crud, text='')
        seccion_superior.columnconfigure(1, weight=1)
        seccion_superior.propagate(True)
        seccion_superior.grid(row=0, column=0, sticky=tk.NSEW)

        ##########################################################################################################
        seccion_logo = ttk.LabelFrame(seccion_superior, text='')
        seccion_logo.grid(row=0, column=0, padx=5, sticky=tk.W)

        etiqueta_logo = tk.Label(seccion_logo, image=self.logo_pase)
        etiqueta_logo.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW)

        # Se crea un Label Frame para la sección de la conexión
        etiqueta_user = ttk.Label(
            seccion_superior, text=f'Bienvenido/a: {self.user_name}\nEstas conectado a -> {self.estacionamiento}')
        etiqueta_user.grid(row=0, column=1, padx=5, pady=5)

        seccion_datos_usuario = ttk.LabelFrame(
            self.panel_crud, text="\tIngresa los datos del usuario a registrar")
        seccion_datos_usuario.grid(row=1, column=0, padx=10, pady=10)

        # Crea un LabelFrame para los botones de desconectar y salir
        seccion_botones_salir = ttk.LabelFrame(seccion_superior, text='Salir')
        seccion_botones_salir.grid(row=0, column=3, padx=5, sticky='NW')

        # Crea un botón y lo empaqueta en la seccion_botones_salir
        boton_desconectar = ttk.Button(
            seccion_botones_salir, text='Desconectar', command=self.salir,  image=self.icono_desconectar)
        boton_desconectar.grid(row=0, column=0, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_nombre_usuario = ttk.Label(
            seccion_datos_usuario, text='Nombre de usuario: ')
        etiqueta_nombre_usuario.grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para el nombre de usuario
        self.campo_nombre_usuario = ttk.Entry(
            seccion_datos_usuario, textvariable=self.usuario_nombre)
        self.campo_nombre_usuario.grid(row=0, column=1, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_nombre_usuario = ttk.Label(
            seccion_datos_usuario, text='Nombre completo: ')
        etiqueta_nombre_usuario.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para el nombre de usuario
        campo_nombre_usuario = ttk.Entry(
            seccion_datos_usuario, textvariable=self.usuario_nombre_completo)
        campo_nombre_usuario.grid(row=1, column=1, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_nombre_usuario = ttk.Label(
            seccion_datos_usuario, text='Contraseña: ')
        etiqueta_nombre_usuario.grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para el nombre de usuario
        campo_nombre_usuario = ttk.Entry(
            seccion_datos_usuario, textvariable=self.usuario_contraseña, show="*")
        campo_nombre_usuario.grid(row=2, column=1, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_nombre_usuario = ttk.Label(
            seccion_datos_usuario, text='Telefono: ')
        etiqueta_nombre_usuario.grid(
            row=4, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para el nombre de usuario
        campo_nombre_usuario = ttk.Entry(
            seccion_datos_usuario, textvariable=self.usuario_telefono)
        campo_nombre_usuario.grid(row=4, column=1, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_nombre_usuario = ttk.Label(
            seccion_datos_usuario, text='Telefono de emergencia: ')
        etiqueta_nombre_usuario.grid(
            row=5, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para el nombre de usuario
        campo_nombre_usuario = ttk.Entry(
            seccion_datos_usuario, textvariable=self.usuario_telefono_emergencia)
        campo_nombre_usuario.grid(row=5, column=1, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_nombre_usuario = ttk.Label(
            seccion_datos_usuario, text='Sucursal: ')
        etiqueta_nombre_usuario.grid(
            row=6, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para el nombre de usuario
        campo_nombre_usuario = ttk.Entry(
            seccion_datos_usuario, textvariable=self.usuario_sucursal)
        campo_nombre_usuario.grid(row=6, column=1, padx=5, pady=5)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_agregar_usuario = ttk.Button(
            self.panel_crud,  text='Agregar usuario', command=self.agregar_usuario, width=16)
        boton_agregar_usuario.grid(row=2, column=0, padx=5, pady=5)

        self.campo_nombre_usuario.focus()

    def agregar_usuario(self):
        try:
            usuario_nombre = self.usuario_nombre.get()
            usuario_contraseña = self.usuario_contraseña.get()
            usuario_nombre_completo = self.usuario_nombre_completo.get()
            usuario_fecha_alta = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            usuario_telefono = self.usuario_telefono.get()
            usuario_telefono_emergencia = self.usuario_telefono_emergencia.get()
            usuario_sucursal = self.usuario_sucursal.get()

            if len(usuario_nombre) == 0 or len(usuario_contraseña) == 0 or len(usuario_nombre_completo) == 0 or len(usuario_fecha_alta) == 0 or len(usuario_telefono) == 0 or len(usuario_telefono_emergencia) == 0 or len(usuario_sucursal) == 0:
                raise IndexError("No dejar campos en blanco")

            datos_usuario = [usuario_nombre, usuario_contraseña,  usuario_nombre_completo,
                             usuario_fecha_alta,  usuario_telefono,  usuario_telefono_emergencia,  usuario_sucursal]

            self.query.agregar_usuarios(datos_usuario)

            self.desconectar()
        except Exception as e:
            mb.showerror("Error", e)

    def desconectar(self):
        """
        Cierra la ventana principal y detiene el hilo en el que se ejecuta.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # detener el loop principal
        self.panel_crud.quit()
        # Destruye el panel principal
        self.panel_crud.destroy()

    def salir(self):
        """
        Muestra un cuadro de diálogo para informar al usuario que se está cerrando la aplicación y detiene la ejecución del programa.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.desconectar()
        self.query.data_base.close_connection()
        raise SystemExit
