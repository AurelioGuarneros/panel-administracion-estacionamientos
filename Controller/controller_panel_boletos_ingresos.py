from Views.view_calendar import Calendar_date
from Tools.proyect_tools import Tools
from Models.queries import Queries

from tkinter import filedialog, Toplevel
from tkinter import messagebox
import xlsxwriter
from xlsxwriter import exceptions
import os


class Controller_Panel_Boletos_Ingresos:
    """
    Controller del panel de boletos.

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
                 query: Queries = None):
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

    def hacer_consulta_boletos_ingresos(self,
                                        fecha_inicio_entrada: str,
                                        fecha_fin_entrada: str,
                                        corte_numero: int,
                                        corte_numero_inicio: int,
                                        corte_numero_fin: int,
                                        intervalo: int):
        """
        Realiza una consulta SQL con los valores proporcionados por el usuario y devuelve una lista de registros obtenidos.


        :param fecha_inicio_entrada (str): fecha de inicio de entrada en formato yyyy-mm-dd :param hh:mm:ss para consultar.
        :param fecha_fin_entrada (str): fecha de fin de entrada en formato yyyy-mm-dd hh:mm:ss para consultar.
        :param corte_numero (int): número de corte a consultar.
        :param corte_numero_inicio (int): número de corte a consultar, con un rango de inicio.
        :param corte_numero_fin (int): número de corte a consultar, con un rango final.


        :return:
            - registros (list) una lista de tuplas que contiene los registros obtenidos de la consulta.
            - parametros (list): una lista de que contiene los parametros con los que se hizo la consulta.
            - campos (list): una lista de tuplas que contiene las columnas de la consulta.

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
            data_boletos = self.query.hacer_consulta_sql_boletos(parametros, intervalo)
            data_ingresos = self.query.hacer_consulta_sql_ingresos(parametros)

            return data_boletos, data_ingresos, parametros

        except ValueError as e:
            messagebox.showwarning(
                'Error', f'Error: {e}\nPor favor introduzca un dato válido para realizar la consulta.')

        except TypeError as e:
            messagebox.showwarning(
                'Error', f'Error: {e}\nEl dato ingresado no es válido')

    def realizar_reporte(self, data_boletos: list, data_ingresos: tuple, parametros: dict, ventana:Toplevel):
        parametros = parametros
        registros_boletos, campos = data_boletos
        registros_ingresos = data_ingresos

        path = filedialog.askdirectory(
            title="Seleccione la ubicación para guardar los reportes")

        self.name_report(parametros)

        name_reporte_boletos, reporte_ingresos = self.name_report(parametros)

        name_reporte_boletos = os.path.join(
            path, name_reporte_boletos) + '.xlsx'
        reporte_ingresos = os.path.join(path, reporte_ingresos) + '.xlsx'

        ventana.title(f'Panel de administración reporte de boletos e ingresos -> Generando reportes...')

        self.realizar_reporte_boletos(
                name_reporte_boletos, registros_boletos, campos, parametros)

        self.realizar_reporte_ingresos(
                reporte_ingresos, registros_ingresos, parametros)

        ventana.title(f'Panel de administración reporte de boletos e ingresos')
            


    def name_report(self, parametros: dict) -> str:
        range_data = ""
        if 'fecha_inicio_entrada' in parametros and 'fecha_fin_entrada' in parametros:
            range_data = f"{parametros['fecha_inicio_entrada']} - {parametros['fecha_fin_entrada']}"

        elif 'fecha_inicio_entrada' in parametros:
            range_data = f"{parametros['fecha_inicio_entrada']} - Actualidad"

        elif 'fecha_fin_entrada' in parametros:
            range_data = f"Actualidad - {parametros['fecha_fin_entrada']}"

        ############################################################################################################################
        if 'corte_numero' in parametros:
            range_data = f"corte_{parametros['corte_numero']}"

        if 'corte_numero_inicio' in parametros and 'corte_numero_fin' in parametros:
            range_data = f"cortes_{parametros['corte_numero_inicio']} - {parametros['corte_numero_fin']}"

        elif 'corte_numero_inicio' in parametros:
            range_data = f"cortes_{parametros['corte_numero_inicio']} - Actualidad"

        elif 'corte_numero_fin' in parametros:
            range_data = f"Actualidad - {parametros['corte_numero_fin']}"

        return f'Reporte_Boletos_{self.estacionamiento.replace(" ", "_")}_{range_data}', f'Reporte_Ingresos_{self.estacionamiento.replace(" ", "_")}_{range_data}'

    def realizar_reporte_boletos(self, ruta_archivo, registros, campos, parametros):
        try:
            # Verificar que se haya realizado una consulta antes de generar un reporte
            if registros is None:
                raise ValueError(
                    'Primero genera una consulta antes de generar un reporte')
            # if len(registros) == 0: raise ValueError('La consulta esta vacia y no se puede generar un reporte')

            # Crear un archivo de Excel y escribir los registros
            workbook = xlsxwriter.Workbook(
                ruta_archivo, {'remove_timezone': True})
            worksheet = workbook.add_worksheet('Reporte')
            worksheet_grafico3 = workbook.add_worksheet(
                'Grafico total de boletos')
            worksheet_grafico1 = workbook.add_worksheet(
                'Grafico boleto por tiempo')
            worksheet_grafico2 = workbook.add_worksheet(
                'Grafico ingresos por tiempo')

            # Establecer la orientación de la hoja en horizontal
            worksheet_grafico1.set_landscape()
            worksheet_grafico2.set_landscape()
            worksheet_grafico3.set_landscape()

            # ajustar el tamaño de la hoja a oficio
            worksheet_grafico1.set_paper(5)
            worksheet_grafico2.set_paper(5)
            worksheet_grafico3.set_paper(5)

            # ajustar el margen
            worksheet_grafico1.margin_left = 0.8
            worksheet_grafico2.margin_left = 0.8
            worksheet_grafico3.margin_left = 0.8
            
            num_tipo_pago = (len(campos) - 3 ) / 2
            convert_to_pdf = True
    

            number_colums = 0
            margin_left = 0.7

            if num_tipo_pago == 1:
                margin_left = 1.3
                number_colums = 2

            elif num_tipo_pago ==2:
                margin_left = 1.3
                number_colums = 0

            elif num_tipo_pago ==3:
                worksheet.set_paper(1)
                worksheet.set_landscape()
                margin_left = 1
                number_colums = 2

            elif num_tipo_pago == 4:
                worksheet.set_paper(15)
                worksheet.set_landscape()                
                margin_left = 0.2
                worksheet.margin_rigth = 0
                number_colums = 2

            elif num_tipo_pago == 5:
                worksheet.set_paper(15)
                worksheet.set_landscape()
                margin_left = 0.2
                worksheet.margin_rigth = 0
                number_colums = 0

            elif num_tipo_pago == 6: # todo
                worksheet.set_paper(5)
                worksheet.set_landscape
                number_colums = 0

            new_campos = campos + [f"" for _ in range(number_colums)]
            worksheet.margin_left = margin_left
            new_registros = [registro + ('',) * number_colums for registro in registros]
            new_registros = tuple(new_registros)

            if num_tipo_pago >= 7:
                new_registros = registros
                new_campos = campos
                convert_to_pdf = False
                

            # Agregar la imagen en la esquina superior izquierda de la hoja de Excel
            imagen_path = self.tools_instance.read_path_config_file(
                'images', 'logo_pase')

            formato_columnas_informacion = workbook.add_format(
                {'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': '#D9D9D9'})
            formato_columnas = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                                   'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': '#D9D9D9', 'text_wrap': True})
            formato_celdas_texto = workbook.add_format(
                {'bold': True, 'align': 'right', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
            formato_celdas_en_blanco = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'pattern': 1, 'bg_color': 'white'})
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

            worksheet.insert_image(0, 0, imagen_path, {
                                   'x_offset': 0, 'y_offset': 0, 'x_scale': 0.3, 'y_scale': 0.3})
            worksheet_grafico1.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            worksheet_grafico2.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            worksheet_grafico3.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})

            # Agregar título
            titulo = "REPORTE BOLETOS"
            letter_column = self.tools_instance.get_letter_from_column_number(len(new_campos) - 1)
            worksheet.merge_range(f'A1:{letter_column}1', titulo, formato_titulo)

            subtitulo = "Datos del periodo"
            worksheet.merge_range('A3:B3', subtitulo, formato_subtitulo)

            subtitulo = "Datos quien realiza el reporte"
            worksheet.merge_range('C3:G3', subtitulo, formato_subtitulo)

            worksheet.merge_range('C4:D4', 'Estacionamiento',formato_columnas_informacion)
            worksheet.merge_range('C5:D5', 'Nombre completo',formato_columnas_informacion)

            worksheet.merge_range('E4:G4', self.estacionamiento, formato_celdas_texto)
            worksheet.merge_range('E5:G5', self.user_name,formato_celdas_texto)

            columna_A = 0
            columna_B = 1
            columna_C = 2
            columna_D = 3
            columna_E = 4
            columna_F = 5
            columna_G = 6

            # Escribe los parámetros en la hoja de cálculo con los nuevos nombres
            for i, (clave, valor) in enumerate(parametros.items()):
                fila = i + 3
                # columna
                nuevo_nombre = self.nuevos_nombres.get(clave, valor)
                #worksheet.merge_range(fila, columna_A, fila, columna_B, nuevo_nombre, formato_columnas_informacion)
                worksheet.write(fila, columna_A, nuevo_nombre, formato_columnas_informacion)
                if valor == None:
                    valor = 'None' 
                # worksheet.merge_range(fila, columna_C, fila, columna_E, valor, formato_celdas_texto_centrado)
                worksheet.write(fila, columna_B, valor, formato_celdas_texto_centrado)

            fila_inicio = worksheet.dim_rowmax + 3

            # Obtener las columnas de la tabla
            columnas = campos

            # Escribir los registros
            for i, registro in enumerate(new_registros):
                for j, valor in enumerate(registro):
                    if new_campos[j] == 'Intervalo':
                        # Extraer días, horas, minutos y segundos
                        dias = valor.days
                        segundos_totales = valor.seconds
                        horas, segundos_totales = divmod(
                            segundos_totales, 3600)  # 3600 segundos en una hora
                        # 60 segundos en un minuto
                        minutos, segundos = divmod(segundos_totales, 60)

                        # Crear la cadena en el formato deseado
                        valor = f"{horas:02}:{minutos:02}:{segundos:02}" if dias == 0 else f"{dias} Días, {horas:02}:{minutos:02}:{segundos:02}"
                        valor.replace(', ', '\n')

                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_texto)

                    elif 'Promedio' in new_campos[j]:
                        # Extraer días, horas, minutos y segundos
                        dias = valor.days
                        segundos_totales = valor.seconds
                        horas, segundos_totales = divmod(
                            segundos_totales, 3600)  # 3600 segundos en una hora
                        # 60 segundos en un minuto
                        minutos, segundos = divmod(segundos_totales, 60)

                        # Crear la cadena en el formato deseado
                        valor = f"{horas:02}:{minutos:02}:{segundos:02}" if dias == 0 else f"{dias} Días, {horas:02}:{minutos:02}:{segundos:02}"
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_texto)

                    elif 'Importe' in new_campos[j]:
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_moneda)

                    elif 'Boletos' in new_campos[j]:
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_texto)

                    elif '' in new_campos[j]:
                        worksheet.write(i + fila_inicio, j,
                                        "-", formato_celdas_en_blanco)

                    else:
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_texto)


            # Establecer un ancho máximo para las columnas
            max_length = 9

            for i, columna in enumerate(new_campos):
                columna = str(columna).replace('_', '\n')

                if "ADMIN" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 8)

                if "Cancelado" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 10)

                elif "Normal\nImporte" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 10)

                elif "Perdido" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 8)

                elif "Promedio" == columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 9)

                elif "Importe\nIntervalo" == columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 12)

                elif "Boletos" in columna:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)
                    worksheet.set_column(i, i, 8)

                else:
                    worksheet.write(fila_inicio - 1, i,
                                    columna, formato_columnas)

                    # max_length = max([len(str(new_registros[i]))
                    #                  for new_registros in registros] + [len(columna)])
                    # if max_length > ancho_maximo:
                    #     max_length = ancho_maximo  # Establece el ancho máximo si es mayor

                    worksheet.set_column(i, i, max_length)
                    
            worksheet.set_column('A:A', 9)
            worksheet.set_column('B:B', 10)
            worksheet.set_row(fila_inicio - 1, 30)

            fila_final = worksheet.dim_rowmax + 1

            for col_num, col_name in enumerate(columnas):
                if 'Boletos' in col_name:
                    total_boletos = sum(new_registros[col_num]
                                        for new_registros in registros)
                    worksheet.write(fila_final, col_num,
                                    total_boletos, formato_celdas_texto)

                elif 'Importe' in col_name:
                    total_imrporte = sum(new_registros[col_num]
                                         for new_registros in registros)
                    worksheet.write(fila_final, col_num,
                                    total_imrporte, formato_celdas_moneda)

            worksheet.write(fila_final, columna_A, "TOTALES", formato_columnas)

            fila_final = worksheet.dim_rowmax + 1

            # Agregar los datos para el gráfico circular
            chart_tickets = workbook.add_chart({
                'type': 'column'
            })

            # Agregar los datos para el gráfico circular
            chart_money = workbook.add_chart({
                'type': 'column'
            })

            row_start = fila_inicio + 1
            categories = f'=Reporte!$A${row_start}:$A${row_start-1 + len(registros)}'

            for i, columna in enumerate(columnas):
                if i > 0 and i < len(columnas) - 2:
                    col_position = chr(66 + i - 1)
                    name = str(columnas[i]).replace('_', '\n')

                    if i % 2 != 0:
                        chart_tickets.add_series({
                            'name': f'{name}',
                            'categories': categories,
                            'values': f'=Reporte!${col_position}${row_start}:${col_position}${row_start-1 + len(registros)}',
                            'data_labels': {
                                'percentage': True
                                # 'value': True
                            },
                        })

                    else:
                        chart_money.add_series({
                            'name': f'{name}',
                            'categories': categories,
                            'values': f'=Reporte!${col_position}${row_start}:${col_position}${row_start-1 + len(registros)}',
                            'data_labels': {
                                'percentage': True
                                # 'value': True
                            },
                        })

            chart_scale_x = 2.25
            chart_scale_y = 1.8

            chart_tickets.set_style(10)
            # Establece un estilo para el gráfico
            chart_tickets.set_title({
                'name': 'Gráfico de Boletos por rango de tiempo'
            })

            chart_tickets.set_size({
                'x_scale': chart_scale_x,
                'y_scale': chart_scale_y
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico1.insert_chart(7, 0, chart_tickets)

            chart_money.set_style(10)
            # Establece un estilo para el gráfico
            chart_money.set_title({
                'name': 'Gráfico de Ingresos por rango de tiempo'
            })

            chart_money.set_size({
                'x_scale': chart_scale_x,
                'y_scale': chart_scale_y
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico2.insert_chart(7, 0, chart_money)

            # Agregar los datos para el gráfico circular
            chart_total_tickets = workbook.add_chart({
                'type': 'column'
            })

            row_start = fila_inicio

            fila_final = worksheet.dim_rowmax + 1

            # Crear una cadena de fórmula que excluye las categorías que contienen "Ingresos"
            categories_tickets = "="
            categories_money = "="
            values_tickets = "="
            values_money = "="

            for i, columna in enumerate(columnas[:-2]):
                column_letter = self.tools_instance.get_letter_from_column_number(
                    i)
                if "Boletos" in columna:
                    values_tickets += f'Reporte!${column_letter}${fila_final},'
                    categories_tickets += f"Reporte!${column_letter}${row_start},"
                elif "Importe" in columna:
                    values_money += f'Reporte!${column_letter}${fila_final},'
                    categories_money += f"Reporte!${column_letter}${row_start},"

            categories_tickets = categories_tickets[:-1]
            categories_money = categories_money[:-1]
            values_tickets = values_tickets[:-1]
            values_money = values_money[:-1]

            chart_total_tickets.add_series({
                'name': f'Total de boletos',
                'categories': categories_tickets,
                'values': values_tickets,
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
                'name': 'Gráfico de total de boletos'
            })

            chart_total_tickets.set_size({
                'x_scale': chart_scale_x,
                'y_scale': chart_scale_y
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico3.insert_chart(7, 0, chart_total_tickets)

            # Establecer el área de impresión desde la columna A hasta la H y desde la fila 1 hasta la última fila de datos escritos
            worksheet.print_area(0, 0, fila_final, worksheet.dim_colmax)

            # Cerrar el archivo de Excel
            workbook.close()
            os.chmod(ruta_archivo, 0o777)

            if convert_to_pdf:
                self.tools_instance.convert_excel_to_pdf(ruta_archivo)

            if convert_to_pdf == False:
                messagebox.showwarning("Alerta", "El reporte de boletos era demasiado grande para generarlo en PDF, por lo que solo se generó en Excel")
            messagebox.showinfo('Mensaje', 'El reporte de boletos fue generado con exito')

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

    def realizar_reporte_ingresos(self, ruta_archivo, registros, parametros):
        try:
            # Verificar que se haya realizado una consulta antes de generar un reporte
            if registros is None:
                raise ValueError(
                    'Primero genera una consulta antes de generar un reporte')
            # if len(registros) == 0: raise ValueError('La consulta esta vacia y no se puede generar un reporte')

            # Crear un archivo de Excel y escribir los registros
            workbook = xlsxwriter.Workbook(
                ruta_archivo, {'remove_timezone': True})
            worksheet = workbook.add_worksheet('Reporte')
            worksheet_grafico1 = workbook.add_worksheet('Grafico ingresos')

            # Establecer la orientación de la hoja en horizontal
            # worksheet.set_landscape()
            worksheet_grafico1.set_landscape()

            # ajustar el tamaño de la hoja a A4 al tamaño A4
            worksheet.set_paper(1)
            
            # ajustar el margen
            worksheet.margin_left = 1

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
            worksheet_grafico1.insert_image(
                0, 0, imagen_path, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1, 'y_scale': 1})
            # Agregar título en CE - E3
            titulo = "REPORTE INGRESOS"
            worksheet.merge_range('A1:F1', titulo, formato_titulo)

            subtitulo = "Datos del periodo"
            worksheet.merge_range('A8:C8', subtitulo, formato_subtitulo)

            subtitulo = "Datos quien realiza el reporte"
            worksheet.merge_range('D8:F8', subtitulo, formato_subtitulo)

            worksheet.write('D9', 'Lugar', formato_columnas_informacion)
            worksheet.write('D10', 'Nombre', formato_columnas_informacion)

            quien = self.user_name
            lugar = self.estacionamiento

            worksheet.merge_range('E9:F9', lugar, formato_celdas_texto)
            worksheet.merge_range('E10:F10', quien, formato_celdas_texto)

            columna_A = 0
            columna_B = 1
            columna_C = 2
            columna_D = 3
            columna_E = 4
            columna_F = 5
            columna_G = 6

            # Escribe los parámetros en la hoja de cálculo con los nuevos nombres
            for i, (clave, valor) in enumerate(parametros.items()):
                fila = i + 8
                # columna
                nuevo_nombre = self.nuevos_nombres.get(clave, valor)
                columna_A = 0
                columna_B = 1
                worksheet.merge_range(
                    fila, columna_A, fila, columna_B, nuevo_nombre, formato_columnas_informacion)

                if valor == None:
                    valor = 'None'
                worksheet.write(fila, columna_C, valor ,formato_celdas_texto_centrado)
                # worksheet.merge_range(fila, columna_C, fila, columna_D, valor, formato_celdas_texto_centrado)

            fila_inicio = worksheet.dim_rowmax + 2

            # worksheet.merge_range(
            #     fila_inicio, columna_B, fila_inicio, columna_C, 'EFECTIVO', formato_subtitulo)
            worksheet.merge_range(
                fila_inicio, columna_C, fila_inicio, columna_F, 'TOTALES', formato_subtitulo)

            fila_inicio = worksheet.dim_rowmax + 2

            # Obtener las columnas de la tabla
            columnas = ['Concepto',
                        #'N° Boletos',
                        'Importe', 'Total Boletos', 'Subtotal', 'Impuesto', 'Total']

            # Establecer el nombre y ancho de las columnas en función del contenido
            for i, columna in enumerate(columnas):
                worksheet.write(fila_inicio - 1, i, columna, formato_columnas)

            suma_boletos = 0
            suma_importe = 0

            suma_subtotal = 0
            suma_impuesto = 0

            valor_importe = 0
            # Escribir los registros
            for i, registro in enumerate(registros):
                valor = None
                for j, valor in enumerate(registro):
                    if columnas[j] == 'Concepto':
                        if valor == None:
                            valor = 'None'
                        worksheet.write(i + fila_inicio, j,
                                        valor, formato_celdas_texto)

                    if columnas[j] == 'Importe':
                        if valor == None:
                            valor = 0
                        valor_importe = valor
                        worksheet.write(i + fila_inicio, j,valor_importe, formato_celdas_moneda)
                        worksheet.write(i + fila_inicio, columna_F,valor_importe, formato_celdas_moneda)
                        suma_importe = suma_importe + valor

                    #if columnas[j] == 'N° Boletos':
                    if columnas[j] == 'Total Boletos':
                        if valor == None:
                            valor = 0
                        #worksheet.write(i + fila_inicio, j,valor, formato_celdas_texto)
                        worksheet.write(i + fila_inicio, j,valor, formato_celdas_texto)
                        suma_boletos = suma_boletos + valor


                subtotal = 0
                subtotal = valor_importe/1.16
                worksheet.write(i + fila_inicio, columna_D,
                                subtotal, formato_celdas_moneda)
                suma_subtotal = suma_subtotal + subtotal

                impuesto = 0
                impuesto = subtotal*0.16
                worksheet.write(i + fila_inicio, columna_E,
                                impuesto, formato_celdas_moneda)
                suma_impuesto = suma_impuesto + impuesto

            fila_final = worksheet.dim_rowmax + 2

            worksheet.write(fila_final, columna_A, "TOTAL", formato_columnas)
            # worksheet.write(fila_final, columna_B,suma_boletos, formato_celdas_texto)
            worksheet.write(fila_final, columna_B,suma_importe, formato_celdas_moneda)
            worksheet.write(fila_final, columna_C,suma_boletos, formato_celdas_texto)
            worksheet.write(fila_final, columna_D,suma_subtotal, formato_celdas_moneda)
            worksheet.write(fila_final, columna_E,suma_impuesto, formato_celdas_moneda)
            worksheet.write(fila_final, columna_F,suma_importe, formato_celdas_moneda)

            worksheet.set_column('A:A', 11)
            worksheet.set_column('B:B', 14)
            worksheet.set_column('C:C', 12)
            worksheet.set_column('D:D', 14)
            worksheet.set_column('E:E', 14)
            worksheet.set_column('F:F', 14)
            # worksheet.set_column('G:G', 14)

            fila_final = worksheet.dim_rowmax + 1
            columna_final = worksheet.dim_colmax

            row_start = fila_inicio + 1

            # Agregar los datos para el gráfico circular
            chart_money = workbook.add_chart({
                'type': 'column'
            })

            chart_money.add_series({
                'name': 'Ingresos',
                'categories': f'=Reporte!$A${row_start}:$A${row_start-1 +len(registros)}',
                'values':     f'=Reporte!$B${row_start}:$B${row_start-1 +len(registros)}',
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

            chart_scale = 1.7

            chart_money.set_size({
                'x_scale': chart_scale,
                'y_scale': chart_scale
            })

            # Agregar el gráfico a la hoja de trabajo
            worksheet_grafico1.insert_chart(7, 0, chart_money)

            # Establecer el área de impresión desde la columna A hasta la H y desde la fila 1 hasta la última fila de datos escritos
            worksheet.print_area(0, 0, fila_final, columna_final)
            # worksheet.center_horizontally()

            # Cerrar el archivo de Excel
            workbook.close()
            os.chmod(ruta_archivo, 0o777)

            self.tools_instance.convert_excel_to_pdf(ruta_archivo)
            messagebox.showinfo('Mensaje', 'El reporte de ingresos fue generado con exito')

        # Manejo de errores
        except TypeError as e:
            messagebox.showerror(
                'Error', f'Error: No se puede generar el reporte ya que el valor de la hora salida aun no esta definido.\n{e}')
        except ValueError as e:
            messagebox.showerror('Error', f'Error: {e}')
        except exceptions.FileCreateError as e:
            messagebox.showerror(
                'Error', f'Error: El reporte no se puede generar, seleccione el directorio para guardar el reporte y vuelva a intentar')
