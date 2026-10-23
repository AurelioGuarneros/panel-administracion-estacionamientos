"""Complemento seguro para el selector: gestión de estaciones y consulta IMAP.
No descarga ni importa SQL. Compatible con Python 3.9.
"""
import json
import os
import re
import tempfile
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from actualizador_respaldos import ActualizadorRespaldos


def instalar_mejoras(clase):
    if getattr(clase, '_mejoras_instaladas', False):
        return
    original = clase.interface

    def interfaz(self):
        original(self)
        marco = ttk.LabelFrame(self.panel_connect, text='Respaldos y administración')
        marco.grid(row=3, column=0, sticky='ew', padx=7, pady=7)
        self.estado_respaldo = tk.StringVar(value='Seleccione un estacionamiento para consultar el correo.')
        ttk.Label(marco, textvariable=self.estado_respaldo, wraplength=420).grid(
            row=0, column=0, columnspan=3, sticky='w', padx=6, pady=5)
        ttk.Button(marco, text='Actualizar ahora', command=lambda: actualizar_respaldo(self)).grid(
            row=1, column=0, padx=4, pady=5)
        ttk.Button(marco, text='Actualizar todos', command=lambda: actualizar_todos(self)).grid(
            row=1, column=1, padx=4, pady=5)
        ttk.Button(marco, text='Administrar estacionamientos', command=lambda: administrar(self)).grid(
            row=1, column=2, padx=4, pady=5)
        self.lista_desplegable_opciones.bind('<<ComboboxSelected>>', lambda _e: comprobar(self, solo=True, forzar=False))

    clase.interface = interfaz
    clase._mejoras_instaladas = True


def _config(self):
    return Path(self.db_config.database_config_file)


def _leer(self):
    return json.loads(_config(self).read_text(encoding='utf-8'))


