## ADDED Requirements

### Requirement: ABM Salario Base

El sistema SHALL permitir CRUD de salario base por rol (COORDINADOR, NEXO, PROFESOR, TUTOR) con monto y vigencia (desde/hasta).

#### Scenario: Crear salario base

- **WHEN** FINANZAS crea un salario base para PROFESOR con monto 500000 y vigencia desde 2026-01-01
- **THEN** el registro se guarda y está disponible para cálculos

### Requirement: ABM Salario Plus

El sistema SHALL permitir CRUD de plus salarial por (grupo × rol) con monto, vigencia y tope de acumulación nullable.

### Requirement: ABM MateriaGrupoPlus

El sistema SHALL permitir mapear materias a grupos de plus con vigencia temporal (PA-22). Un grupo es un string libre.
