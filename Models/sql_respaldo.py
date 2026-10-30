"""Importa solo tablas y datos del panel; nunca interpreta comandos de un cliente SQL."""
import re
import zipfile
from pathlib import PurePosixPath

TABLAS = {'Cortes', 'Entradas', 'MovimientosPens', 'MovsUsuarios', 'PagosPens',
          'Pensionados', 'Usuarios', 'Cambios'}
MAX_ZIP = 256 * 1024 * 1024
MAX_SQL = 2 * 1024 * 1024 * 1024
MAX_SENTENCIA = 32 * 1024 * 1024
TOKEN = re.compile(r"(?P<espacio>\s+)|(?P<cadena>'(?:\\.|''|[^'\\])*'|\"(?:\\.|\"\"|[^\"\\])*\")|(?P<ident>`(?:``|[^`])*`)|(?P<num>0[xX][0-9A-Fa-f]+|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)|(?P<palabra>[A-Za-z_][A-Za-z0-9_$]*)|(?P<signo>[(),.=+\-@])", re.S)


def validar_zip(ruta):
    with zipfile.ZipFile(ruta) as z:
        archivos = [i for i in z.infolist() if not i.is_dir()]
        if len(archivos) != 1:
            raise ValueError('El ZIP debe contener un único SQL.')
        i = archivos[0]
        nombre = PurePosixPath(i.filename.replace('\\', '/'))
        if (nombre.is_absolute() or '..' in nombre.parts or not i.filename.lower().endswith('.sql')
                or i.flag_bits & 1 or i.file_size > MAX_SQL or i.file_size == 0):
            raise ValueError('Contenido ZIP no admitido.')
        if z.testzip() is not None:
            raise ValueError('ZIP dañado.')
        return i.filename


def sentencias(archivo):
    """Separación incremental, respetando cadenas y comentarios de mysqldump."""
    import io
    texto = io.TextIOWrapper(archivo, encoding='utf-8-sig', errors='strict', newline='')
    buffer, tam, quote, bloque, version = [], 0, None, False, False
    try:
        for linea in iter(lambda: texto.readline(MAX_SENTENCIA+1), ''):
            if len(linea) > MAX_SENTENCIA:
                raise ValueError('Línea SQL demasiado grande.')
            i = 0
            while i < len(linea):
                if tam > MAX_SENTENCIA:
                    raise ValueError('Sentencia SQL demasiado grande.')
                c = linea[i]
                dos = linea[i:i+2]
                if bloque:
                    if dos == '*/':
                        bloque = False
                        if version:
                            buffer.append(' ')
                        version = False
                        i += 2
                        continue
                    if version:
                        buffer.append(c)
                        tam += 1
                    i += 1
                    continue
                if quote:
                    buffer.append(c)
                    tam += 1
                    if c == '\\' and quote != '`' and i+1 < len(linea):
                        buffer.append(linea[i+1]); tam += 1; i += 2
                        continue
                    if c == quote:
                        if i+1 < len(linea) and linea[i+1] == quote:
                            buffer.append(linea[i+1]); tam += 1; i += 2
                            continue
                        quote = None
                    i += 1
                    continue
                if dos == '/*':
                    bloque = True
                    version = linea[i+2:i+3] == '!'
                    i += 3 if version else 2
                    if version:
                        while i < len(linea) and linea[i].isdigit(): i += 1
                        # Cabecera sandbox de mariadb-dump: no es SQL y aquí no hay cliente shell.
                        if linea[i:].lstrip().startswith('\\-'):
                            version = False
                    buffer.append(' ')
                    continue
                if c == '#' or (dos == '--' and (i+2 == len(linea) or linea[i+2].isspace())):
                    buffer.append(' ')
                    break
                if c in "'\"`": quote = c
                if c == ';':
                    valor = ''.join(buffer).strip()
                    if valor: yield valor
                    buffer, tam = [], 0
                else:
                    buffer.append(c); tam += 1
                if tam > MAX_SENTENCIA:
                    raise ValueError('Sentencia SQL demasiado grande.')
                i += 1
        if quote or bloque:
            raise ValueError('SQL incompleto.')
        if ''.join(buffer).strip():
            yield ''.join(buffer).strip()
    finally:
        texto.detach()


