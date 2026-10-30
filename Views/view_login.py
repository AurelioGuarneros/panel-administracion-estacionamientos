from Tools.proyect_tools import Tools
from Controller.controller_login import ControllerLogin

import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle
from PIL import ImageTk, Image


class View_Login:
    """
    Clase de la vista del login.
    """

    def __init__(self):
        """
        Inicializa una instancia de la clase Login y crea la ventana principal de la interface.
        """
        # Crea la ventana principal
        self.window_login = tk.Tk()

        # temas xd
        self.style = ThemedStyle(self.window_login)

        # Establece el tamaño de la ventana y su título
        self.window_login.title(f'Login')

        # Establece el tamaño máximo de la ventana para que ocupe toda la pantalla
        ancho_max = self.window_login.winfo_screenwidth()
        alto_max = self.window_login.winfo_screenheight()
        self.window_login.wm_maxsize(ancho_max, alto_max)

        # Establece la posición inicial de la ventana en la pantalla
        pos_x = int(ancho_max/3)
        pos_y = int(alto_max/10)
        self.window_login.geometry(f"+{pos_x}+{pos_y}")

        # Establece que la ventana no sea redimensionable
        self.window_login.resizable(False, False)

        # Crea las variables para los datos de usuario y tema
        self.user = tk.StringVar()
        self.password = tk.StringVar()
        self.theme = tk.StringVar()
        self.true_theme = None

        # Crea instancias de otras clases
        tools_instance = Tools()
        self.controller_login = ControllerLogin()

        # Crea las variables para los iconos e imágenes
        logo = tools_instance.read_path_config_file('images', 'logo_pase')
        logo_pase = Image.open(logo)
        # Cambiar tamaño de la imagen
        logo_pase = logo_pase.resize((212, 110), Image.LANCZOS)
        self.logo_pase = ImageTk.PhotoImage(logo_pase)

        # Llama al método "interface()" para construir la interfaz gráfica
        self.interface()

        # Inicia el loop principal de la ventana
        self.window_login.mainloop()

    def interface(self):
        """
            Define la interfaz gráfica de usuario.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # Crea un frame principal para la ventana
        self.seccion_principal = ttk.LabelFrame(self.window_login, text='')
        self.seccion_principal.grid(row=0, column=0, sticky=tk.NSEW)

        # Agrega el logo de la empresa
        logo = ttk.Label(self.seccion_principal, image=self.logo_pase)
        logo.grid(row=0, column=0)

        # Crea un frame para el formulario
        self.seccion_formulario = ttk.LabelFrame(
            self.seccion_principal, text='Ingresa los siguientes datos', padding=10)
        self.seccion_formulario.grid(row=1, column=0, sticky=tk.NSEW)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_user = ttk.Label(
            self.seccion_formulario, text='Nombre de usuario: ')
        etiqueta_user.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para el nombre de usuario
        campo_user = ttk.Entry(self.seccion_formulario, textvariable=self.user)
        campo_user.grid(row=0, column=1, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto de la contraseña
        etiqueta_password = ttk.Label(
            self.seccion_formulario, text='Contraseña: ')
        etiqueta_password.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para la contraseña
        campo_password = ttk.Entry(
            self.seccion_formulario, textvariable=self.password, show="*")
        campo_password.grid(row=1, column=1, padx=5, pady=5)

        # Crea el botón para ingresar los datos del usuario y llama al método get_data del controlador para procesar los datos
        self.boton_entrar = ttk.Button(self.seccion_formulario, text='Entrar',
                                       command=lambda: {
                                           self.desactivar(),
                                           self.controller_login.get_data(
                                               user=self.user.get(),
                                               password=self.password.get()),
                                           self.activar()
                                       })
        self.boton_entrar.grid(row=0, column=2, padx=5, pady=5)

        # Crea un frame para la sección del tema
        seccion_tema = ttk.LabelFrame(
            self.seccion_principal, text='Si lo deseas, selecciona un tema', padding=10)
        seccion_tema.grid(row=2, column=0, sticky=tk.NSEW)

        # Define la lista de temas
        THEMES = [
            'default',
            "adapta",
            "aquativo",
            "arc",
            "black",
            "blue",
            "breeze",
            "clearlooks",
            "elegance",
            "equilux",
            "itft1",
            "keramik",
            "kroc",
            "plastik",
            "radiance",
            "scidblue",
            "scidgreen",
            "scidgrey",
            "scidmint",
            "scidpink",
            "scidpurple",
            "scidsand",
            "smog",
            "ubuntu",
            "winxpblue",
            "yaru"
        ]

        # Crear una lista desplegable con los temas disponibles
        lista_desplegable_tema = ttk.Combobox(
            seccion_tema,  values=THEMES, textvariable=self.theme, state='readonly', height=5)
        lista_desplegable_tema.grid(row=2, column=0, padx=5, pady=5)

        # Crear un botón para seleccionar el tema
        self.boton_selecionar_tema = ttk.Button(
            seccion_tema, text='Seleccionar tema', command=lambda: self.seleccionar_tema(self.theme.get()))
        self.boton_selecionar_tema.grid(row=2, column=2, padx=5, pady=5)

    def seleccionar_tema(self,
                         theme=None):
        """
        Esta función cambia el tema de la interface a partir del argumento "theme".
        Si no se proporciona un tema específico, se mantendrá el tema actual.

        :param theme (str or None): El nombre del tema a utilizar en la interface.

        :raises None: 

        :return:
            - None
        """
        if theme:
            self.style.theme_use(theme)

    def desactivar(self):
        """
        Desactiva los botones de la interface

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.window_login.withdraw()  # oculta la ventana
        self.boton_entrar.config(state="disable")
        self.boton_selecionar_tema.config(state="disable")

    def activar(self):
        """
        Activa los botones de la interface

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.password.set("")
        self.window_login.deiconify()
        self.boton_entrar.config(state="normal")
        self.boton_selecionar_tema.config(state="normal")
