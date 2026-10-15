"""Modelo Libro: catálogo, filtros de búsqueda y estadísticas."""
from app.utils.db import get_db
from app.models import ejemplar as ejemplar_model

COLUMNAS = (
    "titulo, autor, anio, isbn, categoria, descripcion, edicion, editorial, sede, "
    "imagen, seccion, estante, fila"
)


def _construir_condiciones(filtros):
    """Convierte los filtros del catálogo en cláusulas SQL y parámetros seguros."""
    filtros = filtros or {}
    condiciones, parametros = [], []

    if filtros.get("busqueda"):
        condiciones.append(
            "(titulo LIKE %s OR autor LIKE %s OR categoria LIKE %s OR editorial LIKE %s OR seccion LIKE %s)"
        )
        parametros.extend([f"%{filtros['busqueda']}%"] * 5)
    if filtros.get("categoria"):
        condiciones.append("categoria = %s")
        parametros.append(filtros["categoria"])
    if filtros.get("autor"):
        condiciones.append("autor LIKE %s")
        parametros.append(f"%{filtros['autor']}%")
    if filtros.get("editorial"):
        condiciones.append("editorial LIKE %s")
        parametros.append(f"%{filtros['editorial']}%")
    if filtros.get("seccion"):
        condiciones.append("seccion LIKE %s")
        parametros.append(f"%{filtros['seccion']}%")
    if filtros.get("sede"):
        condiciones.append("sede = %s")
        parametros.append(filtros["sede"])

    disponibilidad = filtros.get("disponibilidad")
    if disponibilidad == "disponible":
        condiciones.append("cantidad_disponible > 2")
    elif disponibilidad == "pocas":
        condiciones.append("cantidad_disponible > 0 AND cantidad_disponible <= 2")
    elif disponibilidad == "agotado":
        condiciones.append("cantidad_disponible = 0")

    return condiciones, parametros


def listar(filtros=None, limite=None, offset=0):
    """Devuelve libros filtrados y permite limitar resultados para paginar."""
    condiciones, parametros = _construir_condiciones(filtros)
    consulta = "SELECT * FROM libros"
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += " ORDER BY id DESC"
    if limite is not None:
        consulta += " LIMIT %s OFFSET %s"
        parametros.extend((max(1, int(limite)), max(0, int(offset))))

    with get_db() as cur:
        cur.execute(consulta, tuple(parametros))
        return cur.fetchall()


def listar_inventario(filtros=None, limite=None, offset=0):
    """Lista libros con totales calculados directamente desde sus ejemplares."""
    condiciones, parametros = _construir_condiciones(filtros)
    consulta = """
        SELECT l.*,
               COUNT(e.id) AS cantidad_total,
               SUM(CASE WHEN e.estado = 'disponible' THEN 1 ELSE 0 END)
                   AS cantidad_disponible
        FROM libros l
        LEFT JOIN ejemplares e ON e.id_libro = l.id
    """
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += " GROUP BY l.id ORDER BY l.id DESC"
    if limite is not None:
        consulta += " LIMIT %s OFFSET %s"
        parametros.extend((max(1, int(limite)), max(0, int(offset))))

    with get_db() as cur:
        cur.execute(consulta, tuple(parametros))
        return cur.fetchall()


def obtener_por_id(id_libro):
    """Busca un libro por su identificador o devuelve None si no existe."""
    with get_db() as cur:
        cur.execute("SELECT * FROM libros WHERE id = %s", (id_libro,))
        return cur.fetchone()


def _valores_distintos(columna):
    """Obtiene los valores únicos no vacíos de una columna del catálogo."""
    with get_db() as cur:
        cur.execute(
            f"SELECT DISTINCT {columna} FROM libros WHERE {columna} IS NOT NULL AND {columna} != '' "
            f"ORDER BY {columna}"
        )
        return [fila[columna] for fila in cur.fetchall()]


def categorias_disponibles():
    """Lista las categorías presentes en los libros registrados."""
    return _valores_distintos("categoria")


def editoriales_disponibles():
    """Lista las editoriales presentes en los libros registrados."""
    return _valores_distintos("editorial")


def secciones_disponibles():
    """Lista las secciones de biblioteca usadas por el catálogo."""
    return _valores_distintos("seccion")


def destacados(limite=4):
    """Libros con mejor promedio de valoraciones (los mejor calificados primero)."""
    with get_db() as cur:
        cur.execute(f"""
            SELECT l.*, COALESCE(AVG(v.valor), 0) AS promedio, COUNT(v.id) AS total_valoraciones
            FROM libros l
            LEFT JOIN valoraciones v ON v.id_libro = l.id
            GROUP BY l.id
            ORDER BY promedio DESC, total_valoraciones DESC, l.id DESC
            LIMIT {int(limite)}
        """)
        return cur.fetchall()


def crear(datos, cantidad_total, cantidad_disponible):
    """Inserta un libro y sus ejemplares en una sola transacción."""
    if datos.get("sede") not in {"A", "B"}:
        raise ValueError("Selecciona una sede válida para el libro.")
    with get_db() as cur:
        cur.execute(
            f"INSERT INTO libros ({COLUMNAS}, cantidad_total, cantidad_disponible) "
            f"VALUES ({', '.join(['%s'] * 13)}, %s, %s)",
            (
                datos.get("titulo"), datos.get("autor"), datos.get("anio"), datos.get("isbn"),
                datos.get("categoria"), datos.get("descripcion"), datos.get("edicion"),
                datos.get("editorial"), datos.get("sede"), datos.get("imagen"), datos.get("seccion"),
                datos.get("estante"), datos.get("fila"),
                cantidad_total, cantidad_disponible,
            )
        )
        id_libro = cur.lastrowid
        ejemplar_model.crear_lote(cur, id_libro, datos.get("titulo"), cantidad_total, cantidad_disponible)
        return id_libro


