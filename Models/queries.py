from .database import database_connection
from Tools.proyect_tools import Tools

from tkinter import messagebox


class Queries:
    """
    Esta clase contiene métodos para ejecutar consultas a una base de datos mediante una conexión establecida con la clase database_connection
    :param estacionamiento (str): Nombre de la conexión del estacionamiento.
    """

    def __init__(self, estacionamiento: str):
        """
        Inicializa una instancia de la clase `Queries`.
        :param estacionamiento (str): Nombre del estacionamiento.
        """
        # Crear una instancia de la clase "tools" para acceder a sus métodos
        self.tools_instance = Tools()
        self.estacionamiento: str = estacionamiento
        self.data_base = database_connection(
            estacionamiento=self.estacionamiento)

    def obtener_lista_de(self, tabla: str, listar: str, revez: str = None) -> list:
        """
        Devuelve una lista con los valores únicos de la columna especificada de la tabla 'Entradas' de la base de datos.
        :param tabla (str): Nombre de la tabla de la que se quiere hacer la consulta.
        :param listar (str): Nombre de la columna de la tabla de la que se quieren obtener los valores únicos.
        :param revez: (str or None) Si se especifica 'D', devuelve los valores en orden descendente;
            si se especifica 'A', los devuelve en orden ascendente; si no se especifica, los devuelve en el orden en que se encuentran en la tabla.
        :return:
            - lista_sin_nones (list): Una lista con los valores únicos de la columna especificada de la tabla 'Entradas',
                sin incluir valores 'None'.
        """
        if self.data_base.connection:
            # Si revez es igual a 'D', la consulta se hace en orden descendente.
            if revez == 'D':
                query = f"SELECT DISTINCT {listar} FROM {tabla} ORDER BY {listar} DESC;"
            # Si revez es igual a 'A', la consulta se hace en orden ascendente.
            elif revez == 'A':
                query = f"SELECT DISTINCT {listar} FROM {tabla} ORDER BY {listar} ASC;"
            # Si revez no está definido, se realiza una consulta simple.
            if revez == None:
                query = f"SELECT DISTINCT {listar} FROM {tabla};"

            # Se ejecuta la consulta y se obtiene el resultado.
            resultado = self.data_base.execute_query(query)
            if resultado is not None:
                # Se obtiene una lista con los valores de la columna especificada, sin valores None.
                lista = [r[0] for r in resultado]
                lista_sin_nones = list(filter(lambda x: x is not None, lista))
                # Se retorna la lista sin los valores None.
                return lista_sin_nones

    def hacer_consulta_sql_entradas(self, parametros: list):
        """
        Crea una consulta SQL dependiendo de los valores de los campos de consulta.
        :param parametros (list): Una lista de parámetros con los que se realizará la consulta.
        :return:
            - registros (list): Una lista de tuplas que contiene los registros obtenidos de la consulta.
            - promociones (list): Una lista de tuplas que contiene las promociones de la consulta.
        """
        # Creamos una lista vacía para agregar las cláusulas WHERE a nuestra consulta
        where = []
        ############################################################################################################################
        # Si existe el parámetro 'id' en el diccionario de parámetros,
        # se agrega una condición a la lista de condiciones a evaluar.
        if 'id' in parametros:
            where.append(f"id = {parametros['id']}")
        ############################################################################################################################

        ############################################################################################################################
        # Si existe el parámetro 'tarifa_preferente' en el diccionario de parámetros,
        # se agrega una condición a la lista de condiciones a evaluar.
        if 'tarifa_preferente' in parametros:
            if len(parametros['tarifa_preferente']) == 1:
                if parametros['tarifa_preferente']:
                    where.append(
                        f"TarifaPreferente = '{str(parametros['tarifa_preferente'][0])}'")
            else:  # len(parametros['tarifa_preferente']) > 1:
                where.append(
                    f"TarifaPreferente IN {parametros['tarifa_preferente']}")
        ############################################################################################################################

        ############################################################################################################################
        # Si se especifica una fecha de inicio y una fecha de fin para entradas, agregamos una cláusula WHERE que seleccione
        # todas las entradas entre esas dos fechas. Si solo se especifica una fecha de inicio o una fecha de fin para entradas,
        # seleccionamos todas las entradas a partir de la fecha de inicio o hasta la fecha de fin, respectivamente.
        if 'fecha_inicio_entrada' in parametros and 'fecha_fin_entrada' in parametros:
            where.append(f"""CorteInc BETWEEN
                         (SELECT MIN(Folio) FROM Cortes WHERE FechaIni BETWEEN '{parametros['fecha_inicio_entrada']}' AND '{parametros['fecha_fin_entrada']}') AND
                         (SELECT MAX(Folio) FROM Cortes WHERE FechaIni BETWEEN '{parametros['fecha_inicio_entrada']}' AND '{parametros['fecha_fin_entrada']}') """)

        elif 'fecha_inicio_entrada' in parametros:
            where.append(
                f"CorteInc >= (SELECT MIN(Folio) FROM Cortes WHERE FechaIni >= '{parametros['fecha_inicio_entrada']}')")

        elif 'fecha_fin_entrada' in parametros:
            where.append(
                f"CorteInc <= (SELECT MAX(Folio) FROM Cortes WHERE FechaIni <= '{parametros['fecha_fin_entrada']}')")

        ############################################################################################################################
        # Si se especifica el número de corte, agregamos una cláusula WHERE a la lista
        if 'corte_numero' in parametros:
            where.append(f"CorteInc = {parametros['corte_numero']}")

        # Si se especifican tanto el inicio como el fin del rango de números de corte,
        # agregamos una cláusula WHERE entre ellos
        if 'corte_numero_inicio' in parametros and 'corte_numero_fin' in parametros:
            where.append(
                f"CorteInc BETWEEN {parametros['corte_numero_inicio']} AND {parametros['corte_numero_fin']}")

        # Si solo se especifica el número de inicio del rango de números de corte,
        # agregamos una cláusula WHERE para números de corte mayores o iguales a él
        elif 'corte_numero_inicio' in parametros:
            where.append(f"CorteInc >= {parametros['corte_numero_inicio']}")

        # Si solo se especifica el número de fin del rango de números de corte,
        # agregamos una cláusula WHERE para números de corte menores o iguales a él
        elif 'corte_numero_fin' in parametros:
            where.append(f"CorteInc <= {parametros['corte_numero_fin']}")
        ############################################################################################################################

        ############################################################################################################################
        # Si se especifica el importe, agregamos una cláusula WHERE a la lista
        if 'ingreso' in parametros:
            where.append(f"Importe = '{parametros['ingreso']}'")

        # Si se especifica un rango de importes, agregamos una cláusula BETWEEN a la lista
        if 'ingreso_mayor' in parametros and 'ingreso_menor' in parametros:
            where.append(
                f"Importe BETWEEN '{parametros['ingreso_menor']}' AND '{parametros['ingreso_mayor']}'")

        # Si se especifica un importe máximo, agregamos una cláusula <= a la lista
        elif 'ingreso_mayor' in parametros:
            where.append(f"Importe <= '{parametros['ingreso_mayor']}'")

        # Si se especifica un importe mínimo, agregamos una cláusula >= a la lista
        elif 'ingreso_menor' in parametros:
            where.append(f"Importe >= '{parametros['ingreso_menor']}'")

        ############################################################################################################################

        ############################################################################################################################
        # Si tenemos al menos una cláusula WHERE, las unimos con el operador AND y agregamos la cláusula WHERE
        # completa a nuestra consulta SQL. De lo contrario, simplemente dejamos la cláusula WHERE vacía.
        if where:
            where_clause = "WHERE " + " AND ".join(where)
        else:
            where_clause = ""

        ############################################################################################################################
        if self.data_base.connection:
            # Subconsulta de solo lectura: no requiere CREATE/DROP VIEW.
            base = f"""SELECT id, Entrada, Salida, TiempoTotal, Importe,
                       CorteInc, Placas,
                       REPLACE(REPLACE(REPLACE(REPLACE(
                           IF(TarifaPreferente IN ('Danado', 'Normal'),
                              'Normal', TarifaPreferente),
                           'Danado', ''), 's/co', 'Cortesia'),
                           'Per', 'Perdido'), 'CDO', 'Cancelado') AS TarifaPreferente,
                       COALESCE(QRpromo, 'N/A') AS `COALESCE(QRpromo, "N/A")`
                       FROM Entradas {where_clause}"""
            registros = self.data_base.execute_query(f"SELECT * FROM ({base}) AS consulta")
            if registros is None:
                return None
            if len(registros) == 0:
                messagebox.showinfo('Info', 'No hay registros que correspondan a la consulta establecida.')
            promociones = self.data_base.execute_query(
                f"""SELECT TarifaPreferente, COUNT(*), SUM(Importe) AS ImporteTot
                     FROM ({base}) AS consulta
                     GROUP BY TarifaPreferente ORDER BY ImporteTot DESC""")
            if promociones is None:
                return None
            return registros, promociones

    def hacer_consulta_sql_pensionados(self, parametros: list):
        """
        Crea una consulta SQL dependiendo de los valores de los campos de consulta.
        :param parametros (list): Una lista de parámetros con los que se realizará la consulta.
        :return:
            - registros (list): Una lista de tuplas que contiene los registros obtenidos de la consulta.
        """
        where = []
        ##########################################################################################################
        if 'numero_tarjeta' in parametros:
            where.append(f"p.Num_tarjeta = {parametros['numero_tarjeta']}")
        ##########################################################################################################
        if 'nombre_cliente' in parametros:
            where.append(f"p.Nom_cliente = '{parametros['nombre_cliente']}'")
        ##########################################################################################################
        if 'apellido_1_cliente' in parametros:
            where.append(
                f"p.Apell1_cliente = '{parametros['apellido_1_cliente']}'")
        ##########################################################################################################
        if 'apellido_2_cliente' in parametros:
            where.append(
                f"p.Apell2_cliente = '{parametros['apellido_2_cliente']}'")
        ##########################################################################################################
        if 'fecha_inicio_entrada' in parametros and 'fecha_fin_entrada' in parametros:
            where.append(
                f"mp.Entrada BETWEEN '{parametros['fecha_inicio_entrada']}' AND '{parametros['fecha_fin_entrada']}'")

        elif 'fecha_inicio_entrada' in parametros:
            where.append(
                f"mp.Entrada >= '{parametros['fecha_inicio_entrada']}'")

        elif 'fecha_fin_entrada' in parametros:
            where.append(f"mp.Entrada <= '{parametros['fecha_fin_entrada']}'")
        ##########################################################################################################
        if 'estado' in parametros:
            where.append(f"mp.Estatus = '{parametros['estado']}'")
        ##########################################################################################################
        if 'tiempo_dentro' in parametros:
            # Si existe el parámetro 'tiempo_dentro' en el diccionario de parámetros,
            # se agrega una condición a la lista de condiciones a evaluar.
            where.append(
                f"mp.TiempoTotal = '{str(parametros['tiempo_dentro'])}'")

        if 'tiempo_dentro_inicio' in parametros and 'tiempo_dentro_fin' in parametros:
            # Si existen los parámetros 'tiempo_dentro_inicio' y 'tiempo_dentro_fin'
            # en el diccionario de parámetros, se agrega una condición a la lista de
            # condiciones a evaluar.
            where.append(
                f"mp.TiempoTotal BETWEEN '{str(parametros['tiempo_dentro_inicio'])}' AND '{str(parametros['tiempo_dentro_fin'])}'")

        elif 'tiempo_dentro_inicio' in parametros:
            # Si existe únicamente el parámetro 'tiempo_dentro_inicio' en el
            # diccionario de parámetros, se agrega una condición a la lista de
            # condiciones a evaluar.
            where.append(
                f"mp.TiempoTotal >= '{str(parametros['tiempo_dentro_inicio'])}'")

        elif 'tiempo_dentro_fin' in parametros:
            # Si existe únicamente el parámetro 'tiempo_dentro_fin' en el
            # diccionario de parámetros, se agrega una condición a la lista de
            # condiciones a evaluar.
            where.append(
                f"mp.TiempoTotal <= '{str(parametros['tiempo_dentro_fin'])}'")
        ##########################################################################################################
        if where:
            where_clause = "WHERE " + " AND ".join(where)
        else:
            where_clause = ""
        ############################################################################################################################
        if self.data_base.connection:
            # Devolvemos la consulta SQL completa
            query_registros = f"SELECT mp.Id_movs, p.Num_tarjeta, p.Nom_cliente, p.Apell1_cliente, p.Apell2_cliente, mp.Entrada, mp.Salida, TIMEDIFF(mp.Salida, mp.Entrada) AS TiempoTotal, mp.Estatus FROM MovimientosPens mp INNER JOIN Pensionados p ON mp.Idcliente = p.Id_cliente {where_clause};"
            print(f'Query Registros: {query_registros}')

            registros = self.data_base.execute_query(query_registros)

            if len(registros) == 0:
                messagebox.showinfo(
                    'Info', 'No hay registros que correspondan a la consulta establecida.')

            return registros

    def hacer_consulta_sql_ingresos(self, parametros: list):
        """
        Crea una consulta SQL dependiendo de los valores de los campos de consulta.
        :param parametros (list): Una lista de parámetros con los que se realizará la consulta.
        :return:
            - registros (list): Una lista de tuplas que contiene los registros obtenidos de la consulta.
        """
        where = []
        ############################################################################################################################
        if 'fecha_inicio_entrada' in parametros and 'fecha_fin_entrada' in parametros:
            where.append(f"""CorteInc BETWEEN
                         (SELECT MIN(Folio) FROM Cortes WHERE FechaIni BETWEEN '{parametros['fecha_inicio_entrada']}' AND '{parametros['fecha_fin_entrada']}') AND
                         (SELECT MAX(Folio) FROM Cortes WHERE FechaIni BETWEEN '{parametros['fecha_inicio_entrada']}' AND '{parametros['fecha_fin_entrada']}') """)

        elif 'fecha_inicio_entrada' in parametros:
            where.append(
                f"CorteInc >= (SELECT MIN(Folio) FROM Cortes WHERE FechaIni >= '{parametros['fecha_inicio_entrada']}')")

        elif 'fecha_fin_entrada' in parametros:
            where.append(
                f"CorteInc <= (SELECT MAX(Folio) FROM Cortes WHERE FechaIni <= '{parametros['fecha_fin_entrada']}')")

        ############################################################################################################################
        if 'corte_numero' in parametros:
            where.append(f"CorteInc = {parametros['corte_numero']}")

        if 'corte_numero_inicio' in parametros and 'corte_numero_fin' in parametros:
            where.append(
                f"CorteInc BETWEEN {parametros['corte_numero_inicio']} AND {parametros['corte_numero_fin']}")

        elif 'corte_numero_inicio' in parametros:
            where.append(f"CorteInc >= {parametros['corte_numero_inicio']}")

        elif 'corte_numero_fin' in parametros:
            where.append(f"CorteInc <= {parametros['corte_numero_fin']}")

        ############################################################################################################################
        if where:
            where_clause = "WHERE " + " AND ".join(where)
        else:
            where_clause = ""
        ############################################################################################################################
        if self.data_base.connection:
            # Agrupación directa, sin vistas persistentes.
            concepto = """REPLACE(REPLACE(REPLACE(REPLACE(
                IF(TarifaPreferente IN ('Danado', 'Normal'), 'Normal', TarifaPreferente),
                'Danado', ''), 's/co', 'Cortesia'), 'Per', 'Perdido'),
                'CDO', 'Cancelado')"""
            query = f"""SELECT {concepto} AS Concepto,
                         SUM(Importe) AS Importe, COUNT(*) AS Numero_Boletos
                         FROM Entradas {where_clause}
                         GROUP BY Concepto"""
            registros = self.data_base.execute_query(query)
            if registros is None:
                return None
            if not registros:
                messagebox.showinfo('Info', 'No hay registros que correspondan a la consulta establecida.')
            return registros

    def hacer_consulta_sql_boletos(self, parametros: dict, intervalo:int):
        """
        Crea una consulta SQL dependiendo de los valores de los campos de consulta.
        :param parametros (dict): Una lista de parámetros con los que se realizará la consulta.
        :return:
            - registros (list): Una lista de tuplas que contiene los registros obtenidos de la consulta.
            - campos (list): Una lista que contiene las columnas de la consulta.
        """
        where = []
        intervalo = intervalo * 60
        ############################################################################################################################
        if 'fecha_inicio_entrada' in parametros and 'fecha_fin_entrada' in parametros:
            where.append(
                f"""CorteInc BETWEEN (SELECT MIN(Folio) FROM Cortes WHERE FechaIni BETWEEN '{parametros['fecha_inicio_entrada']}' AND '{parametros['fecha_fin_entrada']}') AND (SELECT MAX(Folio) FROM Cortes WHERE FechaIni BETWEEN '{parametros['fecha_inicio_entrada']}' AND '{parametros['fecha_fin_entrada']}') """)

        elif 'fecha_inicio_entrada' in parametros:
            where.append(
                f"""CorteInc >= (SELECT MIN(Folio) FROM Cortes WHERE FechaIni >= '{parametros['fecha_inicio_entrada']}')""")

        elif 'fecha_fin_entrada' in parametros:
            where.append(
                f"""CorteInc <= (SELECT MAX(Folio) FROM Cortes WHERE FechaIni <= '{parametros['fecha_fin_entrada']}')""")
        ############################################################################################################################
        if 'corte_numero' in parametros:
            where.append(f"CorteInc = {parametros['corte_numero']}")

        if 'corte_numero_inicio' in parametros and 'corte_numero_fin' in parametros:
            where.append(
                f"CorteInc BETWEEN {parametros['corte_numero_inicio']} AND {parametros['corte_numero_fin']}")

        elif 'corte_numero_inicio' in parametros:
            where.append(f"CorteInc >= {parametros['corte_numero_inicio']}")

        elif 'corte_numero_fin' in parametros:
            where.append(f"CorteInc <= {parametros['corte_numero_fin']}")

        ############################################################################################################################
        if where:
            where_clause = " AND ".join(where)
        else:
            where_clause = ""

        ############################################################################################################################
        if self.data_base.connection:
            # Agrupar por intervalo y tarifa, sin CREATE VIEW, SET ni PREPARE.
            # La tabla dinámica se arma en Python para evitar SQL dinámico.
            filtro = f"WHERE {where_clause}" if where_clause else ""
            concepto = """REPLACE(REPLACE(REPLACE(REPLACE(
                IF(TarifaPreferente IN ('Danado', 'Normal'), 'Normal', TarifaPreferente),
                'Danado', ''), 's/co', 'Cortesia'), 'Per', 'Perdido'),
                'CDO', 'Cancelado')"""
            query = f"""SELECT
                    FLOOR(TIME_TO_SEC(TIMEDIFF(Salida, Entrada)) / {intervalo}) AS bloque,
                    {concepto} AS tarifa,
                    COUNT(*) AS boletos,
                    COALESCE(SUM(Importe), 0) AS importe,
                    COALESCE(SUM(TIME_TO_SEC(TIMEDIFF(Salida, Entrada))), 0) AS segundos,
                    COUNT(*) AS total_tiempos
                FROM Entradas {filtro}
                GROUP BY bloque, tarifa ORDER BY bloque ASC"""
            filas = self.data_base.execute_query(query)
            if filas is None:
                return None
            if not filas:
                messagebox.showinfo('Info', 'No hay registros que correspondan a la consulta establecida.')
                return None
            tarifas = sorted({str(f[1]) for f in filas if f[1] is not None})
            campos = ['Intervalo']
            for tarifa in tarifas:
                campos.extend([f'{tarifa}_Boletos', f'{tarifa}_Importe'])
            campos.extend(['Tiempo_Promedio', 'Importe_Intervalo'])
            grupos = {}
            for bloque, tarifa, cantidad, importe, segundos, total_tiempos in filas:
                if bloque is None:
                    continue
                bloque = int(bloque)
                grupo = grupos.setdefault(bloque, {'tarifas': {}, 'importe': 0,
                                                   'segundos': 0, 'cantidad': 0})
                grupo['tarifas'][str(tarifa)] = (int(cantidad), importe)
                grupo['importe'] += importe
                grupo['segundos'] += float(segundos)
                grupo['cantidad'] += int(total_tiempos)
            def formato_tiempo(segundos):
                # Mantener formato TIME de MariaDB, incluyendo duraciones mayores a 24 h.
                signo = '-' if segundos < 0 else ''
                segundos = abs(int(round(segundos)))
                horas, resto = divmod(segundos, 3600)
                minutos, segundos = divmod(resto, 60)
                return f'{signo}{horas:02d}:{minutos:02d}:{segundos:02d}'
            registros = []
            for bloque, grupo in sorted(grupos.items()):
                fila = [formato_tiempo(bloque * intervalo)]
                for tarifa in tarifas:
                    n, importe = grupo['tarifas'].get(tarifa, (0, 0))
                    fila.extend([n, importe])
                promedio = grupo['segundos'] / grupo['cantidad'] if grupo['cantidad'] else 0
                fila.extend([formato_tiempo(promedio), grupo['importe']])
                registros.append(tuple(fila))
            return registros, campos

    def hacer_consulta_sql_dias(self, parametros: list):#year_param: int, month_param: int):
        """
        Realiza una consulta SQL en la base de datos y devuelve registros junto con otros valores.

        :param year_param (int): Año para la consulta.
        :param month_param (int): Mes para la consulta.
        :return: Una tupla que contiene registros obtenidos, un parámetro y campos de la consulta.
        :raises Exception: Puede lanzar excepciones en caso de errores en la consulta o falta de registros.
        """
        # Creamos una lista vacía para agregar las cláusulas WHERE a nuestra consulta
        where = []

        # start, end = self.tools_instance.get_start_end_month(
        #     year_param, month_param)

        ############################################################################################################################
        # Si se especifica el número de corte, agregamos una cláusula WHERE a la lista
        if 'corte_numero' in parametros:
            where.append(f"CorteInc = {parametros['corte_numero']}")

        # Si se especifican tanto el inicio como el fin del rango de números de corte,
        # agregamos una cláusula WHERE entre ellos
        if 'corte_numero_inicio' in parametros and 'corte_numero_fin' in parametros:
            where.append(
                f"CorteInc BETWEEN {parametros['corte_numero_inicio']} AND {parametros['corte_numero_fin']}")

        # Si solo se especifica el número de inicio del rango de números de corte,
        # agregamos una cláusula WHERE para números de corte mayores o iguales a él
        elif 'corte_numero_inicio' in parametros:
            where.append(f"CorteInc >= {parametros['corte_numero_inicio']}")

        # Si solo se especifica el número de fin del rango de números de corte,
        # agregamos una cláusula WHERE para números de corte menores o iguales a él
        elif 'corte_numero_fin' in parametros:
            where.append(f"CorteInc <= {parametros['corte_numero_fin']}")
        ############################################################################################################################

        if where:
            where_clause = "WHERE " + " AND ".join(where)
        else:
            where_clause = ""

        if self.data_base.connection:
            concepto = """REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                IF(TarifaPreferente IN ('Danado', 'Normal'), 'Normal', TarifaPreferente),
                'Danado', ''), 's/co', 'Cortesia'), 'Per', 'Perdido'),
                'CDO', 'Cancelado'), 'PRV', 'Proveedor'), 'SNR', 'Sonora_Grill')"""
            query = f"""SELECT DATE(Entrada) AS fecha,
                    {concepto} AS tarifa, COUNT(*) AS boletos,
                    COALESCE(SUM(Importe), 0) AS importe
                    FROM Entradas {where_clause}
                    GROUP BY DATE(Entrada), tarifa
                    ORDER BY fecha"""
            filas = self.data_base.execute_query(query)
            if filas is None:
                return None
            if not filas:
                messagebox.showinfo('Info', 'No hay registros que correspondan a la consulta establecida.')
                return None
            tarifas = sorted({str(f[1]) for f in filas if f[1] is not None})
            campos = ['DIA', 'FECHA', 'EXPEDIDOS'] + tarifas + ['IMPORTE']
            grupos = {}
            for fecha, tarifa, cantidad, importe in filas:
                grupo = grupos.setdefault(fecha, {'total': 0, 'importe': 0, 'tarifas': {}})
                grupo['total'] += int(cantidad)
                grupo['importe'] += importe
                grupo['tarifas'][str(tarifa)] = int(cantidad)
            registros = []
            for fecha, grupo in sorted(grupos.items()):
                registros.append(tuple([fecha.day, fecha, grupo['total']] +
                    [grupo['tarifas'].get(t, 0) for t in tarifas] + [grupo['importe']]))
            return registros, campos

    def hacer_consulta_sql_ingresos_pensiones(self, year_param: int, month_param: int):
        """
        Realiza una consulta SQL en la base de datos y devuelve registros junto con otros valores.

        :param year_param (int): Año para la consulta.
        :param month_param (int): Mes para la consulta.
        :return: Una tupla que contiene registros obtenidos, un parámetro y campos de la consulta.
        :raises Exception: Puede lanzar excepciones en caso de errores en la consulta o falta de registros.
        """
        start, end = self.tools_instance.get_start_end_month(
            year_param, month_param)
        if self.data_base.connection:

            query = f"""SELECT Pensionados.Nom_cliente AS Nombre, Pensionados.Apell1_cliente AS Apellido_1, Pensionados.Apell2_cliente AS Apellido_2, PagosPens.num_tarjeta AS Numero_Tarjeta, PagosPens.Fecha_pago, PagosPens.Mensualidad AS Mensualidad, PagosPens.Monto FROM PagosPens JOIN Pensionados ON PagosPens.Idcliente = Pensionados.Id_cliente WHERE Pensionados.Cortesia = 'No' AND PagosPens.Fecha_pago BETWEEN '{start}' AND '{end}';"""
            registros = self.data_base.execute_query(query)

            campos = [desc[0] for desc in self.data_base.cursor.description]

            query = f"""SELECT Pensionados.Nom_cliente AS Nombre, Pensionados.Apell1_cliente AS Apellido_1, Pensionados.Apell2_cliente AS Apellido_2, PagosPens.num_tarjeta AS Numero_Tarjeta, PagosPens.Fecha_pago, PagosPens.Mensualidad AS Mensualidad, PagosPens.Monto FROM PagosPens JOIN Pensionados ON PagosPens.Idcliente = Pensionados.Id_cliente WHERE Pensionados.Cortesia = 'Si' AND PagosPens.Fecha_pago BETWEEN '{start}' AND '{end}';"""
            registros_cortesia = self.data_base.execute_query(query)

            if len(registros) == 0 and len(registros_cortesia) == 0:
                messagebox.showinfo(
                    'Info', 'No hay registros que correspondan a la consulta establecida.')
                return

            pensionados = self.pensinados_activos(year_param, month_param)

            return registros, registros_cortesia, campos, pensionados

    def pensinados_activos(self, year_param: int, month_param: int):
        """
        Realiza una consulta SQL en la base de datos y devuelve registros junto con otros valores.

        :param year_param (int): Año para la consulta.
        :param month_param (int): Mes para la consulta.
        :return: Una tupla que contiene registros obtenidos, un parámetro y campos de la consulta.
        :raises Exception: Puede lanzar excepciones en caso de errores en la consulta o falta de registros.
        """
        start, end = self.tools_instance.get_start_end_month(
            year_param, month_param)
        if self.data_base.connection:

            query = f"""SELECT Pensionados.Nom_cliente AS Nombre, Pensionados.Apell1_cliente AS Apellido_1, Pensionados.Apell2_cliente AS Apellido_2, Pensionados.num_tarjeta AS Numero_Tarjeta, Pensionados.Cortesia, COUNT(*) AS Total_Entradas FROM MovimientosPens JOIN Pensionados ON MovimientosPens.Idcliente = Pensionados.Id_cliente WHERE MovimientosPens.Entrada BETWEEN '{start}' AND '{end}' GROUP BY Pensionados.num_tarjeta;"""
            pensionados_activos = self.data_base.execute_query(query)

            query = f"""SELECT Pensionados.Nom_cliente AS Nombre, Pensionados.Apell1_cliente AS Apellido_1, Pensionados.Apell2_cliente AS Apellido_2, Pensionados.num_tarjeta AS Numero_Tarjeta, Pensionados.Cortesia, COUNT(MovimientosPens.Id_movs) AS Total_Entradas FROM Pensionados LEFT JOIN MovimientosPens ON MovimientosPens.Idcliente = Pensionados.Id_cliente AND MovimientosPens.Entrada BETWEEN '{start}' AND '{end}' WHERE MovimientosPens.Id_movs IS NULL GROUP BY Pensionados.num_tarjeta;"""
            pensionados_inactivos = self.data_base.execute_query(query)

            campos_pension = [desc[0]
                              for desc in self.data_base.cursor.description]

            return pensionados_activos, pensionados_inactivos, campos_pension

    def agregar_usuarios(self, datos: tuple) -> None:
        """
        Agrega usuarios a la base de datos.
        :param datos (tuple): Una tupla con los datos del usuario a agregar.
        """
        if self.data_base.connection:

            query = f"INSERT INTO Usuarios (Usuario, Contrasena, Nom_usuario, Fecha_alta, Telefono1, TelefonoEmer, Sucursal) VALUES {datos};"

            # Se ejecuta la consulta
            self.data_base.execute_query(query)

    def consultar_usuario(self, id: int) -> list:
        """
        Consulta información de un usuario por su ID.
        :param id (int): El ID del usuario a consultar.
        :return: Una lista con la información del usuario.
        """
        if self.data_base.connection:

            query = f"SELECT Usuario, Contrasena, Nom_usuario, Telefono1, TelefonoEmer, Sucursal FROM Usuarios WHERE Nom_usuario = {id}"

            # Se ejecuta la consulta y se obtiene el resultado.
            resultado = self.data_base.execute_query(query)

            return resultado

    def ver_usuarios(self) -> list:
        """
        Obtiene una lista de usuarios.
        :return: Una lista de usuarios.
        """
        if self.data_base.connection:

            query = f"SELECT Id_usuario, Usuario, Nom_usuario, Fecha_alta, Telefono1, TelefonoEmer, Sucursal FROM Usuarios"

            # Se ejecuta la consulta y se obtiene el resultado.
            resultado = self.data_base.execute_query(query)

            return resultado

    def eliminar_usuario(self, id: int) -> None:
        """
        Elimina un usuario por su ID.
        :param id (int): El ID del usuario a eliminar.
        """
        if self.data_base.connection:

            query = f"DELETE FROM Usuarios WHERE Id_usuario = {id}"

            # Se ejecuta la consulta
            self.data_base.execute_query(query)

    def actualizar_usuarios(self, datos: tuple, id: int) -> None:
        """
        Actualiza la información de un usuario por su ID.
        :param datos (tuple): Una tupla con los datos actualizados del usuario.
        :param id (int): El ID del usuario a actualizar.
        """
        datos = tuple(datos)

        query = f"UPDATE Usuarios SET Usuario = '{datos[0]}', Contrasena = '{datos[1]}', Nom_usuario = '{datos[2]}',  Telefono1 = '{datos[3]}', TelefonoEmer = '{datos[4]}', Sucursal = '{datos[5]}' WHERE Id_usuario = '{id}';"

        # Se ejecuta la consulta
        self.data_base.execute_query(query)

    def hacer_consulta_sql_cambios(self, year_param: int, month_param: int):
        """
        Realiza una consulta SQL en la base de datos y devuelve registros junto con otros valores.

        :param year_param (int): Año para la consulta.
        :param month_param (int): Mes para la consulta.
        :return: Una tupla que contiene registros obtenidos, un parámetro y campos de la consulta.
        :raises Exception: Puede lanzar excepciones en caso de errores en la consulta o falta de registros.
        """
        # Creamos una lista vacía para agregar las cláusulas WHERE a nuestra consulta
        start, end = self.tools_instance.get_start_end_month(
            year_param, month_param)

        if self.data_base.connection:
            query = f"""SELECT nombre AS 'Nombre', valor_anterior AS 'Valor anterior', valor_nuevo AS 'Valor nuevo', tipo_cambio AS 'Tipo de cambio', hora AS 'Fecha del cambio', nombre_usuario AS 'Usuario en turno'
                        FROM Cambios
                        WHERE hora BETWEEN '{start}' AND '{end}';"""

            registros = self.data_base.execute_query(query)

            if len(registros) == 0:
                messagebox.showinfo(
                    'Info', 'No hay registros que correspondan a la consulta establecida.')
                return

            campos = [desc[0] for desc in self.data_base.cursor.description]

            return registros, campos
