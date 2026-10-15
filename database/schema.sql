-- =====================================================================
-- Esquema biblioteca_colegio (v4 - avisos, registro ampliado y roles)
-- Fuente única de verdad de la base de datos. Consistente al 100% con
-- las consultas de app/models/*.py (mismos nombres de columna, mismos
-- tipos, mismas relaciones). Todas las tablas de "actividad" del
-- estudiante referencian usuarios.id (INT), nunca la identificación en
-- texto, para poder tener claves foráneas reales e íntegras.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS biblioteca_colegio
  CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE biblioteca_colegio;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

-- ---------------------------------------------------------------
-- usuarios
-- sede/curso reflejan la sede y el curso actual del estudiante
-- (capturados en el registro); en admins normalmente van vacíos.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  nombre          VARCHAR(100) NOT NULL,
  apellido        VARCHAR(100) NOT NULL,
  identificacion  VARCHAR(50)  NOT NULL UNIQUE,
  telefono        VARCHAR(20)  DEFAULT NULL,
  sede            ENUM('A','B') DEFAULT NULL,
  curso           VARCHAR(10)  DEFAULT NULL,
  contrasena_hash VARCHAR(255) NOT NULL,   -- hash (werkzeug.security), nunca texto plano
  rol             ENUM('estudiante','admin') NOT NULL DEFAULT 'estudiante',
  creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- libros (título / información general de catálogo)
-- cantidad_total y cantidad_disponible son contadores en caché que
-- app/models/ejemplar.py mantiene sincronizados con la tabla
-- `ejemplares`; no se editan manualmente en ningún otro lugar.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS libros (
  id                   INT AUTO_INCREMENT PRIMARY KEY,
  titulo               VARCHAR(255) NOT NULL,
  autor                VARCHAR(255) NOT NULL,
  anio                 SMALLINT UNSIGNED DEFAULT NULL,
  isbn                 VARCHAR(20)  DEFAULT NULL,
  categoria            VARCHAR(100) DEFAULT NULL,
  descripcion          TEXT,
  edicion              VARCHAR(100) DEFAULT NULL,
  editorial            VARCHAR(255) DEFAULT NULL,
  sede                 ENUM('A','B') NOT NULL,
  imagen               VARCHAR(255) DEFAULT NULL,
  seccion              VARCHAR(100) DEFAULT NULL,
  estante              VARCHAR(50)  DEFAULT NULL,
  fila                 VARCHAR(50)  DEFAULT NULL,
  cantidad_total       INT NOT NULL DEFAULT 1,
  cantidad_disponible  INT NOT NULL DEFAULT 1,
  creado_en            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_categoria (categoria),
  KEY idx_editorial (editorial),
  KEY idx_seccion (seccion),
  KEY idx_sede (sede)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- ejemplares (cada copia física de un libro)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ejemplares (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  id_libro          INT NOT NULL,
  codigo_inventario VARCHAR(50) DEFAULT NULL UNIQUE,
  estado            ENUM('disponible','prestado','danado','extraviado') NOT NULL DEFAULT 'disponible',
  creado_en         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_libro) REFERENCES libros(id) ON DELETE CASCADE,
  KEY idx_id_libro (id_libro),
  KEY idx_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- apartados (préstamo de UN ejemplar concreto a UN usuario)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS apartados (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  id_ejemplar       INT NOT NULL,
  id_usuario        INT NOT NULL,
  curso             VARCHAR(100) DEFAULT NULL,
  fecha             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_recogida    DATE DEFAULT NULL,
  fecha_recogida_real DATETIME DEFAULT NULL,
  fecha_entrega     DATE DEFAULT NULL,
  fecha_devolucion  DATETIME DEFAULT NULL,
  renovaciones      TINYINT UNSIGNED NOT NULL DEFAULT 0,
  estado            ENUM('prestado','devuelto') NOT NULL DEFAULT 'prestado',
  nota_titulo       VARCHAR(255) DEFAULT NULL,
  nota              TEXT DEFAULT NULL,
  creado_en         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_ejemplar) REFERENCES ejemplares(id) ON DELETE CASCADE,
  FOREIGN KEY (id_usuario)  REFERENCES usuarios(id)   ON DELETE CASCADE,
  KEY idx_id_ejemplar (id_ejemplar),
  KEY idx_id_usuario (id_usuario),
  KEY idx_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- lista_espera (turno FIFO por libro cuando no hay ejemplares)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lista_espera (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  id_libro         INT NOT NULL,
  id_usuario       INT NOT NULL,
  fecha_solicitud  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado           ENUM('pendiente','notificado','atendido','cancelado') NOT NULL DEFAULT 'pendiente',
  FOREIGN KEY (id_libro)   REFERENCES libros(id)   ON DELETE CASCADE,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
  UNIQUE KEY espera_unica (id_libro, id_usuario),
  KEY idx_id_libro (id_libro),
  KEY idx_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- notas (anotaciones privadas del usuario sobre un libro)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notas (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  id_libro     INT NOT NULL,
  id_usuario   INT NOT NULL,
  nota_titulo  VARCHAR(255) DEFAULT NULL,
  nota         TEXT DEFAULT NULL,
  creado_en    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_libro)   REFERENCES libros(id)   ON DELETE CASCADE,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
  KEY idx_id_libro (id_libro),
  KEY idx_id_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- valoraciones (1 a 5 estrellas, una por usuario y libro)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS valoraciones (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  id_libro    INT NOT NULL,
  id_usuario  INT NOT NULL,
  valor       TINYINT(1) NOT NULL,
  comentario  TEXT DEFAULT NULL,
  creado_en   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unica_valoracion (id_libro, id_usuario),
  FOREIGN KEY (id_libro)   REFERENCES libros(id)   ON DELETE CASCADE,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
  CONSTRAINT chk_valor CHECK (valor BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- favoritos
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS favoritos (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  id_libro    INT NOT NULL,
  id_usuario  INT NOT NULL,
  creado_en   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY favorito_unico (id_libro, id_usuario),
  FOREIGN KEY (id_libro)   REFERENCES libros(id)   ON DELETE CASCADE,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- contactos (bandeja del formulario de contacto)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contactos (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario  INT DEFAULT NULL,
  nombre      VARCHAR(100) NOT NULL,
  email       VARCHAR(150) NOT NULL,
  mensaje     TEXT NOT NULL,
  creado_en   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------
-- avisos (cartelera de anuncios de la página principal)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS avisos (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  titulo         VARCHAR(150) NOT NULL,
  contenido      TEXT NOT NULL,
  imagen         VARCHAR(255) DEFAULT NULL,
  activo         TINYINT(1) NOT NULL DEFAULT 1,
  creado_en      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =====================================================================
-- Datos de ejemplo
-- Administrador -> identificación 999999      / contraseña Admin123
-- Estudiante    -> identificación 1014872158  / contraseña Estudiante123
-- (Los hashes de abajo son reales y funcionan con esas contraseñas.
--  Cámbialas desde "Configuración" apenas pases a producción.)
-- =====================================================================
INSERT INTO usuarios (nombre, apellido, identificacion, telefono, sede, curso, contrasena_hash, rol) VALUES
('Biblioteca', 'Admin', '999999', NULL, NULL, NULL, 'scrypt:32768:8:1$VxsHFt4v5v8uw29x$ea064d66f9a46d578e99151ea2b88cf6ad8f5d26d4033d84abb4fafe6907852239e02ac45972a8064483415be4efb50e9321427d73eedfe625f4c7b6bba0eff0', 'admin'),
('Maria', 'Trujillo', '1014872158', '3000000000', 'A', '501', 'scrypt:32768:8:1$jkeiqtHSlJCBJ2E5$912ab2b6c43eea8d203f367b925f71b3801a05cce9a8e9536ff2be399325e07f4c585d296c01fe38823165079f7402caccaf3e2727737147ab56dfcffdd16be3', 'estudiante');

INSERT INTO libros (titulo, autor, anio, isbn, categoria, descripcion, edicion, editorial, sede, seccion, estante, fila, cantidad_total, cantidad_disponible) VALUES
('Cien años de soledad', 'Gabriel García Márquez', 1968, '9780307474728', 'Literatura / Realismo mágico',
 'Novela emblemática del realismo mágico que narra la historia de la familia Buendía a lo largo de varias generaciones en el mítico pueblo de Macondo.',
 '1ra Edición', 'Editorial Sudamericana', 'A', 'Literatura', 'B', '3', 2, 1),
('El Principito', 'Antoine de Saint-Exupéry', 1943, '9780156012195', 'Literatura infantil / Filosofía',
 'Un cuento poético que narra el viaje de un pequeño príncipe que recorre distintos planetas mientras reflexiona sobre la amistad y el amor.',
 'Edición ilustrada', 'Reynal & Hitchcock', 'A', 'Infantil', 'A', '1', 1, 1);

INSERT INTO ejemplares (id_libro, codigo_inventario, estado) VALUES
(1, 'CAS-0101', 'disponible'),
(1, 'CAS-0102', 'prestado'),
(2, 'EPR-0201', 'disponible');

INSERT INTO apartados (id_ejemplar, id_usuario, curso, fecha, estado) VALUES
(2, 2, '501', NOW(), 'prestado');

INSERT INTO avisos (titulo, contenido, activo) VALUES
('¡Bienvenidos al nuevo año escolar!', 'La biblioteca abre sus puertas con nuevas colecciones de literatura infantil y juvenil. Ven a explorarlas.', 1),
('Semana del libro', 'Del 15 al 19 de septiembre tendremos actividades de lectura en voz alta y un club de intercambio de libros.', 1);
