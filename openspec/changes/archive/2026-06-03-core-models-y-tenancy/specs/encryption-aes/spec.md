## ADDED Requirements

### Requirement: Cifrado AES-256-GCM para PII en reposo

El sistema SHALL proveer una utilidad de cifrado simétrico AES-256 en modo GCM para proteger datos personales sensibles (PII) marcados como `[cifrado]` en el modelo de datos (CBU, DNI, email, CUIL).

#### Scenario: Cifrado round-trip

- **WHEN** se cifra un texto plano con la clave de ENCRYPTION_KEY
- **THEN** el resultado es un string base64 que contiene nonce + ciphertext + tag
- **AND** al descifrar ese resultado con la misma clave, se obtiene el texto original

#### Scenario: Clave de 32 bytes

- **WHEN** se intenta usar una clave que no tiene exactamente 32 bytes
- **THEN** la operación de cifrado/descifrado falla con un error claro

#### Scenario: Nonce único por cifrado

- **WHEN** se cifra el mismo texto plano dos veces
- **THEN** los ciphertext resultantes son diferentes (nonce aleatorio)

#### Scenario: Datos cifrados no expuestos en texto plano

- **WHEN** un valor cifrado se persiste en la base de datos
- **THEN** el dato almacenado NO contiene el texto plano original
- **AND** el texto plano solo es accesible mediante la función de descifrado

### Requirement: No exponer PII en logs

El sistema SHALL garantizar que ningún dato PII (email, DNI, CUIL, CBU) aparezca en texto plano en logs, excepciones o respuestas de error no autorizadas.

#### Scenario: Log sin PII

- **WHEN** se registra un evento que involucra un dato PII
- **THEN** el log contiene el valor cifrado o un marcador como `[REDACTED]`, nunca el texto plano
