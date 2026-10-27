"""Rutas exclusivas del panel de administración."""
from datetime import date
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort

from app.utils.auth import admin_required
from app.models import libro as libro_model, usuario as usuario_model, contacto as contacto_model
from app.models import apartado as apartado_model, lista_espera as lista_espera_model
from app.models import ejemplar as ejemplar_model, aviso as aviso_model
from app.content import SEDES_CURSOS

bp = Blueprint("admin", __name__)


def _sede_desde_slug(sede_slug):
    """Valida el segmento de URL y devuelve el código de sede asociado."""
    sedes = {"sede-a": "A", "sede-b": "B"}
    sede = sedes.get(sede_slug.lower())
    if sede is None:
        abort(404)
    return sede


def _render_gestion(sede=None):
    por_pagina = 10
    busqueda = request.args.get("busqueda", "").strip()
    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
    except (TypeError, ValueError):
        pagina = 1

    filtros = {"busqueda": busqueda}
    if sede:
        filtros["sede"] = sede
    total_libros = libro_model.contar(filtros)
    total_paginas = max(1, (total_libros + por_pagina - 1) // por_pagina)
    pagina = min(pagina, total_paginas)
    return render_template(
        "gestion.html",
        libros=libro_model.listar_inventario(
            filtros,
            limite=por_pagina,
            offset=(pagina - 1) * por_pagina,
        ),
        busqueda=busqueda,
        total_libros=total_libros,
        pagina=pagina,
        total_paginas=total_paginas,
        sede=sede,
    )


def _render_apartados(sede=None):
    por_pagina = 10
    busqueda = request.args.get("busqueda", "").strip()
    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
    except (TypeError, ValueError):
        pagina = 1

    total_apartados = apartado_model.contar_todos(busqueda, sede=sede)
    total_paginas = max(1, (total_apartados + por_pagina - 1) // por_pagina)
    pagina = min(pagina, total_paginas)
    return render_template(
        "apartados.html",
        datos=apartado_model.listar_todos(
            limite=por_pagina,
            offset=(pagina - 1) * por_pagina,
            busqueda=busqueda,
            sede=sede,
        ),
        hoy=date.today(),
        busqueda=busqueda,
        total_apartados=total_apartados,
        pagina=pagina,
        total_paginas=total_paginas,
        sede=sede,
    )


def _url_apartados_actuales():
    """Mantiene la vista de sede al volver de una acción sobre un préstamo."""
    parametros = {
        "pagina": request.args.get("pagina", 1),
        "busqueda": request.args.get("busqueda", ""),
    }
    sede = request.args.get("sede")
    if sede in {"A", "B"}:
        return url_for(
            "admin.prestamos_sede",
            sede_slug=f"sede-{sede.lower()}",
            **parametros,
        )
    return url_for("admin.ver_apartados", **parametros)


@bp.route("/gestion")
@admin_required
def gestion():
    """Muestra el inventario filtrado y paginado en grupos de diez libros."""
    return _render_gestion()


@bp.route("/admin/gestion/<sede_slug>")
@admin_required
def gestion_sede(sede_slug):
    """Muestra únicamente el inventario de la sede solicitada."""
    return _render_gestion(_sede_desde_slug(sede_slug))


@bp.route("/admin/gestion/<sede_slug>/prestamos")
@admin_required
def prestamos_sede(sede_slug):
    """Muestra únicamente los préstamos de una sede."""
    return _render_apartados(_sede_desde_slug(sede_slug))


def _render_lista_espera(sede=None):
    por_pagina = 10
    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
    except (TypeError, ValueError):
        pagina = 1
    total_registros = lista_espera_model.contar_todos(sede=sede)
    total_paginas = max(1, (total_registros + por_pagina - 1) // por_pagina)
    pagina = min(pagina, total_paginas)
    return render_template(
        "lista_espera.html",
        lista_espera=lista_espera_model.listar_todos(
            sede=sede,
            limite=por_pagina,
            offset=(pagina - 1) * por_pagina,
        ),
        total_registros=total_registros,
        pagina=pagina,
        total_paginas=total_paginas,
        sede=sede,
    )


@bp.route("/admin/gestion/<sede_slug>/lista-espera")
@admin_required
def lista_espera_sede(sede_slug):
    """Muestra la lista de espera únicamente para la sede seleccionada."""
    return _render_lista_espera(_sede_desde_slug(sede_slug))


@bp.route("/admin")
@admin_required
def admin_dashboard():
    """Prepara los indicadores y rankings principales del panel administrativo."""
    return render_template(
        "admin_dashboard.html",
        libros_count=libro_model.contar(),
        ejemplares_count=ejemplar_model.contar_todos(),
        apartados_count=apartado_model.contar(),
        usuarios_count=usuario_model.contar_estudiantes(),
        mensajes_count=contacto_model.contar(),
        libros_agotados=libro_model.contar_agotados(),
        libros_mas_apartados=libro_model.mas_apartados(5),
        libros_mejor_valorados=libro_model.mejor_valorados(5),
        categorias_populares=libro_model.categorias_populares(5),
    )


@bp.route("/apartados")
@admin_required
def ver_apartados():
    """Carga diez préstamos por página."""
    return _render_apartados()


@bp.route("/lista-espera")
@admin_required
def ver_lista_espera():
    """Muestra la lista de espera general en páginas de diez registros."""
    return _render_lista_espera()


@bp.route("/apartados/<int:id_apartado>/devolver", methods=["POST"])
@admin_required
def devolver_apartado(id_apartado):
    """Registra la devolución del ejemplar y comunica si la operación tuvo éxito."""
    if apartado_model.devolver(id_apartado):
        flash("Ejemplar marcado como devuelto.")
    else:
        flash("Ese préstamo ya estaba devuelto o no existe.")
    return redirect(_url_apartados_actuales())


@bp.route("/apartados/<int:id_apartado>/reclamar", methods=["POST"])
@admin_required
def reclamar_apartado(id_apartado):
    """Marca que el estudiante recogió el ejemplar reservado."""
    if apartado_model.reclamar(id_apartado):
        flash("Ejemplar marcado como reclamado.")
    else:
        flash("El ejemplar ya fue reclamado, devuelto o no existe.")
    return redirect(_url_apartados_actuales())


@bp.route("/apartados/<int:id_apartado>/renovar", methods=["POST"])
@admin_required
def renovar_apartado(id_apartado):
    """Extiende cinco días el plazo, hasta tres veces por préstamo."""
    if apartado_model.renovar(id_apartado, dias=5, max_renovaciones=3):
        flash("Préstamo extendido por 5 días más.")
    else:
        flash("No se pudo extender: el préstamo está entregado o ya alcanzó las 3 extensiones.")
    return redirect(_url_apartados_actuales())


# ---------------------------------------------------------------
# Cartelera de avisos (visible en la página principal)
# ---------------------------------------------------------------

@bp.route("/avisos")
@admin_required
def ver_avisos():
    """Muestra todos los avisos disponibles para su administración."""
    return render_template("avisos.html", avisos=aviso_model.listar_todos())


def _guardar_imagen_aviso():
    """Valida y guarda el cartel gráfico del anuncio."""
    archivo = request.files.get("imagen")
    if not archivo or not archivo.filename:
        return None
    nombre_original = secure_filename(archivo.filename)
    extension = os.path.splitext(nombre_original)[1].lower()
    if extension not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        raise ValueError("Formato no permitido. Usa PNG, JPG, JPEG, GIF o WEBP.")
    nombre = f"aviso_{uuid.uuid4().hex}{extension}"
    archivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre))
    return f"uploads/{nombre}"


@bp.route("/avisos/nuevo", methods=["GET", "POST"])
@admin_required
def crear_aviso():
    """Crea un anuncio visual: solo imagen, sin texto publicitario."""
    if request.method == "POST":
        try:
            imagen = _guardar_imagen_aviso()
        except ValueError as error:
            flash(str(error))
            return redirect(url_for("admin.crear_aviso"))
        if not imagen:
            flash("Selecciona una imagen para publicar el anuncio.")
            return redirect(url_for("admin.crear_aviso"))
        aviso_model.crear("Anuncio gráfico", "", imagen)
        flash("Anuncio gráfico publicado correctamente.")
        return redirect(url_for("admin.ver_avisos"))
    return render_template("aviso_form.html", aviso=None)


@bp.route("/avisos/<int:id_aviso>/editar", methods=["GET", "POST"])
@admin_required
def editar_aviso(id_aviso):
    """Permite reemplazar la imagen de un anuncio existente."""
    aviso = aviso_model.obtener_por_id(id_aviso)
    if not aviso:
        flash("Anuncio no encontrado.")
        return redirect(url_for("admin.ver_avisos"))
    if request.method == "POST":
        try:
            imagen = _guardar_imagen_aviso()
        except ValueError as error:
            flash(str(error))
            return redirect(url_for("admin.editar_aviso", id_aviso=id_aviso))
        if not imagen and not aviso.get("imagen"):
            flash("Selecciona una imagen para publicar el anuncio.")
            return redirect(url_for("admin.editar_aviso", id_aviso=id_aviso))
        aviso_model.actualizar(id_aviso, "Anuncio gráfico", "", imagen)
        flash("Anuncio actualizado correctamente.")
        return redirect(url_for("admin.ver_avisos"))
    return render_template("aviso_form.html", aviso=aviso)


@bp.route("/avisos/<int:id_aviso>/alternar", methods=["POST"])
@admin_required
def alternar_aviso(id_aviso):
    """Cambia si un aviso está activo y visible en la página principal."""
    aviso_model.alternar_activo(id_aviso)
    flash("Visibilidad del aviso actualizada.")
    return redirect(url_for("admin.ver_avisos"))


@bp.route("/avisos/<int:id_aviso>/eliminar", methods=["POST"])
@admin_required
def eliminar_aviso(id_aviso):
    """Elimina el aviso indicado y vuelve a la lista administrativa."""
    aviso = aviso_model.obtener_por_id(id_aviso)
    aviso_model.eliminar(id_aviso)
    if aviso and aviso.get("imagen"):
        ruta = os.path.join(current_app.static_folder, aviso["imagen"])
        if os.path.isfile(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass
    flash("Anuncio eliminado correctamente.")
    return redirect(url_for("admin.ver_avisos"))


# ---------------------------------------------------------------
# Gestión de cuentas: promover/degradar administradores
# ---------------------------------------------------------------

@bp.route("/usuarios")
@admin_required
def ver_usuarios():
    """Muestra las cuentas que el administrador puede gestionar."""
    return render_template("admin_usuarios.html", usuarios=usuario_model.listar_todos())


@bp.route("/usuarios/nuevo_admin", methods=["POST"])
@admin_required
def crear_admin():
    """Valida y crea una cuenta con permisos de administración."""
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    identificacion = request.form.get("identificacion", "").strip()
    contrasena = request.form.get("contrasena", "")

    if not all([nombre, apellido, identificacion, contrasena]):
        flash("Completa todos los campos para crear un administrador.")
    elif usuario_model.existe_identificacion(identificacion):
        flash("Ya existe una cuenta con esa identificación.")
    else:
        usuario_model.crear(nombre, apellido, identificacion, contrasena, rol="admin")
        flash(f"Cuenta de administrador creada para {nombre} {apellido}.")

    return redirect(url_for("admin.ver_usuarios"))


@bp.route("/usuarios/<int:id_usuario>/cambiar_rol", methods=["POST"])
@admin_required
def cambiar_rol_usuario(id_usuario):
    """Alterna el rol de la cuenta indicada sin permitir cambiar el propio."""
    if id_usuario == session.get("user_id"):
        flash("No puedes cambiar el rol de tu propia cuenta.")
        return redirect(url_for("admin.ver_usuarios"))

    usuario = usuario_model.obtener_por_id(id_usuario)
    if not usuario:
        flash("Usuario no encontrado.")
        return redirect(url_for("admin.ver_usuarios"))

    nuevo_rol = "estudiante" if usuario["rol"] == "admin" else "admin"
    usuario_model.cambiar_rol(id_usuario, nuevo_rol)
    flash(f"{usuario['nombre']} {usuario['apellido']} ahora tiene el rol: {nuevo_rol}.")
    return redirect(url_for("admin.ver_usuarios"))
