"""Modelo Apartado: préstamo de un ejemplar concreto a un usuario.

`crear()` concentra en una sola transacción todo lo que antes estaba
suelto en la ruta: elegir el ejemplar disponible, insertar el
apartado, marcar el ejemplar como prestado y descontar el contador de
`libros.cantidad_disponible`. Así nunca quedan esos pasos a medias.
"""
from app.utils.db import get_db
from app.models import ejemplar as ejemplar_model


class SinDisponibilidad(Exception):
    """No hay ejemplares libres de ese libro."""


def crear(id_libro, id_usuario, curso=None, nota_titulo=None, nota=None,
          fecha_recogida=None, fecha_entrega=None):
    """Aparta una copia libre y actualiza su estado junto con el contador del libro."""
    with get_db() as cur:
        ejemplar = ejemplar_model.buscar_disponible(cur, id_libro)
        if not ejemplar:
            raise SinDisponibilidad()

        cur.execute(
            """INSERT INTO apartados
                    (id_ejemplar, id_usuario, curso, nota_titulo, nota,
                    fecha_recogida, fecha_entrega, fecha, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 'prestado')""",
            (ejemplar["id"], id_usuario, curso, nota_titulo, nota,
               fecha_recogida, fecha_entrega)
        )
        cur.execute("UPDATE ejemplares SET estado = 'prestado' WHERE id = %s", (ejemplar["id"],))
        cur.execute(
            "UPDATE libros SET cantidad_disponible = cantidad_disponible - 1 "
            "WHERE id = %s AND cantidad_disponible > 0",
            (id_libro,)
        )
        if cur.rowcount != 1:
            raise SinDisponibilidad()
        return ejemplar["codigo_inventario"]


def reclamar(id_apartado):
    """Registra que el estudiante recogió el ejemplar, sin cerrarlo."""
    with get_db() as cur:
        cur.execute(
            """UPDATE apartados
               SET fecha_recogida_real = NOW()
               WHERE id = %s AND estado = 'prestado' AND fecha_recogida_real IS NULL""",
            (id_apartado,)
        )
        return cur.rowcount > 0


def usuario_reclamo_libro(id_libro, id_usuario):
    """Comprueba si el usuario ya recogió un ejemplar de este libro."""
    with get_db() as cur:
        cur.execute(
            """SELECT a.id
               FROM apartados a
               JOIN ejemplares e ON e.id = a.id_ejemplar
               WHERE e.id_libro = %s AND a.id_usuario = %s
                 AND a.fecha_recogida_real IS NOT NULL
               LIMIT 1""",
            (id_libro, id_usuario)
        )
        return cur.fetchone() is not None


def devolver(id_apartado):
    """Marca el préstamo como devuelto y libera el ejemplar."""
    with get_db() as cur:
        cur.execute(
            "SELECT id_ejemplar FROM apartados WHERE id = %s AND estado = 'prestado'",
            (id_apartado,)
        )
        apartado = cur.fetchone()
        if not apartado:
            return False

        cur.execute(
            "UPDATE apartados SET estado = 'devuelto', fecha_devolucion = NOW() WHERE id = %s",
            (id_apartado,)
        )
        cur.execute(
            "UPDATE ejemplares SET estado = 'disponible' WHERE id = %s",
            (apartado["id_ejemplar"],)
        )
        cur.execute(
            """UPDATE libros l
               JOIN ejemplares e ON e.id_libro = l.id
               SET l.cantidad_disponible = l.cantidad_disponible + 1
               WHERE e.id = %s""",
            (apartado["id_ejemplar"],)
        )
        # Respeta el orden de llegada y marca el primer turno pendiente
        # como notificado para que administración gestione el contacto.
        cur.execute(
            """SELECT id FROM lista_espera
               WHERE id_libro = (SELECT id_libro FROM ejemplares WHERE id = %s)
                 AND estado = 'pendiente'
               ORDER BY fecha_solicitud ASC, id ASC LIMIT 1 FOR UPDATE""",
            (apartado["id_ejemplar"],)
        )
        siguiente = cur.fetchone()
        if siguiente:
            cur.execute(
                "UPDATE lista_espera SET estado = 'notificado' WHERE id = %s",
                (siguiente["id"],)
            )
        return True


def renovar(id_apartado, dias=5, max_renovaciones=3):
    """Extiende cinco días un préstamo activo hasta el máximo permitido."""
    with get_db() as cur:
        cur.execute(
            """UPDATE apartados
               SET fecha_entrega = DATE_ADD(
                       COALESCE(fecha_entrega, CURDATE()), INTERVAL %s DAY),
                   renovaciones = renovaciones + 1
               WHERE id = %s AND estado = 'prestado' AND renovaciones < %s""",
            (dias, id_apartado, max_renovaciones)
        )
        return cur.rowcount > 0


