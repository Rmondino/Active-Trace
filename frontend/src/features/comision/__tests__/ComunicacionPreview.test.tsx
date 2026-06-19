import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ComunicacionPreview } from '../components/ComunicacionPreview'

const mockPreviews = [
  {
    alumno_id: '1',
    alumno_nombre: 'Juan Pérez',
    asunto: 'Entrega pendiente - Matemáticas',
    cuerpo: 'Hola Juan Pérez, tenés una entrega pendiente de Matemáticas',
  },
  {
    alumno_id: '2',
    alumno_nombre: 'María García',
    asunto: 'Entrega pendiente - Matemáticas',
    cuerpo: 'Hola María García, tenés una entrega pendiente de Matemáticas',
  },
]

describe('ComunicacionPreview', () => {
  it('renderiza previews para cada alumno', () => {
    render(
      <ComunicacionPreview
        previews={mockPreviews}
        onEnviar={vi.fn()}
        isLoading={false}
      />
    )

    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('María García')).toBeInTheDocument()
    expect(screen.getByText('Entrega pendiente - Matemáticas')).toBeInTheDocument()
  })

  it('renderiza botón de envío', () => {
    render(
      <ComunicacionPreview
        previews={mockPreviews}
        onEnviar={vi.fn()}
        isLoading={false}
      />
    )

    expect(screen.getByText('Enviar comunicación')).toBeInTheDocument()
  })

  it('deshabilita botón durante carga', () => {
    render(
      <ComunicacionPreview
        previews={mockPreviews}
        onEnviar={vi.fn()}
        isLoading={true}
      />
    )

    expect(screen.getByText('Enviar comunicación')).toBeDisabled()
  })
})
