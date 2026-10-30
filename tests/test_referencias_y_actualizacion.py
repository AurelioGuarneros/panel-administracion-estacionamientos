"""Regresiones de renombrado, selector y actualización con datos ficticios."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from actualizador_respaldos import ActualizadorRespaldos
from Config.config_database import DatabaseConfig
from Controller.controller_login import ControllerLogin
from Controller.controller_select_conection import Controller_Select_Conection
from Models.estacionamientos_config import EstacionamientosConfig, ErrorValidacion
from Views.view_agregar_usuario_reportes import View_agregar_usuarios
from Views.view_modificar_usuario_reportes import View_modificar_usuarios


class ReferenciasTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        self.ruta = self.raiz / 'catalogo_ficticio.json'
        self.datos = {'settings': [
            {'name_config': 'Admin', 'database': 'db_admin'},
            {'name_config': 'Original ficticio', 'database': 'db_original',
             'email': 'original@example.invalid', 'activo': True,
             'host': 'host.invalid', 'user': 'usuario-ficticio',
             'password': 'cifrado-ficticio', 'iv': 'iv-ficticio',
             'actualizacion_automatica': True, 'configuracion_verificada': True},
            {'name_config': 'Inactivo ficticio', 'database': 'db_inactivo',
             'email': 'inactivo@example.invalid', 'activo': False},
            {'name_config': 'Excluido ficticio', 'database': 'db_test',
             'email': 'excluido@example.invalid', 'actualizacion_automatica': False},
        ]}
        self.guardar()
        self.modelo = EstacionamientosConfig(self.ruta, 'admin')
        self.actualizador = ActualizadorRespaldos.__new__(ActualizadorRespaldos)
        self.actualizador.configuracion = Mock(database_config_file=self.ruta)
        self.actualizador.archivo_estado = self.raiz / 'estado_ficticio.sqlite3'
        self.actualizador.inicializar_registro()

    def guardar(self):
        self.ruta.write_text(json.dumps(self.datos), encoding='utf-8')

    def renombrar(self, origen='Original ficticio', destino='Renombrado ficticio'):
        self.modelo.editar(origen, destino, 'original@example.invalid', 'db_original')

    def test_referencias_anteriores_resuelven_configuracion_sin_cambiar_usuarios(self):
        usuarios = self.raiz / 'usuarios_ficticios.json'
        usuarios.write_text(json.dumps({'ussers': [{'DefaultConection': 'Original ficticio',
                                                   'Password': 'clave-ficticia'}]}))
        antes = usuarios.read_bytes()
        self.renombrar()
        self.renombrar('Renombrado ficticio', 'Nombre final ficticio')
        config = DatabaseConfig.__new__(DatabaseConfig)
        config.database_config_file = self.ruta
        for nombre in ('Original ficticio', 'Renombrado ficticio', 'Nombre final ficticio'):
            r = config.obtener_db_configuracion(nombre)
            self.assertEqual(r['name_config'], 'Nombre final ficticio')
            self.assertEqual(r['database'], 'db_original')
            self.assertEqual(r['password'], 'cifrado-ficticio')
        self.assertEqual(antes, usuarios.read_bytes())

    def test_nombre_anterior_no_se_puede_reasignar(self):
        self.renombrar()
        antes = self.ruta.read_bytes()
        with self.assertRaises(ErrorValidacion):
            self.modelo.agregar(' ORIGINAL FICTICIO ', 'nuevo@example.invalid',
                                'db_nueva', 'Renombrado ficticio')
        self.assertEqual(antes, self.ruta.read_bytes())

    def test_alta_no_hereda_aliases_clave_o_verificacion(self):
        self.renombrar()
        self.modelo.agregar('Nuevo ficticio', 'nuevo@example.invalid', 'db_nueva', 'Renombrado ficticio')
        r = self.modelo.listar()[-1]
        self.assertNotIn('nombres_anteriores', r)
        self.assertNotIn('clave_respaldo', r)
        self.assertFalse(r['actualizacion_automatica'])
        self.assertFalse(r['configuracion_verificada'])
        self.assertNotIn('Nuevo ficticio', [r['nombre'] for r in self.actualizador.listar_estacionamientos()])
        self.actualizador.configuracion.obtener_email_configuracion.side_effect = AssertionError('No leer correo')
        with patch('actualizador_respaldos.imaplib.IMAP4_SSL', side_effect=AssertionError('No conectar correo')):
            with self.assertRaises(ValueError):
                self.actualizador.descargar_respaldo('Nuevo ficticio')
        self.actualizador.configuracion.obtener_email_configuracion.assert_not_called()

    def test_pendiente_no_se_habilita_solo_con_automatico_true(self):
        self.datos['settings'][1]['configuracion_verificada'] = False
        self.guardar()
        self.assertEqual(self.actualizador.listar_estacionamientos(), [])
        with patch('actualizador_respaldos.imaplib.IMAP4_SSL', side_effect=AssertionError('No conectar correo')):
            self.assertEqual(self.actualizador.consultar_respaldos_correo(), {})
        self.actualizador.configuracion.obtener_email_configuracion.assert_not_called()

    def test_editar_asociacion_invalida_verificacion_y_renombrar_la_conserva(self):
        self.renombrar()
        self.assertTrue(self.modelo.listar()[0]['configuracion_verificada'])
        self.modelo.editar('Renombrado ficticio', 'Renombrado ficticio',
                           'otro@example.invalid', 'db_otra')
        r = self.modelo.listar()[0]
        self.assertFalse(r['configuracion_verificada'])
        self.assertFalse(r['actualizacion_automatica'])

    def test_renombrado_conserva_clave_e_historial_ficticio(self):
        with self.actualizador.conectar_registro() as c:
            c.execute('INSERT INTO actualizaciones VALUES (?, ?, ?, ?)',
                      ('Original ficticio', 'respaldo-ficticio', 123.0, 'Estado ficticio'))
            antes = c.execute('SELECT * FROM actualizaciones').fetchall()
        self.renombrar()
        self.assertEqual(self.actualizador.obtener_estado('Renombrado ficticio')['ultimo_respaldo'],
                         'respaldo-ficticio')
        with self.actualizador.conectar_registro() as c:
            self.assertEqual(antes, c.execute('SELECT * FROM actualizaciones').fetchall())
        self.actualizador.registrar_comprobacion('Renombrado ficticio', 'Consultado ficticio')
        with self.actualizador.conectar_registro() as c:
            filas = c.execute('SELECT estacionamiento, ultimo_respaldo FROM actualizaciones').fetchall()
        self.assertEqual(filas, [('Original ficticio', 'respaldo-ficticio')])

    def test_selector_y_selectores_de_usuarios_mantienen_pares(self):
        self.renombrar()
        controlador = Controller_Select_Conection('admin', self.ruta)
        esperado = (['db_original'], ['Renombrado ficticio'])
        self.assertEqual(controlador.get_db_list(), esperado)
        for clase in (View_agregar_usuarios, View_modificar_usuarios):
            vista = clase.__new__(clase)
            vista.database_config_file = self.ruta
            self.assertEqual(vista.get_db_list(), esperado)
            self.assertEqual(vista.nombres_actuales['Original ficticio'], 'Renombrado ficticio')
        with patch('Controller.controller_select_conection.View_Report') as reporte, patch('builtins.print'):
            controlador.conectar('Renombrado ficticio', 'Usuario ficticio', {})
            self.assertEqual(reporte.call_args.kwargs['estacionamiento'], 'Renombrado ficticio')

    def test_usuario_normal_con_referencia_antigua_abre_nombre_actual(self):
        self.renombrar()
        usuario = {'UserName': 'usuario-ficticio', 'Name': 'Usuario ficticio',
                   'Password': 'clave-ficticia', 'Permits': 'normal',
                   'DefaultConection': 'Original ficticio', 'Reportes': {}}
        antes = copy.deepcopy(usuario)
        login = ControllerLogin.__new__(ControllerLogin)
        login.user, login.password = usuario['UserName'], usuario['Password']
        login.tools_instance = Mock()
        login.tools_instance.read_path_config_file.return_value = self.ruta
        with patch('Controller.controller_login.View_Report') as reporte, patch('builtins.print'):
            login.comprobar_usuario(usuario)
        self.assertEqual(reporte.call_args.kwargs['estacionamiento'], 'Renombrado ficticio')
        self.assertEqual(usuario, antes)
        self.modelo.cambiar_estado('Renombrado ficticio', False)
        with patch('Controller.controller_login.View_Report') as reporte, \
             patch('tkinter.messagebox.showerror') as error, patch('builtins.print'):
            login.comprobar_usuario(usuario)
        reporte.assert_not_called()
        error.assert_called_once()
