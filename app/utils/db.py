"""Conexión a MySQL y utilidades comunes de acceso a datos.

Expone `get_db()`, un context manager que entrega un cursor y se
encarga de hacer commit al salir sin errores, rollback si algo falla,
y cerrar siempre la conexión. Todos los modelos en app/models/ lo usan
en vez de abrir/cerrar conexiones a mano en cada función.
"""
import os
from contextlib import contextmanager

import pymysql

from app.config import ConfigBD, Config

ERROR_BD_INEXISTENTE = 1049  # código MySQL: "Unknown database"


def conectar():
    """Abre una nueva conexión a MySQL usando variables de entorno o ConfigBD."""
    return pymysql.connect(
        host=os.getenv('DB_HOST', ConfigBD.HOST),
        port=int(os.getenv('DB_PORT', ConfigBD.PUERTO)),
        user=os.getenv('DB_USER', ConfigBD.USUARIO),
        password=os.getenv('DB_PASSWORD', ConfigBD.CONTRASENA),
        database=os.getenv('DB_NAME', ConfigBD.NOMBRE),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def conectar_sin_bd():
    """Conexión SIN seleccionar base de datos (usada por schema.py si es necesario)."""
    return pymysql.connect(
        host=os.getenv('DB_HOST', ConfigBD.HOST),
        port=int(os.getenv('DB_PORT', ConfigBD.PUERTO)),
        user=os.getenv('DB_USER', ConfigBD.USUARIO),
        password=os.getenv('DB_PASSWORD', ConfigBD.CONTRASENA),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


@contextmanager
def get_db():
    """Context manager: entrega un cursor listo para usar."""
    conn = conectar()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def allowed_file(filename):
    """Valida que la extensión del archivo subido esté permitida."""
    return bool(filename) and "." in filename and \
        filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def columna_existe(cur, tabla, columna):
    """Comprueba en el catálogo de MySQL si una tabla tiene esa columna."""
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (tabla, columna)
    )
    return cur.fetchone()["cnt"] > 0


def tabla_existe(cur, tabla):
    """Comprueba si la tabla indicada existe en la base seleccionada."""
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
        (tabla,)
    )
    return cur.fetchone()["cnt"] > 0