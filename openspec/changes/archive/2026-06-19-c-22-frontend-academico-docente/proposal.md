## Why

C-21 estableció el shell del frontend (login, layout, guard), pero el producto sigue sin funcionalidad académica real. C-22 es el primer change de frontend con valor de negocio: permite al PROFESOR importar calificaciones desde el LMS, detectar alumnos atrasados, configurar umbral de aprobación, y comunicarse con los atrasados — el flujo central del producto (FL-02). Sin esto, el frontend es una cáscara vacía.

## What Changes

- **Nuevo feature**: `comision/` — módulo de gestión de comisión del PROFESOR
- **Selector de materia/cohorte**: pantalla para elegir qué comisión gestionar
- **Importación de calificaciones**: upload de archivo CSV/XLSX, preview con actividades detectadas, selector de actividades, confirmación
- **Configuración de umbral**: slider/input de porcentaje con valores aprobatorios textuales
- **Vista de alumnos atrasados**: tabla con indicadores de causa (faltantes / baja nota)
- **Ranking y reportes**: ranking de aprobados y reporte rápido por materia
- **Notas finales**: vista consolidada de notas por alumno
- **Comunicación a atrasados**: selección de alumnos, preview con plantillas, envío, tracking de estado
- **Exportación**: descarga de XLSX de entregas sin corregir

## Capabilities

### New Capabilities
- `calificaciones-import-ui`: Upload de archivo, preview con selector de actividades, confirmación
- `umbral-config-ui`: Configuración visual del umbral de aprobación (porcentaje + valores textuales)
- `analisis-atrasados-ui`: Tabla de alumnos atrasados con causas, ranking, reporte rápido, notas finales, monitor
- `comunicaciones-envio-ui`: Preview con templates, envío, tracking de estado y aprobación

### Modified Capabilities
- `app-layout`: Agregar items de navegación para las nuevas features académicas (sidebar)
- `frontend-shell`: Agregar rutas de las nuevas features al router

## Impact

- **Nuevo directorio**: `frontend/src/features/comision/` con toda la feature
- **Nuevo directorio**: `frontend/src/features/comunicaciones/` (compartido entre C-22 y futuros features)
- **Modificaciones**: `frontend/src/App.tsx` (nuevas rutas), `frontend/src/layout/Sidebar.tsx` (nuevos items de menú)
- **Dependencias nuevas**: `@tanstack/react-table` (ya en package.json), `xlsx` o similar para export preview
