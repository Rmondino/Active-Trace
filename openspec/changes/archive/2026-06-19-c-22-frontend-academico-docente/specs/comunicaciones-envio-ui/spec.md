## ADDED Requirements

### Requirement: Selección de alumnos desde tabla de atrasados

El sistema SHALL permitir seleccionar alumnos en la tabla de atrasados mediante checkboxes. Los seleccionados SHALL pasar al flujo de comunicación. SHALL haber un botón "Comunicar seleccionados" que lleve a la pestaña de comunicación con esos alumnos precargados.

#### Scenario: Seleccionar alumnos para comunicar

- **WHEN** el PROFESOR selecciona uno o más alumnos en la tabla de atrasados
- **THEN** el botón "Comunicar seleccionados" muestra el count de seleccionados
- **AND** al hacer clic, navega a la pestaña de comunicación con esos alumnos

### Requirement: Formulario de comunicación con templates

El sistema SHALL mostrar un formulario con campos de asunto y cuerpo que aceptan placeholders `{alumno_nombre}`, `{alumno_apellidos}`, `{materia}`, `{comision}`. SHALL tener inputs de texto con indicación visual de los placeholders disponibles.

#### Scenario: Formulario de comunicación visible

- **WHEN** el PROFESOR navega a la pestaña de comunicación con alumnos seleccionados
- **THEN** se muestran los campos de asunto y cuerpo con ayuda de placeholders
- **AND** se muestra la lista de destinatarios seleccionados

### Requirement: Preview de comunicación

El sistema SHALL generar una vista previa de la comunicación para cada alumno seleccionado (`POST /api/comunicaciones/preview`). SHALL mostrar el asunto y cuerpo renderizados (con placeholders reemplazados) para cada destinatario.

#### Scenario: Preview generado exitosamente

- **WHEN** el PROFESOR completa el template y hace clic en "Vista previa"
- **THEN** el sistema llama a `POST /api/comunicaciones/preview`
- **AND** muestra el asunto y cuerpo renderizados para cada alumno

### Requirement: Envío de comunicación

El sistema SHALL tener un botón "Enviar" que llame a `POST /api/comunicaciones/enviar` con el preview_token, asunto, cuerpo y destinatarios. SHALL mostrar el resultado (lote_id, total, requiere_aprobación).

#### Scenario: Envío exitoso

- **WHEN** el PROFESOR confirma el envío después de ver el preview
- **THEN** el sistema llama a `POST /api/comunicaciones/enviar`
- **AND** muestra mensaje de éxito con el total de comunicaciones encoladas

### Requirement: Tracking de comunicaciones

El sistema SHALL mostrar el estado de las comunicaciones enviadas para la materia (`GET /api/comunicaciones?materia_id=X`) en una tabla con: destinatario (enmascarado), asunto, estado, fecha de envío.

#### Scenario: Tracking visible

- **WHEN** el PROFESOR ve la sección de tracking
- **THEN** se muestra una tabla con las comunicaciones enviadas y su estado
- **AND** los estados se muestran con colores: Pendiente (amarillo), Enviado (verde), Error (rojo), Cancelado (gris)
