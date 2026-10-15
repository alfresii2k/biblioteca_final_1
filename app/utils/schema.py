"""Inicialización del esquema de base de datos.

`database/schema.sql` es la única fuente de verdad de la estructura.
Al arrancar, si la tabla `usuarios` no existe todavía, se ejecuta ese
archivo completo (crea la BD, las tablas y los datos de ejemplo). Si
ya existe, no se toca nada: así no se pisan datos reales en cada
reinicio del servidor.
"""
import os
import re

import pymysql

from app.utils.db import conectar, conectar_sin_bd, columna_existe, tabla_existe
from app.config import Config

ERROR_BD_INEXISTENTE = 1049  # código MySQL: "Unknown database"


def _dividir_sentencias(sql_texto: str):
    """Separa el script SQL en sentencias individuales por ';'.

    Suficiente para este schema.sql (sin procedimientos ni literales
    con ';' dentro), y evita depender de una librería externa solo
    para esto.
    """
    sin_comentarios = re.sub(r"--.*", "", sql_texto)
    partes = [p.strip() for p in sin_comentarios.split(";")]
    return [p for p in partes if p]


def _base_de_datos_lista():
    """True si la BD ya existe y tiene la tabla `usuarios`."""
    try:
        conn = conectar()
    except pymysql.err.OperationalError as error:
        if error.args and error.args[0] == ERROR_BD_INEXISTENTE:
            return False
        raise
    try:
        return tabla_existe(conn.cursor(), "usuarios")
    finally:
        conn.close()


def _tablas_requeridas():
    """Lista de tablas que la app necesita para funcionar."""
    return {
        "usuarios",
        "libros",
        "ejemplares",
        "apartados",
        "lista_espera",
        "notas",
        "valoraciones",
        "favoritos",
        "contactos",
        "avisos",
    }


def _tablas_faltantes():
    """Devuelve las tablas requeridas que aún no existen en la BD actual."""
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("SHOW TABLES")
        existentes = {fila[next(iter(fila))] for fila in cur.fetchall()}
        return _tablas_requeridas() - existentes
    finally:
        cur.close()
        conn.close()


def _columnas_usuario_faltantes():
    """Añade columnas introducidas por versiones posteriores del registro."""
    columnas = {
        "telefono": "VARCHAR(20) DEFAULT NULL",
        "sede": "ENUM('A','B') DEFAULT NULL",
        "curso": "VARCHAR(10) DEFAULT NULL",
    }
    conn = conectar()
    cur = conn.cursor()
    try:
        faltantes = [
            (columna, definicion)
            for columna, definicion in columnas.items()
            if not columna_existe(cur, "usuarios", columna)
        ]
        for columna, definicion in faltantes:
            cur.execute(f"ALTER TABLE usuarios ADD COLUMN {columna} {definicion}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _columnas_apartado_faltantes():
    """Añade campos del flujo de recogida y extensión sin perder préstamos."""
    conn = conectar()
    cur = conn.cursor()
    try:
        if not columna_existe(cur, "apartados", "fecha_recogida_real"):
            cur.execute(
                "ALTER TABLE apartados ADD COLUMN fecha_recogida_real DATETIME DEFAULT NULL "
                "AFTER fecha_recogida"
            )
        if not columna_existe(cur, "apartados", "renovaciones"):
            cur.execute(
                "ALTER TABLE apartados ADD COLUMN renovaciones TINYINT UNSIGNED "
                "NOT NULL DEFAULT 0 AFTER fecha_devolucion"
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _columna_sede_libro_faltante():
    """Añade la sede obligatoria a libros; los registros existentes pasan a Sede A."""
    conn = conectar()
    cur = conn.cursor()
    try:
        if not columna_existe(cur, "libros", "sede"):
            cur.execute("ALTER TABLE libros ADD COLUMN sede ENUM('A','B') DEFAULT NULL")
            cur.execute("UPDATE libros SET sede = 'A' WHERE sede IS NULL")
            cur.execute("ALTER TABLE libros MODIFY COLUMN sede ENUM('A','B') NOT NULL")
        cur.execute("SHOW INDEX FROM libros WHERE Key_name = 'idx_sede'")
        if not cur.fetchone():
            cur.execute("CREATE INDEX idx_sede ON libros (sede)")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _sentencias_para_tablas(sql_texto, tablas):
    """Recupera solo los CREATE TABLE de las tablas indicadas."""
    sentencias = []
    for parte in _dividir_sentencias(sql_texto):
        match = re.search(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+`?([A-Za-z0-9_]+)`?", parte, re.IGNORECASE)
        if match and match.group(1) in tablas:
            sentencias.append(parte)
    return sentencias


def inicializar_base_datos():
    """Crea el esquema completo la primera vez que se arranca la app.

    Si la BD ya existe, solo crea las tablas faltantes para evitar
    pisar datos reales. Esto corrige bases antiguas que tienen
    `usuarios` pero aún no tienen tablas nuevas como `avisos`.
    """
    ruta_schema = os.path.join(Config.BASE_DIR, "database", "schema.sql")
    with open(ruta_schema, "r", encoding="utf-8") as f:
        sql_texto = f.read()

    if not _base_de_datos_lista():
        conn = conectar_sin_bd()
        cur = conn.cursor()
        try:
            for sentencia in _dividir_sentencias(sql_texto):
                cur.execute(sentencia)
            conn.commit()
            print("✅ Base de datos inicializada desde database/schema.sql")
            return
        except Exception as error:
            conn.rollback()
            print(f"⚠️  No se pudo inicializar la base de datos automáticamente: {error}")
            print("   Ejecuta manualmente: mysql -u root -p < database/schema.sql")
            return
        finally:
            cur.close()
            conn.close()

    faltantes = _tablas_faltantes()
    if not faltantes:
        _columnas_usuario_faltantes()
        _columnas_apartado_faltantes()
        _columna_sede_libro_faltante()
        return

    sentencias = _sentencias_para_tablas(sql_texto, faltantes)
    if not sentencias:
        return

    conn = conectar()
    cur = conn.cursor()
    try:
        for sentencia in sentencias:
            cur.execute(sentencia)
        conn.commit()
        print(f"✅ Tablas faltantes creadas: {', '.join(sorted(faltantes))}")
    except Exception as error:
        conn.rollback()
        print(f"⚠️  No se pudieron crear las tablas faltantes: {error}")
        print("   Comprueba la base de datos y ejecuta el schema.sql manualmente.")
    finally:
        cur.close()
        conn.close()

    _columnas_usuario_faltantes()
    _columnas_apartado_faltantes()
    _columna_sede_libro_faltante()
