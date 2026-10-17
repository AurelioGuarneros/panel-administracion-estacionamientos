from Tools.proyect_tools import Tools
from Controller.controller_panel_dias import Controller_Panel_Dias
from Models.queries import Queries

import tkinter as tk
from tkinter import ttk
from tkinter import StringVar, IntVar
from tkinter import PhotoImage

from PIL import ImageTk, Image



class View_Panel_Dias:
    """
    Clase de la vista de selección de conexion.

    :param user_name (str): Nombre de usuario.
    :param estacionamiento (str): Nombre del estacionamiento.
    :param query (Queries): Objeto de tipo Queries que tiene la conexion a la base de datos.

    :raises None: 

    :return:
        - None
    """

    def __init__(self, user_name: str = None, estacionamiento: str = None, query: Queries = None):
        """
        Constructor de la clase. Crea la ventana principal, la tabla y los campos de consulta.

        :param user_name (str): Nombre de usuario.
        :param estacionamiento (str): Nombre del estacionamiento.
        :param query (Queries): Objeto de tipo Queries que tiene la conexion a la base de datos."""
        self.user_name = user_name
        self.estacionamiento = estacionamiento

        self.query = query

        if self.query.data_base.connection:
            # Crea la ventana principal
            self.panel_dias = tk.Toplevel()
            # instancia de la clase de herramientas
            tools_instance = Tools()
            # se elimina la funcinalidad del boton de cerrar
            self.panel_dias.protocol(
                "WM_DELETE_WINDOW", lambda: self.desconectar())
            # # deshabilita los botones de minimizar y maximizar
            # self.panel_dias.attributes('-toolwindow', True)
            # # coloca la ventana al frente de otras ventanas
            # self.panel_dias.attributes('-topmost', True)

            ancho_max = self.panel_dias.winfo_screenwidth()
            alto_max = self.panel_dias.winfo_screenheight()

            self.panel_dias.resizable(False, True)

            self.panel_dias.title(f'Panel de administración reporte dias')

            # Configura la columna principal del panel para que use todo el espacio disponible
            self.panel_dias.columnconfigure(0, weight=1)

            self.max_size_x = None
            self.max_size_y = None

            # Crea las variables para almacenar los registros y las consultas a la base de datos
            self.registros = None
            self.parametros = ''
            self.campos = ''

            # Crea las variables para los iconos e imagenes
            logo = tools_instance.read_path_config_file('images', 'logo_pase')
            logo_pase = Image.open(logo)
            # Cambiar tamaño de la imagen
            logo_pase = logo_pase.resize((106, 55), Image.LANCZOS)
            self.logo_pase = ImageTk.PhotoImage(logo_pase)

            icono_calendario = tools_instance.read_path_config_file(
                'images', 'icono_calendario')
            self.icono_calendario = PhotoImage(
                file=icono_calendario).subsample(25)

            icono_salir = tools_instance.read_path_config_file(
                'images', 'icono_salir')
            self.icono_salir = PhotoImage(file=icono_salir).subsample(50)

            icono_desconectar = tools_instance.read_path_config_file(
                'images', 'icono_desconectar')
            self.icono_desconectar = PhotoImage(
                file=icono_desconectar).subsample(50)

            icono_borrar = tools_instance.read_path_config_file(
                'images', 'icono_borrar')
            self.icono_borrar = PhotoImage(file=icono_borrar).subsample(25)

            self.font = ("Times", 16)

            self.variable_mes = StringVar()
            self.opciones_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

            self.variable_años = StringVar()
            self.opciones_años = [i for i in range(2020, 2041)]


            self.variable_corte_numero = StringVar()
            self.variable_corte_inicio = StringVar()
            self.variable_corte_fin = StringVar()

            self.opciones_corte = self.query.obtener_lista_de(
                'Cortes', 'Folio', 'D')

            # Obtiene los nombres de las columnas de la tabla que se va a mostrar
            self.columnas = 1

            self.controlador_dias = Controller_Panel_Dias(
                estacionamiento=self.estacionamiento,
                user_name=self.user_name,
                query=self.query)

            self.tabla = None

            self.view_campos_consulta()

            # Inicia el loop principal de la ventana
            self.panel_dias.mainloop()
        else:
            return None

    def view_campos_consulta(self):
        """Crea y empaqueta los campos de consulta en la ventana."""
        # Label frame principal
        seccion_superior = ttk.LabelFrame(self.panel_dias, text='')
        seccion_superior.columnconfigure(1, weight=1)
        # seccion_superior.grid_propagate(True)
        seccion_superior.propagate(True)
        seccion_superior.grid(row=0, column=0, sticky=tk.NSEW)

        ##########################################################################################################
        seccion_logo = ttk.LabelFrame(seccion_superior, text='')
        seccion_logo.grid(row=0, column=0, padx=5, sticky=tk.W)

        etiqueta_logo = tk.Label(seccion_logo, image=self.logo_pase)
        etiqueta_logo.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW)

        seccion_informacion = ttk.LabelFrame(
            seccion_superior, text='Información')
        seccion_informacion.grid(row=0, column=1, padx=5, sticky=tk.W)

        etiqueta_bienvenida = ttk.Label(
            seccion_informacion, text=f'Nombre: {self.user_name}', font=("Times", 12))
        etiqueta_bienvenida.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        etiqueta_bienvenida = ttk.Label(
            seccion_informacion, text=f'Estacionamiento: {self.estacionamiento}', font=("Times", 12))
        etiqueta_bienvenida.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        # Crea un LabelFrame para los botones de desconectar y salir
        seccion_botones_consulta = ttk.LabelFrame(
            seccion_superior, text='Botones consulta', width=16)
        seccion_botones_consulta.grid(row=0, column=2, padx=5, sticky=tk.NW)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_consulta = ttk.Button(
            seccion_botones_consulta, text='Realizar consulta', command=self.consulta_dias, width=16)
        boton_consulta.grid(row=0, column=0, padx=5, pady=5)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_generar_reporte = ttk.Button(seccion_botones_consulta, text='Generar reporte', compound='left', width=16,
                                           command=lambda:
                                           {
                                               self.controlador_dias.realizar_reporte_dias(
                                                   registros=self.registros, parametros=self.parametros, campos=self.campos),
                                           })
        boton_generar_reporte.grid(row=0, column=1, padx=5, pady=5)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_limpiar_campos = ttk.Button(
            seccion_botones_consulta,  text='Vaciar tabla', command=self.limpiar_registros, width=16)
        boton_limpiar_campos.grid(row=1, column=1, padx=5, pady=5)

        # Crea un LabelFrame para los botones de desconectar y salir
        seccion_botones_salir = ttk.LabelFrame(seccion_superior, text='Salir')
        seccion_botones_salir.grid(row=0, column=3, padx=5, sticky='NW')

        # Crea un botón y lo empaqueta en la seccion_botones_salir
        boton_desconectar = ttk.Button(
            seccion_botones_salir, text='Desconectar', command=self.salir,  image=self.icono_desconectar)
        boton_desconectar.grid(row=0, column=0, padx=5, pady=5)

        seccion_información = ttk.LabelFrame(
            self.panel_dias, text='Seleccione la información a consultar')
        seccion_información.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)

        # seccion_datos = ttk.Frame(seccion_información)
        # seccion_datos.grid(row=0, column=0, padx=5, pady=5)

        # etiqueta_mes = ttk.Label(
        #     seccion_datos, text='Seleccione Mes', font=self.font)
        # etiqueta_mes.grid(row=2, column=0, padx=5, pady=5)

        # self.lista_desplegable_meses = ttk.Combobox(
        #     seccion_datos, values=self.opciones_meses, textvariable=self.variable_mes, state='readonly', width=12,  height=5, font=self.font)
        # self.lista_desplegable_meses.grid(row=2, column=1, padx=5, pady=5)
        # self.lista_desplegable_meses.current(0)

        # etiqueta_año = ttk.Label(
        #     seccion_datos, text='Seleccione Año', font=self.font)
        # etiqueta_año.grid(row=3, column=0, padx=5, pady=5)

        # self.lista_desplegable_años = ttk.Combobox(
        #     seccion_datos, values=self.opciones_años, textvariable=self.variable_años, state='readonly', width=12,  height=5, font=self.font)
        # self.lista_desplegable_años.grid(row=3, column=1, padx=5, pady=5)
        # self.lista_desplegable_años.current(3)




        seccion_cortes = ttk.LabelFrame(
            self.panel_dias, text='Filtro por cortes')
        seccion_cortes.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)

        ###########################
        etiqueta_corte = ttk.Label(seccion_cortes,  text='Corte: ')
        etiqueta_corte.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.lista_desplegable_corte = ttk.Combobox(
            seccion_cortes,  values=self.opciones_corte, textvariable=self.variable_corte_numero, state='readonly', height=5)
        self.lista_desplegable_corte.grid(row=0, column=1, padx=5, pady=5)
        boton_borrar_corte = ttk.Button(seccion_cortes, image=self.icono_borrar,
                                        command=lambda:
                                        {
                                            self.variable_corte_numero.set(''),
                                            self.lista_desplegable_corte.selection_clear()
                                        })
        boton_borrar_corte.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ###########################

        ###########################
        etiqueta_corte_inicio = ttk.Label(
            seccion_cortes,  text='Corte inicio: ')
        etiqueta_corte_inicio.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.lista_desplegable_corte_inicio = ttk.Combobox(
            seccion_cortes,  values=self.opciones_corte, textvariable=self.variable_corte_inicio, state='readonly', height=5)
        self.lista_desplegable_corte_inicio.grid(
            row=1, column=1, padx=5, pady=5)
        boton_borrar_corte_inicio = ttk.Button(seccion_cortes, image=self.icono_borrar,
                                                command=lambda:
                                                {
                                                    self.variable_corte_inicio.set(
                                                        ''),
                                                    self.lista_desplegable_corte_inicio.selection_clear()
                                                })
        boton_borrar_corte_inicio.grid(
            row=1, column=2, padx=5, pady=5, sticky=tk.W)
        ###########################

        ###########################
        etiqueta_corte_final = ttk.Label(seccion_cortes,  text='Corte final: ')
        etiqueta_corte_final.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.lista_desplegable_corte_final = ttk.Combobox(
            seccion_cortes,  values=self.opciones_corte, textvariable=self.variable_corte_fin, state='readonly', height=5)
        self.lista_desplegable_corte_final.grid(
            row=2, column=1, padx=5, pady=5)
        boton_borrar_corte_final = ttk.Button(seccion_cortes, image=self.icono_borrar,
                                                command=lambda:
                                                {
                                                    self.variable_corte_fin.set(
                                                        ''),
                                                    self.lista_desplegable_corte_final.selection_clear()
                                                })
        boton_borrar_corte_final.grid(
            row=2, column=2, padx=5, pady=5, sticky=tk.W)
        ###########################








        # Establecer tamaño mínimo de la ventana
        # ancho_min = seccion_información.winfo_width()
        # alto_min = seccion_información.winfo_height()
        # self.panel_dias.wm_minsize(ancho_min, alto_min)

        ancho_max = self.panel_dias.winfo_screenwidth()
        alto_max = self.panel_dias.winfo_screenheight()
        self.panel_dias.wm_maxsize(ancho_max, alto_max)

    def llenar_tabla(self, registros: list) -> None:
        """
        Crea y empaqueta los campos de consulta en la ventana.

        :param registros (list): una lista de tuplas que contiene los registros obtenidos de la consulta.

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

    def consulta_dias(self):
        """
        Realiza una consulta de entrada con los parámetros proporcionados por el usuario y llena la tabla con los resultados obtenidos."""
        try:

            # Se llama a la función de hacer_consulta dias del controlador de dias para obtener los registros correspondientes
            self.registros, self.parametros, self.campos = self.controlador_dias.hacer_consulta_dias(
                corte_numero=self.variable_corte_numero.get(),
                corte_numero_inicio=self.variable_corte_inicio.get(),
                corte_numero_fin=self.variable_corte_fin.get())
                # year_param=int(self.variable_años.get()),
                # month_param=self.lista_desplegable_meses.current()+1)

            print(f'Parametros: {self.parametros}')
            print(f'Campos: {self.campos}')

            def view_tabla():
                """Función anidada para hacer la tabla con sus respectivos registros"""
                # Crea un Frame para la tabla y lo configura para llenar todo el espacio disponible
                seccion_tabla = ttk.LabelFrame(self.panel_dias, text='')
                seccion_tabla.grid(
                    row=2, column=0, sticky='NSEW', padx=5, pady=5)

                # Configurar las opciones columnspan y rowspan del LabelFrame
                self.panel_dias.columnconfigure(0, weight=1)
                self.panel_dias.rowconfigure(2, weight=1)
                seccion_tabla.columnconfigure(0, weight=1)
                seccion_tabla.rowconfigure(0, weight=1)

                # Crea un Treeview con una columna por cada campo de la tabla
                self.tabla = ttk.Treeview(seccion_tabla, columns=self.campos)
                self.tabla.config(height=8)
                self.tabla.grid(row=0, column=0, sticky='NESW', padx=5, pady=5)

                # Define los encabezados de columna
                i = 1
                for headd in (self.campos):
                    self.tabla.heading(f'#{i}', text=headd)
                    self.tabla.column(f'#{i}', width=100)
                    i = i + 1
                self.tabla.column('#0', width=0, stretch=False)
                self.tabla.column('#1', width=30, stretch=False)
                self.tabla.column('#2', width=70, stretch=False)

                # Crea un Scrollbar vertical y lo asocia con el Treeview
                scrollbar_Y = ttk.Scrollbar(
                    seccion_tabla, orient='vertical', command=self.tabla.yview)
                self.tabla.configure(yscroll=scrollbar_Y.set)
                scrollbar_Y.grid(row=0, column=1, sticky='NS')

                # Crea un Scrollbar horizontal y lo asocia con el Treeview
                scrollbar_X = ttk.Scrollbar(
                    seccion_tabla, orient='horizontal', command=self.tabla.xview)
                self.tabla.configure(xscroll=scrollbar_X.set)
                scrollbar_X.grid(row=1, column=0, sticky='EW')

                # Empaqueta el Treeview en la ventana
                self.tabla.grid(row=0, column=0, sticky='NESW', padx=5,
                                pady=5, ipadx=5, ipady=5, columnspan=2, rowspan=2)

                seccion_tabla.grid_propagate(False)
                seccion_tabla.grid_rowconfigure(
                    0, weight=1, minsize=0, maxsize=self.max_size_x)

            view_tabla()

            # Se llena la tabla con los registros obtenidos
            self.llenar_tabla(self.registros)
        except Exception as e:
            print(e)

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

    def limpiar_registros(self):
        """
        Elimina todos los registros de la variable registros y vacia la tabla

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.registros = None
        self.parametros = ''
        self.vaciar_tabla()

    def desconectar(self):
        """
        Cierra la ventana principal y detiene el hilo en el que se ejecuta.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # detener el loop principal
        self.panel_dias.quit()
        # Destruye el panel principal
        self.panel_dias.destroy()

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
