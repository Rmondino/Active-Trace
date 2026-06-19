## Why

Activia-trace tiene todo el backend implementado (C-01→C-14) pero **carece de interfaz de usuario**. Sin un frontend, el producto no es utilizable por los actores del dominio (PROFESOR, COORDINADOR, ADMIN, etc.). Este change establece la base de la SPA: shell de navegación, autenticación completa (login, 2FA, recuperación de contraseña), guard de rutas por permiso y layout adaptativo. Es el cimiento sobre el que se construirán todas las features de frontend (C-22, C-23, C-24).

## What Changes

- **Scaffolding** del proyecto frontend con React 18 + TypeScript + Vite + Tailwind CSS
- **Cliente HTTP centralizado** (Axios) con interceptor de auth y refresh transparente de tokens
- **Pantalla de login** con email + password, manejo de errores y rate limiting UX
- **Pantalla de 2FA** (ingreso de código TOTP post-login cuando el usuario tiene 2FA habilitado)
- **Pantalla de configuración de 2FA** (enroll + verify con QR code)
- **Pantalla de recuperación de contraseña** (forgot + reset)
- **Guard de rutas por permiso** (Route Protection) que redirige a login sin sesión
- **Layout principal** con menú lateral/header adaptado a los permisos del usuario
- **Logout** (cierre de sesión con revocación de token)
- **CORS middleware** en el backend (necesario para que el frontend se conecte)
- **Endpoint `POST /api/auth/2fa/authenticate`** en el backend para completar el flujo de login con 2FA (actualmente devuelve `session_token` pero no hay forma de canjearlo por tokens reales)
- **Fix de schemas de auth** con `extra='forbid'` para cumplir la regla dura #5

## Capabilities

### New Capabilities
- `frontend-shell`: Scaffolding Vite + React + TS + Tailwind + estructura feature-based
- `auth-ui`: Login, 2FA (enroll + authenticate), forgot/reset password, logout
- `http-client`: Cliente Axios centralizado con interceptors, refresh transparente, manejo de 401/403
- `route-guard`: Protección de rutas por autenticación y permisos
- `app-layout`: Layout principal con sidebar/header adaptativo por rol

### Modified Capabilities
- `user-auth` (backend): Agregar `POST /api/auth/2fa/authenticate` para completar login con 2FA
- `api`: Agregar CORS middleware para permitir conexiones del frontend

## Impact

- **Nuevo directorio**: `frontend/` con toda la estructura
- **Backend**: `backend/app/main.py` — agregar CORS middleware
- **Backend**: `backend/app/routers/auth.py` — nuevo endpoint 2fa/authenticate, fix extra='forbid'
- **Backend**: `backend/app/services/auth_service.py` — nuevo service `authenticate_2fa`
- **Dependencias nuevas** (frontend): react, react-dom, react-router-dom, @tanstack/react-query, axios, react-hook-form, @hookform/resolvers, zod, tailwindcss, postcss, autoprefixer, qrcode (para QR 2FA)
- **DevDependencies**: typescript, @types/react, @types/react-dom, vite, @vitejs/plugin-react, tailwindcss, postcss, autoprefixer, vitest, @testing-library/react, @testing-library/jest-dom, jsdom
