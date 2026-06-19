import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { FileUpload } from '../components/FileUpload'

const mockMutate = vi.fn()
const mockUploadPreview = vi.fn()

vi.mock('../hooks/useCalificaciones', () => ({
  useUploadPreview: () => mockUploadPreview(),
}))

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

const defaultProps = {
  materiaId: 'm1',
  cohorteId: 'c1',
  onImportComplete: vi.fn(),
}

describe('FileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUploadPreview.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isError: false,
      data: undefined,
    })
  })

  it('renderiza input file y botón de previsualizar', () => {
    const { container } = render(<FileUpload {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByText('Importar calificaciones')).toBeInTheDocument()
    expect(container.querySelector('input[type="file"]')).toBeInTheDocument()
  })

  it('muestra nombre del archivo seleccionado', async () => {
    const user = userEvent.setup()
    const { container } = render(<FileUpload {...defaultProps} />, { wrapper: createWrapper() })

    const file = new File(['a,b,c\n1,2,3'], 'notas.csv', { type: 'text/csv' })
    const input = container.querySelector('input[type="file"]')!
    await user.upload(input, file)

    expect(screen.getByText(/notas\.csv/)).toBeInTheDocument()
  })

  it('habilita botón Previsualizar al seleccionar archivo', async () => {
    const user = userEvent.setup()
    const { container } = render(<FileUpload {...defaultProps} />, { wrapper: createWrapper() })

    const file = new File(['a,b,c\n1,2,3'], 'notas.csv', { type: 'text/csv' })
    const input = container.querySelector('input[type="file"]')!
    await user.upload(input, file)

    expect(screen.getByText('Previsualizar')).toBeEnabled()
  })

  it('llama al mutate al hacer clic en Previsualizar', async () => {
    const user = userEvent.setup()
    const { container } = render(<FileUpload {...defaultProps} />, { wrapper: createWrapper() })

    const file = new File(['a,b,c\n1,2,3'], 'notas.csv', { type: 'text/csv' })
    const input = container.querySelector('input[type="file"]')!
    await user.upload(input, file)

    await user.click(screen.getByText('Previsualizar'))
    expect(mockMutate).toHaveBeenCalledTimes(1)
  })

  it('muestra error cuando falla la previsualización', () => {
    mockUploadPreview.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isError: true,
      data: undefined,
    })

    render(<FileUpload {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al procesar el archivo')).toBeInTheDocument()
  })
})
