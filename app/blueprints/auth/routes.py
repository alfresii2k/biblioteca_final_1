"""Rutas de registro, inicio y cierre de sesión."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.models import usuario as usuario_model
from app.content import SEDES_CURSOS

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Valida los datos de registro y crea una cuenta de estudiante."""
    if request.method == "POST":
        apellido = request.form.get("apellido", "").strip()
        nombre = request.form.get("nombre", "").strip()
        identificacion = request.form.get("identificacion", "").strip()
        telefono = request.form.get("telefono", "").strip()
        sede = request.form.get("sede", "").strip().upper()
        curso = request.form.get("curso", "").strip()
        contrasena = request.form.get("contrasena", "")

        if not all([apellido, nombre, identificacion, telefono, sede, curso, contrasena]):
            return render_template("register.html", error="Completa todos los campos.", sedes_cursos=SEDES_CURSOS)

        if sede not in SEDES_CURSOS or curso not in SEDES_CURSOS[sede]:
            return render_template(
                "register.html",
                error="Selecciona una sede y un curso válidos para esa sede.",
                sedes_cursos=SEDES_CURSOS
            )

        if usuario_model.existe_identificacion(identificacion):
            return render_template(
                "register.html",
                error="Ya existe un usuario con esa identificación.",
                sedes_cursos=SEDES_CURSOS
            )

        usuario_model.crear(nombre, apellido, identificacion, contrasena, telefono=telefono, sede=sede, curso=curso)
        flash("Cuenta creada correctamente. Ya puedes iniciar sesión.")
        return redirect(url_for("auth.login"))

    return render_template("register.html", sedes_cursos=SEDES_CURSOS)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Comprueba las credenciales y guarda la identidad en la sesión."""
    if session.get("user_id"):
        return redirect(url_for("pagina.inicio"))

    error = None
    if request.method == "POST":
        identificacion = request.form.get("identificacion", "").strip()
        contrasena = request.form.get("contrasena", "")

        usuario = usuario_model.verificar_credenciales(identificacion, contrasena)
        if usuario:
            session.clear()
            session["user_id"] = usuario["id"]
            session["user"] = usuario["nombre"]
            session["apellido"] = usuario["apellido"]
            session["identificacion"] = usuario["identificacion"]
            session["rol"] = usuario["rol"]
            if usuario["rol"] == "estudiante":
                session["sede"] = usuario["sede"]
            session.permanent = True
            return redirect(url_for("pagina.inicio"))

        error = "Identificación o contraseña incorrecta."

    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    """Vacía la sesión actual y redirige al formulario de acceso."""
    session.clear()
    return redirect(url_for("auth.login"))
