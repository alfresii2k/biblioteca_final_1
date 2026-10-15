"""Punto de entrada para iniciar el servidor Flask de desarrollo."""

from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    print("Servidor Web Iniciado en http://localhost:5000")
    app.run(debug=Config.DEBUG, port=5000)
