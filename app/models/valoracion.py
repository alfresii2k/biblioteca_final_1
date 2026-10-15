"""Modelo Valoracion: calificación de 1 a 5 estrellas por usuario y libro."""
from app.utils.db import get_db


def ya_valoro(id_libro, id_usuario):
    """Comprueba si el usuario ya valoró el libro para evitar duplicados."""
    with get_db() as cur:
        cur.execute(
            "SELECT id FROM valoraciones WHERE id_libro = %s AND id_usuario = %s",
            (id_libro, id_usuario)
        )
        return cur.fetchone() is not None


def crear(id_libro, id_usuario, valor, comentario=None):
    """Guarda la puntuación y el comentario opcional del usuario."""
    with get_db() as cur:
        cur.execute(
            "INSERT INTO valoraciones (id_libro, id_usuario, valor, comentario) VALUES (%s, %s, %s, %s)",
            (id_libro, id_usuario, valor, comentario)
        )


def valoraciones_de_usuario(id_usuario):
    """Devuelve {id_libro: valor} con todo lo que ya calificó ese usuario."""
    with get_db() as cur:
        cur.execute("SELECT id_libro, valor FROM valoraciones WHERE id_usuario = %s", (id_usuario,))
        return {fila["id_libro"]: fila["valor"] for fila in cur.fetchall()}


def promedio_y_total(id_libro):
    """Devuelve el promedio de estrellas y el número de valoraciones."""
    with get_db() as cur:
        cur.execute(
            "SELECT COALESCE(AVG(valor), 0) AS promedio, COUNT(*) AS total "
            "FROM valoraciones WHERE id_libro = %s",
            (id_libro,)
        )
        return cur.fetchone()


def listar_de_libro(id_libro, limite=10):
    """Reseñas con comentario, más recientes primero, con el nombre de quien la escribió."""
    with get_db() as cur:
        cur.execute(
            f"""SELECT v.valor, v.comentario, v.creado_en, u.nombre, u.apellido
                FROM valoraciones v
                JOIN usuarios u ON u.id = v.id_usuario
                WHERE v.id_libro = %s AND v.comentario IS NOT NULL AND v.comentario != ''
                ORDER BY v.creado_en DESC
                LIMIT {int(limite)}""",
            (id_libro,)
        )
        return cur.fetchall()
