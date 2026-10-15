"""Capa de acceso a datos (modelos).

Cada módulo agrupa TODAS las consultas SQL relacionadas con una tabla
del dominio. Los blueprints (app/blueprints/*) nunca escriben SQL
directamente: llaman a estas funciones. Así el SQL vive en un solo
lugar, con nombres de columna consistentes con database/schema.sql.
"""
