"""Función de fábrica ('application factory') de la aplicación Flask.

Crea la instancia de Flask, la configura, registra los blueprints y
deja la base de datos lista antes de servir la primera petición.
"""
import os
from datetime import timedelta

from flask import Flask, session

from app.config import Config
from app.utils.schema import inicializar_base_datos


def create_app():
    """Configura Flask, registra las rutas y prepara la base de datos."""
    app = Flask(__name__)

    # Configuración general (clave secreta, sesión, subida de archivos).
    app.secret_key = Config.SECRET_KEY
    app.permanent_session_lifetime = timedelta(minutes=Config.PERMANENT_SESSION_LIFETIME_MINUTES)
    app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Blueprints: cada uno agrupa las rutas de un área de la aplicación.
    from app.blueprints.pagina.routes import bp as pagina_bp
    from app.blueprints.auth.routes import bp as auth_bp
    from app.blueprints.libros.routes import bp as libros_bp
    from app.blueprints.usuario.routes import bp as usuario_bp
    from app.blueprints.admin.routes import bp as admin_bp
    from app.blueprints.contacto.routes import bp as contacto_bp

    app.register_blueprint(pagina_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(libros_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(contacto_bp)

    @app.context_processor
    def inject_mensajes_no_leidos():
        if session.get("rol") != "estudiante" or not session.get("user_id"):
            return {"mensajes_no_leidos": 0}
        from app.models import contacto as contacto_model
        return {
            "mensajes_no_leidos": contacto_model.contar_no_leidos_estudiante(
                session["user_id"]
            )
        }

    # Base de datos lista (crea el esquema completo solo la primera vez).
    with app.app_context():
        inicializar_base_datos()

    return app
