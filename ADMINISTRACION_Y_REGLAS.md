# Guía de administración de la biblioteca

## 1. Inventario: contar copias físicas, no solo títulos

Cada título puede tener varios ejemplares con código de inventario propio. La cantidad disponible se reduce al crear un préstamo y aumenta al registrar una devolución.

**Ejemplo con tres copias de un mismo libro**
1. Inicio: 3 disponibles.
2. El estudiante A se lleva una: 2 disponibles y 1 préstamo activo.
3. El estudiante B se lleva otra: 1 disponible.
4. El estudiante C se lleva la última: 0 disponibles.
5. El siguiente estudiante no puede apartarlo y puede apuntarse a la lista de espera.
6. Cuando una copia vuelve, el sistema incrementa el inventario y marca como `notificado` al turno pendiente más antiguo.

No cambies manualmente la cantidad disponible sin comprobar el estado de los ejemplares. Una copia prestada no debe contarse como disponible.

## 2. Lista de espera

- Se permite un solo turno por estudiante y título.
- Se usa orden FIFO: primero en entrar, primero en ser atendido.
- Si hay disponibilidad, la aplicación debe invitar a apartar el libro en lugar de duplicar turnos.
- Al devolver un ejemplar, el primer turno pendiente pasa a `notificado` y queda visible para administración.
- **Importante:** en esta versión, `notificado` es una marca de gestión interna; no envía automáticamente correo, SMS ni notificación push, y la copia no queda bloqueada exclusivamente para ese estudiante. Administración debe contactar al estudiante y coordinar la entrega. Para garantizar el turno de forma automática, el siguiente paso sería implementar una reserva temporal con vencimiento.

## 3. Préstamos y devoluciones

- Verificar identidad y curso del estudiante al entregar el libro.
- Registrar la fecha de recogida y una fecha de entrega futura.
- Al devolver, confirmar el ejemplar correcto y registrar la devolución una sola vez.
- Revisar diariamente los préstamos vencidos desde el panel.
- No borrar un libro con préstamos activos sin revisar antes su historial.

## 4. Anuncios gráficos

Ruta: **Administración → Avisos → Nuevo aviso**.

- Subir una imagen tipo cartel; no hace falta escribir título ni descripción.
- Formatos admitidos: PNG, JPG, JPEG, GIF y WEBP; máximo 5 MB.
- Revisar la vista previa antes de publicar.
- Ocultar los anuncios vencidos en vez de acumular campañas antiguas en la página principal.
- Usar imágenes legibles, con buen contraste y texto grande para estudiantes.

## 5. Revisión diaria sugerida para administración

- [ ] Comprobar préstamos vencidos y devoluciones del día.
- [ ] Revisar la lista de espera y contactar a quien tenga el turno más antiguo.
- [ ] Confirmar que las cantidades del catálogo coinciden con las copias físicas.
- [ ] Ocultar anuncios caducados.
- [ ] Revisar mensajes de contacto y cuentas nuevas.
- [ ] Hacer copia de seguridad de la base de datos según la política del colegio.

## 6. Antes de publicar la aplicación

- Cambiar la clave secreta y las contraseñas de ejemplo.
- Configurar la conexión de base de datos con variables de entorno.
- Probar con una copia de seguridad de la base real; no ejecutar migraciones directamente sobre datos únicos sin respaldo.
- Probar los flujos de préstamo, devolución, falta de disponibilidad, duplicación de turnos y carga de imágenes.
