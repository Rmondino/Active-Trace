## ADDED Requirements

### Requirement: Scaffolding del proyecto frontend

El proyecto SHALL incluir un directorio `frontend/` con un proyecto Vite + React 18 + TypeScript. El scaffold SHALL incluir: `package.json`, `tsconfig.json`, `vite.config.ts`, `tailwind.config.ts`, `postcss.config.js`, `index.html`, y `src/main.tsx`.

#### Scenario: El proyecto se construye sin errores

- **WHEN** se ejecuta `npm install && npm run build` en `frontend/`
- **THEN** el build produce archivos en `frontend/dist/` sin errores de compilación

### Requirement: Estructura feature-based

El frontend SHALL organizarse en módulos feature-based bajo `src/features/{name}/` donde cada feature agrupa `pages/`, `components/`, `hooks/`, `services/` y `types/`. El código compartido (cross-feature) vive en `src/shared/`.

#### Scenario: Existe la estructura de directorios

- **WHEN** se inspecciona `frontend/src/`
- **THEN** existen los directorios `features/`, `shared/` y `layout/`
- **AND** `features/` contiene al menos el directorio `auth/` con subdirectorios `pages/`, `components/`, `hooks/`, `services/` y `types/`

### Requirement: Tailwind CSS configurado

El proyecto SHALL usar Tailwind CSS v3 como único sistema de estilos. No se permiten CSS modules ni estilos inline (salvo valores dinámicos calculados en runtime). Los estilos base se definen en `src/index.css` con las directivas `@tailwind base/components/utilities`.

#### Scenario: Tailwind procesa correctamente

- **WHEN** se ejecuta `npm run build`
- **THEN** los archivos CSS generados incluyen las utility classes de Tailwind usadas en los componentes

### Requirement: TypeScript estricto

El `tsconfig.json` SHALL tener `strict: true`, `noUnusedLocals: true`, y `noUnusedParameters: true`. No se permite el uso de `any`.

#### Scenario: TypeScript compila sin errores

- **WHEN** se ejecuta `npx tsc --noEmit`
- **THEN** no hay errores de tipo en ningún archivo

### Requirement: Componentes React < 200 LOC

Cada componente React (archivo `.tsx`) SHALL tener un máximo de 200 líneas. Componentes que excedan este límite SHALL dividirse en subcomponentes más pequeños.

#### Scenario: Verificación de límite de LOC

- **WHEN** se mide la cantidad de líneas de cualquier archivo `.tsx` en `frontend/src/`
- **THEN** ninguno supera las 200 líneas
