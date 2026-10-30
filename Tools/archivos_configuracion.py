"""Respaldo privado y reemplazo atómico con control de cambios concurrentes."""
from contextlib import suppress
import os
from pathlib import Path
import secrets
import stat
import tempfile
from datetime import datetime, timezone


def guardar_con_respaldo(ruta, contenido, esperado):
    ruta = Path(ruta)
    if ruta.is_symlink() or not ruta.is_file():
        raise ValueError('Se requiere un archivo regular, sin enlaces simbólicos.')
    original = ruta.stat()
    if ruta.read_bytes() != esperado:
        raise ValueError('El archivo cambió durante la revisión; no se reemplazó.')
    nombre = ruta.name + '.antes_recuperacion_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + secrets.token_hex(6) + '.respaldo'
    respaldo = ruta.with_name(nombre)
    descriptor = os.open(respaldo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as archivo:
            archivo.write(esperado)
            if os.name != 'nt':
                actual = os.fstat(archivo.fileno())
                if (actual.st_uid, actual.st_gid) != (original.st_uid, original.st_gid):
                    os.fchown(archivo.fileno(), original.st_uid, original.st_gid)
            archivo.flush()
            os.fsync(archivo.fileno())
    except BaseException:
        with suppress(OSError): respaldo.unlink()
        raise
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(dir=ruta.parent, prefix='.recuperacion_', suffix='.respaldo', delete=False) as archivo:
            temporal = archivo.name
            archivo.write(contenido)
            archivo.flush()
            if os.name != 'nt':
                actual = os.fstat(archivo.fileno())
                if (actual.st_uid, actual.st_gid) != (original.st_uid, original.st_gid):
                    os.fchown(archivo.fileno(), original.st_uid, original.st_gid)
                os.fchmod(archivo.fileno(), stat.S_IMODE(original.st_mode))
                if hasattr(os, 'listxattr'):
                    atributos = os.listxattr(ruta)
                    for atributo in os.listxattr(temporal):
                        if atributo not in atributos: os.removexattr(temporal, atributo)
                    for atributo in atributos:
                        os.setxattr(temporal, atributo, os.getxattr(ruta, atributo))
            os.fsync(archivo.fileno())
        actual = ruta.stat()
        if ((actual.st_dev, actual.st_ino, actual.st_mtime_ns, actual.st_ctime_ns) !=
                (original.st_dev, original.st_ino, original.st_mtime_ns, original.st_ctime_ns)
                or ruta.is_symlink() or ruta.read_bytes() != esperado):
            raise ValueError('El archivo cambió durante la recuperación; se conserva.')
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            reemplazar = ctypes.WinDLL('kernel32', use_last_error=True).ReplaceFileW
            reemplazar.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                   wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID]
            reemplazar.restype = wintypes.BOOL
            if not reemplazar(str(ruta), temporal, None, 0, None, None): raise ctypes.WinError(ctypes.get_last_error())
        else:
            os.replace(temporal, ruta)
            with suppress(OSError):
                fd = os.open(ruta.parent, os.O_RDONLY | os.O_DIRECTORY)
                try: os.fsync(fd)
                finally: os.close(fd)
        return respaldo
    finally:
        if temporal:
            with suppress(FileNotFoundError): os.unlink(temporal)
