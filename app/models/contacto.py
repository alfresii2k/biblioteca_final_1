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
        cur.execute("SELECT COUNT(*) AS total FROM mensajes")
        return cur.fetchone()["total"]


def crear_mensaje(id_usuario, remitente, contenido):
    """Añade un mensaje a la conversación privada de un estudiante."""
    with get_db() as cur:
        cur.execute(
            """INSERT INTO mensajes (id_usuario, remitente, contenido)
               VALUES (%s, %s, %s)""",
            (id_usuario, remitente, contenido),
        )


def listar_conversacion(id_usuario, sede=None):
    """Devuelve los mensajes de una conversación, validando opcionalmente su sede."""
    consulta = """
        SELECT m.id, m.remitente, m.contenido, m.creado_en, m.leido,
               u.id AS id_usuario, u.nombre, u.apellido, u.curso, u.sede
        FROM mensajes m
        JOIN usuarios u ON u.id = m.id_usuario
        WHERE m.id_usuario = %s AND u.rol = 'estudiante'
    """
    parametros = [id_usuario]
    if sede:
        consulta += " AND u.sede = %s"
        parametros.append(sede)
    consulta += " ORDER BY m.creado_en ASC, m.id ASC"
    with get_db() as cur:
        cur.execute(consulta, tuple(parametros))
        return cur.fetchall()


def listar_bandeja(sede):
    """Lista una conversación por estudiante, limitada estrictamente a una sede."""
    with get_db() as cur:
        cur.execute(
            """
            SELECT u.id AS id_usuario, u.nombre, u.apellido, u.curso, u.sede,
                   (SELECT m.creado_en FROM mensajes m
                    WHERE m.id_usuario = u.id AND m.remitente = 'estudiante'
                    ORDER BY m.creado_en DESC, m.id DESC LIMIT 1) AS ultimo_en,
                   (SELECT COUNT(*) FROM mensajes m
                    WHERE m.id_usuario = u.id
                      AND m.remitente = 'estudiante' AND m.leido = 0) AS no_leidos
            FROM usuarios u
            WHERE u.rol = 'estudiante' AND u.sede = %s
              AND EXISTS (SELECT 1 FROM mensajes m WHERE m.id_usuario = u.id)
            ORDER BY ultimo_en DESC
            """,
            (sede,),
        )
        return cur.fetchall()


def marcar_leidos(id_usuario, remitente, sede=None):
    """Marca como leídos los mensajes del interlocutor solo en la sede validada."""
    consulta = """
        UPDATE mensajes m
        JOIN usuarios u ON u.id = m.id_usuario
        SET m.leido = 1
        WHERE m.id_usuario = %s AND m.remitente = %s AND u.rol = 'estudiante'
    """
    parametros = [id_usuario, remitente]
    if sede:
        consulta += " AND u.sede = %s"
        parametros.append(sede)
    with get_db() as cur:
        cur.execute(consulta, tuple(parametros))


def contar_no_leidos_estudiante(id_usuario):
    """Cuenta respuestas administrativas pendientes de leer por el estudiante."""
    with get_db() as cur:
        cur.execute(
            """SELECT COUNT(*) AS total FROM mensajes
               WHERE id_usuario = %s AND remitente = 'admin' AND leido = 0""",
            (id_usuario,),
        )
        return cur.fetchone()["total"]
