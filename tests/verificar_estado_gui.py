"""Prueba gráfica real del selector y su nueva ventana, con datos ficticios."""
import builtins
import hashlib
import imaplib
import io
import json
from pathlib import Path
import smtplib
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import pymysql
from PIL import Image
from Controller.controller_select_conection import Controller_Select_Conection
from Tools.proyect_tools import Tools
from Views.view_select_conection import View_Conect


def main():
    evidencia = Path(tempfile.mkdtemp(prefix='estado_gui_', dir=RAIZ))
    home = evidencia / 'home_ficticio'
    carpeta = home / '.local/share/panel-estacionamientos'
    carpeta.mkdir(parents=True)
    registro = carpeta / 'actualizaciones.sqlite3'
    catalogo = evidencia / 'catalogo_ficticio.json'
    catalogo.write_text(json.dumps({'settings': [
        {'name_config': 'Ejemplo con carga registrada', 'database': 'db_ficticia'},
        {'name_config': 'Punta Santa Rosa PV', 'database': 'db_punta_ficticia'},
        {'name_config': 'Ejemplo con error', 'database': 'db_error_ficticia'},
        {'name_config': 'Ciudad Mendoza', 'database': 'db_ciudad_ficticia', 'activo': False},
    ]}), encoding='utf-8')
    with sqlite3.connect(registro) as c:
        c.execute('CREATE TABLE actualizaciones (estacionamiento TEXT PRIMARY KEY, ultimo_respaldo TEXT, ultima_comprobacion REAL, estado TEXT)')
        c.execute('CREATE TABLE importaciones (estacionamiento TEXT PRIMARY KEY, uid_importado TEXT, fecha_importacion REAL, archivo TEXT)')
        for nombre, estado in [('Ejemplo con carga registrada', 'Actualizado'),
                               ('Punta Santa Rosa PV', 'Respaldo encontrado en correo; pendiente de importar'),
                               ('Ejemplo con error', 'ERROR Access denied password=SECRETO_FICTICIO'),
                               ('Ciudad Mendoza', 'Encontrado')]:
            c.execute('INSERT INTO actualizaciones VALUES (?, ?, ?, ?)',
                      (nombre, '2026-10-23T20:00:00Z', 1792785600.0, estado))
        c.execute('INSERT INTO importaciones VALUES (?, ?, ?, ?)',
                  ('Ejemplo con carga registrada', 'uid_ficticio', 1792789200.0, 'ficticio.zip'))
    antes = (hashlib.sha256(registro.read_bytes()).hexdigest(), registro.stat().st_mtime_ns,
             set(carpeta.iterdir()), catalogo.read_bytes())
    conectar = sqlite3.connect
    consultas = []
    def conectar_ro(ubicacion, **kwargs):
        assert ubicacion == registro.resolve().as_uri() + '?mode=ro&immutable=1'
        assert kwargs.get('uri') is True
        c = conectar(ubicacion, **kwargs)
        c.set_trace_callback(consultas.append)
        return c
    abrir = builtins.open
    def abrir_seguro(file, *a, **kw):
        if isinstance(file, (str, bytes, Path)) and not isinstance(file, bytes):
            assert not Path(file).resolve().is_relative_to(RAIZ / 'Config/config_files'), 'No leer configuraciones existentes'
        return abrir(file, *a, **kw)
    def rutas(self, tipo, clave):
        if tipo == 'config_files' and clave == 'database_config_file':
            return str(catalogo)
        imagenes = {'logo_pase': 'logo_pase.jpg', 'icono_desconectar': 'icono_desconectar.png',
                    'icono_salir': 'icono_salir.png'}
        if tipo == 'images' and clave in imagenes:
            return str(RAIZ / 'Public/Images' / imagenes[clave])
        raise AssertionError('Recurso no autorizado en prueba gráfica')
    root = tk.Tk()
    root.withdraw()
    errores = []
    root.report_callback_exception = lambda *e: errores.append(e[0].__name__)

    def actualizar():
        root.update_idletasks()
        root.update()
        assert not errores, errores

    def hijos(widget):
        for w in widget.winfo_children():
            yield w
            yield from hijos(w)

    def boton(widget, texto):
        return next(w for w in hijos(widget) if isinstance(w, ttk.Button) and w.cget('text') == texto)

    def captura(ventana, nombre):
        actualizar()
        ventana.after(200, root.quit)
        root.mainloop()
        raw = evidencia / (nombre + '.xwd')
        subprocess.run(['xwd', '-silent', '-id', str(ventana.winfo_id()), '-out', str(raw)], check=True)
        datos = raw.read_bytes()
        h = struct.unpack('>25I', datos[:100])
        assert h[7] == 0 and h[11] == 32
        Image.frombytes('RGB', (h[4], h[5]), datos[h[0] + h[19]*12:], 'raw', 'BGRX', h[12], 1).save(evidencia / nombre)

    try:
        with patch.object(Tools, 'read_path_config_file', new=rutas), \
             patch.object(Tools, 'descifrar_AES', side_effect=AssertionError('No descifrar')), \
             patch.object(Path, 'home', return_value=home), \
             patch.object(builtins, 'open', new=abrir_seguro), \
             patch.object(io, 'open', new=abrir_seguro), \
             patch.object(sqlite3, 'connect', side_effect=conectar_ro), \
             patch.object(pymysql, 'connect', side_effect=AssertionError('MariaDB bloqueado')) as db, \
             patch.object(imaplib, 'IMAP4_SSL', side_effect=AssertionError('IMAP bloqueado')) as imap, \
             patch.object(smtplib, 'SMTP', side_effect=AssertionError('SMTP bloqueado')) as smtp, \
             patch.object(socket.socket, 'connect', side_effect=AssertionError('Red bloqueada')) as red:
            # Widgets y callbacks reales; el verificador controla el bucle de eventos.
            with patch.object(tk.Misc, 'mainloop', return_value=None):
                selector = View_Conect('Administrador ficticio', {}, 'admin')
            selector.panel_connect.geometry('+20+20')
            actualizar()
            admin = getattr(selector, 'admin_estacionamientos', None)
            if admin:
                admin.window.destroy()
            actualizar()
            abrir_estado = boton(selector.panel_connect, 'Estado de actualización')
            assert abrir_estado.winfo_viewable()
            captura(selector.panel_connect, '01_selector.png')
            abrir_estado.invoke()
            actualizar()
            vista = selector.estado_actualizacion
            vista.window.geometry('1180x580+40+40')
            actualizar()
            assert vista.window.title() == 'Estado de actualización'
            assert len(vista.registros) == 3
            assert all(r['nombre'] != 'Ciudad Mendoza' for r in vista.registros)
            assert all(r['recepcion'] == 'Sin fecha registrada' for r in vista.registros)
            assert all(r['estado'] != 'Actualizado' for r in vista.registros)
            assert vista.registros[0]['importacion'] == '23/10/2026 15:00:00'
            assert vista.registros[2]['estado'] == 'Error'
            assert 'SECRETO_FICTICIO' not in str(vista.registros)
            vista.tabla.selection_set('1')
            vista.tabla.event_generate('<<TreeviewSelect>>')
            actualizar()
            assert 'pendiente de verificación' in vista.detalle.get('1.0', 'end')
            assert vista.detalle.cget('state') == 'disabled'
            captura(vista.window, '02_estado.png')
            vista.tabla.xview_moveto(1)
            captura(vista.window, '03_estados_y_errores.png')
            vista.tabla.xview_moveto(0)
            vista.window.geometry('720x480+40+40')
            actualizar()
            captura(vista.window, '04_pantalla_reducida.png')
            for w in vista.window.winfo_children():
                assert w.winfo_ismapped()
                assert 0 <= w.winfo_y() and w.winfo_y() + w.winfo_height() <= vista.window.winfo_height()
            boton(vista.window, 'Refrescar registro local').invoke()
            actualizar()
            assert vista.tabla.selection() == ('1',)
            # El mismo botón vuelve a enfocar/refrescar una sola ventana.
            abrir_estado.invoke()
            assert selector.estado_actualizacion is vista
            assert antes == (hashlib.sha256(registro.read_bytes()).hexdigest(), registro.stat().st_mtime_ns,
                             set(carpeta.iterdir()), catalogo.read_bytes())
            # Un registro ausente no se crea y el catálogo permanece visible.
            faltante = carpeta / 'ausente.sqlite3'
            ruta_anterior = vista.modelo.ruta
            vista.modelo.ruta = faltante
            boton(vista.window, 'Refrescar registro local').invoke()
            actualizar()
            assert not faltante.exists()
            assert len(vista.registros) == 3
            assert 'No existe registro' in vista.aviso.cget('text')
            captura(vista.window, '05_sin_registro.png')
            vista.modelo.ruta = ruta_anterior
            boton(vista.window, 'Cerrar').invoke()
            actualizar()
            abrir_estado.invoke()
            actualizar()
            assert selector.estado_actualizacion is not vista
            assert selector.estado_actualizacion.window.winfo_exists()
            for servicio in (db, imap, smtp, red):
                servicio.assert_not_called()
        assert consultas and all(q.lstrip().upper().startswith('SELECT ') for q in consultas)
        resultado = {'resultado': 'OK', 'selector_real': True, 'boton_real': True,
                     'refrescar_y_reabrir': True, 'fechas_separadas': True,
                     'punta_pendiente': True, 'ciudad_excluida': True,
                     'solo_select_sqlite': True, 'registro_y_catalogo_intactos': True,
                     'servicios_externos_bloqueados': True}
        (evidencia / 'RESULTADO.json').write_text(json.dumps(resultado, indent=2))
        print('Prueba gráfica aprobada. Evidencias:', evidencia)
    finally:
        root.destroy()


if __name__ == '__main__':
    main()
