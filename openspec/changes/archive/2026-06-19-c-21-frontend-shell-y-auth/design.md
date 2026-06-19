## Context

Activia-trace tiene todo el backend implementado (C-01→C-14: auth JWT con 2FA, RBAC, estructura académica, equipos docentes, calificaciones, comunicaciones, etc.) pero **carece completamente de interfaz de usuario**. No existe directorio `frontend/`. Este diseño establece la SPA desde cero.

El backend de auth está funcional salvo por dos gaps detectados durante la exploración:
1. **Flujo de login con 2FA incompleto**: `POST /api/auth/login` devuelve `session_token` cuando el usuario tiene 2FA, pero no hay endpoint para canjear ese token + código TOTP por tokens reales.
2. **Sin CORS middleware**: el backend no permite conexiones cross-origin, necesario para que Vite dev (puerto 5173) y cualquier frontend empaquetado funcionen.

Además, los schemas de auth violan la regla dura #5 del proyecto (`extra='forbid'`).

## Goals / Non-Goals

**Goals:**
- Scaffolding completo del proyecto frontend con React 18 + TypeScript + Vite + Tailwind CSS
- Cliente HTTP Axios centralizado con interceptor de auth y refresh transparente de tokens
- Pantallas de login, 2FA (enroll + authenticate), forgot/reset password, logout
- Guard de rutas por autenticación y permisos (`modulo:accion`)
- Layout principal con sidebar/header adaptativo según permisos del usuario
- Agregar CORS middleware al backend para la conexión frontend
- Agregar endpoint `POST /api/auth/2fa/authenticate` para completar login con 2FA
- Fix de schemas de auth con `extra='forbid'`
- Tests de componentes clave (login, 2FA, route guard, refresh)

**Non-Goals:**
- Implementar páginas de features de dominio (C-22, C-23, C-24) — eso viene después
- Implementar diseño responsive completo — se prioriza desktop con Tailwind utility classes
- SSR, SEO, Server Components — es una SPA pura, sin necesidad de SSR
- Storybook o catálogo de componentes
- E2E con Playwright — se deja para fases posteriores

## Decisions

### D1: Vite sobre CRA
- **Decisión**: Vite con template React-TS
- **Por qué**: Ya está en el stack del proyecto, es más rápido que CRA, HMR nativo. CRA está deprecado.
- **Alternativa**: CRA — descartado por deprecación y lentitud.

### D2: react-router-dom v6 con nested layouts
- **Decisión**: react-router-dom v6 con `<Outlet>` para layouts anidados y loaders
- **Por qué**: El layout (sidebar + header) envuelve todas las rutas protegidas; react-router lo resuelve con nested routing de forma declarativa. No necesita configuración adicional.

### D3: Auth state en React Context (no Redux)
- **Decisión**: `AuthProvider` con React Context + `useReducer` para el estado de sesión (user, tokens, permisos)
- **Por qué**: El estado de auth es global pero simple (usuario logueado o no). No justifica Redux ni Zustand. TanStack Query maneja el server state; Context solo maneja el estado de sesión.
- **Alternativa**: Zustand — más elegante pero agrega una dependencia más. Context alcanza.

### D4: Refresh transparente con cola de peticiones
- **Decisión**: El interceptor de Axios atrapa 401, intenta refresh, y si tiene éxito reenvía la petición original. Si múltiples peticiones fallan 401 simultáneamente, se encolan y solo una hace el refresh.
- **Implementación**: Variable `isRefreshing` + cola de callbacks `failedQueue`. Mientras se refresca, las demás peticiones 401 se encolan. Al completar el refresh, se replayan todas.
- **Por qué**: Sin esto, múltiples peticiones simultáneas intentarían refrescar el token en paralelo, causando race conditions.

### D5: Ruta protegida por permiso
- **Decisión**: Componente `ProtectedRoute` que verifica `isAuthenticated` y opcionalmente `requiredPermission`. Sin sesión → redirect a `/login`. Sin permiso → muestra página 403 o redirige a home.
- **Por qué**: Cada feature futura (C-22, C-23, C-24) usará rutas con distintos permisos. Tener el guard incorporado desde el inicio evita refactors.
- **Implementación**: `<Route element={<ProtectedRoute permission="modulo:accion" />}>` envuelve rutas hijas.

### D6: Sidebar adaptativo por permisos
- **Decisión**: El menú del sidebar se construye a partir de una configuración declarativa de items con `requiredPermission`. Se filtran contra `user.permissions` (o roles) al renderizar.
- **Por qué**: El layout debe adaptarse a lo que cada rol puede ver. Un ADMIN ve todo; un PROFESOR solo ve su comisión y comunicaciones.
- **Implementación**: Array de `MenuItem[]` con `{ label, path, icon, requiredPermission }`. Se filtra por permisos del usuario.

### D7: QR code inline para 2FA
- **Decisión**: Usar librería `qrcode` (o `qrcode.react`) para renderizar el QR inline en el componente `TwoFASetup`
- **Por qué**: No depende de servicios externos, funciona offline en dev, privacidad (el secret nunca sale del browser).

### D8: CORS en backend — orígenes por settings
- **Decisión**: Agregar `CORSMiddleware` en `main.py` con orígenes configurables via `Settings.cors_origins`
- **Valor por defecto**: `["http://localhost:5173", "http://localhost:3000"]`
- **Por qué**: Necesario para Vite dev (5173) y producción. Configurable por entorno.

