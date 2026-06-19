## ADDED Requirements

### Requirement: Ver perfil propio

El sistema SHALL mostrar el perfil del usuario autenticado con todos los campos descifrados: nombre, apellidos, email, DNI, CUIL (solo lectura), CBU, alias CBU, banco, regional, legajo, facturador, estado. Usa `GET /api/usuarios/me`.

#### Scenario: Perfil visible

- **WHEN** el usuario autenticado navega a su perfil
- **THEN** se muestran todos los campos del perfil con sus valores actuales

### Requirement: Editar perfil propio

El sistema SHALL permitir al usuario editar su perfil mediante `PUT /api/usuarios/me`. Los campos editables SHALL ser: nombre, apellidos, CBU, alias CBU, banco, regional. CUIL SHALL ser solo lectura (no modificable).

#### Scenario: Edición exitosa

- **WHEN** el usuario modifica campos editables y guarda
- **THEN** el sistema llama a `PUT /api/usuarios/me`
- **AND** muestra los valores actualizados
