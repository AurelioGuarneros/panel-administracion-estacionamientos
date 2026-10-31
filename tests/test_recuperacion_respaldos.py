"""Flujo real con IMAP/MariaDB/auxiliar simulados: nunca accede a servicios reales."""
import hashlib
import io
import json
from pathlib import Path
import queue
import tempfile
import unittest
from unittest.mock import Mock, MagicMock, patch
import zipfile
from email.message import EmailMessage

from actualizador_respaldos import ActualizadorRespaldos
from Models.sql_respaldo import TABLAS, sql_validado, validar_sentencia, sentencias
from Models.configuracion_respaldos import leer_perfil
from Tools.configurar_respaldos import configurar
from Models.estado_actualizaciones import EstadoActualizaciones
from Models.database import database_connection
from Views.view_estado_actualizaciones import ViewEstadoActualizaciones


def sql_ficticio(base='db_PUNTO_SANTA_ROSA_PV'):
    return ('-- respaldo ficticio\nCREATE DATABASE IF NOT EXISTS `'+base+'`; USE `'+base+'`;\n'
            + 'SET @saved_cs_client = @@character_set_client;\n'
            + ''.join('DROP TABLE IF EXISTS `'+t+'`; CREATE TABLE `'+t+'` (`id` int NOT NULL, `texto` varchar(80) DEFAULT NULL, PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n' for t in sorted(TABLAS-{'Cambios'}))
            + "INSERT INTO `Entradas` VALUES (1,'texto; -- no es SQL \\\' ni comando');\n")


def zip_ficticio(sql=None, nombre='respaldo.sql'):
    b = io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z: z.writestr(nombre,sql or sql_ficticio())
    return b.getvalue()


def perfil_ficticio():
    return {'version':1,'imap':{'host':'correo.example.invalid','puerto':993,'usuario':'receptor@example.invalid','password':'ficticia','carpeta':'INBOX'},
            'mariadb':{'socket':'/run/mysqld/mysqld.sock',
                       'importador':{'user':'panel_imp_0123456789ab','password':'ficticia'},
                       'lector':{'user':'panel_lect_0123456789ab','password':'ficticia'}},
            'estaciones':[{'database':'db_PUNTO_SANTA_ROSA_PV','email':'origen@example.invalid','activo':True,'name_config':'PV ficticio'}]}


class RecuperacionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.ruta = self.raiz/'catalogo.json'
        self.ruta.write_text(json.dumps({'settings':[dict(perfil_ficticio()['estaciones'][0],actualizacion_automatica=False,configuracion_verificada=False)],'estacionamientos_eliminados':[]}))
        self.servicio = ActualizadorRespaldos.__new__(ActualizadorRespaldos)
        self.servicio.configuracion = Mock(database_config_file=self.ruta)
        self.servicio.perfil = perfil_ficticio()
        self.servicio.directorio = self.raiz
        self.servicio.archivo_estado = self.raiz/'estado.sqlite3'
        self.servicio.inicializar_registro()

    def correo(self, adjuntos):
        conexion = Mock()
        conexion.select.return_value = ('OK',[b'1'])
        conexion.response.return_value = ('UIDVALIDITY',[b'90'])
        def uid(accion,*args):
            if accion == 'search': return 'OK',[b' '.join(str(u).encode() for u in adjuntos)]
            numero, que = int(args[0]),args[1]
            if que == '(RFC822.SIZE)': return 'OK',[b'1 (RFC822.SIZE 3000)']
            mensaje = EmailMessage()
            origen,contenido = adjuntos[numero]
            mensaje['From'] = origen
            mensaje['Date'] = 'Fri, 30 Oct 2026 10:00:00 -0600'
            mensaje.set_content('Ficticio')
            mensaje.add_attachment(contenido,maintype='application',subtype='zip',filename='respaldo.zip')
            return 'OK',[(b'1 (INTERNALDATE "30-Oct-2026 10:00:00 -0600" BODY[] {1}',mensaje.as_bytes())]
        conexion.uid.side_effect = uid
        return conexion

    def test_zip_mas_reciente_valido_conserva_correo_y_mayusculas(self):
        conexion = self.correo({1:('origen@example.invalid',zip_ficticio()),
                                2:('impostor@example.invalid',zip_ficticio()),
                                3:('origen@example.invalid',b'zip roto')})
        with patch('actualizador_respaldos.imaplib.IMAP4_SSL',return_value=conexion) as imap, patch('pymysql.connect',side_effect=AssertionError('No MariaDB')):
            respaldo = self.servicio.descargar_respaldo('PV ficticio')
        self.assertEqual(respaldo['uid'],'1')
        self.assertEqual(respaldo['database'],'db_PUNTO_SANTA_ROSA_PV')
        self.assertEqual(hashlib.sha256(Path(respaldo['archivo']).read_bytes()).hexdigest(),respaldo['sha256'])
        self.assertEqual(imap.call_args.args,('correo.example.invalid',993))
        self.assertEqual(imap.call_args.kwargs['timeout'],60)
        self.assertTrue(imap.call_args.kwargs['ssl_context'].check_hostname)
        conexion.select.assert_called_once_with('INBOX',readonly=True)
        self.assertFalse(any(c.args[0] in ('store','expunge','delete') for c in conexion.uid.call_args_list))
        cuerpos = [c for c in conexion.uid.call_args_list if c.args[0]=='fetch' and c.args[-1]!='(RFC822.SIZE)']
        self.assertTrue(all('BODY.PEEK[]' in c.args[-1] for c in cuerpos))
        conexion.logout.assert_called_once()
        with self.servicio.conectar_registro() as c:
            fila=c.execute('SELECT fase,archivo,sha256,recepcion FROM eventos_respaldos').fetchone()
        self.assertEqual(fila[:3],('descarga',respaldo['archivo'],respaldo['sha256']))
        self.assertIsNotNone(fila[3])

    def test_busca_mas_alla_de_veinte_y_rechaza_sql_peligroso(self):
        adjuntos={u:('origen@example.invalid',zip_ficticio('DROP DATABASE mysql;')) for u in range(2,25)}
        adjuntos[1]=('origen@example.invalid',zip_ficticio())
        with patch.object(self.servicio,'_correo',return_value=self.correo(adjuntos)):
            self.assertEqual(self.servicio.descargar_respaldo('PV ficticio')['uid'],'1')

    def test_fallo_una_estacion_no_impide_las_demas(self):
        self.servicio.listar_estacionamientos=Mock(return_value=[{'nombre':'Uno'},{'nombre':'Dos'}])
        self.servicio.actualizar_estacion=Mock(side_effect=[RuntimeError('SECRETO_FICTICIO'),{}])
        self.servicio.registrar_evento=Mock()
        resultado=self.servicio.ejecutar_todos(importar=True)
        self.assertEqual(self.servicio.actualizar_estacion.call_count,2)
        self.assertIn('Error',resultado[0][1]);self.assertNotIn('Error',resultado[1][1])
        self.assertNotIn('SECRETO_FICTICIO',str(resultado)+str(self.servicio.registrar_evento.call_args))

    def respaldo(self):
        carpeta=self.raiz/'respaldos/db_PUNTO_SANTA_ROSA_PV';carpeta.mkdir(parents=True,exist_ok=True)
        archivo=carpeta/'respaldo_uid_1_ficticio.zip';archivo.write_bytes(zip_ficticio())
        return {'uid':'1','archivo':str(archivo),'sha256':hashlib.sha256(archivo.read_bytes()).hexdigest(),'database':'db_PUNTO_SANTA_ROSA_PV'}

    def test_no_duplica_hash_ni_restaura_si_ya_activado(self):
        respaldo=self.respaldo()
        with patch.object(self.servicio,'descargar_respaldo',return_value=respaldo), patch.object(self.servicio,'recibo_activacion',return_value={'sha256':respaldo['sha256'],'fecha':1793376000.0}), patch.object(self.servicio,'restaurar_temporal') as restaurar, patch.object(self.servicio,'activar_preparacion') as activar:
            self.servicio.actualizar_estacion('PV ficticio')
            self.servicio.actualizar_estacion('PV ficticio')
        restaurar.assert_not_called();activar.assert_not_called()
        self.assertEqual(self.servicio.obtener_ultima_importacion('PV ficticio')['uid'],'1')
        self.assertEqual(self.servicio.obtener_ultima_importacion('PV ficticio')['fecha'],1793376000.0)

    def test_fallo_de_restauracion_no_activa_y_registra_error(self):
        with patch.object(self.servicio,'descargar_respaldo',return_value=self.respaldo()), patch.object(self.servicio,'recibo_activacion',return_value=None), patch.object(self.servicio,'restaurar_temporal',side_effect=RuntimeError('SECRETO_FICTICIO')), patch.object(self.servicio,'activar_preparacion') as activar:
            with self.assertRaises(RuntimeError): self.servicio.actualizar_estacion('PV ficticio')
        activar.assert_not_called()
        self.assertIsNone(self.servicio.obtener_ultima_importacion('PV ficticio'))
        with self.servicio.conectar_registro() as c:
            self.assertNotIn('SECRETO_FICTICIO',str(c.execute('SELECT * FROM eventos_respaldos').fetchall()))

    def test_importacion_temporal_usa_solo_pymysql_y_conserva_nombre(self):
        respaldo=self.respaldo()
        conexion=MagicMock();cursor=conexion.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value=(0,)
        with patch('pymysql.connect',return_value=conexion) as conectar, patch('actualizador_respaldos.verificar_integridad') as verificar, patch('subprocess.Popen',side_effect=AssertionError('No ejecutar cliente SQL')):
            self.servicio.restaurar_temporal('PV ficticio',archivo_exacto=respaldo['archivo'])
        consultas=[c.args[0] for c in cursor.execute.call_args_list]
        self.assertIn('USE `panel_stage_db_PUNTO_SANTA_ROSA_PV`',consultas)
        self.assertFalse(any(q.startswith('DROP DATABASE') for q in consultas))
        verificar.assert_called_once_with(conexion,'panel_stage_db_PUNTO_SANTA_ROSA_PV')
        self.assertFalse(conectar.call_args.kwargs['local_infile'])
        conexion.close.assert_called_once()

    def test_zip_alterado_no_abre_mariadb(self):
        respaldo=self.respaldo()
        with patch('pymysql.connect',side_effect=AssertionError('No conectar con archivo alterado')):
            with self.assertRaisesRegex(ValueError,'cambió'):
                self.servicio.restaurar_temporal('PV ficticio',archivo_exacto=respaldo['archivo'],sha256='0'*64)

    def test_temporal_ocupada_se_conserva(self):
        respaldo=self.respaldo();conexion=MagicMock()
        cursor=conexion.cursor.return_value.__enter__.return_value;cursor.fetchone.return_value=(7,)
        with patch('pymysql.connect',return_value=conexion), patch('actualizador_respaldos.verificar_integridad') as verificar:
            with self.assertRaisesRegex(RuntimeError,'ocupada'):
                self.servicio.restaurar_temporal('PV ficticio',archivo_exacto=respaldo['archivo'])
        self.assertFalse(any(c.args[0].startswith('DROP') for c in cursor.execute.call_args_list))
        verificar.assert_not_called()

    def test_activacion_no_pide_password_sistema(self):
        respaldo=self.respaldo()
        self.servicio.registrar_preparacion('PV ficticio','1',respaldo['archivo'],'panel_stage_db_PUNTO_SANTA_ROSA_PV')
        with patch('subprocess.run',return_value=Mock(returncode=0)) as ejecutar:
            self.servicio.activar_preparacion('PV ficticio','1',respaldo['archivo'],respaldo['sha256'])
        self.assertEqual(ejecutar.call_args.args[0],['sudo','-n','/usr/local/sbin/panel-activar-seguro','db_PUNTO_SANTA_ROSA_PV',respaldo['sha256']])

    def test_inactivos_retirados_y_asociacion_cambiada_no_se_descargan(self):
        datos=json.loads(self.ruta.read_text());datos['settings'][0]['activo']=False
        self.ruta.write_text(json.dumps(datos));self.assertEqual(self.servicio.listar_estacionamientos(),[])
        datos['settings'][0]['activo']=True;datos['estacionamientos_eliminados']=[{'database':'db_PUNTO_SANTA_ROSA_PV'}]
        self.ruta.write_text(json.dumps(datos));self.assertEqual(self.servicio.listar_estacionamientos(),[])
        datos['estacionamientos_eliminados']=[];datos['settings'][0]['email']='cambiado@example.invalid'
        self.ruta.write_text(json.dumps(datos));self.assertEqual(self.servicio.listar_estacionamientos(),[])

    def test_reportes_usan_lector_local_sin_reescribir_catalogo(self):
        objeto=database_connection.__new__(database_connection)
        objeto.config_db=Mock();objeto.config_db.obtener_db_configuracion.return_value=perfil_ficticio()['estaciones'][0]
        objeto.connection=None
        antes=self.ruta.read_bytes()
        with patch('Models.configuracion_respaldos.leer_perfil',return_value=perfil_ficticio()),patch('pymysql.connect',return_value=Mock()) as conectar:
            objeto.synchronize('PV ficticio')
        self.assertEqual(conectar.call_args.kwargs['database'],'db_PUNTO_SANTA_ROSA_PV')
        self.assertEqual(conectar.call_args.kwargs['user'],'panel_lect_0123456789ab')
        self.assertEqual(antes,self.ruta.read_bytes())

    def test_vista_no_llama_tk_desde_trabajador(self):
        vista=ViewEstadoActualizaciones.__new__(ViewEstadoActualizaciones)
        vista.ocupado=False;vista.tabla=Mock();vista.tabla.selection.return_value=[]
        vista.acciones=[Mock()];vista.aviso=Mock();vista.window=Mock()
        vista.modelo=Mock();vista.modelo.ruta=self.servicio.archivo_estado;vista.modelo.catalogo.ruta=self.ruta
        vista.cola=queue.Queue()
        def iniciar(*args,**kwargs):
            kwargs['target']()
            return Mock()
        with patch('threading.Thread',side_effect=iniciar), patch('actualizador_respaldos.ActualizadorRespaldos') as servicio:
            servicio.return_value.ejecutar_todos.return_value=[('PV ficticio','Disponible')]
            vista.actualizar(True,True)
        self.assertEqual(vista.cola.get_nowait(),'PV ficticio: Disponible')
        vista.window.after.assert_called_once_with(100,vista.recoger)


