"""Demostración controlada: nombres solicitados con correos y conexiones ficticios."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from Models.estacionamientos_config import EstacionamientosConfig, ErrorValidacion
from Views.view_admin_estacionamientos import ViewAdminEstacionamientos


class EliminacionCatalogoTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        self.ruta = self.raiz / 'catalogo_ficticio.json'
        self.ciudad = {'name_config': 'Ciudad Mendoza', 'database': 'db_ciudad_ficticia',
                       'email': 'ciudad@example.invalid', 'host': 'host.invalid',
                       'user': 'usuario-ficticio', 'password': 'cifrado-ficticio',
                       'iv': 'iv-ficticio', 'ubicacion': 'Ubicación ficticia', 'activo': True,
                       'actualizacion_automatica': False, 'configuracion_verificada': False}
        self.punta = dict(self.ciudad, name_config='PUNTA SANTA ROSA PV',
                          email='punta@example.invalid', database='db_punta_ficticia')
        self.datos = {'settings': [{'name_config': 'Admin', 'database': 'db_admin'},
                                  self.ciudad, self.punta]}
        self.guardar()
        self.modelo = EstacionamientosConfig(self.ruta, 'admin')
        self.ajenos = {}
        for nombre in ('base_historica_ficticia.sql', 'respaldo_ficticio.zip',
                       'historico_ficticio.json', 'usuarios_ficticios.json'):
            p = self.raiz / nombre
            p.write_bytes(b'DATOS FICTICIOS A CONSERVAR')
            self.ajenos[p] = p.read_bytes()

    def guardar(self):
        self.ruta.write_text(json.dumps(self.datos), encoding='utf-8')

    def test_baja_y_reactivacion_de_ciudad_conservan_toda_configuracion(self):
        antes = copy.deepcopy(self.modelo.listar())
        self.modelo.cambiar_estado('Ciudad Mendoza', False)
        self.assertNotIn('Ciudad Mendoza', [r['name_config'] for r in self.modelo.activos()])
        self.assertIn('PUNTA SANTA ROSA PV', [r['name_config'] for r in self.modelo.activos()])
        ciudad = self.modelo.listar()[0]
        self.assertEqual(ciudad, dict(antes[0], activo=False))
        self.modelo.cambiar_estado('Ciudad Mendoza', True)
        self.assertEqual(antes, self.modelo.listar())

    def test_conflicto_heredado_no_se_elude_para_reactivar(self):
        self.ciudad['email'] = self.punta['email']
        self.guardar()
        self.modelo.cambiar_estado('Ciudad Mendoza', False)
        antes = self.ruta.read_bytes()
        with self.assertRaisesRegex(ErrorValidacion, 'PUNTA SANTA ROSA PV'):
            self.modelo.cambiar_estado('Ciudad Mendoza', True)
        self.assertEqual(antes, self.ruta.read_bytes())

    def test_eliminacion_solo_retira_del_catalogo_y_no_permite_reactivar(self):
        self.modelo.eliminar('Ciudad Mendoza', 'Ciudad Mendoza')
        self.assertEqual(self.modelo.listar(), [self.punta])
        self.assertEqual(self.modelo.activos(), [self.punta])
        with self.assertRaises(ErrorValidacion):
            self.modelo.cambiar_estado('Ciudad Mendoza', True)
        for p, datos in self.ajenos.items():
            self.assertEqual(p.read_bytes(), datos)
        retirado = json.loads(self.ruta.read_text())['estacionamientos_eliminados'][0]
        self.assertNotIn('password', retirado)
        self.assertNotIn('email', retirado)
        self.assertNotIn('host', retirado)

    def test_exige_confirmacion_exacta_y_admin(self):
        antes = self.ruta.read_bytes()
        for texto in (None, '', 'Sí', 'ciudad mendoza', ' Ciudad Mendoza '):
            with self.assertRaises(ErrorValidacion):
                self.modelo.eliminar('Ciudad Mendoza', texto)
        with self.assertRaises(PermissionError):
            EstacionamientosConfig(self.ruta, 'normal').eliminar('Ciudad Mendoza', 'Ciudad Mendoza')
        with self.assertRaises(ErrorValidacion):
            self.modelo.eliminar('Admin', 'Admin')
        self.assertEqual(antes, self.ruta.read_bytes())

    def test_identidad_eliminada_no_se_reasigna_al_historial_de_otro(self):
        self.modelo.editar('Ciudad Mendoza', 'Ciudad renombrada',
                           'ciudad@example.invalid', 'db_ciudad_ficticia')
        self.modelo.eliminar('Ciudad renombrada', 'Ciudad renombrada')
        for nombre, base in [('Ciudad renombrada', 'db_nueva'),
                             ('ciudad mendoza', 'db_nueva'),
                             ('Nuevo ficticio', 'db_ciudad_ficticia')]:
            with self.assertRaises(ErrorValidacion):
                self.modelo.agregar(nombre, 'nuevo@example.invalid', base, 'PUNTA SANTA ROSA PV')

    def test_eliminar_inactivo_y_repeticion_controlada(self):
        self.modelo.cambiar_estado('Ciudad Mendoza', False)
        self.modelo.eliminar('Ciudad Mendoza', 'Ciudad Mendoza')
        antes = self.ruta.read_bytes()
        with self.assertRaises(ErrorValidacion):
            self.modelo.eliminar('Ciudad Mendoza', 'Ciudad Mendoza')
        self.assertEqual(antes, self.ruta.read_bytes())

    def test_fallo_de_guardado_conserva_catalogo_y_referencias(self):
        antes = self.ruta.read_bytes()
        with patch.object(self.modelo, '_guardar', side_effect=OSError('Fallo ficticio')):
            with self.assertRaises(OSError):
                self.modelo.eliminar('Ciudad Mendoza', 'Ciudad Mendoza')
        self.assertEqual(antes, self.ruta.read_bytes())

    def test_interfaz_cancelar_error_y_confirmacion(self):
        vista = ViewAdminEstacionamientos.__new__(ViewAdminEstacionamientos)
        vista.window = Mock()
        vista.modelo = self.modelo
        vista.seleccionado = Mock(return_value=self.ciudad)
        vista.tabla = MagicMock()
        vista.campos = {c: Mock() for c in ('name_config', 'email', 'database', 'ubicacion')}
        vista.on_change, vista.recargar = Mock(), Mock()
        antes = self.ruta.read_bytes()
        for respuesta in (None, 'incorrecto'):
            with patch('Views.view_admin_estacionamientos.simpledialog.askstring', return_value=respuesta) as dialogo, \
                 patch('Views.view_admin_estacionamientos.messagebox.showerror'):
                vista.eliminar()
            self.assertIn('No podrá reactivarse', dialogo.call_args.args[1])
            self.assertIn('se conservarán', dialogo.call_args.args[1])
            self.assertEqual(antes, self.ruta.read_bytes())
            vista.on_change.assert_not_called()
        with patch('Views.view_admin_estacionamientos.simpledialog.askstring', return_value='Ciudad Mendoza'):
            vista.eliminar()
        vista.on_change.assert_called_once()
        vista.recargar.assert_called_once()
        self.assertEqual(self.modelo.listar(), [self.punta])
