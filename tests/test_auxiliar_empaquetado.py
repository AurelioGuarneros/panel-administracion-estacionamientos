"""Validación del auxiliar sin sudo ni conexión a MariaDB."""
import runpy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]


class AuxiliarEmpaquetadoTests(unittest.TestCase):
    def cargar(self):
        return runpy.run_path(str(RAIZ / 'deployment/trixie/panel-activar-seguro'), run_name='prueba_auxiliar')

    def test_rechaza_usuario_no_privilegiado_sin_conectar(self):
        espacio = self.cargar()
        with patch('os.geteuid', return_value=1000), patch('pymysql.connect', side_effect=AssertionError('Sin bases')):
            with self.assertRaisesRegex(RuntimeError, 'sudo'):
                espacio['main']()

    def test_rechaza_base_no_autorizada_sin_conectar(self):
        espacio = self.cargar()
        with tempfile.TemporaryDirectory() as carpeta:
            permitidas = Path(carpeta) / 'bases.txt'
            permitidas.write_text('db_permitida\n')
            espacio['main'].__globals__['ALLOWED'] = permitidas
            with patch('os.geteuid', return_value=0), patch('sys.argv', ['helper', 'db_retirada']), patch('pymysql.connect', side_effect=AssertionError('Sin bases')):
                with self.assertRaisesRegex(RuntimeError, 'no autorizada'):
                    espacio['main']()

    def test_rechaza_argumentos_sql(self):
        espacio = self.cargar()
        with patch('os.geteuid', return_value=0), patch('sys.argv', ['helper', 'db_x;DROP DATABASE x']), patch('pymysql.connect', side_effect=AssertionError('Sin bases')):
            with self.assertRaisesRegex(RuntimeError, 'Uso:'):
                espacio['main']()

    def ejecutar_simulado(self, existente=False, falla_validacion=False, duplicado=False):
        import json
        import os
        from unittest.mock import MagicMock, Mock
        espacio = self.cargar()
        with tempfile.TemporaryDirectory() as carpeta:
            raiz=Path(carpeta)
            allow=raiz/'bases.txt';allow.write_text('db_PUNTO_SANTA_ROSA_PV\n')
            cfg=raiz/'activacion.json';cfg.write_text(json.dumps({'socket':'/run/mysqld/mysqld.sock','lector':'panel_lect_0123456789ab'}))
            espacio['main'].__globals__.update(ALLOWED=allow,CONFIG=cfg)
            conexion=MagicMock();cursor=conexion.cursor.return_value.__enter__.return_value
            sha='a'*64
            if duplicado:
                filas=[('10.11.14-MariaDB',0),(1,),(sha,)]
            else:
                filas=[('10.11.14-MariaDB',0),(0,),('db_PUNTO_SANTA_ROSA_PV',) if existente else None]
                if existente: filas.extend([(1,None,None),(1,None,None)])
                filas.extend([(0,),(0,),(0,)])
            cursor.fetchone.side_effect=filas
            cuentas={'Entradas':1}
            checks=[cuentas]
            if existente: checks.append(cuentas)
            if not duplicado: checks.append(RuntimeError('No valida') if falla_validacion else cuentas)
            checker=Mock(side_effect=checks)
            recibo=Mock()
            espacio['main'].__globals__.update(check=checker,escribir_recibo=recibo)
            original_open=os.open
            descriptor=original_open(raiz/'lock',os.O_CREAT|os.O_RDWR,0o600)
            def abrir(ruta,*args,**kwargs):
                if str(ruta)=='/var/lib/panel-estacionamientos/activacion.lock': return descriptor
                return original_open(ruta,*args,**kwargs)
            original_path=Path
            def ruta_segura(valor):
                return raiz/'backups' if str(valor)=='/var/backups/panel-estacionamientos' else original_path(valor)
            error=None
            with patch('os.geteuid',return_value=0),patch('sys.argv',['helper','db_PUNTO_SANTA_ROSA_PV',sha]),patch('pymysql.connect',return_value=conexion),patch('fcntl.flock'),patch('os.open',side_effect=abrir),patch('pathlib.Path',side_effect=ruta_segura),patch('subprocess.run',return_value=Mock(returncode=0)),patch('builtins.print'):
                try: espacio['main']()
                except RuntimeError as e: error=e
            return cursor.execute.call_args_list,recibo,error

    def test_primera_activacion_atomica_con_marca_y_base_original(self):
        consultas,recibo,error=self.ejecutar_simulado()
        self.assertIsNone(error)
        renames=[c.args[0] for c in consultas if c.args[0].startswith('RENAME TABLE')]
        self.assertEqual(len(renames),1)
        self.assertIn('`panel_stage_db_PUNTO_SANTA_ROSA_PV`',renames[0])
        self.assertIn('`db_PUNTO_SANTA_ROSA_PV`.`_panel_respaldo`',renames[0])
        recibo.assert_called_once()

    def test_validacion_posterior_falla_y_restaura_base_anterior(self):
        consultas,recibo,error=self.ejecutar_simulado(existente=True,falla_validacion=True)
        self.assertIn('revertida',str(error))
        renames=[c.args[0] for c in consultas if c.args[0].startswith('RENAME TABLE')]
        self.assertEqual(len(renames),2)
        self.assertIn('panel_anterior_db_PUNTO_SANTA_ROSA_PV',renames[1])
        recibo.assert_not_called()

    def test_cierre_tras_rename_reconcilia_marca_sin_activar_otra_vez(self):
        consultas,recibo,error=self.ejecutar_simulado(duplicado=True)
        self.assertIsNone(error)
        self.assertFalse(any(c.args[0].startswith(('RENAME','DROP','CREATE')) for c in consultas))
        recibo.assert_called_once()
