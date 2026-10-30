"""Login y apertura local con usuarios, archivos y ventanas ficticios."""
from contextlib import ExitStack
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from Controller.controller_login import ControllerLogin
from Controller.controller_select_conection import Controller_Select_Conection
from Views.view_admin_estacionamientos import ViewAdminEstacionamientos


class AdminSinMariaDBTests(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(temporal.cleanup)
        raiz = Path(temporal.name)
        self.usuarios = raiz / 'usuarios_ficticios.json'
        self.catalogo = raiz / 'conexiones_ficticias.json'
        self.usuario = {
            'UserName': 'admin_ficticio', 'Password': 'clave_ficticia',
            'Name': 'Administrador ficticio', 'Permits': 'admin',
            'DefaultConection': 'Demo', 'Reportes': {},
        }
        self.usuarios.write_text(json.dumps({'ussers': [self.usuario]}), encoding='utf-8')
        self.catalogo.write_text(json.dumps({'settings': [{
            'name_config': 'Demo', 'database': 'db_demo', 'email': 'demo@example.invalid',
            'host': 'host.invalid', 'user': 'usuario_db_ficticio',
            'password': 'clave_db_ficticia', 'iv': 'iv_ficticio',
        }]}), encoding='utf-8')
        self.pendientes = []
        self.ventana = MagicMock()
        self.ventana.after_idle.side_effect = self.pendientes.append
        self.ventana.mainloop.side_effect = lambda: [accion() for accion in self.pendientes]

    def ruta(self, instancia, tipo, clave):
        return str(self.usuarios if clave == 'user_settings_file' else self.catalogo)

    def test_login_admin_abre_catalogo_sin_conectar_servicios(self):
        from Views import view_select_conection as selector
        with ExitStack() as pila:
            pila.enter_context(patch('Tools.proyect_tools.Tools.read_path_config_file',
                                     new=lambda instancia, tipo, clave: self.ruta(instancia, tipo, clave)))
            pila.enter_context(patch('pymysql.connect', side_effect=AssertionError('No conectar MariaDB')))
            pila.enter_context(patch.object(socket.socket, 'connect', side_effect=AssertionError('No conectar red')))
            pila.enter_context(patch('Config.config_database.DatabaseConfig.create_databases',
                                     side_effect=AssertionError('No crear bases')))
            pila.enter_context(patch('Models.database.database_connection',
                                     side_effect=AssertionError('No crear conexión')))
            pila.enter_context(patch('Controller.controller_login.View_Report',
                                     side_effect=AssertionError('No abrir reportes tras login admin')))
            pila.enter_context(patch('Controller.controller_select_conection.View_Report',
                                     side_effect=AssertionError('No abrir reportes desde catálogo')))
            pila.enter_context(patch('Controller.controller_email.ReciveEmail',
                                     side_effect=AssertionError('No consultar correo')))
            pila.enter_context(patch.object(selector, 'tk', MagicMock()))
            selector.tk.Toplevel.return_value = self.ventana
            for nombre in ('ttk', 'StringVar', 'PhotoImage', 'Image', 'ImageTk'):
                pila.enter_context(patch.object(selector, nombre, MagicMock()))
            selector.StringVar.return_value.get.return_value = ''
            pila.enter_context(patch('Views.view_admin_estacionamientos.tk.Toplevel', return_value=MagicMock()))
            construir = pila.enter_context(patch.object(ViewAdminEstacionamientos, 'construir'))
            error = pila.enter_context(patch('tkinter.messagebox.showerror'))
            pila.enter_context(patch('builtins.print'))
            login = ControllerLogin()
            login.get_data('admin_ficticio', 'clave_ficticia')
            construir.assert_called_once()
            self.assertEqual(construir.call_args.args[0][0]['name_config'], 'Demo')
            self.ventana.after_idle.assert_called_once()
            error.assert_not_called()

    def test_reporte_solo_se_abre_al_solicitar_conexion(self):
        controlador = Controller_Select_Conection('admin', self.catalogo)
        with patch('Controller.controller_select_conection.View_Report') as reporte, patch('builtins.print'):
            controlador.get_db_list()
            reporte.assert_not_called()
            controlador.conectar('Demo', 'Nombre ficticio', {})
            reporte.assert_called_once_with(user_name='Nombre ficticio', estacionamiento='Demo',
                                            reportes={}, admin=True)

    def test_usuario_normal_conserva_su_acceso_original_a_reportes(self):
        self.usuario['Permits'] = 'normal'
        self.usuarios.write_text(json.dumps({'ussers': [self.usuario]}), encoding='utf-8')
        with patch('Tools.proyect_tools.Tools.read_path_config_file',
                   new=lambda instancia, tipo, clave: self.ruta(instancia, tipo, clave)), \
                patch('Controller.controller_login.View_Report') as reporte, \
                patch('Controller.controller_login.View_Conect') as selector, patch('builtins.print'):
            login = ControllerLogin()
            login.get_data('admin_ficticio', 'clave_ficticia')
            reporte.assert_called_once_with(user_name='Administrador ficticio', estacionamiento='Demo', reportes={})
            selector.assert_not_called()

    def test_usuario_normal_no_puede_abrir_administracion(self):
        controlador = Controller_Select_Conection('normal', self.catalogo)
        with self.assertRaises(PermissionError):
            controlador.abrir_administracion(None, Mock())
