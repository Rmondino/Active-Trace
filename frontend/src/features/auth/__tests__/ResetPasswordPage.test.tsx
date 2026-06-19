import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ResetPasswordPage } from '@/features/auth/pages/ResetPasswordPage'
import type { ReactNode } from 'react'

vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    reset: vi.fn(),
  },
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
        <MemoryRouter initialEntries={['/reset?token=abc123']}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
}

describe('ResetPasswordPage', () => {
  it('renderiza los inputs de nueva contraseña y confirmación', () => {
    render(<ResetPasswordPage />, { wrapper: createWrapper() })

    expect(screen.getByLabelText('Nueva contraseña')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Restablecer contraseña' }),
    ).toBeInTheDocument()
  })

  it('muestra error si las contraseñas no coinciden', async () => {
    const user = userEvent.setup()
    render(<ResetPasswordPage />, { wrapper: createWrapper() })

    await user.type(screen.getByLabelText('Nueva contraseña'), 'newpassword123')
    await user.type(
      screen.getByLabelText('Confirmar contraseña'),
      'differentpassword',
    )
    await user.click(
      screen.getByRole('button', { name: 'Restablecer contraseña' }),
    )

    expect(
      screen.getByText('Las contraseñas no coinciden'),
    ).toBeInTheDocument()
  })

  it('muestra error si el token no está presente', () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ResetPasswordPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(
      screen.getByText(
        'Token de recuperación no válido. Solicitá un nuevo cambio de contraseña.',
      ),
    ).toBeInTheDocument()
  })
})
