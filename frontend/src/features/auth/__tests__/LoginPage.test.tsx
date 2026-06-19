import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import type { ReactNode } from 'react'

const mockLogin = vi.hoisted(() => vi.fn())

vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    login: mockLogin,
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
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </QueryClientProvider>
    )
  }
}

describe('LoginPage', () => {
  it('renderiza el formulario con email, password y botón de submit', () => {
    render(<LoginPage />, { wrapper: createWrapper() })

    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument()
  })

  it('muestra errores de validación al enviar vacío', async () => {
    const user = userEvent.setup()
    render(<LoginPage />, { wrapper: createWrapper() })

    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(screen.getByText('Email inválido')).toBeInTheDocument()
    expect(screen.getByText('La contraseña es requerida')).toBeInTheDocument()
  })

  it('muestra error del servidor al enviar credenciales inválidas', async () => {
    const user = userEvent.setup()
    mockLogin.mockRejectedValue(new Error('Credenciales inválidas'))

    render(<LoginPage />, { wrapper: createWrapper() })

    await user.type(screen.getByLabelText('Email'), 'test@example.com')
    await user.type(screen.getByLabelText('Contraseña'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(await screen.findByText('Credenciales inválidas')).toBeInTheDocument()
  })
})