### D9: Endpoint `POST /api/auth/2fa/authenticate`
- **Decisión**: Nuevo endpoint público que recibe `session_token` (access JWT de la primera etapa) + `code` (TOTP de 6 dígitos). Verifica el código contra `user.two_fa_secret`, y si es válido, emite access + refresh tokens reales.
- **Por qué**: Sin este endpoint el login con 2FA no puede completarse. Es parte del flujo de auth (C-03) pero se implementó incompleto.
- **Request**: `{ session_token: str, code: str }`
- **Response**: `{ access_token, refresh_token, token_type: "bearer", user: { id } }`
- **Errores**: 401 si token inválido, 400 si código incorrecto
- **Implementación**: El service decodifica el session_token, obtiene el user_id, verifica TOTP con pyotp, emite tokens y los devuelve.

### D10: Fix schemas de auth con `extra='forbid'`
- **Decisión**: Agregar `model_config = ConfigDict(extra='forbid')` a todos los schemas de `routers/auth.py`
- **Por qué**: Es regla dura #5 del proyecto. Los schemas de auth son los únicos que no la cumplen.

## Frontend Architecture

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css                    ← Tailwind directives
│   ├── vite-env.d.ts
│   ├── shared/
│   │   ├── services/
│   │   │   └── api.ts               ← Axios instance + interceptors
│   │   ├── hooks/
│   │   │   └── useAuth.ts           ← Auth context hook
│   │   ├── components/
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── ErrorMessage.tsx
│   │   └── types/
│   │       ├── auth.ts
│   │       └── api.ts
│   ├── features/
│   │   └── auth/
│   │       ├── components/
│   │       │   ├── LoginForm.tsx
│   │       │   ├── TwoFAForm.tsx
│   │       │   ├── TwoFASetup.tsx
│   │       │   ├── ForgotPasswordForm.tsx
│   │       │   └── ResetPasswordForm.tsx
│   │       ├── hooks/
│   │       │   └── useAuthMutations.ts
│   │       ├── services/
│   │       │   └── authService.ts
│   │       └── pages/
│   │           ├── LoginPage.tsx
│   │           ├── TwoFAPage.tsx
│   │           ├── TwoFASetupPage.tsx
│   │           ├── ForgotPasswordPage.tsx
│   │           └── ResetPasswordPage.tsx
│   └── layout/
│       ├── AppLayout.tsx
│       ├── Sidebar.tsx
│       └── Header.tsx
└── tests/
    ├── setup.ts
    ├── features/
    │   └── auth/
    │       ├── LoginPage.test.tsx
    │       ├── TwoFAPage.test.tsx
    │       ├── ForgotPasswordPage.test.tsx
    │       └── ResetPasswordPage.test.tsx
    └── shared/
        ├── api.test.ts
        └── ProtectedRoute.test.tsx
```

## Auth Flow (State Machine)

```
[No autenticado]
     │
     ▼
┌─────────────────┐
│   LoginForm     │ ← email + password
│   POST /login   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
[2FA req]  [Sin 2FA]
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│2FAForm │ │  Dashboard   │
│POST    │ │ (redirect to │
│/2fa/   │ │  /dashboard) │
│auth    │ │              │
└───┬────┘ └──────────────┘
    │
    ▼
[Dashboard]
```

## States Coverage per View

| View | Loading | Empty | Input Validation | Server Error | Success |
|------|---------|-------|-----------------|--------------|---------|
| Login | Spinner en botón | N/A | Email inválido, password vacío | 401 credenciales, rate limit | Redirige a dashboard o 2FA |
| 2FA | Spinner en botón | N/A | Código no numérico, <6 dígitos | 401 session expirado, 400 código inválido | Redirige a dashboard |
| Forgot | Spinner en botón | N/A | Email inválido | N/A (siempre ok por seguridad) | Mensaje "revisá tu email" |
| Reset | Spinner en botón | N/A | Password < 8 chars, confirm no match | 400 token inválido/expirado | Redirige a login |
| 2FA Setup | Spinner en QR load | N/A | Código no numérico | 400 código inválido | Muestra "2FA activado" |
| Layout | Skeleton | N/A | N/A | N/A | Menú filtrado por permisos |

## Risks / Trade-offs

**[Risk 1] Refresh token expira durante uso intensivo**
→ **Mitigación**: El interceptor intenta refresh automático. Si el refresh falla (refresh expirado), redirige a login. La sesión es de 7 días, suficiente para uso diario.

**[Risk 2] 2FA secret en texto plano en DB**
→ **Trade-off**: El `two_fa_secret` del usuario no está cifrado con AES. Es un riesgo conocido del backend existente. Cifrarlo requeriría descifrarlo en cada login con 2FA, lo que agrega latencia. Aceptado como trade-off actual.

**[Risk 3] Sin Storybook ni design system formal**
→ **Mitigación**: Tailwind utility classes + diseño consistente. El layout es simple (sidebar + header + content). Cuando se agreguen más features se puede considerar un design system.

**[Risk 4] CORS abierto en dev**
→ **Mitigación**: `cors_origins` configurable via Settings. En prod se setea al dominio real. Nunca `allow_origins=["*"]` en prod con credentials.

## Open Questions

- Ninguna. Todas las decisiones están resueltas por el stack definido en ARQUITECTURA.md y la exploración del backend.
