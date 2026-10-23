"""Ejecutar desde la raíz del repositorio. No modifica bases de datos."""
from pathlib import Path
import shutil
import sys

raiz = Path.cwd()
vista = raiz / 'Views' / 'view_select_conection.py'
complemento = raiz / 'panel_mejoras.py'
marca = 'from panel_mejoras import instalar_mejoras'
if not vista.is_file() or not complemento.is_file():
    sys.exit('ERROR: ejecute desde la raíz del proyecto con panel_mejoras.py presente.')
texto = vista.read_text(encoding='utf-8')
if marca in texto:
    print('Las mejoras ya están instaladas; no se duplicaron.')
else:
    shutil.copy2(vista, vista.with_suffix('.py.antes_mejoras'))
    nuevo = texto.rstrip() + '\n\n' + marca + '\ninstalar_mejoras(View_Conect)\n'
    compile(nuevo, str(vista), 'exec')
    vista.write_text(nuevo, encoding='utf-8')
    print('Mejoras instaladas; copia de seguridad: Views/view_select_conection.py.antes_mejoras')
print('No se modificaron bases de datos ni credenciales.')
