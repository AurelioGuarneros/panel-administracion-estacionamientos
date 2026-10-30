"""Datos totalmente ficticios. Solo se escribe al construir las bases de prueba."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfoNotFoundError

from Models.estado_actualizaciones import EstadoActualizaciones, SIN_FECHA, PENDIENTE, error_seguro
from Models.estacionamientos_config import EstacionamientosConfig


class EstadoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sqlite = self.root / 'ficticio.sqlite3'
        self.catalogo = self.root / 'catalogo_ficticio.json'
        self.catalogo.write_text(json.dumps({'settings': [
            {'name_config': 'Admin', 'database': 'db_admin'},
            {'name_config': 'Ejemplo ficticio', 'database': 'db_ejemplo'},
            {'name_config': 'Punta Santa Rosa PV', 'database': 'db_punta'},
            {'name_config': 'Ciudad Mendoza', 'database': 'db_ciudad', 'activo': False},
        ]}))
        self.config = EstacionamientosConfig(self.catalogo, 'admin')
        self.modelo = EstadoActualizaciones(self.config, self.sqlite)
        self.check = 1792785600.0  # 23/10/2026 14:00:00, Ciudad de México; dato ficticio.
        self.carga = self.check + 3600

    def crear(self, checks=(), imports=(), comprobaciones=True, importaciones=True):
        with sqlite3.connect(self.sqlite) as c:
            if comprobaciones:
                c.execute('CREATE TABLE actualizaciones (estacionamiento TEXT PRIMARY KEY, ultimo_respaldo TEXT, ultima_comprobacion REAL, estado TEXT)')
                c.executemany('INSERT INTO actualizaciones VALUES (?, ?, ?, ?)', checks)
            if importaciones:
                c.execute('CREATE TABLE importaciones (estacionamiento TEXT PRIMARY KEY, uid_importado TEXT, fecha_importacion REAL, archivo TEXT)')
                c.executemany('INSERT INTO importaciones VALUES (?, ?, ?, ?)', imports)

    def fila(self, nombre='Ejemplo ficticio'):
        return next(r for r in self.modelo.listar()['registros'] if r['nombre'] == nombre)

    def test_importacion_real_del_registro_no_implica_actualizado(self):
        self.crear([('Ejemplo ficticio', '2026-10-23T20:00:00Z', self.check, 'Actualizado')],
                   [('Ejemplo ficticio', 'uid_ficticio', self.carga, 'ficticio.zip')])
        r = self.fila()
        self.assertEqual(r['importacion'], '23/10/2026 15:00:00')
        self.assertEqual(r['comprobacion'], '23/10/2026 14:00:00')
        self.assertEqual(r['recepcion'], SIN_FECHA)
        self.assertEqual(r['estado'], PENDIENTE)
        self.assertIn('No consultada', r['operacion'])

    def test_punta_pendiente_y_ciudad_no_aparece_aunque_tenga_historia(self):
        self.crear([('Ciudad Mendoza', None, self.check, 'Encontrado'),
                    ('Punta Santa Rosa PV', None, self.check, 'Error al consultar')],
                   [('Ciudad Mendoza', 'uid', self.carga, 'ficticio.zip')])
        registros = self.modelo.listar()['registros']
        self.assertEqual([r['nombre'] for r in registros], ['Ejemplo ficticio', 'Punta Santa Rosa PV'])
        punta = self.fila('Punta Santa Rosa PV')
        self.assertEqual(punta['estado'], PENDIENTE)
        self.assertIn('pendiente de verificación', punta['motivo'])
        self.assertNotEqual(punta['error'], 'Sin error registrado en SQLite')

    def test_solo_activos_del_catalogo_no_todos_los_del_registro(self):
        self.crear([('Desconocido ficticio', None, self.check, 'Actualizado')])
        self.assertEqual(len(self.modelo.listar()['registros']), 2)

    def test_sin_registro_no_crea_archivo_y_conserva_estacionamientos(self):
        antes = set(self.root.iterdir())
        resultado = self.modelo.listar()
        self.assertEqual(set(self.root.iterdir()), antes)
        self.assertFalse(self.sqlite.exists())
        self.assertEqual(len(resultado['registros']), 2)
        self.assertTrue(resultado['avisos'])
        self.assertEqual(self.fila()['importacion'], SIN_FECHA)

    def test_faltan_tablas_no_se_crean(self):
        self.crear(comprobaciones=False, importaciones=False)
        self.assertEqual(len(self.modelo.listar()['avisos']), 2)
        with sqlite3.connect(self.sqlite) as c:
            self.assertEqual(c.execute('SELECT name FROM sqlite_master').fetchall(), [])

    def test_tabla_de_importaciones_ausente_no_oculta_comprobacion(self):
        self.crear([('Ejemplo ficticio', None, self.check, 'Encontrado')], importaciones=False)
        self.assertNotEqual(self.fila()['comprobacion'], SIN_FECHA)
        self.assertEqual(self.fila()['importacion'], SIN_FECHA)

    def test_corrupto_no_se_repara_y_no_crashea(self):
        self.sqlite.write_bytes(b'NO ES SQLITE FICTICIO')
        antes = self.sqlite.read_bytes()
        self.assertTrue(self.modelo.listar()['avisos'])
        self.assertEqual(self.sqlite.read_bytes(), antes)

    def test_esquema_incompatible_no_se_modifica(self):
        with sqlite3.connect(self.sqlite) as c:
            c.execute('CREATE TABLE actualizaciones (otro TEXT)')
        antes = self.sqlite.read_bytes()
        self.assertTrue(self.modelo.listar()['avisos'])
        self.assertEqual(self.sqlite.read_bytes(), antes)

    def test_lectura_real_ro_sin_archivos_auxiliares_ni_cambios(self):
        self.crear([('Ejemplo ficticio', None, self.check, 'Encontrado')])
        antes = (hashlib.sha256(self.sqlite.read_bytes()).hexdigest(), self.sqlite.stat().st_mtime_ns,
                 set(self.root.iterdir()), self.catalogo.read_bytes())
        conectar = sqlite3.connect
        consultas = []
        conexiones = []
        def vigilado(ubicacion, **kwargs):
            self.assertIn('mode=ro&immutable=1', ubicacion)
            self.assertTrue(kwargs['uri'])
            c = conectar(ubicacion, **kwargs)
            c.set_trace_callback(consultas.append)
            conexiones.append(c)
            return c
        with patch('Models.estado_actualizaciones.sqlite3.connect', side_effect=vigilado):
            self.modelo.listar()
            self.modelo.listar()
        self.assertTrue(all(q.lstrip().upper().startswith('SELECT ') for q in consultas))
        self.assertEqual(antes, (hashlib.sha256(self.sqlite.read_bytes()).hexdigest(), self.sqlite.stat().st_mtime_ns,
                                 set(self.root.iterdir()), self.catalogo.read_bytes()))
        for c in conexiones:
            with self.assertRaises(sqlite3.ProgrammingError):
                c.execute('SELECT 1')

    def test_wal_pendiente_pospone_lectura_sin_modificar_archivos(self):
        self.crear()
        wal = self.sqlite.with_name(self.sqlite.name + '-wal')
        wal.write_bytes(b'WAL FICTICIO NO LEER')
        antes = (self.sqlite.read_bytes(), wal.read_bytes())
        with patch('Models.estado_actualizaciones.sqlite3.connect', side_effect=AssertionError('No abrir SQLite con WAL pendiente')):
            resultado = self.modelo.listar()
        self.assertIn('Lectura pospuesta', resultado['avisos'][0])
        self.assertEqual(antes, (self.sqlite.read_bytes(), wal.read_bytes()))

    def test_estado_error_y_redaccion_de_credenciales(self):
        secreto = 'ERROR Access denied password=SECRETO_FICTICIO user=ficticio@example.invalid'
        self.crear([('Ejemplo ficticio', None, self.check, secreto)])
        r = self.fila()
        self.assertEqual(r['estado'], 'Error')
        self.assertIn('Acceso denegado', r['error'])
        self.assertNotIn('SECRETO_FICTICIO', str(r))
        self.assertNotIn('ficticio@example.invalid', str(r))

    def test_error_anterior_a_importacion_no_borra_fecha_de_exito(self):
        self.crear([('Ejemplo ficticio', None, self.check, 'Error al consultar')],
                   [('Ejemplo ficticio', 'uid', self.carga, 'ficticio.zip')])
        r = self.fila()
        self.assertEqual(r['estado'], PENDIENTE)
        self.assertNotEqual(r['importacion'], SIN_FECHA)
        self.assertIn('Error', r['error'])

    def test_fechas_invalidas_nunca_se_sustituyen_por_hora_actual(self):
        self.crear()
        for fecha in (None, 0, -1, float('inf'), 'fecha desconocida', time.time()+100000):
            with sqlite3.connect(self.sqlite) as c:
                c.execute('DELETE FROM importaciones')
                c.execute('INSERT INTO importaciones VALUES (?, ?, ?, ?)',
                          ('Ejemplo ficticio', 'uid', fecha, 'ficticio.zip'))
            self.assertEqual(self.fila()['importacion'], SIN_FECHA)

    def test_importacion_sin_identidad_no_se_muestra_como_exitosa(self):
        self.crear(imports=[('Ejemplo ficticio', '', self.carga, 'ficticio.zip')])
        self.assertEqual(self.fila()['importacion'], SIN_FECHA)

    def test_clave_estable_y_aliases(self):
        datos = json.loads(self.catalogo.read_text())
        datos['settings'][1].update(name_config='Nombre nuevo', clave_respaldo='Nombre viejo',
                                    nombres_anteriores=['Nombre viejo'])
        self.catalogo.write_text(json.dumps(datos))
        self.crear([('Nombre viejo', None, self.check, 'Encontrado')],
                   [('Nombre viejo', 'uid', self.carga, 'ficticio.zip')])
        self.assertNotEqual(self.fila('Nombre nuevo')['importacion'], SIN_FECHA)

    def test_aliases_ambiguos_no_inventan_importacion(self):
        datos = json.loads(self.catalogo.read_text())
        datos['settings'][1]['nombres_anteriores'] = ['Nombre anterior']
        self.catalogo.write_text(json.dumps(datos))
        self.crear(imports=[('Nombre anterior', 'uid', self.carga, 'ficticio.zip'),
                            ('Ejemplo ficticio', 'otro', self.carga, 'otro.zip')])
        self.assertEqual(self.fila()['importacion'], SIN_FECHA)
        self.assertIn('ambiguas', self.fila()['motivo'])

    def test_permiso_denegado_no_revela_excepcion(self):
        self.crear()
        with patch('Models.estado_actualizaciones.sqlite3.connect', side_effect=PermissionError('SECRETO_FICTICIO')):
            r = self.modelo.listar()
        self.assertTrue(r['avisos'])
        self.assertNotIn('SECRETO_FICTICIO', str(r))

    def test_permiso_denegado_al_comprobar_archivo_conserva_activos(self):
        with patch.object(Path, 'is_file', side_effect=PermissionError('SECRETO_FICTICIO')):
            r = self.modelo.listar()
        self.assertEqual(len(r['registros']), 2)
        self.assertTrue(r['avisos'])
        self.assertNotIn('SECRETO_FICTICIO', str(r))

    def test_sin_estacionamientos_activos(self):
        self.crear()
        modelo = EstadoActualizaciones(Mock(activos=Mock(return_value=[])), self.sqlite)
        self.assertEqual(modelo.listar()['registros'], [])

    def test_error_libre_no_expone_datos_sensibles(self):
        self.assertNotIn('SECRETO_FICTICIO', error_seguro('ERROR SECRETO_FICTICIO'))
        self.assertEqual(error_seguro('Sin respaldos'), '')

    def test_cambio_concurrente_descarta_fechas_inconsistentes(self):
        self.crear([('Ejemplo ficticio', None, self.check, 'Encontrado')])
        with patch.object(self.modelo, '_wal_pendiente', side_effect=[False, True]):
            resultado = self.modelo.listar()
        self.assertIn('cambió durante', resultado['avisos'][0])
        self.assertEqual(resultado['registros'][0]['comprobacion'], SIN_FECHA)

    def test_zona_no_disponible_identifica_fechas_en_utc(self):
        self.crear([('Ejemplo ficticio', None, self.check, 'Encontrado')])
        with patch('Models.estado_actualizaciones.ZoneInfo', side_effect=ZoneInfoNotFoundError):
            modelo = EstadoActualizaciones(self.config, self.sqlite)
        resultado = modelo.listar()
        self.assertIn('UTC', resultado['zona'])
        self.assertEqual(resultado['registros'][0]['comprobacion'], '23/10/2026 20:00:00')