def _guardar(self, datos):
    ruta = _config(self)
    respaldo = ruta.with_name(ruta.name + '.antes_gestion')
    if not respaldo.exists():
        respaldo.write_bytes(ruta.read_bytes())
        os.chmod(respaldo, 0o600)
    fd, tmp = tempfile.mkstemp(prefix='.estaciones_', dir=str(ruta.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, ruta)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _refrescar(self):
    self.opciones_conexiones = self.select_controller.get_db_list()[1]
    self.lista_desplegable_opciones.configure(values=self.opciones_conexiones)
    if self.variable_estacionamiento.get() not in self.opciones_conexiones:
        self.variable_estacionamiento.set(self.opciones_conexiones[0] if self.opciones_conexiones else '')


def comprobar(self, solo=True, forzar=False):
    nombre = self.variable_estacionamiento.get().strip()
    if solo and not nombre:
        messagebox.showwarning('Estacionamiento', 'Seleccione un estacionamiento.', parent=self.panel_connect)
        return
    if getattr(self, '_consulta_en_curso', False):
        return
    try:
        actualizador = ActualizadorRespaldos()
        if solo and not forzar and not actualizador.necesita_comprobacion(nombre):
            estado = actualizador.obtener_estado(nombre)
            self.estado_respaldo.set(f'{nombre}: {estado["estado"]} (consulta reciente)')
            return
    except Exception as e:
        messagebox.showerror('Configuración', str(e), parent=self.panel_connect)
        return
    self._consulta_en_curso = True
    self.estado_respaldo.set('Consultando correo en segundo plano; los reportes siguen disponibles...')

    def trabajador():
        try:
            # El método actual consulta todos los remitentes en una conexión IMAP.
            resultados = actualizador.consultar_respaldos_correo()
            nombres = [nombre] if solo else list(resultados)
            textos = []
            for n in nombres:
                info = resultados.get(n, {'estado': 'Sin resultado', 'fecha': None})
                estado = info['estado']
                if estado == 'Encontrado':
                    estado = 'Respaldo encontrado en correo; pendiente de importar'
                actualizador.registrar_comprobacion(n, estado)
                textos.append(f'{n}: {estado}' + (f' ({info["fecha"]})' if info.get('fecha') else ''))
            mensaje = ' | '.join(textos) if solo else f'Consulta completada: {len(nombres)} estacionamientos. No se importaron datos.'
        except Exception as e:
            mensaje = f'Error al consultar correo: {e}'
        def finalizar():
            self._consulta_en_curso = False
            try:
                if self.panel_connect.winfo_exists():
                    self.estado_respaldo.set(mensaje)
            except tk.TclError:
                pass
        try:
            self.panel_connect.after(0, finalizar)
        except RuntimeError:
            pass
    threading.Thread(target=trabajador, daemon=True).start()


def administrar(self):
    ventana = tk.Toplevel(self.panel_connect)
    ventana.title('Administrar estacionamientos')
    ventana.geometry('780x450')
    ventana.transient(self.panel_connect)
    tabla = ttk.Treeview(ventana, columns=('nombre','correo','base','estado'), show='headings', height=12)
    for clave, titulo, ancho in [('nombre','Estacionamiento',170),('correo','Remitente',245),('base','Base de datos',200),('estado','Estado',85)]:
        tabla.heading(clave, text=titulo)
        tabla.column(clave, width=ancho)
    tabla.pack(fill='both', expand=True, padx=8, pady=8)

    def refrescar():
        for item in tabla.get_children():
            tabla.delete(item)
        for i, item in enumerate(_leer(self)['settings']):
            if item.get('name_config') == 'Admin':
                continue
            tabla.insert('', 'end', iid=str(i), values=(item.get('name_config',''), item.get('email',''), item.get('database',''), 'Activo' if item.get('activo', True) else 'Inactivo'))
        _refrescar(self)

    def formulario(nuevo=False):
        seleccion = tabla.selection()
        if not nuevo and not seleccion:
            messagebox.showinfo('Seleccione', 'Seleccione un estacionamiento.', parent=ventana)
            return
        datos = _leer(self)
        indice = int(seleccion[0]) if not nuevo else None
        anterior = datos['settings'][indice] if indice is not None else {}
        dialogo = tk.Toplevel(ventana)
        dialogo.title('Agregar estacionamiento' if nuevo else 'Editar estacionamiento')
        dialogo.transient(ventana)
        campos = [('name_config','Nombre'),('email','Correo remitente'),('database','Base de datos')]
        entradas = {}
        for fila,(clave,titulo) in enumerate(campos):
            ttk.Label(dialogo,text=titulo).grid(row=fila,column=0,sticky='w',padx=8,pady=6)
            var=tk.StringVar(value=anterior.get(clave,''))
            ttk.Entry(dialogo,textvariable=var,width=42).grid(row=fila,column=1,padx=8,pady=6)
            entradas[clave]=var
        activo=tk.BooleanVar(value=anterior.get('activo',True))
        ttk.Checkbutton(dialogo,text='Activo',variable=activo).grid(row=3,column=1,sticky='w')

        def guardar():
            valores={clave:var.get().strip() for clave,var in entradas.items()}
            nombre, correo, base=valores['name_config'], valores['email'], valores['database']
            if not nombre or nombre.lower()=='admin' or not re.fullmatch(r'[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',correo) or not re.fullmatch(r'db_[a-z0-9_]+',base):
                messagebox.showerror('Datos inválidos','Indique nombre, correo válido y base db_nombre (minúsculas).',parent=dialogo)
                return
            for j,item in enumerate(datos['settings']):
                if j==indice:
                    continue
                if item.get('name_config','').casefold()==nombre.casefold() or item.get('database')==base:
                    messagebox.showerror('Duplicado','Ya existe ese nombre o base de datos.',parent=dialogo)
                    return
            if nuevo:
                # Heredar la conexión cifrada de un estacionamiento existente; no se generan contraseñas.
                plantilla=next((x for x in datos['settings'] if x.get('name_config')!='Admin' and all(k in x for k in ('host','user','password','iv'))),None)
                if plantilla is None:
                    messagebox.showerror('Configuración','No hay conexión existente para usar como plantilla.',parent=dialogo)
                    return
                registro={k:plantilla[k] for k in ('host','user','password','iv')}
                registro.update(valores)
                registro['activo']=activo.get()
                datos['settings'].append(registro)
            else:
                datos['settings'][indice].update(valores)
                datos['settings'][indice]['activo']=activo.get()
            try:
                _guardar(self,datos)
                refrescar()
                dialogo.destroy()
            except Exception as e:
                messagebox.showerror('No se guardó',str(e),parent=dialogo)
        ttk.Button(dialogo,text='Guardar',command=guardar).grid(row=4,column=1,sticky='e',padx=8,pady=10)
        dialogo.grab_set()

    def cambiar_estado():
        seleccion=tabla.selection()
        if not seleccion:
            return
        indice=int(seleccion[0])
        datos=_leer(self)
        item=datos['settings'][indice]
        nuevo_estado=not item.get('activo',True)
        accion='activar' if nuevo_estado else 'desactivar'
        if messagebox.askyesno('Confirmar',f'¿Desea {accion} {item["name_config"]}?\nNo se borrarán datos.',parent=ventana):
            item['activo']=nuevo_estado
            _guardar(self,datos)
            refrescar()

    botones=ttk.Frame(ventana)
    botones.pack(pady=5)
    ttk.Button(botones,text='Agregar',command=lambda:formulario(True)).pack(side='left',padx=5)
    ttk.Button(botones,text='Editar',command=lambda:formulario(False)).pack(side='left',padx=5)
    ttk.Button(botones,text='Activar / desactivar',command=cambiar_estado).pack(side='left',padx=5)
    ttk.Button(botones,text='Cerrar',command=ventana.destroy).pack(side='left',padx=5)
    refrescar()



def _procesar_estacion(actualizador, nombre):
    import configparser
    import pymysql
    estaciones = {e["nombre"]: e for e in actualizador.listar_estacionamientos()}
    base = estaciones[nombre]["database"]
    temporal = "panel_stage_" + base
    descarga = actualizador.descargar_respaldo(nombre)
    uid, archivo = str(descarga["uid"]), descarga["archivo"]
    instalada = actualizador.obtener_ultima_importacion(nombre)
    if instalada and str(instalada["uid"]) == uid:
        return f"{nombre}: UID {uid} ya instalado"
    cnf = configparser.ConfigParser()
    ruta = Path.home() / '.config/panel-estacionamientos/importador_temporal.cnf'
    if not cnf.read(ruta):
        raise RuntimeError('No existe configuración del importador')
    cfg = cnf['client']
    cn = pymysql.connect(unix_socket=cfg.get('socket','/run/mysqld/mysqld.sock'),
                         user=cfg['user'],password=cfg['password'])
    try:
        with cn.cursor() as c:
            c.execute('SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s',(temporal,))
            ocupada = c.fetchone()[0] > 0
        preparacion = actualizador.obtener_ultima_preparacion(nombre)
        if ocupada:
            if not preparacion or str(preparacion['uid']) != uid or preparacion['base_temporal'] != temporal:
                raise RuntimeError('Temporal ocupada por otro UID; no se sobrescribe')
            from activador_respaldos import verificar_integridad
            verificar_integridad(cn,temporal)
        else:
            restauracion = actualizador.restaurar_temporal(nombre,None,archivo_exacto=archivo)
            from activador_respaldos import verificar_integridad
            verificar_integridad(cn,temporal)
            actualizador.registrar_preparacion(nombre,uid,archivo,temporal)
    finally:
        cn.close()
    resultado=actualizador.activar_preparacion(nombre,uid,archivo)
    return f"{nombre}: {resultado} (UID {uid})"


def actualizar_todos(self):
    if getattr(self,'_consulta_en_curso',False):
        return
    self._consulta_en_curso=True
    self.estado_respaldo.set('Actualizando estaciones en segundo plano...')
    def trabajador():
        actualizador=ActualizadorRespaldos()
        resultados=[]
        try:
            estaciones=actualizador.listar_estacionamientos()
            for i,estacion in enumerate(estaciones,1):
                nombre=estacion['nombre']
                try:
                    linea=_procesar_estacion(actualizador,nombre)
                except Exception as e:
                    linea=f'{nombre}: ERROR {e}'
                resultados.append(linea)
                self.panel_connect.after(0,lambda n=nombre,i=i,t=len(estaciones): self.estado_respaldo.set(f'{i}/{t}: {n} procesado'))
            salida=Path.home()/'.local/share/panel-estacionamientos/resultado_actualizar_todos.txt'
            salida.write_text('\n'.join(resultados)+'\n',encoding='utf-8')
            correctas=sum(': ERROR ' not in r for r in resultados)
            mensaje=f'Finalizado: {correctas}/{len(resultados)} estaciones. Informe: {salida}'
        except Exception as e:
            mensaje=f'Error general: {e}'
        self.panel_connect.after(0,lambda: (_terminar_actualizacion(self,mensaje)))
    threading.Thread(target=trabajador,daemon=True).start()


def _terminar_actualizacion(self,mensaje):
    self._consulta_en_curso=False
    self.estado_respaldo.set(mensaje)


def actualizar_respaldo(self):
    nombre=self.variable_estacionamiento.get().strip()
    if not nombre or getattr(self,'_consulta_en_curso',False):
        return
    self._consulta_en_curso=True
    self.estado_respaldo.set(f'{nombre}: actualizando...')
    def trabajador():
        try:
            mensaje=_procesar_estacion(ActualizadorRespaldos(),nombre)
        except Exception as e:
            mensaje=f'{nombre}: ERROR {e}'
        self.panel_connect.after(0,lambda: _terminar_actualizacion(self,mensaje))
    threading.Thread(target=trabajador,daemon=True).start()