def listar_por_usuario(id_usuario, busqueda="", limite=None, offset=0):
    """Lista el historial personal, con búsqueda y límite opcionales."""
    consulta = """
        SELECT a.id AS apartado_id, a.estado, a.fecha AS fecha_apartado,
               a.fecha_recogida, a.fecha_recogida_real, a.fecha_entrega, a.fecha_devolucion,
               l.id AS libro_id, l.titulo AS libro_titulo, l.autor AS libro_autor, l.imagen AS libro_imagen,
               e.codigo_inventario AS codigo_ejemplar,
               n.id AS nota_id, n.nota_titulo, n.nota
        FROM apartados a
        JOIN ejemplares e ON a.id_ejemplar = e.id
        JOIN libros l ON e.id_libro = l.id
        LEFT JOIN (
            SELECT id_libro, id_usuario, MAX(id) AS nota_id
            FROM notas
            WHERE nota IS NOT NULL AND nota != ''
            GROUP BY id_libro, id_usuario
        ) ultima_nota ON ultima_nota.id_libro = l.id AND ultima_nota.id_usuario = a.id_usuario
        LEFT JOIN notas n ON n.id = ultima_nota.nota_id
        WHERE a.id_usuario = %s
    """
    parametros = [id_usuario]
    if busqueda:
        consulta += " AND (l.titulo LIKE %s OR l.autor LIKE %s)"
        parametros.extend((f"%{busqueda}%", f"%{busqueda}%"))
    consulta += " ORDER BY a.fecha DESC"
    if limite is not None:
        consulta += " LIMIT %s OFFSET %s"
        parametros.extend((max(1, int(limite)), max(0, int(offset))))

    with get_db() as cur:
        cur.execute(consulta, tuple(parametros))
        return cur.fetchall()


def contar_por_usuario(id_usuario, busqueda=""):
    """Cuenta el historial personal que coincide con la búsqueda."""
    consulta = """SELECT COUNT(*) AS total
                  FROM apartados a
                  JOIN ejemplares e ON e.id = a.id_ejemplar
                  JOIN libros l ON l.id = e.id_libro
                  WHERE a.id_usuario = %s"""
    parametros = [id_usuario]
    if busqueda:
        consulta += " AND (l.titulo LIKE %s OR l.autor LIKE %s)"
        parametros.extend((f"%{busqueda}%", f"%{busqueda}%"))
    with get_db() as cur:
        cur.execute(consulta, tuple(parametros))
        return cur.fetchone()["total"]


def listar_todos(limite=None, offset=0, busqueda="", sede=None):
    """Lista préstamos administrativos filtrados y paginados opcionalmente."""
    with get_db() as cur:
        consulta = """
            SELECT a.id, a.estado, a.fecha, a.fecha_recogida, a.fecha_entrega,
                   a.fecha_devolucion, a.fecha_recogida_real, a.curso,
                   l.id AS id_libro, l.titulo AS libro_titulo, l.autor, l.categoria, l.imagen,
                   e.codigo_inventario AS codigo_ejemplar,
                   u.nombre, u.apellido, u.identificacion, u.telefono, u.curso AS usuario_curso,
                   a.renovaciones
            FROM apartados a
            JOIN ejemplares e ON a.id_ejemplar = e.id
            JOIN libros l ON e.id_libro = l.id
            JOIN usuarios u ON a.id_usuario = u.id
        """
        condiciones = []
        parametros = []
        if sede:
            condiciones.append("l.sede = %s")
            parametros.append(sede)
        if busqueda:
            condiciones.append("(u.nombre LIKE %s OR u.apellido LIKE %s " \
                "OR CONCAT_WS(' ', u.nombre, u.apellido) LIKE %s " \
                "OR u.identificacion LIKE %s OR l.titulo LIKE %s OR l.autor LIKE %s)")
            termino = f"%{busqueda}%"
            parametros.extend((termino, termino, termino, termino, termino, termino))
        if condiciones:
            consulta += " WHERE " + " AND ".join(condiciones)
        consulta += " ORDER BY a.id DESC"
        if limite is not None:
            consulta += " LIMIT %s OFFSET %s"
            parametros.extend((max(1, int(limite)), max(0, int(offset))))
        cur.execute(consulta, tuple(parametros))
        return cur.fetchall()


def contar_todos(busqueda="", sede=None):
    """Cuenta todos los préstamos que coinciden con la búsqueda administrativa."""
    consulta = """SELECT COUNT(*) AS total
                  FROM apartados a
                  JOIN ejemplares e ON e.id = a.id_ejemplar
                  JOIN libros l ON l.id = e.id_libro
                  JOIN usuarios u ON u.id = a.id_usuario"""
    condiciones = []
    parametros = []
    if sede:
        condiciones.append("l.sede = %s")
        parametros.append(sede)
    if busqueda:
        condiciones.append("(u.nombre LIKE %s OR u.apellido LIKE %s " \
            "OR CONCAT_WS(' ', u.nombre, u.apellido) LIKE %s " \
            "OR u.identificacion LIKE %s OR l.titulo LIKE %s OR l.autor LIKE %s)")
        termino = f"%{busqueda}%"
        parametros.extend((termino, termino, termino, termino, termino, termino))
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    with get_db() as cur:
        cur.execute(consulta, tuple(parametros))
        return cur.fetchone()["total"]


def contar():
    """Cuenta los préstamos registrados, tanto activos como devueltos."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM apartados")
        return cur.fetchone()["total"]
