"""Rutas de gestión del catálogo: libros, apartados, lista de espera y valoraciones."""
import os
import uuid
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, current_app
)
from werkzeug.utils import secure_filename

from app.utils.db import allowed_file
from app.utils.auth import login_required, admin_required, estudiante_required
from app.models import (
    libro as libro_model,
    favorito as favorito_model,
    apartado as apartado_model,
    lista_espera as lista_espera_model,
    valoracion as valoracion_model,
    usuario as usuario_model,
)

PLAZO_MAXIMO_DIAS = 15

bp = Blueprint("libros", __name__)


def _guardar_imagen(imagen_file):
    """Guarda la imagen subida y devuelve su ruta relativa, o None si no hay archivo.

    Lanza ValueError si el archivo tiene una extensión no permitida.
    """
    if not imagen_file or not imagen_file.filename:
        return None
    if not allowed_file(imagen_file.filename):
        raise ValueError("Formato de imagen no permitido. Usa PNG, JPG, JPEG o GIF.")

    nombre = f"{uuid.uuid4().hex}_{secure_filename(imagen_file.filename)}"
    imagen_file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre))
    return f"uploads/{nombre}"


def _leer_cantidades(form, actual_total=1, actual_disponible=1):
    """Parsea y valida cantidad_total / cantidad_disponible del formulario."""
    try:
        total = max(1, int(form.get("cantidad_total", actual_total)))
    except (TypeError, ValueError):
        total = actual_total
    try:
        disponible = max(0, int(form.get("cantidad_disponible", actual_disponible)))
    except (TypeError, ValueError):
        disponible = actual_disponible
    return total, min(disponible, total)


def _datos_libro_desde_form(form):
    """Extrae los campos bibliográficos de un formulario HTTP."""
    return {
        "titulo": form.get("titulo"),
        "autor": form.get("autor"),
        "anio": form.get("anio") or form.get("año") or None,
        "isbn": form.get("isbn"),
        "categoria": form.get("categoria"),
        "descripcion": form.get("descripcion"),
        "edicion": form.get("edicion"),
        "editorial": form.get("editorial"),
        "sede": form.get("sede", "").strip(),
        "seccion": form.get("seccion"),
        "estante": form.get("estante"),
        "fila": form.get("fila"),
    }


def _url_retorno_edicion():
    """Devuelve solo una URL de retorno local indicada por el formulario."""
    destino = request.form.get("return_to", "")
    partes = urlsplit(destino)
    if (
        partes.scheme
        or partes.netloc
        or not partes.path.startswith("/")
        or partes.path.startswith("//")
        or "\\" in partes.path
    ):
        return url_for("libros.books")
    return partes.path + (f"?{partes.query}" if partes.query else "")


@bp.route("/books")
def books():
    """Muestra el catálogo público aplicando los filtros recibidos por URL."""
    filtros = {
        "busqueda": request.args.get("busqueda", "").strip(),
        "categoria": request.args.get("categoria", "").strip(),
        "autor": request.args.get("autor", "").strip(),
        "editorial": request.args.get("editorial", "").strip(),
        "seccion": request.args.get("seccion", "").strip(),
        "disponibilidad": request.args.get("disponibilidad", "").strip(),
    }

    favoritos_ids = set()
    if session.get("rol") == "estudiante":
        favoritos_ids = favorito_model.ids_favoritos_de_usuario(session["user_id"])

    return render_template(
        "books.html",
        libros=libro_model.listar(filtros),
        categorias=libro_model.categorias_disponibles(),
        editoriales=libro_model.editoriales_disponibles(),
        secciones=libro_model.secciones_disponibles(),
        busqueda=filtros["busqueda"],
        categoria_seleccionada=filtros["categoria"],
        autor=filtros["autor"],
        editorial=filtros["editorial"],
        seccion=filtros["seccion"],
        disponibilidad=filtros["disponibilidad"],
        favoritos_ids=favoritos_ids,
        abrir_modal=request.args.get("abrir_modal") == "1",
        sede_preseleccionada=request.args.get("sede", "") if request.args.get("sede") in {"A", "B"} else "",
        mostrar_aviso_acceso=request.args.get("login_required") == "1",
    )


