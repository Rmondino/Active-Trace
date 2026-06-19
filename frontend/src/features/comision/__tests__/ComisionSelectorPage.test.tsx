import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { ComisionSelectorPage } from '../pages/ComisionSelectorPage'

vi.mock('../hooks/useAsignaciones', () => ({
  useAsignaciones: vi.fn(),
}))

import { useAsignaciones } from '../hooks/useAsignaciones'

const mockAsignaciones = [
  { materia_id: '1', materia_nombre: 'Matemáticas', cohorte_id: 'c1', cohorte_nombre: '2026A', carrera_nombre: 'Ingeniería', rol: 'PROFESOR' },
  { materia_id: '2', materia_nombre: 'Física', cohorte_id: 'c2', cohorte_nombre: '2026B', carrera_nombre: 'Ingeniería', rol: 'PROFESOR' },
]

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>{children}</BrowserRouter>
      </QueryClientProvider>
    )
  }
}

describe('ComisionSelectorPage', () => {
  it('renderiza título y lista de comisiones', () => {
    vi.mocked(useAsignaciones).mockReturnValue({
      data: mockAsignaciones, isLoading: false, error: null,
    } as ReturnType<typeof useAsignaciones>)

    render(<ComisionSelectorPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Mis Comisiones')).toBeInTheDocument()
    expect(screen.getByText('Matemáticas')).toBeInTheDocument()
    expect(screen.getByText('Física')).toBeInTheDocument()
  })

  it('filtra comisiones al escribir en el buscador', async () => {
    const user = userEvent.setup()
    vi.mocked(useAsignaciones).mockReturnValue({
      data: mockAsignaciones, isLoading: false, error: null,
    } as ReturnType<typeof useAsignaciones>)

    render(<ComisionSelectorPage />, { wrapper: createWrapper() })

    const search = screen.getByPlaceholderText('Buscar comisión...')
    await user.type(search, 'Física')

    expect(screen.queryByText('Matemáticas')).not.toBeInTheDocument()
    expect(screen.getByText('Física')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay resultados', async () => {
    const user = userEvent.setup()
    vi.mocked(useAsignaciones).mockReturnValue({
      data: mockAsignaciones, isLoading: false, error: null,
    } as ReturnType<typeof useAsignaciones>)

    render(<ComisionSelectorPage />, { wrapper: createWrapper() })

    const search = screen.getByPlaceholderText('Buscar comisión...')
    await user.type(search, 'Inexistente')

    expect(screen.getByText('No se encontraron comisiones')).toBeInTheDocument()
  })

  it('muestra error cuando falla la carga', () => {
    vi.mocked(useAsignaciones).mockReturnValue({
      data: undefined, isLoading: false, error: new Error('Error de red'),
    } as ReturnType<typeof useAsignaciones>)

    render(<ComisionSelectorPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar comisiones')).toBeInTheDocument()
  })
})
