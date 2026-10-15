"""Modelo Aviso: cartelera de anuncios de la página principal."""
from app.utils.db import get_db


def listar_activos():
    """Devuelve los avisos visibles, del más reciente al más antiguo."""
    with get_db() as cur:
        cur.execute("SELECT * FROM avisos WHERE activo = 1 ORDER BY creado_en DESC")
        return cur.fetchall()


def listar_todos():
    """Devuelve todos los avisos para el panel de administración."""
    with get_db() as cur:
        cur.execute("SELECT * FROM avisos ORDER BY creado_en DESC")
        return cur.fetchall()


def obtener_por_id(id_aviso):
    """Busca un aviso por su identificador o devuelve None si no existe."""
    with get_db() as cur:
        cur.execute("SELECT * FROM avisos WHERE id = %s", (id_aviso,))
        return cur.fetchone()


def crear(titulo, contenido, imagen=None):
    """Inserta un aviso y devuelve el identificador asignado por la base de datos."""
    with get_db() as cur:
        cur.execute(
            "INSERT INTO avisos (titulo, contenido, imagen) VALUES (%s, %s, %s)",
            (titulo, contenido or "", imagen)
        )
        return cur.lastrowid


def actualizar(id_aviso, titulo, contenido, imagen=None):
    """Actualiza el texto del aviso y reemplaza la imagen solo si se proporciona."""
    with get_db() as cur:
        if imagen:
            cur.execute(
                "UPDATE avisos SET titulo = %s, contenido = %s, imagen = %s WHERE id = %s",
                (titulo, contenido or "", imagen, id_aviso)
            )
        else:
            cur.execute(
                "UPDATE avisos SET titulo = %s, contenido = %s WHERE id = %s",
                (titulo, contenido or "", id_aviso)
            )


def alternar_activo(id_aviso):
    """Invierte el estado activo del aviso indicado."""
    with get_db() as cur:
        cur.execute("UPDATE avisos SET activo = 1 - activo WHERE id = %s", (id_aviso,))


def eliminar(id_aviso):
    """Elimina de la base de datos el aviso indicado."""
    with get_db() as cur:
        cur.execute("DELETE FROM avisos WHERE id = %s", (id_aviso,))
