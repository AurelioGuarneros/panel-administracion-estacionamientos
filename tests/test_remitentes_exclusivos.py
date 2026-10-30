"""Reglas de catálogo con archivos ficticios, sin servicios externos."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from Models.estacionamientos_config import EstacionamientosConfig, ErrorValidacion
from Views.view_admin_estacionamientos import ViewAdminEstacionamientos


class RemitentesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / 'catalogo_ficticio.json'
        self.datos = {'settings': [
            {'name_config': 'Norte ficticio', 'database': 'db_norte',
             'email': 'norte@example.invalid', 'activo': True,
             'host': 'host.invalid', 'user': 'ficticio',
             'password': 'cifrado-ficticio', 'iv': 'iv-ficticio',
             'actualizacion_automatica': False},
            {'name_config': 'Sur ficticio', 'database': 'db_sur',
             'email': 'sur@example.invalid', 'activo': False},
        ]}
        self.guardar()
        self.modelo = EstacionamientosConfig(self.ruta, 'admin')

    def guardar(self):
        self.ruta.write_text(json.dumps(self.datos), encoding='utf-8')

    def rechaza_sin_guardar(self, operacion, nombre):
        antes = self.ruta.read_bytes()
        with self.assertRaisesRegex(ErrorValidacion, nombre):
            operacion()
        self.assertEqual(antes, self.ruta.read_bytes())

    def test_alta_rechaza_remitente_activo_e_inactivo_normalizado(self):
        for correo, nombre in [(' NORTE@EXAMPLE.INVALID ', 'Norte ficticio'),
                               (' SUR@example.invalid ', 'Sur ficticio')]:
            self.rechaza_sin_guardar(lambda: self.modelo.agregar(
                'Nuevo ficticio', correo, 'db_nueva', 'Norte ficticio'), nombre)

    def test_edicion_rechaza_remitente_inactivo_y_permite_propio(self):
        self.rechaza_sin_guardar(lambda: self.modelo.editar(
            'Norte ficticio', 'Otro nombre', 'sur@example.invalid', 'db_norte'), 'Sur ficticio')
        self.modelo.editar('Norte ficticio', 'Otro nombre', 'NORTE@example.invalid',
                           'db_norte', ubicacion=' Centro ficticio ')
        r = self.modelo.listar()[0]
        self.assertEqual(r['ubicacion'], 'Centro ficticio')
        self.assertEqual(r['password'], 'cifrado-ficticio')

    def test_edicion_de_inactivo_rechaza_remitente_activo(self):
        self.rechaza_sin_guardar(lambda: self.modelo.editar(
            'Sur ficticio', 'Sur ficticio', 'norte@example.invalid', 'db_sur'), 'Norte ficticio')

    def test_duplicado_heredado_bloquea_edicion_y_reactivacion(self):
        self.datos['settings'][1]['email'] = 'NORTE@example.invalid'
        self.guardar()
        self.rechaza_sin_guardar(lambda: self.modelo.editar(
            'Norte ficticio', 'Norte ficticio', 'norte@example.invalid', 'db_norte'), 'Sur ficticio')
        self.rechaza_sin_guardar(lambda: self.modelo.cambiar_estado('Sur ficticio', True), 'Norte ficticio')
        self.modelo.cambiar_estado('Norte ficticio', False)
        self.assertEqual(len(self.modelo.listar()), 2)

    def test_alta_conserva_conexion_y_politica_sin_copiar_ubicacion(self):
        self.datos['settings'][0]['ubicacion'] = 'Ubicación de plantilla'
        self.guardar()
        self.modelo.agregar('Nuevo ficticio', 'nuevo@example.invalid', 'db_nueva',
                            'Norte ficticio', ubicacion='Nueva ubicación')
        nuevo = self.modelo.listar()[-1]
        self.assertEqual(nuevo['ubicacion'], 'Nueva ubicación')
        for campo in ('host', 'user', 'password', 'iv', 'actualizacion_automatica'):
            self.assertEqual(nuevo[campo], self.datos['settings'][0][campo])
        self.assertTrue(nuevo['activo'])

    def test_formato_y_base_duplicada(self):
        for correo, base in [('sin-arroba', 'db_nueva'),
                             ('Nombre <a@example.invalid>', 'db_nueva'),
                             ('nuevo@example.invalid', ' DB_SUR '),
                             ('nuevo@example.invalid', 'db;sql')]:
            antes = self.ruta.read_bytes()
            with self.assertRaises(ErrorValidacion):
                self.modelo.agregar('Nuevo ficticio', correo, base, 'Norte ficticio')
            self.assertEqual(antes, self.ruta.read_bytes())

    def test_error_en_interfaz_identifica_dueno_y_no_refresca(self):
        vista = ViewAdminEstacionamientos.__new__(ViewAdminEstacionamientos)
        vista.window = Mock()
        vista.on_change, vista.recargar = Mock(), Mock()
        with patch('Views.view_admin_estacionamientos.messagebox.showerror') as error:
            vista.ejecutar(lambda: self.modelo.agregar(
                'Nuevo ficticio', 'sur@example.invalid', 'db_nueva', 'Norte ficticio'))
        self.assertIn('Sur ficticio', error.call_args.args[1])
        vista.on_change.assert_not_called()
        vista.recargar.assert_not_called()

    def test_baja_reactivacion_conserva_historico_y_credenciales(self):
        antes = copy.deepcopy(self.modelo.listar())
        self.modelo.cambiar_estado('Norte ficticio', False)
        self.modelo.cambiar_estado('Norte ficticio', True)
        self.assertEqual(antes, self.modelo.listar())
