"""Modelo Nota: anotaciones privadas del usuario sobre un libro."""
from app.utils.db import get_db


def crear(id_libro, id_usuario, nota_titulo, nota):
    """Guarda una anotación privada del usuario sobre un libro."""
    with get_db() as cur:
        cur.execute(
            """INSERT INTO notas (id_libro, id_usuario, nota_titulo, nota)
               VALUES (%s, %s, %s, %s)""",
            (id_libro, id_usuario, nota_titulo, nota)
        )


def listar_por_libro_y_usuario(id_libro, id_usuario):
    """Lista notas con contenido de un usuario para el libro indicado."""
    with get_db() as cur:
        cur.execute("""
            SELECT nota_titulo, nota, creado_en
            FROM notas
            WHERE id_libro = %s AND id_usuario = %s AND nota IS NOT NULL AND nota != ''
            ORDER BY creado_en DESC
        """, (id_libro, id_usuario))
        return cur.fetchall()


def listar_por_usuario(id_usuario):
    """Lista las notas del usuario junto con los datos de cada libro."""
    with get_db() as cur:
        cur.execute("""
            SELECT n.id AS nota_id, n.nota, n.nota_titulo, n.creado_en,
                   l.id AS libro_id, l.titulo AS libro_titulo, l.autor AS libro_autor, l.imagen AS libro_imagen
            FROM notas n
            JOIN libros l ON n.id_libro = l.id
            WHERE n.id_usuario = %s AND n.nota IS NOT NULL AND n.nota != ''
            ORDER BY n.creado_en DESC
        """, (id_usuario,))
        return cur.fetchall()


def obtener_por_id_y_usuario(id_nota, id_usuario):
    """Busca una nota solo si pertenece al usuario que la solicita."""
    with get_db() as cur:
        cur.execute("""
            SELECT n.id, n.id_libro, n.nota, n.nota_titulo,
                   l.titulo AS libro_titulo, l.autor AS libro_autor
            FROM notas n
            JOIN libros l ON n.id_libro = l.id
            WHERE n.id = %s AND n.id_usuario = %s
        """, (id_nota, id_usuario))
        return cur.fetchone()


def actualizar(id_nota, id_usuario, nota_titulo, nota):
    """Actualiza una nota propia e indica si se modificó alguna fila."""
    with get_db() as cur:
        cur.execute(
            "UPDATE notas SET nota_titulo = %s, nota = %s WHERE id = %s AND id_usuario = %s",
            (nota_titulo, nota, id_nota, id_usuario)
        )
        return cur.rowcount > 0


def eliminar(id_nota, id_usuario):
    """Elimina una nota propia e indica si se eliminó alguna fila."""
    with get_db() as cur:
        cur.execute(
            "DELETE FROM notas WHERE id = %s AND id_usuario = %s",
            (id_nota, id_usuario)
        )
        return cur.rowcount > 0
