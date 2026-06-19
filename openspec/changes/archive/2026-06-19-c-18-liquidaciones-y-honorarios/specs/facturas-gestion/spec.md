## ADDED Requirements

### Requirement: CRUD Facturas

El sistema SHALL permitir a docentes facturantes cargar facturas (detalle, archivo adjunto) y a FINANZAS listarlas, ver detalle y marcarlas como abonadas.

#### Scenario: Cargar factura

- **WHEN** un docente facturante sube una factura con detalle y archivo
- **THEN** la factura queda en estado Pendiente

#### Scenario: Abonar factura

- **WHEN** FINANZAS marca una factura como abonada
- **THEN** cambia a estado Abonada con fecha de pago
