"""Decoradores de autenticación/autorización para las rutas.

Reemplazan el `if 'user' not in session: return redirect(...)` que
antes estaba copiado y pegado al inicio de casi cada vista.
"""
from functools import wraps

from flask import session, redirect, url_for, flash


def login_required(vista):
    """Protege una vista para que solo la use una sesión iniciada."""
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        """Comprueba la sesión y delega en la vista original."""
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)
    return envoltorio


def admin_required(vista):
    """Restringe una vista a cuentas con sesión y rol de administrador."""
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        """Valida sesión y rol antes de ejecutar la vista administrativa."""
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("rol") != "admin":
            flash("No tienes permisos para acceder a esa sección.")
            return redirect(url_for("libros.books"))
        return vista(*args, **kwargs)
    return envoltorio


def estudiante_required(vista):
    """Solo cuentas con rol 'estudiante', no administradores."""
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        """Comprueba que la sesión pertenezca a un estudiante."""
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("rol") != "estudiante":
            flash("Esta acción es solo para cuentas de estudiante.")
            return redirect(url_for("pagina.inicio"))
        return vista(*args, **kwargs)
    return envoltorio


def id_usuario_actual():
    """Devuelve el identificador de usuario guardado en la sesión actual."""
    return session.get("user_id")
