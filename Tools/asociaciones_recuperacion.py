"""Plan de ampliación de estaciones; preserva íntegros IMAP, cuentas y contraseñas."""
import copy
import re
from Tools.catalogo_inicial import validar_local


def ampliar_asociaciones(perfil, catalogo):
    validar_local(catalogo)
    nuevo = copy.deepcopy(perfil)
    anteriores = nuevo['estaciones']
    agregadas = []
    for r in catalogo['settings']:
        if r['name_config'] == 'Admin' or not r.get('activo', True): continue
        base, email = r['database'], r.get('email', '')
        if not re.fullmatch(r'db_[A-Za-z0-9_]+',base) or not re.fullmatch(r'[A-Za-z0-9_.+%\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}',email):
            raise ValueError('Asociación no autorizable; requiere revisión.')
        por_base = [a for a in anteriores if a['database'].casefold() == base.casefold()]
        por_email = [a for a in anteriores if a['email'].casefold() == email.casefold()]
        if por_base:
            if len(por_base) != 1 or por_base[0]['database'] != base or por_base[0]['email'].casefold() != email.casefold():
                raise ValueError('Una base ya autorizada tiene otra asociación; se conserva sin cambios.')
            continue
        if por_email: raise ValueError('Un remitente autorizado corresponde a otra base; se conserva sin cambios.')
        nueva = {k:copy.deepcopy(r[k]) for k in ('id','name_config','database','email','nombres_anteriores','clave_respaldo') if k in r}
        nueva['activo'] = True
        anteriores.append(nueva)
        agregadas.append(base)
    assert nuevo['imap'] == perfil['imap'] and nuevo['mariadb'] == perfil['mariadb']
    return nuevo, agregadas


def reglas_sudoers(usuario, bases):
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*', usuario): raise ValueError('Usuario Linux inválido.')
    if any(not re.fullmatch(r'db_[A-Za-z0-9_]+',b) for b in bases): raise ValueError('Base inválida.')
    return ('\n'.join(usuario+' ALL=(root) NOPASSWD: /usr/local/sbin/panel-activar-seguro ^'+b+' [0-9a-f]{64}$' for b in bases)+'\n').encode()
