from Tools.proyect_tools import Tools
from Controller.controller_crud_usuarios_tpv import Controller_CRUD_usuarios
from Models.queries import Queries


from tkinter import messagebox as mb
import tkinter as tk
from tkinter import ttk
from tkinter import StringVar

from PIL import ImageTk, Image
from tkinter import PhotoImage


class View_CRUD_usuarios:

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

        self.panel_crud.title(f'Administración de usuarios')

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

        self.ID_usuario = tk.StringVar()

        self.registros = None

        self.controlador_crud_usuarios = Controller_CRUD_usuarios(
            estacionamiento=self.estacionamiento,
            user_name=self.user_name,
            query=self.query)

        # Llama a la función interface() que configura la interfaz gráfica
        self.interface()

        # # Calcula la posición de la ventana en la pantalla
        # pos_x = int(self.seccion_tabla.winfo_screenwidth() / 2)
        # pos_y = int(self.seccion_tabla.winfo_screenheight() / 2)

        # Establece la geometría de la ventana con su posición y tamaño
        self.panel_crud.geometry(f"850x500")
        # self.panel_crud.resizable(False, False)

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
        seccion_admin_usuarios = ttk.LabelFrame(
            seccion_superior, text=f'Bienvenido/a: {self.user_name}, estas conectado a -> {self.estacionamiento}')
        # seccion_admin_usuarios.columnconfigure(1, weight=1)
        # seccion_admin_usuarios.propagate(True)
        seccion_admin_usuarios.grid(row=0, column=1, sticky=tk.NW)

        seccion_botones_admin_usuarios = ttk.LabelFrame(
            seccion_admin_usuarios, text="Selecciona que deseas realizar")
        seccion_botones_admin_usuarios.grid(row=0, column=1, sticky=tk.NW)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_agregar_usuario = ttk.Button(seccion_botones_admin_usuarios,  text='Agregar usuario',
                                           command=lambda: {
                                               # self.desactivar(),
                                               self.controlador_crud_usuarios.agregar_usuarios(),
                                               self.ver_usuarios(),
                                               # self.activar(),
                                           }, width=16)
        boton_agregar_usuario.grid(row=0, column=0, padx=5, pady=5)

        # Crea la etiqueta para el campo de entrada de texto del nombre de usuario
        etiqueta_user = ttk.Label(
            seccion_botones_admin_usuarios, text='Ingresa el nombre del usuario: ')
        etiqueta_user.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # Crea el campo de entrada de texto para el nombre de usuario
        self. campo_user = ttk.Entry(
            seccion_botones_admin_usuarios, textvariable=self.ID_usuario)
        self. campo_user.grid(row=0, column=2, padx=5, pady=5)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_modificar_usuario = ttk.Button(
            seccion_botones_admin_usuarios,  text='Modificar usuario', command=self.modificar_usuario, width=16)
        boton_modificar_usuario.grid(row=0, column=3, padx=5, pady=5)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_eliminar_usuario = ttk.Button(
            seccion_botones_admin_usuarios,  text='Eliminar usuario', command=self.eliminar_usuario, width=16)
        boton_eliminar_usuario.grid(row=0, column=4, padx=5, pady=5)

        # Crea un LabelFrame para los botones de desconectar y salir
        seccion_botones_salir = ttk.LabelFrame(seccion_superior, text='Salir')
        seccion_botones_salir.grid(row=0, column=3, padx=5, sticky='NW')

        # Crea un botón y lo empaqueta en la seccion_botones_salir
        boton_desconectar = ttk.Button(
            seccion_botones_salir, text='Desconectar', command=self.salir,  image=self.icono_desconectar)
        boton_desconectar.grid(row=0, column=0, padx=5, pady=5)
        ##########################################################################################################

        # Crea una tabla en la interfaz y la llena con los datos de la base de datos.

        # Crea un Frame para la tabla y lo configura para llenar todo el espacio disponible

        self.seccion_tabla = ttk.LabelFrame(self.panel_crud, text='')
        self.seccion_tabla.grid(row=2, column=0, sticky='NSEW', padx=5, pady=5)

        # Configurar las opciones columnspan y rowspan del LabelFrame
        self.panel_crud.columnconfigure(0, weight=1)
        self.panel_crud.rowconfigure(2, weight=1)
        self.seccion_tabla.columnconfigure(0, weight=1)
        self.seccion_tabla.rowconfigure(0, weight=1)

        # Obtiene los nombres de las columnas de la tabla que se va a mostrar
        columnas = ['ID', 'Nombre de usuario', 'Nombre completo',
                    'Fecha Alta', 'Telefono', 'Telefono de Emergencia', 'Sucursal']

        # Crea un Treeview con una columna por cada campo de la tabla
        self.tabla = ttk.Treeview(self.seccion_tabla, columns=(columnas))
        self.tabla.config(height=8)
        self.tabla.grid(row=0, column=0, sticky='NESW', padx=5, pady=5)

        # Define los encabezados de columna
        i = 1
        for headd in (columnas):
            self.tabla.heading(f'#{i}', text=headd)
            self.tabla.column(f'#{i}', width=100)
            i = i + 1
        self.tabla.column('#0', width=0, stretch=False)
        self.tabla.column('#1', width=25, stretch=False)
        self.tabla.column('#2', width=110, stretch=False)
        self.tabla.column('#3', width=210, stretch=False)
        self.tabla.column('#4', width=140, stretch=False)
        self.tabla.column('#5', width=100, stretch=False)
        self.tabla.column('#6', width=100, stretch=False)
        self.tabla.column('#7', width=120, stretch=False)

        # Crea un Scrollbar vertical y lo asocia con el Treeview
        scrollbar_Y = ttk.Scrollbar(
            self.seccion_tabla, orient='vertical', command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar_Y.set)
        scrollbar_Y.grid(row=0, column=1, sticky='NS')

        # Crea un Scrollbar horizontal y lo asocia con el Treeview
        scrollbar_X = ttk.Scrollbar(
            self.seccion_tabla, orient='horizontal', command=self.tabla.xview)
        self.tabla.configure(xscroll=scrollbar_X.set)
        scrollbar_X.grid(row=1, column=0, sticky='EW')

        # Empaqueta el Treeview en la ventana
        self.tabla.grid(row=0, column=0, sticky='NESW', padx=5,
                        pady=5, ipadx=5, ipady=5, columnspan=2, rowspan=2)

        # self.seccion_tabla.grid_propagate(False)
        self.seccion_tabla.grid_rowconfigure(
            0, weight=1, minsize=0)  # , maxsize=self.max_size_x)

        self.campo_user.focus()
        self.ver_usuarios()

    def llenar_tabla(self, registros):
        """
        Llena la tabla con los registros que cumplen con los criterios de búsqueda.

        :param registros (list): Un conjunto de tuplas que representan los registros obtenidos de la base de datos.

        :raises None: 

        :return:
            - None
        """
        # Limpia la tabla antes de llenarla con nuevos registros
        self.vaciar_tabla()

        if self.registros:
            for registro in registros:
                # Pasa los valores del registro como tupla
                self.tabla.insert('', 'end', values=registro)

    def vaciar_tabla(self):
        """
        Elimina todas las filas de la tabla.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # Elimina todas las filas de la tabla
        self.tabla.delete(*self.tabla.get_children())

    def consultar_usuario(self, id):
        self.registros = self.controlador_crud_usuarios.consultar_usuario(
            id=id)
        if self.registros:
            return True
        else:
            return False

    def ver_usuarios(self):
        self.registros = self.controlador_crud_usuarios.ver_usuarios()
        self.llenar_tabla(self.registros)
        self.campo_user.focus()

    def eliminar_usuario(self):
        id = self.ID_usuario.get()

        if id == "":
            mb.showerror("Error", "Ingresa un id")
            self.campo_user.focus()
            return None

        pregunta = mb.askokcancel(
            "Alerta", f"¿Estas seguro de elminar al usuario con folio: {id}?")
        if pregunta:
            if self.consultar_usuario(id):
                self.controlador_crud_usuarios.eliminar_usuarios(id)
                self.ver_usuarios()
                self.ID_usuario.set("")
                self.campo_user.focus()
            else:
                mb.showwarning(
                    "Error", f"No existe usuario con folio {id} o ya ha sido eliminado")
                self.ID_usuario.set("")
                self.ver_usuarios()
                self.campo_user.focus()
        else:
            self.ID_usuario.set("")
        self.campo_user.focus()

    def modificar_usuario(self):
        id = self.ID_usuario.get()

        if id == "":
            mb.showerror("Error", "Ingresa un nombre")
            self.campo_user.focus()
            return None

        pregunta = mb.askokcancel(
            "Alerta", f"¿Estas seguro de modificar al usuario con nombre: {id}?")
        if pregunta:
            if self.consultar_usuario(id):
                self.controlador_crud_usuarios.modificar_usuarios(id)
                self.ver_usuarios()
                self.ID_usuario.set("")
                self.campo_user.focus()
            else:
                mb.showwarning("Error", f"No existe usuario con nombre {id}")
                self.ID_usuario.set("")
                self.ver_usuarios()
                self.campo_user.focus()
        else:
            self.ID_usuario.set("")
            self.campo_user.focus()

    def desactivar(self):
        """
        Desactiva los botones de la interface

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.panel_crud.withdraw()  # oculta la ventana

    def activar(self):
        """
        Activa los botones de la interface

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.panel_crud.deiconify()

    def desconectar(self):
        """
        Elimina el panel y detiene la ejecución del hilo donde se ejecuta la ventana

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
