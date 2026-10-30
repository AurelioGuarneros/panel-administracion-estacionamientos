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


def _identidades(registro):
    """Espacios separados: nombre/alias, base, id y clave histórica."""
    identidades = {('nombre', n.strip().casefold()) for n in
                   [registro['name_config'], *registro.get('nombres_anteriores', [])]}
    identidades.add(('base', registro['database'].strip().casefold()))
    for campo in ('id', 'clave_respaldo'):
        if registro.get(campo): identidades.add((campo, registro[campo].strip().casefold()))
    return identidades


def validar_local(datos):
    if not isinstance(datos, dict) or not isinstance(datos.get('settings'), list) or not isinstance(datos.get('estacionamientos_eliminados', []), list):
        raise ValueError('Catálogo local inválido.')
    identidades, correos = set(), set()
    administradores = 0
    for grupo in ('settings', 'estacionamientos_eliminados'):
        for r in datos.get(grupo, []):
            if not isinstance(r, dict) or not all(isinstance(r.get(k), str) and r[k].strip() for k in ('name_config', 'database')):
                raise ValueError('Identidad local incompleta.')
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', r['database']): raise ValueError('Base local inválida.')
            if 'activo' in r and type(r['activo']) is not bool: raise ValueError('Estado local inválido.')
            aliases = r.get('nombres_anteriores', [])
            if not isinstance(aliases, list) or any(not isinstance(n,str) or not n.strip() for n in aliases): raise ValueError('Alias local inválido.')
            for campo in ('id', 'clave_respaldo'):
                if campo in r and (not isinstance(r[campo],str) or not r[campo].strip()): raise ValueError('Identificador local inválido.')
            propias = _identidades(r)
            if propias & identidades: raise ValueError('Identidades locales duplicadas o retiradas en uso.')
            identidades.update(propias)
            if r['name_config'] == 'Admin' and grupo == 'settings': administradores += 1
            elif grupo == 'settings' and r.get('email'):
                if not isinstance(r['email'],str): raise ValueError('Remitente local inválido.')
                correo = r['email'].strip().casefold()
                if correo in correos: raise ValueError('Remitente local duplicado.')
                correos.add(correo)
    if administradores != 1: raise ValueError('Se requiere conservar un único registro Admin.')
    return datos


def recuperar_catalogo(local, catalogo, plantilla):
    """Plan puro e idempotente; no reescribe registros locales ni libera retirados."""
    validar_catalogo(catalogo)
    validar_local(local)
    resultado = copy.deepcopy(local)
    resumen = {'agregados': [], 'retirados': [], 'ejemplos_eliminados': [], 'omitidos': []}
    ejemplos = [r for r in plantilla['settings'] if r['name_config'] != 'Admin']
    conservados = []
    for r in resultado['settings']:
        if any(r == ejemplo for ejemplo in ejemplos):
            resumen['ejemplos_eliminados'].append(r['database'])
        else: conservados.append(r)
    resultado['settings'] = conservados
    resultado.setdefault('estacionamientos_eliminados', [])
    # Reservar los retirados distribuidos antes de incorporar registros activos.
    for r in catalogo['estacionamientos_eliminados']:
        identidades = _identidades(r)
        if any(identidades & _identidades(a) for a in resultado['settings']):
            raise ValueError('Un retirado del catálogo inicial coincide con un registro local; requiere revisión.')
        coincidencias = [a for a in resultado['estacionamientos_eliminados'] if identidades & _identidades(a)]
        if coincidencias:
            if len(coincidencias) != 1 or coincidencias[0]['database'].casefold() != r['database'].casefold():
                raise ValueError('Referencia retirada ambigua; requiere revisión.')
            existente = coincidencias[0]
            reservados = {n.strip().casefold() for n in [existente['name_config'], *existente.get('nombres_anteriores', [])]}
            for nombre in [r['name_config'], *r.get('nombres_anteriores', [])]:
                if nombre.strip().casefold() not in reservados:
                    existente.setdefault('nombres_anteriores', []).append(nombre)
                    reservados.add(nombre.strip().casefold())
        else:
            resultado['estacionamientos_eliminados'].append(copy.deepcopy(r))
            resumen['retirados'].append(r['database'])
    nuevos = configurar_catalogo(plantilla, catalogo)['settings'][1:]
    for r in nuevos:
        propias = _identidades(r)
        retirados = [a for a in resultado['estacionamientos_eliminados'] if propias & _identidades(a)]
        coincidencias = [a for a in resultado['settings'] if propias & _identidades(a)]
        if len(coincidencias) > 1 or (retirados and coincidencias):
            raise ValueError('La incorporación tiene identidades ambiguas; requiere revisión.')
        if retirados or coincidencias:
            resumen['omitidos'].append(r['database'])
            continue
        if any(str(a.get('email','')).strip().casefold() == r['email'].casefold() for a in resultado['settings'] if a['name_config'] != 'Admin'):
            raise ValueError('Un remitente del catálogo inicial está asignado a otra identidad local.')
        resultado['settings'].append(r)
        resumen['agregados'].append(r['database'])
    validar_local(resultado)
    return resultado, resumen
