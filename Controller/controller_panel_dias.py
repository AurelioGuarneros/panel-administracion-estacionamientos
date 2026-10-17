from Tools.proyect_tools import Tools
from Models.queries import Queries

from tkinter import filedialog
from tkinter import messagebox
import xlsxwriter
from xlsxwriter import exceptions
import os
from datetime import date


class Controller_Panel_Dias:
    """
    Controller del panel de dias.

    :param estacionamiento (str): Nombre del estacionamiento.
    :param user_name (str): Nombre de usuario.
    :param query (Queries): Objeto de tipo Queries que tiene la conexion a la base de datos.
    :raises None:

    :return:
        - None
    """

    def __init__(self,
                 estacionamiento: str = None, user_name: str = None, query: Queries = None):
        """
        Constructor de la clase. Crea la ventana principal, la tabla y los campos de consulta.

        :param estacionamiento (str): Nombre del estacionamiento.
        :param user_name (str): Nombre de usuario.
        :param query (Queries): Objeto de tipo Queries que tiene la conexion a la base de datos.
        """
        self.user_name = user_name
        self.estacionamiento = estacionamiento
        self.query = query
        self.tools_instance = Tools()

        # Define un diccionario con los nuevos nombres de clave
        self.nuevos_nombres = {
            'corte_numero': 'N° Corte',
            'corte_numero_inicio': 'N° Corte inicio',
            'corte_numero_fin': 'N° Corte final'
        }

    def hacer_consulta_dias(self, corte_numero: int,
                                  corte_numero_inicio: int,
                                  corte_numero_fin: int):
                               #year_param: int, month_param: int) -> tuple[list, dict, list]:
        """
        Realiza una consulta SQL con los valores proporcionados por el usuario y devuelve una lista de registros obtenidos.

        :param year_param (int): El año para el cual se desea obtener el mes.
        :param month_param (int): El mes que se desea obtener (1-12).

        :return (list): Una lista de registros obtenidos en la consulta.
        """

        try:
            parametros = {}
            self.corte_numero = corte_numero
            self.corte_numero_inicio = corte_numero_inicio
            self.corte_numero_fin = corte_numero_fin

            # # Obtener los valores de los campos de consulta
            # self.year_param = year_param
            # self.month_param = month_param

            # date_str = date(year_param, month_param, 1)
            # date_str.month

            # month_options = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            #                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            # month_str = month_options[date_str.month-1]

            # # Validar y agregar los parámetros a la consulta
            # if month_str != '':
            #     parametros['MES'] = month_str



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
            registros, campos = self.query.hacer_consulta_sql_dias(parametros)
                #int(year_param), month_param)

            return registros, parametros, campos

        except ValueError as e:
            messagebox.showwarning('Error', f'Error: {e}\n.')

        except Exception as e:
            print(e)

    def realizar_reporte_dias(self, registros: list, parametros: dict, campos: list) -> None:
        """
        Realiza un reporte de los registros obtenidos en una consulta y lo guarda en un archivo de Excel.

        :param registros (list): una lista de tuplas que contiene los registros obtenidos de la consulta.
        :param parametros (dict): un diccinario que contiene los parametros con los que se hizo la consulta.
        :param campos (list): una lista de tuplas que contiene las columnas de la consulta.

        :return:
            - None

        :raises TypeError: Si no se ha realizado una consulta antes de generar un reporte.
        :raises ValueError: Si la consulta está vacía y no se puede generar un reporte.
        :raises exceptions.FileCreateError: Si el archivo de Excel no se puede crear.
        """
        self.registros = registros
        self.parametros = parametros
        self.campos = campos

        try:
            # Verificar que se haya realizado una consulta antes de generar un reporte
            if self.registros is None:
                raise ValueError(
                    'Primero genera una consulta antes de generar un reporte')
            # if len(self.registros) == 0: raise ValueError('La consulta esta vacia y no se puede generar un reporte')

            # Obtener la ruta y el nombre del archivo donde se guardará el reporte
            name_report = f'Reporte_Diario_{self.estacionamiento.replace(" ", "_")}'
            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension='.xlsx', initialfile=name_report)

            # Crear un archivo de Excel y escribir los registros
            workbook = xlsxwriter.Workbook(
                ruta_archivo, {'remove_timezone': True})
            worksheet = workbook.add_worksheet('Reporte')
            worksheet_grafico1 = workbook.add_worksheet('Grafico1')
            worksheet_grafico2 = workbook.add_worksheet('Grafico2')
            worksheet_grafico3 = workbook.add_worksheet('Grafico3')

            # Establecer la orientación de la hoja en horizontal
            worksheet_grafico1.set_landscape()
            worksheet_grafico2.set_landscape()
            worksheet_grafico3.set_landscape()

            # ajustar el tamaño de la hoja a oficio
            worksheet.set_paper(12)

            num_tipo_pago = len(campos) - 5
            if num_tipo_pago >= 6:
                worksheet.set_landscape()

            worksheet_grafico1.set_paper(5)
            worksheet_grafico2.set_paper(5)
            worksheet_grafico3.set_paper(5)

            # Agregar la imagen en la esquina superior izquierda de la hoja de Excel
            imagen_path = self.tools_instance.read_path_config_file(
                'images', 'logo_pase')

            formato_columnas_informacion = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': '#D9D9D9'})
            formato_columnas = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                                   'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': '#D9D9D9', 'text_wrap': True})
            formato_celdas_texto = workbook.add_format(
                {'bold': True, 'align': 'right', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_numero = workbook.add_format(
                {'num_format': '0', 'bold': True, 'align': 'right', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_moneda = workbook.add_format(
                {'num_format': '$#,##0', 'bold': True, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_hora = workbook.add_format(
                {'num_format': 'h:mm:ss', 'bold': True, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_titulo = workbook.add_format(
                {'bold': True, 'font_size': 14, 'align': 'center'})
            formato_subtitulo = workbook.add_format(
                {'bold': True, 'font_size': 12, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1})
            formato_celdas_texto_centrado = workbook.add_format(
                {'bold': False, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_fecha = workbook.add_format(
                {'num_format': 'yyyy-mm-dd', 'bold': True, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})

            worksheet.insert_image(0, 0, imagen_path, {
                                   'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            worksheet_grafico1.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            worksheet_grafico2.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            worksheet_grafico3.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})

            # Agregar título en CE - E3
            titulo = "REPORTE DIARIO"
            worksheet.merge_range('A1:L1', titulo, formato_titulo)

            letter_campo_titulo = self.tools_instance.get_letter_from_column_number(len(self.campos)-1)

            subtitulo = "Datos del periodo"
            worksheet.merge_range('A7:C7', subtitulo, formato_subtitulo)

            subtitulo = "Datos de quien realiza el reporte"
            worksheet.merge_range(F'D7:{letter_campo_titulo}7', subtitulo, formato_subtitulo)

            worksheet.merge_range('D8:E8', 'Estacionamiento',formato_columnas_informacion)
            worksheet.merge_range('D9:E9', 'Nombre completo',formato_columnas_informacion)

            worksheet.merge_range(f'F8:{letter_campo_titulo}8', self.estacionamiento, formato_celdas_texto)
            worksheet.merge_range(f'F9:{letter_campo_titulo}9', self.user_name,formato_celdas_texto)

            columna_A = 0
            columna_B = 1
            columna_C = 2
            columna_D = 3
            columna_E = 4
            columna_F = 5
            columna_G = 6

            # Escribe los parámetros en la hoja de cálculo con los nuevos nombres
            for i, (clave, valor) in enumerate(self.parametros.items()):
                nuevo_nombre = self.nuevos_nombres.get(clave, valor)
                fila = i + 7
                worksheet.merge_range(
                    fila, columna_A, fila, columna_B, nuevo_nombre, formato_columnas_informacion)

                if valor == None:
                    valor = 'None'
                worksheet.write(fila, columna_C, valor,
                                formato_celdas_texto_centrado)

            fila_inicio = worksheet.dim_rowmax + 3

            # Obtener las columnas de la tabla
            columnas = self.campos

            # Escribir los registros
            for i, registro in enumerate(self.registros):
                for j, valor in enumerate(registro):
                    if columnas[j] == 'FECHA':
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_fecha)

                    elif 'IMPORTE' in columnas[j]:
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_moneda)
                    else:
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_texto)

            # Establecer un ancho máximo para las columnas
            max_length = 9.5

            for i, columna in enumerate(columnas):
                columna = str(columna).replace('_', '\n')

                if "DIA" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 3)

                elif "FECHA" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 10)

                elif "ADMIN" in columna or "Normal" in columna or "SHAKE" in columna or "Sonora\nGrill" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 6.5)

                elif "Perdido" in columna or "Normal" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 7)

                else:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, max_length)

            fila_final = worksheet.dim_rowmax + 2

            worksheet.merge_range(
                fila_final, columna_A, fila_final, columna_B, "TOTALES", formato_columnas)

            for col_num, col_name in enumerate(columnas):
                if 'DIA' in col_name or 'FECHA' in col_name:
                    continue

                format = formato_celdas_moneda if 'IMPORTE' in col_name else formato_celdas_texto

                total = sum(registro[col_num] for registro in self.registros)

                worksheet.write(fila_final, col_num, total, format)

            fila_final = worksheet.dim_rowmax + 1

            # Establecer el área de impresión desde la columna A hasta la H y desde la fila 1 hasta la última fila de datos escritos
            worksheet.print_area(0, 0, fila_final, worksheet.dim_colmax)

            #########################################################################################################
            # Agregar los datos para el gráfico circular
            chart_tickets = workbook.add_chart({
                'type': 'column'
            })

            column_letter = self.tools_instance.get_letter_from_column_number(
                len(self.campos)-3)
            categories = f'=Reporte!$D${fila_inicio}:${column_letter}${fila_inicio}'
            values = f'=Reporte!$D{worksheet.dim_rowmax+1}:${column_letter}${worksheet.dim_rowmax+1}'

            chart_tickets.add_series({
                'name': f'Total de boletos',
                'categories': categories,
                'values': values,
                'data_labels': {
                    'percentage': True,
                    'value': True
                },
            })

            chart_scale_x = 2.25
            chart_scale_y = 1.8

            chart_tickets.set_style(10)
            # Establece un estilo para el gráfico
            chart_tickets.set_title({
                'name': 'Gráfico de Boletos totales por tarifa'
            })

            chart_tickets.set_size({
                'x_scale': chart_scale_x,
                'y_scale': chart_scale_y
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico1.insert_chart(7, 0, chart_tickets)

            #########################################################################################################
            # Agregar los datos para el gráfico circular
            chart_total_tickets = workbook.add_chart({
                'type': 'column'
            })

            row_start = fila_inicio

            fila_final = worksheet.dim_rowmax + 1

            column_letter = self.tools_instance.get_letter_from_column_number(
                worksheet.dim_colmax)

            categories_money = f'=Reporte!$B${row_start+1}:$B${row_start + len(self.registros)}'
            values_money = f'=Reporte!$C${row_start+1}:$C${row_start + len(self.registros)}'

            chart_total_tickets.add_series({
                'name': f'Total de boletos',
                'categories': categories_money,
                'values': values_money,
                'data_labels': {
                    'percentage': True,
                    'value': True
                },
            })

            chart_scale_x = 2.25
            chart_scale_y = 1.8

            chart_total_tickets.set_style(10)
            # Establece un estilo para el gráfico
            chart_total_tickets.set_title({
                'name': 'Gráfico de boletos totales por día'
            })

            chart_total_tickets.set_size({
                'x_scale': chart_scale_x,
                'y_scale': chart_scale_y
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico2.insert_chart(7, 0, chart_total_tickets)

            #########################################################################################################
            # Agregar los datos para el gráfico circular
            chart_total_money = workbook.add_chart({
                'type': 'column'
            })

            row_start = fila_inicio

            fila_final = worksheet.dim_rowmax + 1

            column_letter = self.tools_instance.get_letter_from_column_number(
                len(self.campos)-1)

            categories_money = f'=Reporte!$B${row_start+1}:$B${row_start+len(self.registros)}'
            values_money = f'=Reporte!${column_letter}${row_start+1}:${column_letter}${row_start+len(self.registros)}'

            chart_total_money.add_series({
                'name': f'Total de ingresos',
                'categories': categories_money,
                'values': values_money,
                'data_labels': {
                    'percentage': True,
                    'value': True
                },
            })

            chart_scale_x = 2.25
            chart_scale_y = 1.8

            chart_total_money.set_style(10)
            # Establece un estilo para el gráfico
            chart_total_money.set_title({
                'name': 'Gráfico de ingresos totales por día'
            })

            chart_total_money.set_size({
                'x_scale': chart_scale_x,
                'y_scale': chart_scale_y
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico3.insert_chart(7, 0, chart_total_money)

            # Cerrar el archivo de Excel
            workbook.close()
            os.chmod(ruta_archivo, 0o777)

            self.tools_instance.convert_excel_to_pdf(ruta_archivo)

            messagebox.showinfo('Mensaje', 'El reporte fue generado con exito')

        # Manejo de errores
        except TypeError as e:
            messagebox.showerror(
                'Error', f'Error: No se puede generar el reporte, intente nuevamente.\n{e}')
        except ValueError as e:
            messagebox.showerror('Error', f'Error: {e}')
        except exceptions.FileCreateError as e:
            messagebox.showerror(
                'Error', f'Error: El reporte no se puede generar, verifique si no esta abierto otro archivo con el mismo nombre o seleccione correctamente la dirección donde se guardará el archivo')
        except Exception as e:
            print(e)
