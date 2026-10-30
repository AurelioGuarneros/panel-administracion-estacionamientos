"""Configuración local de estacionamientos, sin conexiones ni descifrado."""
import copy
import json
import os
import re
import stat
from pathlib import Path
import tempfile
import uuid


class ErrorValidacion(ValueError):
    """Mensaje controlado, sin valores procedentes de la configuración."""


def exigir_admin(permiso):
    if permiso != 'admin':
        raise PermissionError('Se requieren permisos de administrador.')


def resolver_registro(datos, nombre):
    """Los nombres anteriores siguen siendo referencias válidas, sin migrar usuarios."""
    encontrados = [r for r in datos['settings']
                   if r['name_config'] == nombre or nombre in r.get('nombres_anteriores', [])]
    if len(encontrados) != 1:
        raise ErrorValidacion('El estacionamiento no existe o su nombre es ambiguo.')
    return encontrados[0]


class EstacionamientosConfig:
    def __init__(self, ruta, permiso=None):
        self.permiso = permiso
        self.raiz = Path(__file__).resolve().parents[1]
        self.ruta = Path(ruta).resolve()
        if self.raiz not in self.ruta.parents:
            raise ErrorValidacion('La configuración debe estar dentro de integración.')

    def _leer(self):
        with self.ruta.open(encoding='utf-8') as archivo:
            datos = json.load(archivo)
        if not isinstance(datos, dict) or not isinstance(datos.get('settings'), list):
            raise ErrorValidacion('Se esperaba una lista settings.')
        for registro in datos['settings']:
            if not isinstance(registro, dict) or not isinstance(registro.get('name_config'), str) or not isinstance(registro.get('database'), str):
                raise ErrorValidacion('Registro de estacionamiento inválido.')
            if 'activo' in registro and type(registro['activo']) is not bool:
                raise ErrorValidacion('El estado activo debe ser booleano.')
            aliases = registro.get('nombres_anteriores', [])
            if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
                raise ErrorValidacion('Los nombres anteriores deben ser una lista de textos.')
        retirados = datos.get('estacionamientos_eliminados', [])
        if not isinstance(retirados, list) or any(
                not isinstance(r, dict) or not isinstance(r.get('name_config'), str)
                or not isinstance(r.get('database'), str)
                or not isinstance(r.get('nombres_anteriores', []), list)
                or not all(isinstance(n, str) for n in r.get('nombres_anteriores', []))
                for r in retirados):
            raise ErrorValidacion('Las referencias de estacionamientos eliminados son inválidas.')
        return datos

    def listar(self):
        return [r for r in self._leer()['settings'] if r['name_config'] != 'Admin']

    def activos(self):
        return [r for r in self.listar() if r['name_config'] and r.get('activo', True)]

    def resolver_nombre(self, nombre):
        return resolver_registro(self._leer(), nombre)['name_config']

    def _buscar(self, datos, nombre):
        if nombre == 'Admin':
            raise ErrorValidacion('El registro Admin está reservado.')
        encontrados = [r for r in datos['settings'] if r['name_config'] == nombre]
        if len(encontrados) != 1:
            raise ErrorValidacion('El estacionamiento no existe o su nombre es ambiguo.')
        return encontrados[0]

    def _campos(self, datos, nombre, email, database, original=None):
        if not all(isinstance(v, str) and v.strip() for v in (nombre, email, database)):
            raise ErrorValidacion('Nombre, remitente y base de datos son obligatorios.')
        nombre, email, database = nombre.strip(), email.strip(), database.strip()
        if nombre.casefold() == 'admin':
            raise ErrorValidacion('El nombre Admin está reservado.')
        if any(r is not original and any(n.strip().casefold() == nombre.casefold()
               for n in [r['name_config'], *r.get('nombres_anteriores', [])]) for r in datos['settings']):
            raise ErrorValidacion('Ya existe un estacionamiento con ese nombre.')
        retirados = datos.get('estacionamientos_eliminados', [])
        if any(nombre.casefold() == n.strip().casefold() for r in retirados
               for n in [r['name_config'], *r.get('nombres_anteriores', [])]):
            raise ErrorValidacion('El nombre pertenece a un estacionamiento eliminado y está reservado para conservar sus referencias históricas.')
        if not re.fullmatch(r"[^\s@<>(),;]+@[^\s@<>(),;]+\.[^\s@<>(),;]+", email):
            raise ErrorValidacion('Indica un correo remitente válido, sin nombre ni direcciones adicionales.')
        self._validar_remitente(datos, email, original)
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', database):
            raise ErrorValidacion('La base de datos debe usar letras, números y guion bajo, sin espacios.')
        if any(r is not original and r['database'].strip().casefold() == database.casefold() for r in datos['settings']):
            raise ErrorValidacion('La base de datos ya está asignada a otro estacionamiento.')
        if any(r['database'].strip().casefold() == database.casefold() for r in retirados):
            raise ErrorValidacion('La base pertenece a un estacionamiento eliminado y está reservada para conservar sus referencias históricas.')
        return dict(name_config=nombre, email=email, database=database)

    def _validar_remitente(self, datos, email, original=None):
        # Incluye inactivos: desactivar no libera el remitente.
        conflictos = [r['name_config'] for r in datos['settings']
                      if r is not original and r['name_config'] != 'Admin'
                      and str(r.get('email', '')).strip().casefold() == email.strip().casefold()]
        if conflictos:
            raise ErrorValidacion('El correo remitente ya está asignado a: ' +
                                  ', '.join(conflictos) + '. Corrígelo antes de guardar.')

    def _ubicacion(self, ubicacion):
        if not isinstance(ubicacion, str):
            raise ErrorValidacion('La ubicación debe ser texto.')
        return ubicacion.strip()

    def _guardar(self, datos):
        # Reemplazo en el mismo directorio: un fallo no trunca el archivo original.
        temporal = None
        original = self.ruta.stat()
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.ruta.parent, delete=False) as archivo:
                temporal = archivo.name
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
                archivo.flush()
                if os.name != 'nt':
                    actual = os.fstat(archivo.fileno())
                    if (actual.st_uid, actual.st_gid) != (original.st_uid, original.st_gid):
                        os.fchown(archivo.fileno(), original.st_uid, original.st_gid)
                    os.fchmod(archivo.fileno(), stat.S_IMODE(original.st_mode))
                    # En Linux, conservar también las ACL y atributos del original.
                    if hasattr(os, 'listxattr'):
                        atributos = os.listxattr(self.ruta)
                        for atributo in os.listxattr(temporal):
                            if atributo not in atributos:
                                os.removexattr(temporal, atributo)
                        for atributo in atributos:
                            os.setxattr(temporal, atributo, os.getxattr(self.ruta, atributo))
                os.fsync(archivo.fileno())
            if os.name == 'nt':
                # ReplaceFileW conserva la DACL del destino; no ignorar fallos
                # al combinar los metadatos de seguridad.
                import ctypes
                from ctypes import wintypes
                reemplazar = ctypes.WinDLL('kernel32', use_last_error=True).ReplaceFileW
                reemplazar.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                       wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID]
                reemplazar.restype = wintypes.BOOL
                if not reemplazar(str(self.ruta), temporal, None, 0, None, None):
                    raise ctypes.WinError(ctypes.get_last_error())
            else:
                os.replace(temporal, self.ruta)
        finally:
            if temporal and os.path.exists(temporal):
                os.unlink(temporal)

    def agregar(self, nombre, email, database, plantilla, ubicacion=''):
        exigir_admin(self.permiso)
        if not plantilla:
            raise ErrorValidacion('Selecciona una plantilla para agregar el estacionamiento.')
        datos = self._leer()
        origen = self._buscar(datos, plantilla)
        if not all(c in origen for c in ('host', 'user', 'password', 'iv')):
            raise ErrorValidacion('La plantilla no contiene todos los campos de conexión.')
        campos = self._campos(datos, nombre, email, database)
        nuevo = copy.deepcopy(origen)
        # Una plantilla nunca certifica la asociación de un estacionamiento nuevo.
        nuevo.pop('nombres_anteriores', None)
        nuevo.pop('clave_respaldo', None)
        nuevo['id'] = str(uuid.uuid4())
        nuevo.update(campos, activo=True, ubicacion=self._ubicacion(ubicacion),
                     actualizacion_automatica=False, configuracion_verificada=False)
        datos['settings'].append(nuevo)
        self._guardar(datos)

    def editar(self, original, nombre, email, database, ubicacion=None):
        exigir_admin(self.permiso)
        datos = self._leer()
        registro = self._buscar(datos, original)
        campos = self._campos(datos, nombre, email, database, registro)
        if campos['name_config'] != original:
            registro.setdefault('clave_respaldo', original)
            anteriores = registro.setdefault('nombres_anteriores', [])
            if original not in anteriores:
                anteriores.append(original)
        if campos['email'] != registro.get('email') or campos['database'] != registro['database']:
            registro.update(actualizacion_automatica=False, configuracion_verificada=False)
        registro.update(campos)
        if ubicacion is not None:
            registro['ubicacion'] = self._ubicacion(ubicacion)
        self._guardar(datos)

    def cambiar_estado(self, nombre, activo):
        exigir_admin(self.permiso)
        if type(activo) is not bool:
            raise ErrorValidacion('Estado inválido.')
        datos = self._leer()
        registro = self._buscar(datos, nombre)
        if activo:
            self._campos(datos, registro['name_config'], registro.get('email', ''), registro['database'], registro)
        registro['activo'] = activo
        self._guardar(datos)

    def eliminar(self, nombre, confirmacion):
        """Retira solo el catálogo; nunca abre bases, respaldos ni archivos de usuarios."""
        exigir_admin(self.permiso)
        datos = self._leer()
        registro = self._buscar(datos, nombre)
        if confirmacion != nombre:
            raise ErrorValidacion('Para eliminar del catálogo escribe exactamente el nombre del estacionamiento.')
        # Reserva las identidades históricas sin conservar credenciales ni permitir
        # que otro registro nuevo herede su nombre o su base accidentalmente.
        referencia = {k: copy.deepcopy(registro[k]) for k in
                      ('id', 'name_config', 'database', 'nombres_anteriores', 'clave_respaldo') if k in registro}
        datos.setdefault('estacionamientos_eliminados', []).append(referencia)
        datos['settings'].remove(registro)
        self._guardar(datos)
