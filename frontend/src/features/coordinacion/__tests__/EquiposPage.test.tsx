import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { EquiposPage } from '../pages/EquiposPage'

const mockMutation = { mutate: vi.fn(), isPending: false, error: null } as any

vi.mock('../hooks/useEquipos', () => {
  const mut = { mutate: vi.fn(), isPending: false, error: null } as any
  return {
    useAsignaciones: vi.fn(),
    useAsignacionMasiva: () => mut,
    useClonarEquipo: () => mut,
    useVigenciaEquipo: () => mut,
  }
})

vi.mock('../services/equiposService', () => ({
  equiposService: {
    list: vi.fn(),
    masiva: vi.fn(),
    clonar: vi.fn(),
    vigencia: vi.fn(),
    exportExcel: vi.fn(),
  },
}))

import { useAsignaciones } from '../hooks/useEquipos'

const mockAsignaciones = [
  {
    id: '1',
    usuario_id: 'u1',
    usuario_nombre: 'Juan Pérez',
    rol: 'PROFESOR',
    materia_id: 'm1',
    materia_nombre: 'Matemáticas',
    carrera_id: 'c1',
    carrera_nombre: 'Ingeniería',
    cohorte_id: 'co1',
    cohorte_nombre: '2026A',
    comisiones: ['A', 'B'],
    responsable: null,
    desde: '2026-01-01',
    hasta: '2026-12-31',
    estado_vigencia: 'Vigente',
  },
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

describe('EquiposPage', () => {
  it('renderiza el título y las tabs', () => {
    vi.mocked(useAsignaciones).mockReturnValue({
      data: mockAsignaciones, isLoading: false, error: null,
    } as ReturnType<typeof useAsignaciones>)

    render(<EquiposPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Equipos Docentes')).toBeInTheDocument()
    expect(screen.getByText('Asignaciones')).toBeInTheDocument()
    expect(screen.getByText('Asignación Masiva')).toBeInTheDocument()
    expect(screen.getByText('Clonar')).toBeInTheDocument()
    expect(screen.getByText('Vigencia')).toBeInTheDocument()
  })

  it('cambia de tab al hacer clic', async () => {
    const user = userEvent.setup()
    vi.mocked(useAsignaciones).mockReturnValue({
      data: mockAsignaciones, isLoading: false, error: null,
    } as ReturnType<typeof useAsignaciones>)

    render(<EquiposPage />, { wrapper: createWrapper() })

    await user.click(screen.getByText('Clonar'))
    expect(screen.getByText('Clonar equipo')).toBeInTheDocument()
  })

  it('muestra la tabla de asignaciones con datos', () => {
    vi.mocked(useAsignaciones).mockReturnValue({
      data: mockAsignaciones, isLoading: false, error: null,
    } as ReturnType<typeof useAsignaciones>)

    render(<EquiposPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('Matemáticas')).toBeInTheDocument()
  })

  it('muestra error cuando falla la carga', () => {
    vi.mocked(useAsignaciones).mockReturnValue({
      data: undefined, isLoading: false, error: new Error('Error de red'),
    } as ReturnType<typeof useAsignaciones>)

    render(<EquiposPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar asignaciones')).toBeInTheDocument()
  })
})