def tokens(sql):
    resultado, i = [], 0
    while i < len(sql):
        m = TOKEN.match(sql, i)
        if not m:
            raise ValueError('SQL fuera del formato de respaldo admitido.')
        if m.lastgroup != 'espacio': resultado.append((m.lastgroup, m.group()))
        i = m.end()
    return resultado


def validar_sentencia(sql, base):
    t = tokens(sql)
    if not t: return None
    u = [v.upper() if k == 'palabra' else v for k,v in t]
    def identificador(i):
        if i >= len(t) or t[i][0] not in ('palabra', 'ident'):
            raise ValueError('Identificador SQL inválido.')
        return t[i][1].strip('`').replace('``', '`')
    def tabla(i):
        nombre = identificador(i)
        if i+1 < len(t) and t[i+1][1] == '.':
            if nombre.casefold() != base.casefold(): raise ValueError('Referencia a otra base.')
            i += 2; nombre = identificador(i)
        canonicas = {t.casefold():t for t in TABLAS}
        if nombre.casefold() not in canonicas: raise ValueError('Tabla ajena al panel.')
        return canonicas[nombre.casefold()], i+1
    if u[0] == 'SET':
        # No ejecutar SET procedente del correo. La sesión se prepara con código propio.
        texto = ''.join(u[1:])
        permitidas = ('NAMES', 'CHARACTER_SET_CLIENT', 'CHARACTER_SET_RESULTS', 'COLLATION_CONNECTION',
                      'TIME_ZONE', 'UNIQUE_CHECKS', 'FOREIGN_KEY_CHECKS', 'SQL_MODE', 'SQL_NOTES',
                      'AUTOCOMMIT', '@SAVED_CS_CLIENT', '@OLD_', '@@SESSION.', '@@')
        if not any(texto.startswith(p) for p in permitidas):
            raise ValueError('SET no admitido.')
        return None
    if u[0] in ('START', 'COMMIT'):
        if u not in (['START','TRANSACTION'], ['COMMIT']): raise ValueError('Transacción inválida.')
        return None
    if u[0] == 'USE':
        if len(t) != 2 or identificador(1).casefold() != base.casefold(): raise ValueError('Base de origen incorrecta.')
        return None
    if u[:2] == ['CREATE','DATABASE']:
        i = 5 if u[2:5] == ['IF','NOT','EXISTS'] else 2
        if identificador(i).casefold() != base.casefold(): raise ValueError('Base de origen incorrecta.')
        # No ejecutar CREATE DATABASE del adjunto.
        return None
    if u[:2] == ['UNLOCK','TABLES'] and len(t) == 2: return None
    if u[:2] == ['LOCK','TABLES']:
        _, i = tabla(2)
        if u[i:] != ['WRITE']: raise ValueError('LOCK no admitido.')
        return None
    if u[:2] == ['ALTER','TABLE']:
        _, i = tabla(2)
        if u[i:] not in (['DISABLE','KEYS'], ['ENABLE','KEYS']): raise ValueError('ALTER no admitido.')
        return None
    if u[:2] == ['DROP','TABLE']:
        i = 4 if u[2:4] == ['IF','EXISTS'] else 2
        nombre, i = tabla(i)
        if i != len(t): raise ValueError('DROP no admitido.')
        return f'DROP TABLE IF EXISTS `{nombre}`'
    if u[:2] == ['INSERT','INTO']:
        nombre, i = tabla(2)
        inicio = i
        if i < len(t) and u[i] == '(':
            i += 1
            while i < len(t) and u[i] != ')':
                identificador(i); i += 1
                if i < len(t) and u[i] == ',': i += 1
                elif i < len(t) and u[i] != ')': raise ValueError('Columnas inválidas.')
            i += 1
        if i >= len(t) or u[i] != 'VALUES': raise ValueError('Solo INSERT VALUES está permitido.')
        valores = t[i+1:]
        if not valores or valores[0][1] != '(' or valores[-1][1] != ')': raise ValueError('Valores inválidos.')
        for k,v in valores:
            if k in ('cadena','num'): continue
            if v in ('(',')',',','+','-') or (k == 'palabra' and v.upper() in ('NULL','TRUE','FALSE','_BINARY','_UTF8MB4','_UTF8','X','B')): continue
            raise ValueError('Expresiones en INSERT no permitidas.')
        return f'INSERT INTO `{nombre}` ' + ' '.join(v for _,v in t[inicio:])
    if u[:2] == ['CREATE','TABLE']:
        i = 5 if u[2:5] == ['IF','NOT','EXISTS'] else 2
        nombre, i = tabla(i)
        if i >= len(t) or u[i] != '(': raise ValueError('CREATE TABLE no admitido.')
        resto = t[i:]
        peligrosas = {'SELECT','AS','LIKE','DATA','DIRECTORY','INDEX_DIRECTORY','TABLESPACE','CONNECTION',
                      'UNION','INSERT_METHOD','PARTITION','SUBPARTITION','WITH','SYSTEM','PERIOD','DEFINER'}
        if any(k == 'palabra' and v.upper() in peligrosas for k,v in resto):
            raise ValueError('Definición de tabla no admitida.')
        if any(v in ('.','@') for k,v in resto if k != 'cadena'):
            raise ValueError('Referencia externa en tabla.')
        for j, (k,v) in enumerate(resto):
            if k == 'palabra' and v.upper() == 'REFERENCES':
                ref = resto[j+1][1].strip('`')
                canonicas = {t.casefold():t for t in TABLAS}
                if ref.casefold() not in canonicas: raise ValueError('Relación ajena al panel.')
                resto[j+1] = ('ident', '`'+canonicas[ref.casefold()]+'`')
        palabras = set(('PRIMARY KEY UNIQUE FOREIGN REFERENCES CONSTRAINT ON DELETE UPDATE CASCADE RESTRICT '
                        'NO ACTION SET NULL NOT DEFAULT AUTO_INCREMENT UNSIGNED ZEROFILL COMMENT COLLATE '
                        'CHARACTER CHARSET CHAR SET ENGINE INNODB BTREE USING ROW_FORMAT DYNAMIC COMPACT '
                        'COMPRESSED REDUNDANT KEY_BLOCK_SIZE INT INTEGER BIGINT SMALLINT MEDIUMINT TINYINT '
                        'DECIMAL NUMERIC FLOAT DOUBLE REAL BIT BOOL BOOLEAN VARCHAR CHAR TEXT TINYTEXT '
                        'MEDIUMTEXT LONGTEXT BLOB TINYBLOB MEDIUMBLOB LONGBLOB BINARY VARBINARY DATE TIME '
                        'DATETIME TIMESTAMP YEAR ENUM CURRENT_TIMESTAMP INDEX CHECK FULLTEXT SPATIAL '
                        'VISIBLE INVISIBLE ASC DESC').split())
        for j, (k,v) in enumerate(resto):
            if k == 'palabra' and v.upper() not in palabras and not re.fullmatch(r'(?:utf8mb4|utf8|latin1|ascii|binary)(?:_[A-Za-z0-9_]+)?', v, re.I):
                raise ValueError('Expresión de definición no admitida.')
            if k == 'ident' and j+1 < len(resto) and resto[j+1][1] == '(':
                previo = resto[j-1][1].upper() if j else ''
                if previo not in ('KEY', 'INDEX', 'REFERENCES', 'CONSTRAINT'):
                    raise ValueError('Función entre identificadores no admitida.')
        motor = re.search(r'\bENGINE\s*=\s*([A-Za-z0-9_]+)', ' '.join(v for k,v in resto if k != 'cadena'), re.I)
        if not motor or motor.group(1).lower() != 'innodb': raise ValueError('Se requiere InnoDB.')
        return f'CREATE TABLE `{nombre}` ' + ' '.join(v for _,v in resto)
    raise ValueError('Instrucción ajena a un respaldo de tablas y datos.')


def sql_validado(ruta, base):
    nombre = validar_zip(ruta)
    creadas = set()
    with zipfile.ZipFile(ruta) as z, z.open(nombre) as archivo:
        for sentencia in sentencias(archivo):
            segura = validar_sentencia(sentencia, base)
            if segura:
                if segura.startswith('CREATE TABLE '):
                    tabla = segura.split('`')[1]
                    if tabla in creadas: raise ValueError('Tabla repetida en respaldo.')
                    creadas.add(tabla)
                yield segura
    if not (TABLAS - {'Cambios'}).issubset(creadas):
        raise ValueError('Faltan tablas obligatorias en el SQL.')
