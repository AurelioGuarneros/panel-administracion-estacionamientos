# Lista explícita de datos: jamás incluir Config completo ni archivos locales.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

raiz = Path(SPECPATH).parents[1]
datos = [(str(raiz / 'Config/catalogo_inicial.json'), 'Config')]
for nombre in ('path_files_settings', 'user_settings', 'database_connection_configuration', 'system_settings'):
    datos.append((str(raiz / f'Config/config_files/{nombre}.json.example'), 'Config/config_files'))
for nombre in ('logo_pase.jpg', 'icono_desconectar.png', 'icono_salir.png', 'icono_borrar.png', 'icono_calendario.png'):
    datos.append((str(raiz / 'Public/Images' / nombre), 'Public/Images'))
binarios, ocultos = [], ['babel.numbers', 'win32com.client', 'pythoncom', 'pywintypes']
for paquete in ('ttkthemes', 'tkcalendar', 'Crypto', 'babel'):
    d, b, h = collect_all(paquete)
    datos += d
    binarios += b
    ocultos += h
for paquete in ('Views', 'Controller', 'Models', 'Config', 'Tools'):
    ocultos += collect_submodules(paquete)
a = Analysis([str(raiz / 'deployment/windows/arranque.py')], pathex=[str(raiz)],
             binaries=binarios, datas=datos, hiddenimports=ocultos,
             excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='PanelEstacionamientos',
          debug=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PanelEstacionamientos')
