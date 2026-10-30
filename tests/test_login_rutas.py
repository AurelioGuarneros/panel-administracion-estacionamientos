"""Localización y login originales con archivos enteramente ficticios."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, mock_open, patch

RAIZ = Path(__file__).resolve().parents[1]

def ruta_local(_self, tipo, clave):
    # Adaptación del antiguo lanzador de integración al árbol de publicación.
    recursos = {'user_settings_file': 'Config/config_files/user_settings.json',
                'database_config_file': 'Config/config_files/database_connection_configuration.json',
                'system_settings_file': 'Config/config_files/system_settings.json',
                'logo_pase': 'Public/Images/logo_pase.jpg',
                'icono_desconectar': 'Public/Images/icono_desconectar.png'}
    if clave not in recursos:
        raise ValueError("Recurso desconocido")
    return str(RAIZ / recursos[clave])


def cargar_clase(ruta, nombre, espacio):
    arbol = ast.parse((RAIZ / ruta).read_text(encoding='utf-8'))
    clase = next(n for n in arbol.body if isinstance(n, ast.ClassDef) and n.name == nombre)
    exec(compile(ast.Module(body=[clase], type_ignores=[]), ruta, 'exec'), espacio)
    return espacio[nombre]


class LoginRutasTests(unittest.TestCase):
    def setUp(self):
        self.mensajes = Mock()
        self.selector = Mock()
        self.tools = Mock()
        self.tools.read_path_config_file.side_effect = lambda tipo, clave: ruta_local(None, tipo, clave)
        self.clase = cargar_clase('Controller/controller_login.py', 'ControllerLogin', {
            'Tools': Mock(return_value=self.tools),
            'json': json,
            'tk': SimpleNamespace(messagebox=self.mensajes),
            'View_Conect': self.selector,
            'View_Report': Mock(side_effect=AssertionError('No abrir reportes')),
        })

    def test_login_original_con_usuario_ficticio_y_ruta_del_lanzador(self):
        usuario = {
            'UserName': 'usuario_ficticio', 'Password': 'clave_ficticia',
            'Name': 'Nombre ficticio', 'Permits': 'admin', 'Reportes': {},
        }
        apertura = mock_open(read_data=json.dumps({'ussers': [usuario]}))
        with patch('builtins.open', apertura), patch('builtins.print'):
            controlador = self.clase()
            controlador.get_data('usuario_ficticio', 'clave_ficticia')
        apertura.assert_called_once_with(
            str(RAIZ / 'Config/config_files/user_settings.json'), 'r', encoding='utf-8')
        self.selector.assert_called_once_with(permiso='admin', user_name='Nombre ficticio', reportes={})
        self.mensajes.showerror.assert_not_called()

    def test_archivo_existente_sin_usuario_buscado_produce_rechazo_original(self):
        with patch('builtins.open', mock_open(read_data='{"ussers": []}')):
            controlador = self.clase()
            controlador.get_data('usuario_ficticio', 'clave_ficticia')
        self.selector.assert_not_called()
        self.assertIn('no está registrado', self.mensajes.showerror.call_args.args[1])

    def test_resolucion_original_y_lanzador_coinciden_con_mapa_ficticio(self):
        tools = cargar_clase('Tools/proyect_tools.py', 'Tools', {'json': json})
        mapa = {'path_files': [{'config_files': [{'user_settings_file':
                                                'Config/config_files/user_settings.json'}]}]}
        with patch('builtins.open', mock_open(read_data=json.dumps(mapa))):
            relativa = tools.read_path_config_file(None, 'config_files', 'user_settings_file')
        self.assertEqual((RAIZ / relativa).resolve(),
                         Path(ruta_local(None, 'config_files', 'user_settings_file')))
