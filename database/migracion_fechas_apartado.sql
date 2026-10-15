-- ---------------------------------------------------------------
-- Migración: fecha de recogida/entrega en apartados + reseña escrita
-- en valoraciones. Ejecutar UNA sola vez sobre una base de datos que
-- ya existía antes de este cambio (si la base es nueva, no hace
-- falta: schema.sql ya incluye estas columnas).
-- ---------------------------------------------------------------

ALTER TABLE apartados
  ADD COLUMN fecha_recogida DATE DEFAULT NULL AFTER fecha,
  ADD COLUMN fecha_entrega  DATE DEFAULT NULL AFTER fecha_recogida;

ALTER TABLE valoraciones
  ADD COLUMN comentario TEXT DEFAULT NULL AFTER valor;
