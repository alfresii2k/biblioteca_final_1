"""Modelo Ejemplar: copias físicas de cada libro y su disponibilidad.

`libros.cantidad_total` / `libros.cantidad_disponible` son contadores
en caché; las únicas funciones autorizadas a mantenerlos sincronizados
con la tabla `ejemplares` son las de este módulo.
"""
from app.utils.db import get_db


def generar_codigo(titulo, id_libro, indice):
    """Construye un código de inventario único a partir del título y la copia."""
    prefijo = "".join(p[0] for p in (titulo or "").split()[:3] if p).upper() or "BIB"
    return f"{prefijo}-{id_libro:02d}{indice:02d}"


def crear_lote(cur, id_libro, titulo, cantidad_total, cantidad_disponible):
    """Inserta `cantidad_total` ejemplares nuevos para un libro recién creado.

    Recibe el cursor de una transacción en curso (se usa junto con
    libro.crear / libro.actualizar, que ya manejan su propio commit).
    """
    for i in range(1, cantidad_total + 1):
        codigo = generar_codigo(titulo, id_libro, i)
        estado = "disponible" if i <= cantidad_disponible else "danado"
        cur.execute(
            "INSERT INTO ejemplares (id_libro, codigo_inventario, estado) VALUES (%s, %s, %s)",
            (id_libro, codigo, estado)
        )


def sincronizar(cur, id_libro, titulo, cantidad_total, cantidad_disponible):
    """Ajusta la tabla `ejemplares` para que cuadre con los nuevos totales.

    - Si se aumentó `cantidad_total`, crea los ejemplares que falten.
    - Reparte `cantidad_disponible` entre los ejemplares existentes que
      no estén prestados (estado disponible/dañado/extraviado).
    """
    cur.execute("SELECT COUNT(*) AS total FROM ejemplares WHERE id_libro = %s", (id_libro,))
    total_actual = cur.fetchone()["total"]

    if cantidad_total > total_actual:
        for i in range(total_actual + 1, cantidad_total + 1):
            codigo = generar_codigo(titulo, id_libro, i)
            cur.execute(
                "INSERT INTO ejemplares (id_libro, codigo_inventario, estado) VALUES (%s, %s, 'danado')",
                (id_libro, codigo)
            )

    cur.execute(
        "SELECT id FROM ejemplares WHERE id_libro = %s AND estado != 'prestado' ORDER BY id",
        (id_libro,)
    )
    libres = cur.fetchall()
    restantes_disponibles = cantidad_disponible
    for ejemplar in libres:
        nuevo_estado = "disponible" if restantes_disponibles > 0 else "danado"
        cur.execute("UPDATE ejemplares SET estado = %s WHERE id = %s", (nuevo_estado, ejemplar["id"]))
        restantes_disponibles -= 1


def contar_todos():
    """Cuenta todas las copias físicas registradas en el inventario."""
    with get_db() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM ejemplares")
        return cur.fetchone()["total"]


def buscar_disponible(cur, id_libro):
    """Bloquea y devuelve un ejemplar disponible del libro (o None)."""
    cur.execute(
        "SELECT id, codigo_inventario FROM ejemplares "
        "WHERE id_libro = %s AND estado = 'disponible' ORDER BY id LIMIT 1 FOR UPDATE",
        (id_libro,)
    )
    return cur.fetchone()
