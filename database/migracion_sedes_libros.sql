-- Ejecutar una sola vez en instalaciones existentes.
-- Los libros y préstamos históricos se asignan a Sede A, conforme a la
-- decisión de migración. Los nuevos libros deben informar su sede al crearse.
USE biblioteca_colegio;

ALTER TABLE libros
  ADD COLUMN sede ENUM('A','B') DEFAULT NULL AFTER editorial;

UPDATE libros SET sede = 'A' WHERE sede IS NULL;

ALTER TABLE libros
  MODIFY COLUMN sede ENUM('A','B') NOT NULL;

CREATE INDEX idx_sede ON libros (sede);
