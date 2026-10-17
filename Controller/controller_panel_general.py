from Views.view_calendar import Calendar_date
from Tools.proyect_tools import Tools

from tkinter import filedialog
from tkinter import messagebox

import xlsxwriter
from xlsxwriter import exceptions

from datetime import datetime
from datetime import timedelta
from Models.queries import Queries

import os


class Controller_Panel_General:
    """
    Controller del panel general.

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
        Constructor de la clase.
        Crea la ventana principal, la tabla y los campos de consulta.

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
            'id': 'N° boleto',
            'tarifa_preferente': 'Promociones',
            'fecha_inicio_entrada': 'Fecha de entrada inicio',
            'fecha_fin_entrada': 'Fecha de entrada final',
            'fecha_inicio_salida': 'Fecha de salida inicio',
            'fecha_fin_salida': 'Fecha de salida final',
            'corte_numero': 'N° Corte',
            'corte_numero_inicio': 'N° Corte inicio',
            'corte_numero_fin': 'N° Corte final',
            'ingreso': 'Importe',
            'ingreso_mayor': 'Importe final',
            'ingreso_menor': 'Importe inicio',
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

    def hacer_consulta_entrada(self,
                               id: int,
                               tarifa_preferente: str,
                               fecha_inicio_entrada: str,
                               fecha_fin_entrada: str,
                               corte_numero: int,
                               corte_numero_inicio: int,
                               corte_numero_fin: int,
                               ingreso: str,
                               ingreso_mayor: str,
                               ingreso_menor: str) -> list:
        """
        :param id (int): ID del registro a consultar.
        :param tarifa_preferente (str): valor de la tarifa preferente para consultar.
        :param fecha_inicio_entrada (str): fecha de inicio de entrada en formato yyyy-mm-dd hh:mm:ss para consultar.
        :param fecha_fin_entrada (str): fecha de fin de entrada en formato yyyy-mm-dd hh:mm:ss para consultar.
        :param corte_numero (int): número de corte a consultar.
        :param corte_numero_inicio (int): número de corte a consultar, con un rango de inicio.
        :param corte_numero_fin (int): número de corte a consultar, con un rango final.
        :param ingreso (str): valor de ingreso para consultar.
        :param ingreso_mayor (str): valor de ingreso mayor para consultar.
        :param ingreso_menor (str): valor de ingreso menor para consultar.

        :return:
            - una lista de tuplas que contiene los registros obtenidos de la consulta.
            - una lista de que contiene los parametros con los que se hizo la consulta.
            - una lista de tuplas que contiene las columnas de la consulta.
        :rtype: Tuple[List[Tuple], List, List[Tuple]]
        :raises: ValueError si los campos para la consulta están vacíos o TypeError si el dato ingresado no es válido.
        """

        try:
            parametros = {}

            # Obtener los valores de los campos de consulta
            self.id = id
            self.tarifa_preferente = tarifa_preferente

            self.fecha_inicio_entrada = fecha_inicio_entrada
            self.fecha_fin_entrada = fecha_fin_entrada

            self.corte_numero = corte_numero
            self.corte_numero_inicio = corte_numero_inicio
            self.corte_numero_fin = corte_numero_fin

            self.ingreso = ingreso
            self.ingreso_mayor = ingreso_mayor
            self.ingreso_menor = ingreso_menor

            # Validar y agregar los parámetros a la consulta
            ##########################################################################################################
            if id != '':
                parametros['id'] = int(id)
            ##########################################################################################################
            if tarifa_preferente != []:
                parametros['tarifa_preferente'] = tuple(tarifa_preferente)
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
            if ingreso != '':
                parametros['ingreso'] = round(float(ingreso), 1)
            if ingreso_mayor != '':
                parametros['ingreso_mayor'] = round(float(ingreso_mayor), 1)
            if ingreso_menor != '':
                parametros['ingreso_menor'] = round(float(ingreso_menor), 1)

            if 'ingreso_mayor' in parametros and 'ingreso_menor' in parametros:
                if parametros['ingreso_menor'] > parametros['ingreso_mayor']:
                    raise ValueError(
                        "El ingreso menor debe de ser menor al ingreso mayor.")
            ##########################################################################################################
            # Validar que se hayan proporcionado parámetros para la consulta
            if parametros == {}:
                raise ValueError('Los campos están vacíos')

            # Realizar la consulta y devolver la lista de registros obtenidos
            registros, promociones = self.query.hacer_consulta_sql_entradas(
                parametros)
            return registros, parametros, promociones

        except ValueError as e:
            messagebox.showwarning(
                'Error', f'Error: {e}\nPor favor introduzca un dato válido para realizar la consulta.')
        except TypeError as e:
            messagebox.showwarning(
                'Error', f'Error: {e}\nEl dato ingresado no es válido')

    def realizar_reporte_general(self,
                                 registros,
                                 parametros,
                                 promociones):
        """
        Realiza un reporte de los registros obtenidos en una consulta y lo guarda en un archivo de Excel.

        :param registros: una lista de tuplas que contiene los registros obtenidos de la consulta.
        :type registros: list
        :param parametros: una lista de que contiene los parametros con los que se hizo la consulta.
        :type parametros: list
        :param promociones: una lista de tuplas que contiene las promociones de la consulta.
        :type promociones: list

        :raises TypeError: Si no se ha realizado una consulta antes de generar un reporte.
        :raises ValueError: Si la consulta está vacía y no se puede generar un reporte.
        :raises exceptions.FileCreateError: Si el archivo de Excel no se puede crear.

        :return:
            - None
        """
        self.registros = registros
        self.promociones = promociones

        self.parametros = parametros
        print(self.parametros)

        # Obtener las columnas de la tabla
        # columnas = self.query.obtener_campos_tabla()
        columnas = ['N° boleto', 'Entrada', 'Salida', 'Tiempo',
                    'Importe', 'N° Corte', 'Placas', 'Promociones', 'QR Promo']

        try:
            # Verificar que se haya realizado una consulta antes de generar un reporte
            if self.registros is None:
                raise ValueError(
                    'Primero genera una consulta antes de generar un reporte')
            if len(self.registros) == 0:
                raise ValueError(
                    'La consulta esta vacia y no se puede generar un reporte')

            # Obtener la ruta y el nombre del archivo donde se guardará el reporte
            name_report = f'Reporte_General_{self.estacionamiento.replace(" ", "_")}'
            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension='.xlsx', initialfile=name_report)

            # Crear un archivo de Excel y escribir los registros
            workbook = xlsxwriter.Workbook(
                ruta_archivo, {'remove_timezone': True})
            worksheet = workbook.add_worksheet('Reporte')
            # Establecer la orientación de la hoja en horizontal
            worksheet.set_landscape()
            # ajustar el tamaño de la hoja a A4 al tamaño A4
            worksheet.set_paper(9)
            
            worksheet.margin_left = 1

            # Agregar la imagen en la esquina superior izquierda de la hoja de Excel
            imagen_path = self.tools_instance.read_path_config_file(
                'images', 'logo_pase')

            formato_columnas_informacion = workbook.add_format(
                {'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': '#D9D9D9'})
            formato_columnas = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': '#D9D9D9'})
            formato_columnas_blanco = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_texto = workbook.add_format(
                {'bold': False, 'align': 'right', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_texto_centrado = workbook.add_format(
                {'bold': False, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_moneda = workbook.add_format(
                {'num_format': '$#,##0.00', 'bold': True, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_total_ingreso = workbook.add_format(
                {'num_format': '$#,##0.00', 'bold': True, 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white', 'bg_color': '#D9D9D9'})
            formato_titulo = workbook.add_format(
                {'bold': True, 'font_size': 14, 'align': 'center'})
            formato_subtitulo = workbook.add_format(
                {'bold': True, 'font_size': 12, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1})

            worksheet.insert_image(0, 0, imagen_path, {
                                   'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            # Agregar título en CE - E3
            titulo = "REPORTE GENERAL"
            worksheet.merge_range('A3:H3', titulo, formato_titulo)

            subtitulo = "Datos del periodo"
            worksheet.merge_range('A8:C8', subtitulo, formato_subtitulo)

            worksheet.write('C5', 'Lugar', formato_columnas)
            worksheet.write('C6', 'Quien lo realiza', formato_columnas)

            quien = self.user_name
            lugar = self.estacionamiento

            worksheet.merge_range('D5:F5', lugar, formato_celdas_texto)
            worksheet.merge_range('D6:F6', quien, formato_celdas_texto)

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
                if isinstance(valor, tuple):
                    valor = ', '.join(str(elem) for elem in valor)
                    worksheet.write(fila, columna, valor, formato_celdas_texto)

                else:
                    if nuevo_nombre in ['Importe', 'Importe inicio', 'Importe final']:
                        worksheet.write(fila, columna, valor,
                                        formato_celdas_moneda)

                    else:
                        worksheet.write(fila, columna, valor,
                                        formato_celdas_texto)

            # Guarda el número de la última fila después de haber escrito los parámetros
            ultima_fila = worksheet.dim_rowmax + 1

            # Calcula la suma de la columna importe
            suma_importe = sum(0 if registro[columnas.index(
                'Importe')] is None else registro[columnas.index('Importe')] for registro in self.registros)

            # Escribe la suma en la hoja de cálculo
            worksheet.merge_range(
                ultima_fila, 0, ultima_fila, 1, 'Total de ingresos:', formato_columnas_blanco)
            worksheet.write(ultima_fila, 2, suma_importe,
                            formato_celdas_total_ingreso)

            fila = ultima_fila

            subtitulo = "Promociones"
            worksheet.merge_range('F8:H8', subtitulo, formato_subtitulo)

            # acomodar ancho de columnas

            worksheet.write('F9', 'Promocion', formato_columnas)
            worksheet.write('G9', 'Cantidad', formato_columnas)
            worksheet.write('H9', 'Total', formato_columnas)

            row = 9
            col = 5
            total_promocion = 0
            total_boletos = 0

            for promocion in self.promociones:
                worksheet.write(
                    row, col, promocion[0] if promocion[0] is not None else 'None', formato_celdas_texto_centrado)
                worksheet.write(
                    row, col + 1, promocion[1], formato_celdas_texto_centrado)
                worksheet.write(
                    row, col + 2, promocion[2] if promocion[2] is not None else 0, formato_celdas_moneda)

                row += 1
                total_boletos += promocion[1]
                total_promocion += promocion[2] if promocion[2] is not None else 0

            row + 3

            worksheet.write(row, col, 'Total', formato_columnas)
            worksheet.write(row, col + 1, total_boletos, formato_columnas)
            worksheet.write(row, col + 2, total_promocion,
                            formato_celdas_moneda)  # Monto Total por Promocion

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
                        worksheet.write(
                            i + FILA_INICIO_REGISTRO, j, fecha_hora_str, formato_celdas_texto_centrado)

                    # Si el campo es "Importe", aplicar el formato de moneda
                    elif columnas[j] == 'Importe':
                        if valor == None:
                            valor = 0
                        worksheet.write(i + FILA_INICIO_REGISTRO,
                                        j, valor, formato_celdas_moneda)

                    elif columnas[j] == 'Tiempo':
                        tiempo_str = valor
                        if valor is None:
                            tiempo_str = 'None'

                        worksheet.write(i + FILA_INICIO_REGISTRO, j,
                                        tiempo_str, formato_celdas_texto_centrado)

                    elif columnas[j] == 'Promociones':
                        if valor == None:
                            valor = 'None'
                        worksheet.write(i + FILA_INICIO_REGISTRO,
                                        j, valor, formato_celdas_texto_centrado)
                    else:
                        worksheet.write(i + FILA_INICIO_REGISTRO,
                                        j, valor, formato_celdas_texto_centrado)

                    worksheet.set_row(i + FILA_INICIO_REGISTRO, 30)

            worksheet.set_column('A:A', 13)
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 20)
            worksheet.set_column('D:D', 10)
            worksheet.set_column('E:E', 10)
            worksheet.set_column('F:F', 10)
            worksheet.set_column('G:G', 12)
            worksheet.set_column('H:H', 14)
            worksheet.set_column('I:I', 11)

            fila_final = worksheet.dim_rowmax + 2
            columna_final = worksheet.dim_colmax

            # Establecer el área de impresión desde la columna A hasta la H y desde la fila 1 hasta la última fila de datos escritos
            worksheet.print_area(0, 0, fila_final, columna_final)

            # Cerrar el archivo de Excel
            workbook.close()
            os.chmod(ruta_archivo, 0o777)

            self.tools_instance.convert_excel_to_pdf(ruta_archivo)
            messagebox.showinfo('Mensaje', 'El reporte fue generado con exito')

        # Manejo de errores
        except TypeError as e:
            messagebox.showerror(
                'Error', f'Error: No se puede generar el reporte ya que el valor del importe u hora de salida aun no esta definido.\n{e}')

        except ValueError as e:
            messagebox.showerror('Error', f'Error: {e}')

        except exceptions.FileCreateError as e:
            messagebox.showerror(
                'Error', f'Error: El reporte no se puede generar, seleccione el directorio para guardar el reporte y vuelva a intentar')
