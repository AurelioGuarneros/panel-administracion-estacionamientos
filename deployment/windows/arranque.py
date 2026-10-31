"""Entrada gráfica para PyInstaller. El código original conserva su entrada main.py."""
import ctypes
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import threading
import traceback

from Tools.entorno_windows import datos_usuario, preparar

_MUTEX = None


def bloquear_instancia():
    global _MUTEX
    from ctypes import wintypes
    crear = ctypes.WinDLL('kernel32', use_last_error=True).CreateMutexW
    crear.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    crear.restype = wintypes.HANDLE
    _MUTEX = crear(None, False, 'Local\\PanelEstacionamientosUsuario')
    if not _MUTEX:
        raise ctypes.WinError(ctypes.get_last_error())
    return ctypes.get_last_error() != 183


def registrar(tipo, valor, traza):
    # Sin mensajes de excepción, variables locales, contraseñas ni rutas de usuario.
    ruta = datos_usuario() / 'logs'
    ruta.mkdir(parents=True, exist_ok=True)
    archivo = ruta / 'errores.log'
    if archivo.exists() and archivo.stat().st_size > 1024 * 1024:
        archivo.replace(ruta / 'errores-anteriores.log')
    with archivo.open('a', encoding='utf-8') as salida:
        salida.write(f'{datetime.now(timezone.utc).isoformat()} {tipo.__name__}\n')
        for marco in traceback.extract_tb(traza):
            salida.write(f'  {Path(marco.filename).name}:{marco.lineno} {marco.name}\n')


def iniciar():
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
    if not bloquear_instancia():
        messagebox.showinfo('Panel de Estacionamientos', 'El panel ya está abierto.')
        return 0
    raiz = tk.Tk()
    raiz.withdraw()
    destino = datos_usuario()
    destino.mkdir(parents=True, exist_ok=True)

    def error(tipo, valor, traza):
        registrar(tipo, valor, traza)
        messagebox.showerror('Panel de Estacionamientos',
                             'Ocurrió un error. Consulta datos/logs/errores.log en la carpeta del panel de tu usuario.')

    sys.excepthook = error
    threading.excepthook = lambda args: error(args.exc_type, args.exc_value, args.exc_traceback)
    tk.Tk.report_callback_exception = lambda self, *args: error(*args)
    origen = None
    if not (destino / 'Config/config_files').exists():
        importar = messagebox.askyesnocancel('Primer inicio',
            '¿Quieres importar las configuraciones de una instalación anterior?\n'
            'Sí: seleccionar la carpeta anterior. No: crear una instalación nueva.\n'
            'Los archivos originales se conservarán.')
        if importar is None:
            raiz.destroy()
            return 0
        if importar:
            origen = filedialog.askdirectory(title='Carpeta anterior que contiene Config')
            if not origen:
                raiz.destroy()
                return 0

    def pedir_clave(texto):
        clave = simpledialog.askstring('Crear administrador local Aurelio', texto, show='*', parent=raiz)
        if clave is None:
            raise InterruptedError('Preparación cancelada')
        return clave

    try:
        preparar(destino, pedir_clave, origen)
    except InterruptedError:
        raiz.destroy()
        return 0
    except (ValueError, OSError):
        registrar(*sys.exc_info())
        messagebox.showerror('Primer inicio', 'No se pudo preparar la configuración. Comprueba la carpeta seleccionada y que la contraseña no esté vacía y coincida. No se reemplazaron configuraciones existentes.')
        raiz.destroy()
        return 1
    raiz.destroy()
    os.chdir(destino)
    from main import main
    main()
    return 0


if __name__ == '__main__':
    try:
        if '--smoke-test' in sys.argv:
            from Tools.prueba_paquete_windows import ejecutar
            ejecutar(Path(sys.argv[sys.argv.index('--smoke-test') + 1]))
        else:
            raise SystemExit(iniciar())
    except Exception:
        registrar(*sys.exc_info())
        raise
