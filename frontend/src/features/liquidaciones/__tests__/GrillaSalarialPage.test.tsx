import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { GrillaSalarialPage } from '../pages/GrillaSalarialPage'

const mockUseBases = vi.fn()
const mockUsePlus = vi.fn()
const mockUseGrupos = vi.fn()

vi.mock('../hooks/useLiquidaciones', () => ({
  useBasesSalariales: (...args: any[]) => mockUseBases(...args),
  usePlusSalariales: (...args: any[]) => mockUsePlus(...args),
  useGruposMateria: (...args: any[]) => mockUseGrupos(...args),
}))

const mockBases = [
  { id: '1', rol: 'PROFESOR', monto: 500000, desde: '2026-01-01', hasta: null },
  { id: '2', rol: 'TUTOR', monto: 300000, desde: '2026-01-01', hasta: '2026-06-30' },
]

const mockPlus = [
  { id: '1', grupo: 'Laboratorio', rol: 'PROFESOR', descripcion: 'Plus lab', monto: 50000, desde: '2026-01-01', hasta: null, tope_acumulacion: 3 },
]

const mockGrupos = [
  { id: '1', materia_id: 'm1', materia_nombre: 'Matemáticas', grupo: 'Laboratorio', desde: '2026-01-01', hasta: null },
]

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('GrillaSalarialPage', () => {
  it('renderiza título y tabs', () => {
    mockUseBases.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUsePlus.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseGrupos.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<GrillaSalarialPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Grilla Salarial')).toBeInTheDocument()
    expect(screen.getByText('Bases')).toBeInTheDocument()
    expect(screen.getByText('Plus')).toBeInTheDocument()
    expect(screen.getByText('Grupos de Materia')).toBeInTheDocument()
  })

  it('muestra tabla de bases salariales', () => {
    mockUseBases.mockReturnValue({ data: mockBases, isLoading: false, error: null })
    mockUsePlus.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseGrupos.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<GrillaSalarialPage />, { wrapper: createWrapper() })

    expect(screen.getByText('PROFESOR')).toBeInTheDocument()
    expect(screen.getByText('TUTOR')).toBeInTheDocument()
  })

  it('muestra tabla de plus al cambiar tab', async () => {
    const userEvent = (await import('@testing-library/user-event')).default
    mockUseBases.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUsePlus.mockReturnValue({ data: mockPlus, isLoading: false, error: null })
    mockUseGrupos.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<GrillaSalarialPage />, { wrapper: createWrapper() })

    await userEvent.click(screen.getByText('Plus'))
    expect(screen.getByText('Laboratorio')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay datos', () => {
    mockUseBases.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUsePlus.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseGrupos.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<GrillaSalarialPage />, { wrapper: createWrapper() })

    expect(screen.getByText('No hay bases salariales registradas')).toBeInTheDocument()
  })

  it('muestra error cuando falla la carga', () => {
    mockUseBases.mockReturnValue({ data: undefined, isLoading: false, error: new Error('Error') })
    mockUsePlus.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseGrupos.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<GrillaSalarialPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar bases salariales')).toBeInTheDocument()
  })
})
