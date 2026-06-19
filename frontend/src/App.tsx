import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/shared/hooks/useAuth'
import { ProtectedRoute } from '@/shared/components/ProtectedRoute'
import { AppLayout } from '@/layout/AppLayout'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { TwoFAPage } from '@/features/auth/pages/TwoFAPage'
import { ForgotPasswordPage } from '@/features/auth/pages/ForgotPasswordPage'
import { ResetPasswordPage } from '@/features/auth/pages/ResetPasswordPage'
import { TwoFASetupPage } from '@/features/auth/pages/TwoFASetupPage'
import { ComisionSelectorPage } from '@/features/comision/pages/ComisionSelectorPage'
import { ComisionLayout } from '@/features/comision/pages/ComisionLayout'
import { CalificacionesPage } from '@/features/comision/pages/CalificacionesPage'
import { AtrasadosPage } from '@/features/comision/pages/AtrasadosPage'
import { ComunicacionPage } from '@/features/comision/pages/ComunicacionPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/login/2fa" element={<TwoFAPage />} />
            <Route path="/forgot" element={<ForgotPasswordPage />} />
            <Route path="/reset" element={<ResetPasswordPage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<div>Dashboard</div>} />
                <Route path="/2fa/setup" element={<TwoFASetupPage />} />
                <Route path="/comision" element={<ComisionSelectorPage />} />
                <Route path="/comision/:materiaId/:cohorteId" element={<ComisionLayout />}>
                  <Route path="calificaciones" element={<CalificacionesPage />} />
                  <Route path="atrasados" element={<AtrasadosPage />} />
                  <Route path="comunicacion" element={<ComunicacionPage />} />
                </Route>
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
