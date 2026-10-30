"""Catálogo distribuible y reglas de identidad, sin red ni bases reales."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from Tools.catalogo_inicial import validar_catalogo, configurar_catalogo
from Tools.preparar_configuracion import preparar_configuracion, ARCHIVOS
from Models.estacionamientos_config import EstacionamientosConfig, ErrorValidacion
from actualizador_respaldos import ActualizadorRespaldos

RAIZ = Path(__file__).resolve().parents[1]


class CatalogoInicialTests(unittest.TestCase):
    def setUp(self):
        self.catalogo = json.loads((RAIZ / 'Config/catalogo_inicial.json').read_text())
        self.plantilla = json.loads((RAIZ / 'Config/config_files/database_connection_configuration.json.example').read_text())

    def test_publico_estricto_y_retirados(self):
        validar_catalogo(self.catalogo)
        self.assertEqual(len(self.catalogo['settings']), 12)
        self.assertEqual([r['name_config'] for r in self.catalogo['estacionamientos_eliminados']], ['Ciudad Mendoza'])
        self.assertNotIn('Ciudad Mendoza', [r['name_config'] for r in self.catalogo['settings']])
        for campo in ('password', 'iv', 'host', 'user', 'ubicacion', 'privado'):
            datos = copy.deepcopy(self.catalogo)
            datos['settings'][0][campo] = 'no_distribuir'
            with self.assertRaises(ValueError):
                validar_catalogo(datos)

    def test_duplicados_aliases_y_retirados_se_rechazan(self):
        for campo in ('id', 'database', 'email', 'name_config', 'clave_respaldo'):
            datos = copy.deepcopy(self.catalogo)
            datos['settings'][0][campo] = datos['settings'][1].get(campo, datos['settings'][1]['name_config'])
            with self.assertRaises(ValueError):
                validar_catalogo(datos)
        for campo in ('id', 'database', 'name_config'):
            datos = copy.deepcopy(self.catalogo)
            datos['settings'][0][campo] = datos['estacionamientos_eliminados'][0][campo]
            with self.assertRaises(ValueError):
                validar_catalogo(datos)
        datos = copy.deepcopy(self.catalogo)
        datos['settings'][0]['nombres_anteriores'] = [datos['settings'][1]['name_config']]
        with self.assertRaises(ValueError):
            validar_catalogo(datos)

    def test_inactivo_conservado_y_actualizador_bloqueado(self):
        self.catalogo['settings'][0]['activo'] = False
        datos = configurar_catalogo(self.plantilla, self.catalogo)
        self.assertFalse(datos['settings'][1]['activo'])
        for r in datos['settings'][1:]:
            self.assertFalse(r['actualizacion_automatica'])
            self.assertFalse(r['configuracion_verificada'])
        actualizador = ActualizadorRespaldos.__new__(ActualizadorRespaldos)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'datos.json'
            ruta.write_text(json.dumps(datos))
            actualizador.configuracion = Mock(database_config_file=ruta)
            with patch('imaplib.IMAP4_SSL', side_effect=AssertionError('Sin correo')), patch('pymysql.connect', side_effect=AssertionError('Sin MariaDB')):
                self.assertEqual(actualizador.listar_estacionamientos(), [])
                self.assertEqual(actualizador.consultar_respaldos_correo(), {})

    def test_instalacion_y_reinstalacion_no_reintroducen_retirados(self):
        with tempfile.TemporaryDirectory() as carpeta:
            raiz = Path(carpeta)
            config = raiz / 'Config/config_files'
            config.mkdir(parents=True)
            (raiz / 'Config/catalogo_inicial.json').write_text(json.dumps(self.catalogo))
            for nombre in ARCHIVOS:
                (config / (nombre + '.example')).write_bytes((RAIZ / 'Config/config_files' / (nombre + '.example')).read_bytes())
            with patch('imaplib.IMAP4_SSL', side_effect=AssertionError('Sin correo')), patch('pymysql.connect', side_effect=AssertionError('Sin MariaDB')):
                preparar_configuracion(raiz, Mock(side_effect=['ficticia', 'ficticia']))
                ruta = config / 'database_connection_configuration.json'
                datos = json.loads(ruta.read_text())
                self.assertEqual(datos['settings'][1]['id'], self.catalogo['settings'][0]['id'])
                datos['estacionamientos_eliminados'].append(datos['settings'].pop(1))
                datos['settings'][1]['activo'] = False
                ruta.write_text(json.dumps(datos))
                antes = ruta.read_bytes()
                # Incluso un catálogo público inválido no se lee si ya hay uno local.
                (raiz / 'Config/catalogo_inicial.json').write_text('invalido')
                self.assertEqual(preparar_configuracion(raiz, Mock(side_effect=AssertionError('Sin clave'))), [])
                self.assertEqual(ruta.read_bytes(), antes)

    def test_modelo_conserva_ids_al_retirar_y_no_hereda_id_de_plantilla(self):
        with tempfile.TemporaryDirectory(dir=RAIZ / 'tests') as carpeta:
            ruta = Path(carpeta) / 'catalogo.json'
            ruta.write_text(json.dumps(configurar_catalogo(self.plantilla, self.catalogo)))
            modelo = EstacionamientosConfig(ruta, 'admin')
            original = modelo.listar()[0]
            modelo.agregar('Nueva ficticia', 'nueva@example.invalid', 'db_nueva', original['name_config'])
            nueva = modelo.listar()[-1]
            self.assertNotEqual(nueva['id'], original['id'])
            modelo.eliminar(original['name_config'], original['name_config'])
            retirado = json.loads(ruta.read_text())['estacionamientos_eliminados'][-1]
            self.assertEqual(retirado['id'], original['id'])
            with self.assertRaises(ErrorValidacion):
                modelo.agregar(original['name_config'], 'otra@example.invalid', 'db_otra', nueva['name_config'])
