"""Modelo Usuario: registro, autenticación, roles y cambio de contraseña."""
from app.utils.db import get_db
from app.utils.security import hashear_contrasena, verificar_contrasena


def obtener_por_identificacion(identificacion):
    """Busca una cuenta por su número de identificación."""
    with get_db() as cur:
        cur.execute("SELECT * FROM usuarios WHERE identificacion = %s", (identificacion,))
        return cur.fetchone()


def obtener_por_id(id_usuario):
    """Busca una cuenta por su clave primaria."""
    with get_db() as cur:
        cur.execute("SELECT * FROM usuarios WHERE id = %s", (id_usuario,))
        return cur.fetchone()


def existe_identificacion(identificacion):
    """Indica si ya hay una cuenta registrada con esa identificación."""
    return obtener_por_identificacion(identificacion) is not None


def crear(nombre, apellido, identificacion, contrasena, telefono=None, sede=None, curso=None, rol="estudiante"):
    """Crea un usuario nuevo con la contraseña ya hasheada. Devuelve su id."""
    with get_db() as cur:
        cur.execute(
            """INSERT INTO usuarios
                   (nombre, apellido, identificacion, telefono, sede, curso, contrasena_hash, rol)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (nombre, apellido, identificacion, telefono, sede, curso, hashear_contrasena(contrasena), rol)
        )
        return cur.lastrowid


def verificar_credenciales(identificacion, contrasena):
    """Devuelve el usuario si las credenciales son correctas, si no None."""
    usuario = obtener_por_identificacion(identificacion)
    if usuario and verificar_contrasena(usuario["contrasena_hash"], contrasena):
        return usuario
    return None


def cambiar_contrasena(id_usuario, contrasena_actual, contrasena_nueva):
    """Devuelve True si el cambio se aplicó, False si la actual no coincide."""
    usuario = obtener_por_id(id_usuario)
    if not usuario or not verificar_contrasena(usuario["contrasena_hash"], contrasena_actual):
        return False
    with get_db() as cur:
        cur.execute(
            "UPDATE usuarios SET contrasena_hash = %s WHERE id = %s",
            (hashear_contrasena(contrasena_nueva), id_usuario)
        )
    return True


def contar_todos():
    """Cuenta todas las cuentas de usuario registradas."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM usuarios")
        return cur.fetchone()["total"]


def contar_estudiantes():
    """Cuenta únicamente las cuentas que tienen rol de estudiante."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'estudiante'")
        return cur.fetchone()["total"]


# ---------------- Gestión de cuentas (panel admin) ----------------

def listar_todos():
    """Lista los datos de cuenta necesarios para la gestión administrativa."""
    with get_db() as cur:
        cur.execute("""
            SELECT id, nombre, apellido, identificacion, telefono, sede, curso, rol, creado_en
            FROM usuarios ORDER BY rol DESC, apellido, nombre
        """)
        return cur.fetchall()


def cambiar_rol(id_usuario, nuevo_rol):
    """Cambia el rol si es válido y devuelve si se actualizó una cuenta."""
    if nuevo_rol not in ("estudiante", "admin"):
        return False
    with get_db() as cur:
        cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, id_usuario))
        return cur.rowcount > 0
