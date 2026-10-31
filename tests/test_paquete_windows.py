"""Persistencia e importación del paquete usando únicamente datos ficticios."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from Tools.entorno_windows import preparar, resolver


class PaqueteWindowsTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        self.destino = self.raiz / 'nueva'

    def archivos(self, destino):
        return {p.name: p.read_bytes() for p in (destino / 'Config/config_files').glob('*.json')}

    def test_instalacion_y_reinstalacion_sin_sobrescribir(self):
        preparar(self.destino, lambda texto: 'ficticia')
        originales = self.archivos(self.destino)
        preparar(self.destino, lambda texto: self.fail('No pedir contraseña existente'))
        self.assertEqual(originales, self.archivos(self.destino))
        catalogo = json.loads(originales['database_connection_configuration.json'])
        activos = [r for r in catalogo['settings'] if r.get('activo')]
        self.assertEqual(len(activos), 12)
        self.assertEqual(catalogo['estacionamientos_eliminados'][0]['name_config'], 'Ciudad Mendoza')

    def test_cancelar_o_clave_invalida_no_publica_configuracion(self):
        for clave in ('',):
            with self.assertRaises(ValueError):
                preparar(self.destino, lambda texto: clave)
        self.assertFalse((self.destino / 'Config/config_files').exists())
        def cancelar(texto):
            raise InterruptedError()
        with self.assertRaises(InterruptedError):
            preparar(self.destino, cancelar)
        self.assertFalse((self.destino / 'Config/config_files').exists())

    def test_importacion_conserva_originales_y_crea_respaldo(self):
        origen = self.raiz / 'anterior'
        preparar(origen, lambda texto: 'ficticia')
        originales = self.archivos(origen)
        preparar(self.destino, lambda texto: self.fail('No pedir contraseña importada'), origen)
        self.assertEqual(originales, self.archivos(origen))
        self.assertEqual(originales, {p.name: p.read_bytes() for p in (self.destino / 'configuracion-importada-original').glob('*.json')})
        self.assertEqual(originales, self.archivos(self.destino))
        with self.assertRaises(ValueError):
            preparar(self.destino, lambda texto: 'otra', origen)

    def test_importacion_invalida_no_publica(self):
        with self.assertRaises(ValueError):
            preparar(self.destino, lambda texto: 'ficticia', self.raiz / 'noexiste')
        self.assertFalse((self.destino / 'Config/config_files').exists())

    def test_rutas_no_dependen_del_directorio_actual(self):
        with patch.dict('os.environ', LOCALAPPDATA=str(self.raiz)):
            self.assertEqual(Path(resolver('config_files', 'C:/anterior/user_settings.json')),
                self.raiz / 'PanelEstacionamientos/datos/Config/config_files/user_settings.json')
            self.assertTrue(Path(resolver('images', 'Public/Images/logo_pase.jpg')).is_file())

    def test_modelo_empaquetado_permite_editar_copia_usuario(self):
        from Models.estacionamientos_config import EstacionamientosConfig
        with patch.dict('os.environ', LOCALAPPDATA=str(self.raiz)), patch('sys.frozen', True, create=True):
            from Tools.entorno_windows import datos_usuario
            preparar(datos_usuario(), lambda texto: 'ficticia')
            modelo = EstacionamientosConfig(datos_usuario() / 'Config/config_files/database_connection_configuration.json', 'admin')
            modelo.cambiar_estado('Aguascalientes 143', False)
            self.assertEqual(len(modelo.activos()), 11)
