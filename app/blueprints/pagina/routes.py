"""Rutas de las páginas públicas y del inicio autenticado."""
from flask import Blueprint, render_template, session, redirect, url_for

from app.models import libro as libro_model, usuario as usuario_model, valoracion as valoracion_model
from app.models import aviso as aviso_model
from app.content import INFO_BIBLIOTECA, CARRUSEL_IMAGENES
from app.utils.db import get_db
from app.utils.auth import login_required, sede_estudiante_actual

bp = Blueprint("pagina", __name__)


def _estadisticas_generales():
    """Agrupa los conteos del catálogo y de sus ejemplares."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM ejemplares")
        total_ejemplares = cur.fetchone()["total"]
    return {
        "total_libros": libro_model.contar(),
        "total_categorias": libro_model.contar_categorias(),
        "total_estudiantes": usuario_model.contar_estudiantes(),
        "total_ejemplares": total_ejemplares,
    }


@bp.route("/")
def index():
    """Renderiza la página pública o envía al inicio si ya hay sesión."""
    if session.get("user_id"):
        return redirect(url_for("pagina.inicio"))

    libros_destacados = libro_model.destacados(5)
    return render_template(
        "index.html",
        libros_destacados=libros_destacados,
        resenas_destacados=valoracion_model.resenas_por_libros(
            [libro["id"] for libro in libros_destacados]
        ),
        stats=_estadisticas_generales(),
        avisos=aviso_model.listar_activos(),
        info=INFO_BIBLIOTECA,
        carrusel=CARRUSEL_IMAGENES,
    )


@bp.route("/inicio")
@login_required
def inicio():
    """Prepara el inicio autenticado y las valoraciones del estudiante."""
    sede = sede_estudiante_actual()
    user_valoraciones = {}
    if session.get("rol") == "estudiante":
        user_valoraciones = valoracion_model.valoraciones_de_usuario(session["user_id"])
    libros_destacados = libro_model.destacados(5, sede=sede)

    return render_template(
        "inicio.html",
        libros_destacados=libros_destacados,
        resenas_destacados=valoracion_model.resenas_por_libros(
            [libro["id"] for libro in libros_destacados]
        ),
        user_valoraciones=user_valoraciones,
        libros_juego=libro_model.listar({"sede": sede} if sede else None),
        avisos=aviso_model.listar_activos(),
    )


@bp.route("/categorias")
@login_required
def categorias():
    """Muestra el número de libros registrados en cada categoría."""
    sede = sede_estudiante_actual()
    return render_template(
        "categorias.html",
        categorias=libro_model.conteo_por_categoria(sede),
    )
