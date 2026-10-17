from Tools.proyect_tools import Tools
from Controller.controller_panel_general import Controller_Panel_General
from Models.queries import Queries

import tkinter as tk
from tkinter import ttk
from tkinter import StringVar
from tkinter import PhotoImage

from PIL import ImageTk, Image


class View_Panel_General:
    """
    Clase principal que maneja la interfaz gráfica del usuario.

    :param user_name (str): Nombre de usuario.
    :param estacionamiento (str): Nombre del estacionamiento.
    :param query (Queries): Objeto de tipo Queries que tiene la conexion a la base de datos.

    :raises None: 

    :return:
        - None
    """

    def __init__(self,
                 user_name=None,
                 estacionamiento=None,
                 query:Queries=None):
        """
        Constructor de la clase. Crea la ventana principal, la tabla y los campos de consulta.

        :param user_name (str): Nombre de usuario.
        :param estacionamiento (str): Nombre del estacionamiento.
        :param query (Queries): Objeto de tipo Queries que tiene la conexion a la base de datos.

        :raises None: 

        :return:
            - None
        """
        self.user_name = user_name
        self.estacionamiento = estacionamiento
        self.query = query

        # Crea las variables para almacenar los registros y las consultas a la base de datos
        self.registros = None
        self.parametros = ''
        self.promociones = ''

        if self.query.data_base.connection:

            # Crea la ventana principal
            self.panel = tk.Toplevel()
            # se elimina la funcinalidad del boton de cerrar
            self.panel.protocol("WM_DELETE_WINDOW", lambda: self.desconectar())
            # deshabilita los botones de minimizar y maximizar
            # self.panel.attributes('-toolwindow', True)

            ancho_max = self.panel.winfo_screenwidth()
            alto_max = self.panel.winfo_screenheight()

            # Establece el tamaño de la ventana y su título
            pos_x = int(ancho_max/3)
            pos_y = 10
            self.panel.geometry(f"+{pos_x}+{pos_y}")
            self.panel.resizable(False, True)

            self.panel.title(f'Panel de administración reporte general')

            # Configura la columna principal del panel para que use todo el espacio disponible
            self.panel.columnconfigure(0, weight=1)

            self.max_size_x = None
            self.max_size_y = None

            # Crea las variables para el reporte general
            self.variable_folio = StringVar()

            self.variable_tipo_tarifa_preferente = ''

            self.variable_fecha_inicio_entrada = StringVar()
            self.variable_fecha_fin_entrada = StringVar()

            self.variable_fecha_inicio_entrada = StringVar()
            self.variable_fecha_fin_entrada = StringVar()

            self.variable_corte_numero = StringVar()
            self.variable_corte_inicio = StringVar()
            self.variable_corte_fin = StringVar()

            self.variable_importe = StringVar()
            self.variable_importe_inicio = StringVar()
            self.variable_importe_final = StringVar()

            # instancia de la clase de herramientas
            tools_instance = Tools()

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

            # Crea las variables para el manejo de calendario
            self.calendario_fecha_inicio_entrada = None
            self.fecha_hora_inicio_entrada = None
            self.calendario_fecha_fin_entrada = None
            self.fecha_hora_fin_entrada = None

            self.controlador_entrada = Controller_Panel_General(
                estacionamiento=self.estacionamiento,
                user_name=self.user_name,
                query=self.query)
            self.tabla = None

            self.opciones_corte = self.query.obtener_lista_de(
                'Cortes', 'Folio', 'D')
            self.opciones_importe = self.query.obtener_lista_de(
                'Entradas', 'Importe', 'A')
            self.tarifas = self.query.obtener_lista_de(
                'Entradas', 'TarifaPreferente')

            # Crea la tabla y los campos de consulta
            self.view_tabla()
            self.view_campos_consulta()

            # Inicia el loop principal de la ventana
            self.panel.mainloop()
        else:
            return None

    def view_campos_consulta(self):
        """
        Crea y empaqueta los campos de consulta en la ventana.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # Label frame principal
        seccion_superior = ttk.LabelFrame(self.panel, text='')
        seccion_superior.columnconfigure(1, weight=1)
        # seccion_superior.grid_propagate(True)
        seccion_superior.propagate(True)
        seccion_superior.grid(row=0, column=0, sticky=tk.NSEW)

        self.opciones_minutos = ['00', '01', '02', '03', '04', '05',
                                 '10', '15', '20', '25', '30', '35', '40', '45', '50', '55']
        self.opciones_horas = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
                               '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24']
        # self.opciones_minutos = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
        # self.opciones_horas = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

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
            seccion_botones_consulta, text='Realizar consulta', command=self.consulta_entrada, width=16)
        boton_consulta.grid(row=0, column=0, padx=5, pady=5)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_generar_reporte = ttk.Button(seccion_botones_consulta, text='Generar reporte', compound='left', width=16,
                                           command=lambda:
                                           {
                                               self.controlador_entrada.realizar_reporte_general(
                                                   registros=self.registros, parametros=self.parametros, promociones=self.promociones),
                                           })
        boton_generar_reporte.grid(row=0, column=1, padx=5, pady=5)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_limpiar_campos = ttk.Button(
            seccion_botones_consulta,  text='Limpiar campos', command=self.vaciar_campos_general, width=16)
        boton_limpiar_campos.grid(row=1, column=0, padx=5, pady=5)

        # Crea un botón y lo empaqueta en la seccion_botones_consulta
        boton_vaciar_campos = ttk.Button(
            seccion_botones_consulta,  text='Vaciar tabla', command=self.limpiar_registros, width=16)
        boton_vaciar_campos.grid(row=1, column=1, padx=5, pady=5)

        # Crea un LabelFrame para los botones de desconectar y salir
        seccion_botones_salir = ttk.LabelFrame(seccion_superior, text='Salir')
        seccion_botones_salir.grid(row=0, column=3, padx=5, sticky='NW')

        # Crea un botón y lo empaqueta en la seccion_botones_salir
        boton_desconectar = ttk.Button(
            seccion_botones_salir, text='Desconectar', command=self.salir,  image=self.icono_desconectar)
        boton_desconectar.grid(row=0, column=0, padx=5, pady=5)
        ##########################################################################################################

        # R E P O R T E  G E N E R A L
        #########################################################################################################
        seccion_reporte_general = ttk.Frame(self.panel)
        seccion_reporte_general.grid(row=1, column=0, sticky=tk.N)

        ##########################################################################################################
        # R E P O R T E  G E N E R A L  S I M P L E
        notebook_consulta_general = ttk.Notebook(seccion_reporte_general)
        ##########################################################################################################
        seccion_reporte_simple = ttk.Frame(
            notebook_consulta_general)
        notebook_consulta_general.add(
            seccion_reporte_simple, text="Reporte simple")

        #####################################################
        seccion_fechas = ttk.LabelFrame(
            seccion_reporte_simple, text='Filtro por fechas')
        #seccion_fechas.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N)
        ##########################
        # Crear un Frame para las entradas
        seccion_entrada = ttk.Frame(seccion_fechas)
        seccion_entrada.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N)

        # Crear el boton para el calendario entrada inicio
        boton_calendario_inicio_entrada_simple = ttk.Button(seccion_entrada, image=self.icono_calendario,
                                                            command=lambda: {
                                                                boton_calendario_inicio_entrada_simple.config(
                                                                    state="disable"),
                                                                self.controlador_entrada.actualizar_fecha(
                                                                    limite="Inicio",
                                                                    # calendario=self.calendario_fecha_inicio_entrada,
                                                                    fecha=self.fecha_hora_inicio_entrada,
                                                                    variable=self.variable_fecha_inicio_entrada,
                                                                    campo_texto=self.campo_texto_entrada_fecha_inicio_simple),
                                                                boton_calendario_inicio_entrada_simple.config(
                                                                    state="normal")
                                                            })
        boton_calendario_inicio_entrada_simple.grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # Crear las leyendas para los campos de texto de las entradas
        etiqueta_fecha_inicio_entrada = ttk.Label(
            seccion_entrada, text='Fecha inicio:')
        etiqueta_fecha_inicio_entrada.grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # Crear los campos de texto para las entradas
        self.campo_texto_entrada_fecha_inicio_simple = ttk.Label(
            seccion_entrada, text='', width=19)
        self.campo_texto_entrada_fecha_inicio_simple.grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W)

        boton_borrar_fecha_fin_inicio = ttk.Button(seccion_entrada, image=self.icono_borrar,
                                                   command=lambda: {
                                                       self.campo_texto_entrada_fecha_inicio_simple.config(
                                                           text=""),
                                                       self.variable_fecha_inicio_entrada.set(
                                                           '')
                                                   })
        boton_borrar_fecha_fin_inicio.grid(
            row=0, column=3, padx=5, pady=5, sticky=tk.NW)
        ##########################

        ##########################
        # Crear el boton para el calendario entrada fin
        boton_calendario_fin_entrada_simple = ttk.Button(seccion_entrada, image=self.icono_calendario,
                                                         command=lambda: {
                                                             boton_calendario_fin_entrada_simple.config(
                                                                 state="disable"),
                                                             self.controlador_entrada.actualizar_fecha(
                                                                 limite="Final",
                                                                 fecha=self.fecha_hora_fin_entrada,
                                                                 variable=self.variable_fecha_fin_entrada,
                                                                 campo_texto=self.campo_texto_entrada_fecha_fin_simple),
                                                             boton_calendario_fin_entrada_simple.config(
                                                                 state="normal")
                                                         })
        boton_calendario_fin_entrada_simple.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W)

        # Crear las leyendas para los campos de texto de las entradas
        etiqueta_fecha_fin_entrada = ttk.Label(
            seccion_entrada, text='Fecha final:')
        etiqueta_fecha_fin_entrada.grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # Crear los campos de texto para las entradas
        self.campo_texto_entrada_fecha_fin_simple = ttk.Label(
            seccion_entrada, text='')
        self.campo_texto_entrada_fecha_fin_simple.grid(
            row=1, column=2, padx=5, pady=5, sticky=tk.W)

        boton_borrar_fecha_fin_entrada = ttk.Button(seccion_entrada, image=self.icono_borrar,
                                                    command=lambda: {
                                                        self.campo_texto_entrada_fecha_fin_simple.config(
                                                            text=""),
                                                        self.variable_fecha_fin_entrada.set(
                                                            '')
                                                    })
        boton_borrar_fecha_fin_entrada.grid(
            row=1, column=3, padx=5, pady=5, sticky=tk.NW)
        ##########################
        #####################################################

        #####################################################
        seccion_cortes = ttk.LabelFrame(
            seccion_reporte_simple, text='Filtro por cortes')
        seccion_cortes.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NW)

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
        #####################################################

        #####################################################
        seccion_n_boleto = ttk.LabelFrame(
            seccion_reporte_simple, text='Consulta boleto')
        seccion_n_boleto.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NW)
        # Crear la leyenda para el campo de texto de la consulta de folio
        etiqueta_folio = ttk.Label(seccion_n_boleto,  text='N° de boleto: ')
        etiqueta_folio.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # Crear la caja de texto
        self.caja_texto_boleto = ttk.Entry(
            seccion_n_boleto, textvariable=self.variable_folio, width=7)
        self.caja_texto_boleto.grid(row=0, column=1, padx=5, pady=5)

        boton_borrar_folio = ttk.Button(seccion_n_boleto, image=self.icono_borrar,
                                        command=lambda: {
                                            self.variable_folio.set(''),
                                        })
        boton_borrar_folio.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NW)
        #####################################################
        ##########################################################################################################
        self.max_size_x = seccion_reporte_simple.winfo_width()
        self.max_size_y = seccion_reporte_simple.winfo_height()

        # R E P O R T E  G E N E R A L  A V A N Z A D O
        ##########################################################################################################
        seccion_reporte_avanzada = ttk.LabelFrame(
            notebook_consulta_general, text='')
        seccion_reporte_avanzada.grid_propagate(True)
        notebook_consulta_general.add(
            seccion_reporte_avanzada, text="Reporte avanzado")
        #####################################################
        seccion_fechas = ttk.LabelFrame(
            seccion_reporte_avanzada, text='Filtro por fechas')
        #seccion_fechas.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW)
        ##########################
        # Crear un Frame para las entradas
        seccion_entrada = ttk.Frame(seccion_fechas)
        seccion_entrada.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N)

        # Crear el boton para el calendario entrada inicio
        boton_calendario_inicio_entrada = ttk.Button(seccion_entrada, image=self.icono_calendario,
                                                     command=lambda:
                                                     {
                                                         boton_calendario_inicio_entrada.config(
                                                             state="disable"),
                                                         self.controlador_entrada.actualizar_fecha(
                                                             limite="Inicio",
                                                             fecha=self.fecha_hora_inicio_entrada,
                                                             variable=self.variable_fecha_inicio_entrada,
                                                             campo_texto=self.campo_texto_entrada_fecha_inicio_avanzado),
                                                         boton_calendario_inicio_entrada.config(state="normal")})

        boton_calendario_inicio_entrada.grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # Crear las leyendas para los campos de texto de las entradas
        etiqueta_fecha_inicio_entrada = ttk.Label(
            seccion_entrada, text='Fecha inicio:')
        etiqueta_fecha_inicio_entrada.grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # Crear los campos de texto para las entradas
        self.campo_texto_entrada_fecha_inicio_avanzado = ttk.Label(
            seccion_entrada, text='', width=19)
        self.campo_texto_entrada_fecha_inicio_avanzado.grid(
            row=0, column=2, pady=5, sticky=tk.W)

        boton_borrar_fecha_fin_inicio = ttk.Button(seccion_entrada, image=self.icono_borrar,
                                                   command=lambda: {
                                                       self.campo_texto_entrada_fecha_inicio_avanzado.config(
                                                           text=""),
                                                       self.variable_fecha_inicio_entrada.set(
                                                           '')
                                                   })
        boton_borrar_fecha_fin_inicio.grid(
            row=0, column=3, padx=5, pady=5, sticky=tk.NW)
        ##########################

        ##########################
        # Crear el boton para el calendario entrada fin
        boton_calendario_fin_entrada = ttk.Button(seccion_entrada, image=self.icono_calendario,
                                                  command=lambda: {
                                                      boton_calendario_fin_entrada.config(
                                                          state="disable"),
                                                      self.controlador_entrada.actualizar_fecha(
                                                          limite="Final",
                                                          fecha=self.fecha_hora_fin_entrada,
                                                          variable=self.variable_fecha_fin_entrada,
                                                          campo_texto=self.campo_texto_entrada_fecha_fin_avanzado),
                                                      boton_calendario_fin_entrada.config(state="normal")})

        boton_calendario_fin_entrada.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W)

        # Crear las leyendas para los campos de texto de las entradas
        etiqueta_fecha_fin_entrada = ttk.Label(
            seccion_entrada, text='Fecha final:')
        etiqueta_fecha_fin_entrada.grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # Crear los campos de texto para las entradas
        self.campo_texto_entrada_fecha_fin_avanzado = ttk.Label(
            seccion_entrada, text='')
        self.campo_texto_entrada_fecha_fin_avanzado.grid(
            row=1, column=2, pady=5, sticky=tk.W)

        boton_borrar_fecha_fin_entrada = ttk.Button(seccion_entrada, image=self.icono_borrar,
                                                    command=lambda: {
                                                        self.campo_texto_entrada_fecha_fin_avanzado.config(
                                                            text=""),
                                                        self.variable_fecha_fin_entrada.set(
                                                            '')
                                                    })
        boton_borrar_fecha_fin_entrada.grid(
            row=1, column=3, padx=5, pady=5, sticky=tk.NW)
        ##########################
        #####################################################

        #####################################################
        seccion_cortes = ttk.LabelFrame(
            seccion_reporte_avanzada, text='Filtro por cortes')
        seccion_cortes.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NW)

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
        #####################################################

        #####################################################
        seccion_n_boleto = ttk.LabelFrame(
            seccion_reporte_avanzada, text='Consulta boleto')
        seccion_n_boleto.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NW)
        # Crear la leyenda para el campo de texto de la consulta de folio
        etiqueta_folio = ttk.Label(seccion_n_boleto,  text='N° de boleto: ')
        etiqueta_folio.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # Crear la caja de texto
        self.caja_texto_boleto = ttk.Entry(
            seccion_n_boleto, textvariable=self.variable_folio, width=7)
        self.caja_texto_boleto.grid(row=0, column=1, padx=5, pady=5)

        boton_borrar_folio = ttk.Button(seccion_n_boleto, image=self.icono_borrar,
                                        command=lambda: {
                                            self.variable_folio.set(''),
                                        })
        boton_borrar_folio.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NW)
        #####################################################

        #####################################################
        seccion_importe = ttk.LabelFrame(
            seccion_reporte_avanzada, text='Importe')
        seccion_importe.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NW)

        etiqueta_importe = ttk.Label(seccion_importe,  text='Importe: ')
        etiqueta_importe.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.lista_desplegable_ingreso = ttk.Combobox(
            seccion_importe,  values=self.opciones_importe, textvariable=self.variable_importe, state='readonly', height=5)
        self.lista_desplegable_ingreso.grid(row=0, column=1, padx=5, pady=5)
        boton_borrar_importe = ttk.Button(seccion_importe, image=self.icono_borrar,
                                          command=lambda:
                                          {
                                              self.variable_importe.set(''),
                                              self.lista_desplegable_ingreso.selection_clear()
                                          })
        boton_borrar_importe.grid(row=0, column=2, pady=5, sticky=tk.W)

        etiqueta_importe_inicio = ttk.Label(
            seccion_importe,  text='Importe inicio: ')
        etiqueta_importe_inicio.grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.lista_desplegable_ingreso_inicio = ttk.Combobox(
            seccion_importe,  values=self.opciones_importe, textvariable=self.variable_importe_inicio, state='readonly', height=5)
        self.lista_desplegable_ingreso_inicio.grid(
            row=1, column=1, padx=5, pady=5)
        boton_borrar_importe_inicio = ttk.Button(seccion_importe, image=self.icono_borrar,
                                                 command=lambda:
                                                 {
                                                     self.variable_importe_inicio.set(
                                                         ''),
                                                     self.lista_desplegable_ingreso_inicio.selection_clear()
                                                 })
        boton_borrar_importe_inicio.grid(row=1, column=2, pady=5, sticky=tk.W)

        etiqueta_importe_final = ttk.Label(
            seccion_importe,  text='Importe final: ')
        etiqueta_importe_final.grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.lista_desplegable_ingreso_final = ttk.Combobox(
            seccion_importe,  values=self.opciones_importe, textvariable=self.variable_importe_final, state='readonly', height=5)
        self.lista_desplegable_ingreso_final.grid(
            row=2, column=1, padx=5, pady=5)
        boton_borrar_importe_final = ttk.Button(seccion_importe, image=self.icono_borrar,
                                                command=lambda:
                                                {
                                                    self.variable_importe_final.set(
                                                        ''),
                                                    self.lista_desplegable_ingreso_final.selection_clear()
                                                })
        boton_borrar_importe_final.grid(
            row=2, column=2, padx=5, pady=5, sticky=tk.W)
        #####################################################

        #####################################################
        seccion_tarifas = ttk.LabelFrame(
            seccion_reporte_avanzada, text='Tarifas')
        seccion_tarifas.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NW)

        self.lista_tarifa_preferente = tk.Listbox(
            seccion_tarifas, selectmode="multiple", height=5)
        self.lista_tarifa_preferente.grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.NW)

        scrollbar = ttk.Scrollbar(
            seccion_tarifas, orient="vertical", command=self.lista_tarifa_preferente.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.lista_tarifa_preferente.configure(yscrollcommand=scrollbar.set)

        seccion_tarifas.rowconfigure(0, weight=1)
        seccion_tarifas.columnconfigure(0, weight=1)

        for tarifa in self.tarifas:
            self.lista_tarifa_preferente.insert(tk.END, tarifa)

        boton_borrar_tiempo_dentro_minuto_fin = ttk.Button(seccion_tarifas, image=self.icono_borrar,
                                                           command=lambda:
                                                           {
                                                               self.variable_tipo_tarifa_preferente == '',
                                                               self.lista_tarifa_preferente.selection_clear(
                                                                   0, 'end')
                                                           })
        boton_borrar_tiempo_dentro_minuto_fin.grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W)
        #####################################################
        notebook_consulta_general.bind(
            '<<NotebookTabChanged>>', lambda event: self.vaciar_campos_general())
        notebook_consulta_general.grid(row=0, column=0, sticky=tk.NW)
        ##########################################################################################################
        ##########################################################################################################

        # Establecer tamaño mínimo de la ventana
        ancho_min = notebook_consulta_general.winfo_width()
        alto_min = notebook_consulta_general.winfo_height()
        self.panel.wm_minsize(ancho_min, alto_min)

        ancho_max = self.panel.winfo_screenwidth()
        alto_max = self.panel.winfo_screenheight()
        self.panel.wm_maxsize(ancho_max, alto_max)

    def view_tabla(self):
        """
        Crea una tabla en la interfaz y la llena con los datos de la base de datos.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # Crea un Frame para la tabla y lo configura para llenar todo el espacio disponible

        seccion_tabla = ttk.LabelFrame(self.panel, text='')
        seccion_tabla.grid(row=2, column=0, sticky='NSEW', padx=5, pady=5)

        # Configurar las opciones columnspan y rowspan del LabelFrame
        self.panel.columnconfigure(0, weight=1)
        self.panel.rowconfigure(2, weight=1)
        seccion_tabla.columnconfigure(0, weight=1)
        seccion_tabla.rowconfigure(0, weight=1)

        # Obtiene los nombres de las columnas de la tabla que se va a mostrar
        columnas = ['N° boleto', 'Entrada', 'Salida', 'Tiempo',
                    'Importe', 'N° Corte', 'Placas', 'Promocion', 'Qr Promo']

        # Crea un Treeview con una columna por cada campo de la tabla
        self.tabla = ttk.Treeview(seccion_tabla, columns=(columnas))
        self.tabla.config(height=8)
        self.tabla.grid(row=0, column=0, sticky='NESW', padx=5, pady=5)

        # Define los encabezados de columna
        i = 1
        for headd in (columnas):
            self.tabla.heading(f'#{i}', text=headd)
            self.tabla.column(f'#{i}', width=100)
            i = i + 1
        self.tabla.column('#0', width=0, stretch=False)
        self.tabla.column('#1', width=90, stretch=False)

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

    def llenar_tabla(self,
                     registros):
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

    def vaciar_campos_general(self):
        """
        Limpia los campos de entrada de texto y variables de control en la interfaz gráfica.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        self.variable_folio.set('')

        self.variable_tipo_tarifa_preferente = ''

        self.variable_fecha_inicio_entrada.set('')
        self.variable_fecha_fin_entrada.set('')

        self.variable_corte_numero.set('')
        self.variable_corte_inicio.set('')
        self.variable_corte_fin.set('')

        self.variable_importe.set('')
        self.variable_importe_final.set('')
        self.variable_importe_inicio.set('')

        # Limpia los campos de consulta
        self.lista_tarifa_preferente.selection_clear(0, 'end')

        self.campo_texto_entrada_fecha_inicio_simple.config(text="")
        self.campo_texto_entrada_fecha_fin_simple.config(text="")

        self.campo_texto_entrada_fecha_inicio_avanzado.config(text="")
        self.campo_texto_entrada_fecha_fin_avanzado.config(text="")

        self.lista_desplegable_corte.selection_clear()
        self.lista_desplegable_corte_inicio.selection_clear()
        self.lista_desplegable_corte_final.selection_clear()

        self.lista_desplegable_ingreso.selection_clear()
        self.lista_desplegable_ingreso_inicio.selection_clear()
        self.lista_desplegable_ingreso_final.selection_clear()

    def obtener_variables(self):
        """
        Esta función se encarga de obtener las variables necesarias para crear un objeto de reserva
        a partir de los valores seleccionados por el usuario en la interfaz gráfica.

        La función utiliza widgets de tkinter para obtener los valores seleccionados por el usuario,
        y los almacena en variables que son utilizadas por otras funciones para crear el objeto de reserva.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # Obtener los índices de los elementos seleccionados en la lista de tarifa preferente
        indices_seleccionados = self.lista_tarifa_preferente.curselection()
        # Obtener los valores correspondientes a los índices seleccionados
        self.variable_tipo_tarifa_preferente = [
            self.lista_tarifa_preferente.get(i) for i in indices_seleccionados]

    def consulta_entrada(self):
        """
        Realiza una consulta de entrada con los parámetros proporcionados por el usuario y llena la tabla con los resultados obtenidos.

        :param None: 

        :raises None: 

        :return:
            - None
        """
        try:
            self.obtener_variables()

            # Se llama a la función de hacer_consulta entrada del controlador de entrada para obtener los registros correspondientes
            self.registros, self.parametros, self.promociones = self.controlador_entrada.hacer_consulta_entrada(
                id=self.variable_folio.get(),

                tarifa_preferente=self.variable_tipo_tarifa_preferente,

                fecha_inicio_entrada=self.variable_fecha_inicio_entrada.get(),
                fecha_fin_entrada=self.variable_fecha_fin_entrada.get(),

                corte_numero=self.variable_corte_numero.get(),
                corte_numero_inicio=self.variable_corte_inicio.get(),
                corte_numero_fin=self.variable_corte_fin.get(),

                ingreso=self.variable_importe.get(),
                ingreso_mayor=self.variable_importe_final.get(),
                ingreso_menor=self.variable_importe_inicio.get())

            # Se llena la tabla con los registros obtenidos
            self.llenar_tabla(self.registros)
        except Exception as e:
            print(e)

    def desconectar(self):
        """
        Elimina el panel y detiene la ejecución del hilo donde se ejecuta la ventana

        :param None: 

        :raises None: 

        :return:
            - None
        """
        # detener el loop principal
        self.panel.quit()
        # Destruye el panel principal
        self.panel.destroy()

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
