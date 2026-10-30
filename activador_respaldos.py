import re
import pymysql


TABLAS_OBLIGATORIAS = {
    "Cortes",
    "Entradas",
    "MovimientosPens",
    "MovsUsuarios",
    "PagosPens",
    "Pensionados",
    "Usuarios",
}

RELACIONES_OBLIGATORIAS = {
    ("PagosPens", "Pensionados"),
    ("MovsUsuarios", "Usuarios"),
    ("MovimientosPens", "Pensionados"),
}


def validar_nombre(nombre):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", nombre):
        raise ValueError(f"Nombre de base no permitido: {nombre}")
    return nombre


def validar_base_temporal(conexion, base):
    validar_nombre(base)

    if not base.startswith("panel_stage_db_"):
        raise ValueError(
            "Solo se permite validar bases temporales del Panel"
        )

    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT TABLE_NAME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_TYPE = 'BASE TABLE'
        """, (base,))

        tablas = {fila[0] for fila in cursor.fetchall()}

        faltantes = TABLAS_OBLIGATORIAS - tablas

        if faltantes:
            raise RuntimeError(
                f"Faltan tablas obligatorias: {sorted(faltantes)}"
            )

        cursor.execute("""
            SELECT TABLE_NAME, REFERENCED_TABLE_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (base,))

        relaciones = set(cursor.fetchall())

        faltantes = RELACIONES_OBLIGATORIAS - relaciones

        if faltantes:
            raise RuntimeError(
                f"Faltan relaciones: {sorted(faltantes)}"
            )

        cursor.execute("""
            SELECT TABLE_NAME, ENGINE
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_TYPE = 'BASE TABLE'
        """, (base,))

        motores = dict(cursor.fetchall())

        incorrectos = [
            tabla for tabla, motor in motores.items()
            if motor != "InnoDB"
        ]

        if incorrectos:
            raise RuntimeError(
                f"Tablas que no utilizan InnoDB: {incorrectos}"
            )

    return {
        "base": base,
        "tablas": sorted(tablas),
        "relaciones": len(relaciones),
        "resultado": "VALIDADA",
    }


def verificar_integridad(conexion, base):
    """Comprueba datos y relaciones sin modificar las tablas."""
    validar_base_temporal(conexion, base)

    relaciones = (
        ("PagosPens", "Pensionados"),
        ("MovsUsuarios", "Usuarios"),
        ("MovimientosPens", "Pensionados"),
    )

    resultado = {}

    with conexion.cursor() as cursor:
        for tabla in sorted(TABLAS_OBLIGATORIAS):
            cursor.execute(f"SELECT COUNT(*) FROM `{base}`.`{tabla}`")
            resultado[tabla] = cursor.fetchone()[0]

        cursor.execute("""
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (base,))

        claves = cursor.fetchall()

        for tabla, principal in relaciones:
            if not any(
                fila[0] == tabla and fila[2] == principal
                for fila in claves
            ):
                raise RuntimeError(
                    f"Relación no encontrada: {tabla} -> {principal}"
                )

    return resultado


if __name__ == "__main__":
    print("Módulo de validación instalado correctamente.")
    print("No se modificó ninguna base de datos.")
