"""Ventana independiente para administrar el catálogo local."""
import errno
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from Models.estacionamientos_config import ErrorValidacion, exigir_admin


class ViewAdminEstacionamientos:
    def __init__(self, parent, modelo, on_change, permiso=None):
        exigir_admin(permiso)
        exigir_admin(modelo.permiso)
        self.modelo, self.on_change = modelo, on_change
        registros = self.modelo.listar()
        self.window = tk.Toplevel(parent)
        try:
            self.construir(registros)
        except Exception:
            self.window.destroy()
            raise

    def construir(self, registros):
        self.window.title('Administrar estacionamientos')
        ancho = min(960, max(320, self.window.winfo_screenwidth() - 40))
        alto = min(520, max(240, self.window.winfo_screenheight() - 80))
        self.window.geometry(f'{ancho}x{alto}')
        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=1)
        marco = ttk.Frame(self.window)
        marco.grid(row=0, column=0, columnspan=3, sticky='nsew', padx=6, pady=6)
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(marco, columns=('nombre', 'ubicacion', 'email', 'database', 'estado'), show='headings', selectmode='browse', height=6)
        for campo, titulo in zip(self.tabla['columns'], ('Nombre', 'Ubicación', 'Correo remitente', 'Base de datos', 'Estado')):
            self.tabla.heading(campo, text=titulo)
            anchos = {'nombre': 180, 'ubicacion': 160, 'email': 240, 'database': 180, 'estado': 80}
            self.tabla.column(campo, width=anchos[campo], minwidth=80, stretch=False)
        self.tabla.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(marco, orient='vertical', command=self.tabla.yview)
        horizontal = ttk.Scrollbar(marco, orient='horizontal', command=self.tabla.xview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.bind('<<TreeviewSelect>>', self.seleccionar)
        self.campos = {}
        for fila, (campo, titulo) in enumerate((('name_config', 'Nombre'), ('ubicacion', 'Ubicación'), ('email', 'Correo remitente'), ('database', 'Base de datos')), 1):
            ttk.Label(self.window, text=titulo).grid(row=fila, column=0)
            self.campos[campo] = tk.StringVar(self.window)
            ttk.Entry(self.window, textvariable=self.campos[campo], width=20).grid(row=fila, column=1, columnspan=2, sticky='ew', padx=6)
        ttk.Label(self.window, text='Plantilla para agregar').grid(row=5, column=0)
        self.plantilla = ttk.Combobox(self.window, state='readonly')
        self.plantilla.grid(row=5, column=1, columnspan=2, sticky='ew', padx=6)
        ayuda = ttk.Label(self.window, text='Las altas quedan pendientes de verificación, con actualización automática deshabilitada. El remitente debe ser exclusivo, incluso entre inactivos. El correo central receptor se configura por separado.', wraplength=ancho - 24)
        ayuda.grid(row=6, column=0, columnspan=3, pady=4, sticky='ew')
        self.window.bind('<Configure>', lambda event: ayuda.configure(wraplength=max(100, event.width - 24)) if event.widget == self.window else None)
        for columna, (titulo, accion) in enumerate((('Agregar con plantilla', self.agregar), ('Guardar edición', self.editar), ('Activar / desactivar', self.cambiar_estado), ('Eliminar definitivamente del catálogo…', self.eliminar))):
            ttk.Button(self.window, text=titulo, command=accion).grid(row=7 + columna, column=0, columnspan=3, sticky='ew', padx=6, pady=2)
        self.recargar(registros)

    def recargar(self, registros=None):
        seleccion = self.tabla.selection()
        self.registros = self.modelo.listar() if registros is None else registros
        self.tabla.delete(*self.tabla.get_children())
        for indice, r in enumerate(self.registros):
            self.tabla.insert('', 'end', iid=str(indice), values=(r['name_config'], r.get('ubicacion', ''), r.get('email', ''), r['database'], 'Activo' if r.get('activo', True) else 'Inactivo'))
        if seleccion and seleccion[0] in self.tabla.get_children():
            self.tabla.selection_set(seleccion[0])
            self.tabla.focus(seleccion[0])
            self.seleccionar()
        self.plantilla.configure(values=[r['name_config'] for r in self.registros])
        if self.plantilla.get() not in [r['name_config'] for r in self.registros]:
            self.plantilla.set('')

    def seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            raise ErrorValidacion('Selecciona un estacionamiento en la tabla.')
        return self.registros[int(seleccion[0])]

    def seleccionar(self, event=None):
        if self.tabla.selection():
            registro = self.seleccionado()
            for campo, variable in self.campos.items():
                variable.set(registro.get(campo, ''))

    def ejecutar(self, operacion):
        try:
            resultado = operacion()
        except (OSError, ValueError) as error:
            messagebox.showerror('Administración', 'No se pudo guardar. ' + causa_segura(error), parent=self.window)
            return
        if resultado is False:
            return
        fallos = []
        for nombre, refrescar in (('selector', self.on_change), ('tabla', self.recargar)):
            try:
                if refrescar() is False:
                    fallos.append(nombre)
            except Exception:
                fallos.append(nombre)
        if fallos:
            messagebox.showwarning('Cambios guardados',
                                   'El archivo se guardó, pero falló la actualización de: ' + ', '.join(fallos) + '. Cierra y vuelve a abrir la pantalla.',
                                   parent=self.window)

    def valores(self):
        return [self.campos[c].get() for c in ('name_config', 'email', 'database')]

    def agregar(self):
        self.ejecutar(lambda: self.modelo.agregar(*self.valores(), plantilla=self.plantilla.get(), ubicacion=self.campos['ubicacion'].get()))

    def editar(self):
        self.ejecutar(lambda: self.modelo.editar(self.seleccionado()['name_config'], *self.valores(), ubicacion=self.campos['ubicacion'].get()))

    def cambiar_estado(self):
        def operacion():
            registro = self.seleccionado()
            activo = not registro.get('activo', True)
            accion = 'Activar' if activo else 'Desactivar'
            if messagebox.askyesno('Confirmar', f"¿{accion} {registro['name_config']}?", parent=self.window):
                self.modelo.cambiar_estado(registro['name_config'], activo)
            else:
                return False
        self.ejecutar(operacion)

    def eliminar(self):
        def operacion():
            registro = self.seleccionado()
            nombre = registro['name_config']
            confirmacion = simpledialog.askstring(
                'Eliminar definitivamente del catálogo',
                f'Eliminarás «{nombre}» del catálogo.\n'
                'No podrá reactivarse desde el catálogo. Los usuarios que lo tengan\n'
                'como conexión predeterminada necesitarán otra asignación.\n'
                'Sus bases de datos, respaldos e información histórica se conservarán.\n\n'
                'Para confirmar, escribe exactamente el nombre del estacionamiento:',
                parent=self.window)
            if confirmacion is None:
                return False
            self.modelo.eliminar(nombre, confirmacion)
            self.tabla.selection_remove(*self.tabla.selection())
            for variable in self.campos.values():
                variable.set('')
        self.ejecutar(operacion)


def causa_segura(error):
    """Nunca mostrar str(error) de errores externos: puede contener secretos."""
    if isinstance(error, ErrorValidacion):
        return str(error)
    if isinstance(error, json.JSONDecodeError):
        return f'El JSON no es válido (línea {error.lineno}, columna {error.colno}).'
    if isinstance(error, UnicodeError):
        return 'La configuración no tiene una codificación UTF-8 válida.'
    if isinstance(error, PermissionError):
        return 'Permiso denegado. Verifica el rol administrador y los permisos del archivo y su carpeta.'
    if isinstance(error, FileNotFoundError):
        return 'No se encuentra el archivo de configuración o su carpeta.'
    if isinstance(error, OSError):
        causas = {
            errno.ENOSPC: 'No hay espacio disponible en el disco.',
            errno.EROFS: 'El sistema de archivos es de solo lectura.',
            errno.EIO: 'Error de entrada/salida al acceder al archivo.',
            errno.ENOTSUP: 'El sistema de archivos no admite conservar los atributos de seguridad.',
        }
        return causas.get(error.errno, 'Falló el acceso al archivo de configuración' +
                          (f' (código {error.errno}).' if error.errno is not None else '.'))
    return 'La configuración tiene un formato o un valor no válido.'
