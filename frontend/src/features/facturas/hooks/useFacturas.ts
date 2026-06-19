import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { facturasService } from '../services/facturasService'
import type { FacturaPayload } from '../types/facturas'

export function useFacturas() {
  return useQuery({
    queryKey: ['facturas'],
    queryFn: () => facturasService.list(),
  })
}

export function useFactura(id: string) {
  return useQuery({
    queryKey: ['facturas', id],
    queryFn: () => facturasService.get(id),
    enabled: !!id,
  })
}

export function useCrearFactura() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: FacturaPayload) => facturasService.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['facturas'] }),
  })
}

export function useAbonarFactura() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => facturasService.abonar(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['facturas'] }),
  })
}
