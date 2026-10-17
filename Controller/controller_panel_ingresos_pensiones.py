from Tools.proyect_tools import Tools
from Models.queries import Queries

from tkinter import filedialog
from tkinter import messagebox
import xlsxwriter
from xlsxwriter import exceptions
import os
from datetime import date


class Controller_Panel_Ingresos_Pensiones:
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

    def hacer_consulta_ingresos_pensiones(self, year_param: int, month_param: int):
        """
        Realiza una consulta SQL con los valores proporcionados por el usuario y devuelve una lista de registros obtenidos.

        :param year_param (int): El año para el cual se desea obtener el mes.
        :param month_param (int): El mes que se desea obtener (1-12).

        :return (list): Una lista de registros obtenidos en la consulta.
        """

        try:
            parametros = {}

            # Obtener los valores de los campos de consulta
            self.year_param = year_param
            self.month_param = month_param

            date_str = date(year_param, month_param, 1)
            date_str.month

            month_options = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            month_str = month_options[date_str.month-1]

            # Validar y agregar los parámetros a la consulta
            if month_str != '':
                parametros['MES'] = month_str

            # Validar que se hayan proporcionado parámetros para la consulta
            if parametros == {}:
                raise ValueError('Los campos están vacíos')

            # Realizar la consulta y devolver la lista de registros obtenidos
            registros, registros_cortesia, campos, pensionados = self.query.hacer_consulta_sql_ingresos_pensiones(
                int(year_param), month_param)

            return registros, registros_cortesia, parametros, campos, pensionados

        except ValueError as e:
            messagebox.showwarning('Error', f'Error: {e}\n.')

        except Exception as e:
            print(e)

    def realizar_reporte_ingresos_pensiones(self, registros: list, registros_cortesia: list, parametros: dict, campos: list, pensionados: tuple) -> None:
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
        self.registros_cortesia = registros_cortesia
        self.parametros = parametros
        self.campos = campos
        self.pensionados_activos, self.pensionados_inactivos, self.campos_pension = pensionados

        try:
            # Verificar que se haya realizado una consulta antes de generar un reporte
            if self.registros is None:
                raise ValueError(
                    'Primero genera una consulta antes de generar un reporte')
            # if len(self.registros) == 0: raise ValueError('La consulta esta vacia y no se puede generar un reporte')

            # Obtener la ruta y el nombre del archivo donde se guardará el reporte
            name_report = f'Reporte_Ingresos_Pensiones_{self.estacionamiento.replace(" ", "_")}_{self.parametros["MES"]}'
            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension='.xlsx', initialfile=name_report)

            # Crear un archivo de Excel y escribir los registros
            workbook = xlsxwriter.Workbook(
                ruta_archivo, {'remove_timezone': True})
            worksheet = workbook.add_worksheet('Reporte')

            # Establecer la orientación de la hoja en horizontal
            worksheet.set_landscape()

            # ajustar el tamaño de la hoja a oficio
            worksheet.set_paper(12)

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
                {'num_format': '$#,##0.00', 'bold': True, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_hora = workbook.add_format(
                {'num_format': 'h:mm:ss', 'bold': True, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_titulo = workbook.add_format(
                {'bold': True, 'font_size': 14, 'align': 'center'})
            formato_subtitulo = workbook.add_format(
                {'bold': True, 'font_size': 12, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1})
            formato_celdas_texto_centrado = workbook.add_format(
                {'bold': False, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_fecha = workbook.add_format(
                {'num_format': 'yyyy-mm-dd hh:mm:ss', 'bold': True, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})

            worksheet.insert_image(0, 0, imagen_path, {
                                   'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})

            # Agregar título en CE - E3
            titulo = "REPORTE INGRESOS DE PENSIONES"
            worksheet.merge_range('A1:G1', titulo, formato_titulo)

            subtitulo = "Datos del periodo"
            worksheet.merge_range('A7:B7', subtitulo, formato_subtitulo)

            subtitulo = "Datos quien realiza el reporte"
            worksheet.merge_range('D7:G7', subtitulo, formato_subtitulo)

            worksheet.merge_range('D8:E8', 'Estacionamiento',
                                  formato_columnas_informacion)
            worksheet.merge_range('D9:E9', 'Nombre completo',
                                  formato_columnas_informacion)

            worksheet.merge_range(
                'F8:G8', self.estacionamiento, formato_celdas_texto)
            worksheet.merge_range('F9:G9', self.user_name,
                                  formato_celdas_texto)

            columna_A = 0
            columna_B = 1
            columna_C = 2
            columna_D = 3
            columna_E = 4
            columna_F = 5
            columna_G = 6

            # Escribe los parámetros en la hoja de cálculo con los nuevos nombres
            for i, (clave, valor) in enumerate(self.parametros.items()):
                fila = i + 7
                worksheet.write(fila, columna_A, clave,
                                formato_columnas_informacion)

                if valor == None:
                    valor = 'None'
                worksheet.write(fila, columna_B, valor,
                                formato_celdas_texto_centrado)

            fila_inicio = worksheet.dim_rowmax + 3

            # Obtener las columnas de la tabla
            columnas = self.campos

            # Escribir los registros
            for i, registro in enumerate(self.registros):
                for j, valor in enumerate(registro):
                    if 'Fecha' in columnas[j]:
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_fecha)

                    elif 'Monto' in columnas[j]:
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_moneda)
                    else:
                        worksheet.write(i + fila_inicio, j, valor,
                                        formato_celdas_texto_centrado)

                    worksheet.set_row(i + fila_inicio, 30)

            # Establecer un ancho máximo para las columnas
            max_length = 30

            for i, columna in enumerate(columnas):
                columna = str(columna).replace('_', ' ')

                if "Apellido" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 16)

                elif "Fecha" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 18.5)

                elif "Monto" in columna or "Numero" in columna or "Mensualidad" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 12)

                else:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, max_length)

            fila_final = worksheet.dim_rowmax + 2

            worksheet.merge_range(
                fila_final, columna_A, fila_final, columna_B, "TOTAL", formato_columnas)

            for col_num, col_name in enumerate(columnas):
                if 'Monto' in col_name:
                    total = sum(registro[col_num]
                                for registro in self.registros)

                    worksheet.write(fila_final, col_num, total,
                                    formato_celdas_moneda)

            fila_final = worksheet.dim_rowmax + 3

            if len(self.registros_cortesia) > 0:
                worksheet.merge_range(fila_final, columna_A, fila_final,
                                      columna_G, "PENSIONES CON CORTESIA", formato_columnas)
                fila_final += 1

                # Escribir los registros
                for i, registro in enumerate(self.registros_cortesia):
                    for j, valor in enumerate(registro):
                        if 'Fecha' in columnas[j]:
                            worksheet.write(i + fila_final, j,
                                            valor, formato_celdas_fecha)

                        elif 'Monto' in columnas[j]:
                            worksheet.write(i + fila_final, j,
                                            valor, formato_celdas_moneda)
                        else:
                            worksheet.write(
                                i + fila_final, j, valor, formato_celdas_texto_centrado)

                        worksheet.set_row(i + fila_final, 30)

            fila_final = worksheet.dim_rowmax + 1

            worksheet.print_area(0, 0, fila_final, worksheet.dim_colmax)

            ###############################################################################################
            worksheet_2 = workbook.add_worksheet('Pensionados Activos')

            worksheet_2.set_paper(12)
            worksheet_2.set_landscape()

            worksheet_2.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            titulo = F"REPORTE PENSIONADOS ACTIVOS -> {self.parametros['MES']}"
            worksheet_2.merge_range('A1:G1', titulo, formato_titulo)

            fila_inicio = worksheet_2.dim_rowmax + 7

            # Obtener las columnas de la tabla
            columnas = self.campos_pension

            # Escribir los registros
            for i, registro in enumerate(self.pensionados_activos):
                for j, valor in enumerate(registro):
                    worksheet_2.write(i + fila_inicio, j, valor,
                                      formato_celdas_texto_centrado)

                    worksheet_2.set_row(i + fila_inicio, 30)

            # Establecer un ancho máximo para las columnas
            max_length = 12

            for i, columna in enumerate(columnas):
                columna = str(columna).replace('_', ' ')

                if "Apellido" in columna:
                    worksheet_2.write(fila_inicio - 1, i,
                                      columna, formato_columnas)
                    worksheet_2.set_column(i, i, 16)

                elif "Nombre" in columna:
                    worksheet_2.write(fila_inicio - 1, i,
                                      columna, formato_columnas)
                    worksheet_2.set_column(i, i, 30)

                else:
                    worksheet_2.write(fila_inicio - 1, i,
                                      columna, formato_columnas)
                    worksheet_2.set_column(i, i, max_length)

            fila_final = worksheet_2.dim_rowmax + 2

            total = len(self.pensionados_activos)

            worksheet_2.merge_range(fila_final, columna_C, fila_final,
                                    columna_E, "TOTAL DE PENSIONADOS ACTIVOS", formato_columnas)
            worksheet_2.write(fila_final, columna_F, total,
                              formato_celdas_texto_centrado)

            worksheet_2.print_area(0, 0, fila_final, worksheet_2.dim_colmax)
            ###############################################################################################

            worksheet_3 = workbook.add_worksheet('Pensionados Inactivos')

            worksheet_3.set_paper(12)
            worksheet_3.set_landscape()

            worksheet_3.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})

            titulo = F"REPORTE PENSIONADOS INACTIVOS -> {self.parametros['MES']}"
            worksheet_3.merge_range('A1:G1', titulo, formato_titulo)

            fila_inicio = worksheet_3.dim_rowmax + 7

            # Obtener las columnas de la tabla
            columnas = self.campos_pension

            # Escribir los registros
            for i, registro in enumerate(self.pensionados_inactivos):
                for j, valor in enumerate(registro):
                    worksheet_3.write(i + fila_inicio, j, valor,
                                      formato_celdas_texto_centrado)

                    worksheet_3.set_row(i + fila_inicio, 30)

            # Establecer un ancho máximo para las columnas
            max_length = 12

            for i, columna in enumerate(columnas):
                columna = str(columna).replace('_', ' ')

                if "Apellido" in columna:
                    worksheet_3.write(fila_inicio - 1, i,
                                      columna, formato_columnas)
                    worksheet_3.set_column(i, i, 16)

                elif "Nombre" in columna:
                    worksheet_3.write(fila_inicio - 1, i,
                                      columna, formato_columnas)
                    worksheet_3.set_column(i, i, 30)

                else:
                    worksheet_3.write(fila_inicio - 1, i,
                                      columna, formato_columnas)
                    worksheet_3.set_column(i, i, max_length)

            fila_final = worksheet_3.dim_rowmax + 2

            total = len(self.pensionados_inactivos)

            worksheet_3.merge_range(fila_final, columna_C, fila_final,
                                    columna_E, "TOTAL DE PENSIONADOS INACTIVOS", formato_columnas)
            worksheet_3.write(fila_final, columna_F, total,
                              formato_celdas_texto_centrado)

            worksheet_3.print_area(0, 0, fila_final, worksheet_2.dim_colmax)
            ###############################################################################################

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
