"""Flujo del panel con JSON ficticio; sin GUI ni servicios externos."""
import errno
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from Models.estacionamientos_config import EstacionamientosConfig, ErrorValidacion
from Views.view_admin_estacionamientos import ViewAdminEstacionamientos, causa_segura
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


class TablaFicticia:
    def __init__(self):
        self.filas = {}
        self.seleccion = ()

    def selection(self):
        return self.seleccion

    def selection_set(self, iid):
        self.seleccion = (iid,)

    def get_children(self):
        return tuple(self.filas)

    def delete(self, *items):
        for item in items:
            del self.filas[item]
        self.seleccion = ()

    def insert(self, parent, position, iid, values):
        self.filas[iid] = values

    def focus(self, iid):
        pass


class FuncionalTests(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(temporal.cleanup)
        self.ruta = Path(temporal.name) / 'ficticio.json'
        self.ruta.write_text(json.dumps({'settings': [{
            'name_config': 'Demo', 'email': 'demo@example.invalid',
            'database': 'demo_db', 'host': 'host.invalid', 'user': 'ficticio',
            'password': 'SECRETO_FICTICIO', 'iv': 'iv-ficticio',
        }]}), encoding='utf-8')
        self.vista = ViewAdminEstacionamientos.__new__(ViewAdminEstacionamientos)
        self.vista.modelo = EstacionamientosConfig(self.ruta, 'admin')
        self.vista.window = Mock()
        self.vista.tabla = TablaFicticia()
        self.vista.plantilla = Mock()
        self.vista.on_change = Mock()
        self.vista.campos = {c: Mock() for c in ('name_config', 'email', 'database', 'ubicacion')}
        self.vista.recargar()
        self.vista.tabla.selection_set('0')

    def valores(self, nombre='Demo'):
        for campo, valor in zip(self.vista.campos, (nombre, 'demo@example.invalid', 'demo_db', 'Ubicación ficticia')):
            self.vista.campos[campo].get.return_value = valor

    def test_editar_estado_y_volver_a_editar_sin_perder_seleccion(self):
        self.valores('Demo editado')
        with patch('Views.view_admin_estacionamientos.messagebox') as mensajes:
            mensajes.askyesno.return_value = True
            self.vista.editar()
            self.assertEqual(self.vista.tabla.selection(), ('0',))
            self.vista.cambiar_estado()
            self.valores('Demo final')
            self.vista.editar()
            mensajes.showerror.assert_not_called()
        registro = self.vista.modelo.listar()[0]
        self.assertEqual(registro['name_config'], 'Demo final')
        self.assertFalse(registro['activo'])
        self.assertEqual(registro['password'], 'SECRETO_FICTICIO')
        self.assertEqual(self.vista.on_change.call_count, 3)

    def test_alta_y_error_de_plantilla_concreto(self):
        self.valores('Nuevo')
        self.vista.plantilla.get.return_value = ''
        with patch('Views.view_admin_estacionamientos.messagebox.showerror') as error:
            self.vista.agregar()
        self.assertIn('Selecciona una plantilla', error.call_args.args[1])
        self.assertEqual(len(self.vista.modelo.listar()), 1)
        self.vista.plantilla.get.return_value = 'Demo'
        self.vista.campos['email'].get.return_value = 'nuevo@example.invalid'
        self.vista.campos['database'].get.return_value = 'nueva_db'
        self.vista.agregar()
        self.assertEqual(len(self.vista.modelo.listar()), 2)

    def test_fallo_de_escritura_no_trunca_y_muestra_causa_sin_secretos(self):
        self.valores()
        original = self.ruta.read_bytes()
        with patch('Models.estacionamientos_config.os.replace',
                   side_effect=OSError(errno.ENOSPC, 'SECRETO_FICTICIO')), \
                patch('Views.view_admin_estacionamientos.messagebox.showerror') as error:
            self.vista.editar()
        mensaje = error.call_args.args[1]
        self.assertIn('espacio', mensaje)
        self.assertNotIn('SECRETO_FICTICIO', mensaje)
        self.assertEqual(self.ruta.read_bytes(), original)
        self.assertEqual(list(self.ruta.parent.iterdir()), [self.ruta])
        self.vista.on_change.assert_not_called()

    def test_errores_externos_no_exponen_su_texto(self):
        for error in (ValueError('SECRETO_FICTICIO'),
                      PermissionError('SECRETO_FICTICIO'),
                      OSError(errno.EIO, 'SECRETO_FICTICIO', 'SECRETO_FICTICIO'),
                      json.JSONDecodeError('SECRETO_FICTICIO', 'SECRETO_FICTICIO', 0)):
            self.assertNotIn('SECRETO_FICTICIO', causa_segura(error))
        self.assertIn('Selecciona', causa_segura(ErrorValidacion('Selecciona una plantilla.')))

    def test_lanzador_dirige_configuraciones_a_copias_locales_sin_leerlas(self):
        with patch.object(Path, 'open', side_effect=AssertionError('No leer configuraciones')):
            ruta = ruta_local(None, 'config_files', 'database_config_file')
            self.assertEqual(Path(ruta), RAIZ / 'Config/config_files/database_connection_configuration.json')
            self.assertEqual(Path(ruta_local(None, 'config_files', 'user_settings_file')),
                             RAIZ / 'Config/config_files/user_settings.json')
            with self.assertRaises(ValueError):
                ruta_local(None, 'config_files', '../original.json')
