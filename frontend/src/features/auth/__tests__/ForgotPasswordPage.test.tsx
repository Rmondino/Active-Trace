import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ForgotPasswordPage } from '@/features/auth/pages/ForgotPasswordPage'
import type { ReactNode } from 'react'

const mockForgot = vi.hoisted(() => vi.fn())

vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    forgot: mockForgot,
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
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </QueryClientProvider>
    )
  }
}

describe('ForgotPasswordPage', () => {
  it('renderiza el formulario con input de email y botón de envío', () => {
    render(<ForgotPasswordPage />, { wrapper: createWrapper() })

    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Enviar instrucciones' }),
    ).toBeInTheDocument()
  })

  it('muestra mensaje de éxito después de enviar un email válido', async () => {
    const user = userEvent.setup()
    mockForgot.mockResolvedValue({ message: 'ok', token: 'abc123' })

    render(<ForgotPasswordPage />, { wrapper: createWrapper() })

    await user.type(screen.getByLabelText('Email'), 'test@example.com')
    await user.click(
      screen.getByRole('button', { name: 'Enviar instrucciones' }),
    )

    expect(
      await screen.findByText(
        'Si el email está registrado, vas a recibir instrucciones para recuperar tu contraseña.',
      ),
    ).toBeInTheDocument()
  })
})
