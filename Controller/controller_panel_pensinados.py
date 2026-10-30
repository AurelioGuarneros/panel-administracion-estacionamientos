from Views.view_calendar import Calendar_date
from Tools.proyect_tools import Tools

from tkinter import filedialog
from tkinter import messagebox

import xlsxwriter
from xlsxwriter import exceptions

from datetime import datetime

import os


class Controller_Panel_Pensionados:
    """
    Controller del panel de pensionados.

    :param estacionamiento (str): Nombre del estacionamiento.
    :param user_name (str): Nombre de usuario.
    :param query (Queries): Objeto de tipo Queries que tiene la conexion a la base de datos.

    :raises None: 

    :return:
        - None
    """

    def __init__(self,
                 estacionamiento=None,
                 user_name=None,
                 query=None):
        """
        Constructor de la clase. Crea la ventana principal, la tabla y los campos de consulta.

        :param estacionamiento (str): Nombre del estacionamiento.
        :param user_name (str): Nombre de usuario.
        :param query (Queries): Objeto de tipo Queries que tiene la conexion a la base de datos.

        :raises None: 

        :return:
            - None
        """
        self.user_name = user_name
        self.estacionamiento = estacionamiento
        self.query = query
        self.tools_instance = Tools()

        # Define un diccionario con los nuevos nombres de clave
        self.nuevos_nombres = {
            'numero_tarjeta': 'N° Tarjeta',
            'nombre_cliente': 'Nombre',
            'apellido_1_cliente': 'Apellido M',
            'apellido_2_cliente': 'Apellido P',
            'fecha_inicio_entrada': 'Fecha de entrada inicio',
            'fecha_fin_entrada': 'Fecha de entrada final',
            'estado': 'Estado',
            'tiempo_dentro': 'Tiempo dentro',
            'tiempo_dentro_inicio': 'Tiempo dentro inicio',
            'tiempo_dentro_fin': 'Tiempo dentro final'
        }

    def actualizar_fecha(self,
                         limite="Inicio",
                         fecha=None,
                         variable=None,
                         campo_texto=None):
        """
        Actualiza la fecha y hora de inicio para la búsqueda de registros en la base de datos. 

        :param calendario (Calendar_date): instancia de la clase Calendar_date.
        :param fecha (str): fecha seleccionada por el usuario.
        :param variable (StringVar): variable que se utiliza para almacenar la fecha :param seleccionada.
        :param campo_texto (Label): caja de texto donde se muestra la fecha seleccionada.

        :raises None:

        :return:
            - None
        """
        # Crea una instabcia de la clase Calendar_date
        if limite == "Final":
            calendario = Calendar_date(horas=23, minutos=59, segundos=59)
            print("Calendario final")
        else:
            calendario = Calendar_date(horas=0, minutos=0, segundos=0)
            print("Calendario inicio")

        calendario.mostrar_calendario()

        # Guarda el valor de selected_datetime dentro de la variable fecha
        fecha = calendario.selected_datetime

        # Reasigna el valor de la variable por fecha
        variable.set(fecha)

        # Elimina cualquier texto existente en la caja de texto
        campo_texto.config(text="")

        # Inserta el nuevo valor en la caja de texto
        campo_texto.config(text=fecha)

    def hacer_consulta_pensionados(self,
                                   numero_tarjeta: int,
                                   nombre_cliente: str,
                                   apellido_1_cliente: str,
                                   apellido_2_cliente: str,
                                   fecha_inicio_entrada: str,
                                   fecha_fin_entrada: str,
                                   estado: str,
                                   tiempo_dentro: str,
                                   tiempo_dentro_inicio: str,
                                   tiempo_dentro_fin: str,
                                   ) -> list:
        """
        Realiza una consulta en la base de datos con los parámetros especificados y devuelve una lista de registros y los parámetros de la consulta.

        :param numero_tarjeta (int): número de tarjeta a consultar.
        :param nombre_cliente (str): nombre de cliente a consultar.
        :param apellido_1_cliente (str): primer apellido a consultar.
        :param apellido_2_cliente (str): segundo apellido a consultar.
        :param fecha_inicio_entrada (str): fecha de inicio de entrada en formato yyyy-mm-dd hh:mm:ss para consultar.
        :param fecha_fin_entrada (str): fecha de fin de entrada en formato yyyy-mm-dd hh:mm:ss para consultar.
        :param estado (str): Estado del pensinado a consultar.
        :param tiempo_dentro (str): tiempo a consultar.
        :param tiempo_dentro_inicio (str): tiempo de inicio a consultar.
        :param tiempo_dentro_fin (str): tiempo final a consultar.

        :return:
            - registros (list): una lista de tuplas que contiene los registros obtenidos de la consulta.
            - parametros (list): una lista de que contiene los parámetros con los que se hizo la consulta.

        :raises: ValueError si los campos para la consulta están vacíos. TypeError si el dato ingresado no es válido.

        """
        try:
            parametros = {}

            # Obtener los valores de los campos de consulta
            self.numero_tarjeta = numero_tarjeta
            self.nombre_cliente = nombre_cliente
            self.apellido_1_cliente = apellido_1_cliente
            self.apellido_2_cliente = apellido_2_cliente
            self.fecha_inicio_entrada = fecha_inicio_entrada
            self.fecha_fin_entrada = fecha_fin_entrada
            self.estado = estado

            # Validar y agregar los parámetros a la consulta
            ##########################################################################################################
            if self.numero_tarjeta != '':
                parametros['numero_tarjeta'] = int(self.numero_tarjeta)
            ##########################################################################################################
            if self.nombre_cliente != '':
                parametros['nombre_cliente'] = str(self.nombre_cliente)
            ##########################################################################################################
            if self.apellido_1_cliente != '':
                parametros['apellido_1_cliente'] = str(self.apellido_1_cliente)
            ##########################################################################################################
            if self.apellido_2_cliente != '':
                parametros['apellido_2_cliente'] = str(self.apellido_2_cliente)
            ##########################################################################################################
            if self.fecha_inicio_entrada != '':
                if len(self.fecha_inicio_entrada) != 19:
                    raise ValueError(
                        'Error, La cantidad de caracteres no corresponde al formato de fecha')
                parametros['fecha_inicio_entrada'] = str(fecha_inicio_entrada)

            if self.fecha_fin_entrada != '':
                if len(self.fecha_fin_entrada) != 19:
                    raise ValueError(
                        'Error, La cantidad de caracteres no corresponde al formato de fecha')
                parametros['fecha_fin_entrada'] = str(self.fecha_fin_entrada)

            if 'fecha_inicio_entrada' in parametros and 'fecha_fin_entrada' in parametros:
                if parametros['fecha_inicio_entrada'] > parametros['fecha_fin_entrada']:
                    raise ValueError(
                        "La fecha de inicio debe ser menor o igual que la fecha final.")
            ##########################################################################################################
            if self.estado != '':
                parametros['estado'] = str(self.estado)
            ##########################################################################################################
            if tiempo_dentro != '' and tiempo_dentro != '0:00:00':
                parametros['tiempo_dentro'] = str(tiempo_dentro)

            if tiempo_dentro_inicio != '' and tiempo_dentro_inicio != '0:00:00':
                parametros['tiempo_dentro_inicio'] = str(tiempo_dentro_inicio)

            if tiempo_dentro_fin != '' and tiempo_dentro_fin != '0:00:59':
                parametros['tiempo_dentro_fin'] = str(tiempo_dentro_fin)

            if 'tiempo_dentro_inicio' in parametros and 'tiempo_dentro_fin' in parametros:
                if parametros['tiempo_dentro_inicio'] > parametros['tiempo_dentro_fin']:
                    raise ValueError(
                        "El tiempo de inicio debe ser menor o igual que el tiempo final.")
            ##########################################################################################################

            # Validar que se hayan proporcionado parámetros para la consulta
            if parametros == {}:
                raise ValueError('Los campos están vacíos')

            # Realizar la consulta y devolver la lista de registros obtenidos
            registros = self.query.hacer_consulta_sql_pensionados(parametros)
            return registros, parametros

        except ValueError as e:
            messagebox.showwarning(
                'Error', f'Error: {e}\nPor favor introduzca un dato válido para realizar la consulta.')
        except TypeError as e:
            messagebox.showwarning(
                'Error', f'Error: {e}\nEl dato ingresado no es válido')

    def realizar_reporte_pensionados(self,
                                     registros,
                                     parametros):
        """
        Realiza un reporte de los registros obtenidos en una consulta y lo guarda en un archivo de Excel.

        :param registros (list): una lista de tuplas que contiene los registros obtenidos de la consulta.
        :param parametros (list): una lista que contiene los parametros con los que se hizo la consulta.

        :return:
            - None

        :raises TypeError: Si no se ha realizado una consulta antes de generar un reporte.
        :raises ValueError: Si la consulta está vacía y no se puede generar un reporte.
        :raises exceptions.FileCreateError: Si el archivo de Excel no se puede crear.

        """
        self.registros = registros

        self.parametros = parametros
        print(self.parametros)

        # Obtener las columnas de la tabla
        columnas = ['ID', 'N°Tarjeta', 'Nombre', 'Apellido Materno',
                    'Apellido Paterno', 'Entrada', 'Salida', 'Tiempo', 'Estado']

        try:
            # Verificar que se haya realizado una consulta antes de generar un reporte
            if self.registros is None:
                raise ValueError(
                    'Primero genera una consulta antes de generar un reporte')
            # if len(self.registros) == 0: raise ValueError('La consulta esta vacia y no se puede generar un reporte')

            # Obtener la ruta y el nombre del archivo donde se guardará el reporte
            name_report = f'Reporte_Pensiones_{self.estacionamiento.replace(" ", "_")}'
            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension='.xlsx', initialfile=name_report)

            # Crear un archivo de Excel y escribir los registros
            workbook = xlsxwriter.Workbook(
                ruta_archivo, {'remove_timezone': True})
            worksheet = workbook.add_worksheet('Reporte')
            worksheet.set_landscape()
            # ajustar el tamaño de la hoja a A4 al tamaño A4
            worksheet.set_paper(1)

            # Agregar la imagen en la esquina superior izquierda de la hoja de Excel
            imagen_path = self.tools_instance.read_path_config_file(
                'images', 'logo_pase')

            formato_columnas_informacion = workbook.add_format(
                {'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': '#D9D9D9'})
            formato_columnas = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': '#D9D9D9'})
            formato_celdas_texto = workbook.add_format(
                {'bold': False, 'align': 'right', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})

            formato_titulo = workbook.add_format(
                {'bold': True, 'font_size': 14, 'align': 'center'})
            formato_subtitulo = workbook.add_format(
                {'bold': True, 'font_size': 12, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1})

            worksheet.insert_image(0, 0, imagen_path, {
                                   'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})

            # Agregar título en CE - E3
            titulo = "REPORTE PENSIONADOS"
            worksheet.merge_range('D3:G3', titulo, formato_titulo)

            subtitulo = "Datos del periodo"
            worksheet.merge_range('A8:D8', subtitulo, formato_subtitulo)

            subtitulo = "Datos quien realiza el reporte"
            worksheet.merge_range('F8:I8', subtitulo, formato_subtitulo)

            worksheet.write('F9', 'Estacionamiento',
                            formato_columnas_informacion)
            worksheet.write('F10', 'Nombre completo',
                            formato_columnas_informacion)

            quien = self.user_name
            lugar = self.estacionamiento

            worksheet.merge_range('G9:I9', lugar, formato_celdas_texto)
            worksheet.merge_range('G10:I10', quien, formato_celdas_texto)

            # Escribe los parámetros en la hoja de cálculo con los nuevos nombres
            for i, (clave, valor) in enumerate(self.parametros.items()):
                fila = i + 8
                # columna
                nuevo_nombre = self.nuevos_nombres.get(clave, valor)
                columna_A = 0
                columna_B = 1
                worksheet.merge_range(
                    fila, columna_A, fila, columna_B, nuevo_nombre, formato_columnas_informacion)

                columna = 2  # C

                worksheet.merge_range(
                    fila, columna, fila, columna+1, valor, formato_celdas_texto)

            FILA_INICIO_REGISTRO = worksheet.dim_rowmax + 4

            # Establecer el nombre y ancho de las columnas en función del contenido
            for i, columna in enumerate(columnas):
                worksheet.write(FILA_INICIO_REGISTRO - 1, i,
                                columnas[i], formato_columnas)

            # Escribir los registros
            for i, registro in enumerate(self.registros):
                for j, valor in enumerate(registro):
                    # Si el campo es "Entrada" o "Salida", convertir a fecha y hora
                    if columnas[j] == 'Entrada' or columnas[j] == 'Salida':
                        if valor == None:
                            fecha_hora_str = 'None'

                        else:
                            fecha_hora = datetime.strptime(valor.strftime(
                                '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                            fecha_hora_str = datetime.strftime(
                                fecha_hora, '%Y-%m-%d %H:%M:%S')
                        worksheet.write(i + FILA_INICIO_REGISTRO,
                                        j, fecha_hora_str, formato_celdas_texto)

                    elif columnas[j] == 'Tiempo':
                        if valor == None:
                            valor = 'None'

                        worksheet.write(i + FILA_INICIO_REGISTRO,
                                        j, valor, formato_celdas_texto)

                    else:
                        worksheet.write(i + FILA_INICIO_REGISTRO,
                                        j, valor, formato_celdas_texto)

                worksheet.set_column('A:A', 6)
                worksheet.set_column('B:B', 10)
                worksheet.set_column('C:C', 10)
                worksheet.set_column('D:D', 18)
                worksheet.set_column('E:E', 18)
                worksheet.set_column('F:F', 18)
                worksheet.set_column('G:G', 18)
                worksheet.set_column('H:H', 8)
                worksheet.set_column('I:I', 8)

                fila_final = worksheet.dim_rowmax + 1
                columna_final = 8

            # Establecer el área de impresión desde la columna A hasta la H y desde la fila 1 hasta la última fila de datos escritos
            worksheet.print_area(0, 0, fila_final, worksheet.dim_colmax)
            # worksheet.center_horizontally()

            # Cerrar el archivo de Excel
            workbook.close()
            os.chmod(ruta_archivo, 0o777)

            self.tools_instance.convert_excel_to_pdf(
                excel_file=ruta_archivo, pdf_file=f'{ruta_archivo[:-5]}.pdf')
            messagebox.showinfo('Mensaje', 'El reporte fue generado con exito')

        # Manejo de errores
        except TypeError as e:
            messagebox.showerror(
                'Error', f'Error: No se puede generar el reporte ya que el valor de la hora salida aun no esta definido.\n{e}')
        except ValueError as e:
            messagebox.showerror('Error', f'Error: {e}')
        except exceptions.FileCreateError as e:
            messagebox.showerror(
                'Error', f'Error: El reporte no se puede generar, seleccione el directorio para guardar el reporte y vuelva a intentar')