class SqlSeguroTests(unittest.TestCase):
    def test_rechaza_comandos_funciones_y_esquemas_ajenos(self):
        peligrosos=[r'\! touch /tmp/no', 'SOURCE /etc/passwd', 'DELIMITER $$',
                    "INSERT INTO Entradas VALUES (SLEEP(1))", "INSERT INTO Entradas SELECT * FROM mysql.user",
                    'DROP DATABASE db_demo', 'CREATE USER x', 'CREATE TRIGGER x',
                    'CREATE TABLE Entradas (`id` int) ENGINE=FEDERATED CONNECTION=\'x\'',
                    'CREATE TABLE Entradas (`id` int DEFAULT (`sys_exec`(1))) ENGINE=InnoDB',
                    'CREATE TABLE Entradas (`id` int DEFAULT sys_exec(1)) ENGINE=InnoDB',
                    'DROP TABLE mysql.user', 'USE db_otra',
                    'CREATE TABLE Entradas AS SELECT 1', 'LOAD DATA LOCAL INFILE \'x\' INTO TABLE Entradas']
        for sql in peligrosos:
            with self.subTest(sql=sql), self.assertRaises(ValueError): validar_sentencia(sql,'db_demo')

    def test_version_comments_y_cadenas_no_son_comandos(self):
        sql=b"/*!40101 SET NAMES utf8mb4 */;\nINSERT INTO Entradas VALUES (1,'; DROP DATABASE mysql;');"
        consultas=list(sentencias(io.BytesIO(sql)))
        self.assertIsNone(validar_sentencia(consultas[0],'db_demo'))
        self.assertTrue(validar_sentencia(consultas[1],'db_demo').startswith('INSERT'))

    def test_zip_traversal_multiple_y_tablas_faltantes(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta=Path(carpeta)/'respaldo.zip'
            for contenido in [zip_ficticio(nombre='../respaldo.sql'),zip_ficticio('SET NAMES utf8mb4;')]:
                ruta.write_bytes(contenido)
                with self.assertRaises(ValueError): list(sql_validado(ruta,'db_PUNTO_SANTA_ROSA_PV'))
            with zipfile.ZipFile(ruta,'w') as z:
                z.writestr('uno.sql','SELECT 1');z.writestr('dos.sql','SELECT 2')
            with self.assertRaises(ValueError): list(sql_validado(ruta,'db_demo'))

    def test_respaldo_normal_con_base_mayusculas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta=Path(carpeta)/'respaldo.zip';ruta.write_bytes(zip_ficticio())
            consultas=list(sql_validado(ruta,'db_PUNTO_SANTA_ROSA_PV'))
            self.assertTrue(any(q.startswith('CREATE TABLE `Usuarios`') for q in consultas))
            self.assertFalse(any(q.startswith(('USE','CREATE DATABASE','SET')) for q in consultas))


class PerfilTests(unittest.TestCase):
    def test_configurar_no_modifica_json_ni_sobrescribe_perfil(self):
        with tempfile.TemporaryDirectory() as carpeta:
            raiz=Path(carpeta);config=raiz/'Config/config_files';config.mkdir(parents=True)
            catalogo=config/'database_connection_configuration.json'
            catalogo.write_text(json.dumps({'settings':perfil_ficticio()['estaciones']}))
            antes=catalogo.read_bytes();destino=raiz/'privado/recuperacion.json'
            configurar(raiz,destino,entrada=Mock(side_effect=['correo.example.invalid','','receptor@example.invalid','','']),clave=Mock(return_value='ficticia'))
            self.assertEqual(antes,catalogo.read_bytes())
            import os
            if os.name != 'nt':
                self.assertEqual(destino.stat().st_mode & 0o777,0o600)
            self.assertEqual(leer_perfil(destino)['imap']['host'],'correo.example.invalid')
            datos=destino.read_bytes()
            with self.assertRaises(FileExistsError): configurar(raiz,destino)
            self.assertEqual(datos,destino.read_bytes())


@unittest.skipIf(__import__('os').name == 'nt', 'Despliegue Trixie específico de Linux (pwd/sudo).')
class PreparacionTrixieTests(unittest.TestCase):
    def cargar(self):
        import runpy
        return runpy.run_path(str(Path(__file__).resolve().parents[1]/'deployment/trixie/preparar_sistema.py'),run_name='prueba_preparacion')

    def test_detecta_version_y_mayusculas_sin_modificar_servidor(self):
        comprobar=self.cargar()['comprobar']
        cursor=Mock()
        for version,caso in [('10.11.14-MariaDB',0),('10.5.20-MariaDB',0),('10.11.14-MariaDB',1),('8.0.36',0)]:
            cursor.fetchone.return_value=(version,caso)
            if version=='10.11.14-MariaDB' and caso==0: comprobar(cursor)
            else:
                with self.assertRaises(RuntimeError): comprobar(cursor)
        self.assertTrue(all(c.args[0].startswith('SELECT') for c in cursor.execute.call_args_list))

    def test_componentes_existentes_no_se_sobrescriben(self):
        escribir=self.cargar()['escribir_exclusivo']
        with tempfile.TemporaryDirectory() as carpeta:
            ruta=Path(carpeta)/'config';ruta.write_bytes(b'configuracion previa')
            with self.assertRaises(RuntimeError): escribir(ruta,b'otra configuracion',0o600)
            self.assertEqual(ruta.read_bytes(),b'configuracion previa')

    def test_rechaza_permisos_globales_o_sobre_bases_definitivas_al_importador(self):
        verificar=self.cargar()['verificar_grants']
        cursor=Mock()
        for grants in [[('GRANT ALL PRIVILEGES ON *.* TO cuenta',)],
                       [('GRANT INSERT ON `db_PUNTO_SANTA_ROSA_PV`.* TO cuenta',)],
                       [('GRANT SELECT ON `panel_stage_db_PUNTO_SANTA_ROSA_PV`.* TO cuenta WITH GRANT OPTION',)]]:
            cursor.fetchall.return_value=grants
            with self.assertRaises(RuntimeError): verificar(cursor,perfil_ficticio())

    def test_acepta_grants_exactos_de_importador_y_lector(self):
        verificar=self.cargar()['verificar_grants']
        cursor=Mock()
        cursor.fetchall.side_effect=[[
            ('GRANT USAGE ON *.* TO cuenta',),
            ('GRANT SELECT, INSERT, CREATE, DROP, ALTER, INDEX, REFERENCES ON `panel\\_stage\\_db\\_PUNTO\\_SANTA\\_ROSA\\_PV`.* TO cuenta',)],
            [('GRANT SELECT, SHOW VIEW ON `db\\_PUNTO\\_SANTA\\_ROSA\\_PV`.* TO cuenta',)]]
        verificar(cursor,perfil_ficticio())


class EventosInterfazTests(unittest.TestCase):
    def test_estado_muestra_archivo_recepcion_y_exito_sin_datos_sensibles(self):
        with tempfile.TemporaryDirectory() as carpeta:
            raiz=Path(carpeta)
            catalogo=raiz/'catalogo.json';catalogo.write_text(json.dumps({'settings':perfil_ficticio()['estaciones']}))
            servicio=ActualizadorRespaldos.__new__(ActualizadorRespaldos)
            servicio.configuracion=Mock(database_config_file=catalogo)
            servicio.archivo_estado=raiz/'actualizaciones.sqlite3';servicio.inicializar_registro()
            respaldo={'uid':'ficticio','archivo':'/ficticio/respaldo.zip','sha256':'a'*64,'buzon':'ficticio','recepcion':1793376000.0}
            servicio.registrar_importacion('PV ficticio','ficticio',respaldo['archivo'])
            servicio.registrar_evento('PV ficticio','importacion','Importado y activado',respaldo)
            lector=EstadoActualizaciones(Mock(activos=Mock(return_value=perfil_ficticio()['estaciones'])),servicio.archivo_estado)
            datos=lector.listar()['registros'][0]
            self.assertEqual(datos['estado'],'Importado y activado')
            self.assertIn('respaldo.zip',datos['motivo'])
            self.assertNotEqual(datos['recepcion'],'Sin fecha registrada')

    def test_los_eventos_no_autorizan_estacion_retirada(self):
        with tempfile.TemporaryDirectory() as carpeta:
            modelo=EstadoActualizaciones(Mock(activos=Mock(return_value=[])),Path(carpeta)/'inexistente.sqlite3')
            self.assertEqual(modelo.listar()['registros'],[])

    def test_interfaz_omite_excepcion_privada_y_rehabilita_botones(self):
        vista=ViewEstadoActualizaciones.__new__(ViewEstadoActualizaciones)
        vista.ocupado=True;vista.window=Mock();vista.window.winfo_exists.return_value=True
        vista.acciones=[Mock()];vista.refrescar=Mock();vista.aviso=Mock();vista.escribir_detalle=Mock()
        vista.cola=queue.Queue();vista.cola.put('Resultado controlado')
        vista.recoger()
        self.assertFalse(vista.ocupado)
        vista.acciones[0].configure.assert_called_once_with(state='normal')
        vista.refrescar.assert_called_once()