def actualizar(id_libro, datos, cantidad_total, cantidad_disponible):
    """Actualiza la ficha de un libro y sincroniza sus copias físicas."""
    if datos.get("sede") not in {"A", "B"}:
        raise ValueError("Selecciona una sede válida para el libro.")
    with get_db() as cur:
        cur.execute(
            f"""UPDATE libros SET
                    titulo=%s, autor=%s, anio=%s, isbn=%s, categoria=%s, descripcion=%s,
                    edicion=%s, editorial=%s, sede=%s, imagen=%s, seccion=%s, estante=%s, fila=%s,
                    cantidad_total=%s, cantidad_disponible=%s
                WHERE id=%s""",
            (
                datos.get("titulo"), datos.get("autor"), datos.get("anio"), datos.get("isbn"),
                datos.get("categoria"), datos.get("descripcion"), datos.get("edicion"),
                datos.get("editorial"), datos.get("sede"), datos.get("imagen"), datos.get("seccion"),
                datos.get("estante"), datos.get("fila"),
                cantidad_total, cantidad_disponible, id_libro,
            )
        )
        ejemplar_model.sincronizar(cur, id_libro, datos.get("titulo"), cantidad_total, cantidad_disponible)


def eliminar(id_libro):
    """Elimina el libro y devuelve sus datos previos para limpiar recursos."""
    with get_db() as cur:
        cur.execute("SELECT imagen FROM libros WHERE id = %s", (id_libro,))
        libro = cur.fetchone()
        cur.execute("DELETE FROM libros WHERE id = %s", (id_libro,))
        return libro


def alternar_disponibilidad(id_libro):
    """Pone en 0 o restaura la cantidad_disponible (usado por el botón admin)."""
    with get_db() as cur:
        cur.execute("SELECT cantidad_total, cantidad_disponible FROM libros WHERE id = %s", (id_libro,))
        libro = cur.fetchone()
        if not libro:
            return False

        if libro["cantidad_disponible"] > 0:
            cur.execute("UPDATE libros SET cantidad_disponible = 0 WHERE id = %s", (id_libro,))
            cur.execute(
                "UPDATE ejemplares SET estado = 'danado' WHERE id_libro = %s AND estado = 'disponible'",
                (id_libro,)
            )
        else:
            nueva_disp = libro["cantidad_total"]
            cur.execute("UPDATE libros SET cantidad_disponible = %s WHERE id = %s", (nueva_disp, id_libro))
            cur.execute(
                "UPDATE ejemplares SET estado = 'disponible' WHERE id_libro = %s AND estado = 'danado'",
                (id_libro,)
            )
        return True


# ---------------- Estadísticas para el panel admin ----------------

def contar(filtros=None):
    """Cuenta libros que coinciden con los filtros recibidos."""
    condiciones, parametros = _construir_condiciones(filtros)
    consulta = "SELECT COUNT(*) AS total FROM libros"
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    with get_db() as cur:
        cur.execute(consulta, tuple(parametros))
        return cur.fetchone()["total"]


def contar_categorias():
    """Cuenta las categorías distintas que tienen libros registrados."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(DISTINCT categoria) AS total FROM libros")
        return cur.fetchone()["total"]


def contar_agotados():
    """Cuenta los libros cuya disponibilidad actual es cero."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM libros WHERE cantidad_disponible = 0")
        return cur.fetchone()["total"]


def mas_apartados(limite=5):
    """Devuelve los libros más solicitados para el resumen administrativo."""
    with get_db() as cur:
        cur.execute(f"""
            SELECT l.titulo, COUNT(a.id) AS veces_apartado
            FROM apartados a
            JOIN ejemplares e ON a.id_ejemplar = e.id
            JOIN libros l ON e.id_libro = l.id
            GROUP BY l.id
            ORDER BY veces_apartado DESC
            LIMIT {int(limite)}
        """)
        return cur.fetchall()


def mejor_valorados(limite=5):
    """Devuelve los libros con mejores promedios de valoración."""
    with get_db() as cur:
        cur.execute(f"""
            SELECT l.titulo, COALESCE(AVG(v.valor), 0) AS promedio, COUNT(v.id) AS votos
            FROM valoraciones v
            JOIN libros l ON v.id_libro = l.id
            GROUP BY l.id
            ORDER BY promedio DESC, votos DESC
            LIMIT {int(limite)}
        """)
        return cur.fetchall()


def categorias_populares(limite=5):
    """Ordena las categorías por cantidad total de préstamos."""
    with get_db() as cur:
        cur.execute(f"""
            SELECT l.categoria, COUNT(a.id) AS monto
            FROM apartados a
            JOIN ejemplares e ON a.id_ejemplar = e.id
            JOIN libros l ON e.id_libro = l.id
            GROUP BY l.categoria
            ORDER BY monto DESC
            LIMIT {int(limite)}
        """)
        return cur.fetchall()


def conteo_por_categoria():
    """Devuelve la cantidad de títulos registrada en cada categoría."""
    with get_db() as cur:
        cur.execute("SELECT categoria, COUNT(*) AS total FROM libros GROUP BY categoria ORDER BY categoria")
        return cur.fetchall()
