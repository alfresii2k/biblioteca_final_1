-- Ejecutar una sola vez en bases existentes para registrar la recogida real.
ALTER TABLE apartados
  ADD COLUMN fecha_recogida_real DATETIME DEFAULT NULL AFTER fecha_recogida;