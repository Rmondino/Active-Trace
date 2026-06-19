## ADDED Requirements

### Requirement: Bandeja de entrada

El sistema SHALL listar los mensajes recibidos por el usuario autenticado, ordenados del más reciente al más antiguo. Cada mensaje SHALL mostrar: remitente, asunto (primeros caracteres del cuerpo), fecha, y si fue leído o no.

#### Scenario: Bandeja con mensajes

- **WHEN** el usuario autenticado navega a su bandeja de entrada
- **THEN** se muestran los mensajes recibidos ordenados por fecha descendente

#### Scenario: Bandeja vacía

- **WHEN** el usuario no tiene mensajes
- **THEN** se muestra un mensaje "No tenés mensajes"

### Requirement: Ver detalle de mensaje

El sistema SHALL mostrar el contenido completo de un mensaje (remitente, cuerpo, fecha) y marcarlo como leído automáticamente.

### Requirement: Responder mensaje

El sistema SHALL permitir responder a un mensaje dentro del mismo hilo. La respuesta SHALL quedar asociada al mensaje original.

### Requirement: Nuevo mensaje

El sistema SHALL permitir enviar un nuevo mensaje a otro usuario del sistema (selector de destinatario + cuerpo).

### Requirement: Marcar como leído

El sistema SHALL marcar un mensaje como leído automáticamente al abrirlo (`PATCH /api/inbox/{id}/leer` o implícito al obtener detalle).
