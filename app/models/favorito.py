"""Modelo Favorito: libros marcados como favoritos por un usuario."""
from app.utils.db import get_db


def ids_favoritos_de_usuario(id_usuario):
    """Devuelve como conjunto los identificadores de libros favoritos del usuario."""
    with get_db() as cur:
        cur.execute("SELECT id_libro FROM favoritos WHERE id_usuario = %s", (id_usuario,))
        return {fila["id_libro"] for fila in cur.fetchall()}


def listar_por_usuario(id_usuario):
    """Lista los libros favoritos del usuario, del último agregado al primero."""
    with get_db() as cur:
        cur.execute("""
            SELECT f.id AS favorito_id, l.*
            FROM favoritos f
            JOIN libros l ON f.id_libro = l.id
            WHERE f.id_usuario = %s
            ORDER BY f.creado_en DESC
        """, (id_usuario,))
        return cur.fetchall()


def existe(id_libro, id_usuario):
    """Indica si el libro ya está en la lista de favoritos del usuario."""
    with get_db() as cur:
        cur.execute(
            "SELECT id FROM favoritos WHERE id_libro = %s AND id_usuario = %s",
            (id_libro, id_usuario)
        )
        return cur.fetchone() is not None


def agregar(id_libro, id_usuario):
    """Guarda una relación de favorito entre el usuario y el libro."""
    with get_db() as cur:
        cur.execute(
            "INSERT INTO favoritos (id_libro, id_usuario) VALUES (%s, %s)",
            (id_libro, id_usuario)
        )


def quitar(id_libro, id_usuario):
    """Elimina de favoritos la relación entre el usuario y el libro."""
    with get_db() as cur:
        cur.execute(
            "DELETE FROM favoritos WHERE id_libro = %s AND id_usuario = %s",
            (id_libro, id_usuario)
        )
