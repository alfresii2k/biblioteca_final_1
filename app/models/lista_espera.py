"""Modelo ListaEspera: turno FIFO por libro cuando no hay ejemplares."""
from app.utils.db import get_db


def libro_tiene_disponibilidad(id_libro):
    """Comprueba si queda al menos una copia disponible del libro."""
    with get_db() as cur:
        cur.execute("SELECT cantidad_disponible FROM libros WHERE id = %s", (id_libro,))
        libro = cur.fetchone()
        return bool(libro) and libro["cantidad_disponible"] > 0


def ya_esta_en_espera(id_libro, id_usuario):
    """Comprueba si el usuario ya ocupa un turno para ese libro."""
    with get_db() as cur:
        cur.execute(
            "SELECT id FROM lista_espera WHERE id_libro = %s AND id_usuario = %s",
            (id_libro, id_usuario)
        )
        return cur.fetchone() is not None


def unirse(id_libro, id_usuario):
    """Añade al usuario al final de la lista de espera del libro."""
    with get_db() as cur:
        cur.execute(
            "INSERT INTO lista_espera (id_libro, id_usuario) VALUES (%s, %s)",
            (id_libro, id_usuario)
        )


def listar_por_usuario(id_usuario):
    """Lista los turnos de espera del usuario con disponibilidad actual."""
    with get_db() as cur:
        cur.execute("""
            SELECT w.id AS espera_id, w.fecha_solicitud, w.estado,
                   l.id AS libro_id, l.titulo AS libro_titulo, l.autor AS libro_autor,
                   l.cantidad_disponible
            FROM lista_espera w
            JOIN libros l ON w.id_libro = l.id
            WHERE w.id_usuario = %s
            ORDER BY w.fecha_solicitud ASC
        """, (id_usuario,))
        return cur.fetchall()


def listar_todos(sede=None, limite=None, offset=0):
    """Lista turnos de espera junto con los datos de libros y usuarios."""
    with get_db() as cur:
        consulta = """
            SELECT w.id, w.id_libro, w.id_usuario, w.fecha_solicitud AS creado_en, w.estado,
                   l.titulo AS libro_titulo, l.autor AS libro_autor, l.categoria, l.imagen,
                   l.cantidad_disponible,
                   u.nombre AS usuario_nombre, u.apellido AS usuario_apellido,
                   u.identificacion, u.sede AS usuario_sede
            FROM lista_espera w
            JOIN libros l ON w.id_libro = l.id
            JOIN usuarios u ON w.id_usuario = u.id
        """
        parametros = ()
        if sede:
            consulta += " WHERE l.sede = %s"
            parametros = (sede,)
        consulta += " ORDER BY w.fecha_solicitud ASC"
        if limite is not None:
            consulta += " LIMIT %s OFFSET %s"
            parametros += (limite, offset)
        cur.execute(consulta, parametros)
        return cur.fetchall()


def contar_todos(sede=None):
    """Cuenta los turnos de espera, opcionalmente filtrados por sede."""
    consulta = """
        SELECT COUNT(*) AS total
        FROM lista_espera w
        JOIN libros l ON l.id = w.id_libro
    """
    parametros = ()
    if sede:
        consulta += " WHERE l.sede = %s"
        parametros = (sede,)
    with get_db() as cur:
        cur.execute(consulta, parametros)
        return cur.fetchone()["total"]
