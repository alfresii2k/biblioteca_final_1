"""Configuración centralizada del proyecto.

Todos los valores se pueden sobreescribir con variables de entorno o un
archivo .env (ver .env.example) sin tocar el código. Si no se define
nada, la app arranca igual con valores por defecto razonables para
desarrollo local.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(valor, por_defecto=False):
    """Interpreta valores típicos de variables de entorno como booleanos."""
    if valor is None:
        return por_defecto
    return str(valor).strip().lower() in ("1", "true", "yes", "on")


class ConfigBD:
    """Parámetros de conexión a MySQL."""
    HOST = os.getenv("DB_HOST", "localhost")
    PUERTO = int(os.getenv("DB_PORT", "3306"))
    USUARIO = os.getenv("DB_USER", "root")
    CONTRASENA = os.getenv("DB_PASSWORD", "")
    NOMBRE = os.getenv("DB_NAME", "biblioteca_colegio")


class Config:
    """Configuración general de la aplicación Flask."""
    SECRET_KEY = os.getenv("SECRET_KEY", "biblioteca123-cambia-en-produccion")
    PERMANENT_SESSION_LIFETIME_MINUTES = int(os.getenv("SESSION_LIFETIME_MINUTES", "30"))
    DEBUG = _bool(os.getenv("FLASK_DEBUG"), True)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "avif"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB por archivo subido
