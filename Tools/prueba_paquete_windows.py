"""Prueba integrada del ejecutable; datos ficticios, sin servicios ni consola."""
import json
import os
from pathlib import Path
import socket
import tempfile
from unittest.mock import patch


def ejecutar(informe):
    from Tools.entorno_windows import preparar, datos_usuario
    from Tools.proyect_tools import Tools
    from Models.estacionamientos_config import EstacionamientosConfig
    from Controller.controller_login import ControllerLogin
    from Views.view_login import View_Login
    import tkinter as tk
    from ttkthemes import ThemedStyle
    from tkcalendar import DateEntry
    import win32com.client
    with tempfile.TemporaryDirectory(prefix='panel-smoke-') as temporal:
        with patch.dict(os.environ, LOCALAPPDATA=temporal), patch.object(socket.socket, 'connect', side_effect=AssertionError('No conectar red')):
            destino = datos_usuario()
            preparar(destino, lambda texto: 'clave-ficticia-prueba')
            originales = {p.name: p.read_bytes() for p in (destino / 'Config/config_files').glob('*.json')}
            preparar(destino, lambda texto: (_ for _ in ()).throw(AssertionError('No volver a pedir contraseña')))
            assert originales == {p.name: p.read_bytes() for p in (destino / 'Config/config_files').glob('*.json')}
            cwd = Path.cwd()
            try:
                os.chdir(destino)
                tools = Tools()
                ruta = tools.read_path_config_file('config_files', 'database_config_file')
                modelo = EstacionamientosConfig(ruta, 'admin')
                assert len(modelo.activos()) == 12
                datos = json.loads(Path(ruta).read_text(encoding='utf-8'))
                assert any(r['name_config'] == 'Ciudad Mendoza' for r in datos['estacionamientos_eliminados'])
                modelo.editar('Aguascalientes 143', 'Aguascalientes 143', 'aguascalientes143@pasesa.com.mx', 'db_aguascalientes_143', 'Prueba local')
                # Construcción real del login, imágenes, temas, calendario y catálogo.
                with patch.object(tk.Misc, 'mainloop', lambda self, *args: None):
                    vista = View_Login()
                style = ThemedStyle(vista.window_login)
                for tema in style.theme_names():
                    style.set_theme(tema)
                calendario = DateEntry(vista.window_login)
                calendario.destroy()
                login = ControllerLogin()
                with patch.object(tk.Misc, 'mainloop', lambda self, *args: None):
                    login.get_data('Aurelio', 'clave-ficticia-prueba')
                vista.window_login.update()
                assert len([w for w in vista.window_login.winfo_children() if isinstance(w, tk.Toplevel)]) >= 1
                vista.window_login.destroy()
            finally:
                os.chdir(cwd)
    informe.parent.mkdir(parents=True, exist_ok=True)
    informe.write_text(json.dumps({'resultado': 'OK', 'activos': 12, 'retirado': 'Ciudad Mendoza',
        'pruebas': ['preparacion', 'reinstalacion', 'edicion_catalogo', 'login_admin', 'temas', 'calendario', 'sin_red']}, indent=2), encoding='utf-8')
