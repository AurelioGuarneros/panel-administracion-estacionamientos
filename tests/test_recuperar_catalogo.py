"""Recuperación y ampliación de autorizaciones aisladas, sin servicios reales."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, MagicMock, patch

from Tools.catalogo_inicial import recuperar_catalogo, configurar_catalogo
from Tools.recuperar_catalogo import ejecutar
from Tools.archivos_configuracion import guardar_con_respaldo
from Tools.asociaciones_recuperacion import ampliar_asociaciones, reglas_sudoers
from deployment.trixie import actualizar_autorizaciones as autorizaciones
from deployment.trixie.preparar_sistema import conceder_permisos
from test_recuperacion_respaldos import perfil_ficticio

RAIZ = Path(__file__).resolve().parents[1]


class RecuperarCatalogoTests(unittest.TestCase):
    def setUp(self):
        self.catalogo=json.loads((RAIZ/'Config/catalogo_inicial.json').read_text())
        self.plantilla=json.loads((RAIZ/'Config/config_files/database_connection_configuration.json.example').read_text())
        self.local=copy.deepcopy(self.plantilla)

    def test_ejemplo_intacto_recupera_doce_y_ciudad_retirada(self):
        antes=copy.deepcopy(self.local)
        datos,resumen=recuperar_catalogo(self.local,self.catalogo,self.plantilla)
        self.assertEqual(len(datos['settings']),13)
        self.assertEqual(len(resumen['agregados']),12)
        self.assertEqual(resumen['ejemplos_eliminados'],['db_ejemplo'])
        self.assertNotIn('db_ejemplo',[r['database'] for r in datos['settings']])
        self.assertEqual(datos['estacionamientos_eliminados'][0]['name_config'],'Ciudad Mendoza')
        self.assertTrue(all(r['activo'] for r in datos['settings'][1:]))
        self.assertEqual(self.local,antes)

    def test_administrador_y_ejemplo_personalizados_se_conservan(self):
        self.local['settings'][0].update(user='ficticio',password='clave_ficticia',iv='iv_ficticio')
        self.local['settings'][1]['password']='personalizada_ficticia'
        self.local['settings'][1]['activo']=False
        anteriores=copy.deepcopy(self.local['settings'])
        datos,resumen=recuperar_catalogo(self.local,self.catalogo,self.plantilla)
        self.assertEqual(datos['settings'][:2],anteriores)
        self.assertEqual(resumen['ejemplos_eliminados'],[])
        self.assertEqual(len(resumen['agregados']),12)

    def test_cualquier_personalizacion_impide_borrar_el_ejemplo(self):
        for campo,valor in [('ubicacion','propia'),('host','otro.invalid'),('id','propio'),('activo',False),('actualizacion_automatica',True)]:
            local=copy.deepcopy(self.local);local['settings'][1][campo]=valor
            datos,resumen=recuperar_catalogo(local,self.catalogo,self.plantilla)
            self.assertIn(local['settings'][1],datos['settings'])
            self.assertEqual(resumen['ejemplos_eliminados'],[])

    def test_inactivos_renombrados_y_retiros_locales_no_reaparecen(self):
        self.local=configurar_catalogo(self.plantilla,self.catalogo)
        original=copy.deepcopy(self.local['settings'][1])
        self.local['settings'][1].update(name_config='Renombrado ficticio',activo=False,nombres_anteriores=[original['name_config']])
        retirado=self.local['settings'].pop(2)
        self.local['estacionamientos_eliminados'].append({k:retirado[k] for k in ('id','name_config','database')})
        datos,resumen=recuperar_catalogo(self.local,self.catalogo,self.plantilla)
        self.assertEqual(datos,self.local)
        self.assertEqual(resumen['agregados'],[])
        self.assertNotIn(retirado['database'],[r['database'] for r in datos['settings']])

    def test_instalacion_nueva_ya_preparada_no_se_reescribe(self):
        local=configurar_catalogo(self.plantilla,self.catalogo)
        datos,resumen=recuperar_catalogo(local,self.catalogo,self.plantilla)
        self.assertEqual(datos,local)
        self.assertEqual(resumen['agregados'],[])

    def test_personalizados_no_se_sobrescriben_y_no_hay_duplicados(self):
        r=copy.deepcopy(self.catalogo['settings'][0]);r.update(name_config='Otro nombre',host='local.invalid',password='ficticia',activo=False)
        self.local['settings'].append(r)
        datos,resumen=recuperar_catalogo(self.local,self.catalogo,self.plantilla)
        self.assertIn(r,datos['settings'])
        self.assertEqual(len(resumen['agregados']),11)
        self.assertEqual(len({r['database'].casefold() for r in datos['settings']}),len(datos['settings']))

    def test_conflicto_de_correo_o_retirado_activo_aborta_sin_mutar_entrada(self):
        for registro in [dict(self.catalogo['settings'][0],database='db_otra',name_config='Personalizado',id='otro'),
                         {'name_config':'Ciudad Mendoza','database':'db_ciudad_mendoza','email':'ciudad@example.invalid'}]:
            local=copy.deepcopy(self.local);local['settings'].append(registro)
            antes=copy.deepcopy(local)
            with self.assertRaises(ValueError): recuperar_catalogo(local,self.catalogo,self.plantilla)
            self.assertEqual(local,antes)

    def carpeta(self,raiz):
        carpeta=raiz/'Config/config_files';carpeta.mkdir(parents=True)
        ruta=carpeta/'database_connection_configuration.json'
        ruta.write_text(json.dumps(self.local))
        (carpeta/'database_connection_configuration.json.example').write_text(json.dumps(self.plantilla))
        (raiz/'Config/catalogo_inicial.json').write_text(json.dumps(self.catalogo))
        return ruta

    def test_simulacion_no_escribe_y_aplicacion_respalda_bytes_y_es_idempotente(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz=Path(temporal);ruta=self.carpeta(raiz)
            ruta.chmod(0o640);antes=ruta.read_bytes();archivos=set(ruta.parent.iterdir())
            resumen,respaldo=ejecutar(raiz)
            self.assertEqual(len(resumen['agregados']),12);self.assertIsNone(respaldo)
            self.assertEqual(archivos,set(ruta.parent.iterdir()));self.assertEqual(ruta.read_bytes(),antes)
            resumen,respaldo=ejecutar(raiz,True)
            self.assertEqual(respaldo.read_bytes(),antes)
            self.assertEqual(respaldo.stat().st_mode & 0o777,0o600)
            self.assertEqual(ruta.stat().st_mode & 0o777,0o640)
            despues=ruta.read_bytes();archivos=set(ruta.parent.iterdir())
            resumen,respaldo=ejecutar(raiz,True)
            self.assertEqual(ruta.read_bytes(),despues);self.assertIsNone(respaldo)
            self.assertEqual(archivos,set(ruta.parent.iterdir()))

    def test_respetar_ruta_del_mapa_que_utiliza_la_interfaz(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz=Path(temporal);ruta=self.carpeta(raiz)
            otra=ruta.with_name('catalogo_personal.json');ruta.rename(otra)
            (ruta.parent/'path_files_settings.json').write_text(json.dumps({'path_files':[{'config_files':[{'database_config_file':'Config/config_files/catalogo_personal.json'}]}]}))
            ejecutar(raiz,True)
            self.assertFalse(ruta.exists())
            self.assertEqual(len(json.loads(otra.read_text())['settings']),13)

    def test_fallo_de_reemplazo_deja_original_y_respaldo(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz=Path(temporal);ruta=self.carpeta(raiz);antes=ruta.read_bytes()
            with patch('Tools.archivos_configuracion.os.replace',side_effect=OSError('fallo ficticio')):
                with self.assertRaises(OSError): ejecutar(raiz,True)
            self.assertEqual(ruta.read_bytes(),antes)
            respaldos=list(ruta.parent.glob('*.respaldo'))
            self.assertEqual(len(respaldos),1);self.assertEqual(respaldos[0].read_bytes(),antes)
            self.assertEqual(list(ruta.parent.glob('.recuperacion_*')),[])

    def test_fallo_al_respaldar_no_inicia_el_reemplazo(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz=Path(temporal);ruta=self.carpeta(raiz);antes=ruta.read_bytes()
            with patch('Tools.archivos_configuracion.os.fsync',side_effect=OSError('Fallo ficticio')),patch('Tools.archivos_configuracion.os.replace') as reemplazar:
                with self.assertRaises(OSError): ejecutar(raiz,True)
            self.assertEqual(ruta.read_bytes(),antes)
            self.assertEqual(list(ruta.parent.glob('*.respaldo')),[])
            reemplazar.assert_not_called()

    def test_edicion_concurrente_no_se_sobrescribe(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta=Path(temporal)/'datos.json';ruta.write_bytes(b'otro contenido')
            with self.assertRaises(ValueError): guardar_con_respaldo(ruta,b'nuevo',b'anterior')
            self.assertEqual(ruta.read_bytes(),b'otro contenido')

    def test_comando_sin_aplicar_no_crea_ni_cache_ni_respaldo(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz=Path(temporal);ruta=self.carpeta(raiz)
            herramientas=raiz/'Tools';herramientas.mkdir()
            for nombre in ('recuperar_catalogo.py','catalogo_inicial.py','archivos_configuracion.py'):
                (herramientas/nombre).write_bytes((RAIZ/'Tools'/nombre).read_bytes())
            antes={p.relative_to(raiz):p.read_bytes() for p in raiz.rglob('*') if p.is_file()}
            proceso=subprocess.run([sys.executable,str(herramientas/'recuperar_catalogo.py')],cwd=raiz.parent,capture_output=True,text=True,timeout=10)
            self.assertEqual(proceso.returncode,0,proceso.stdout+proceso.stderr)
            self.assertIn('12 altas',proceso.stdout)
            self.assertIn('Sin escrituras',proceso.stdout)
            self.assertEqual(antes,{p.relative_to(raiz):p.read_bytes() for p in raiz.rglob('*') if p.is_file()})


class AutorizacionesTests(unittest.TestCase):
    def setUp(self):
        self.perfil=perfil_ficticio()
        self.perfil['estaciones']=[{'name_config':'Estacionamiento de ejemplo','database':'db_ejemplo','email':'estacionamiento@example.invalid','activo':True}]
        self.catalogo=json.loads((RAIZ/'Config/catalogo_inicial.json').read_text())
        plantilla=json.loads((RAIZ/'Config/config_files/database_connection_configuration.json.example').read_text())
        self.local=configurar_catalogo(plantilla,self.catalogo)

    def test_ampliacion_preserva_imap_passwords_y_asociaciones_previas(self):
        antes=copy.deepcopy(self.perfil)
        nuevo,bases=ampliar_asociaciones(self.perfil,self.local)
        self.assertEqual(len(bases),12)
        self.assertEqual(nuevo['imap'],antes['imap']);self.assertEqual(nuevo['mariadb'],antes['mariadb'])
        self.assertEqual(nuevo['estaciones'][0],antes['estaciones'][0])
        self.assertEqual(self.perfil,antes)
        siguiente,bases=ampliar_asociaciones(nuevo,self.local)
        self.assertEqual(siguiente,nuevo);self.assertEqual(bases,[])

    def test_no_se_agregan_inactivos_ni_retirados(self):
        self.local['settings'][1]['activo']=False
        nuevo,bases=ampliar_asociaciones(self.perfil,self.local)
        self.assertEqual(len(bases),11)
        self.assertNotIn('db_ciudad_mendoza',bases)
        self.assertNotIn(self.local['settings'][1]['database'],bases)

    def test_cambio_de_remitente_o_base_no_se_resuelve_silenciosamente(self):
        registro=copy.deepcopy(self.local['settings'][1])
        for cambio in [{'email':'otro@example.invalid'},{'database':'db_otro'}]:
            self.perfil['estaciones']=[dict(registro,**cambio)]
            with self.assertRaises(ValueError): ampliar_asociaciones(self.perfil,self.local)

    def test_permisos_limitados_a_temporales_y_lectura_sin_alterar_cuentas(self):
        cursor=Mock();conceder_permisos(cursor,self.perfil,['db_PUNTO_SANTA_ROSA_PV'])
        consultas=[c.args[0] for c in cursor.execute.call_args_list]
        self.assertEqual(len(consultas),2)
        self.assertIn('`panel\\_stage\\_db\\_PUNTO\\_SANTA\\_ROSA\\_PV`.*',consultas[0])
        self.assertTrue(consultas[1].startswith('GRANT SELECT, SHOW VIEW'))
        self.assertFalse(any('*.*' in q or 'CREATE USER' in q or 'ALTER USER' in q for q in consultas))
        reglas=reglas_sudoers('jorge',['db_PUNTO_SANTA_ROSA_PV']).decode()
        self.assertIn('^db_PUNTO_SANTA_ROSA_PV [0-9a-f]{64}$',reglas)
        self.assertNotIn(' ALL\n',reglas)

    def test_simulacion_root_no_conecta_ni_escribe(self):
        plan={'agregadas':['db_nueva']}
        with patch.object(autorizaciones,'planificar',return_value=plan),patch('pymysql.connect',side_effect=AssertionError('Sin MariaDB')),patch.object(autorizaciones,'aplicar_cambios',side_effect=AssertionError('Sin escrituras')):
            self.assertEqual(autorizaciones.actualizar('jorge','perfil','catalogo'),(['db_nueva'],[]))

    def test_reversion_de_archivos_si_falla_el_perfil(self):
        with tempfile.TemporaryDirectory() as carpeta:
            raiz=Path(carpeta);archivos=[raiz/'bases',raiz/'sudoers',raiz/'perfil.json']
            for p in archivos: p.write_bytes(b'anterior');p.chmod(0o600)
            cambios=[(p,b'anterior',b'nuevo') for p in archivos]
            def guardar(ruta,despues,antes):
                if ruta==archivos[-1]: raise OSError('Fallo ficticio')
                return guardar_con_respaldo(ruta,despues,antes)
            with patch.object(autorizaciones,'guardar_con_respaldo',side_effect=guardar):
                with self.assertRaisesRegex(RuntimeError,'revirtieron'): autorizaciones.aplicar_cambios(cambios)
            self.assertTrue(all(p.read_bytes()==b'anterior' for p in archivos))

    def test_plan_compara_catalogo_perfil_y_auxiliar_sin_escrituras(self):
        with tempfile.TemporaryDirectory() as carpeta:
            raiz=Path(carpeta);perfil=raiz/'recuperacion.json';perfil.write_text(json.dumps(self.perfil));perfil.chmod(0o600)
            catalogo=raiz/'catalogo.json';catalogo.write_text(json.dumps(self.local))
            rutas={k:raiz/k for k in ('helper','bases','config','sudoers')}
            rutas['helper'].write_bytes((RAIZ/'deployment/trixie/panel-activar-seguro').read_bytes())
            rutas['bases'].write_bytes(b'db_ejemplo\n')
            rutas['config'].write_text(json.dumps({'socket':self.perfil['mariadb']['socket'],'lector':self.perfil['mariadb']['lector']['user']}))
            rutas['sudoers'].write_bytes(reglas_sudoers('jorge',['db_ejemplo']))
            cuenta=SimpleNamespace(pw_uid=12345,pw_gid=12345,pw_dir=str(raiz))
            original_stat=Path.stat
            def propietario(ruta,*args,**kwargs):
                valor=original_stat(ruta,*args,**kwargs)
                if ruta==perfil:
                    lista=list(valor);lista[4]=12345
                    return os.stat_result(lista)
                return valor
            antes={p:p.read_bytes() for p in raiz.iterdir()}
            with patch.object(autorizaciones,'RUTAS',rutas),patch('os.geteuid',return_value=0),patch('pwd.getpwnam',return_value=cuenta),patch.object(Path,'stat',propietario),patch.object(autorizaciones,'archivo_root',side_effect=lambda p:p.read_bytes()),patch('pymysql.connect',side_effect=AssertionError('Sin MariaDB')):
                plan=autorizaciones.planificar('jorge',perfil,catalogo)
                self.assertEqual(len(plan['agregadas']),12)
                self.assertEqual([p for p,_,_ in plan['cambios']],[rutas['bases'],rutas['sudoers'],perfil])
                self.assertEqual(plan['nuevo']['imap'],self.perfil['imap'])
                rutas['bases'].write_bytes(b'db_otra\n')
                with self.assertRaises(ValueError): autorizaciones.planificar('jorge',perfil,catalogo)
                rutas['bases'].write_bytes(antes[rutas['bases']])
            self.assertEqual(antes,{p:p.read_bytes() for p in raiz.iterdir()})

    def test_aplicacion_completa_usa_solo_grants_y_conserva_imap_passwords(self):
        with tempfile.TemporaryDirectory() as carpeta:
            raiz=Path(carpeta);(raiz/'.local/share/panel-estacionamientos').mkdir(parents=True)
            perfil=raiz/'recuperacion.json';perfil.write_text(json.dumps(self.perfil));perfil.chmod(0o600)
            catalogo=raiz/'catalogo.json';catalogo.write_text(json.dumps(self.local))
            bases=raiz/'bases';bases.write_bytes(b'db_ejemplo\n');bases.chmod(0o644)
            sudoers=raiz/'sudoers';sudoers.write_bytes(reglas_sudoers('jorge',['db_ejemplo']));sudoers.chmod(0o440)
            nuevo,agregadas=ampliar_asociaciones(self.perfil,self.local)
            cambios=[(bases,bases.read_bytes(),('\n'.join(['db_ejemplo']+agregadas)+'\n').encode()),
                     (sudoers,sudoers.read_bytes(),reglas_sudoers('jorge',['db_ejemplo']+agregadas)),
                     (perfil,perfil.read_bytes(),json.dumps(nuevo).encode())]
            plan={'perfil':self.perfil,'nuevo':nuevo,'agregadas':agregadas,'cambios':cambios,
                  'catalogo':catalogo,'catalogo_bytes':catalogo.read_bytes(),
                  'cuenta':SimpleNamespace(pw_dir=str(raiz),pw_uid=os.getuid(),pw_gid=os.getgid())}
            root=MagicMock();cursor=root.cursor.return_value.__enter__.return_value
            antes=perfil.read_bytes()
            with patch.object(autorizaciones,'planificar',return_value=plan),patch.object(autorizaciones,'RUTAS',{'sudoers':sudoers}),patch.object(autorizaciones,'comprobar'),patch.object(autorizaciones,'verificar_grants'),patch('pymysql.connect',side_effect=[root,Mock(),Mock()]),patch('subprocess.run',return_value=Mock(returncode=0)):
                incorporadas,respaldos=autorizaciones.actualizar('jorge',perfil,catalogo,True)
            self.assertEqual(len(incorporadas),12);self.assertEqual(len(respaldos),3)
            self.assertEqual(respaldos[-1].read_bytes(),antes)
            actual=json.loads(perfil.read_text())
            self.assertEqual(actual['imap'],self.perfil['imap']);self.assertEqual(actual['mariadb'],self.perfil['mariadb'])
            self.assertEqual(perfil.stat().st_mode & 0o777,0o600)
            self.assertEqual(sudoers.stat().st_mode & 0o777,0o440)
            consultas=[c.args[0] for c in cursor.execute.call_args_list]
            self.assertEqual(len(consultas),24)
            self.assertTrue(all(q.startswith('GRANT ') and '*.*' not in q for q in consultas))
            self.assertFalse(any('USER' in q or 'DROP DATABASE' in q for q in consultas))

    def test_grants_de_reintento_se_aceptan_solo_si_estan_en_el_plan(self):
        from deployment.trixie.preparar_sistema import verificar_grants
        cursor=Mock()
        imp=('GRANT CREATE, DROP, INSERT, SELECT, ALTER, INDEX, REFERENCES ON `{}`.* TO cuenta',)
        lect=('GRANT SELECT, SHOW VIEW ON `{}`.* TO cuenta',)
        cursor.fetchall.side_effect=[[(imp[0].format('panel_stage_db_ejemplo'),),(imp[0].format('panel_stage_db_nueva'),)],
                                    [(lect[0].format('db_ejemplo'),),(lect[0].format('db_nueva'),)]]
        verificar_grants(cursor,self.perfil,adicionales=['db_nueva'])
        cursor.fetchall.side_effect=[[(imp[0].format('panel_stage_db_ejemplo'),),(imp[0].format('panel_stage_db_no_planificada'),)]]
        with self.assertRaises(RuntimeError): verificar_grants(cursor,self.perfil,adicionales=['db_nueva'])

    def test_catalogo_y_perfil_recuperados_muestran_y_habilitan_doce(self):
        from actualizador_respaldos import ActualizadorRespaldos
        from Controller.controller_select_conection import Controller_Select_Conection
        with tempfile.TemporaryDirectory(dir=RAIZ/'tests') as carpeta:
            ruta=Path(carpeta)/'conexiones.json'
            plantilla=json.loads((RAIZ/'Config/config_files/database_connection_configuration.json.example').read_text())
            datos,_=recuperar_catalogo(plantilla,self.catalogo,plantilla)
            ruta.write_text(json.dumps(datos))
            controlador=Controller_Select_Conection('admin',ruta)
            bases,nombres=controlador.get_db_list(propagar_error=True)
            self.assertEqual(len(nombres),12)
            self.assertIn('db_PUNTO_SANTA_ROSA_PV',bases)
            self.assertNotIn('Ciudad Mendoza',nombres)
            perfil,_=ampliar_asociaciones(self.perfil,datos)
            actualizador=ActualizadorRespaldos.__new__(ActualizadorRespaldos)
            actualizador.configuracion=Mock(database_config_file=ruta);actualizador.perfil=perfil
            with patch('pymysql.connect',side_effect=AssertionError('Sin MariaDB')),patch('imaplib.IMAP4_SSL',side_effect=AssertionError('Sin correo')):
                estaciones=actualizador.listar_estacionamientos()
            self.assertEqual({r['database'] for r in estaciones},set(bases))
            self.assertEqual(len(estaciones),12)
