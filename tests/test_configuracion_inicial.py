"""Instalaciones aisladas: nunca escribe configuraciones del panel local."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from Tools.preparar_configuracion import ARCHIVOS, preparar_configuracion
import test_login_rutas

RAIZ = test_login_rutas.RAIZ


class ConfiguracionInicialTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        self.carpeta = self.raiz / 'Config/config_files'
        self.carpeta.mkdir(parents=True)
        shutil.copyfile(RAIZ / 'Config/catalogo_inicial.json', self.raiz / 'Config/catalogo_inicial.json')
        for nombre in ARCHIVOS:
            shutil.copyfile(RAIZ / 'Config/config_files' / (nombre + '.example'),
                            self.carpeta / (nombre + '.example'))

    def preparar(self):
        return preparar_configuracion(self.raiz, Mock(side_effect=['clave_solo_pruebas', 'clave_solo_pruebas']))

    def test_instalacion_nueva_y_login_real_del_controlador(self):
        self.assertEqual(set(self.preparar()), set(ARCHIVOS))
        datos = json.loads((self.carpeta / 'user_settings.json').read_text())
        usuario = datos['ussers'][0]
        self.assertEqual(usuario['UserName'], 'Aurelio')
        self.assertTrue(all(usuario['Reportes'].values()))
        login = test_login_rutas.LoginRutasTests()
        login.setUp()
        login.tools.read_path_config_file.side_effect = None
        login.tools.read_path_config_file.return_value = str(self.carpeta / 'user_settings.json')
        with patch('builtins.print'):
            login.clase().get_data('Aurelio', 'clave_solo_pruebas')
        login.selector.assert_called_once_with(permiso='admin', user_name='Aurelio', reportes=usuario['Reportes'])
        login.mensajes.showerror.assert_not_called()
        login.selector.reset_mock()
        login.clase().get_data('Aurelio', 'incorrecta')
        login.selector.assert_not_called()
        login.mensajes.showerror.assert_called_once()

    def test_reinstalacion_conserva_todos_los_bytes_sin_pedir_clave(self):
        for nombre in ARCHIVOS:
            (self.carpeta / nombre).write_bytes(b'contenido local sin interpretar\r\n')
        pedir = Mock(side_effect=AssertionError('No solicitar clave'))
        self.assertEqual(preparar_configuracion(self.raiz, pedir), [])
        for nombre in ARCHIVOS:
            self.assertEqual((self.carpeta / nombre).read_bytes(), b'contenido local sin interpretar\r\n')

    def test_instalacion_parcial_conserva_usuarios(self):
        usuarios = b'{"ussers": [{"UserName": "existente"}]}'
        (self.carpeta / 'user_settings.json').write_bytes(usuarios)
        creados = preparar_configuracion(self.raiz, Mock(side_effect=AssertionError('No solicitar clave')))
        self.assertEqual(len(creados), 3)
        self.assertEqual((self.carpeta / 'user_settings.json').read_bytes(), usuarios)

    def test_clave_vacia_o_distinta_no_crea_archivos(self):
        for claves in [('', ''), ('uno', 'otro')]:
            with self.assertRaises(ValueError):
                preparar_configuracion(self.raiz, Mock(side_effect=claves))
            self.assertFalse(any((self.carpeta / n).exists() for n in ARCHIVOS))

    def test_invocacion_del_instalador_desde_otro_directorio(self):
        herramientas = self.raiz / 'Tools'
        herramientas.mkdir()
        for nombre in ('preparar_configuracion.py', 'catalogo_inicial.py'):
            shutil.copyfile(RAIZ / 'Tools' / nombre, herramientas / nombre)
        usuarios = b'{"ussers": []}'
        (self.carpeta / 'user_settings.json').write_bytes(usuarios)
        proceso = subprocess.run(
            [sys.executable, '-B', str(herramientas / 'preparar_configuracion.py')],
            cwd=self.raiz.parent, input='', capture_output=True, text=True, timeout=10)
        self.assertEqual(proceso.returncode, 0, proceso.stdout + proceso.stderr)
        self.assertTrue(all((self.carpeta / n).is_file() for n in ARCHIVOS))
        self.assertEqual((self.carpeta / 'user_settings.json').read_bytes(), usuarios)

    def test_archivo_creado_concurrentemente_no_se_sobrescribe(self):
        def pedir(_mensaje):
            (self.carpeta / 'user_settings.json').write_text('usuarios conservados')
            return 'clave_solo_pruebas'
        preparar_configuracion(self.raiz, pedir)
        self.assertEqual((self.carpeta / 'user_settings.json').read_text(), 'usuarios conservados')
