"""Catálogo público sin conexiones ni secretos; validación antes de instalar."""
import copy
import re

CAMPOS = {'id', 'name_config', 'database', 'email', 'activo',
          'nombres_anteriores', 'clave_respaldo'}
RETIRADOS = CAMPOS - {'email', 'activo'}


def validar_catalogo(datos):
    if not isinstance(datos, dict) or set(datos) != {'version', 'settings', 'estacionamientos_eliminados'} or datos['version'] != 1:
        raise ValueError('Formato de catálogo inicial inválido.')
    nombres, bases, ids, remitentes, claves = set(), set(), set(), set(), set()
    for grupo, campos in (('settings', CAMPOS), ('estacionamientos_eliminados', RETIRADOS)):
        registros = datos[grupo]
        if not isinstance(registros, list):
            raise ValueError('Lista de catálogo inválida.')
        for r in registros:
            if not isinstance(r, dict) or set(r) - campos:
                raise ValueError('Campo no distribuible en el catálogo.')
            for campo in ('id', 'name_config', 'database'):
                if not isinstance(r.get(campo), str) or not r[campo].strip():
                    raise ValueError('Identidad incompleta.')
            if not re.fullmatch(r'db_[A-Za-z0-9_]+', r['database']):
                raise ValueError('Base inválida.')
            aliases = r.get('nombres_anteriores', [])
            if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
                raise ValueError('Referencias históricas inválidas.')
            for nombre in [r['name_config'], *aliases]:
                normal = nombre.strip().casefold()
                if normal == 'admin' or normal in nombres:
                    raise ValueError('Nombre duplicado o reservado.')
                nombres.add(normal)
            for campo, usados in (('database', bases), ('id', ids), ('clave_respaldo', claves)):
                valor = r.get(campo, r['name_config'])
                if not isinstance(valor, str) or not valor.strip() or valor.strip().casefold() in usados:
                    raise ValueError('Identificador duplicado o inválido.')
                usados.add(valor.strip().casefold())
            if grupo == 'settings':
                if type(r.get('activo')) is not bool:
                    raise ValueError('Estado inválido.')
                correo = r.get('email', '')
                if not isinstance(correo, str) or not re.fullmatch(r'[^\s@<>(),;]+@[^\s@<>(),;]+\.[^\s@<>(),;]+', correo):
                    raise ValueError('Remitente inválido.')
                if correo.strip().casefold() in remitentes:
                    raise ValueError('Remitente duplicado.')
                remitentes.add(correo.strip().casefold())
    return datos


def configurar_catalogo(plantilla, catalogo):
    validar_catalogo(catalogo)
    # Solo se conserva el Admin ficticio; no se publica ni hereda una conexión real.
    administradores = [r for r in plantilla['settings'] if r['name_config'] == 'Admin']
    if len(administradores) != 1:
        raise ValueError('Plantilla Admin inválida.')
    conexion = {k: administradores[0][k] for k in ('host', 'user', 'password', 'iv')}
    registros = []
    for r in catalogo['settings']:
        nuevo = dict(conexion, **copy.deepcopy(r))
        nuevo.update(actualizacion_automatica=False, configuracion_verificada=False)
        registros.append(nuevo)
    return {'settings': copy.deepcopy(administradores) + registros,
            'estacionamientos_eliminados': copy.deepcopy(catalogo['estacionamientos_eliminados'])}
