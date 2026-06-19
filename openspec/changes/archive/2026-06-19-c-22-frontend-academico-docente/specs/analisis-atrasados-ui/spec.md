## ADDED Requirements

### Requirement: Tabla de alumnos atrasados

El sistema SHALL mostrar una tabla con los alumnos atrasados de la materia+cohorte seleccionada (`GET /api/analisis/atrasados?materia_id=X&cohorte_id=Y`). La tabla SHALL mostrar: nombre del alumno, comisión, total de actividades, aprobadas, desaprobadas, sin nota, y causas (faltantes / baja nota). SHALL soportar sorting por columna y resaltar visualmente las causas de atraso.

#### Scenario: Tabla de atrasados con datos

- **WHEN** el PROFESOR navega a la pestaña de atrasados para una materia con alumnos atrasados
- **THEN** se muestra una tabla con los alumnos, indicando cuáles están atrasados y por qué causa

#### Scenario: Sin alumnos atrasados

- **WHEN** todos los alumnos están al día
- **THEN** la tabla muestra un mensaje "No hay alumnos atrasados" o está vacía

### Requirement: Ranking de aprobados

El sistema SHALL mostrar un ranking de alumnos por cantidad de actividades aprobadas (`GET /api/analisis/ranking?materia_id=X`) en una tabla ordenada descendente. SHALL mostrar nombre, cantidad aprobada, total y porcentaje.

#### Scenario: Ranking visible

- **WHEN** el PROFESOR selecciona la vista de ranking
- **THEN** se muestra el ranking ordenado de más a menos aprobadas

### Requirement: Reporte rápido

El sistema SHALL mostrar un reporte consolidado de la materia (`GET /api/analisis/reporte-rapido?materia_id=X`) con tarjetas resumen: total alumnos, total actividades, alumnos atrasados, tasa de aprobación general, y tabla de actividades con tasa de aprobación y promedio.

#### Scenario: Reporte rápido visible

- **WHEN** el PROFESOR selecciona la vista de reporte rápido
- **THEN** se muestran tarjetas con las métricas de la materia

### Requirement: Notas finales consolidadas

El sistema SHALL mostrar una tabla de notas finales por alumno (`GET /api/analisis/notas-finales?materia_id=X&cohorte_id=Y`) con todas las actividades como columnas dinámicas, promedio numérico y total de aprobadas.

#### Scenario: Notas finales visibles

- **WHEN** el PROFESOR selecciona la vista de notas finales
- **THEN** se muestra una tabla con alumnos como filas y actividades como columnas, más promedio

### Requirement: Exportación de entregas sin corregir

El sistema SHALL proveer un botón "Exportar sin corregir" que descargue un archivo XLSX (`GET /api/analisis/exportar-sin-corregir?materia_id=X`).

#### Scenario: Exportación exitosa

- **WHEN** el PROFESOR hace clic en "Exportar sin corregir"
- **THEN** el sistema descarga un archivo XLSX con las entregas sin corregir