@bp.route("/libro/<int:id_libro>")
def libro_detalle(id_libro):
    """Muestra el detalle de un libro; visitantes regresan al catálogo."""
    if not session.get("user_id"):
        return redirect(url_for("libros.books", login_required=1))

    libro = libro_model.obtener_por_id(id_libro)
    if not libro:
        flash("Libro no encontrado.")
        return redirect(url_for("libros.books"))

    es_favorito = False
    ya_valoro = False
    puede_valorar = False
    if session.get("rol") == "estudiante":
        es_favorito = favorito_model.existe(id_libro, session["user_id"])
        ya_valoro = valoracion_model.ya_valoro(id_libro, session["user_id"])
        puede_valorar = apartado_model.usuario_reclamo_libro(id_libro, session["user_id"])

    hoy = date.today()
    return render_template(
        "libro_detalle.html",
        libro=libro,
        es_favorito=es_favorito,
        ya_valoro=ya_valoro,
        puede_valorar=puede_valorar,
        resumen_valoracion=valoracion_model.promedio_y_total(id_libro),
        resenas=valoracion_model.listar_de_libro(id_libro),
        en_espera=lista_espera_model.ya_esta_en_espera(id_libro, session["user_id"])
            if session.get("rol") == "estudiante" else False,
        fecha_min_recogida=hoy.isoformat(),
        fecha_max_recogida=(hoy + timedelta(days=30)).isoformat(),
        plazo_maximo_dias=PLAZO_MAXIMO_DIAS,
    )


@bp.route("/buscar", methods=["POST"])
def buscar():
    """Convierte el formulario de búsqueda en filtros de la URL del catálogo."""
    query = request.form.get("busqueda", "").strip()
    categoria = request.form.get("categoria", "").strip()
    return redirect(url_for("libros.books", busqueda=query, categoria=categoria))


@bp.route("/add_book", methods=["GET", "POST"])
@admin_required
def add_book():
    """Registra un libro nuevo y sus ejemplares desde el formulario admin."""
    if request.method == "POST":
        datos = _datos_libro_desde_form(request.form)
        cantidad_total, cantidad_disponible = _leer_cantidades(request.form)
        if datos["sede"] not in {"A", "B"}:
            flash("Selecciona Sede A o Sede B para el libro.")
            return redirect(url_for("libros.books", abrir_modal=1))

        try:
            datos["imagen"] = _guardar_imagen(request.files.get("imagen"))
        except ValueError as error:
            flash(str(error))
            return redirect(url_for("libros.books", abrir_modal=1))

        libro_model.crear(datos, cantidad_total, cantidad_disponible)
        flash("Libro agregado correctamente.")
        return redirect(url_for("libros.books"))

    return redirect(url_for("libros.books", abrir_modal=1))


@bp.route("/editar_libro/<int:id_libro>", methods=["GET", "POST"])
@admin_required
def editar_libro(id_libro):
    """Edita los datos de un libro existente y sincroniza sus ejemplares."""
    libro = libro_model.obtener_por_id(id_libro)
    if not libro:
        flash("Libro no encontrado.")
        return redirect(url_for("libros.books"))

    if request.method == "POST":
        return_to = _url_retorno_edicion()
        datos = _datos_libro_desde_form(request.form)
        if datos["sede"] not in {"A", "B"}:
            flash("Selecciona Sede A o Sede B para el libro.")
            return redirect(f"{return_to}{'&' if '?' in return_to else '?'}editar_libro={id_libro}")
        cantidad_total, cantidad_disponible = _leer_cantidades(
            request.form, libro.get("cantidad_total", 1), libro.get("cantidad_disponible", 1)
        )

        try:
            imagen = _guardar_imagen(request.files.get("imagen"))
        except ValueError as error:
            flash(str(error))
            return redirect(f"{return_to}{'&' if '?' in return_to else '?'}editar_libro={id_libro}")
        datos["imagen"] = imagen or libro.get("imagen")

        libro_model.actualizar(id_libro, datos, cantidad_total, cantidad_disponible)
        flash("Libro actualizado correctamente.")
        return redirect(return_to)

    return render_template("editar_libro.html", libro=libro)


@bp.route("/delete_book/<int:id_libro>", methods=["POST"])
@admin_required
def delete_book(id_libro):
    """Elimina un libro y, si existe, su imagen subida al servidor."""
    libro = libro_model.eliminar(id_libro)
    if not libro:
        flash("Libro no encontrado.")
        return redirect(url_for("libros.books"))

    if libro.get("imagen"):
        ruta = os.path.join(current_app.static_folder, libro["imagen"])
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass

    flash("Libro eliminado correctamente.")
    return redirect(url_for("libros.books"))


