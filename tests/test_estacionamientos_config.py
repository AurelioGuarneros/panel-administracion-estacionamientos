import json
import os
import stat
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from Models.estacionamientos_config import EstacionamientosConfig


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / 'ficticio.json'
        self.datos = {'extra': {'conservar': True}, 'settings': [
            {'name_config': 'Admin', 'database': 'reservada', 'extra': 42},
            {'name_config': 'Ejemplo', 'email': 'ficticio@example.invalid', 'database': 'db_ficticia',
             'host': 'host-ficticio.invalid', 'user': 'usuario-ficticio', 'password': 'cifrado-ficticio',
             'iv': 'iv-ficticio', 'desconocido': {'valor': [1, 2]}}]}
        self.ruta.write_text(json.dumps(self.datos), encoding="utf-8")
        self.modelo = EstacionamientosConfig(self.ruta, 'admin')

    def leer(self):
        return json.loads(self.ruta.read_text(encoding="utf-8"))

    def test_edicion_conserva_campos_y_admin(self):
        self.modelo.editar('Ejemplo', 'Nuevo', 'nuevo@example.invalid', 'db_nueva')
        actual = self.leer()
        self.assertEqual(actual['extra'], self.datos['extra'])
        self.assertEqual(actual['settings'][0], self.datos['settings'][0])
        for campo in ('host', 'user', 'password', 'iv', 'desconocido'):
            self.assertEqual(actual['settings'][1][campo], self.datos['settings'][1][campo])
        self.assertNotIn('activo', actual['settings'][1])

    def test_alta_copia_plantilla(self):
        self.modelo.agregar('Otro', 'otro@example.invalid', 'db_otro', 'Ejemplo')
        nuevo = self.leer()['settings'][2]
        for campo in ('host', 'user', 'password', 'iv', 'desconocido'):
            self.assertEqual(nuevo[campo], self.datos['settings'][1][campo])
        self.assertTrue(nuevo['activo'])

    def test_estado_ausente_y_sin_activos(self):
        self.assertEqual(len(self.modelo.activos()), 1)
        self.modelo.cambiar_estado('Ejemplo', False)
        self.assertEqual(self.modelo.activos(), [])
        self.assertEqual(len(self.modelo.listar()), 1)
        self.modelo.cambiar_estado('Ejemplo', True)
        self.assertEqual(len(self.modelo.activos()), 1)

    def test_denegar_todas_las_escrituras(self):
        for permiso in (None, 'normal', True, 'ADMIN'):
            modelo = EstacionamientosConfig(self.ruta, permiso)
            for accion in (lambda: modelo.editar('Ejemplo', 'X', 'x@example.invalid', 'db_x'),
                           lambda: modelo.agregar('X', 'x@example.invalid', 'db_x', 'Ejemplo'),
                           lambda: modelo.cambiar_estado('Ejemplo', False)):
                with self.assertRaises(PermissionError):
                    accion()
        self.assertEqual(self.leer(), self.datos)

    def test_reservado_duplicados_y_plantilla_obligatoria(self):
        for accion in (lambda: self.modelo.editar('Admin', 'X', 'x@example.invalid', 'db_x'),
                       lambda: self.modelo.cambiar_estado('Admin', False),
                       lambda: self.modelo.agregar('ejemplo', 'x@example.invalid', 'db_x', 'Ejemplo'),
                       lambda: self.modelo.agregar('X', 'x@example.invalid', 'db_x', ''),
                       lambda: self.modelo.agregar('Admin', 'x@example.invalid', 'db_x', 'Ejemplo'),
                       lambda: self.modelo.editar('Ejemplo', '', 'x@example.invalid', 'db_x')):
            with self.assertRaises(ValueError):
                accion()
        self.assertEqual(self.leer(), self.datos)

    def test_fallo_guardado_no_trunca(self):
        if os.name == 'nt':
            self.skipTest('Esta prueba simula os.replace en POSIX.')
        with patch('Models.estacionamientos_config.os.replace', side_effect=OSError):
            with self.assertRaises(OSError):
                self.modelo.cambiar_estado('Ejemplo', False)
        self.assertEqual(self.leer(), self.datos)
        self.assertEqual(list(self.ruta.parent.iterdir()), [self.ruta])

    @unittest.skipIf(os.name == 'nt', 'Permisos POSIX; Windows utiliza DACL.')
    def test_preserva_permisos_originales(self):
        for modo in (0o600, 0o640, 0o644):
            self.ruta.chmod(modo)
            self.modelo.editar('Ejemplo', 'Ejemplo', 'ficticio@example.invalid', 'db_ficticia')
            self.assertEqual(stat.S_IMODE(self.ruta.stat().st_mode), modo)

    @unittest.skipIf(os.name == 'nt', 'Permisos POSIX.')
    def test_fallo_permisos_aborta_sin_tocar_original(self):
        with patch('Models.estacionamientos_config.os.fchmod', side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                self.modelo.cambiar_estado('Ejemplo', False)
        self.assertEqual(self.leer(), self.datos)
        self.assertEqual(list(self.ruta.parent.iterdir()), [self.ruta])

    def test_utf8_con_acentos(self):
        self.modelo.editar('Ejemplo', 'Estación México', 'ficticio@example.invalid', 'db_ficticia')
        self.assertEqual(self.leer()['settings'][1]['name_config'], 'Estación México')

    def test_rechaza_ruta_externa_y_json_invalido(self):
        with self.assertRaises(ValueError):
            EstacionamientosConfig('/fuera/ficticio.json', 'admin')
        self.ruta.write_text('{', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.modelo.listar()
