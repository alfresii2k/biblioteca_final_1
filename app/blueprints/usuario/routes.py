"""Rutas del área personal: favoritos, notas, perfil y configuración."""
from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.utils.auth import login_required, estudiante_required
from app.models import (
    favorito as favorito_model,
    libro as libro_model,
    nota as nota_model,
    apartado as apartado_model,
    lista_espera as lista_espera_model,
    usuario as usuario_model,
)

bp = Blueprint("usuario", __name__)


@bp.route("/favoritos")
@estudiante_required
def favoritos():
    """Muestra los libros guardados por el estudiante actual."""
    return render_template("favoritos.html", libros=favorito_model.listar_por_usuario(session["user_id"]))


@bp.route("/agregar_favorito/<int:id_libro>", methods=["POST"])
@estudiante_required
def agregar_favorito(id_libro):
    """Valida y agrega un libro a los favoritos del estudiante."""
    if not libro_model.obtener_por_id(id_libro):
        flash("Libro no encontrado.")
    elif favorito_model.existe(id_libro, session["user_id"]):
        flash("Este libro ya está en tus favoritos.")
    else:
        favorito_model.agregar(id_libro, session["user_id"])
        flash("Libro agregado a tus favoritos.")
    return redirect(request.referrer or url_for("libros.books"))


@bp.route("/quitar_favorito/<int:id_libro>", methods=["POST"])
@estudiante_required
def quitar_favorito(id_libro):
    """Quita el libro indicado de la lista personal de favoritos."""
    favorito_model.quitar(id_libro, session["user_id"])
    flash("Libro removido de tus favoritos.")
    return redirect(request.referrer or url_for("usuario.favoritos"))


@bp.route("/nota/<int:id_libro>", methods=["GET", "POST"])
@estudiante_required
def nota_libro(id_libro):
    """Guarda una nota nueva o presenta el formulario para escribirla."""
    libro = libro_model.obtener_por_id(id_libro)
    if not libro:
        flash("Libro no encontrado.")
        return redirect(url_for("libros.books"))

    if request.method == "POST":
        nota_titulo = request.form.get("nota_titulo", "").strip()
        nota = request.form.get("nota", "").strip()
        nota_model.crear(id_libro, session["user_id"], nota_titulo, nota)
        flash("Tu nota fue guardada correctamente.")
        return redirect(url_for("usuario.anotaciones"))

    notas_previas = nota_model.listar_por_libro_y_usuario(id_libro, session["user_id"])
    return render_template("anotar_libro.html", libro=libro, notas_previas=notas_previas)


@bp.route("/nota/<int:id_nota>/editar", methods=["GET", "POST"])
@estudiante_required
def editar_nota(id_nota):
    """Valida y actualiza una nota que pertenezca al estudiante actual."""
    nota = nota_model.obtener_por_id_y_usuario(id_nota, session["user_id"])
    if not nota:
        flash("Anotación no encontrada.")
        return redirect(url_for("usuario.anotaciones"))

    if request.method == "POST":
        titulo = request.form.get("nota_titulo", "").strip()
        contenido = request.form.get("nota", "").strip()
        if not titulo or not contenido:
            flash("El título y el contenido de la nota son obligatorios.")
        else:
            nota_model.actualizar(id_nota, session["user_id"], titulo, contenido)
            flash("Anotación actualizada correctamente.")
            return redirect(url_for("usuario.anotaciones"))

    libro = libro_model.obtener_por_id(nota["id_libro"])
    return render_template("anotar_libro.html", libro=libro, nota=nota, notas_previas=[])


@bp.route("/nota/<int:id_nota>/eliminar", methods=["POST"])
@estudiante_required
def eliminar_nota(id_nota):
    """Elimina una nota propia y comunica el resultado de la operación."""
    if nota_model.eliminar(id_nota, session["user_id"]):
        flash("Anotación eliminada correctamente.")
    else:
        flash("Anotación no encontrada.")
    return redirect(url_for("usuario.anotaciones"))


@bp.route("/anotaciones")
@estudiante_required
def anotaciones():
    """Muestra todas las anotaciones privadas del estudiante."""
    return render_template("anotaciones.html", anotaciones=nota_model.listar_por_usuario(session["user_id"]))


@bp.route("/perfil")
@login_required
def perfil():
    """Carga los datos personales, favoritos, préstamos y lista de espera."""
    favoritos = favorito_model.listar_por_usuario(session["user_id"])
    busqueda_apartados = request.args.get("busqueda_apartados", "").strip()
    por_pagina = 10
    try:
        pagina_apartados = max(1, int(request.args.get("pagina_apartados", 1)))
    except (TypeError, ValueError):
        pagina_apartados = 1
    total_apartados = apartado_model.contar_por_usuario(session["user_id"], busqueda_apartados)
    total_paginas_apartados = max(1, (total_apartados + por_pagina - 1) // por_pagina)
    pagina_apartados = min(pagina_apartados, total_paginas_apartados)

    return render_template(
        "perfil.html",
        perfil=usuario_model.obtener_por_id(session["user_id"]),
        favoritos=favoritos,
        apartados=apartado_model.listar_por_usuario(
            session["user_id"],
            busqueda=busqueda_apartados,
            limite=por_pagina,
            offset=(pagina_apartados - 1) * por_pagina,
        ),
        busqueda_apartados=busqueda_apartados,
        total_apartados=total_apartados,
        pagina_apartados=pagina_apartados,
        total_paginas_apartados=total_paginas_apartados,
        lista_espera=lista_espera_model.listar_por_usuario(session["user_id"]),
        hoy=date.today(),
    )


@bp.route("/configuracion", methods=["GET", "POST"])
@login_required
def configuracion():
    """Valida el cambio de contraseña y vuelve al perfil al completarlo."""
    error = None
    if request.method == "POST":
        actual = request.form.get("contrasena_actual", "")
        nueva = request.form.get("contrasena_nueva", "")
        confirmar = request.form.get("confirmar_contrasena", "")

        if not all([actual, nueva, confirmar]):
            error = "Todos los campos son obligatorios."
        elif nueva != confirmar:
            error = "La nueva contraseña no coincide con la confirmación."
        elif usuario_model.cambiar_contrasena(session["user_id"], actual, nueva):
            flash("Contraseña actualizada correctamente.")
            return redirect(url_for("usuario.perfil"))
        else:
            error = "La contraseña actual es incorrecta."

    return render_template("configuracion.html", error=error)
