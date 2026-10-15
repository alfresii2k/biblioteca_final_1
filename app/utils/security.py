"""Utilidades de seguridad: hash y verificación de contraseñas.

Antes las contraseñas se guardaban y comparaban en texto plano. Ahora
se usa el hashing seguro que ya trae Werkzeug (PBKDF2/scrypt con sal
aleatoria), sin dependencias nuevas.
"""
from werkzeug.security import generate_password_hash, check_password_hash


def hashear_contrasena(contrasena: str) -> str:
    """Genera un hash seguro para guardar una contraseña sin texto plano."""
    return generate_password_hash(contrasena)


def verificar_contrasena(hash_guardado: str, contrasena: str) -> bool:
    """Compara una contraseña con su hash; un hash inválido nunca autentica."""
    if not hash_guardado:
        return False
    try:
        return check_password_hash(hash_guardado, contrasena)
    except ValueError:
        # Hash con formato desconocido/corrupto: nunca autenticar.
        return False