@bp.route("/toggle_disponibilidad/<int:id_libro>", methods=["POST"])
@admin_required
def toggle_disponibilidad(id_libro):
    """Alterna la disponibilidad del inventario del libro indicado."""
    if libro_model.alternar_disponibilidad(id_libro):
        flash("Disponibilidad actualizada.")
    else:
        flash("Libro no encontrado.")
    return redirect(url_for("libros.books"))


@bp.route("/apartar/<int:id_libro>", methods=["POST"])
@login_required
def apartar(id_libro):
    """Valida las fechas y crea el préstamo del ejemplar si hay disponibilidad."""
    nota = request.form.get("nota", "").strip()
    nota_titulo = request.form.get("nota_titulo", "").strip()
    perfil = usuario_model.obtener_por_id(session["user_id"])
    curso = perfil.get("curso") if perfil else None

    destino = redirect(request.referrer or url_for("libros.libro_detalle", id_libro=id_libro))

    fecha_recogida_str = request.form.get("fecha_recogida", "").strip()
    fecha_entrega_str = request.form.get("fecha_entrega", "").strip()
    fecha_recogida = fecha_entrega = None
    hoy = date.today()

    if fecha_recogida_str and fecha_entrega_str:
        try:
            fecha_recogida = datetime.strptime(fecha_recogida_str, "%Y-%m-%d").date()
            fecha_entrega = datetime.strptime(fecha_entrega_str, "%Y-%m-%d").date()
        except ValueError:
            flash("La fecha seleccionada no es válida.")
            return destino

        if fecha_recogida < hoy:
            flash("La fecha de recogida no puede ser anterior a hoy.")
            return destino
        if fecha_entrega <= fecha_recogida:
            flash("La fecha de entrega debe ser posterior a la de recogida.")
            return destino
        if (fecha_entrega - fecha_recogida).days > PLAZO_MAXIMO_DIAS:
            flash(f"El plazo máximo de lectura es de {PLAZO_MAXIMO_DIAS} días.")
            return destino

    try:
        codigo = apartado_model.crear(
            id_libro, session["user_id"], curso=curso, nota_titulo=nota_titulo, nota=nota,
            fecha_recogida=fecha_recogida, fecha_entrega=fecha_entrega,
        )
        flash(f"Ejemplar {codigo} apartado correctamente.")
    except apartado_model.SinDisponibilidad:
        flash("No hay ejemplares disponibles en este momento.")
    return destino


@bp.route("/lista_espera/<int:id_libro>", methods=["POST"])
@estudiante_required
def lista_espera(id_libro):
    """Inscribe al estudiante en espera solo si el libro está agotado."""
    if lista_espera_model.libro_tiene_disponibilidad(id_libro):
        flash("El libro ya tiene ejemplares disponibles. Puedes apartarlo directamente.")
    elif lista_espera_model.ya_esta_en_espera(id_libro, session["user_id"]):
        flash("Ya estás en la lista de espera para este libro.")
    else:
        lista_espera_model.unirse(id_libro, session["user_id"])
        flash("Te has unido a la lista de espera. Te notificaremos cuando haya disponibilidad.")
    return redirect(url_for("libros.books"))


@bp.route("/valorar/<int:id_libro>", methods=["POST"])
@estudiante_required
def valorar(id_libro):
    """Valida y guarda una valoración única de una a cinco estrellas."""
    if not apartado_model.usuario_reclamo_libro(id_libro, session["user_id"]):
        flash("Podrás valorar este libro después de reclamar un ejemplar.")
        return redirect(url_for("libros.libro_detalle", id_libro=id_libro))

    try:
        valor = int(request.form.get("valor"))
    except (TypeError, ValueError):
        valor = 0
    comentario = request.form.get("comentario", "").strip() or None

    if not 1 <= valor <= 5:
        flash("Selecciona una valoración entre 1 y 5 estrellas.")
    elif valoracion_model.ya_valoro(id_libro, session["user_id"]):
        flash("Ya valoraste este libro. Solo puedes puntuarlo una vez.")
    else:
        valoracion_model.crear(id_libro, session["user_id"], valor, comentario)
        flash("Gracias por valorar este libro.")
    return redirect(url_for("libros.libro_detalle", id_libro=id_libro))
