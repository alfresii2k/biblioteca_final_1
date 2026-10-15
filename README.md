# 📚 Biblioteca Colegio — Backend refactorizado

Sistema web de biblioteca escolar (Flask + MySQL). Esta versión conserva
el **diseño visual original** (mismas plantillas, mismos estilos) pero
reconstruye por completo el **backend**: modelo de datos, autenticación,
acceso a la base de datos y la lógica de negocio de préstamos.

---

## ¿Qué cambió respecto a la versión anterior?

La versión anterior funcionaba "a medias" porque el código y la base de
datos se habían desincronizado con el tiempo. Esto es lo que se corrigió:

| Problema encontrado | Solución aplicada |
|---|---|
| Contraseñas guardadas y comparadas **en texto plano** | Hash seguro con `werkzeug.security` (PBKDF2/scrypt) |
| Columnas usadas en el código que **no existían** en la BD (`año` vs `anio`, `codigo` vs `codigo_inventario`, `contraseña` vs `contrasena_hash`, `disponible`) | Un único `database/schema.sql` consistente con el código |
| Tablas mezclando `identificacion` (texto) e `id_usuario` (número) como clave foránea, según la consulta | Todo unificado a `usuarios.id` (INT) con claves foráneas reales |
| El formulario de "Contacto" **no guardaba nada** en la base de datos | Ahora sí inserta en `contactos`, con campo de correo agregado |
| La carpeta `models/` del proyecto raíz no se usaba y tenía archivos corruptos/mezclados (uno de ellos ni siquiera era código Python) | Se eliminó por completo y se reemplazó por `app/models/`, una capa de acceso a datos real |
| SQL duplicado y repetido dentro de cada ruta (`routes.py`) | Todo el SQL vive en `app/models/*.py`; las rutas solo orquestan |
| Un libro "prestado" no tenía forma de volver a estar disponible | Se agregó un botón **"Marcar devuelto"** en el panel admin (`/apartados`) |
| Cada ruta repetía `if 'user' not in session: redirect(...)` | Decoradores `@login_required`, `@admin_required`, `@usuario_required` |
| Migraciones con `ALTER TABLE ... IF NOT EXISTS` corriendo en cada arranque | Un solo `schema.sql` que se ejecuta **una sola vez** (si la tabla `usuarios` no existe) |
| Credenciales de BD y `SECRET_KEY` quemadas en el código | Configurables por variables de entorno (`.env`) |

**Se modificó la base de datos** (nombres de columnas y algunas
relaciones) porque era la única forma de dejar todo consistente, tal
como se autorizó. El detalle completo está en `database/schema.sql`.

---

## Novedades de esta versión (segunda ronda de cambios)

| Pedido | Qué se implementó |
|---|---|
| Cartel de anuncios en la página principal | Tabla `avisos` + panel admin (`/avisos`) para crear, editar, ocultar/mostrar y eliminar avisos. Solo los avisos activos aparecen en la landing, antes de iniciar sesión |
| Horarios, dirección, reglas y reseña histórica | Sección fija en la landing, con el contenido centralizado en `app/content.py` (fácil de editar sin tocar plantillas ni la BD) |
| Carrusel/galería de imágenes | Componente Bootstrap Carousel en la landing, usando `app/content.py` para la lista de imágenes |
| Campo de teléfono en el registro | Columna `usuarios.telefono`, campo obligatorio en `/register` |
| Sede y curso dinámicos | Columnas `usuarios.sede` (`A`/`B`) y `usuarios.curso`. El select de curso se llena por JavaScript según la sede elegida (`app/content.py::SEDES_CURSOS`), y se valida también en el servidor |
| Renombrar "Usuario" → "Estudiante" | El rol en la base de datos ahora es el ENUM `('estudiante','admin')`; toda la interfaz (badges, menús, formularios) usa "Estudiante" |
| Gestión de administradores | Página `/usuarios` (solo admin): crea nuevas cuentas de administrador y promueve/degrada el rol de cualquier cuenta existente (no se puede auto-degradar) |

Cuando un estudiante aparta un libro, su `curso` (guardado en el
registro) se copia automáticamente al préstamo — ya no hay que
volver a pedirlo en el formulario de apartado.

---

## Estructura del proyecto

```
biblioteca_app/
├── run.py                     # Punto de entrada (python run.py)
├── requirements.txt
├── .env.example                # Variables de entorno (copiar a .env)
├── database/
│   └── schema.sql               # ÚNICA fuente de verdad de la BD
└── app/
    ├── __init__.py               # Application factory
    ├── config.py                 # Configuración (lee .env)
    ├── content.py                 # Textos institucionales + sedes/cursos (sin BD)
    ├── models/                   # Acceso a datos (SQL vive aquí)
    │   ├── usuario.py, libro.py, ejemplar.py, apartado.py, aviso.py,
    │   └── lista_espera.py, nota.py, valoracion.py, favorito.py, contacto.py
    ├── utils/
    │   ├── db.py                  # Conexión MySQL + context manager get_db()
    │   ├── auth.py                # Decoradores @login_required / @admin_required / @estudiante_required
    │   ├── security.py            # Hash y verificación de contraseñas
    │   └── schema.py              # Inicializa la BD la primera vez
    ├── blueprints/                # Rutas, agrupadas por área (sin SQL directo)
    │   ├── auth/, pagina/, libros/, usuario/, admin/, contacto/
    ├── templates/                 # HTML (mismo diseño visual original)
    └── static/                    # CSS, JS, imágenes, subidas de portadas
```

