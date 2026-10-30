"""Estado local y actualización explícita en segundo plano, solo para administradores."""
import tkinter as tk
from tkinter import ttk, messagebox
import queue
import threading


class ViewEstadoActualizaciones:
    def __init__(self, parent, modelo):
        self.modelo = modelo
        self.ocupado = False
        self.cola = queue.Queue()
        self.window = tk.Toplevel(parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cerrar)
        try:
            self.construir()
            self.refrescar()
        except Exception:
            self.window.destroy()
            raise

    def construir(self):
        self.window.title('Estado de actualización')
        ancho = min(1180, max(320, self.window.winfo_screenwidth() - 60))
        alto = min(580, max(280, self.window.winfo_screenheight() - 100))
        self.window.geometry(f'{ancho}x{alto}')
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(2, weight=1)
        self.ayuda = ttk.Label(self.window, text='La apertura solo lee el registro local. Usa los botones para consultar el correo, descargar ZIP validados e importar en MariaDB local.', wraplength=ancho-24)
        self.ayuda.grid(row=0, column=0, sticky='ew', padx=10, pady=6)
        self.aviso = ttk.Label(self.window, wraplength=ancho-24)
        self.aviso.grid(row=1, column=0, sticky='ew', padx=10, pady=3)
        marco = ttk.Frame(self.window)
        marco.grid(row=2, column=0, sticky='nsew', padx=10, pady=6)
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        columnas = ('nombre', 'comprobacion', 'recepcion', 'importacion', 'estado', 'error')
        self.tabla = ttk.Treeview(marco, columns=columnas, show='headings', selectmode='browse', height=7)
        titulos = ('Estacionamiento', 'Última comprobación de correo', 'Último respaldo recibido', 'Última importación exitosa registrada', 'Estado de actualización', 'Último error registrado')
        for campo, titulo, ancho_columna in zip(columnas, titulos, (200, 225, 190, 270, 195, 330)):
            self.tabla.heading(campo, text=titulo)
            self.tabla.column(campo, width=ancho_columna, minwidth=120, stretch=False)
        self.tabla.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(marco, orient='vertical', command=self.tabla.yview)
        horizontal = ttk.Scrollbar(marco, orient='horizontal', command=self.tabla.xview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.bind('<<TreeviewSelect>>', self.seleccionar)
        detalle_marco = ttk.Frame(self.window)
        detalle_marco.grid(row=3, column=0, sticky='ew', padx=10, pady=4)
        detalle_marco.columnconfigure(0, weight=1)
        self.detalle = tk.Text(detalle_marco, height=6, wrap='word', state='disabled',
                               font='TkDefaultFont', takefocus=True)
        self.detalle.grid(row=0, column=0, sticky='ew')
        detalle_scroll = ttk.Scrollbar(detalle_marco, orient='vertical', command=self.detalle.yview)
        detalle_scroll.grid(row=0, column=1, sticky='ns')
        self.detalle.configure(yscrollcommand=detalle_scroll.set)
        self.zona = ttk.Label(self.window, wraplength=ancho-24)
        self.zona.grid(row=4, column=0, sticky='ew', padx=10, pady=3)
        botones = ttk.Frame(self.window)
        botones.grid(row=5, column=0, sticky='ew', padx=10, pady=6)
        ttk.Button(botones, text='Refrescar registro local', command=self.refrescar).pack(side='left')
        self.acciones = []
        for texto, importar, todos in (('Consultar y descargar ZIP', False, True),
                                      ('Importar seleccionado', True, False),
                                      ('Descargar e importar todos', True, True)):
            boton = ttk.Button(botones, text=texto, command=lambda i=importar,t=todos: self.actualizar(i,t))
            boton.pack(side='left',padx=3)
            self.acciones.append(boton)
        ttk.Button(botones, text='Cerrar', command=self.cerrar).pack(side='right')
        self.window.bind('<Configure>', self.redimensionar)

    def redimensionar(self, event):
        if event.widget == self.window:
            for etiqueta in (self.ayuda, self.aviso, self.zona):
                etiqueta.configure(wraplength=max(100, event.width-24))

    def escribir_detalle(self, texto):
        self.detalle.configure(state='normal')
        self.detalle.delete('1.0', 'end')
        self.detalle.insert('1.0', texto)
        self.detalle.configure(state='disabled')

    def refrescar(self):
        seleccion = self.tabla.selection()
        nombre = self.registros[int(seleccion[0])]['nombre'] if seleccion and hasattr(self, 'registros') else None
        datos = self.modelo.listar()
        self.registros = datos['registros']
        self.tabla.delete(*self.tabla.get_children())
        self.aviso.configure(text=' '.join(datos['avisos']) or 'El registro disponible no permite demostrar que los datos sean los más recientes. No se marcará «Actualizado» sin evidencia.')
        self.zona.configure(text='Zona horaria: ' + datos['zona'] + '. La fecha de operación en la base es un dato separado y no se consulta en esta etapa.')
        for indice, fila in enumerate(self.registros):
            self.tabla.insert('', 'end', iid=str(indice), values=tuple(fila[c] for c in ('nombre', 'comprobacion', 'recepcion', 'importacion', 'estado', 'error')))
        if self.registros:
            indice = next((i for i, r in enumerate(self.registros) if r['nombre'] == nombre), 0)
            self.tabla.selection_set(str(indice))
            self.tabla.focus(str(indice))
            self.seleccionar()
        else:
            self.escribir_detalle('No hay estacionamientos activos en el catálogo. No se ha consultado ningún servicio externo.')

    def seleccionar(self, event=None):
        seleccion = self.tabla.selection()
        if seleccion:
            r = self.registros[int(seleccion[0])]
            self.escribir_detalle(r['nombre'] + '\n' + r['motivo'] + '\nÚltimo error: ' + r['error'] + '\nÚltima operación en la base: ' + r['operacion'])

    def cerrar(self):
        if self.ocupado:
            messagebox.showinfo('Actualización', 'Espera a que finalice la actualización en curso.', parent=self.window)
            return
        self.window.destroy()

    def actualizar(self, importar, todos):
        if self.ocupado: return
        seleccion = self.tabla.selection()
        nombre = None if todos else (self.registros[int(seleccion[0])]['nombre'] if seleccion else None)
        if not todos and not nombre: return
        self.ocupado = True
        for boton in self.acciones: boton.configure(state='disabled')
        self.aviso.configure(text='Procesando respaldos. Cada estación conserva su base anterior hasta validar y activar la nueva.')
        def trabajar():
            try:
                from actualizador_respaldos import ActualizadorRespaldos
                servicio = ActualizadorRespaldos(config_path=self.modelo.catalogo.ruta, directorio=self.modelo.ruta.parent)
                if todos:
                    resultado = servicio.ejecutar_todos(importar=importar)
                else:
                    servicio.actualizar_estacion(nombre)
                    resultado = [(nombre,'Base local disponible')]
                texto = '\n'.join(n+': '+estado for n,estado in resultado) or 'No hay estaciones autorizadas. Configura el perfil local de recuperación.'
            except Exception:
                texto = 'No se completó la actualización. Revisa el perfil local, MariaDB, permisos o el registro de la estación. No se muestran credenciales.'
            self.cola.put(texto)
        threading.Thread(target=trabajar,daemon=False).start()
        self.window.after(100,self.recoger)

    def recoger(self):
        if not self.window.winfo_exists(): return
        try: texto = self.cola.get_nowait()
        except queue.Empty:
            self.window.after(100,self.recoger)
            return
        self.ocupado = False
        for boton in self.acciones: boton.configure(state='normal')
        self.refrescar()
        self.aviso.configure(text=texto)
        self.escribir_detalle(texto)
