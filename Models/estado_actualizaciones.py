"""Estado local conservador. No abre correo, MariaDB ni el actualizador."""
import math
from pathlib import Path
import sqlite3
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


SIN_FECHA = 'Sin fecha registrada'
PENDIENTE = 'Pendiente de comprobar'


def error_seguro(estado):
    """No publicar errores libres: pueden contener contraseñas, usuarios o SQL."""
    if not isinstance(estado, str) or 'error' not in estado.casefold():
        return ''
    texto = estado.casefold()
    for fragmento, mensaje in (
        ('access denied', 'Acceso denegado durante la última comprobación registrada.'),
        ('autentic', 'Error de autenticación registrado.'),
        ('nombre de base no permitido', 'Nombre de base no permitido por el actualizador.'),
        ('no se encontraron correos', 'No se encontraron correos en la comprobación registrada.'),
        ('al consultar', 'Error al consultar el correo.'),
        ('conexi', 'Error de conexión registrado.'),
    ):
        if fragmento in texto:
            return mensaje
    return 'Error registrado. El texto original no se muestra porque puede contener datos sensibles.'


class EstadoActualizaciones:
    def __init__(self, catalogo, ruta_sqlite=None):
        self.catalogo = catalogo
        self.ruta = Path(ruta_sqlite) if ruta_sqlite is not None else (
            Path.home() / '.local/share/panel-estacionamientos/actualizaciones.sqlite3')
        try:
            self.zona = ZoneInfo('America/Mexico_City')
            self.nombre_zona = 'America/Mexico_City'
        except ZoneInfoNotFoundError:
            self.zona = timezone.utc
            self.nombre_zona = 'UTC (zona de Ciudad de México no disponible)'

    def _timestamp(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            return None
        if not math.isfinite(valor) or valor <= 0 or valor > time.time() + 300:
            return None
        try:
            datetime.fromtimestamp(valor, self.zona)
        except (ValueError, OverflowError, OSError):
            return None
        return valor

    def _fecha(self, valor):
        valor = self._timestamp(valor)
        return datetime.fromtimestamp(valor, self.zona).strftime('%d/%m/%Y %H:%M:%S') if valor is not None else SIN_FECHA

    def _wal_pendiente(self):
        wal = self.ruta.with_name(self.ruta.name + '-wal')
        return wal.exists() and wal.stat().st_size > 0

    def _leer_registro(self):
        conexion = None
        self.eventos = {}
        try:
            if not self.ruta.is_file():
                return {}, {}, ['No existe registro local. No se creó ningún archivo.']
            # immutable evita crear o actualizar -wal/-shm. Nunca ignorar un WAL activo.
            if self._wal_pendiente():
                return {}, {}, ['El registro se está actualizando. Lectura pospuesta; vuelve a refrescar cuando termine.']
            antes = self.ruta.stat()
            uri = self.ruta.resolve().as_uri() + '?mode=ro&immutable=1'
            conexion = sqlite3.connect(uri, uri=True, timeout=1)
            conexion.row_factory = sqlite3.Row
            permitidos = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ}
            conexion.set_authorizer(lambda accion, a, b, *_: sqlite3.SQLITE_OK
                                    if accion in permitidos or (accion == sqlite3.SQLITE_FUNCTION and b == 'max')
                                    else sqlite3.SQLITE_DENY)
            tablas = {r[0] for r in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            avisos = []
            def leer(tabla, columnas):
                if tabla not in tablas:
                    descripcion = {'actualizaciones': 'comprobaciones de correo', 'importaciones': 'importaciones registradas'}
                    avisos.append('No hay información local de ' + descripcion[tabla] + '.')
                    return {}
                # Tablas y columnas constantes; nunca ejecutar texto del catálogo o del registro.
                filas = conexion.execute('SELECT ' + columnas + ' FROM ' + tabla).fetchall()
                resultado = {}
                for fila in filas:
                    nombre = fila['estacionamiento']
                    if nombre in resultado:
                        raise ValueError('Referencias duplicadas en el registro')
                    resultado[nombre] = dict(fila)
                return resultado
            comprobaciones = leer('actualizaciones', 'estacionamiento, ultima_comprobacion, estado, ultimo_respaldo')
            importaciones = leer('importaciones', 'estacionamiento, uid_importado, fecha_importacion, archivo')
            if 'eventos_respaldos' in tablas:
                filas = conexion.execute("SELECT e.* FROM eventos_respaldos e JOIN (SELECT estacionamiento,MAX(id) AS ultimo FROM eventos_respaldos GROUP BY estacionamiento) u ON e.id=u.ultimo").fetchall()
                self.eventos = {r['estacionamiento']:dict(r) for r in filas}
            despues = self.ruta.stat()
            if self._wal_pendiente() or (antes.st_ino, antes.st_size, antes.st_mtime_ns) != (despues.st_ino, despues.st_size, despues.st_mtime_ns):
                self.eventos = {}
                return {}, {}, ['El registro cambió durante la lectura. Refresca para obtener una lectura consistente.']
            return comprobaciones, importaciones, avisos
        except (OSError, ValueError, sqlite3.Error):
            self.eventos = {}
            return {}, {}, ['No se pudo leer el registro local. Puede faltar permiso de lectura o tener un formato no compatible. No se modificó.']
        finally:
            if conexion is not None:
                conexion.close()

    @staticmethod
    def _referencia(registro, filas):
        if registro.get('clave_respaldo'):
            return filas.get(registro['clave_respaldo']), False
        claves = {registro['name_config'], *registro.get('nombres_anteriores', [])}
        coincidencias = [filas[k] for k in claves if k in filas]
        return (coincidencias[0], False) if len(coincidencias) == 1 else (None, len(coincidencias) > 1)

    def listar(self):
        activos = self.catalogo.activos()
        comprobaciones, importaciones, avisos = self._leer_registro()
        registros = []
        for estacion in activos:
            comprobacion, ambiguo_c = self._referencia(estacion, comprobaciones)
            importacion, ambiguo_i = self._referencia(estacion, importaciones)
            comprobacion = comprobacion or {}
            importacion = importacion or {}
            fecha_comprobacion = self._timestamp(comprobacion.get('ultima_comprobacion'))
            fecha_importacion = self._timestamp(importacion.get('fecha_importacion'))
            if not all(isinstance(importacion.get(c), str) and importacion[c].strip() for c in ('uid_importado', 'archivo')):
                fecha_importacion = None
            ultimo_error = error_seguro(comprobacion.get('estado'))
            estado = PENDIENTE
            motivo = 'El registro existente no acredita la recepción del último respaldo ni su coincidencia con la importación.'
            if fecha_importacion is None:
                motivo += ' No hay una importación exitosa con fecha válida registrada para este estacionamiento.'
            if ultimo_error and (fecha_importacion is None or (fecha_comprobacion is not None and fecha_comprobacion >= fecha_importacion)):
                estado = 'Error'
                motivo = 'Existe un error en la última comprobación registrada; no se ha verificado la situación actual del correo o de MariaDB.'
            if ambiguo_c or ambiguo_i:
                estado = PENDIENTE
                motivo = 'Hay referencias históricas ambiguas; solo se muestran datos que pueden atribuirse sin ambigüedad.'
            if estacion['name_config'].strip().casefold() == 'punta santa rosa pv':
                estado = PENDIENTE
                motivo = 'PUNTA SANTA ROSA PV está pendiente de verificación. Su base de datos no se ha consultado ni modificado. ' + motivo
            if avisos:
                motivo += ' Consulta los avisos del registro local.'
            evento, _ = self._referencia(estacion, getattr(self,'eventos',{}))
            recepcion = SIN_FECHA
            if evento:
                permitidos = {'ZIP y SQL validados','Ya importado; sin duplicar','Importado y activado',
                              'Error de importación; revisar temporal o auxiliar',
                              'Error de actualización; revisar configuración, correo o temporal'}
                if evento.get('estado') in permitidos:
                    estado = evento['estado']
                    ultimo_error = estado if estado.startswith('Error') else ''
                    motivo = 'Resultado registrado del flujo de recuperación: ' + estado + '. Archivo: ' + Path(evento.get('archivo','')).name
                    recepcion = self._fecha(self._timestamp(evento.get('recepcion')))
            registros.append({
                'nombre': estacion['name_config'],
                'comprobacion': self._fecha(fecha_comprobacion),
                # ultimo_respaldo no documenta procedencia ni UID de recepción en el esquema actual.
                # Una fecha suelta, la cabecera Date o el mtime de un ZIP no acreditan recepción.
                'recepcion': recepcion,
                'importacion': self._fecha(fecha_importacion),
                'estado': estado,
                'error': ultimo_error or 'Sin error registrado en SQLite',
                'operacion': 'No consultada: esta ventana no conecta a MariaDB.',
                'motivo': motivo,
            })
        return {'registros': registros, 'avisos': avisos, 'zona': self.nombre_zona}
