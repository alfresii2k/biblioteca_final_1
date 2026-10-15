"""Rutas del formulario de contacto y su bandeja de entrada."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.utils.auth import login_required, admin_required
from app.models import contacto as contacto_model

bp = Blueprint("contacto", __name__)


@bp.route("/contacto", methods=["GET", "POST"])
@login_required
def contacto():
    """Recibe el mensaje de un usuario autenticado o muestra el formulario."""
    if request.method == "POST":
        nombre = request.form.get("nombre", session.get("user", "")).strip()
        email = request.form.get("email", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        if not nombre or not email or not mensaje:
            flash("Completa nombre, correo y mensaje antes de enviar.")
            return redirect(url_for("contacto.contacto"))

        contacto_model.crear(session["user_id"], nombre, email, mensaje)
        flash("Tu mensaje fue enviado correctamente. Gracias por contactarnos.")
        return redirect(url_for("libros.books"))

    return render_template("contacto.html")


@bp.route("/contactos")
@admin_required
def ver_contactos():
    """Muestra al administrador los mensajes enviados por la comunidad."""
    return render_template("contactos.html", contactos=contacto_model.listar_todos())
