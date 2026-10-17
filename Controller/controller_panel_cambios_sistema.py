

from Tools.proyect_tools import Tools
from Models.queries import Queries

from tkinter import filedialog
from tkinter import messagebox
import xlsxwriter
from xlsxwriter import exceptions
import os
from datetime import date, datetime


class Controller_Panel_Cambios_Sistema:
    """
    Controller del panel de cambios.

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
            'MES': 'Mes'
        }

    def hacer_consulta_cambios(self, year_param: int, month_param: int):
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
            registros, campos = self.query.hacer_consulta_sql_cambios(int(year_param), month_param)

            return registros, parametros, campos

        except ValueError as e:
            messagebox.showwarning('Error', f'Error: {e}\n.')

        except Exception as e:
            print(e)

    def realizar_reporte_cambios(self, registros: list, parametros: dict, campos: list) -> None:
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
            name_report = f'Reporte_Cambios_Sistema_{self.estacionamiento.replace(" ", "_")}'
            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension='.xlsx', initialfile=name_report)

            # Crear un archivo de Excel y escribir los registros
            workbook = xlsxwriter.Workbook(
                ruta_archivo, {'remove_timezone': True})
            worksheet = workbook.add_worksheet('Reporte')
            worksheet.set_landscape()

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

            # Agregar título en CE - E3
            titulo = "REPORTE DE CAMBIOS DEL SISTEMA"
            worksheet.merge_range('A1:G1', titulo, formato_titulo)

            subtitulo = "Datos del periodo"
            worksheet.merge_range('A7:B7', subtitulo, formato_subtitulo)

            subtitulo = "Datos quien realiza el reporte"
            worksheet.merge_range('C7:F7', subtitulo, formato_subtitulo)

            worksheet.merge_range('C8:D8', 'Estacionamiento',
                                  formato_columnas_informacion)
            worksheet.merge_range('C9:D9', 'Nombre completo',
                                  formato_columnas_informacion)

            worksheet.merge_range('E8:F8', self.estacionamiento, formato_celdas_texto)
            worksheet.merge_range('E9:F9', self.user_name,formato_celdas_texto)

            columna_A = 0
            columna_B = 1
            columna_C = 2
            columna_D = 3
            columna_E = 4
            columna_F = 5
            columna_G = 6

            # Escribe los parámetros en la hoja de cálculo con los nuevos nombres
            for i, (clave, valor) in enumerate(self.parametros.items()):
                nuevo_nombre = self.nuevos_nombres.get(clave, "N/A")
                fila = i + 7
                worksheet.write(fila, columna_A, nuevo_nombre,formato_columnas_informacion)

                if valor == None:
                    valor = 'None'
                worksheet.write(fila, columna_B, valor,formato_celdas_texto_centrado)

            FILA_INICIO_REGISTRO = worksheet.dim_rowmax + 3

            # Obtener las columnas de la tabla
            columnas = self.campos

            # Escribir los registros
            for i, registro in enumerate(self.registros):
                for j, valor in enumerate(registro):
                    # Si el campo es "Entrada" o "Salida", convertir a fecha y hora
                    if columnas[j] == 'Fecha del cambio':
                        if valor == None:
                            fecha_hora_str = 'None'
                        else:
                            fecha_hora = datetime.strptime(valor.strftime(
                                '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                            fecha_hora_str = datetime.strftime(
                                fecha_hora, '%Y-%m-%d %H:%M:%S')
                        worksheet.write(
                            i + FILA_INICIO_REGISTRO, j, fecha_hora_str, formato_celdas_texto_centrado)

                    else:
                        worksheet.write(i + FILA_INICIO_REGISTRO,
                                        j, valor, formato_celdas_texto_centrado)

                    worksheet.set_row(i + FILA_INICIO_REGISTRO, 30)

            # Establecer un ancho máximo para las columnas
            max_length = 11

            for i, columna in enumerate(columnas):
                columna = str(columna).replace('_', '\n')

                if "Nombre" in columna:
                    worksheet.write(FILA_INICIO_REGISTRO - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 32)

                elif "Usuario" in columna:
                    worksheet.write(FILA_INICIO_REGISTRO - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 17)

                elif "Valor" in columna:
                    worksheet.write(FILA_INICIO_REGISTRO - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 18)

                elif "Fecha" in columna:
                    worksheet.write(FILA_INICIO_REGISTRO - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 11)

                elif "Tipo" in columna:
                    worksheet.write(FILA_INICIO_REGISTRO - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 20)



            fila_final = worksheet.dim_rowmax + 1

            # Establecer el área de impresión desde la columna A hasta la H y desde la fila 1 hasta la última fila de datos escritos
            worksheet.print_area(0, 0, fila_final, worksheet.dim_colmax)



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

