"""Mensajería privada entre estudiantes y la biblioteca, separada por sede."""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app.models import contacto as contacto_model, usuario as usuario_model
from app.utils.auth import admin_required, estudiante_required, sede_estudiante_actual

bp = Blueprint("contacto", __name__)


def _sede_desde_slug(sede_slug):
    sedes = {"sede-a": "A", "sede-b": "B"}
    sede = sedes.get(sede_slug.lower())
    if sede is None:
        abort(404)
    return sede


@bp.route("/mensajes", methods=["GET", "POST"])
@bp.route("/contacto", methods=["GET", "POST"])
@estudiante_required
def mensajes_estudiante():
    """Permite al estudiante leer y responder su conversación de soporte."""
    sede = sede_estudiante_actual()
    id_usuario = session["user_id"]
    if request.method == "POST":
        contenido = request.form.get("mensaje", "").strip()
        if not contenido or len(contenido) > 4000:
            flash("El mensaje debe tener entre 1 y 4000 caracteres.")
            return redirect(url_for("contacto.mensajes_estudiante"))
        contacto_model.crear_mensaje(id_usuario, "estudiante", contenido)
        flash("Tu mensaje fue enviado a la biblioteca.")
        return redirect(url_for("contacto.mensajes_estudiante"))

    contacto_model.marcar_leidos(id_usuario, "admin", sede=sede)
    return render_template(
        "mensajes_estudiante.html",
        conversacion=contacto_model.listar_conversacion(id_usuario, sede=sede),
        nombre=f"{session.get('user', '')} {session.get('apellido', '')}".strip(),
    )


@bp.route("/contactos")
@admin_required
def ver_contactos():
    """Presenta la selección explícita de sede para la bandeja administrativa."""
    return render_template("contactos.html", sede=None, contactos=[])


@bp.route("/contactos/<sede_slug>")
@admin_required
def bandeja_sede(sede_slug):
    """Muestra exclusivamente conversaciones pertenecientes a la sede elegida."""
    sede = _sede_desde_slug(sede_slug)
    return render_template(
        "contactos.html",
        sede=sede,
        contactos=contacto_model.listar_bandeja(sede),
    )


@bp.route("/contactos/<sede_slug>/<int:id_usuario>", methods=["GET", "POST"])
@admin_required
def conversacion_admin(sede_slug, id_usuario):
    """Abre y responde un chat tras validar que el estudiante es de esa sede."""
    sede = _sede_desde_slug(sede_slug)
    usuario = usuario_model.obtener_por_id(id_usuario)
    if not usuario or usuario["rol"] != "estudiante" or usuario.get("sede") != sede:
        abort(404)

    if request.method == "POST":
        contenido = request.form.get("mensaje", "").strip()
        if not contenido or len(contenido) > 4000:
            flash("El mensaje debe tener entre 1 y 4000 caracteres.")
        else:
            contacto_model.crear_mensaje(id_usuario, "admin", contenido)
            flash("Tu respuesta fue enviada al estudiante.")
            return redirect(url_for(
                "contacto.conversacion_admin",
                sede_slug=sede_slug,
                id_usuario=id_usuario,
            ))

    contacto_model.marcar_leidos(id_usuario, "estudiante", sede=sede)
    return render_template(
        "chat_admin.html",
        sede=sede,
        usuario=usuario,
        conversacion=contacto_model.listar_conversacion(id_usuario, sede=sede),
        mensaje_inicial=request.args.get("mensaje", "")[:4000],
    )
