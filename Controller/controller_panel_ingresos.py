from Views.view_calendar import Calendar_date
from Tools.proyect_tools import Tools

from tkinter import filedialog
from tkinter import messagebox

import xlsxwriter
from xlsxwriter import exceptions

import os


class Controller_Panel_Ingresos:
    """
    Controller del panel de ingresos.

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
            'fecha_inicio_entrada': 'Fecha de inicio',
            'fecha_fin_entrada': 'Fecha de final',
            'corte_numero': 'N° Corte',
            'corte_numero_inicio': 'N° Corte inicio',
            'corte_numero_fin': 'N° Corte final'
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
        :param variable (StringVar): variable que se utiliza para almacenar la fecha seleccionada.
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

    def hacer_consulta_ingresos(self,
                                fecha_inicio_entrada: str,
                                fecha_fin_entrada: str,
                                corte_numero: int,
                                corte_numero_inicio: int,
                                corte_numero_fin: int) -> list:
        """
        Realiza una consulta SQL con los valores proporcionados por el usuario y devuelve una lista de registros obtenidos.

        :param fecha_inicio_entrada (str): fecha de inicio de entrada en formato yyyy-mm-dd hh:mm:ss para consultar.
        :param fecha_fin_entrada (str): fecha de fin de entrada en formato yyyy-mm-dd hh:mm:ss para consultar.
        :param corte_numero (int): número de corte a consultar.
        :param corte_numero_inicio (int): número de corte a consultar, con un rango de inicio.
        :param corte_numero_fin (int): número de corte a consultar, con un rango final.

        :return:
            - registros (tuple): una lista de tuplas que contiene los registros obtenidos de la consulta.
            - parametros (tuple): una lista de que contiene los parametros con los que se hizo la consulta.

        :raises ValueError: si los campos para la consulta están vacíos.
        :raises TypeError: si el dato ingresado no es válido.
        """

        try:
            parametros = {}

            # Obtener los valores de los campos de consulta
            self.fecha_inicio_entrada = fecha_inicio_entrada
            self.fecha_fin_entrada = fecha_fin_entrada

            self.corte_numero = corte_numero
            self.corte_numero_inicio = corte_numero_inicio
            self.corte_numero_fin = corte_numero_fin

            # Validar y agregar los parámetros a la consulta
            ##########################################################################################################
            if fecha_inicio_entrada != '':
                if len(fecha_inicio_entrada) != 19:
                    raise ValueError(
                        'Error, La cantidad de caracteres no corresponde al formato de fecha')
                parametros['fecha_inicio_entrada'] = str(fecha_inicio_entrada)

            if fecha_fin_entrada != '':
                if len(fecha_fin_entrada) != 19:
                    raise ValueError(
                        'Error, La cantidad de caracteres no corresponde al formato de fecha')
                parametros['fecha_fin_entrada'] = str(fecha_fin_entrada)

            if 'fecha_inicio_entrada' in parametros and 'fecha_fin_entrada' in parametros:
                if parametros['fecha_inicio_entrada'] > parametros['fecha_fin_entrada']:
                    raise ValueError(
                        "La fecha de inicio debe ser menor o igual que la fecha final.")
            ##########################################################################################################
            if corte_numero != '':
                parametros['corte_numero'] = int(corte_numero)
            if corte_numero_inicio != '':
                parametros['corte_numero_inicio'] = int(corte_numero_inicio)
            if corte_numero_fin != '':
                parametros['corte_numero_fin'] = int(corte_numero_fin)

            if 'corte_numero_inicio' in parametros and 'corte_numero_fin' in parametros:
                if parametros['corte_numero_inicio'] > parametros['corte_numero_fin']:
                    raise ValueError(
                        "El corte de inicio debe ser menor o igual que el corte final.")
            ##########################################################################################################
            # Validar que se hayan proporcionado parámetros para la consulta
            if parametros == {}:
                raise ValueError('Los campos están vacíos')

            # Realizar la consulta y devolver la lista de registros obtenidos
            registros = self.query.hacer_consulta_sql_ingresos(parametros)

            print(f'Parametros: {parametros}')
            return registros, parametros

        except ValueError as e:
            messagebox.showwarning(
                'Error', f'Error: {e}\nPor favor introduzca un dato válido para realizar la consulta.')
        except Exception as e:
            messagebox.showwarning(
                'Error', f'Mostrar el siguiente error a un administrador\nError: {e}')

    def realizar_reporte_ingresos(self,
                                  registros,
                                  parametros):
        """
        Realiza un reporte de los registros obtenidos en una consulta y lo guarda en un archivo de Excel.

        :param registros (list): una lista de tuplas que contiene los registros obtenidos de la consulta.
        :param parametros (list): una lista de que contiene los parametros con los que se hizo la consulta.

        :return:
            - None

        :raises TypeError: Si no se ha realizado una consulta antes de generar un reporte.
        :raises ValueError: Si la consulta está vacía y no se puede generar un reporte.
        :raises exceptions.FileCreateError: Si el archivo de Excel no se puede crear.
        """
        self.registros = registros
        self.parametros = parametros

        try:
            # Verificar que se haya realizado una consulta antes de generar un reporte
            if self.registros is None:
                raise ValueError(
                    'Primero genera una consulta antes de generar un reporte')
            # if len(self.registros) == 0: raise ValueError('La consulta esta vacia y no se puede generar un reporte')

            # Obtener la ruta y el nombre del archivo donde se guardará el reporte
            name_report = f'Reporte_Ingresos_{self.estacionamiento.replace(" ", "_")}'
            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension='.xlsx', initialfile=name_report)

            # Crear un archivo de Excel y escribir los registros
            workbook = xlsxwriter.Workbook(
                ruta_archivo, {'remove_timezone': True})
            worksheet = workbook.add_worksheet('Reporte')
            worksheet_grafico1 = workbook.add_worksheet('Grafico1')
            worksheet_grafico2 = workbook.add_worksheet('Grafico2')

            # Establecer la orientación de la hoja en horizontal
            worksheet.set_landscape()
            worksheet_grafico1.set_landscape()
            worksheet_grafico2.set_landscape()

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
            formato_celdas_moneda = workbook.add_format(
                {'num_format': '$#,##0.00', 'bold': True, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_titulo = workbook.add_format(
                {'bold': True, 'font_size': 14, 'align': 'center'})
            formato_subtitulo = workbook.add_format(
                {'bold': True, 'font_size': 12, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1})
            formato_celdas_texto_centrado = workbook.add_format(
                {'bold': False, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})

            worksheet.insert_image(0, 0, imagen_path, {
                                   'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            worksheet_grafico1.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            worksheet_grafico2.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            # Agregar título en CE - E3
            titulo = "REPORTE INGRESOS"
            worksheet.merge_range('A3:G3', titulo, formato_titulo)

            subtitulo = "Datos del periodo"
            worksheet.merge_range('A8:D8', subtitulo, formato_subtitulo)

            subtitulo = "Datos quien realiza el reporte"
            worksheet.merge_range('E8:G8', subtitulo, formato_subtitulo)

            worksheet.write('E9', 'Lugar', formato_columnas_informacion)
            worksheet.write('E10', 'Nombre', formato_columnas_informacion)

            quien = self.user_name
            lugar = self.estacionamiento

            worksheet.merge_range('F9:G9', lugar, formato_celdas_texto)
            worksheet.merge_range('F10:G10', quien, formato_celdas_texto)

            columna_A = 0
            columna_B = 1
            columna_C = 2
            columna_D = 3
            columna_E = 4
            columna_F = 5
            columna_G = 6

            # Escribe los parámetros en la hoja de cálculo con los nuevos nombres
            for i, (clave, valor) in enumerate(self.parametros.items()):
                fila = i + 8
                # columna
                nuevo_nombre = self.nuevos_nombres.get(clave, valor)
                columna_A = 0
                columna_B = 1
                worksheet.merge_range(
                    fila, columna_A, fila, columna_B, nuevo_nombre, formato_columnas_informacion)

                if valor == None:
                    valor = 'None'
                # worksheet.write(fila, columna_D, valor ,formato_celdas_texto_centrado)
                worksheet.merge_range(
                    fila, columna_C, fila, columna_D, valor, formato_celdas_texto_centrado)

            fila_inicio = worksheet.dim_rowmax + 2

            worksheet.merge_range(
                fila_inicio, columna_B, fila_inicio, columna_C, 'EFECTIVO', formato_subtitulo)
            worksheet.merge_range(
                fila_inicio, columna_D, fila_inicio, columna_G, 'TOTALES', formato_subtitulo)

            fila_inicio = worksheet.dim_rowmax + 2

            # Obtener las columnas de la tabla
            columnas = ['Concepto', 'N° Boletos', 'Importe',
                        'Total Boletos', 'Subtotal', 'Impuesto', 'Total']

            # Establecer el nombre y ancho de las columnas en función del contenido
            for i, columna in enumerate(columnas):
                worksheet.write(fila_inicio - 1, i, columna, formato_columnas)

            suma_boletos = 0
            suma_importe = 0

            suma_subtotal = 0
            suma_impuesto = 0

            valor_importe = 0
            # Escribir los registros
            for i, registro in enumerate(self.registros):
                valor = None
                for j, valor in enumerate(registro):
                    if columnas[j] == 'Concepto':
                        if valor == None:
                            valor = 'None'
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_texto)

                    if columnas[j] == 'N° Boletos':
                        if valor == None:
                            valor = 0
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_texto)
                        worksheet.write(i + fila_inicio, columna_D,
                                        valor, formato_celdas_texto)
                        suma_boletos = suma_boletos + valor

                    if columnas[j] == 'Importe':
                        if valor == None:
                            valor = 0
                        valor_importe = valor
                        worksheet.write(i + fila_inicio, j,
                                        valor_importe, formato_celdas_moneda)
                        worksheet.write(i + fila_inicio, columna_G,
                                        valor_importe, formato_celdas_moneda)
                        suma_importe = suma_importe + valor

                subtotal = 0
                subtotal = valor_importe/1.16
                worksheet.write(i + fila_inicio, columna_E,
                                subtotal, formato_celdas_moneda)
                suma_subtotal = suma_subtotal + subtotal

                impuesto = 0
                impuesto = subtotal*0.16
                worksheet.write(i + fila_inicio, columna_F,
                                impuesto, formato_celdas_moneda)
                suma_impuesto = suma_impuesto + impuesto

            fila_final = worksheet.dim_rowmax + 2

            worksheet.write(fila_final, columna_A, "TOTAL", formato_columnas)
            worksheet.write(fila_final, columna_B,
                            suma_boletos, formato_celdas_texto)
            worksheet.write(fila_final, columna_C,
                            suma_importe, formato_celdas_moneda)
            worksheet.write(fila_final, columna_D,
                            suma_boletos, formato_celdas_texto)
            worksheet.write(fila_final, columna_E,
                            suma_subtotal, formato_celdas_moneda)
            worksheet.write(fila_final, columna_F,
                            suma_impuesto, formato_celdas_moneda)
            worksheet.write(fila_final, columna_G,
                            suma_importe, formato_celdas_moneda)

            worksheet.set_column('A:A', 10)
            worksheet.set_column('B:B', 10)
            worksheet.set_column('C:C', 14)
            worksheet.set_column('D:D', 13)
            worksheet.set_column('E:E', 14)
            worksheet.set_column('F:F', 14)
            worksheet.set_column('G:G', 14)

            fila_final = worksheet.dim_rowmax + 1
            columna_final = worksheet.dim_colmax

            chart_scale = 1.5

            # Agregar los datos para el gráfico circular
            chart_tickets = workbook.add_chart({
                'type': 'column'
            })

            row_start = fila_inicio + 1

            chart_tickets.add_series({
                'name': 'Boletos',
                'categories': f'=Reporte!$A${row_start}:$A${row_start-1 +len(self.registros)}',
                'values':     f'=Reporte!$B${row_start}:$B${row_start-1 +len(self.registros)}',
                'data_labels': {
                    'percentage': True,
                    'value': True
                },
            })

            chart_tickets.set_style(10)
            # Establece un estilo para el gráfico
            chart_tickets.set_title({
                'name': 'Gráfico de Boletos'
            })

            chart_tickets.set_size({
                'x_scale': chart_scale,
                'y_scale': chart_scale
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico1.insert_chart(7, 0, chart_tickets)

            # Agregar los datos para el gráfico circular
            chart_money = workbook.add_chart({
                'type': 'column'
            })

            chart_money.add_series({
                'name': 'Ingresos',
                'categories': f'=Reporte!$A${row_start}:$A${row_start-1 +len(self.registros)}',
                'values':     f'=Reporte!$C${row_start}:$C${row_start-1 +len(self.registros)}',
                'data_labels': {
                    'percentage': True,
                    'value': True
                },
            })

            chart_money.set_style(10)
            # Establece un estilo para el gráfico
            chart_money.set_title({
                'name': 'Gráfico de Ingresos'
            })

            chart_money.set_size({
                'x_scale': chart_scale,
                'y_scale': chart_scale
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico2.insert_chart(7, 0, chart_money)

            # Establecer el área de impresión desde la columna A hasta la H y desde la fila 1 hasta la última fila de datos escritos
            worksheet.print_area(0, 0, fila_final, columna_final)
            # worksheet.center_horizontally()

            # Cerrar el archivo de Excel
            workbook.close()
            os.chmod(ruta_archivo, 0o777)

            self.tools_instance.convert_excel_to_pdf(ruta_archivo)
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
