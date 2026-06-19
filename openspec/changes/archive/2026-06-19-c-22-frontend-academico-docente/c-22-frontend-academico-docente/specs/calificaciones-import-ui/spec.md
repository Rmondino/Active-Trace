## ADDED Requirements

### Requirement: Upload de archivo de calificaciones

El sistema SHALL proveer un componente de upload de archivo que permita al PROFESOR seleccionar un archivo CSV o XLSX desde su sistema de archivos. Al seleccionar el archivo, SHALL mostrar el nombre, tamaño y tipo del archivo antes de enviarlo. SHALL incluir un botón "Previsualizar" que llame a `POST /api/calificaciones/import` con `confirm=false`, materia_id y cohorte_id.

#### Scenario: Upload exitoso con preview

- **WHEN** el PROFESOR selecciona un archivo CSV/XLSX válido y hace clic en "Previsualizar"
- **THEN** el sistema envía el archivo a `POST /api/calificaciones/import` con `confirm=false`
- **AND** muestra la preview con actividades detectadas, tipo (numérica/textual), y una muestra de alumnos con sus valores

#### Scenario: Error en el upload

- **WHEN** el servidor devuelve un error (archivo inválido, formato incorrecto)
- **THEN** el sistema muestra el mensaje de error del servidor

### Requirement: Selector de actividades para importación

El sistema SHALL mostrar las actividades detectadas en el preview como una lista con checkboxes, cada una con su nombre y tipo (numérica/textual). Por defecto, todas las actividades SHALL estar seleccionadas. El PROFESOR puede deseleccionar actividades que no quiere incluir.

#### Scenario: Selección de actividades

- **WHEN** el PROFESOR deselecciona una o más actividades
- **THEN** esas actividades NO se incluyen en la importación al confirmar

### Requirement: Confirmación de importación

El sistema SHALL tener un botón "Confirmar importación" que llame a `POST /api/calificaciones/preview/{preview_id}/confirm` con el array de actividades seleccionadas. Al confirmar, SHALL mostrar el resultado (total de calificaciones importadas, total de aprobados).

#### Scenario: Confirmación exitosa

- **WHEN** el PROFESOR hace clic en "Confirmar importación"
- **THEN** el sistema envía las actividades seleccionadas al endpoint de confirmación
- **AND** muestra el total de calificaciones importadas y aprobados

### Requirement: Importación de completions (entregas sin corregir)

El sistema SHALL proveer un segundo upload para el reporte de finalización del LMS (completions). SHALL llamar a `POST /api/calificaciones/import/completions` y mostrar las entregas sin corregir detectadas.

#### Scenario: Carga de completions exitosa

- **WHEN** el PROFESOR sube un archivo de completions
- **THEN** el sistema muestra la lista de entregas sin corregir (alumno + actividad)
