from Tools.proyect_tools import Tools

from tkinter import messagebox as mb
import tkinter as tk
from tkinter import ttk

from PIL import ImageTk, Image
from tkinter import PhotoImage

import json


class View_agregar_usuarios:

    def __init__(self, user_name=None):

        self.user_name = user_name

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

        self.user_settings_file = (self.tools_instance.read_path_config_file(
            'config_files', 'user_settings_file'))
        self.database_config_file = self.tools_instance.read_path_config_file(
            'config_files', "database_config_file")
        _, self.opciones_conexiones = self.get_db_list()

        self.usuario_nombre = tk.StringVar()
        self.usuario_nombre_completo = tk.StringVar()
        self.usuario_contraseña = tk.StringVar()
        self.usuario_permiso = tk.StringVar()
        self.usuario_conexion_defecto = tk.StringVar()

        self.permiso_reporte_general = tk.BooleanVar()
        self.permiso_reporte_pensionado = tk.BooleanVar()
        self.permiso_reporte_boletos = tk.BooleanVar()
        self.permiso_reporte_dias = tk.BooleanVar()
        self.permiso_reporte_ingresos_pensiones = tk.BooleanVar()
        self.permiso_reporte_cambios = tk.BooleanVar()


        self.permiso_reporte_general.set(True)
        self.permiso_reporte_pensionado.set(False)
        self.permiso_reporte_boletos.set(False)
        self.permiso_reporte_dias.set(False)
        self.permiso_reporte_ingresos_pensiones.set(False)
        self.permiso_reporte_cambios.set(False)

        self.registros = None

        # Obtiene la configuración seleccionada

        with open(self.user_settings_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

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
            seccion_superior, text=f'Bienvenido/a: {self.user_name}\n')
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
            seccion_datos_usuario, text='Permiso: ')
        etiqueta_nombre_usuario.grid(
            row=4, column=0, padx=5, pady=5, sticky=tk.W)

        permit = ["admin", "normal"]

        lista_desplegable_tema = ttk.Combobox(
            seccion_datos_usuario,  values=permit, textvariable=self.usuario_permiso, state='readonly', height=5)
        lista_desplegable_tema.grid(row=4, column=1, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_nombre_usuario = ttk.Label(
            seccion_datos_usuario, text='Conexion por defecto: ')
        etiqueta_nombre_usuario.grid(
            row=5, column=0, padx=5, pady=5, sticky=tk.W)

        lista_desplegable_conexion = ttk.Combobox(
            seccion_datos_usuario,  values=self.opciones_conexiones, textvariable=self.usuario_conexion_defecto, state='readonly', height=5)
        lista_desplegable_conexion.grid(row=5, column=1, padx=5, pady=5)
        lista_desplegable_conexion.current(0)

        seccion_permisos = ttk.LabelFrame(
            self.panel_crud, text='Seleccione los permisos de acceso a los reportes')
        seccion_permisos.grid(row=2, column=0, padx=10)

        checkbox_reportegeneral = ttk.Checkbutton(
            seccion_permisos, text='Reporte General', variable=self.permiso_reporte_general)
        checkbox_reportegeneral.grid(row=0, column=0, padx=5, sticky=tk.W)

        checkbox_reportegeneral = ttk.Checkbutton(
            seccion_permisos, text='Reporte Pensionado', variable=self.permiso_reporte_pensionado)
        checkbox_reportegeneral.grid(row=1, column=0, padx=5, sticky=tk.W)

        checkbox_reportedias = ttk.Checkbutton(
            seccion_permisos, text='Reporte Dias', variable=self.permiso_reporte_dias)
        checkbox_reportedias.grid(row=2, column=0, padx=5, sticky=tk.W)

        checkbox_reportegeneral = ttk.Checkbutton(
            seccion_permisos, text='Reporte Boletos/Ingresos', variable=self.permiso_reporte_boletos)
        checkbox_reportegeneral.grid(row=0, column=1, padx=5, sticky=tk.W)

        checkbox_reporte_ingresos_pensiones = ttk.Checkbutton(
            seccion_permisos, text='Reporte Ingresos Pensiones', variable=self.permiso_reporte_ingresos_pensiones)
        checkbox_reporte_ingresos_pensiones.grid(row=1, column=1, padx=5, sticky=tk.W)

        checkbox_reporte_ingresos_pensiones = ttk.Checkbutton(
            seccion_permisos, text='Reporte Cambios del sistema', variable=self.permiso_reporte_cambios)
        checkbox_reporte_ingresos_pensiones.grid(row=2, column=1, padx=5, sticky=tk.W)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_agregar_usuario = ttk.Button(
            self.panel_crud,  text='Agregar usuario', command=self.agregar_usuario, width=16)
        boton_agregar_usuario.grid(row=3, column=0, padx=5, pady=5)

        self.campo_nombre_usuario.focus()

    def agregar_usuario(self):
        try:
            usuario_nombre = self.usuario_nombre.get()
            usuario_nombre_completo = self.usuario_nombre_completo.get()
            usuario_contraseña = self.usuario_contraseña.get()
            usuario_permiso = self.usuario_permiso.get()
            usuario_conexion_defecto = self.usuario_conexion_defecto.get()

            permiso_reporte_general = self.permiso_reporte_general.get()
            permiso_reporte_pensionado = self.permiso_reporte_pensionado.get()
            permiso_reporte_boletos = self.permiso_reporte_boletos.get()
            permiso_reporte_dias = self.permiso_reporte_dias.get()
            permiso_reporte_ingresos_pensiones = self.permiso_reporte_ingresos_pensiones.get()
            permiso_reporte_cambios = self.permiso_reporte_cambios.get()

            if len(usuario_nombre) == 0 or len(usuario_contraseña) == 0 or len(usuario_nombre_completo) == 0 or len(usuario_permiso) == 0 or len(usuario_conexion_defecto) == 0:
                raise IndexError("No dejar campos en blanco")

            if permiso_reporte_general == False and permiso_reporte_pensionado == False and permiso_reporte_boletos == False and permiso_reporte_dias == False and permiso_reporte_cambios == False:
                raise IndexError("No puede haber un usuario sin permisos")

            if any(user['UserName'] == usuario_nombre for user in self.data['ussers']):
                mb.showerror(
                    "Error", "Ya existe un usuario con ese nombre de usuario, selecciona otro")
                self.campo_nombre_usuario.focus()
                self.usuario_nombre.set("")

                return

            if usuario_permiso == "admin":
                usuario_conexion_defecto = "N/A"

            nuevo_usuario = {
                "UserName": usuario_nombre,
                "Name": usuario_nombre_completo,
                "Password": usuario_contraseña,
                "Permits": usuario_permiso,
                "DefaultConection": usuario_conexion_defecto,
                "Reportes": {
                    "Reporte_General": permiso_reporte_general,
                    "Reporte_Pensionados": permiso_reporte_pensionado,
                    "Reporte_Boletos_Ingresos": permiso_reporte_boletos,
                    "Reporte_Dias": permiso_reporte_dias,
                    "Reporte_Ingresos_Pension": permiso_reporte_ingresos_pensiones,
                    "Reporte_Cambios_Sistema" :permiso_reporte_cambios
                }
            }

            self.data['ussers'].append(nuevo_usuario)

            # Guardar los cambios en el archivo JSON
            with open(self.user_settings_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)

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
        raise SystemExit

    def get_db_list(self):
        """
        Obtiene la lista de bases de datos disponibles y sus nombres de conexiones desde el archivo de configuración.

        :return: tuple[list, list] or None: Una tupla que contiene dos listas, la primera con las bases de datos y la segunda con los nombres de conexiones, o None si hay un error.
        """
        try:
            with open(self.database_config_file, "r", encoding='utf-8') as f:
                data = json.load(f)

            registros = [r for r in data['settings']
                         if r['name_config'] and r['name_config'] != 'Admin'
                         and r.get('activo', True) and r['database'] != 'db_test']
            self.nombres_actuales = {alias: r['name_config'] for r in data['settings']
                                     for alias in r.get('nombres_anteriores', [])}
            return ([r['database'] for r in registros],
                    [r['name_config'] for r in registros])

        except ValueError as e:
            # Si se lanza una excepción ValueError, muestra un mensaje de error
            tk.messagebox.showerror('Error', f'Error: {e}')
