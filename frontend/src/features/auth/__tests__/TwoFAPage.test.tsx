import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { TwoFAPage } from '@/features/auth/pages/TwoFAPage'
import type { ReactNode } from 'react'

vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    authenticate2fa: vi.fn(),
  },
}))

vi.mock('@/shared/hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: false,
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter
          initialEntries={[
            { pathname: '/login/2fa', state: { sessionToken: 'test-token' } },
          ]}
        >
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
}

describe('TwoFAPage', () => {
  it('renderiza el formulario con input de código y botón verificar', () => {
    render(<TwoFAPage />, { wrapper: createWrapper() })

    expect(screen.getByLabelText('Código de verificación')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Verificar' })).toBeInTheDocument()
  })

  it('muestra error de sesión si no hay sessionToken', () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TwoFAPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(
      screen.getByText(
        'Sesión no válida. Por favor, iniciá sesión nuevamente.',
      ),
    ).toBeInTheDocument()
  })
})
