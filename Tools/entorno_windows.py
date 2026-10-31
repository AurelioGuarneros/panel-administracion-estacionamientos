"""Rutas y preparación del paquete; nunca modifica la instalación de origen."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from Tools.preparar_configuracion import ARCHIVOS, preparar_configuracion


def recursos():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))


def datos_usuario():
    return Path(os.environ['LOCALAPPDATA']) / 'PanelEstacionamientos' / 'datos'


def preparar(destino, pedir_clave, origen=None):
    """Publica una configuración completa por renombrado; conserva las existentes."""
    destino = Path(destino)
    carpeta = destino / 'Config/config_files'
    carpeta.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino, prefix='.primer-inicio-') as temporal:
        etapa = Path(temporal)
        config = etapa / 'Config/config_files'
        config.mkdir(parents=True)
        for nombre in ARCHIVOS:
            shutil.copyfile(recursos() / 'Config/config_files' / (nombre + '.example'), config / (nombre + '.example'))
        shutil.copyfile(recursos() / 'Config/catalogo_inicial.json', etapa / 'Config/catalogo_inicial.json')
        if origen is not None:
            origen = Path(origen) / 'Config/config_files'
            if not all((origen / nombre).is_file() for nombre in ARCHIVOS):
                raise ValueError('La carpeta elegida no contiene las cuatro configuraciones del panel.')
            if carpeta.exists():
                raise ValueError('Ya existe configuración local; no se importará encima.')
            respaldo = etapa / 'configuracion-importada-original'
            respaldo.mkdir()
            for nombre in ARCHIVOS:
                contenido = (origen / nombre).read_bytes()
                json.loads(contenido)
                (respaldo / nombre).write_bytes(contenido)
                (config / nombre).write_bytes(contenido)
            # El paquete usa sus propios recursos y una copia local de las configuraciones.
            shutil.copyfile(config / 'path_files_settings.json.example', config / 'path_files_settings.json')
        # Si hubo una preparación parcial, tampoco reemplazar archivos existentes.
        if carpeta.exists():
            for nombre in ARCHIVOS:
                if (carpeta / nombre).exists():
                    shutil.copyfile(carpeta / nombre, config / nombre)
        preparar_configuracion(etapa, pedir_clave=pedir_clave)
        if not carpeta.exists():
            if origen is not None:
                shutil.copytree(etapa / 'configuracion-importada-original', destino / 'configuracion-importada-original')
            config.rename(carpeta)
        else:
            for nombre in ARCHIVOS:
                try:
                    with (carpeta / nombre).open('xb') as salida:
                        salida.write((config / nombre).read_bytes())
                except FileExistsError:
                    pass
    return destino


def resolver(tipo, valor):
    ruta = Path(valor)
    if tipo == 'images':
        return str(recursos() / 'Public/Images' / ruta.name)
    if tipo == 'config_files':
        return str(datos_usuario() / 'Config/config_files' / ruta.name)
    return str(ruta if ruta.is_absolute() else datos_usuario() / ruta)