---

## Instalación

1. **Requisitos**: Python 3.10+ y un servidor MySQL/MariaDB corriendo.

2. **Entorno virtual y dependencias**
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Variables de entorno**
   ```bash
   cp .env.example .env
   # Edita .env con tu usuario/contraseña de MySQL
   ```
   La app funciona incluso sin `.env` (usa `root` sin contraseña en
   `localhost`, igual que antes), pero en producción define siempre tu
   propio `SECRET_KEY`.

   > Si vienes de la versión anterior de este proyecto y ya tenías la
   > base de datos creada, bórrala y vuelve a crearla con el
   > `schema.sql` nuevo (o migra manualmente agregando las columnas
   > `telefono`, `sede`, `curso` a `usuarios`, renombrando el ENUM de
   > `rol` a `('estudiante','admin')` y creando la tabla `avisos`).

4. **Arrancar la aplicación**
   ```bash
   python run.py
   ```
   En el primer arranque, si la base de datos `biblioteca_colegio` (o la
   tabla `usuarios`) no existe todavía, la app la crea automáticamente
   ejecutando `database/schema.sql` (tablas + datos de ejemplo). Si ya
   existe, no la vuelve a tocar.

   Si prefieres crearla tú mismo antes de arrancar:
   ```bash
   mysql -u root -p < database/schema.sql
   ```

5. Abre **http://localhost:5000**

---

## Usuarios de prueba (vienen en `schema.sql`)

| Rol | Identificación | Contraseña |
|---|---|---|
| Administrador | `999999` | `Admin123` |
| Estudiante | `1014872158` | `Estudiante123` |

Cámbialas desde "Configuración" apenas pases a un entorno real.

---

## Notas de arquitectura

- **`app/models/`** contiene toda la lógica de acceso a datos. Las
  rutas (`app/blueprints/*/routes.py`) nunca escriben SQL: llaman a
  funciones de los modelos. Esto evita el problema original de tener
  la misma consulta copiada (y desactualizada) en varios archivos.
- **`get_db()`** (`app/utils/db.py`) es un *context manager*: abre
  conexión, hace `commit` si todo sale bien, `rollback` si algo falla,
  y siempre cierra cursor y conexión. Ya no hay bloques `try/finally`
  repetidos en cada función.
- **`apartado.crear()`** concentra en una sola transacción: buscar un
  ejemplar disponible, crear el préstamo, marcar el ejemplar como
  prestado y descontar el contador del libro. Antes esos 3-4 pasos
  podían quedar a medias si algo fallaba en el medio.
- **`libros.cantidad_total` / `cantidad_disponible`** siguen existiendo
  como contadores en caché (para no tener que hacer `COUNT()` sobre
  `ejemplares` en cada listado), pero ahora solo `app/models/ejemplar.py`
  tiene permiso de tocarlos, así nunca se desincronizan.
- **`app/content.py`** guarda contenido institucional (horarios,
  reglas, reseña, sedes/cursos, imágenes del carrusel) fuera de la
  base de datos porque son datos que casi nunca cambian; así se editan
  en un solo archivo Python sin tocar plantillas ni ejecutar SQL.
- La validación de **sede/curso** ocurre dos veces: en el navegador
  (JavaScript en `register.html`, para una mejor experiencia) y en el
  servidor (`auth/routes.py`, contra `app/content.py::SEDES_CURSOS`),
  para que nadie pueda saltarse la regla enviando el formulario a mano.

## Próximos pasos opcionales (no incluidos, para no tocar más de lo pedido)

- Notificar automáticamente a la lista de espera cuando se libera un ejemplar.
- Paginación en `/books` si el catálogo crece mucho.
- Recuperación de contraseña por correo.
- Subir imagen propia para cada aviso (el modelo ya soporta el campo `imagen`, falta el formulario de carga).


## Reglas operativas recomendadas para la biblioteca

- **Inventario por ejemplar:** cada copia física tiene un código único. Si hay 3 copias disponibles y se presta una, quedan 2 disponibles; al devolverla, vuelve a haber 3.
- **Lista de espera FIFO:** se ordena por fecha de solicitud, primero quien llegó primero. Al registrar una devolución se marca como `notificado` el siguiente turno pendiente para que administración gestione el aviso.
- **Anuncios gráficos:** desde Administración → Avisos se suben carteles en PNG, JPG, JPEG, GIF o WEBP. No se redacta contenido publicitario. El límite es 5 MB.
- **Préstamos:** registrar recogida, fecha límite y devolución desde el panel administrativo. Revisar préstamos vencidos y contactar al estudiante según el protocolo del colegio.
- **Buenas prácticas antes de producción:** cambiar la clave secreta y las contraseñas de ejemplo, configurar copias de seguridad de MariaDB y validar los datos reales antes de migrar.
