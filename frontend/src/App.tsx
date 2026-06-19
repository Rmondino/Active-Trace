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
import { PerfilPage } from '@/features/perfil/pages/PerfilPage'
import { InboxPage } from '@/features/inbox/pages/InboxPage'
import { InboxDetailPage } from '@/features/inbox/pages/InboxDetailPage'
import { NuevoMensajePage } from '@/features/inbox/pages/NuevoMensajePage'
import { GrillaSalarialPage } from '@/features/liquidaciones/pages/GrillaSalarialPage'
import { LiquidacionesPage } from '@/features/liquidaciones/pages/LiquidacionesPage'
import { LiquidacionDetallePage } from '@/features/liquidaciones/pages/LiquidacionDetallePage'
import { KpisPage } from '@/features/liquidaciones/pages/KpisPage'
import { FacturasPage } from '@/features/facturas/pages/FacturasPage'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { CarrerasPage } from '@/features/admin/pages/CarrerasPage'
import { CohortesPage } from '@/features/admin/pages/CohortesPage'
import { MateriasPage } from '@/features/admin/pages/MateriasPage'
import { UsuariosPage } from '@/features/admin/pages/UsuariosPage'
import { AuditoriaPage } from '@/features/admin/pages/AuditoriaPage'

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
                <Route path="/" element={<DashboardPage />} />
                <Route path="/2fa/setup" element={<TwoFASetupPage />} />
                <Route path="/perfil" element={<PerfilPage />} />
                <Route path="/inbox" element={<InboxPage />} />
                <Route path="/inbox/nuevo" element={<NuevoMensajePage />} />
                <Route path="/inbox/:id" element={<InboxDetailPage />} />
                <Route path="/liquidaciones" element={<LiquidacionesPage />} />
                <Route path="/liquidaciones/grilla" element={<GrillaSalarialPage />} />
                <Route path="/liquidaciones/kpis" element={<KpisPage />} />
                <Route path="/liquidaciones/:id" element={<LiquidacionDetallePage />} />
                <Route path="/facturas" element={<FacturasPage />} />
                <Route path="/admin/carreras" element={<CarrerasPage />} />
                <Route path="/admin/cohortes" element={<CohortesPage />} />
                <Route path="/admin/materias" element={<MateriasPage />} />
                <Route path="/admin/usuarios" element={<UsuariosPage />} />
                <Route path="/admin/auditoria" element={<AuditoriaPage />} />
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
