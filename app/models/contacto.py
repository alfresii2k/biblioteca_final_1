"""Modelo Contacto: bandeja de entrada del formulario de contacto."""
from app.utils.db import get_db


def crear(id_usuario, nombre, email, mensaje):
    """Guarda un mensaje de contacto asociado al usuario que lo envía."""
    with get_db() as cur:
        cur.execute(
            """INSERT INTO contactos (id_usuario, nombre, email, mensaje)
               VALUES (%s, %s, %s, %s)""",
            (id_usuario, nombre, email, mensaje)
        )


def listar_todos():
    """Devuelve los mensajes recibidos, ordenados del más reciente."""
    with get_db() as cur:
        cur.execute("SELECT * FROM contactos ORDER BY creado_en DESC")
        return cur.fetchall()


def contar():
    """Cuenta los mensajes disponibles en la bandeja de entrada."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM contactos")
        return cur.fetchone()["total"]
