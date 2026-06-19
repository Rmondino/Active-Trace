## ADDED Requirements

### Requirement: Visualización del umbral actual

El sistema SHALL mostrar el umbral de aprobación actual para la materia seleccionada (obtenido de `GET /api/umbral?materia_id=X`). SHALL mostrar el porcentaje y los valores textuales aprobatorios. Si no hay umbral configurado, SHALL mostrar los valores por defecto (60% y "Satisfactorio", "Supera lo esperado").

#### Scenario: Umbral configurado

- **WHEN** el PROFESOR ve la sección de umbral para una materia con umbral configurado
- **THEN** se muestra el porcentaje actual y los valores aprobatorios

#### Scenario: Umbral sin configurar (defaults)

- **WHEN** el PROFESOR ve la sección de umbral para una materia sin configuración
- **THEN** se muestran los valores por defecto (60%, Satisfactorio/Supera lo esperado)

### Requirement: Configuración del umbral

El sistema SHALL permitir al PROFESOR modificar el umbral mediante un slider o input numérico (0-100) para el porcentaje, y un input de texto para los valores aprobatorios. SHALL tener un botón "Guardar" que llame a `PUT /api/umbral?materia_id=X`.

#### Scenario: Guardar umbral exitoso

- **WHEN** el PROFESOR cambia el porcentaje y/o los valores aprobatorios y hace clic en "Guardar"
- **THEN** el sistema llama a `PUT /api/umbral` con los nuevos valores
- **AND** muestra mensaje de confirmación "Umbral actualizado"
