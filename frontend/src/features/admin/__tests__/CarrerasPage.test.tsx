import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { CarrerasPage } from '../pages/CarrerasPage'

const mockUseCarreras = vi.fn()
const mockCreate = { mutate: vi.fn(), isPending: false }
const mockUpdate = { mutate: vi.fn(), isPending: false }
const mockDelete = { mutate: vi.fn(), isPending: false }

vi.mock('../hooks/useCarreras', () => ({
  useCarreras: (...args: any[]) => mockUseCarreras(...args),
  useCreateCarrera: () => mockCreate,
  useUpdateCarrera: () => mockUpdate,
  useDeleteCarrera: () => mockDelete,
}))

const mockCarreras = [
  { id: '1', codigo: 'ABC', nombre: 'Analista', estado: 'activo', created_at: '', updated_at: '' },
  { id: '2', codigo: 'DEF', nombre: 'Diseño', estado: 'inactivo', created_at: '', updated_at: '' },
]

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('CarrerasPage', () => {
  it('renderiza título y botón nueva carrera', () => {
    mockUseCarreras.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<CarrerasPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Carreras')).toBeInTheDocument()
    expect(screen.getByText('Nueva carrera')).toBeInTheDocument()
  })

  it('muestra tabla de carreras', () => {
    mockUseCarreras.mockReturnValue({ data: mockCarreras, isLoading: false, error: null })

    render(<CarrerasPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Analista')).toBeInTheDocument()
    expect(screen.getByText('Diseño')).toBeInTheDocument()
    expect(screen.getByText('ABC')).toBeInTheDocument()
  })

  it('muestra estado con badge', () => {
    mockUseCarreras.mockReturnValue({ data: mockCarreras, isLoading: false, error: null })

    render(<CarrerasPage />, { wrapper: createWrapper() })

    const activo = screen.getByText('activo')
    expect(activo.className).toContain('green')
  })

  it('muestra mensaje cuando no hay datos', () => {
    mockUseCarreras.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<CarrerasPage />, { wrapper: createWrapper() })

    expect(screen.getByText('No hay carreras registradas')).toBeInTheDocument()
  })

  it('muestra error cuando falla la carga', () => {
    mockUseCarreras.mockReturnValue({ data: undefined, isLoading: false, error: new Error('Error') })

    render(<CarrerasPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar carreras')).toBeInTheDocument()
  })
})
