import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { LiquidacionesPage } from '../pages/LiquidacionesPage'

const mockUseLiquidaciones = vi.fn()
const mockGenerar = { mutate: vi.fn(), isPending: false }
const mockCerrar = { mutate: vi.fn(), isPending: false }

vi.mock('../hooks/useLiquidaciones', () => ({
  useLiquidaciones: (...args: any[]) => mockUseLiquidaciones(...args),
  useGenerarLiquidaciones: () => mockGenerar,
  useCerrarLiquidacion: () => mockCerrar,
}))

const mockLiquidaciones = [
  {
    id: '1',
    cohorte_id: 'c1',
    periodo: '2026-06',
    usuario_id: 'u1',
    usuario_nombre: 'Juan Pérez',
    rol: 'PROFESOR',
    comisiones: 2,
    monto_base: 500000,
    monto_plus: 100000,
    total: 600000,
    es_nexo: false,
    excluido_por_factura: false,
    estado: 'Pendiente',
    creada_at: '2026-06-01',
  },
  {
    id: '2',
    cohorte_id: 'c1',
    periodo: '2026-06',
    usuario_id: 'u2',
    usuario_nombre: 'María Gómez',
    rol: 'TUTOR',
    comisiones: 1,
    monto_base: 300000,
    monto_plus: 0,
    total: 300000,
    es_nexo: false,
    excluido_por_factura: false,
    estado: 'Cerrada',
    creada_at: '2026-06-01',
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

describe('LiquidacionesPage', () => {
  it('renderiza título y filtros', () => {
    mockUseLiquidaciones.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Liquidaciones')).toBeInTheDocument()
    expect(screen.getByText('Consultar')).toBeInTheDocument()
    expect(screen.getByText('Generar liquidaciones')).toBeInTheDocument()
  })

  it('muestra la tabla de liquidaciones', () => {
    mockUseLiquidaciones.mockReturnValue({ data: mockLiquidaciones, isLoading: false, error: null })

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('María Gómez')).toBeInTheDocument()
  })

  it('muestra estado Cerrada con badge verde', () => {
    mockUseLiquidaciones.mockReturnValue({ data: mockLiquidaciones, isLoading: false, error: null })

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    const cerrada = screen.getByText('Cerrada')
    expect(cerrada).toBeInTheDocument()
    expect(cerrada.className).toContain('green')
  })

  it('muestra error cuando falla la carga', () => {
    mockUseLiquidaciones.mockReturnValue({ data: undefined, isLoading: false, error: new Error('Error de red') })

    render(<LiquidacionesPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar liquidaciones')).toBeInTheDocument()
  })
})
