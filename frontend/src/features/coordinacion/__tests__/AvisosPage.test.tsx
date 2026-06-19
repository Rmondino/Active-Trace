import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { AvisosPage } from '../pages/AvisosPage'

const mockUseAvisos = vi.fn()
const mockCreateAviso = { mutate: vi.fn(), isPending: false } as any
const mockUpdateAviso = { mutate: vi.fn(), isPending: false } as any
const mockDeleteAviso = { mutate: vi.fn(), isPending: false } as any

vi.mock('../hooks/useAvisos', () => ({
  useAvisos: (...args: any[]) => mockUseAvisos(...args),
  useCreateAviso: () => mockCreateAviso,
  useUpdateAviso: () => mockUpdateAviso,
  useDeleteAviso: () => mockDeleteAviso,
}))

const mockAvisos = [
  {
    id: '1',
    alcance: 'General',
    materia_id: null,
    cohorte_id: null,
    rol_destino: null,
    severidad: 'Info',
    titulo: 'Bienvenida al ciclo',
    cuerpo: 'Bienvenidos al ciclo 2026',
    inicio_en: '2026-01-01',
    fin_en: null,
    orden: 1,
    activo: true,
    requiere_ack: false,
    total_acks: 0,
    creado_at: '2026-01-01T00:00:00Z',
  },
  {
    id: '2',
    alcance: 'Materia',
    materia_id: 'm1',
    cohorte_id: null,
    rol_destino: 'TUTOR',
    severidad: 'Advertencia',
    titulo: 'Cambio de horario',
    cuerpo: 'El horario cambió',
    inicio_en: '2026-02-01',
    fin_en: '2026-02-15',
    orden: 2,
    activo: true,
    requiere_ack: true,
    total_acks: 3,
    creado_at: '2026-01-15T00:00:00Z',
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

describe('AvisosPage', () => {
  it('renderiza título y botón nuevo aviso', () => {
    mockUseAvisos.mockReturnValue({ data: mockAvisos, isLoading: false, error: null })

    render(<AvisosPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Avisos')).toBeInTheDocument()
    expect(screen.getByText('Nuevo aviso')).toBeInTheDocument()
  })

  it('muestra los avisos en la tabla', () => {
    mockUseAvisos.mockReturnValue({ data: mockAvisos, isLoading: false, error: null })

    render(<AvisosPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Bienvenida al ciclo')).toBeInTheDocument()
    expect(screen.getByText('Cambio de horario')).toBeInTheDocument()
  })

  it('abre el formulario de creación al hacer clic en nuevo aviso', async () => {
    const user = userEvent.setup()
    mockUseAvisos.mockReturnValue({ data: mockAvisos, isLoading: false, error: null })

    render(<AvisosPage />, { wrapper: createWrapper() })

    await user.click(screen.getByRole('button', { name: 'Nuevo aviso' }))
    expect(screen.getByRole('heading', { name: 'Nuevo aviso' })).toBeInTheDocument()
  })

  it('muestra error cuando falla la carga', () => {
    mockUseAvisos.mockReturnValue({ data: undefined, isLoading: false, error: new Error('Error de red') })

    render(<AvisosPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar avisos')).toBeInTheDocument()
  })
})
