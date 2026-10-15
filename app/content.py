"""Contenido institucional fijo (no vive en la base de datos).

Textos que casi nunca cambian (horarios, dirección, normativa, reseña
histórica) y la relación sede -> cursos válidos. Se edita directamente
aquí cuando el colegio necesite actualizar algún dato; no requiere
tocar plantillas ni la base de datos.
"""

SEDES_CURSOS = {
    "A": ["101", "201", "301", "401", "501"],
    "B": [
        "601", "602", "603",
        "701", "702", "703",
        "801", "802", "803",
        "901", "902", "903",
        "1001", "1002", "1003", "1004",
        "1101", "1102", "1103", "1104",
    ],
}

INFO_BIBLIOTECA = {
    "horario": [
        {"dias": "Sede A", "horas": "Martes, jueves y viernes · 6:30 a.m. – 4:00 p.m."},
        {"dias": "Sede B", "horas": "Lunes, martes y miércoles · 6:30 a.m. – 4:00 p.m."},
    ],
    "direccion": "Calle 123 #45-67, Bogotá D.C., Colombia",
    "telefono_contacto": "(601) 555-0100",
    "reglas": [
        "El préstamo de cada ejemplar tiene una duración máxima de 8 días calendario.",
        "Cuida los libros: evita doblar hojas, subrayar o exponerlos a líquidos.",
        "Guarda silencio y respeta los espacios de lectura de tus compañeros.",
        "No se permiten alimentos ni bebidas dentro de las salas de lectura.",
        "Si pierdes o dañas un ejemplar, debes reponerlo o cubrir su costo de reposición.",
    ],
    "resena_historica": (
        "La biblioteca escolar nació con la fundación del colegio como un pequeño "
        "rincón de lectura para acompañar el proceso académico de los estudiantes. "
        "Con el paso de los años creció hasta convertirse en un espacio central de "
        "la vida institucional, ampliando su colección y sus actividades culturales "
        "para fomentar el hábito de la lectura en toda la comunidad educativa."
    ),
}

# Imágenes de la galería/carrusel en la página principal (reemplázalas
# por fotografías reales de la biblioteca cuando estén disponibles).
CARRUSEL_IMAGENES = [
    {"src": "image/imagen.png", "titulo": "Nuestra biblioteca", "descripcion": "Un espacio pensado para la lectura y el estudio."},
    {"src": "image/imagen_2.png", "titulo": "Colección en crecimiento", "descripcion": "Cientos de títulos disponibles para toda la comunidad."},
    {"src": "image/imagen_3.png", "titulo": "Actividades escolares", "descripcion": "Clubes de lectura y jornadas culturales durante el año."},
]
