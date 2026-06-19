import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { liquidacionesService } from '../services/liquidacionesService'
import type { SalarioBasePayload, SalarioPlusPayload, MateriaGrupoPlusPayload } from '../types/liquidaciones'

export function useBasesSalariales() {
  return useQuery({
    queryKey: ['salarios', 'bases'],
    queryFn: () => liquidacionesService.bases.list(),
  })
}

export function useCreateBaseSalarial() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SalarioBasePayload) => liquidacionesService.bases.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'bases'] }),
  })
}

export function useUpdateBaseSalarial() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SalarioBasePayload }) =>
      liquidacionesService.bases.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'bases'] }),
  })
}

export function useDeleteBaseSalarial() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => liquidacionesService.bases.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'bases'] }),
  })
}

export function usePlusSalariales() {
  return useQuery({
    queryKey: ['salarios', 'plus'],
    queryFn: () => liquidacionesService.plus.list(),
  })
}

export function useCreatePlusSalarial() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SalarioPlusPayload) => liquidacionesService.plus.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'plus'] }),
  })
}

export function useUpdatePlusSalarial() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SalarioPlusPayload }) =>
      liquidacionesService.plus.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'plus'] }),
  })
}

export function useDeletePlusSalarial() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => liquidacionesService.plus.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'plus'] }),
  })
}

export function useGruposMateria() {
  return useQuery({
    queryKey: ['salarios', 'grupos-materia'],
    queryFn: () => liquidacionesService.gruposMateria.list(),
  })
}

export function useCreateGrupoMateria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: MateriaGrupoPlusPayload) => liquidacionesService.gruposMateria.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'grupos-materia'] }),
  })
}

export function useUpdateGrupoMateria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: MateriaGrupoPlusPayload }) =>
      liquidacionesService.gruposMateria.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'grupos-materia'] }),
  })
}

export function useDeleteGrupoMateria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => liquidacionesService.gruposMateria.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salarios', 'grupos-materia'] }),
  })
}

export function useLiquidaciones(cohorte_id: string, periodo: string) {
  return useQuery({
    queryKey: ['liquidaciones', cohorte_id, periodo],
    queryFn: () => liquidacionesService.liquidaciones.list(cohorte_id, periodo),
    enabled: !!cohorte_id && !!periodo,
  })
}

export function useLiquidacionDetalle(id: string) {
  return useQuery({
    queryKey: ['liquidaciones', id],
    queryFn: () => liquidacionesService.liquidaciones.get(id),
    enabled: !!id,
  })
}

export function useGenerarLiquidaciones() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ cohorte_id, periodo }: { cohorte_id: string; periodo: string }) =>
      liquidacionesService.liquidaciones.generar(cohorte_id, periodo),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['liquidaciones'] }),
  })
}

export function useCerrarLiquidacion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => liquidacionesService.liquidaciones.cerrar(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['liquidaciones'] }),
  })
}

export function useKpisContables(cohorte_id: string, periodo: string) {
  return useQuery({
    queryKey: ['liquidaciones', 'kpis', cohorte_id, periodo],
    queryFn: () => liquidacionesService.kpis(cohorte_id, periodo),
    enabled: !!cohorte_id && !!periodo,
  })
}
