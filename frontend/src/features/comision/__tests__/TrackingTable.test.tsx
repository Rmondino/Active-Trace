import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { Comunicacion } from '../types/comunicaciones'
import { TrackingTable } from '../components/TrackingTable'

const mockData: Comunicacion[] = [
  {
    id: 'c1',
    destinatario_mask: 'j***@example.com',
    asunto: 'Actividades pendientes',
    estado: 'Enviado',
    lote_id: 'l-1',
    created_at: '2026-06-01T10:00:00Z',
    enviado_at: '2026-06-01T10:05:00Z',
    error_msg: null,
  },
  {
    id: 'c2',
    destinatario_mask: 'm***@example.com',
    asunto: 'Notificación de atraso',
    estado: 'Pendiente',
    lote_id: 'l-2',
    created_at: '2026-06-02T14:00:00Z',
    enviado_at: null,
    error_msg: null,
  },
  {
    id: 'c3',
    destinatario_mask: 'p***@example.com',
    asunto: 'Error en comunicación',
    estado: 'Error',
    lote_id: 'l-3',
    created_at: '2026-06-03T09:00:00Z',
    enviado_at: null,
    error_msg: 'SMTP connection failed',
  },
  {
    id: 'c4',
    destinatario_mask: 'l***@example.com',
    asunto: 'Cancelada',
    estado: 'Cancelado',
    lote_id: 'l-4',
    created_at: '2026-06-04T11:00:00Z',
    enviado_at: null,
    error_msg: null,
  },
]

const defaultProps = {
  data: mockData,
  isLoading: false,
}

describe('TrackingTable', () => {
  it('renderiza los destinatarios y asuntos', () => {
    render(<TrackingTable {...defaultProps} />)

    expect(screen.getByText('j***@example.com')).toBeInTheDocument()
    expect(screen.getByText('Actividades pendientes')).toBeInTheDocument()
    expect(screen.getByText('m***@example.com')).toBeInTheDocument()
    expect(screen.getByText('Notificación de atraso')).toBeInTheDocument()
  })

  it('muestra los estados correctamente', () => {
    render(<TrackingTable {...defaultProps} />)

    expect(screen.getByText('Enviado')).toBeInTheDocument()
    expect(screen.getByText('Pendiente')).toBeInTheDocument()
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('Cancelado')).toBeInTheDocument()
  })

  it('muestra estado de carga', () => {
    render(<TrackingTable {...defaultProps} isLoading={true} />)

    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay comunicaciones', () => {
    render(<TrackingTable {...defaultProps} data={[]} />)

    expect(screen.getByText('Sin comunicaciones enviadas')).toBeInTheDocument()
  })
})
