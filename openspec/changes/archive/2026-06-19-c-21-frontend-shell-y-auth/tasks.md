## 1. Backend — CORS middleware

- [x] 1.1 Agregar `CORS_ORIGINS` a `Settings` en `backend/app/core/config.py` (default `http://localhost:5173,http://localhost:3000`)
- [x] 1.2 Agregar `CORSMiddleware` en `backend/app/main.py` con los orígenes configurados
- [x] 1.3 Agregar `CORS_ORIGINS` al `.env.example`

## 2. Backend — 2FA authenticate endpoint

- [x] 2.1 Crear schema `Authenticate2FARequest` y `Authenticate2FAResponse` en `backend/app/routers/auth.py` con `extra='forbid'`
- [x] 2.2 Agregar schema `LoginResponse` con `extra='forbid'` (fix regla dura #5)
- [x] 2.3 Agregar schema `RefreshResponse` con `extra='forbid'` (fix regla dura #5)
- [x] 2.4 Agregar schema `RefreshRequest` con `extra='forbid'` (fix regla dura #5)
- [x] 2.5 Agregar schema `LogoutRequest` con `extra='forbid'` (fix regla dura #5)
- [x] 2.6 Agregar schema `ForgotRequest` con `extra='forbid'` (fix regla dura #5)
- [x] 2.7 Agregar schema `ResetRequest` con `extra='forbid'` (fix regla dura #5)
- [x] 2.8 Agregar schema `EnrollResponse` con `extra='forbid'` (fix regla dura #5)
- [x] 2.9 Agregar schema `Verify2FARequest` con `extra='forbid'` (fix regla dura #5)
- [x] 2.10 Implementar `authenticate_2fa` en `backend/app/services/auth_service.py` (decodifica session_token, verifica TOTP, emite tokens)
- [x] 2.11 Implementar endpoint `POST /api/auth/2fa/authenticate` en `backend/app/routers/auth.py`

## 3. Frontend — Scaffolding

- [x] 3.1 Inicializar proyecto Vite + React + TypeScript en `frontend/`
- [x] 3.2 Configurar Tailwind CSS (`tailwind.config.ts`, `postcss.config.js`, `src/index.css`)
- [x] 3.3 Configurar TypeScript estricto (`tsconfig.json`)
- [x] 3.4 Crear estructura de directorios feature-based (`features/auth/{pages,components,hooks,services,types}`, `shared/`, `layout/`)
- [x] 3.5 Crear `src/App.tsx` con Router + QueryClientProvider + AuthProvider
- [x] 3.6 Crear `src/main.tsx` como entry point

## 4. Frontend — HTTP Client con refresh transparente

- [x] 4.1 Crear `src/shared/services/api.ts` con instancia Axios
- [x] 4.2 Implementar interceptor de request (Authorization header)
- [x] 4.3 Implementar interceptor de response con refresh transparente y cola de peticiones
- [x] 4.4 Crear `src/shared/types/api.ts` con tipos genéricos de API

## 5. Frontend — Auth Context y sesión

- [x] 5.1 Crear `src/shared/types/auth.ts` con tipos de sesión
- [x] 5.2 Implementar `AuthContext` + `AuthProvider` con estado de sesión (user, tokens, permisos)
- [x] 5.3 Implementar `useAuth` hook
- [x] 5.4 Persistir tokens en `localStorage` (access_token, refresh_token)
- [x] 5.5 Recuperar sesión al cargar la app desde `localStorage`
- [x] 5.6 Crear `src/features/auth/services/authService.ts` con llamadas a la API

## 6. Frontend — Pantalla de Login

- [x] 6.1 Crear `LoginForm` componente con React Hook Form + Zod (email, password)
- [x] 6.2 Crear `LoginPage` con manejo de estados (loading, error 401, rate limit)
- [x] 6.3 Crear hook `useLoginMutation` con TanStack Query
- [x] 6.4 Redirigir a dashboard o 2FA según respuesta del login

## 7. Frontend — Pantalla de 2FA

- [x] 7.1 Crear `TwoFAForm` componente con input de 6 dígitos
- [x] 7.2 Crear `TwoFAPage` que recibe session_token del login
- [x] 7.3 Implementar mutación para `POST /api/auth/2fa/authenticate`
- [x] 7.4 Manejar errores: código inválido, session expirado

## 8. Frontend — Configuración de 2FA

- [x] 8.1 Crear `TwoFASetup` componente con QR code y secreto en texto
- [x] 8.2 Crear `TwoFASetupPage` con enroll + verify flow
- [x] 8.3 Renderizar QR code inline usando la librería `qrcode`
- [x] 8.4 Implementar verify code para activar 2FA

## 9. Frontend — Recuperación de contraseña

- [x] 9.1 Crear `ForgotPasswordForm` y `ForgotPasswordPage`
- [x] 9.2 Crear `ResetPasswordForm` y `ResetPasswordPage` (con validación de password + confirmación)
- [x] 9.3 Implementar mutaciones con TanStack Query

## 10. Frontend — Route Guard

- [x] 10.1 Crear `ProtectedRoute` componente con verificación de autenticación
- [x] 10.2 Implementar redirect a `/login?redirect=URL` preservando ruta original
- [x] 10.3 Implementar verificación de permisos opcional (`requiredPermission` prop)
- [x] 10.4 Mostrar página 403 cuando falta permiso

## 11. Frontend — Layout

- [x] 11.1 Crear `AppLayout` con sidebar + header + Outlet
- [x] 11.2 Crear `Sidebar` con items de navegación filtrados por permisos
- [x] 11.3 Implementar sidebar plegable (collapsible)
- [x] 11.4 Crear `Header` con info del usuario y botón de logout
- [x] 11.5 Integrar logout con `POST /api/auth/logout`

## 12. Tests

- [x] 12.1 Configurar vitest + testing-library + jsdom en `frontend/`
- [x] 12.2 Test: LoginPage render y validación de formulario
- [x] 12.3 Test: LoginPage submit con credenciales inválidas muestra error
- [x] 12.4 Test: TwoFAPage render y submit de código
- [x] 12.5 Test: ForgotPasswordPage render y submit
- [x] 12.6 Test: ResetPasswordPage validación de contraseñas
- [x] 12.7 Test: ProtectedRoute redirige a login sin sesión
- [x] 12.8 Test: ProtectedRoute permite acceso con sesión
- [x] 12.9 Test: Interceptor de refresh transparente

## 13. Backend — Tests de 2FA authenticate

- [x] 13.1 Test: 2FA authenticate exitoso devuelve tokens
- [x] 13.2 Test: 2FA authenticate con código inválido devuelve 400
- [x] 13.3 Test: 2FA authenticate con session_token expirado devuelve 401
- [x] 13.4 Test: CORS middleware permite origen configurado
